#!/usr/bin/env python3
"""contracts — قراردادهای نسخه‌دارِ پلِ اقدام. هیچ اجرایی، فقط شکل و اعتبار.

چرا قرارداد **قبل از** اجراکننده نوشته می‌شود: اگر اول executor بسازی، شکلِ
داده را همان‌جا اختراع می‌کنی و بعد هر مصرف‌کننده‌ای باید حدس بزند. این‌جا شکل
اول تثبیت می‌شود، و `world_discovery` (یا هر مولدِ دیگری) بعداً فقط به همین
شکل ترجمه می‌شود — بدونِ هیچ importِ دوطرفه.

سه سندِ نسخه‌دار:
    action-request.v1   «می‌خواهم این کار را بکنم»  (مولد می‌نویسد)
    action-plan.v1      «مجازی/نیستی، و اگر آری چطور»  (پل می‌نویسد)
    action-receipt.v1   «چه واقعاً شد»  (اجراکننده می‌نویسد)

قاعدهٔ حاکمِ همهٔ این فایل: **fail-closed**. میدانِ غایب، نوعِ ناشناخته، مقدارِ
ناخوانا ⇒ نامعتبر. هیچ پیش‌فرضِ سخاوتمندانه‌ای وجود ندارد، چون تنها مصرف‌کنندهٔ
این قرارداد چیزی است که ممکن است اثرِ بیرونی داشته باشد.

$0 · stdlib · تابعِ خالص · صفر I/O.
"""
from __future__ import annotations

import hashlib
import json
import re

REQUEST_SCHEMA = "action-request.v1"
PLAN_SCHEMA = "action-plan.v1"
RECEIPT_SCHEMA = "action-receipt.v1"
VERDICT_SCHEMA = "action-verdict.v1"

# ── نردبانِ کلاسِ عمل — ترتیب معنا دارد: بالاتر = خطرناک‌تر ──────────────────
# `A6` عمداً بالاترین است تا `max()` هرگز به سمتِ امن‌تر لغزش نکند.
LADDER = ("A0", "A1", "A2", "A3", "A4", "A5", "A6")
_RANK = {c: i for i, c in enumerate(LADDER)}

CLASS_MEANING = {
    "A0": "OBSERVE_ONLY — خواندن؛ صفر تغییر، صفر ارسال، صفر خرج",
    "A1": "INTERNAL_ARTIFACT — ساختِ artifact در sandbox؛ برگشت‌پذیر",
    "A2": "INTERNAL_REVERSIBLE — تغییرِ کم‌خطرِ allowlisted؛ فعلاً بی‌مجوز",
    "A3": "OWNER_ACTION — فقط کارتِ رأی تولید می‌شود",
    "A4": "EXTERNAL_EFFECT — پیام/فرم/انتشار/deploy؛ fail-closed",
    "A5": "MONEY_OR_CONTRACT — هر خرج یا تعهد؛ fail-closed",
    "A6": "FORBIDDEN — همیشه REJECTED",
}

DECISIONS = ("ALLOW", "OWNER_GATE", "BLOCK", "REJECT")
STATUSES = ("EXECUTED", "BLOCKED", "REJECTED", "FAILED", "NOOP", "CONFLICT")

# ── میدان‌های اجباری ────────────────────────────────────────────────────────
_REQUEST_REQUIRED = (
    "schema", "action_id", "prereg_id", "source_component", "intent",
    "action_type", "target", "expected_effect", "allowed_scope",
    "external_effect", "estimated_cost", "rollback", "falsifier",
)
# میدان‌هایی که در «امضای» عمل می‌آیند — تغییرِ هرکدام یعنی عملِ **دیگری**.
# نه `requested_at` و نه `intent` این‌جا نیستند: اولی زمان است (تغییرش عمل را
# عوض نمی‌کند) و دومی متنِ آزاد است. اگر `intent` در امضا می‌بود، بازنویسیِ
# توضیح یک approval ِ معتبر را می‌سوزاند؛ و اگر `target` نمی‌بود، همان approval
# روی مقصدِ دیگری replay می‌شد.
_SIGNATURE_FIELDS = ("action_id", "action_type", "target", "allowed_scope",
                     "external_effect", "estimated_cost", "prereg_id")


def _num(v) -> "float | None":
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return float(v)


def canonical(obj) -> str:
    """سریال‌سازیِ قطعی — کلیدها مرتب، فاصلهٔ ثابت. hash باید بازتولیدپذیر باشد."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


def payload_hash(req: dict) -> str:
    """امضای عمل. تغییرِ هر میدانِ امضا ⇒ hash نو ⇒ approval ِ قدیمی بی‌اعتبار."""
    sig = {k: req.get(k) for k in _SIGNATURE_FIELDS}
    return hashlib.sha256(canonical(sig).encode("utf-8")).hexdigest()[:32]


def validate_request(req) -> dict:
    """{ok, errors}. هیچ استثنایی پرتاب نمی‌شود — ورودیِ خصمانه هم فقط رد می‌شود."""
    errors = []
    if not isinstance(req, dict):
        return {"ok": False, "errors": ["not-a-dict"]}
    if req.get("schema") != REQUEST_SCHEMA:
        errors.append(f"bad-schema:{req.get('schema')!r}")
    for k in _REQUEST_REQUIRED:
        if k not in req:
            errors.append(f"missing:{k}")
    aid = str(req.get("action_id") or "")
    if not re.fullmatch(r"[A-Za-z0-9._:-]{4,80}", aid):
        errors.append("bad:action_id")
    if not isinstance(req.get("allowed_scope"), list):
        errors.append("bad:allowed_scope")
    if not isinstance(req.get("external_effect"), bool):
        errors.append("bad:external_effect")     # None/"false"/1 هیچ‌کدام bool نیستند
    if _num(req.get("estimated_cost")) is None or _num(req.get("estimated_cost")) < 0:
        errors.append("bad:estimated_cost")
    for k in ("rollback", "falsifier", "expected_effect", "intent"):
        if k in req and not str(req.get(k) or "").strip():
            errors.append(f"empty:{k}")
    m = req.get("metric")
    if m is not None:
        if not isinstance(m, dict):
            errors.append("bad:metric")
        else:
            for k in ("path", "key"):
                if not str(m.get(k) or "").strip():
                    errors.append(f"bad:metric.{k}")
            if _num(m.get("baseline")) is None:
                errors.append("bad:metric.baseline")
    return {"ok": not errors, "errors": errors}


def has_completion_evidence(req: dict) -> dict:
    """آیا این عمل اصلاً می‌تواند «تکمیل» امتیاز بگیرد؟

    جدا از اعتبار: یک درخواست می‌تواند کاملاً معتبر و اجراپذیر باشد ولی
    **ابطال‌ناپذیر**. آن‌وقت اجرا مجاز است ولی هیچ‌وقت COMPLETE نمی‌شود — چون
    چیزی نیست که غلط بودنش را نشان دهد. سکوت این‌جا خطرناک است، پس صریح است."""
    why = []
    m = req.get("metric") if isinstance(req.get("metric"), dict) else None
    if not m or _num(m.get("baseline")) is None:
        why.append("no-metric")
    if not str(req.get("falsifier") or "").strip():
        why.append("no-falsifier")
    return {"scorable": not why, "why": why}


def new_plan(*, action_id: str, classification: str, decision: str,
             reason: str, idempotency_key: str = "", steps=None,
             preconditions=None, scope_receipt=None, owner_gate=None,
             rollback_plan=None, expires_at: str = "") -> dict:
    if classification not in _RANK:
        classification, decision = "A6", "REJECT"
        reason = f"unknown-classification|{reason}"
    if decision not in DECISIONS:
        decision, reason = "BLOCK", f"unknown-decision|{reason}"
    return {
        "schema": PLAN_SCHEMA, "action_id": str(action_id),
        "classification": classification, "decision": decision,
        "steps": list(steps or []), "preconditions": list(preconditions or []),
        "scope_receipt": dict(scope_receipt or {}),
        "owner_gate": dict(owner_gate or {}),
        "rollback_plan": dict(rollback_plan or {}),
        "idempotency_key": str(idempotency_key),
        "expires_at": str(expires_at), "reason": str(reason),
    }


def validate_plan(plan) -> dict:
    errors = []
    if not isinstance(plan, dict):
        return {"ok": False, "errors": ["not-a-dict"]}
    if plan.get("schema") != PLAN_SCHEMA:
        errors.append("bad-schema")
    if plan.get("classification") not in _RANK:
        errors.append("bad:classification")
    if plan.get("decision") not in DECISIONS:
        errors.append("bad:decision")
    if not str(plan.get("reason") or "").strip():
        errors.append("empty:reason")     # تصمیمِ بی‌دلیل قابلِ ممیزی نیست
    return {"ok": not errors, "errors": errors}


def escalate(*classes: str) -> str:
    """بالاترین (خطرناک‌ترین) کلاس. ناشناخته ⇒ A6 — هرگز لغزش به سمتِ امن‌تر."""
    best = "A0"
    for c in classes:
        if c not in _RANK:
            return "A6"
        if _RANK[c] > _RANK[best]:
            best = c
    return best


def new_receipt(*, action_id: str, idempotency_key: str, status: str,
                classification: str, started_at: str, finished_at: str,
                steps_completed=None, artifacts=None, external_effects=None,
                cost=0, before=None, after=None, rollback_available=False,
                evidence=None, errors=None) -> dict:
    if status not in STATUSES:
        status = "FAILED"
        errors = list(errors or []) + ["unknown-status"]
    return {
        "schema": RECEIPT_SCHEMA, "action_id": str(action_id),
        "idempotency_key": str(idempotency_key), "status": status,
        "classification": str(classification),
        "started_at": str(started_at), "finished_at": str(finished_at),
        "steps_completed": list(steps_completed or []),
        "artifacts": list(artifacts or []),
        "external_effects": list(external_effects or []),
        "cost": float(cost or 0), "before": dict(before or {}),
        "after": dict(after or {}),
        "rollback_available": bool(rollback_available),
        "evidence": list(evidence or []), "errors": list(errors or []),
    }
