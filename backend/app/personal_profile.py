from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet


def _load_dotenv_file() -> None:
    dotenv_path = Path(".env")
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = [part.strip() for part in line.split("=", 1)]
        if key and key not in os.environ:
            os.environ[key] = value.strip('"\'')


def _write_dotenv_file(secret: str, encrypted: str) -> None:
    dotenv_path = Path(".env")
    lines = []

    if dotenv_path.exists():
        lines = dotenv_path.read_text(encoding="utf-8").splitlines()

    updated: list[str] = []
    seen_secret = False
    seen_encrypted = False

    for line in lines:
        if line.startswith("PERSONAL_PROFILE_SECRET="):
            updated.append(f'PERSONAL_PROFILE_SECRET="{secret}"')
            seen_secret = True
            continue
        if line.startswith("PERSONAL_PROFILE_ENCRYPTED="):
            updated.append(f'PERSONAL_PROFILE_ENCRYPTED="{encrypted}"')
            seen_encrypted = True
            continue
        updated.append(line)

    if not seen_secret:
        updated.append(f'PERSONAL_PROFILE_SECRET="{secret}"')
    if not seen_encrypted:
        updated.append(f'PERSONAL_PROFILE_ENCRYPTED="{encrypted}"')

    dotenv_path.write_text("\n".join(updated) + "\n", encoding="utf-8")


def save_personal_profile(profile: dict[str, Any]) -> dict[str, Any]:
    """Persist a profile locally using the same encrypted env-backed mechanism.

    This keeps the app safe for a single-user local workflow while also supporting a
    basic admin-style management endpoint that can be replaced later by a true
    multi-user or authenticated profile service.
    """
    _load_dotenv_file()

    secret = os.getenv("PERSONAL_PROFILE_SECRET") or Fernet.generate_key().decode("utf-8")
    encrypted = Fernet(secret.encode("utf-8")).encrypt(json.dumps(profile, separators=(",", ":")).encode("utf-8"))

    os.environ["PERSONAL_PROFILE_SECRET"] = secret
    os.environ["PERSONAL_PROFILE_ENCRYPTED"] = encrypted.decode("utf-8")
    _write_dotenv_file(secret, encrypted.decode("utf-8"))
    return profile


def load_personal_profile() -> dict[str, Any]:
    """Load the private anchor profile from a Fernet-encrypted environment payload.

    This keeps the personalized values out of source files while still allowing a
    single-user local profile today and a parameterized future multi-user model later.
    """
    _load_dotenv_file()

    secret = os.getenv("PERSONAL_PROFILE_SECRET")
    encrypted = os.getenv("PERSONAL_PROFILE_ENCRYPTED")

    if not secret or not encrypted:
        raise RuntimeError(
            "Set PERSONAL_PROFILE_SECRET and PERSONAL_PROFILE_ENCRYPTED in the environment "
            "or in a .env file to enable the personalized anchor profile."
        )

    try:
        plaintext = Fernet(secret.encode("utf-8")).decrypt(encrypted.encode("utf-8"))
    except Exception as exc:  # pragma: no cover - defensive runtime guard
        raise RuntimeError("PERSONAL_PROFILE_SECRET and PERSONAL_PROFILE_ENCRYPTED do not match.") from exc

    return json.loads(plaintext.decode("utf-8"))
