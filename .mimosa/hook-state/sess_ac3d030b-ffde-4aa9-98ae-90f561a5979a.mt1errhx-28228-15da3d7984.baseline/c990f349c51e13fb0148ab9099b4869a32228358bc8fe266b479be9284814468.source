#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SILENT-WINDOW-LAUNCHER — اجرای Live-4 فقط پس از ریستِ مشاهده‌شدهٔ سهمیه.
بدون scheduler: خودت (یا نشست بعدی ایجنت) این را یک‌بار صدا می‌زند؛
اگر ریست دیده شد پنجرهٔ رزرو باز و درایور اجرا می‌شود؛ وگرنه QUOTA-RESET-NOT-OBSERVED."""
import json, sys
from pathlib import Path
ROOT = Path(r"F:/backup")
sys.path.insert(0, str(ROOT/"_ops")); sys.path.insert(0, str(ROOT/"_ops/cortex")); sys.path.insert(0, str(ROOT/"_ops/budget"))
import live4_reservation as LR
PREV_DAY = "2026-08-19"   # آخرین روزِ مصرف‌شدهٔ ثبت‌شده
out = LR.start(PREV_DAY)
print(json.dumps(out, ensure_ascii=False)[:300])
if not out.get("active"):
    print("QUOTA-RESET-NOT-OBSERVED — remain blocked (24h rule)")
    sys.exit(2)
rc = 0
try:
    import subprocess
    rc = subprocess.run([sys.executable, "-X", "utf8",
        str(ROOT/"06-EVIDENCE/CL01-191-20260818-2233/live4/live4_driver.py")],
        cwd=str(ROOT)).returncode
finally:
    LR.stop(f"driver-finished-rc{rc}")
