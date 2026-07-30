#!/usr/bin/env python3
"""translator — artifact ِ کشف → درخواستِ عمل، یا رسیدِ «هیچ اقدامی».

قاعدهٔ حاکم، و تنها چیزی که واقعاً مهم است:

    NO_VALID_DISCOVERY یک **نتیجهٔ معتبر** است، نه شکستی که باید دورش زد.

مترجم اجازه ندارد آن را به عمل، به PASS، یا به «تقریباً کشف» تبدیل کند. هر
مسیری که از این‌جا بیرون می‌رود یا رسیدِ صادقانهٔ بی‌اقدام است، یا یک آزمایشِ
اطلاعاتیِ A0 که صریح می‌گوید کشف هنوز validated نیست.

آنچه مترجم **هرگز** نمی‌کند: تلگرام نمی‌فرستد · state زنده نمی‌نویسد · مجوز
جعل نمی‌کند · artifact ِ منبع را تغییر نمی‌دهد · target/falsifier را بازنویسی
نمی‌کند · confidence را بالا نمی‌برد.

$0 · stdlib · صفر اثرِ بیرونی · صفر خرج.
"""
from __future__ import annotations

from . import contracts
from . import policy
from . import validator


def _tid(result: dict, now) -> str:
    return f"wda-{contracts.content_hash(result)[:16]}"


def _source_ref(artifact: dict, v: dict) -> dict:
    return {"schema": (artifact or {}).get("schema"),
            "result_schema": (v.get("result") or {}).get("schema"),
            "artifact_id": v.get("artifact_id"),
            "content_hash": v.get("content_hash")}


def build_no_action_receipt(artifact: dict, *, reason: str, now=None) -> dict:
    """رسیدِ «هیچ اقدامی» — برای NO_VALID_DISCOVERY، CONTESTED، FALSIFIED و
    artifact ِ نامعتبر. `action_id` صریح `None` است، نه غایب."""
    v = validator.validate_artifact(artifact)
    result = v.get("result") or {}
    ev = validator.evidence_summary(result) if result else {
        "evidence_count": 0, "independent_source_count": 0,
        "falsifier_present": False}
    return contracts.new_translation_receipt(
        translation_id=_tid(result, now) if result else "wda-invalid",
        created_at=str(now or ""),
        source_artifact=_source_ref(artifact, v),
        source_status=v.get("status"),
        experiment_level_declared=None, experiment_level_inferred=None,
        action_class=None, decision="NO_ACTION", action_id=None,
        reason=reason,
        evidence_count=ev["evidence_count"],
        independent_source_count=ev["independent_source_count"],
        falsifier_present=ev["falsifier_present"],
        external_effects=[], estimated_cost=0, owner_gate_required=False,
        warnings=v.get("warnings") or [], errors=v.get("errors") or [])


def build_action_request(discovery: dict, experiment: dict, *, now=None,
                         prereg_id: str = "", sandbox_scope=("workspace",)) -> dict:
    """فقط برای کشف/آزمایشِ معتبر. خروجی `action-request.v1` ِ پلِ اقدام.

    عمداً هیچ‌چیزی را «بهبود» نمی‌دهد: `falsifier` و `target` عیناً از آزمایش
    می‌آیند. اگر آزمایش falsifier ندارد، این‌جا ساخته نمی‌شود — پل خودش
    امتیازِ تکمیل را نمی‌دهد و ما هم جایش تصمیم نمی‌گیریم."""
    did = str((discovery or {}).get("discovery_id")
              or (discovery or {}).get("id") or "unknown")[:40]
    lvl = policy.infer_level(experiment, (experiment or {}).get("level"))
    return {
        "schema": "action-request.v1",
        "action_id": f"wd-{did}-{contracts.content_hash(experiment)[:8]}",
        "prereg_id": str(prereg_id or ""),
        "source_component": "world_discovery",   # فقط ممیزی — صفر privilege
        "requested_at": str(now or ""),
        "intent": str((experiment or {}).get("title")
                      or (experiment or {}).get("description") or "")[:400],
        "action_type": _action_type_for(lvl["class"]),
        "target": str((experiment or {}).get("target") or "")[:300],
        "expected_effect": str((experiment or {}).get("expected_outcome")
                               or (experiment or {}).get("expected_effect") or "")[:300],
        "allowed_scope": list(sandbox_scope),
        "forbidden_actions": ["external-send", "spend", "account-creation",
                              "form-submission", "pii-collection"],
        "required_capabilities": list((experiment or {}).get("capabilities") or []),
        "external_effect": bool((experiment or {}).get("external_effect")),
        "estimated_cost": float((experiment or {}).get("estimated_cost") or 0),
        "rollback": str((experiment or {}).get("rollback")
                        or "فقط‌خواندنی — هیچ تغییری نیست")[:300],
        "falsifier": str((experiment or {}).get("falsifier") or "")[:300],
        "evidence_required": list((experiment or {}).get("evidence_required") or []),
        "metric": (experiment or {}).get("metric"),
    }


def _action_type_for(cls: "str | None") -> str:
    """کلاس → نوعِ عملِ پل. ناشناخته ⇒ رشته‌ای که پل خودش A6 می‌کند.

    عمداً یک نوعِ *نامعتبر* برمی‌گردانیم به‌جای حدس‌زدنِ نوعِ امن: اگر این‌جا
    چیزی مثل `read_public` جا بزنیم، مترجم دارد به‌جای طبقه‌بندِ پل تصمیم
    می‌گیرد — و همان نقضِ «source privilege ندارد» است."""
    return {"A0": "read_public", "A1": "write_sandbox_artifact",
            "A3": "owner_action_card", "A4": "send_message",
            "A5": "paid_api_call"}.get(cls or "", "unknown-from-discovery")


def translate_discovery_artifact(artifact: dict, *, now=None,
                                 prereg_id: str = "") -> dict:
    """نقطهٔ ورودیِ اصلی. همیشه یک رسیدِ ترجمه برمی‌گرداند — هرگز استثنا.

    ترتیبِ گیت‌ها: اعتبارِ artifact → وضعیت → آزمایش → سطحِ استنتاجی → تصمیم."""
    v = validator.validate_artifact(artifact)
    if not v["ok"]:
        return build_no_action_receipt(
            artifact, reason="invalid-artifact:" + ",".join(v["errors"][:4]),
            now=now)

    result = v["result"]
    status = v["status"]
    ev = validator.evidence_summary(result)
    exp = validator.experiment_of(result)
    declared = (exp or {}).get("level") if exp else None
    lvl = policy.infer_level(exp, declared) if exp else {
        "level": None, "class": None, "reasons": ["no-experiment-in-artifact"]}

    d = policy.decide(status, lvl["class"], has_experiment=bool(exp),
                      falsifier_present=ev["falsifier_present"] or
                      bool(str((exp or {}).get("falsifier") or "").strip()))

    warnings = list(v.get("warnings") or [])
    # اختلافِ عددِ خودگزارشی با شمارشِ ما — نشانه، نه حکم
    sr = ev.get("self_reported_triangulated")
    if isinstance(sr, int) and sr > ev["independent_source_count"]:
        warnings.append(
            f"self-reported-triangulated={sr} > شمارشِ مستقلِ ما="
            f"{ev['independent_source_count']}")

    action_id = None
    if d["decision"] in ("DRY_RUN", "OWNER_GATE") and status == "DISCOVERY_VALIDATED":
        req = build_action_request(result.get("discovery") or {}, exp or {},
                                   now=now, prereg_id=prereg_id)
        action_id = req["action_id"]

    return contracts.new_translation_receipt(
        translation_id=_tid(result, now), created_at=str(now or ""),
        source_artifact=_source_ref(artifact, v),
        source_status=status,
        experiment_level_declared=declared,
        experiment_level_inferred=lvl["level"],
        action_class=lvl["class"] if d["decision"] != "NO_ACTION" else None,
        decision=d["decision"], action_id=action_id,
        reason=d["reason"] + " | " + "؛ ".join(lvl["reasons"][:4]),
        evidence_count=ev["evidence_count"],
        independent_source_count=ev["independent_source_count"],
        falsifier_present=ev["falsifier_present"],
        external_effects=[], estimated_cost=0,
        owner_gate_required=(d["decision"] == "OWNER_GATE"),
        warnings=warnings, errors=[])


def compose_owner_draft(action_plan: dict, *, now=None) -> dict:
    """فقط draft — transport ندارد. پیاده‌سازی در `telegram_draft`."""
    from . import telegram_draft
    return telegram_draft.from_plan(action_plan, now=now)
