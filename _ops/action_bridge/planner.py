#!/usr/bin/env python3
"""planner — درخواست → نقشه. تنها جایی که «مجاز است؟» جواب می‌گیرد.

ترتیبِ گیت‌ها عمدی است و از ارزان/قطعی به گران/محتمل می‌رود؛ هر گیت که ببندد،
بقیه اصلاً سنجیده نمی‌شوند:

    ۱ اعتبارِ قرارداد        شکلِ بد = هیچ تصمیمی
    ۲ پیش‌ثبت                عمل بدونِ prereg معتبر اجرا نمی‌شود
    ۳ طبقه‌بندی               ناشناخته = A6
    ۴ محدوده                 مقصد باید داخلِ scope ِ اعلام‌شده باشد
    ۵ idempotency            تکراری = NOOP · payload ِ نو با idِ قدیم = CONFLICT
    ۶ مجوز (فقط A3)          bind + expiry + replay
    ۷ تصمیمِ نهایی

`source_component` هیچ‌جای این زنجیره امتیاز نمی‌گیرد — عمداً. اگر روزی
`world_discovery` (یا هر مولدِ دیگری) بتواند با نامش گیتی را رد کند، کلِ پل یک
لایهٔ تزئینی است.

$0 · stdlib · تابعِ خالص جز `resolve` · صفر نوشتن.
"""
from __future__ import annotations

import classifier
import contracts
import idempotency
import owner_gate
import scope_guard


def plan(req, *, sandbox_root, prereg_lookup=None, ledger=None,
         approval=None, used_nonces=None, now: float = 0.0) -> dict:
    """نقشهٔ عمل. `prereg_lookup(prereg_id) -> dict|None` توسط صداکننده داده
    می‌شود تا این ماژول به `prereg` وابسته نشود (اصلِ بی‌importِ دوطرفه)."""
    # ۱) قرارداد
    v = contracts.validate_request(req)
    if not v["ok"]:
        return contracts.new_plan(
            action_id=str((req or {}).get("action_id") or "?"),
            classification="A6", decision="REJECT",
            reason="invalid-request:" + ",".join(v["errors"][:6]))

    aid = str(req["action_id"])

    # ۲) پیش‌ثبت — «عمل بدونِ prereg معتبر اجرا نمی‌شود»
    pre = prereg_lookup(str(req.get("prereg_id"))) if callable(prereg_lookup) else None
    if not isinstance(pre, dict):
        return contracts.new_plan(
            action_id=aid, classification="A6", decision="BLOCK",
            reason=f"no-valid-prereg:{req.get('prereg_id')!r}")

    # ۳) طبقه‌بندی
    c = classifier.classify(req)
    cls = c["classification"]
    decision = classifier.decide(cls)
    reasons = list(c["reasons"])

    if decision == "REJECT":
        return contracts.new_plan(action_id=aid, classification=cls,
                                  decision="REJECT",
                                  reason="|".join(reasons[:6]))

    # ۴) محدوده — فقط برای عمل‌هایی که مقصدِ فایلی دارند
    scope_receipt = {}
    if cls in ("A1", "A2"):
        sc = scope_guard.check(str(req.get("target") or ""),
                               sandbox_root=sandbox_root,
                               allowed_scope=req.get("allowed_scope"))
        scope_receipt = sc
        if not sc["ok"]:
            return contracts.new_plan(
                action_id=aid, classification=contracts.escalate(cls, "A6"),
                decision="REJECT", scope_receipt=sc,
                reason=f"scope:{sc['reason']}")

    # ۵) idempotency
    idem = idempotency.check(req, ledger if ledger is not None else {})
    key = idem["key"]
    if idem["state"] == "DUPLICATE":
        return contracts.new_plan(
            action_id=aid, classification=cls, decision="BLOCK",
            idempotency_key=key, reason="duplicate-noop",
            scope_receipt=scope_receipt,
            steps=[{"op": "noop", "why": "already-executed"}])
    if idem["state"] == "CONFLICT":
        return contracts.new_plan(
            action_id=aid, classification=cls, decision="BLOCK",
            idempotency_key=key, scope_receipt=scope_receipt,
            reason=f"idempotency-conflict:{idem['reason']}")

    # ۶) مجوز — فقط A3 اصلاً مسیرِ مجوز دارد. A4/A5 حتی با مجوز هم در این دور
    #    باز نمی‌شوند (سیاستِ `DECISION_BY_CLASS`)، و A6 هرگز.
    gate = {}
    if decision == "OWNER_GATE":
        card = owner_gate.make_card(req, {"classification": cls,
                                          "reason": "|".join(reasons[:4])},
                                    now=now)
        gate = {"card": card, "authorized": False}
        if approval is not None:
            vr = owner_gate.verify(approval, req, now=now,
                                   used_nonces=used_nonces)
            gate["verify"] = vr
            gate["authorized"] = bool(vr["ok"])
            if not vr["ok"]:
                return contracts.new_plan(
                    action_id=aid, classification=cls, decision="BLOCK",
                    idempotency_key=key, owner_gate=gate,
                    scope_receipt=scope_receipt,
                    reason=f"approval:{vr['reason']}")
            decision = "ALLOW"      # مجوزِ معتبر ⇒ همین یک عمل باز می‌شود

    # ۷) نقشه
    sc_info = contracts.has_completion_evidence(req)
    steps = _steps_for(cls, req)
    return contracts.new_plan(
        action_id=aid, classification=cls, decision=decision,
        idempotency_key=key, steps=steps,
        preconditions=[{"prereg_id": req.get("prereg_id"), "present": True},
                       {"scorable": sc_info["scorable"], "why": sc_info["why"]}],
        scope_receipt=scope_receipt, owner_gate=gate,
        rollback_plan={"declared": str(req.get("rollback") or "")[:200]},
        expires_at="", reason="|".join(reasons[:6]))


def _steps_for(cls: str, req: dict) -> list:
    if cls == "A0":
        return [{"op": "observe", "target": str(req.get("target") or "")[:200]}]
    if cls == "A1":
        return [{"op": "write_artifact", "target": str(req.get("target") or "")[:200]}]
    if cls == "A3":
        return [{"op": "emit_owner_card"}]
    return [{"op": "blocked", "class": cls}]
