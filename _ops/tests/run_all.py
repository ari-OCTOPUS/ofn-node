#!/usr/bin/env python3
"""اجرای کل سوئیت متابولیسم/مناظره/تکثیر — هر تست در پروسهٔ جدا (env ایزوله).
اجرا: python -X utf8 run_all.py"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TESTS = ["test_client.py", "test_telemetry.py", "test_organ_gate.py",
         "test_epoch.py", "test_debate.py", "test_fitness_sigma.py"]

if __name__ == "__main__":
    failed = []
    for t in TESTS:
        print(f"\n── {t} " + "─" * (60 - len(t)))
        r = subprocess.run([sys.executable, "-X", "utf8", str(HERE / t)],
                           cwd=str(HERE), timeout=300)
        if r.returncode != 0:
            failed.append(t)
    print("\n" + "=" * 66)
    if failed:
        print(f"❌ شکست: {', '.join(failed)}")
        sys.exit(1)
    print(f"✅ همهٔ {len(TESTS)} فایل تست سبز")
