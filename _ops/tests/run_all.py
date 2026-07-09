#!/usr/bin/env python3
"""اجرای کل سوئیت متابولیسم/مناظره/تکثیر — هر تست در پروسهٔ جدا (env ایزوله).
اجرا: python -X utf8 run_all.py"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TESTS = ["test_client.py", "test_telemetry.py", "test_organ_gate.py",
         "test_epoch.py", "test_debate.py", "test_fitness_sigma.py",
         "test_budget_gate_v2.py", "test_money_gate.py", "test_capability_gate.py",
         "test_attribution.py", "test_panel_lead.py",
         "test_chrono_heartbeat.py", "test_chrono_langar.py",
         "test_telegram_channel.py", "test_leg.py", "test_doctor.py",
         "test_phase5.py", "test_spectral.py", "test_chamber.py",
         "test_calibration.py", "test_box.py", "test_evolution.py",
         "test_box_b134.py", "test_sensory.py", "test_rhythm.py",
         "test_cockpit.py", "test_project_f.py", "test_studio_telegram.py",
         "test_live_loop.py", "test_dual_brain.py", "test_acquisition.py",
             "test_neural.py", "test_deep_pf.py", "test_pf_full.py", "test_frontier.py",
             "test_organism_protective.py", "test_canonical_consolidation.py",
             "test_sprint_beat.py", "test_approval_queue_consistency.py",
             "test_consolidation_wiring.py", "test_spinal_cord_w1.py",
             "test_afferent_path_w2.py", "test_doctor_evolution_wiring.py",
             "test_box_wiring.py", "test_lead_leg_loop.py",
             "test_human_append_guard.py", "test_idea_graph.py",
             "test_connection_selftest.py", "test_germline_wiring.py",
             "test_checkpoint_wiring.py", "test_spectral_wiring.py",
             "test_profile_w3.py", "test_llm_routing_smoke.py",
             "test_barbell_attribution.py", "test_relationships_wired.py",
             "test_phase0_safety_net.py", "test_phase1_wiring.py",
             "test_phase2_scheduler.py", "test_phase4_epistemics.py",
             "test_phase3_trackb.py", "test_phase5_epistemics_wiring.py",
             "test_dashboard.py", "test_cardiac_allometry.py",
         "test_baseline.py", "test_held_out_evaluator.py", "test_phase_gate.py",
         "test_rfc_sweep.py", "test_consolidation_distinguish.py", "test_gate_sweep.py",
         "test_latent_space.py", "test_encoders.py", "test_consolidation_latent.py",
         "test_bcm_forgetting.py"]
# تست‌های خارج از _ops/tests/ (path tuyệtق)
EXTRA_TESTS = [HERE.parents[1] / "07 - Knowledge" / "Time-Architecture" / "test_fusion_sim.py",
               HERE.parents[1] / "07 - Knowledge" / "school-memory" / "test_curriculum.py"]

if __name__ == "__main__":
    failed = []
    for t in TESTS + EXTRA_TESTS:
        p = HERE / t          # نام‌های نسبیِ TESTS → _ops/tests؛ EXTRA_TESTSِ absolute دست‌نخورده می‌ماند
        label = p.name
        print(f"\n── {label} " + "─" * (60 - len(label)))
        r = subprocess.run([sys.executable, "-X", "utf8", str(p)],
                           cwd=str(p.parent), timeout=300)
        if r.returncode != 0:
            failed.append(label)
    print("\n" + "=" * 66)

    # A3: markerِ capability فقط با اجرای سبزِ کاملِ سوئیت نوشته می‌شود (با fingerprintِ کدِ پول)؛
    # هر شکست revokeش می‌کند (fail-closed). تنها یکی از سه شرطِ گیت است — به‌تنهایی هیچ باز نمی‌کند.
    sys.path.insert(0, str(HERE.parent / "budget"))
    try:
        import capability_gate as _cg
    except Exception as _e:  # noqa: BLE001 — گزارشِ سوئیت نباید به import گره بخورد
        _cg = None
        print(f"(هشدار: capability_gate لود نشد، marker دست‌نخورده: {_e})")

    if failed:
        if _cg:
            _cg.revoke_capability()
        print(f"❌ شکست: {', '.join(failed)}  (capability revoked)")
        sys.exit(1)
    if _cg:
        _cg.mark_capability("green: " + ",".join(TESTS))
    print(f"✅ همهٔ {len(TESTS)} فایل تست سبز  (capability marker با fingerprint نوشته شد)")
