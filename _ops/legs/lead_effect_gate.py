#!/usr/bin/env python3
"""lead_effect_gate.py — Trust-Engine P0 · LEAD-SAFETY-C1: گیتِ per-effect برای ارسالِ لید.

می‌بندد footgunِ ایمنیِ حیاتی که فورنسیک/کارتوگرافی گرفتند: `chrono.release_gated_effects`
با یک رأیِ انسانی **همهٔ** effectهای pending را releasable می‌کند (batch). برای پولِ تلگرام امن،
برای **ارسالِ به مشتری فاجعه** است (یک تأیید = هر ارسالِ pending آزاد شود). این ماژول، همراهِ
`chrono.release_one` (per-effect) و `effector_gate_bridge` (staleness)، ارسالِ لید را
**یکی-یکی، صریح، fail-closed** می‌کند.

قاعده‌ها (همه fail-closed، دفاع در عمق):
  1. STOP / master-halt / FREEZE → deny.
  2. gate/context غایب → deny (هرگز crash، هرگز send).
  3. **بازبینیِ دوبارهٔ رده‌ی رضایت (R4):** market_signal هرگز؛ synthetic_test هرگز؛ بدونِ
     outreach_allowed → deny. (دفاعِ دومِ مستقل از inbox.)
  4. **authorizationِ صریحِ per-effect:** فقط effect_idهایی که رأیِ مالک صریحاً authorize کرده
     آزاد می‌شوند. allowlist پیش‌فرض خالی → هیچ‌چیز بدونِ رأی آزاد نمی‌شود.
  5. idempotent: effectِ settled/refused دوباره release نمی‌شود.

هرگز چیزی نمی‌فرستد (ارسالِ واقعی کارِ outbound_worker است که فقط stubِ NOT_ARMED دارد).
stdlib-only. flag خاموش = بی‌اثر (این‌جا flag ندارد؛ خودِ outbound_worker پشتِ فلگ است).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib               # noqa: E402
import consent_firewall as cf   # noqa: E402


def _authz_store() -> Path:
    return opslib.STATE_DIR / "legs" / "lead-effect-authz.json"


def _events() -> Path:
    return opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl"


def _load_authz() -> dict:
    try:
        return json.loads(_authz_store().read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def _save_authz(idx: dict) -> None:
    try:
        _authz_store().parent.mkdir(parents=True, exist_ok=True)
        tmp = _authz_store().with_suffix(".json.tmp")
        tmp.write_text(json.dumps(idx, ensure_ascii=False), "utf-8")
        os.replace(tmp, _authz_store())
    except (OSError, TypeError, ValueError):
        pass   # fail-soft: نبودِ ثبت → may_release محافظه‌کارانه deny می‌کند


def _emit(event_type: str, corr: str, payload: dict) -> None:
    import uuid
    try:
        opslib.append_jsonl(_events(), {
            "event_id": uuid.uuid4().hex, "event_type": event_type,
            "occurred_at": opslib.now_iso(), "correlation_id": corr,
            "source_component": "LeadEffectGate", "schema_version": "1.0", "payload": payload})
    except Exception:  # noqa: BLE001
        pass


def _halt_reason() -> str | None:
    try:
        return (opslib.master_halted() or opslib.halted()
                or ("STOP-ORGANISM" if opslib.STOP_ORGANISM.exists() else None)
                or ("FREEZE" if opslib.frozen() else None))
    except Exception:  # noqa: BLE001 — هر خطا در سنجشِ halt → fail-closed (halt فرض کن)
        return "halt_probe_error"


def authorize(effect_id: str, lead_id: str, decision_token: str, *, now_ms: int | None = None) -> dict:
    """رأیِ مالک را برای **یک** effect ثبت کن (allowlistِ per-effect). idempotent.
    فقط پس از این، may_release می‌تواند اجازه دهد. token = ردِ همان رأیِ انسانی (release_ref)."""
    eid = str(effect_id or "").strip()
    tok = str(decision_token or "").strip()
    if not eid or not tok:
        return {"ok": False, "reason": "effect_id/token required"}
    idx = _load_authz()
    if eid in idx:                    # idempotent — دوباره authorize همان است
        return {"ok": True, "reason": "already_authorized", "effect_id": eid}
    import time
    idx[eid] = {"lead_id": str(lead_id or ""), "token": tok,
                "authorized_at": int(now_ms if now_ms is not None else time.time() * 1000)}
    _save_authz(idx)
    _emit("proposal.owner_approved", eid, {"lead_id": lead_id, "kind": "lead_effect_authorized"})
    return {"ok": True, "reason": "authorized", "effect_id": eid}


def is_authorized(effect_id: str) -> bool:
    return str(effect_id or "").strip() in _load_authz()


def _authz_token(effect_id: str) -> str | None:
    rec = _load_authz().get(str(effect_id or "").strip())
    return rec.get("token") if isinstance(rec, dict) else None


def may_release(effect_id: str, candidate: dict, *, gate=None) -> dict:
    """رأیِ نهاییِ آزادسازی — هرگز استثنا، همیشه dict با `allow`. fail-closed مطلق.

    خروجی: {allow: bool, reason: str, status?: str}
    """
    try:
        eid = str(effect_id or "").strip()
        # ۱) kill-switch مقدم
        kill = _halt_reason()
        if kill:
            return {"allow": False, "reason": f"halted:{kill}"}
        # ۲) gate/context الزامی (fail-closed)
        if gate is None or not eid:
            return {"allow": False, "reason": "no_gate_or_effect"}
        # ۳) بازبینیِ دوبارهٔ رده‌ی رضایت — دفاع در عمق (R4)
        ctype = cf.classify(candidate if isinstance(candidate, dict) else {})
        if ctype == "market_signal":
            return {"allow": False, "reason": "market_signal_never_sends"}
        # channel را دقیقاً مثلِ classify نرمال می‌کنیم (strip) + casefold — راستی‌آزماییِ متخاصمِ
        # 2026-07-21 نشان داد مقایسهٔ خامِ ' synthetic_test' (فاصله/تب/newline) گارد را دور می‌زد.
        channel = str(((candidate or {}).get("source") or {}).get("channel") or "").strip().casefold()
        if channel == "synthetic_test":
            return {"allow": False, "reason": "synthetic_never_sends"}
        if not cf.may_outreach(candidate if isinstance(candidate, dict) else {}):
            return {"allow": False, "reason": "outreach_not_allowed"}
        # ۴) authorizationِ صریحِ per-effect (allowlist؛ پیش‌فرض خالی)
        if not is_authorized(eid):
            return {"allow": False, "reason": "not_authorized"}
        # ۵) idempotency: settled/refused دوباره release نمی‌شود
        try:
            st = gate.status_of(eid)
        except Exception as e:  # noqa: BLE001
            return {"allow": False, "reason": f"status_error:{type(e).__name__}"}
        if st in ("settled", "refused"):
            return {"allow": False, "reason": f"already_{st}"}
        if st is None:
            return {"allow": False, "reason": "unknown_effect"}
        return {"allow": True, "reason": "ok", "status": st}
    except Exception as e:  # noqa: BLE001 — هر خطای غیرمنتظره → deny
        return {"allow": False, "reason": f"exception:{type(e).__name__}"}


def release_and_settle(effect_id: str, candidate: dict, *, gate, now_ms: int | None = None) -> dict:
    """اگر may_release اجازه داد: **یک** effect را release_one کن، release_ts ثبت کن، و با
    گاردِ stalenessِ effector_gate_bridge settle کن. هرگز batch، هرگز send. همیشه dict.

    خروجی: {released: bool, settled: bool, reason: str}
    """
    verdict = may_release(effect_id, candidate, gate=gate)
    if not verdict.get("allow"):
        return {"released": False, "settled": False, "reason": verdict.get("reason", "deny")}
    eid = str(effect_id).strip()
    token = _authz_token(eid) or ""
    # per-effect release (نه batch)
    try:
        released = bool(gate.release_one(eid, {"hash": token}))
    except Exception as e:  # noqa: BLE001
        return {"released": False, "settled": False, "reason": f"release_error:{type(e).__name__}"}
    if not released:
        return {"released": False, "settled": False, "reason": "release_one_failed"}
    # staleness-guarded settle از مسیرِ bridge (chrono دست‌نخورده)
    try:
        import effector_gate_bridge as egb   # noqa: WPS433 — lazy، هم‌پوشهٔ legs
        egb.mark_released(eid, now_ms=now_ms)
        res = egb.settle_fresh(gate, eid, now_ms=now_ms)
        _emit("effect.released", eid, {"settled": res.get("settled"), "reason": res.get("reason")})
        return {"released": True, "settled": bool(res.get("settled")),
                "reason": res.get("reason", "")}
    except Exception as e:  # noqa: BLE001
        return {"released": True, "settled": False, "reason": f"settle_error:{type(e).__name__}"}


if __name__ == "__main__":
    print(json.dumps({"note": "per-effect gate — authorize→may_release→release_and_settle؛ "
                              "هرگز batch، هرگز send. transport = outbound_worker (stub NOT_ARMED)."},
                     ensure_ascii=False))
