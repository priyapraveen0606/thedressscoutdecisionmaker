#!/usr/bin/env python3
from __future__ import annotations

import json

from cryptography.fernet import Fernet

PROFILE = {
    "height_cm": 156,
    "weight_kg": 74,
    "body_shape": "pear",
    "preferred_colors": ["green", "teal", "dark_blue", "formal_blue", "white", "half_white"],
    "foot_type": "flat_foot",
    "max_hem_below_knee_in": 1.5,
    "formal_wear_black_disfavored": True,
    "min_sleeve_required": True,
}


def main() -> None:
    key = Fernet.generate_key()
    encrypted = Fernet(key).encrypt(json.dumps(PROFILE, separators=(",", ":")).encode("utf-8"))

    print(f'PERSONAL_PROFILE_SECRET="{key.decode()}"')
    print(f'PERSONAL_PROFILE_ENCRYPTED="{encrypted.decode()}"')


if __name__ == "__main__":
    main()
