#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""effector_registry — رجیستریِ اعلانیِ sensor→actuator (۲۰۲۶-۰۸-۰۸).

چه چیزی هست
────────────
یک فایلِ **تعریف**، نه اجرا. نگاشتِ هر حسِ (sensor) تولیدشده در اختاپوس به
اَکچوئیتورِ (actuator) ممکن — چه وصل باشد، چه نباشد، چه DEAD-OUTPUT باشد.

چرا (علتِ معماری)
────────────────
اختاپوس «sensor-rich، actuator-poor» است: ۵ منبعِ زندهٔ حسِ غنی تولید می‌کنند ولی
هیچ اکچوئیتوری آن‌ها را مصرف نمی‌کند. این رجیستری این شکاف را **قابلِ دیدن** می‌کند
— تا وقتی مالک یا ایجنت نگاه می‌کند، ببیند کدام حس به کجا می‌رسد و کجا بن‌بست می‌شود.
این خودش فعلی از چیزی نمی‌سازد؛ فقط نقشه است. کارِ ایجنت‌های بعدی وصل‌کردنِ
DEAD-OUTPUTهاست (با رأیِ مالک).

مرزها (ساختاری)
───────────────
· فقط داده — $0، stdlib-only، هیچ LLMای، هیچ side-effectای.
· `status` واقعی از کدِ زنده سنجیده شده در زمانِ ساخت (۰۸-۰۸). هر تغییرِ
  سیم‌کشی باید این فایل را هم به‌روز کند.
· هیچ فیلدی که بگوید «این اکچوئیتور را وصل کن» نیست — فقط توصیفِ وضعیتِ امروز.
  تصمیمِ وصل‌کردن با مالک است.
"""
from __future__ import annotations

# هر ورودی: نامِ حس (sensor) → اطلاعاتِ اکچوئیتورِ ممکن.
#
# status مقادیر ممکن:
#   "wired"        — اکچوئیتور واقعاً صدا زده می‌شود و خروجیِ حس را مصرف می‌کند.
#   "display-only" — خروجی به مالک نمایش داده می‌شود ولی هیچ تصمیمی نمی‌سازد.
#   "dead-output"  — تولید می‌شود ولی هیچ مصرف‌کننده‌ای نیست (بیماریِ اصلی).
#   "shadow"       — اکثرِ تیک‌ها ثبت می‌شود ولی اعمال نمی‌شود (observation-only).
#
# `actuator` مسیرِ کدِ واقعی است (نه فرضی). اگر وصل نیست، `None`.
# `gate` فلگِ پشتِ اکچوئیتور است (اگر هست).

EFFECTORS = {
    # ── BCM: فشارِ آموخته‌شده ──────────────────────────────────────────────
    "bcm.learned_pressure": {
        "produced_by": "_ops/wiring.py (neural_beat) → state/neural/effect-shadow.jsonl",
        "field": "learned_pressure / learned_pressure_capped",
        "actuator": "wiring.protective_override (throttle_or_halt)",
        "gate": "OCTOPUS_NEURAL_LEARNED_APPLY",
        "status": "wired",  # ۰۸-۰۸: applied=true ثبت می‌شود وقتی APPLY روشن است و فشار>0
        "propose_only": False,   # مستقیم اعمال می‌شود (ترمز، fail-safe)
        "verified_at": "2026-08-08",
        "evidence": (
            "effect-shadow.jsonl: ۵ ردیفِ آخر applied=true (beat 28659+). "
            "wiring.py:1702-1738: _learned_applied = bool(APPLY && pressure>0). "
            "protective_override صدا زده می‌شود در brain_worker.py:192 و organism.py:639."
        ),
    },
    "bcm.weights_bidirectional": {
        "produced_by": "_ops/neural/bcm.py → state/bcm-weights.json",
        "field": "weights (n_keys potentiated)",
        "actuator": None,
        "gate": None,
        "status": "dead-output",  # وزن‌ها تولید می‌شوند ولی هیچ تصمیمی نمی‌خواندشان
        "propose_only": None,
        "verified_at": "2026-08-08",
        "evidence": (
            "bcm.py Step() وزن‌ها را تولید می‌کند؛ جستجو برای مصرف‌کننده‌ای که "
            "weights را در یک تصمیم بخواند: هیچ. در self_context برای نمایش آمده، "
            "نه تصمیم. این خودِ بیماریِ «sensor-rich/actuator-poor» است."
        ),
    },

    # ── Hebbian: هم‌خانواده‌سازی ────────────────────────────────────────────
    "hebbian.associations": {
        "produced_by": "_ops/neural/hebbian.py → neural/hebbian.json",
        "field": "co-occurrence associations",
        "actuator": None,
        "gate": "OCTOPUS_WIRE_HEBBIAN",
        "status": "dead-output",
        "propose_only": None,
        "verified_at": "2026-08-08",
        "evidence": (
            "hebbian.json تولید می‌شود ولی grep برای مصرف‌کننده‌ای که آن را در "
            "تصمیم بخواند: هیچ (تنها در effect-shadow برای نمایش)."
        ),
    },

    # ── Consolidation: بینش‌های بلندمدت ─────────────────────────────────────
    "consolidation.insights": {
        "produced_by": "_ops/memory/consolidation.py → state/memory/memory.db",
        "field": "conclusions / frontier (insights)",
        "actuator": None,
        "gate": "OCTOPUS_WIRE_CONSOLIDATION",
        "status": "dead-output",  # append-only، بدون dedup، بدون retract
        "propose_only": None,
        "verified_at": "2026-08-08",
        "evidence": (
            "state/memory/memory.db (۲۹۰+ سیکل، ۳ بینشِ تکراری). "
            "append-only، بدون retract. "
            "مصرف‌کننده‌ای که insight را به action تبدیل کند: هیچ."
        ),
    },

    # ─ـ deep_dive.smallest_fix: دقیق‌ترین خروجیِ تصمیم ──────────────────────
    "deep_dive.smallest_fix": {
        "produced_by": "_ops/doctor/self_knowledge.py → state/doctor/self-knowledge-latest.json",
        "field": "smallest_fix (یک جملهٔ دقیق)",
        "actuator": None,   # ← این مهم‌ترین DEAD-OUTPUT است
        "gate": None,
        "status": "display-only",  # به مالک در digest نمایش داده می‌شود ولی هیچ actionی
        "propose_only": None,
        "verified_at": "2026-08-08",
        "evidence": (
            "organ_dialogue.py:142: «🔧 کوچک‌ترین فیکس: ...» به digest اضافه می‌شود "
            "(نمایش). ولی کامنتِ همان خط می‌گوید «هیچ ماژولی نمی‌خواندش». "
            "باید به action_bridge.propose وصل شود (propose-only). فعلاً بن‌بست."
        ),
    },

    # ── C6 probes: ۱۲ حسِ فرضیه‌ساز ──────────────────────────────────────────
    "c6.hypothesis_producer": {
        "produced_by": "_ops/c6_producer.py + c6_probes.py → state/c6/hypothesis-queue.jsonl",
        "field": "hypotheses (12 probe types)",
        "actuator": "c6_trigger.c6_research_beat → RFC card",
        "gate": "OCTOPUS_WIRE_C6_TRIGGER",
        "status": "wired",   # فرضیه → آزمایشِ sandbox → RFC card (propose-only)
        "propose_only": True,
        "verified_at": "2026-08-08",
        "evidence": (
            "c6_trigger.py:173 c6_research_beat فرضیه را برمی‌دارد، آزمایش می‌کند، "
            "و به‌صورت RFC card به مالک می‌فرستد (propose-only، پشتِ approval). "
            "این یک effectorِ کاملِ حلقهٔ بسته است — مثالِ خوب."
        ),
    },

    # ─ـ self_model: pathology ───────────────────────────────────────────────
    "self_model.pathology": {
        "produced_by": "_ops/cortex/self_model.py → state/self-model-latest.json",
        "field": "pathology (symptom/root_cause)",
        "actuator": None,   # فقط alert، نه action
        "gate": "OCTOPUS_WIRE_SELF_MODEL",
        "status": "display-only",  # در digest به مالک نشان داده می‌شود
        "propose_only": None,
        "verified_at": "2026-08-08",
        "evidence": (
            "self_model.py:159 emit_self_claims فقط alert می‌سازد. pathology به "
            "organ_dialogue برای نمایش می‌رود، ولی self_patch proposal از آن ساخته "
            "نمی‌شود. امکان: pathology → action_bridge.propose(self_patch)."
        ),
    },

    # ── effect-shadow: سایهٔ اثرِ عصبی ───────────────────────────────────────
    "effect_shadow.would_throttle": {
        "produced_by": "_ops/wiring.py:1698 → state/neural/effect-shadow.jsonl",
        "field": "would_throttle_brain / would_schedule",
        "actuator": None,   # خودش فقط observation است؛ throttle واقعی bcm.learned_pressure است
        "gate": "OCTOPUS_WIRE_NEURAL_EFFECT_SHADOW",
        "status": "shadow",  # ثبت می‌شود ولی اعمال نمی‌شود (طراحی)
        "propose_only": None,
        "verified_at": "2026-08-08",
        "evidence": (
            "این خودش حس نیست، بلکه سایهٔ اثرِ bcm.learned_pressure است. "
            "تولید در wiring.py:1698 → effect-shadow.jsonl. "
            "طراحی: observation-only تا داده جمع شود، بعد APPLY زنده شود "
            "(که امروز زنده است). throttle واقعی از bcm.learned_pressure می‌آید."
        ),
    },

    # ── vault_bridge: شاهدِ RAG از ابسیدین ───────────────────────────────────
    "vault_bridge.rag_evidence": {
        "produced_by": "_ops/memory/vault_bridge.py → retrieval_router.py",
        "field": "rag_evidence (chunks from 109,220 vault notes)",
        "actuator": "retrieval_router (context injection)",
        "gate": "OCTOPUS_WIRE_VAULT_RAG",
        "status": "wired",   # به contextِ تصمیم تزریق می‌شود
        "propose_only": False,
        "verified_at": "2026-08-08",
        "evidence": (
            "retrieval_router.py:92-93: vault_bridge.search_vault_evidence صدا زده "
            "می‌شود و evidence در contextِ goal_directed تزریق می‌شود. "
            "این یک effectorِ زنده است — شاهدِ معنا به تصمیم می‌رسد."
        ),
    },

    # ── latent_space: بردارِ آگاهی ۴۸بُعدی ──────────────────────────────────
    "latent_space.vector": {
        "produced_by": "_ops/memory/latent_space.py → state/memory/latent-vectors.jsonl",
        "field": "48-dim awareness vector",
        "actuator": None,   # برای retrieval استفاده می‌شود ولی نه برای تصمیم
        "gate": "OCTOPUS_WIRE_LATENT_PERSIST",
        "status": "display-only",
        "propose_only": None,
        "verified_at": "2026-08-08",
        "evidence": (
            "بردار در latent-vectors.jsonl persist می‌شود ولی مصرف‌کنندهٔ decision ندارد. "
            "در consolidation record ضبط می‌شود ولی کسی آن را برای تصمیم نمی‌خواند."
        ),
    },
}


def status_counts() -> dict:
    """شمارشِ سریع: چند حس وصل، چند display، چند dead، چند shadow.

    برای dashboardها و snapshot. $0."""
    from collections import Counter
    c = Counter(e["status"] for e in EFFECTORS.values())
    return {"total": len(EFFECTORS), **dict(c)}


def dead_outputs() -> list:
    """فهرستِ حس‌هایی که تولید می‌شوند ولی هیچ مصرف‌کننده‌ای ندارند.

    این‌ها خودِ بیماریِ «sensor-rich/actuator-poor» هستند — کارِ بعدی وصل‌کردنشان است."""
    return [name for name, e in EFFECTORS.items() if e["status"] == "dead-output"]


def display_only() -> list:
    """فهرستِ حس‌هایی که به مالک نمایش داده می‌شوند ولی action نمی‌سازند."""
    return [name for name, e in EFFECTORS.items() if e["status"] == "display-only"]


def wired() -> list:
    """فهرستِ حس‌هایی که واقعاً به یک اکچوئیتور وصل‌اند (حلقهٔ بسته)."""
    return [name for name, e in EFFECTORS.items() if e["status"] == "wired"]


if __name__ == "__main__":
    import json
    print(json.dumps({
        "counts": status_counts(),
        "dead_outputs": dead_outputs(),
        "display_only": display_only(),
        "wired": wired(),
    }, ensure_ascii=False, indent=2))
