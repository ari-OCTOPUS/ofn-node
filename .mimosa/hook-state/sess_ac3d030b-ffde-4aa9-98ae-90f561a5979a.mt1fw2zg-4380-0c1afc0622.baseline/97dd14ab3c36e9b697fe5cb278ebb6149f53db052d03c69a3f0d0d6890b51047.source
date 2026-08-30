#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mutate_live_state_guard.py — اثباتِ بازتولیدپذیرِ اینکه `test_live_state_guard.py`
واقعاً چیزی را نگه می‌دارد.

ادعای «گارد جهش‌آزموده است» بدونِ اسکریپت یک جملهٔ تبلیغاتی است. این فایل ۹ جهشِ
هدفمند در `live_state_guard.py` می‌گذارد و انتظار دارد **هر کدام تستِ مشخصِ خودش**
را قرمز کند. اجرا:  `python mutate_live_state_guard.py`

انضباطِ ثبت‌شده که اینجا کد شده است:
  · **لنگر باید یکتا باشد** — قبل از اعمال شمرده می‌شود. `replace(...,1)` به اولین
    وقوع می‌خورد که معمولاً تابعِ خواهر است، و بعد «SURVIVED» ِ دروغ می‌گیری.
  · **قبل از هر اجرا کامیت** — بازیابی `git checkout -- <file>` است و دانه‌بندی‌اش
    فایل است نه هانک. ۰۸-۰۳ همین اسکریپت یک رفعِ کامیت‌نشده را پاک کرد، چون یک بار
    اولِ جلسه کامیت کرده بودم و فکر کردم پوشش دارم. حالا اگر فایل dirty باشد
    **امتناع می‌کند**.
  · **بایت‌کدِ کهنه** — `-B` + پاک‌کردنِ `__pycache__`، وگرنه دو جهشِ هم‌اندازه در یک
    ثانیه ممکن است اصلاً اجرا نشوند و نتیجهٔ قبلی دوباره خوانده شود.
  · **SURVIVED دو معنی دارد** — گاردِ کور، یا جهشی که به هدف نخورد. تفکیک با
    «فایل واقعاً عوض شد؟» + «کدام تست قرمز شد؟». نمونهٔ واقعی: M1 اول SURVIVED شد و
    معلوم شد **تست** کور بود نه گارد (فیکسچرِ `state/../state/x` هنوز لفظاً با ریشه
    شروع می‌شود، پس حتی گاردِ بی‌abspath هم می‌گرفتش).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GUARD = HERE / "live_state_guard.py"
TEST = HERE / "test_live_state_guard.py"
REPO = HERE.parent.parent

MUTATIONS = [
    ("M1 traversal: abspath حذف",
     "return os.path.normcase(os.path.abspath(s))",
     "return os.path.normcase(s)",
     "t_traversal_cannot_escape_the_check"),
    ("M2 حالتِ append از تشخیص بیفتد",
     'any(ch in mode for ch in ("w", "a", "x", "+"))',
     'any(ch in mode for ch in ("w", "x", "+"))',
     "t_every_write_vector_raises"),
    ("M3 صفر-بایتی هرگز benign نشود",
     "            return os.path.isdir(path)",
     "            return False",
     "t_zero_byte_ops_are_recorded_but_not_blocked"),
    ("M4 همه‌چیز benign اعلام شود",
     "    benign = _benign(op, path)",
     "    benign = True",
     "t_every_write_vector_raises"),
    ("M5 sqlite هرگز داخلِ ریشه دیده نشود",
     "            hit = _inside(db)",
     "            hit = None",
     "t_every_write_vector_raises"),
    ("M6 عمقِ اجازه برنگردد (نشتِ allow)",
     "        _allow_depth -= 1",
     "        pass",
     "t_allowed_writes_are_declared_and_recorded"),
    ("M7 هر میزبان loopback شمرده شود",
     'return h.startswith("127.")',
     "return True",
     "t_external_network_is_blocked_loopback_is_not"),
    ("M8 بردارِ io.open از فهرست بیفتد",
     '    ("io.open",           io,       "open",     _wrap_open),',
     "",
     "t_every_write_vector_raises"),
    ("M9 قاعدهٔ دربرگیری بشکند",
     "if n == r or n.startswith(r + os.sep):",
     "if n == r:",
     "t_every_write_vector_raises"),
]


def _run_test() -> tuple[int, str]:
    pc = HERE / "__pycache__"
    if pc.exists():
        for f in pc.glob("*.pyc"):
            try:
                f.unlink()
            except OSError:
                pass
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("OCTOPUS_TEST_LIVE_STATE_GUARD", None)
    r = subprocess.run([sys.executable, "-B", "-X", "utf8", str(TEST)],
                       cwd=str(HERE), capture_output=True, text=True,
                       errors="replace", env=env, timeout=180)
    return r.returncode, r.stdout + r.stderr


def _restore() -> None:
    subprocess.run(["git", "checkout", "--", str(GUARD)],
                   cwd=str(REPO), check=True, capture_output=True)


def main() -> int:
    dirty = subprocess.run(["git", "status", "--porcelain", "--", str(GUARD)],
                           cwd=str(REPO), capture_output=True, text=True).stdout.strip()
    if dirty:
        print("❌ امتناع: live_state_guard.py کامیت‌نشده است.\n"
              "   بازیابیِ جهش `git checkout --` است و **کلِ فایل** را برمی‌گرداند —\n"
              "   یعنی هر ویرایشِ کامیت‌نشده‌ات را پاک می‌کند. اول کامیت کن.")
        return 2

    print("پایه (بدونِ جهش):")
    rc, out = _run_test()
    print(f"  rc={rc}  {'✅ سبز' if rc == 0 else '❌ قرمز — پایه باید سبز باشد'}")
    if rc != 0:
        print(out[-1500:])
        return 2

    killed = survived = misfired = 0
    for name, old, new, target in MUTATIONS:
        src = GUARD.read_text("utf-8")
        n = src.count(old)
        if n != 1:
            print(f"  ⚠️  {name}: لنگر {n} بار پیدا شد (باید ۱) — جهش به هدف نخورد")
            misfired += 1
            continue
        GUARD.write_text(src.replace(old, new), "utf-8")
        if GUARD.read_text("utf-8") == src:
            print(f"  ⚠️  {name}: فایل عوض نشد")
            misfired += 1
            _restore()
            continue
        rc, out = _run_test()
        if rc != 0:
            where = "همان تستِ هدف" if target in out else "تستی دیگر — بررسی کن"
            print(f"  ✅ KILLED   {name}  → قرمز ({where})")
            killed += 1
        else:
            print(f"  ❌ SURVIVED {name}  → سبز ماند ⇒ یا گاردِ کور روی {target}، "
                  f"یا فیکسچرِ تست ضعیف است")
            survived += 1
        _restore()

    print(f"\nکشته‌شده: {killed}   بازمانده: {survived}   نافرجام: {misfired}")
    rc, _ = _run_test()
    print(f"بازگردانی: rc={rc} {'✅' if rc == 0 else '❌ فایل درست برنگشت'}")
    return 0 if (survived == 0 and misfired == 0 and rc == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
