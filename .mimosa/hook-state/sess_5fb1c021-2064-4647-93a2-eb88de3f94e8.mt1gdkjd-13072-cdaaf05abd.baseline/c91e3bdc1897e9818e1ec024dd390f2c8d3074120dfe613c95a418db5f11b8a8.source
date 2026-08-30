#!/usr/bin/env python3
"""contracts — قراردادِ مرزِ «کشفِ دنیا» ↔ «پلِ اقدام».

این پکیج تنها جایی است که هر دو طرف را می‌شناسد. جهتِ وابستگی یک‌طرفه است و
هرگز معکوس نمی‌شود:

    artifact ِ world_discovery  →  این مترجم  →  قراردادِ عمومیِ action_bridge

نه `action_bridge` داخلِ `world_discovery` را می‌شناسد، نه برعکس. اگر روزی یکی
دیگری را import کرد، دو اندام به هم جوش خورده‌اند و جدا مردنشان ناممکن شده.

⚠️ **ناهم‌خوانیِ سند با artifact — کشفِ مرزیِ ۲۰۲۶-۰۷-۳۰.**
`INTEGRATION-MANIFEST` ِ GLM قراردادِ خروجی را با کلیدهای `experiment` و
`opportunity` مستند کرده، ولی artifact ِ واقعیِ روی دیسک **هیچ‌کدام را ندارد**
(چون `experiments_designed=0`). همچنین `asymmetry_hypotheses` در artifact طولش
**صفر** است در حالی که گزارشِ انسانی چهار فرضیه (ASYMM-001..004) دارد.

این تناقض نیست — تفکیکِ «گزارشِ انسانی» از «قراردادِ ماشین» است. ولی یعنی
مترجم **نباید** شکلِ مستند را فرض کند. هر کلید قبل از خواندن باید وجودش تأیید
شود (درسِ ثبت‌شده: «قبل از شمردنِ یک میدان، وجودش را در همان اسکیما تأیید کن»).

$0 · stdlib · تابعِ خالص · صفر I/O.
"""
from __future__ import annotations

import hashlib
import json

TRANSLATION_SCHEMA = "world-discovery-action.translation.v1"
DRAFT_SCHEMA = "world-discovery.telegram-draft.v1"
RESEARCH_REQUEST_SCHEMA = "world-discovery.research-request.v1"

# اسکیماهایی که این مترجم می‌شناسد. **نسخهٔ ناشناخته = BLOCK**، نه «شاید سازگار».
KNOWN_BUNDLE_SCHEMAS = frozenset({"world-discovery.bundle.v1"})
KNOWN_RESULT_SCHEMAS = frozenset({"world-discovery.discover.v1"})

# وضعیت‌هایی که مرز باید **بدونِ تحریف** حمل کند. هرکدام معنایش فرق دارد و
# جمع‌کردنشان در «شکست» همان چیزی است که NO_VALID_DISCOVERY را به PASS
# تبدیل می‌کند.
SOURCE_STATUSES = (
    "DISCOVERY_VALIDATED",       # کشفِ سه‌گوش‌شده با ≥۲ منبعِ مستقل
    "NO_VALID_DISCOVERY",        # جست‌وجو شد، چیزی به حدِ نصاب نرسید — نتیجهٔ معتبر
    "CONTESTED",                 # شاهدِ متناقض پیدا شد
    "FALSIFIED",                 # ابطال شد
    "INSUFFICIENT_EVIDENCE",     # شاهد کم بود (مثلاً retriever شکست خورد)
    "BLOCKED_BY_OWNER",
    "IMPLEMENTED_NOT_INTEGRATED",
)

# وضعیت‌هایی که **هرگز** به عملِ اجرایی تبدیل نمی‌شوند.
NON_ACTIONABLE = frozenset({
    "NO_VALID_DISCOVERY", "CONTESTED", "FALSIFIED",
    "INSUFFICIENT_EVIDENCE", "BLOCKED_BY_OWNER",
    "IMPLEMENTED_NOT_INTEGRATED",
})

DECISIONS = ("NO_ACTION", "DRY_RUN", "OWNER_GATE", "BLOCK", "REJECT")

# نگاشتِ **پایه**. سطحِ اعلام‌شدهٔ منبع کفِ کلاس را می‌دهد، نه حکمِ نهایی —
# `policy.infer_level()` می‌تواند بالاترش ببرد، هرگز پایین‌تر.
LEVEL_TO_CLASS = {"E0": "A0", "E1": "A1", "E2": "A3", "E3": "A4", "E4": "A5"}


def canonical(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


def content_hash(obj) -> str:
    return hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()[:32]


def unwrap(artifact) -> dict:
    """bundle → result. شکلِ ناشناخته = `{}` (و صداکننده BLOCK می‌کند).

    artifact واقعی دو لایه است: `{schema: bundle.v1, result: {schema: discover.v1}}`.
    ولی ممکن است روزی مستقیم `discover.v1` بدهند، پس هر دو پذیرفته می‌شوند —
    و هر چیزِ دیگری نه."""
    if not isinstance(artifact, dict):
        return {}
    if artifact.get("schema") in KNOWN_RESULT_SCHEMAS:
        return artifact
    if artifact.get("schema") in KNOWN_BUNDLE_SCHEMAS:
        r = artifact.get("result")
        return r if isinstance(r, dict) else {}
    return {}


def new_translation_receipt(**kw) -> dict:
    """رسیدِ ترجمه. هر میدان صریح مقداردهی می‌شود — `None` ِ ضمنی ممنوع، چون
    «نبود» و «صفر» را یکی می‌کند."""
    decision = kw.get("decision")
    if decision not in DECISIONS:
        decision = "BLOCK"
        kw["errors"] = list(kw.get("errors") or []) + [f"unknown-decision:{kw.get('decision')!r}"]
    return {
        "schema": TRANSLATION_SCHEMA,
        "translation_id": str(kw.get("translation_id") or ""),
        "created_at": str(kw.get("created_at") or ""),
        "source_artifact": dict(kw.get("source_artifact") or {}),
        "source_status": kw.get("source_status"),
        "experiment_level_declared": kw.get("experiment_level_declared"),
        "experiment_level_inferred": kw.get("experiment_level_inferred"),
        "action_class": kw.get("action_class"),
        "decision": decision,
        "action_id": kw.get("action_id"),
        "reason": str(kw.get("reason") or ""),
        "evidence_count": int(kw.get("evidence_count") or 0),
        "independent_source_count": int(kw.get("independent_source_count") or 0),
        "falsifier_present": bool(kw.get("falsifier_present")),
        "external_effects": list(kw.get("external_effects") or []),
        "estimated_cost": float(kw.get("estimated_cost") or 0),
        "owner_gate_required": bool(kw.get("owner_gate_required")),
        "warnings": list(kw.get("warnings") or []),
        "errors": list(kw.get("errors") or []),
    }


def validate_translation_receipt(rec) -> dict:
    errors = []
    if not isinstance(rec, dict):
        return {"ok": False, "errors": ["not-a-dict"]}
    if rec.get("schema") != TRANSLATION_SCHEMA:
        errors.append("bad-schema")
    if rec.get("decision") not in DECISIONS:
        errors.append("bad:decision")
    if not str(rec.get("reason") or "").strip():
        errors.append("empty:reason")
    # ناوردی‌های سختِ این دور — نقضشان یعنی مرز نشت کرده
    if rec.get("external_effects") != []:
        errors.append("invariant:external_effects-not-empty")
    if float(rec.get("estimated_cost") or 0) != 0:
        errors.append("invariant:cost-not-zero")
    # وضعیتِ غیرقابلِ‌اقدام هرگز `action_id` نمی‌گیرد
    if rec.get("source_status") in NON_ACTIONABLE and rec.get("action_id"):
        errors.append("invariant:non-actionable-status-has-action-id")
    return {"ok": not errors, "errors": errors}
