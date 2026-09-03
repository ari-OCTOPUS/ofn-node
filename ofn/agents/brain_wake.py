"""brain_wake — پیوند قلب→مغز (P3 از HARMONY-MERGER، فرمان مالک «بریم پیوند»).

وقتی رویدادِ بیزینسیِ جدی روی ۱۳۸ رخ می‌دهد (پرداخت وریفای، سفارش، لیدِ
تازه)، این ماژول یک `cognitive_wake.v1` واقعی به outbox مش می‌نویسد تا
octopus-mesh-send (تایمر ساعتی موجود) آن را به مغز ۱۸۰ برساند — همان
فرمتِ اثبات‌شده با ۲۲/۲۲ ACK. ۱۸۰ با لامای محلی فکر می‌کند، ۱۸۲ verify،
۱۳۸ کارت — حلقهٔ سه‌بردی بالاخره با رویداد واقعی چرخید.

قواعد:
  · hold_external=true همیشه — مغز فقط «فکر» می‌کند، ارسال دست مالک
  · may_authorize=false — پیشنهاد، نه اجازه
  · wake_sha256 — اثر انگشت محتوا برای ۱۸۲ (verify بدون دانلود)
  · dedup با wake_id (هر batch یک بار)
  · بدون رویداد جدی = بدون wake (سکوت، نه اسپم)
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

SCHEMA = "octopus.brain-wake.v1"
EVENTS = opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl"
MESH_EVENTS = Path.home() / "octopus-mesh/state/events"
OUTBOX = Path.home() / "octopus-mesh/outbox"
STATE = opslib.STATE_DIR / "brain-wake-state.json"

# رویدادهایی که ارزش بیدارکردن مغز دارند (بقیه = سکوت)
WAKE_WORTHY = frozenset({
    "payment.verified", "payment.claimed",
    "communication.quote_requested",
    "lead.discovered", "order.received",
})


def wake_id(now: datetime) -> str:
    return "CW-" + now.strftime("%Y%m%dT%H%M%SZ")


def build_wake(events: list[dict], now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    businesses = sorted({e.get("correlation_id", "").split(":")[0]
                         or "unknown" for e in events})
    payload = {
        "event_type": "cognitive_wake.v1",
        "wake_id": wake_id(now),
        "run_id": "wake-" + now.strftime("%Y%m%dT%H%M%SZ"),
        "reason": "business_events_batch",
        "businesses": businesses,
        "events_summary": [
            {"type": e["event_type"], "at": e["occurred_at"],
             "lead": e.get("correlation_id")}
            for e in events[:50]
        ],
        "state_refs": [str(EVENTS)],
        "deadline": (now + timedelta(hours=4)).isoformat(),
        "hold_external": True,
        "may_authorize": False,
    }
    payload["wake_sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return payload


def _load_state() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"last_wake_at": None}


def _save_state(d: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")


def _read_recent_events(since_epoch: float) -> list[dict]:
    import datetime as dt
    if not EVENTS.exists():
        return []
    out = []
    for ln in EVENTS.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            e = json.loads(ln)
            if e.get("event_type") not in WAKE_WORTHY:
                continue
            ts = dt.datetime.fromisoformat(
                e["occurred_at"].replace("Z", "+00:00")).timestamp()
            if ts >= since_epoch:
                out.append(e)
        except (ValueError, KeyError, AttributeError):
            continue
    return out


def cycle(state_dir: Path | None = None) -> dict:
    sd = state_dir or (opslib.STATE_DIR)
    st = _load_state()
    since = st.get("last_wake_epoch", 0.0)
    events = _read_recent_events(since)
    if not events:
        return {"schema": SCHEMA, "ok": True, "wake": False,
                "reason": "no fresh business events — silence is honest"}
    now = datetime.now(timezone.utc)
    payload = build_wake(events, now)
    MESH_EVENTS.mkdir(parents=True, exist_ok=True)
    OUTBOX.mkdir(parents=True, exist_ok=True)
    evt_file = MESH_EVENTS / f"{payload['run_id']}.json"
    evt_file.write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    out_file = OUTBOX / f"{payload['run_id']}.json"
    out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    _save_state({"last_wake_at": payload["run_id"],
                 "last_wake_epoch": now.timestamp()})
    return {"schema": SCHEMA, "ok": True, "wake": True,
            "wake_id": payload["wake_id"], "events": len(events),
            "businesses": payload["businesses"],
            "outbox_file": str(out_file),
            "note": "hourly octopus-mesh-send timer will deliver to 180"}


def main() -> int:
    print(json.dumps(cycle(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
