#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""taxonomy.py — واژگانِ واحدِ ستون‌فقراتِ اختاپوس (منبعِ یگانه؛ رفعِ ریسکِ fork).

Memory Gate + Decision Receipt + Outcome Store + Event Spine همه از این‌جا trust_grade،
namespace، effect_class و event_type را می‌خوانند تا هرگز drift خاموش نکنند. stdlib فقط،
بدونِ side-effect، فقط ثابت‌ها + validatorهای خالص. هیچ مدل/agent نمی‌تواند این‌ها را
runtime «ارتقا» دهد — enumِ ثابت است.
"""
from __future__ import annotations

# ── trust: از چه اعتباری برخوردار است (مرتب از قوی به ضعیف) ────────────────────
TRUST_GRADES = ("OWNER_CONFIRMED", "DETERMINISTIC", "GRADED", "ADVISORY", "UNVERIFIED", "UNKNOWN")
_TRUST_RANK = {g: i for i, g in enumerate(TRUST_GRADES)}   # ۰=قوی‌ترین

# ── namespace: نوعِ حافظه/دانش ───────────────────────────────────────────────
NAMESPACES = ("procedural", "owner_fact", "self_claim", "self_knowledge", "semantic", "episodic")

# ── effect class: شدتِ اثرِ یک اقدام (taxonomyِ دلتا-اسکن) ─────────────────────
EFFECT_CLASSES = ("E0", "E1", "E2", "E3", "E4")
_EFFECT_DESC = {
    "E0": "pure internal computation",
    "E1": "internal durable write",
    "E2": "owner-only notification/advisory",
    "E3": "external-world reversible action",
    "E4": "external-world irreversible/financial/legal action",
}

# ── event type: رویدادهای زنجیرهٔ تصمیم→اثر→نتیجه (spine + outcome_store) ──────
# 2026-07-21 (spine shadow expansion): پنج نامِ canonicalِ cross-domain — **additive**؛
# نام‌های قدیمی دست‌نخورده معتبر می‌مانند (سازگاریِ replay/schema حفظ است).
EVENT_TYPES = ("delivered", "deferred", "accepted-measurement", "rejected", "failed",
               "decided", "reviewed", "verified", "settled",
               "mission-created", "decision-recorded", "proposal-issued",
               "owner-verdict-recorded", "outcome-recorded",
               "system.booted",   # C2-E: شناسنامهٔ تولد (RESURRECTION §birth-certificate)
               "system.beat",     # C5: ضربانِ واحد (one-heartbeat scheduler)
               "hebb.observation")  # W2 (۲۰۲۶-۰۷-۳۱): مشاهدهٔ Hebbian واقعی — «پلِ به EFE».
                                    # additive: نام‌های قدیمی معتبر می‌مانند (همان قراردادِ ۰۷-۲۱).
                                    # domain=neural؛ Advisory؛ پشتِ OCTOPUS_HEBBIAN_LEDGER.

# ── privacy ──────────────────────────────────────────────────────────────────
PRIVACY_CLASSES = ("public", "scrubbed", "owner_only")


def is_trust(g) -> bool:
    return g in _TRUST_RANK


def trust_at_least(g, floor) -> bool:
    """آیا trust‌ِ g دستِ‌کم به‌قوّتِ floor است؟ (grade نامعتبر → False، fail-closed)."""
    if g not in _TRUST_RANK or floor not in _TRUST_RANK:
        return False
    return _TRUST_RANK[g] <= _TRUST_RANK[floor]


def is_namespace(n) -> bool:
    return n in NAMESPACES


def is_effect_class(e) -> bool:
    return e in EFFECT_CLASSES


def effect_desc(e) -> str:
    return _EFFECT_DESC.get(e, "unknown")


def is_event_type(t) -> bool:
    return t in EVENT_TYPES


def is_privacy(p) -> bool:
    return p in PRIVACY_CLASSES


# قوانینِ ثابتِ commit (کدام namespace چطور trust می‌گیرد) — مرجعِ واحد برای Memory Gate.
# «چه کسی مجاز است این namespace را commit کند» — نه خودِ مدل.
COMMIT_RULES = {
    "procedural":     {"committer": "owner_or_deterministic", "default_trust": "OWNER_CONFIRMED"},
    "owner_fact":     {"committer": "owner_only",             "default_trust": "OWNER_CONFIRMED"},
    "self_claim":     {"committer": "external_grade",         "default_trust": "ADVISORY"},
    "self_knowledge": {"committer": "advisory_until_graded",  "default_trust": "ADVISORY"},
    "semantic":       {"committer": "scrub_salience_bar",     "default_trust": "GRADED"},
    "episodic":       {"committer": "auto_scrubbed",          "default_trust": "GRADED"},
}
