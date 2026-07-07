#!/usr/bin/env python3
"""اجرای کل سوئیت متابولیسم/مناظره/تکثیر — هر تست در پروسهٔ جدا (env ایزوله).
اجرا: python -X utf8 run_all.py"""
import datetime
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TESTS = ["test_client.py", "test_telemetry.py", "test_organ_gate.py",
         "test_epoch.py", "test_debate.py", "test_fitness_sigma.py",
         "test_budget_gate_v2.py", "test_money_gate.py", "test_capability_gate.py"]

# A3: markerِ capability فقط با اجرای سبزِ کاملِ همین سوئیت نوشته می‌شود؛ هر شکست revokeش می‌کند
# (fail-closed). این تنها یکی از سه شرطِ capability_gate است — به‌تنهایی هیچ گیتی باز نمی‌کند.
CAPABILITY_MARKER = HERE.parent / "state" / "CAPABILITY-OK.flag"

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
        try:
            CAPABILITY_MARKER.unlink()   # هر شکست = لغوِ توانایی (fail-closed)
        except OSError:
            pass
        print(f"❌ شکست: {', '.join(failed)}  (capability revoked)")
        sys.exit(1)
    CAPABILITY_MARKER.parent.mkdir(parents=True, exist_ok=True)
    CAPABILITY_MARKER.write_text(
        f"{datetime.datetime.now().isoformat(timespec='seconds')} green: {','.join(TESTS)}\n", "utf-8")
    print(f"✅ همهٔ {len(TESTS)} فایل تست سبز  (capability marker نوشته شد)")
