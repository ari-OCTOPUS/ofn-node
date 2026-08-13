"""Gate 0 + فلگ. راز Bearer هرگز لاگ نمی‌شود."""
from __future__ import annotations

import hmac
import os
from urllib.parse import urlparse

from . import FLAG

KINDS = frozenset({"ask", "status", "panel", "task"})
TARGET_AGENTS = frozenset({"ofn", "hypno"})
TARGET_INSTANCES = frozenset({"ziman", "lead", "studio", "panel", "hypno"})

# هاست‌هایی که CONTROL_URL نباید به آن‌ها اشاره کند (مغزهای برد، نه ویندوز).
_FORBIDDEN_LABELS = frozenset({"ziman", "lead", "studio", "panel", "hypno", "app"})
_FORBIDDEN_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def flag_on() -> bool:
    return os.environ.get(FLAG, "0") == "1"


def bearer_configured() -> bool:
    return bool(str(os.environ.get("OCTOPUS_BOARD_CP_BEARER", "")).strip())


def control_url() -> str:
    return str(os.environ.get("OCTOPUS_BOARD_CONTROL_URL", "")).strip()


def control_url_ok(url: str | None = None) -> bool:
    """Gate 0: HTTPS ویندوز-facing؛ نه لگ‌های برد، نه :8796."""
    raw = (url if url is not None else control_url()).strip()
    if not raw:
        return False
    try:
        p = urlparse(raw)
    except Exception:  # noqa: BLE001
        return False
    if p.scheme != "https":
        return False
    if p.username or p.password:
        return False
    host = (p.hostname or "").strip().lower().rstrip(".")
    if not host:
        return False
    if ":8796" in raw:
        return False
    if p.port == 8796:
        return False
    if host in _FORBIDDEN_HOSTS:
        return False
    label = host.split(".")[0]
    if label in _FORBIDDEN_LABELS:
        return False
    return True


def gate0_ready() -> bool:
    """URL مشخص + HTTPS مجاز. راز را در خروجی نمی‌آوریم."""
    return control_url_ok() and bearer_configured()


def is_armed() -> bool:
    """فلگ + Gate 0. بدون این، pull خالی/۵۰۳ است."""
    return flag_on() and gate0_ready()


def bearer_ok(header_val: str) -> bool:
    expected = str(os.environ.get("OCTOPUS_BOARD_CP_BEARER", "")).strip()
    if not expected:
        return False
    got = str(header_val or "").strip()
    if got.lower().startswith("bearer "):
        got = got[7:].strip()
    if not got:
        return False
    return hmac.compare_digest(got.encode("utf-8"), expected.encode("utf-8"))
