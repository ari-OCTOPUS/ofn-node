"""limited_effect.py — فاز N: اثر محدود (رأی مالک = انتخاب ۳ فاز M).

رأی در `_ops/owner-verdicts.yaml` ثبت شده است (`limited_effect_phase_n`).
این ماژول با خواندن رأی tracked فعال می‌شود؛ env صریح `OCTOPUS_LIMITED_EFFECT_PHASE_N`
برنده است (rollback فوری با =0).

اثرهای مجاز:
    · throttle (کم‌کردن سرعت loop)
    · pause_proposal (پیشنهاد توقف)
    · reduce_concurrency (کاهش هم‌زمانی)
    · block_suspicious_proposal (جلوگیری موقت از proposal مشکوک)
    · request_human_approval (درخواست تأیید انسانی)

هر اقدام باید ۵ فیلد الزامی داشته باشد؛ غایب = DENY:
    proposal_hash · policy_version · state_version · expiry_at · idempotency_key
+ owner_verdict (رجیستر رأی).

ممنوع همیشگی: تغییر کد/policy، بازنویسی حافظهٔ معنایی، اجرای proposal بدون
PolicyGate، پیام خارجی، secret/Project-F. این ماژول فقط proposal/درخواست تولید
می‌کند؛ اجرای واقعی همیشه از PolicyGate می‌گذرد.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

LIMITED_SCHEMA = "limited-effect.v1"

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
STATE_DIR = Path(os.environ.get("OCTOPUS_STATE_DIR", str(_OPS / "state")))
ACTIVE_EFFECTS = STATE_DIR / "limited-effects" / "active.jsonl"

REQUIRED_FIELDS = (
    "proposal_hash",
    "policy_version",
    "state_version",
    "expiry_at",
    "idempotency_key",
    "owner_verdict",
)

ALLOWED_ACTIONS = (
    "throttle",
    "pause_proposal",
    "reduce_concurrency",
    "block_suspicious_proposal",
    "request_human_approval",
)

VERDICT_CHOICE_3 = "3"   # اثر محدود


def enabled() -> bool:
    """آیا رأی مالک انتخاب ۳ است؟ env صریح برنده؛ fallback به رأی tracked."""
    try:
        import sys
        if str(_OPS) not in sys.path:
            sys.path.insert(0, str(_OPS))
        import owner_verdicts as _ov  # noqa: WPS433
        value = _ov.get("OCTOPUS_LIMITED_EFFECT_PHASE_N")
    except Exception:  # noqa: BLE001 — fail-soft به advisory
        value = os.environ.get("OCTOPUS_LIMITED_EFFECT_PHASE_N", "0")
    return str(value or "0").strip() == VERDICT_CHOICE_3


def evaluate(request: dict | None) -> dict[str, Any]:
    """درگاه واحد فاز N. بدون رأی مثبت یا فیلد ناقص → DENY.

    Args:
        request: {action, proposal_hash, policy_version, state_version,
                  expiry_at, idempotency_key, owner_verdict, ...}

    Returns:
        {schema, allowed, decision, reason, action, expires_at?, applied}
    """
    if not enabled():
        return {
            "schema": LIMITED_SCHEMA,
            "allowed": False,
            "decision": "DENY",
            "reason": "limited-effect disabled: owner vote != choice 3 (Phase M)",
            "applied": False,
        }
    if not isinstance(request, dict):
        return {
            "schema": LIMITED_SCHEMA,
            "allowed": False,
            "decision": "DENY",
            "reason": "request must be dict",
            "applied": False,
        }
    action = str(request.get("action") or "")
    if action not in ALLOWED_ACTIONS:
        return {
            "schema": LIMITED_SCHEMA,
            "allowed": False,
            "decision": "DENY",
            "reason": f"action not allowed: {action!r}",
            "applied": False,
        }
    missing = []
    for f in REQUIRED_FIELDS:
        v = request.get(f)
        if v is None or (isinstance(v, str) and not v.strip()):
            missing.append(f)
    if missing:
        return {
            "schema": LIMITED_SCHEMA,
            "allowed": False,
            "decision": "DENY",
            "reason": "missing required fields: " + ", ".join(missing),
            "applied": False,
        }
    expiry = str(request.get("expiry_at") or "")
    if expiry < time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()):
        return {
            "schema": LIMITED_SCHEMA,
            "allowed": False,
            "decision": "DENY",
            "reason": "expiry_at in the past",
            "applied": False,
        }
    # در این مرحله هیچ اجرا/تغییری واقعی نیست — فقط proposal/درخواست.
    return {
        "schema": LIMITED_SCHEMA,
        "allowed": True,
        "decision": "ALLOWED_AS_PROPOSAL",
        "reason": "proposal only — execution requires PolicyGate + owner approval",
        "action": action,
        "expires_at": expiry,
        "idempotency_key": request.get("idempotency_key"),
        "applied": False,   # ← هیچ اجرای واقعی در این ماژول نیست
    }


def record_effect(request: dict | None) -> dict[str, Any]:
    """proposal مجاز را در `state/limited-effects/active.jsonl` ثبت کن (fail-soft).

    ثبت = شفافیت/audit، نه اجرا. رکورد فقط proposal است (`applied=false`).
    """
    res = evaluate(request)
    if not res.get("allowed"):
        return res
    rec = {
        "schema": LIMITED_SCHEMA,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "allowed": True,
        "decision": "ALLOWED_AS_PROPOSAL",
        "action": res.get("action"),
        "proposal_hash": request.get("proposal_hash"),
        "policy_version": request.get("policy_version"),
        "state_version": request.get("state_version"),
        "expiry_at": res.get("expires_at"),
        "idempotency_key": request.get("idempotency_key"),
        "owner_verdict": request.get("owner_verdict"),
        "applied": False,
        "may_authorize": False,
    }
    try:
        ACTIVE_EFFECTS.parent.mkdir(parents=True, exist_ok=True)
        with ACTIVE_EFFECTS.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        rec["recorded"] = True
    except OSError:
        rec["recorded"] = False
    return rec


if __name__ == "__main__":
    print(json.dumps(evaluate({}), ensure_ascii=False, indent=2))
