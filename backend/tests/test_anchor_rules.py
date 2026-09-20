import json
import os

from cryptography.fernet import Fernet

from backend.app.ai_service import build_search_queries, evaluate_search_results, summarize_results
from backend.app.crawler import parse_product_html
from backend.app.engine import evaluate_product
from backend.app.personal_profile import _load_dotenv_file, load_personal_profile
from backend.app.schema import ProductCandidate, UserProfile


_load_dotenv_file()

profile_payload = {
    "height_cm": int(os.getenv("ANCHOR_HEIGHT_CM", "156")),
    "weight_kg": int(os.getenv("ANCHOR_WEIGHT_KG", "74")),
    "body_shape": os.getenv("ANCHOR_BODY_SHAPE", "pear"),
    "preferred_colors": os.getenv("ANCHOR_PREFERRED_COLORS", "green,teal,dark_blue,formal_blue,white,half_white").split(","),
    "foot_type": os.getenv("ANCHOR_FOOT_TYPE", "flat_foot"),
    "max_hem_below_knee_in": float(os.getenv("ANCHOR_HEM_MAX_IN", "1.5")),
    "formal_wear_black_disfavored": os.getenv("ANCHOR_BLACK_DISFAVORED", "true").lower() == "true",
    "min_sleeve_required": os.getenv("ANCHOR_SLEEVES_REQUIRED", "true").lower() == "true",
}

os.environ["PERSONAL_PROFILE_SECRET"] = os.getenv("PERSONAL_PROFILE_SECRET", Fernet.generate_key().decode())
os.environ["PERSONAL_PROFILE_ENCRYPTED"] = os.getenv(
    "PERSONAL_PROFILE_ENCRYPTED",
    Fernet(os.environ["PERSONAL_PROFILE_SECRET"]).encrypt(json.dumps(profile_payload).encode()).decode(),
)


def test_buy_when_anchor_profile_matches():
    profile_data = load_personal_profile()
    profile = UserProfile(**profile_data)
    product = ProductCandidate(
        title="Petite Green Fit & Flare Dress",
        brand="Anchor Studio",
        price=78.0,
        color="green",
        silhouette="fit_flare",
        neckline="v_neck",
        sleeve_length="short",
        hem_length_below_knee_in=0.5,
        is_office_formal=True,
    )

    result = evaluate_product(product, profile)

    assert result.decision == "BUY"
    assert result.score >= 85


def test_pass_for_disallowed_sleeveless_formal_cut():
    profile_data = load_personal_profile()
    profile = UserProfile(**profile_data)
    product = ProductCandidate(
        title="Sleeveless Blue Wrap Dress",
        brand="No Fit Co",
        price=45.0,
        color="formal_blue",
        silhouette="fit_flare",
        neckline="v_neck",
        sleeve_length="sleeveless",
        hem_length_below_knee_in=0.25,
        is_office_formal=True,
    )

    result = evaluate_product(product, profile)

    assert result.decision == "PASS"
    assert "Sleeves are mandatory" in result.reasons[0]


def test_alter_then_buy_for_minor_hem_length_issue():
    profile_data = load_personal_profile()
    profile = UserProfile(**profile_data)
    product = ProductCandidate(
        title="Formal White A-Line Dress",
        brand="Mila",
        price=92.0,
        color="white",
        silhouette="long_a_line",
        neckline="round",
        sleeve_length="short",
        hem_length_below_knee_in=2.0,
        is_office_formal=True,
    )

    result = evaluate_product(product, profile)

    assert result.decision == "ALTER_THEN_BUY"
    assert any("hem" in reason.lower() for reason in result.reasons)


def test_parse_amazon_product_html():
    html = '''
    <html>
      <head>
        <title>Amazon Essentials Women's Midi Dress | Amazon</title>
      </head>
      <body>
        <h1 id="productTitle">Amazon Essentials Women's Midi Dress</h1>
        <div id="variation_color_name">Teal</div>
        <span class="a-price-whole">64</span>
      </body>
    </html>
    '''

    product = parse_product_html("https://www.amazon.com/dp/example", html)

    assert product.brand == "Amazon"
    assert product.color == "teal"
    assert product.silhouette in {"fit_flare", "long_a_line", "sheath"}
    assert product.price == 64.0


def test_parse_fablestreet_product_html():
    html = '''
    <html>
      <head>
        <meta property="og:title" content="Fable Street Aline Dress in Green" />
      </head>
      <body>
        <h1 class="product-title">Aline Dress</h1>
        <div class="product-colour">Green</div>
        <span class="price">$82</span>
      </body>
    </html>
    '''

    product = parse_product_html("https://www.fablestreet.com/products/aline-dress", html)

    assert product.brand == "Fable Street"
    assert product.color == "green"
    assert product.silhouette == "long_a_line"
    assert product.price == 82.0


def test_build_search_queries_for_profile():
    profile = {
        "body_shape": "pear",
        "preferred_colors": ["green", "teal", "dark_blue", "formal_blue", "white", "half_white"],
        "min_sleeve_required": True,
        "max_hem_below_knee_in": 1.5,
    }

    queries = build_search_queries(profile, retailers=["amazon", "fablestreet"], limit=3)

    assert len(queries) == 3
    assert any("green" in query.lower() for query in queries)
    assert any("sleeves" in query.lower() for query in queries)
    assert any("a-line" in query.lower() or "fit and flare" in query.lower() for query in queries)


def test_summarize_results_without_openai_key():
    summary = summarize_results([
        {"title": "Teal A-line Dress", "decision": "BUY", "score": 91, "brand": "Amazon"},
        {"title": "White Sheath Dress", "decision": "ALTER_THEN_BUY", "score": 76, "brand": "Fable Street"},
    ])

    assert "BUY" in summary or "ALTER_THEN_BUY" in summary
    assert "Teal" in summary or "White" in summary


def test_evaluate_search_results_filters_curated_feed():
    profile = {
        "height_cm": 156,
        "weight_kg": 74,
        "body_shape": "pear",
        "preferred_colors": ["green", "teal", "dark_blue", "formal_blue", "white", "half_white"],
        "foot_type": "flat_foot",
        "max_hem_below_knee_in": 1.5,
        "formal_wear_black_disfavored": True,
        "min_sleeve_required": True,
    }

    items = [
        {"title": "Teal A-Line Dress", "brand": "Amazon", "price": 64, "color": "teal", "silhouette": "long_a_line", "neckline": "v_neck", "sleeve_length": "short", "hem_length_below_knee_in": 0.5, "is_office_formal": True},
        {"title": "Black Structured Sheath", "brand": "Amazon", "price": 88, "color": "black", "silhouette": "sheath", "neckline": "round", "sleeve_length": "short", "hem_length_below_knee_in": 0.75, "is_office_formal": True},
    ]

    curated = evaluate_search_results(items, profile, minimum_score=80)

    assert len(curated) == 1
    assert curated[0]["decision"] == "BUY"
    assert curated[0]["score"] >= 80
