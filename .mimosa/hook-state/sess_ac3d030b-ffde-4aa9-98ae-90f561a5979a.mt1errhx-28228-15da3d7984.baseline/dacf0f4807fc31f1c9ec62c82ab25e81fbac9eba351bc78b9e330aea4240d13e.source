"""mining_stop_intent — مکانیزمِ ثبتِ نیتِ توقفِ نودهای ماینینگ.

D-014: دکمهٔ توقف واقعی نودها — ولی از مسیرِ ثبت نیت، نه دستور مستقیم (D-20).
فایل حالت اتمیک: _ops/state/mining-stop-intent.json
هیچ SSH، هیچ شبکه، هیچ دسترسی مستقیم به نود.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

# ─── تنظیمات ────────────────────────────────────────────────────────────────
_MAX_HISTORY = 20


def _path() -> Path:
    """مسیر فایل حالت. env var برای تست."""
    return Path(os.environ.get(
        "OCTOPUS_MINING_STOP_INTENT_FILE",
        Path(__file__).resolve().parent.parent / "state" / "mining-stop-intent.json",
    ))


def _now_iso(now: float | None = None) -> str:
    ts = now if now is not None else datetime.now(timezone.utc).timestamp()
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _atomic_write(path: Path, data: dict) -> None:
    """نوشتن اتمیک: .json.tmp + os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    os.replace(tmp, path)


def _load_state() -> dict:
    """خواندن فایل حالت. fail-soft: اگر فایل نبود یا خراب بود، دیکت خالی."""
    p = _path()
    if not p.exists():
        return {"history": []}
    try:
        text = p.read_text("utf-8")
        data = json.loads(text)
        if "history" not in data:
            data["history"] = []
        return data
    except Exception:
        return {"history": []}


# ─── API صادرشده ────────────────────────────────────────────────────────────

def register_stop_intent(*, reason: str = "", now: float | None = None) -> dict:
    """یک نیت توقف تازه ثبت می‌کند."""
    state = _load_state()
    intent = {
        "registered_at": _now_iso(now),
        "reason": reason,
        "acknowledged_nodes": [],
        "acked_count": 0,
    }
    state["history"].append(intent)
    # سقف ۲۰
    if len(state["history"]) > _MAX_HISTORY:
        state["history"] = state["history"][-_MAX_HISTORY:]
    _atomic_write(_path(), state)
    return intent


def acknowledge(leg_or_node: str, *, now: float | None = None) -> dict:
    """وقتی نودی تأیید کرد. امروز هیچ صداکننده‌ای ندارد — فقط در تست."""
    state = _load_state()
    if not state["history"]:
        return status()
    latest = state["history"][-1]
    if leg_or_node not in latest["acknowledged_nodes"]:
        latest["acknowledged_nodes"].append(leg_or_node)
    latest["acked_count"] = len(latest["acknowledged_nodes"])
    _atomic_write(_path(), state)
    return status()


def status() -> dict:
    """وضعیت فعلی: latest_intent, acked_count, total_intents."""
    try:
        state = _load_state()
        hist = state.get("history", [])
        if hist:
            latest = hist[-1]
            return {
                "latest_intent": latest,
                "acked_count": latest["acked_count"],
                "total_intents": len(hist),
            }
        return {
            "latest_intent": None,
            "acked_count": 0,
            "total_intents": 0,
        }
    except Exception:
        return {
            "latest_intent": None,
            "acked_count": 0,
            "total_intents": 0,
        }


def stop_card_text(*, now: float | None = None) -> str:
    """متن کارت توقف برای تلگرام (HTML امن، ≤۶ خط). صادقانه."""
    try:
        st = status()
        li = st.get("latest_intent")
        if li is None:
            return "هیچ نیتِ توقفی ثبت نشده"
        acked = li.get("acked_count", 0)
        reason = li.get("reason", "")
        ts = li.get("registered_at", "")
        line1 = f"⏹ نیتِ توقف ثبت شد ({ts[:19]})"
        lines = [line1]
        if reason:
            lines.append(f"دلیل: {reason}")
        lines.append(f"{acked} نود تأیید کرد")
        return "\n".join(lines)
    except Exception:
        return "خطا در خواندن وضعیت"
