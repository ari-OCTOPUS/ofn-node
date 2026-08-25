from __future__ import annotations

import hashlib
import json
import os
import ssl
import time
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlparse

from ofn.organism.cognition.secrets import load_named_secrets


ALLOWED_HOSTS = {"api.deepseek.com"}


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


def teacher_status(secrets: dict[str, str] | None = None) -> dict[str, Any]:
    try:
        secrets = secrets if secrets is not None else load_named_secrets()
    except PermissionError:
        return {
            "deepseek": "SECRET_PERMISSION_UNSAFE",
            "flash": "SECRET_PERMISSION_UNSAFE",
            "ready": False,
            "learn_env": os.environ.get("OCTOPUS_LEARN_EXTERNAL") == "1",
            "host": "api.deepseek.com",
        }
    deepseek_key = secrets.get("DEEPSEEK_API_KEY") or ""
    flash_key = secrets.get("FLASH_API_KEY") or ""
    deepseek = "READY" if len(deepseek_key) >= 12 else "NOT_CONFIGURED"
    flash = "READY" if len(flash_key) >= 12 else (
        "USES_DEEPSEEK_CHAT_AS_FLASH" if deepseek == "READY" else "NOT_CONFIGURED"
    )
    return {
        "deepseek": deepseek,
        "flash": flash,
        "ready": deepseek == "READY",
        "learn_env": os.environ.get("OCTOPUS_LEARN_EXTERNAL") == "1",
        "host": "api.deepseek.com",
    }


def external_api_label(status: dict[str, Any] | None = None) -> str:
    status = status if status is not None else teacher_status()
    if status.get("learn_env") and status.get("ready"):
        return "LEARN_ONLY_DEEPSEEK"
    return "DISABLED"


def _complete(
    *,
    api_key: str,
    model: str,
    prompt: str,
    max_tokens: int,
    track: str,
) -> dict[str, Any]:
    url = "https://api.deepseek.com/v1/chat/completions"
    parsed = urlparse(url)
    if parsed.hostname not in ALLOWED_HOSTS:
        return {"status": "DENIED_HOST", "answer": None, "track": track}
    body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You tutor board-life-001, a local Orange Pi organism. "
                    "Reply briefly in the user's language. "
                    "Label the answer as unverified model knowledge, not a sensor reading. "
                    "Do not invent GPS, live weather, prices, or board capabilities."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0,
        "stream": False,
    }
    raw_body = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=raw_body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key,
        },
    )
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        NoRedirectHandler(),
    )
    t0 = time.monotonic()
    try:
        with opener.open(request, timeout=25) as response:
            raw = response.read()
            status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = exc.code
    except Exception as exc:
        return {
            "status": "DEGRADED",
            "error": f"{type(exc).__name__}",
            "answer": None,
            "track": track,
        }
    try:
        payload = json.loads(raw.decode("utf-8", "replace")) if raw else {}
    except json.JSONDecodeError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    choices = payload.get("choices") if isinstance(payload.get("choices"), list) else []
    first = choices[0] if choices and isinstance(choices[0], dict) else {}
    message = first.get("message") if isinstance(first.get("message"), dict) else {}
    answer = message.get("content")
    if not isinstance(answer, str) or not answer.strip():
        answer = None
    return {
        "status": "OK" if status == 200 and answer else "DEGRADED",
        "http_status": status,
        "latency_ms": int((time.monotonic() - t0) * 1000),
        "response_hash": hashlib.sha256(raw or b"").hexdigest(),
        "answer": answer.strip() if answer else None,
        "track": track,
        "model": model,
        "error": None if answer else "empty_or_invalid_model_content",
    }


def complete_flash(prompt: str) -> dict[str, Any]:
    secrets = load_named_secrets()
    key = secrets.get("FLASH_API_KEY") or secrets.get("DEEPSEEK_API_KEY") or ""
    if len(key) < 12:
        return {"status": "NOT_CONFIGURED", "answer": None, "track": "flash"}
    model = secrets.get("FLASH_MODEL") or secrets.get("DEEPSEEK_MODEL") or "deepseek-chat"
    return _complete(
        api_key=key,
        model=model,
        prompt=prompt,
        max_tokens=80,
        track="flash",
    )


def complete_deep(prompt: str) -> dict[str, Any]:
    secrets = load_named_secrets()
    key = secrets.get("DEEPSEEK_API_KEY") or ""
    if len(key) < 12:
        return {"status": "NOT_CONFIGURED", "answer": None, "track": "deep"}
    model = secrets.get("DEEPSEEK_MODEL") or "deepseek-chat"
    return _complete(
        api_key=key,
        model=model,
        prompt=prompt,
        max_tokens=180,
        track="deep",
    )
