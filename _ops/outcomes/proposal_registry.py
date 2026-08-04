#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""proposal_registry.py — GAP-2: رجیستریِ durableِ تحویلِ کارتِ پیشنهاد + بازسازیِ meta از توکن.

نقش در رستاخیز (C2-B): توکنِ stateless فقط (pid12, exp, sig) دارد؛ برای ثبتِ رأی بعد از
restart باید metaی کامل (proposal_id, leg_id, amount, correlation, lead) از یک SoTِ durable
بازسازی شود. آن SoT همین‌جاست: رویدادِ `delivered` در **outcomes.db** (event_type مجازِ
taxonomy؛ producer=تحویلِ کارت — جدا از رأی که verdict_recorder می‌نویسد).

قیود:
  - پشتِ همان `OCTOPUS_WIRE_VERDICT_OUTCOME` (فلگِ نویسندهٔ outcomes) — **فلگ جدید نمی‌سازیم.**
  - idempotent: کلیدِ `deliv|<proposal_id>` → تحویل/بازتحویلِ تکراری = ردیفِ نو نوشته نمی‌شود.
  - fail-soft در نوشتن (تحویل هرگز به‌خاطرِ ثبت نمی‌میرد)؛ fail-closed در resolve
    (توکنِ ناشناخته/منقضی/جعلی/غیرمالک → None + دلیل).
  - صفر ledger/effector/approval/settle/pay — فقط outcomes.db (measurement).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _bootstrap_paths() -> None:
    for _p in (str(_HERE), str(_HERE.parent), str(_HERE.parent / "budget"),
               str(_HERE.parent / "spine")):
        if _p not in sys.path:
            sys.path.insert(0, _p)


def flag_on() -> bool:
    return str(os.environ.get("OCTOPUS_WIRE_VERDICT_OUTCOME", "")).strip().lower() in (
        "1", "true", "yes", "on")


def _default_state_dir() -> "Path | None":
    try:
        _bootstrap_paths()
        import opslib  # noqa: WPS433
        return Path(opslib.STATE_DIR)
    except Exception:  # noqa: BLE001
        return None


def _open_store(state_dir: "Path | None" = None, create: bool = False):
    """OutcomeStore روی state/outcomes/outcomes.db (یا state_dir صریح در تست)."""
    _bootstrap_paths()
    import outcome_store as _osx  # noqa: WPS433
    root = Path(state_dir) if state_dir is not None else _default_state_dir()
    if root is None:
        return None
    db = root / "outcomes" / "outcomes.db"
    if not create and not db.exists():
        return None
    db.parent.mkdir(parents=True, exist_ok=True)
    return _osx.OutcomeStore(path=db)


def record_delivery_durably(meta: dict, *, state_dir=None) -> dict:
    """تحویلِ کارت را durable کن (event_type=delivered، idempotent). fail-soft.
    خروجی: {recorded, reason?} — recorded=False روی flag-off/تکرار/خطا (هرگز raise)."""
    if not flag_on():
        return {"recorded": False, "reason": "flag-off"}
    pid = str((meta or {}).get("proposal_id") or "")
    if not pid:
        return {"recorded": False, "reason": "no-proposal-id"}
    store = None
    try:
        _bootstrap_paths()
        import proposal_token as _pt  # noqa: WPS433
        store = _open_store(state_dir, create=True)
        if store is None:
            return {"recorded": False, "reason": "no-state-dir"}
        payload = {k: meta.get(k) for k in ("proposal_id", "amount", "kind", "leg_id",
                                            "correlation_id", "mission_id", "lead_id")}
        payload["pid12"] = _pt.pid12(pid)
        corr = str(meta.get("correlation_id") or ("prop_" + pid))
        wrote = bool(store.record({
            "correlation_id": corr, "mission_id": str(meta.get("mission_id") or ""),
            "proposal_id": pid, "leg_id": str(meta.get("leg_id") or "unknown"),
            "lead_id": (str(meta.get("lead_id")) if meta.get("lead_id") else None),
            "event_type": "delivered", "verdict": None, "value_aud_claimed": 0.0,
            "idempotency_key": f"deliv|{pid}", "payload": payload}))
        return {"recorded": wrote}
    except Exception as e:  # noqa: BLE001 — ثبتِ تحویل هرگز تحویل را نمی‌کشد
        return {"recorded": False, "reason": f"durable-error: {type(e).__name__}"}
    finally:
        try:
            if store is not None:
                store.close()
        except Exception:  # noqa: BLE001
            pass


def _find_delivery(store, want_pid12: str) -> "dict | None":
    """metaی تحویل‌شده با pid12 — جدیدترین اول. None = ناشناخته."""
    _bootstrap_paths()
    import proposal_token as _pt  # noqa: WPS433
    rows = store._conn.execute(   # noqa: SLF001 — read-only projection query
        "SELECT proposal_id, payload_json FROM outcomes "
        "WHERE event_type='delivered' ORDER BY recorded_at DESC").fetchall()
    for pid, payload_json in rows:
        if _pt.pid12(pid) != want_pid12:
            continue
        try:
            payload = json.loads(payload_json or "{}")
        except ValueError:
            payload = {}
        meta = {k: payload.get(k) for k in ("proposal_id", "amount", "kind", "leg_id",
                                            "correlation_id", "mission_id", "lead_id")}
        meta["proposal_id"] = meta.get("proposal_id") or str(pid)
        return meta
    return None


def _already_decided(store, proposal_id: str) -> bool:
    # ⚠️ ۲۰۲۶-۰۸-۰۵: این تاپل قبلاً **درجا نوشته شده** بود و `owner-decision`
    # را نمی‌شناخت، پس پیشنهادی که مالک در وب‌اپ تأیید کرده بود از دکمهٔ
    # تلگرام دوباره «تصمیم‌گیری‌نشده» دیده می‌شد — یک سوراخِ تصمیمِ دوگانهٔ
    # واقعی روی دادهٔ زنده. حالا از تعریفِ واحدِ taxonomy می‌خواند.
    try:
        from .taxonomy import DECIDED_EVENT_TYPES  # noqa: WPS433
    except ImportError:  # pragma: no cover — اجرای مسطح (بدونِ بسته)
        from taxonomy import DECIDED_EVENT_TYPES   # type: ignore  # noqa: WPS433
    marks = ",".join("?" for _ in DECIDED_EVENT_TYPES)
    row = store._conn.execute(   # noqa: SLF001
        f"SELECT 1 FROM outcomes WHERE proposal_id=? "
        f"AND event_type IN ({marks}) LIMIT 1",
        (str(proposal_id), *DECIDED_EVENT_TYPES)).fetchone()
    return row is not None


def resolve_stateless(token, from_id, *, state_dir=None, now=None) -> "tuple[dict | None, str]":
    """توکنِ pb1 بعد از restart → metaی کامل. **fail-closed در همهٔ شاخه‌ها.**
    (meta, "ok") فقط وقتی: قالب معتبر + تحویلِ ثبت‌شده + HMAC معتبر (bind به pid کامل +
    expiry + owner=from_id) + هنوز تصمیم‌گیری‌نشده. در غیر این صورت (None, دلیل)."""
    store = None
    try:
        _bootstrap_paths()
        import proposal_token as _pt  # noqa: WPS433
        parsed = _pt.parse(token)
        if parsed is None:
            return (None, "bad-format")
        want_pid12, _exp = parsed
        store = _open_store(state_dir, create=False)
        if store is None:
            return (None, "no-registry")
        meta = _find_delivery(store, want_pid12)
        if meta is None:
            return (None, "unknown-card")
        ok, reason = _pt.verify(token, meta["proposal_id"], from_id, now=now)
        if not ok:
            return (None, reason)
        if _already_decided(store, meta["proposal_id"]):
            return (None, "already-decided")
        return (meta, "ok")
    except Exception as e:  # noqa: BLE001 — resolve هرگز threadِ poller را نمی‌کشد
        return (None, f"resolve-error: {type(e).__name__}")
    finally:
        try:
            if store is not None:
                store.close()
        except Exception:  # noqa: BLE001
            pass
