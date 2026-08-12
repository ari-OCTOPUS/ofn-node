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
        # ADR-035: APPLY=1 may gate_internal via protective_skip; APPLY=0 proposal/SHADOW.
        "actuator": "wiring.emit_pain_assessment → organism/brain_worker (executable-gated)",
        "gate": "OCTOPUS_NEURAL_LEARNED_APPLY (+ PROPOSAL for shadow fold)",
        "status": "armed-apply",
        "propose_only": False,
        "verified_at": "2026-08-12",
        "evidence": (
            "ADR-035: OCTOPUS_NEURAL_LEARNED_APPLY=1; organism/brain_worker set "
            "protective_skip only when executable=True. Rollback: APPLY=0 + restart. "
            "Explicit control-plane halt: wiring.request_protective_halt."
        ),
    },
    "bcm.weights_bidirectional": {
        "produced_by": "_ops/neural/bcm.py → state/bcm-weights.json",
        "field": "weights (n_keys potentiated)",
        "actuator": None,
        "gate": None,
        # ۰۸-۰۸ دیپ‌چک: bcm-weights.json خواننده دارد (cockpit_readmodel.read_bcm،
        # live_snapshot، miniapp_state، export_status، approval_channel blueprint) ولی
        # همگی برای نمایش/گزارش‌اند (rule R19، snapshot، کارتِ بلوپرینت)، نه تصمیم.
        # پس dead-output دقیق نیست — display-only است. تصمیمی که از وزنِ BCM بخواند: هیچ.
        "status": "display-only",
        "propose_only": None,
        "verified_at": "2026-08-08",
        "evidence": (
            "bcm-weights.json خواننده دارد: cockpit_readmodel.py:128 (rule R19)، "
            "live_snapshot.py:275، miniapp_state.py:943، export_status.py:181. "
            "ولی همگی display/report هستند. تصمیمی که وزنِ BCM را در یک انتخاب بخواند: هیچ."
        ),
    },

    # ── Hebbian: هم‌خانواده‌سازی ────────────────────────────────────────────
    "hebbian.associations": {
        "produced_by": "_ops/neural/hebbian.py → neural/hebbian.json",
        "field": "co-occurrence associations",
        "actuator": None,
        "gate": "OCTOPUS_WIRE_HEBBIAN",
        # ۰۸-۰۸ دیپ‌چک: deep_think.py:168 هببیان را در context تولید می‌خواند
        # (تزریق به پرامپت، نه تصمیم). پس display-only است، نه dead-output.
        "status": "display-only",
        "propose_only": None,
        "verified_at": "2026-08-08",
        "evidence": (
            "hebbian.json خواننده دارد: deep_think.py:168 (_jload برای context)، "
            "cockpit_readmodel، wiring. ولی برای context-injection/display است، "
            "نه تصمیمِ action."
        ),
    },

    # ── Consolidation: بینش‌های بلندمدت ─────────────────────────────────────
    "consolidation.insights": {
        "produced_by": "_ops/memory/consolidation.py → state/memory/memory.db",
        "field": "conclusions / frontier (insights) + episodic/procedural",
        "actuator": "memory/retrieval_router (episodic/procedural search)",
        "gate": "OCTOPUS_WIRE_CONSOLIDATION",
        # ۰۸-۰۸ دیپ‌چک: memory.db دو نوع داده دارد. episodic/procedural توسط
        # retrieval_router در نقطهٔ تصمیم search می‌شود (wired). ولی conclusions/
        # frontier (بینش‌های تکراریِ ۲۹۰+ سیکل) هیچ مصرف‌کننده‌ای ندارد. پس این
        # یک مورد مختلط است — بخشی wired، بخشی dead.
        "status": "wired",  # برای episodic/procedural
        "propose_only": None,
        "verified_at": "2026-08-08",
        "evidence": (
            "memory.db: retrieval_router.py:76-82 episodic/procedural را در نقطهٔ "
            "تصمیم search می‌کند (wired). ولی conclusions/frontier (بینش‌های "
            "تکراری ۲۹۰+ سیکل) dead ماندند — retrieval_router فقط namespace‌های "
            "episodic/procedural را می‌خواند، نه conclusions/frontier را."
        ),
    },

    # ─ـ deep_dive.smallest_fix: دقیق‌ترین خروجیِ تشخیص ─────────────────────
    "deep_dive.smallest_fix": {
        "produced_by": "_ops/doctor/self_knowledge.py → state/doctor/self-knowledge-latest.json",
        "field": "smallest_fix (یک جملهٔ دقیق)",
        "actuator": "cortex/improve.py gather_signals → proposal (propose-only)",
        "gate": "OCTOPUS_WIRE_DOCTOR_SELFKNOW (content source); improve path $0",
        "status": "partial",  # 2026-08-07: به proposal وصل شد؛ auto_applicable=False
        "propose_only": True,
        "verified_at": "2026-08-12",
        "evidence": (
            "improve.py:318-433: smallest_fix از deep_dive خوانده می‌شود و "
            "proposal با source=smallest_fix می‌سازد (auto_applicable=False). "
            "organ_dialogue همچنان نمایش می‌دهد. brain_pulse هم focus/SF را به چت "
            "می‌آورد. هنوز به action_bridge/apply خودکار وصل نیست — propose-only."
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
