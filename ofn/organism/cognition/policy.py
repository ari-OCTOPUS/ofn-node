from __future__ import annotations

import os
import re


DENY = re.compile(
    r"(هوا|weather|باران|forecast|bitcoin|btc|خبر|news|قیمت|geoip|"
    r"lat|lon|مختصات|actuator|armed|telegram|password|api[_-]?key|secret)",
    re.IGNORECASE,
)


def topic_allowed(text: str) -> tuple[bool, str]:
    stripped = " ".join((text or "").split())
    if len(stripped) < 3:
        return False, "too_short"
    if len(stripped) > 240:
        return False, "too_long"
    if DENY.search(stripped):
        return False, "denied_live_or_dangerous"
    return True, "ok"


def extract_learn_topic(text: str) -> str:
    cleaned = " ".join((text or "").strip().split())
    cleaned = re.sub(
        r"^(یاد بگیر|یادبگیر|learn)\s*[:：-]?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned.strip()


def learn_external_enabled() -> bool:
    return os.environ.get("OCTOPUS_LEARN_EXTERNAL") == "1"


def wan_enabled() -> bool:
    return os.environ.get("OCTOPUS_WAN") == "1"
