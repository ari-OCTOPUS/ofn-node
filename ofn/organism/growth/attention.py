from __future__ import annotations

import json
from typing import Any

from ofn.organism.growth.habits import set_meta
from ofn.organism.growth.parent import PRESENCE_EVERY_TICKS
from ofn.organism.runtime.public_status import meta_value


THERMAL_ATTENTION_C = 2.0


def _soc_temp_c(snapshot: dict[str, Any]) -> float | None:
    sensors = snapshot.get("sensors") or {}
    item = sensors.get("soc_temp_mC") or {}
    value = item.get("value")
    if isinstance(value, (int, float)):
        return float(value) / 1000.0
    body = (snapshot.get("discovery") or {}).get("body") or {}
    for zone in body.get("thermal_zones") or []:
        temp = zone.get("temp_C")
        if isinstance(temp, (int, float)):
            return float(temp)
    return None


def _arp_ips(snapshot: dict[str, Any]) -> list[str]:
    neighbors = (snapshot.get("discovery") or {}).get("neighbors") or {}
    ips = [str(item.get("ip")) for item in neighbors.get("arp") or [] if item.get("ip")]
    return sorted(set(ips))


def notice_attention(con, snapshot: dict[str, Any]) -> dict[str, Any] | None:
    current = {
        "soc_temp_C": _soc_temp_c(snapshot),
        "arp": _arp_ips(snapshot),
    }
    raw = meta_value(con, "last_attention_json")
    set_meta(con, "last_attention_json", json.dumps(current, sort_keys=True))
    if not raw:
        return None
    try:
        previous = json.loads(raw)
    except json.JSONDecodeError:
        return None
    reasons: list[str] = []
    prev_temp = previous.get("soc_temp_C")
    cur_temp = current.get("soc_temp_C")
    if (
        isinstance(prev_temp, (int, float))
        and isinstance(cur_temp, (int, float))
        and abs(float(cur_temp) - float(prev_temp)) >= THERMAL_ATTENTION_C
    ):
        reasons.append(
            f"soc_temp {float(prev_temp):.1f}C->{float(cur_temp):.1f}C"
        )
    prev_arp = set(previous.get("arp") or [])
    cur_arp = set(current.get("arp") or [])
    added = sorted(cur_arp - prev_arp)
    removed = sorted(prev_arp - cur_arp)
    if added:
        reasons.append("arp_added:" + ",".join(added))
    if removed:
        reasons.append("arp_removed:" + ",".join(removed))
    if not reasons:
        return None
    return {
        "kind": "attention",
        "reasons": reasons,
        "current": current,
        "previous": previous,
    }


def maybe_presence(con, spoke_already: bool) -> bool:
    raw_every = meta_value(con, "presence_every_ticks", str(PRESENCE_EVERY_TICKS))
    try:
        every = max(1, int(raw_every or PRESENCE_EVERY_TICKS))
    except ValueError:
        every = PRESENCE_EVERY_TICKS
    raw_quiet = meta_value(con, "quiet_ticks", "0") or "0"
    try:
        quiet = int(raw_quiet)
    except ValueError:
        quiet = 0
    if spoke_already:
        set_meta(con, "quiet_ticks", "0")
        return False
    quiet += 1
    if quiet >= every:
        set_meta(con, "quiet_ticks", "0")
        raw_count = meta_value(con, "presence_utterances", "0") or "0"
        try:
            count = int(raw_count)
        except ValueError:
            count = 0
        set_meta(con, "presence_utterances", str(count + 1))
        return True
    set_meta(con, "quiet_ticks", str(quiet))
    return False
