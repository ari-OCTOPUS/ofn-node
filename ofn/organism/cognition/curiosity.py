from __future__ import annotations

from typing import Any

from ofn.organism.cognition.learn import already_learned
from ofn.organism.memory.gate import MemoryUnavailable, require_memory_gate


def propose_curiosity(snapshot: dict[str, Any], con) -> str | None:
    try:
        require_memory_gate(con, "curiosity")
    except MemoryUnavailable:
        return None
    senses = (snapshot.get("discovery") or {}).get("senses") or {}
    place = snapshot.get("place") or {}
    hosts = snapshot.get("world_hosts") or []
    candidates: list[str] = []
    if senses.get("microphone") in {"CAPTURE_DEVICE_PRESENT", "ES8323_CAPTURE"}:
        candidates.append("کدک صوتی ES8323 / ES8388 روی برد چیست و capture یعنی چه")
    if place.get("wlan0_operstate") == "down":
        candidates.append("وقتی wlan0 روی لینوکس down است معمولاً یعنی چه")
    family = [
        item for item in hosts
        if item.get("given_name") == "همسایه-هم‌خانواده" or "138" in str(item.get("ip") or "")
    ]
    if family:
        candidates.append("OUI مشترک در MAC آدرس چه معنایی دارد")
    if senses.get("camera") == "NOT_FOUND":
        candidates.append("تفاوت دوربین V4L2 با خروجی HDMI روی برد ARM چیست")
    if senses.get("gps") == "NOT_FOUND":
        candidates.append("تفاوت گیرنده ماهواره‌ای مکان با تخمین مکان از نشانی اینترنت چیست")
    candidates.append("Orange Pi 5 Pro با SoC RK3588 چه جور بردی است")
    for item in candidates:
        if already_learned(con, item) is None:
            return item
    return None
