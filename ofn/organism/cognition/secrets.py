from __future__ import annotations

from pathlib import Path


SECRETS_PATH = Path("/etc/octopus/secrets.env")
ALLOWED_KEYS = {
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_MODEL",
    "FLASH_API_KEY",
    "FLASH_MODEL",
}


def load_named_secrets(path: Path = SECRETS_PATH) -> dict[str, str]:
    secrets: dict[str, str] = {}
    if not path.is_file():
        return secrets
    mode = path.stat().st_mode & 0o777
    if mode & 0o077:
        raise PermissionError("secrets_must_be_0600")
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if key not in ALLOWED_KEYS:
            continue
        secrets[key] = value.strip().strip('"').strip("'")
    return secrets
