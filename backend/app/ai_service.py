from __future__ import annotations

import json
import os
from typing import Any

from .engine import evaluate_product
from .schema import ProductCandidate, UserProfile

try:
    from openai import OpenAI
except ModuleNotFoundError:  # pragma: no cover - optional dependency for AI layer
    OpenAI = None


def _get_openai_client() -> Any | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    return OpenAI(api_key=api_key)


def build_search_queries(profile: dict[str, Any], retailers: list[str] | None = None, limit: int = 3) -> list[str]:
    """Build safe, retailer-specific search strings for the crawler layer.

    These queries stay server-side and are not exposed to the frontend.
    """
    colors = profile.get("preferred_colors", ["green", "teal", "dark_blue", "formal_blue"])
    preferred_palette = ", ".join(colors[:3])
    sleeve_required = "sleeves" if profile.get("min_sleeve_required", True) else "sleeveless"
    silhouette = "a-line" if profile.get("body_shape") == "pear" else "fit and flare"
    retailers = retailers or ["amazon", "fablestreet"]

    queries: list[str] = []
    for retailer in retailers[:2]:
        queries.append(
            f"{retailer} women office formal {silhouette} dress {preferred_palette} {sleeve_required}"
        )
    if len(queries) < limit:
        queries.append(
            f"women office formal {silhouette} dress {preferred_palette} {sleeve_required}"
        )
    return queries[:limit]


def evaluate_search_results(items: list[dict[str, Any]], profile_data: dict[str, Any], minimum_score: int = 80) -> list[dict[str, Any]]:
    """Evaluate a batch of crawled products and keep only the curated feed above threshold."""
    profile = UserProfile(**profile_data)
    curated: list[dict[str, Any]] = []

    for item in items:
        candidate = ProductCandidate(
            title=item.get("title", "Office Dress"),
            brand=item.get("brand", "Catalog Brand"),
            price=float(item.get("price", 0.0) or 0.0),
            color=item.get("color", "green"),
            silhouette=item.get("silhouette", "fit_flare"),
            neckline=item.get("neckline", "v_neck"),
            sleeve_length=item.get("sleeve_length", "short"),
            hem_length_below_knee_in=float(item.get("hem_length_below_knee_in", 0.5) or 0.5),
            is_office_formal=bool(item.get("is_office_formal", True)),
        )
        decision = evaluate_product(candidate, profile)
        if decision.score >= minimum_score:
            curated.append(
                {
                    "title": candidate.title,
                    "brand": candidate.brand,
                    "price": candidate.price,
                    "color": candidate.color,
                    "decision": decision.decision,
                    "score": decision.score,
                    "summary": decision.summary,
                    "reasons": decision.reasons,
                }
            )
    return curated


def summarize_results(results: list[dict[str, Any]]) -> str:
    """Generate a local summary without exposing secrets to the browser.

    If no OpenAI key is configured, the function falls back to a deterministic summary.
    """
    if not results:
        return "No items matched the review criteria."

    client = _get_openai_client()
    if client is None:
        top = max(results, key=lambda item: item.get("score", 0))
        return (
            f"Top recommendation: {top.get('title', 'item')} ({top.get('decision', 'BUY')}, "
            f"score {top.get('score', 0)}). Review the remaining items for fit and styling changes."
        )

    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "messages": [
            {
                "role": "system",
                "content": "You are a concise style assistant. Summarize recommendations without exposing private profile data.",
            },
            {
                "role": "user",
                "content": json.dumps(results, ensure_ascii=True),
            },
        ],
        "temperature": 0.2,
    }

    try:
        completion = client.chat.completions.create(**payload)
        content = completion.choices[0].message.content
        if content:
            return content.strip()
    except Exception:
        pass

    top = max(results, key=lambda item: item.get("score", 0))
    return (
        f"Top recommendation: {top.get('title', 'item')} ({top.get('decision', 'BUY')}, "
        f"score {top.get('score', 0)}). The AI summary was unavailable, so the deterministic local summary was used."
    )
