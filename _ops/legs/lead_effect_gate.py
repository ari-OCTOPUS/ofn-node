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


def list_authorized() -> list:
    """فهرستِ **فقط‌خواندنیِ** allowlist ِ per-effect (بازبینی ۰۷-۳۱ — برای
    درایورِ outbound_worker.drive_outbound). token هرگز بیرون داده نمی‌شود.
    خروجی: [{"effect_id": str, "lead_id": str}] — ترتیبِ درجِ store."""
    out = []
    for eid, rec in _load_authz().items():
        if isinstance(rec, dict):
            out.append({"effect_id": str(eid),
                        "lead_id": str(rec.get("lead_id") or "")})
    return out


def _authorized_effect_for_lead(lead_id: str) -> str | None:
    """effect_idِ قبلاً authorize‌شده برای این lead_id، یا None. مبنای idempotencyِ per-lead."""
    lid = str(lead_id or "").strip()
    if not lid:
        return None
    for eid, rec in _load_authz().items():
        if isinstance(rec, dict) and rec.get("lead_id") == lid:
            return eid
    return None


def _authz_token(effect_id: str) -> str | None:
    rec = _load_authz().get(str(effect_id or "").strip())
    return rec.get("token") if isinstance(rec, dict) else None


def may_release(effect_id: str, candidate: dict, *, gate=None, now=None) -> dict:
    """رأیِ نهاییِ آزادسازی — هرگز استثنا، همیشه dict با `allow`. fail-closed مطلق.

    `now` (ثانیه، تزریق‌پذیر) فقط برای چکِ سقفِ روزانه است (رأی مالک ۲۰۲۶-۰۷-۳۱: ۱۰).

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
        # ۴٫۵) سقفِ روزانهٔ عددی (رأی مالک ۲۰۲۶-۰۷-۳۱: LEAD_DAILY_SEND_CAP=10) —
        # دفاع در عمق: لایهٔ اولِ deny این‌جاست تا effect ِ سقف‌خورده releasable بمانَد
        # و پس از rollover ِ نیمه‌شب دوباره بتواند برود. لایهٔ دوم در خودِ worker.
        try:
            import outbound_worker as _ow   # noqa: WPS433 — lazy، هم‌پوشه
            if _ow.cap_reached(now=now):
                return {"allow": False, "reason": "daily-cap"}
        except Exception:  # noqa: BLE001 — شمارِ نامعلوم = fail-closed (ارسال ممنوع)
            return {"allow": False, "reason": "cap_probe_error"}
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


def on_lead_verdict(lead_id: str, candidate: dict, verdict: str, *, gate) -> dict:
    """بریجِ effect-layer: رأیِ **approve**ِ owner روی یک لید → ساختِ یک effectِ `lead_outbound`
    و authorizeِ per-effect آن. این **جدا از measurement** است (verdict_recorder اصلِ
    «سنجش ≠ اثر» را نگه می‌دارد و structurally بدونِ effector است؛ این‌جا لایهٔ اثر است).

    هرگز نمی‌فرستد (transport = outbound_worker که NOT_ARMED است). rejected/deferred → هیچ.
    consent دوباره چک می‌شود: market_signal/synthetic هرگز effectِ authorize‌شده نمی‌گیرند.
    fail-closed مطلق؛ همیشه dict. نقطهٔ اتصالِ live: دکمهٔ کارتِ لید این را (پشتِ فلگ) صدا می‌زند
    — که همان نقطهٔ arm است (owner-gated).

    خروجی: {authorized: bool, effect_id?: str, reason: str}
    """
    try:
        v = str(verdict or "").strip().lower()
        if v not in ("approve", "approved", "ok", "yes", "accept", "accepted"):
            return {"authorized": False, "reason": f"non_approve_verdict:{v}"}
        if gate is None or not str(lead_id or "").strip():
            return {"authorized": False, "reason": "no_gate_or_lead"}
        kill = _halt_reason()
        if kill:
            return {"authorized": False, "reason": f"halted:{kill}"}
        # consent re-check (دفاع در عمق، R4): سیگنال/synthetic هرگز effectِ authorize‌شده نمی‌گیرند
        ctype = cf.classify(candidate if isinstance(candidate, dict) else {})
        if ctype == "market_signal":
            return {"authorized": False, "reason": "market_signal_never_sends"}
        channel = str(((candidate or {}).get("source") or {}).get("channel") or "").strip().casefold()
        if channel == "synthetic_test":
            return {"authorized": False, "reason": "synthetic_never_sends"}
        # F2 (راستی‌آزماییِ متخاصم): outreach باید مجاز باشد — هم‌راستا با may_release تا لیدی که
        # هرگز نمی‌تواند قانوناً بفرستد (مثلِ consent.basis=none) effectِ authorize‌شده و رویدادِ
        # approved نگیرد (وضعیتِ گیج‌کننده + arm بی‌مورد).
        if not cf.may_outreach(candidate if isinstance(candidate, dict) else {}):
            return {"authorized": False, "reason": "outreach_not_allowed"}
        lid = str(lead_id).strip()
        # F1 (راستی‌آزماییِ متخاصم): idempotency keyed on lead_id — یک لید فقط **یک** effectِ
        # outbound می‌گیرد. وگرنه double-tap/retry/webhookِ تکراری = N effectِ authorize‌شده =
        # N ارسال به همان مشتری وقتی مسلح شود. درسِ «کلید روی تصمیم، نه پاسخ».
        existing = _authorized_effect_for_lead(lid)
        if existing is not None:
            return {"authorized": True, "effect_id": existing, "reason": "already_authorized_for_lead"}
        import uuid
        eid = gate.request("lead_outbound", lid, beat=None)
        token = "owner-verdict-" + uuid.uuid4().hex[:12]
        res = authorize(eid, lid, token)
        return {"authorized": bool(res.get("ok")), "effect_id": eid, "reason": res.get("reason")}
    except Exception as e:  # noqa: BLE001 — هرگز مسیرِ verdict را نمی‌کشد
        return {"authorized": False, "reason": f"exception:{type(e).__name__}"}


def bridge_from_inbox(lead_id: str, *, gate) -> dict:
    """D1 (فاز D، 2026-07-21): bridge سبک برای لایهٔ wire (live_loop). فایلِ inboxِ یک lead_id
    را می‌خواند، کاندیدِ سازگار با consent-firewall را بازسازی می‌کند، و on_lead_verdict(approve)
    را صدا می‌زند. هم‌الگو با verdict_recorder برای live_loop: کل منطقِ I/O + consent در همین
    ماژول محصور می‌ماند تا live_loop **لایهٔ wireِ خالص** بماند (بدونِ importِ لایهٔ production).

    همهٔ گاردهای on_lead_verdict (consent re-check، idempotency، STOP، fail-closed) اعمال می‌شوند.
    هرگز settle/send/ledger نمی‌زند؛ فقط یک effectِ lead_outbound می‌سازد و authorize می‌کند
    (transportش در outbound_worker هنوز NOT_ARMED است — این D1 است، نه D7).

    خروجی: {authorized: bool, effect_id?, reason: str} — همیشه dict، هرگز استثنا.
      · lead_id خالی/فایل غایب → {authorized: False, reason: "no_inbox_file"}
      · gate غایب → on_lead_verdict fail-closed {authorized: False, reason: "no_gate_or_lead"}
    """
    try:
        lid = str(lead_id or "").strip()
        if not lid:
            return {"authorized": False, "reason": "no_inbox_file"}
        path = opslib.STATE_DIR / "legs" / "lead-inbox" / f"{lid}.json"
        if not path.exists():
            return {"authorized": False, "reason": "no_inbox_file"}
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return {"authorized": False, "reason": "no_inbox_file"}
        cb = data.get("candidate") or {}
        candidate = {
            "source": {"channel": data.get("source")},
            "candidate_type": cb.get("candidate_type"),
            "consent": cb.get("consent") or {},
            "request": cb.get("request") or {},
            # (۲۰۲۶-۰۷-۳۱) contact ِ حفظ‌شده در فایلِ inbox عبور می‌کند تا transport
            # گیرنده داشته باشد؛ نبودش = NO_RECIPIENT ِ صادقِ همان لایه.
            "contact": cb.get("contact") or {},
        }
        return on_lead_verdict(lid, candidate, "approve", gate=gate)
    except Exception as e:  # noqa: BLE001 — bridge هرگز caller را نمی‌کشد
        return {"authorized": False, "reason": f"exception:{type(e).__name__}"}


def release_and_settle(effect_id: str, candidate: dict, *, gate, now_ms: int | None = None) -> dict:
    """اگر may_release اجازه داد: **یک** effect را release_one کن، release_ts ثبت کن، و با
    گاردِ stalenessِ effector_gate_bridge settle کن. هرگز batch، هرگز send. همیشه dict.

    خروجی: {released: bool, settled: bool, reason: str}
    """
    verdict = may_release(effect_id, candidate, gate=gate,
                          now=(float(now_ms) / 1000.0 if now_ms is not None else None))
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


# ── D6 (فاز D): جداسازیِ release از send برای staleness واقعی ──────────────────
# WIRING-HANDOFF §۳ «ضعفِ صادقانه»: release_and_settle فعلی اتمیک است (همان now_ms)، پس
# گاردِ stalenessِ effector_gate_bridge عملاً بی‌اثر است. این دو تابع، release را در t0 و
# settle را در t1 (ممکن است دیرتر) انجام می‌دهند تا staleness واقعی کار کند: اگر t1-t0>window
# → settle_fresh refuse می‌کند (effect کهنه نمی‌تواند settle شود).
# این مسیر هنوز NOT_ARMED است (transport در D7 وصل می‌شود). ولی ستاپِ ایمن برای staleness.


def release_only(effect_id: str, candidate: dict, *, gate, now_ms: int | None = None) -> dict:
    """D6: فقط release (در t0) — بدونِ settle. نقطهٔ اولِ جداسازی.
    may_release را چک می‌کند، اگر اجازه داد release_one + mark_released (در t0).
    خروجی: {released: bool, reason: str, released_at_ms?: int}
    هرگز settle/send. caller بعداً settle_after_release را (در t1) صدا می‌زند."""
    verdict = may_release(effect_id, candidate, gate=gate,
                          now=(float(now_ms) / 1000.0 if now_ms is not None else None))
    if not verdict.get("allow"):
        return {"released": False, "reason": verdict.get("reason", "deny")}
    eid = str(effect_id).strip()
    token = _authz_token(eid) or "owner-verdict-release"
    try:
        import effector_gate_bridge as egb   # noqa: WPS433 — lazy
        released = bool(gate.release_one(eid, {"hash": token}))
        if not released:
            return {"released": False, "reason": "release_one_failed"}
        t0 = int(now_ms if now_ms is not None else _now_ms())
        egb.mark_released(eid, now_ms=t0)
        _emit("effect.released", eid, {"settled": False, "phase": "release_only",
                                       "released_at_ms": t0})
        return {"released": True, "reason": "ok", "released_at_ms": t0}
    except Exception as e:  # noqa: BLE001
        return {"released": False, "reason": f"release_error:{type(e).__name__}"}


def settle_after_release(effect_id: str, *, gate, now_ms: int | None = None,
                         max_age_hours: float | None = None) -> dict:
    """D6: فقط settle (در t1) — با گاردِ stalenessِ واقعی. نقطهٔ دومِ جداسازی.
    اگر now_ms (t1) − release_ts (t0) > window → stale_refused.
    خروجی: {settled: bool, reason: str, age_hours?: float}
    هرگز send. این مسیر برای وقتی است که send از release جدا شده (transport آینده)."""
    eid = str(effect_id).strip()
    try:
        import effector_gate_bridge as egb   # noqa: WPS433 — lazy
        res = egb.settle_fresh(gate, eid, now_ms=now_ms, max_age_hours=max_age_hours)
        _emit("effect.settled", eid, {"settled": res.get("settled"),
                                       "reason": res.get("reason", ""),
                                       "age_hours": res.get("age_hours")})
        return {"settled": bool(res.get("settled")), "reason": res.get("reason", ""),
                "age_hours": res.get("age_hours")}
    except Exception as e:  # noqa: BLE001
        return {"settled": False, "reason": f"settle_error:{type(e).__name__}"}


def _now_ms() -> int:
    """UTC millis (هم‌الگو با chrono._utc_ms)."""
    import time as _t   # noqa: WPS433
    return int(_t.time() * 1000)


if __name__ == "__main__":
    print(json.dumps({"note": "per-effect gate — authorize→may_release→release_and_settle؛ "
                              "هرگز batch، هرگز send. transport = outbound_worker (stub NOT_ARMED)."},
                     ensure_ascii=False))
