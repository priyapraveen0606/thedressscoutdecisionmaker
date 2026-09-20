from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ColorChoice = Literal["green", "teal", "dark_blue", "formal_blue", "white", "half_white"]
BodyShape = Literal["pear", "hourglass", "straight", "apple"]
FootType = Literal["flat_foot", "neutral", "high_arch"]
SilhouetteChoice = Literal["fit_flare", "long_a_line", "sheath", "shift", "bodycon"]
NecklineChoice = Literal["round", "v_neck", "boat", "square", "collared"]
SleeveChoice = Literal["sleeveless", "short", "three_quarter", "long"]
DecisionChoice = Literal["BUY", "ALTER_THEN_BUY", "PASS"]


class UserProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    height_cm: float = Field(..., ge=120, le=210)
    weight_kg: float = Field(..., ge=30, le=150)
    body_shape: BodyShape = "pear"
    preferred_colors: list[ColorChoice] = Field(
        default_factory=lambda: ["green", "teal", "dark_blue", "formal_blue", "white", "half_white"]
    )
    foot_type: FootType = "flat_foot"
    max_hem_below_knee_in: float = 1.5
    formal_wear_black_disfavored: bool = True
    min_sleeve_required: bool = True


class ProductCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=2)
    brand: str = Field(..., min_length=2)
    price: float | None = None
    color: str = "green"
    silhouette: SilhouetteChoice = "fit_flare"
    neckline: NecklineChoice = "v_neck"
    sleeve_length: SleeveChoice = "short"
    hem_length_below_knee_in: float = 0.0
    is_office_formal: bool = True

    @field_validator("color")
    @classmethod
    def normalize_color(cls, value: str) -> str:
        cleaned = value.strip().lower().replace("-", "_")
        aliases = {
            "darkblue": "dark_blue",
            "formalblue": "formal_blue",
            "halfwhite": "half_white",
            "tealblue": "teal",
            "greenish": "green",
            "black": "black",
        }
        return aliases.get(cleaned, cleaned)


class EvaluateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user: UserProfile
    product: ProductCandidate


class DecisionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: DecisionChoice
    score: int = Field(..., ge=0, le=100)
    reasons: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    summary: str
