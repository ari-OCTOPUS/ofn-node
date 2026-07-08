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
         "test_cockpit.py", "test_project_f.py", "test_studio_telegram.py"]
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
