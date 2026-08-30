#!/usr/bin/env python3
"""تست STAGE 3: fitness ضدreward-hacking (فقط APPROVAL انسانی + تطبیق) و قفل σ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("fitness")
import opslib       # noqa: E402
import fitness      # noqa: E402
import replication  # noqa: E402


def _seed_honest_cell():
    harness.add_outbox_jsonl(ENV["brain"], [{"event": "sent", "business": "ziman"}] * 5
                             + [{"event": "rejected", "business": "ziman"}] * 2)
    harness.add_outbox_rows(ENV["brain"], [("ziman", "sent")] * 5 + [("ziman", "rejected")] * 2)
    harness.add_usage(ENV["brain"], [(opslib.today(), "deepseek", "ziman", 5000, 2000, 0.01)])


def _seed_tampered_cell():
    # مدعی ۱۰ sent در jsonl ولی db فقط ۲ → دستکاری (fitness جعلی برای گرفتن ساب‌ایجنت)
    harness.add_outbox_jsonl(ENV["brain"], [{"event": "sent", "business": "painting"}] * 10)
    harness.add_outbox_rows(ENV["brain"], [("painting", "sent")] * 2)


def t_acceptance_from_human_events_only():
    _seed_honest_cell()
    rep = fitness.compute(write=False)
    z = rep["cells"]["ziman"]
    assert z["judged"] == 7 and abs(z["acceptance_rate"] - 5 / 7) < 1e-3, z
    assert "outbox.jsonl" in rep["acceptance_source"]


def t_reward_hacking_excluded():
    _seed_tampered_cell()
    rep = fitness.compute(write=False)
    p = rep["cells"]["painting"]
    assert p.get("excluded") and p["reason"] == "integrity-mismatch", p
    assert rep["integrity_alerts"], "دستکاری باید alert بدهد"


def t_shadow_until_4_weeks():
    rep = fitness.compute(write=False)
    assert rep["authoritative"] is False, "بدون ~۴ هفته دادهٔ EXPERIENCE باید سایه بماند"


def t_sigma_pre_replication():
    s = replication.sigma_state(active_cells=2)
    assert s["zone"] == "pre-replication" and s["sigma_effective"] == 0.0, s


def t_sigma_over_one_alerts():
    lg = opslib.genome_ledger()
    for _ in range(3):
        lg.append("APPROVAL", {"origin": {"loop": "replication"}, "cell": "x"}, actor="approval-queue")
    s = replication.sigma_state(active_cells=2)
    assert s["sigma_effective"] == 1.5 and s["zone"] == "cancer-axis", s
    assert any("cancer-axis" in a for a in s["alerts"]), s


def t_no_spawn_without_double_gate():
    rep = replication.evaluate(write=False)
    assert rep["proposals_written"] == [], "پیش از گیت دوقفله هیچ PROPOSAL نباید نوشته شود"
    assert rep["live_gate"]["open"] is False
    assert "2026-07-21" in rep["live_gate"]["why"] or "flag" in rep["live_gate"]["why"]
    # واجد شرایط بودن ziman (نرخ 71٪ ≥ 40٪ با ۷ داوری) فقط در would_propose دیده شود
    assert "ziman" in rep["eligible_cells"], rep["eligible_cells"]


def t_projectf_excluded():
    assert "PROJECT_F" in replication.EXCLUDED_ORGANS
    assert "projectf" in replication.EXCLUDED_CELLS


def t_fake_approval_wall():
    # دیوار باربر: ledger تنها کانالی است که ایجنت می‌تواند بنویسد — جعل APPROVAL/EXPERIENCE
    # در آن باید در σ دیده شود (حمله رسیده) ولی acceptance_rate را که فقط از عمل انسانی
    # outbox.jsonl ⟂ core.db می‌آید، تکان ندهد.
    before = fitness.compute(write=False)["cells"]["ziman"]
    s0 = replication.sigma_state(active_cells=2)["sigma_effective"]
    lg = opslib.genome_ledger()
    for _ in range(5):
        lg.append("APPROVAL", {"origin": {"loop": "replication"}, "cell": "ziman"},
                  actor="approval-queue")
    lg.append("NOTE", {"subtype": "EXPERIENCE", "cell": "ziman", "claim": "sent x100"},
              actor="agent")
    s1 = replication.sigma_state(active_cells=2)["sigma_effective"]
    assert s1 > s0, (s0, s1)   # جعل واقعاً در ledger نشست — تست الکی پاس نمی‌شود
    rep = fitness.compute(write=False)
    z = rep["cells"]["ziman"]
    assert z["acceptance_rate"] == before["acceptance_rate"], (before, z)
    assert z["judged"] == before["judged"], (before, z)
    assert not z.get("excluded"), z
    assert rep["authoritative"] is False, "EXPERIENCE جعلی نباید گیت سایه را باز کند"


if __name__ == "__main__":
    failed = harness.run([
        ("پذیرش فقط از رویداد انسانی sent/rejected", t_acceptance_from_human_events_only),
        ("fitness جعلی → حذف cell + alert", t_reward_hacking_excluded),
        ("fitness عددی تا ۴ هفته فقط سایه", t_shadow_until_4_weeks),
        ("σ پیش از تکثیر: صفر/pre-replication", t_sigma_pre_replication),
        ("σ>1 → خط قرمز محور سرطان + توقف", t_sigma_over_one_alerts),
        ("بدون گیت دوقفله هیچ spawn-proposal", t_no_spawn_without_double_gate),
        ("PROJECT_F مستثنا تا GATE 0", t_projectf_excluded),
        ("APPROVAL جعلی در ledger → acceptance_rate بی‌حرکت", t_fake_approval_wall),
    ])
    sys.exit(1 if failed else 0)
