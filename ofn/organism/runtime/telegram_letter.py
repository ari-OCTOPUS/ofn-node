from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


SECRETS_PATH = Path("/etc/octopus/secrets.env")
LETTERS_PATH = Path("/opt/octopus/lab/state/LETTERS.jsonl")
TELEGRAM_API = "https://api.telegram.org"


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


def load_telegram_secrets(path: Path = SECRETS_PATH) -> dict[str, str]:
    secrets: dict[str, str] = {}
    if not path.is_file():
        return secrets
    mode = path.stat().st_mode & 0o777
    if mode & 0o077:
        raise PermissionError("telegram_secrets_must_be_0600")
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if key not in {"TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"}:
            continue
        secrets[key] = value.strip().strip('"').strip("'")
    return secrets


def telegram_ready(secrets: dict[str, str] | None = None) -> str:
    try:
        secrets = secrets if secrets is not None else load_telegram_secrets()
    except PermissionError:
        return "TELEGRAM_SECRET_PERMISSION_UNSAFE"
    token = secrets.get("TELEGRAM_BOT_TOKEN") or ""
    chat = secrets.get("TELEGRAM_CHAT_ID") or ""
    if not token or not chat:
        return "TELEGRAM_NOT_CONFIGURED"
    if ":" not in token or len(token) < 20:
        return "TELEGRAM_TOKEN_INVALID_SHAPE"
    return "READY"


def append_local_letter(letter: dict[str, Any], path: Path = LETTERS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(letter, ensure_ascii=False, sort_keys=True) + "\n")


def send_telegram(text: str, secrets: dict[str, str] | None = None) -> dict[str, Any]:
    secrets = secrets if secrets is not None else load_telegram_secrets()
    status = telegram_ready(secrets)
    if status != "READY":
        return {"sent": False, "status": status}
    token = secrets["TELEGRAM_BOT_TOKEN"]
    chat = secrets["TELEGRAM_CHAT_ID"]
    body = urllib.parse.urlencode(
        {
            "chat_id": chat,
            "text": text[:3500],
            "disable_web_page_preview": "true",
        }
    ).encode("utf-8")
    url = f"{TELEGRAM_API}/bot{token}/sendMessage"
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        NoRedirectHandler(),
    )
    try:
        with opener.open(request, timeout=8) as response:
            raw = response.read(4096)
            return {
                "sent": response.status == 200,
                "status": "SENT" if response.status == 200 else f"HTTP_{response.status}",
                "bytes": len(raw),
            }
    except Exception as exc:
        return {"sent": False, "status": type(exc).__name__}
