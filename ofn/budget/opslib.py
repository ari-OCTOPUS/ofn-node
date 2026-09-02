"""opslib — شیمِ بومیِ بورد برای پاهای کپی‌شده از خزانه (2026-08-31).

پاهای lead_outbound_transport / outbound_worker از خزانه آمده‌اند و چهار
تابع از opslib می‌خواهند. این شیم همان قرارداد را روی بورد می‌دهد، با
یک تفاوتِ آگاهانه: اقتدارِ halt، همان اوراکلِ واحدِ بورد است —
env=HALT_SURVIVAL_LOOP=1 یا فایلِ ~/ofn/HALT-ALL — نه kill-فایل‌های
ویندوزیِ خزانه (تک‌اوراکل، نه اوراکلِ دوم).
fail-closed: نبودِ دایرکتوریِ خانه → halted.
"""
from __future__ import annotations

import datetime as _dt
import json as _json
import os as _os
from pathlib import Path as _P

HOME = _P(_os.path.expanduser("~"))
OFN_ROOT = HOME / "ofn"
STATE_DIR = OFN_ROOT / "data" / "state"
HALT_FLAG = OFN_ROOT / "HALT-ALL"
ALERTS_JSONL = OFN_ROOT / "data" / "octopus-alerts.jsonl"


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def master_halted() -> str | None:
    """None=اجازه؛ متنِ دلیل=توقف. fail-closed."""
    try:
        if _os.environ.get("HALT_SURVIVAL_LOOP") == "1":
            return "HALT_SURVIVAL_LOOP=1"
        if HALT_FLAG.exists():
            return f"halt-flag:{HALT_FLAG}"
        return None
    except Exception as e:  # noqa: BLE001
        return f"halt-check-error:{type(e).__name__}"


def append_jsonl(path, obj: dict) -> None:
    p = _P(str(path))
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8", newline="\n") as f:
        f.write(_json.dumps(obj, ensure_ascii=False) + "\n")


def alert(lines) -> None:
    if isinstance(lines, str):
        lines = [lines]
    append_jsonl(ALERTS_JSONL, {"ts": now_iso(), "kind": "alert",
                                "lines": [str(x) for x in lines]})
