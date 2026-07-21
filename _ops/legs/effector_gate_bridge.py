#!/usr/bin/env python3
"""effector_gate_bridge.py — Trust-Engine P0: لایهٔ پلِ EffectorGate برای مسیرِ لید.

پُر می‌کند شکافی را که راستی‌آزماییِ متخاصمِ فاز B گرفت (سند 06/00):
`chrono.sweep_stale_effects` فقط `status='pending'` را جارو می‌کند (chrono.py:424)؛ ولی
یک effectِ **releasable** (release شده، settle نشده) را هیچ مکانیزمِ موجودی منقضی نمی‌کند —
پس یک اثرِ تأییدشده می‌توانست هفته‌ها بعد ارسال شود (first-touchِ کهنه). این گاردِ staleness
در **لایهٔ bridge/worker** زندگی می‌کند، **chrono را دست نمی‌زند**، و پیش از settle چک می‌کند.

قاعدهٔ سخت (fail-closed):
  · settle فقط از مسیرِ این پل برای مسیرِ لید — پیش از settle، اگر عمرِ releasable از پنجره
    گذشته → settle نکن، رویدادِ `communication.failed(stale_refused)` + alert.
  · اثباتِ تازگی الزامی است: اگر release_ts ثبت نشده باشد → refuse (نمی‌توان تازگی را اثبات کرد).
  · release فقط پس از رأیِ همان proposal (coarse-release در chrono همهٔ pendingها را با هر
    human-append releasable می‌کند؛ پس این پل هرگز پیش از رأیِ همان proposal، request نمی‌زند
    — مسئولیتِ caller، اینجا مستند).

stdlib-only. هرگز خودش چیزی نمی‌فرستد (settle فقط وضعیتِ گیت را عوض می‌کند؛ ارسالِ واقعی =
workerِ جدا پشتِ OCTOPUS_WIRE_LEAD_OUTBOUND، خارج از این فایل).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib   # noqa: E402


def _now_ms() -> int:
    import time
    return int(time.time() * 1000)


def _release_store() -> Path:
    return opslib.STATE_DIR / "legs" / "effector-release-ts.json"


def _events() -> Path:
    return opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl"


def _stale_hours() -> float:
    """پنجرهٔ O-1 (owner-tunable). پیش‌فرض ۲۴h؛ سقفِ سختِ ۷۲h."""
    try:
        h = float(os.environ.get("OCTOPUS_LEAD_STALE_HOURS", "24"))
    except (TypeError, ValueError):
        h = 24.0
    return min(max(h, 0.0), 72.0)


def _load_ts() -> dict:
    try:
        return json.loads(_release_store().read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def _save_ts(idx: dict) -> None:
    try:
        _release_store().parent.mkdir(parents=True, exist_ok=True)
        tmp = _release_store().with_suffix(".json.tmp")
        tmp.write_text(json.dumps(idx, ensure_ascii=False), "utf-8")
        os.replace(tmp, _release_store())
    except (OSError, TypeError, ValueError):
        pass   # fail-soft: نبودِ ثبت → settle_fresh محافظه‌کارانه refuse می‌کند


def _emit(event_type: str, correlation_id: str, payload: dict) -> None:
    import uuid
    try:
        opslib.append_jsonl(_events(), {
            "event_id": uuid.uuid4().hex, "event_type": event_type,
            "occurred_at": opslib.now_iso(), "correlation_id": correlation_id,
            "source_component": "EffectorGateBridge", "schema_version": "1.0",
            "payload": payload})
    except Exception:  # noqa: BLE001
        pass


def mark_released(effect_id: str, now_ms: int | None = None) -> None:
    """زمانِ release را برای این effect ثبت کن (caller پس از release_gated_effects صدا می‌زند).
    مبنای سنجشِ تازگی است — بدونِ آن، settle_fresh محافظه‌کارانه refuse می‌کند.

    **first-write-wins** (راستی‌آزماییِ متخاصمِ 2026-07-21): اولین زمانِ release مرجعِ قطعی است؛
    re-markِ بعدی نادیده گرفته می‌شود تا یک effectِ کهنه با re-stamp «تازه» نشود (bypassِ گارد)."""
    idx = _load_ts()
    key = str(effect_id)
    if key in idx:
        return   # قبلاً ثبت شده — re-mark تازگیِ جعلی نمی‌سازد
    idx[key] = int(now_ms if now_ms is not None else _now_ms())
    _save_ts(idx)


def settle_fresh(gate, effect_id: str, *, now_ms: int | None = None,
                 max_age_hours: float | None = None) -> dict:
    """settleِ گیت‌شده با گاردِ staleness. هرگز استثنا؛ همیشه dict با `settled`.

    خروجی: {settled: bool, reason: str, age_hours?: float}
    """
    now = int(now_ms if now_ms is not None else _now_ms())
    window_h = _stale_hours() if max_age_hours is None else min(max(max_age_hours, 0.0), 72.0)
    try:
        status = gate.status_of(effect_id)
    except Exception as e:  # noqa: BLE001
        return {"settled": False, "reason": f"status_error:{type(e).__name__}"}
    if status != "releasable":
        # fail-closed: فقط releasable ممکن است settle شود (نه pending/settled/refused/None).
        return {"settled": False, "reason": f"not_releasable:{status}"}

    idx = _load_ts()
    rel_ts = idx.get(str(effect_id))
    if rel_ts is None:
        # اثباتِ تازگی ممکن نیست → refuse (fail-closed).
        _emit("communication.failed", effect_id,
              {"kind": "stale_refused", "reason": "no_release_ts"})
        try:
            opslib.alert([f"effector-bridge: settle refused (no release_ts) eid={effect_id}"])
        except Exception:  # noqa: BLE001
            pass
        return {"settled": False, "reason": "no_release_ts"}

    # release_ts خراب/غیرعددی → refuse (fail-closed، هرگز throw — راستی‌آزماییِ متخاصم).
    try:
        rel_ms = int(rel_ts)
    except (TypeError, ValueError):
        _emit("communication.failed", effect_id, {"kind": "stale_refused", "reason": "bad_release_ts"})
        return {"settled": False, "reason": "bad_release_ts"}

    age_h = (now - rel_ms) / 3_600_000.0
    if age_h < 0:
        # ts آینده (clock-skew/garbage) → تازگی قابلِ اثبات نیست → refuse (نه پذیرشِ عمرِ منفی).
        _emit("communication.failed", effect_id,
              {"kind": "stale_refused", "reason": "future_release_ts", "age_hours": round(age_h, 3)})
        return {"settled": False, "reason": "future_release_ts", "age_hours": round(age_h, 3)}
    if age_h > window_h:
        _emit("communication.failed", effect_id,
              {"kind": "stale_refused", "age_hours": round(age_h, 3),
               "window_hours": window_h})
        try:
            opslib.alert([f"effector-bridge: STALE settle refused eid={effect_id} "
                          f"age={age_h:.1f}h > {window_h:.0f}h"])
        except Exception:  # noqa: BLE001
            pass
        return {"settled": False, "reason": "stale_refused", "age_hours": round(age_h, 3)}

    # تازه است → settleِ واقعیِ گیت (که خودش fail-closed است: kill/release_ref).
    try:
        ok = bool(gate.settle(effect_id))
    except Exception as e:  # noqa: BLE001
        return {"settled": False, "reason": f"settle_error:{type(e).__name__}"}
    if ok:
        # صداقتِ audit (کشفِ دموِ 2026-07-21): settle = «گیت اثر را پاک کرد»، نه «پیام ارسال شد».
        # ارسالِ واقعی کارِ transport (outbound_worker) است که فعلاً NOT_ARMED است. پس این‌جا
        # effect.settled می‌زنیم؛ communication.sent فقط باید از transportِ واقعیِ ارسال‌کننده بیاید
        # (که چون مسلح نیست، هرگز امیت نمی‌شود) — تا لاگ نگوید چیزی فرستاده شد که نفرستاده.
        _emit("effect.settled", effect_id, {"age_hours": round(age_h, 3)})
        idx.pop(str(effect_id), None)   # مصرف‌شده
        _save_ts(idx)
    return {"settled": ok, "reason": "settled" if ok else "gate_refused",
            "age_hours": round(age_h, 3)}
