from __future__ import annotations

from .schema import DecisionResult, ProductCandidate, UserProfile

PREFERRED_SILHOUETTES = {"fit_flare", "long_a_line"}
PREFERRED_NECKLINES = {"v_neck", "round", "collared"}
PREFERRED_COLORS = {"green", "teal", "dark_blue", "formal_blue", "white", "half_white"}


def evaluate_product(product: ProductCandidate, user: UserProfile) -> DecisionResult:
    reasons: list[str] = []
    actions: list[str] = []
    score = 100

    if product.silhouette not in PREFERRED_SILHOUETTES:
        score -= 35
        reasons.append("Silhouette is not a recommended fit & flare or long A-line.")
        actions.append("Choose a fit & flare or long A-line silhouette for balance.")

    if user.min_sleeve_required and product.sleeve_length == "sleeveless":
        score -= 45
        reasons.append("Sleeves are mandatory for the anchor fit.")
        actions.append("Select a sleeved option; sleeveless cuts fail the requirement.")

    max_hem = user.max_hem_below_knee_in
    if product.hem_length_below_knee_in > max_hem:
        score -= 30
        reasons.append(f"Hem sits {product.hem_length_below_knee_in} inches below the knee, above the allowed {max_hem} inches.")
        actions.append("Keep the hem at or just above the knee to preserve the petite proportion.")

    if product.color.lower() == "black" and product.is_office_formal and user.formal_wear_black_disfavored:
        score -= 15
        reasons.append("Black is deprioritized for formal office wear in this profile.")
        actions.append("Pick a preferred formal tone such as teal, blue, or white instead.")
    elif product.color not in user.preferred_colors and product.color.lower() != "black":
        score -= 10
        reasons.append(f"Color {product.color} is outside the preferred office palette.")
        actions.append("Stay within the anchor palette for a higher-confidence buy decision.")

    if product.neckline not in PREFERRED_NECKLINES:
        score -= 10
        reasons.append("Neckline does not align with the anchor styling preferences.")
        actions.append("Favor a V-neck, round neck, or collared neckline.")

    if product.color not in PREFERRED_COLORS and product.color.lower() != "black":
        score -= 5
        reasons.append("Color choice falls outside the tighter style-safe palette.")

    if product.silhouette in PREFERRED_SILHOUETTES and product.hem_length_below_knee_in <= max_hem:
        score += 5

    if score >= 85 and not reasons:
        decision = "BUY"
        summary = "Strong match to the petite office-anchor profile: balanced silhouette, sleeve compliance, and preferred palette."
    elif score >= 70 and len(reasons) <= 2:
        decision = "ALTER_THEN_BUY"
        summary = "This is close to the anchor fit; a small alteration or tonal adjustment may convert it to a buy."
    else:
        decision = "PASS"
        summary = "The item conflicts with the key petite styling rules and is a poor fit for the anchor profile."

    if decision == "BUY" and reasons:
        reasons = [r for r in reasons if "below the knee" not in r and "not in" not in r]

    return DecisionResult(
        decision=decision,
        score=max(0, min(100, score)),
        reasons=reasons,
        actions=actions,
        summary=summary,
    )
