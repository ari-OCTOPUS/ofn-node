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
         "test_attribution.py"]

if __name__ == "__main__":
    failed = []
    for t in TESTS:
        print(f"\n── {t} " + "─" * (60 - len(t)))
        r = subprocess.run([sys.executable, "-X", "utf8", str(HERE / t)],
                           cwd=str(HERE), timeout=300)
        if r.returncode != 0:
            failed.append(t)
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
