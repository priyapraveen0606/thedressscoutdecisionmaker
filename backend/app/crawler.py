from __future__ import annotations

import re
from typing import Any

import httpx
from bs4 import BeautifulSoup

from .schema import ProductCandidate


def _text(node: Any) -> str:
    if node is None:
        return ""
    if hasattr(node, "get_text"):
        return node.get_text(" ", strip=True)
    return str(node).strip()


def _clean_color(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z]", "", value.lower())
    aliases = {
        "tealblue": "teal",
        "darkblue": "dark_blue",
        "formalblue": "formal_blue",
        "halfwhite": "half_white",
        "greenish": "green",
    }
    return aliases.get(cleaned, cleaned or "green")


def _infer_silhouette(title: str, color: str, html: str) -> str:
    lowered = f"{title} {html}".lower()
    if "aline" in lowered or "a-line" in lowered:
        return "long_a_line"
    if "fit" in lowered and "flare" in lowered:
        return "fit_flare"
    if "sheath" in lowered:
        return "sheath"
    if "shift" in lowered:
        return "shift"
    return "fit_flare"


def _extract_price(text: str) -> float:
    match = re.search(r"\$?(\d+(?:\.\d+)?)", text or "")
    if not match:
        return 0.0
    return float(match.group(1))


def parse_product_html(url: str, html: str) -> ProductCandidate:
    """Parse product HTML from a storefront into a ProductCandidate."""
    soup = BeautifulSoup(html, "html.parser")
    title = _text(soup.select_one("h1, h2, .product-title, #productTitle, meta[property='og:title']")) or "Office Dress"
    if soup.select_one("meta[property='og:title']"):
        title = soup.select_one("meta[property='og:title']").get("content", title)

    brand = "Amazon" if "amazon" in url.lower() else "Fable Street" if "fablestreet" in url.lower() else "Catalog Brand"

    color_source = (
        _text(soup.select_one("#variation_color_name, .product-colour, .color, [data-color]"))
        or _text(soup.select_one("meta[property='og:color']"))
        or "green"
    )
    color = _clean_color(color_source)

    price = _extract_price(
        _text(soup.select_one(".a-price-whole, .price, .product-price, [data-price]"))
        or _text(soup.select_one("span.price, .ProductPrice, .product-price"))
        or "0"
    )

    silhouette = _infer_silhouette(title, color, html)
    neckline = "v_neck" if "v" in title.lower() else "round"
    sleeve = "short" if "sleeve" not in title.lower() else "short"

    return ProductCandidate(
        title=title,
        brand=brand,
        price=price,
        color=color,
        silhouette=silhouette,
        neckline=neckline,
        sleeve_length=sleeve,
        hem_length_below_knee_in=0.5,
        is_office_formal=True,
    )


async def crawl_catalog(url: str) -> list[ProductCandidate]:
    """Fetch and normalize a small set of items from a catalog page."""
    if not url:
        return []

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPError:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    product_nodes: list[Any] = []

    if "amazon" in url.lower():
        product_nodes = soup.select(".s-result-item, .ProductGridItem, .a-cardui")[:10]
    elif "fablestreet" in url.lower():
        product_nodes = soup.select("article, .product-card, .ProductCard, .product")[:10]
    else:
        product_nodes = soup.select("article, .product, .item")[:10]

    products: list[ProductCandidate] = []
    for item in product_nodes:
        candidate_html = str(item)
        title = _text(item.select_one("h1, h2, h3, .product-title, .title, #productTitle")) or "Office Dress"
        brand = "Amazon" if "amazon" in url.lower() else "Fable Street" if "fablestreet" in url.lower() else "Catalog Brand"
        color = _clean_color(_text(item.select_one(".product-colour, .color, [data-color]")) or "green")
        price = _extract_price(_text(item.select_one(".price, .a-price-whole, [data-price]")) or 0.0)

        try:
            products.append(
                ProductCandidate(
                    title=title,
                    brand=brand,
                    price=float(price),
                    color=color,
                    silhouette=_infer_silhouette(title, color, candidate_html),
                    neckline="v_neck" if "v" in title.lower() else "round",
                    sleeve_length="short",
                    hem_length_below_knee_in=0.5,
                    is_office_formal=True,
                )
            )
        except (TypeError, ValueError):
            continue

    if not products:
        return [parse_product_html(url, response.text)]

    return products
