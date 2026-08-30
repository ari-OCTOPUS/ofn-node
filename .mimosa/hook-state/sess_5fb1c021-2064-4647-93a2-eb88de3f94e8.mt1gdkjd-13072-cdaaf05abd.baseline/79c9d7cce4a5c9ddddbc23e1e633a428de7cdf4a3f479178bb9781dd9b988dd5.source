"""test_power_isolation_guard.py — یک پروبِ بدایزوله نباید بتواند سیستمِ زنده را بخواباند.

حادثهٔ ۲۰۲۶-۰۷-۲۸ ۱۹:۵۷:۲۱ — پنج عملِ قدرت در **یک ثانیه** در
`state/telegram/power-audit.jsonl` ثبت شد: apply_budget(رد) · panic(انجام) ·
restart(رد) · resume-all(انجام) · stop(انجام). پنج عمل در یک ثانیه کارِ انسان
نیست؛ یک پروب بود که `power` را بعد از ماژولِ دیگری import کرده بود، وقتی
`opslib` از قبل با مسیرهای **زنده** بایند شده بود.

`stop_organism()` یک `STOP-ORGANISM` واقعی نوشت. چون `RESTART-REQUESTED` همراهش
نبود، معنایش «تا وقتی انسان پاکش کند بالا نیا» بود: ارگانیسم و مرکز ۳۰ دقیقه
خوابیدند و مالک باید دستی فایل را حذف می‌کرد.

چرا `harness` جلویش را نگرفت
────────────────────────────
گرفت — وقتی **اول** صدا زده شود. `opslib` مسیرهایش را در زمانِ import می‌بندد
(opslib.py:32)، پس اگر چیزی زودتر importش کرده باشد، `harness.setup` بعدی فقط
`os.environ` را عوض می‌کند و ثابت‌های از-قبل-محاسبه‌شده زنده می‌مانند. تستِ
`test_tg_power` خودش سالم است و تنها هم که اجرا شود درست ایزوله می‌شود.

چرا گارد در `power.py` نشست نه در تست
─────────────────────────────────────
گاردِ داخلِ تست فقط همان تست را می‌پوشاند، و مهاجم اینجا **پروبِ دست‌نویس** بود
نه تست. گارد باید جایی باشد که واقعاً می‌نویسد.

⚠️ و جهتِ fail عمداً برعکسِ عادت است: هر ابهامی → **اجازه**. بستنِ ترمزِ
اضطراریِ واقعی بدتر از یک نشانگرِ سرگردان است. گارد فقط حالتی را رد می‌کند که
خودش قابلِ اثبات باشد — «این پروسه ادعای sandbox دارد و نشانگر جای دیگری
می‌افتد».
"""
import os
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness  # noqa: E402
ENV = harness.setup("power-isolation-guard")

_OPS = _HERE.parent
_LIVE = harness.REAL_VAULT / "_ops"


def _run(code: str) -> str:
    """کد را در یک پروسهٔ **تازه** بدوان — چون کلِ باگ دربارهٔ ترتیبِ import در
    یک پروسه است و درون‌پروسه‌ای قابلِ بازتولید نیست."""
    boot = (
        "import sys\n"
        f"sys.path.insert(0, r'{_OPS}')\n"
        f"sys.path.insert(0, r'{_OPS / 'budget'}')\n"
        f"sys.path.insert(0, r'{_OPS / 'telegram_center'}')\n"
    )
    out = subprocess.run([sys.executable, "-X", "utf8", "-c", boot + code],
                         capture_output=True, text=True, encoding="utf-8",
                         errors="replace", timeout=180)
    return (out.stdout or "") + (out.stderr or "")


def t_a_a_mis_isolated_probe_cannot_stop_the_live_organism():
    """بازتولیدِ دقیقِ حادثه: opslib اول (زنده)، بعد ادعای sandbox."""
    live_marker = _LIVE / "STOP-ORGANISM"
    existed = live_marker.exists()
    out = _run(
        "import opslib, os\n"
        "os.environ['ORG_ROOT'] = r'C:\\\\Users\\\\x\\\\Temp\\\\pretend-sandbox'\n"
        "import power\n"
        "ok, msg = power.stop_organism()\n"
        "print('OK=', ok)\n"
    )
    assert "OK= False" in out, out[-500:]
    assert live_marker.exists() == existed, (
        "پروبِ بدایزوله نشانگرِ زنده را عوض کرد — دقیقاً همان حادثه")


def t_b_panic_is_blocked_too_because_a_fake_emergency_is_still_fake():
    """`panic` جزو EMERGENCY_ACTIONS است و عمداً پشتِ فلگ قفل نیست. ولی اضطرارِ
    یک پروسه‌ای که فکر می‌کند در sandbox است، خودش ساختگی است."""
    out = _run(
        "import opslib, os\n"
        "os.environ['ORG_ROOT'] = r'C:\\\\Users\\\\x\\\\Temp\\\\pretend-sandbox'\n"
        "import power\n"
        "ok, _ = power.panic()\n"
        "print('OK=', ok)\n"
    )
    assert "OK= False" in out, out[-500:]
    assert not (_LIVE / "HALT-ALL").exists(), "HALT-ALLِ زنده ساخته شد"


def t_c_a_properly_isolated_test_is_not_blocked():
    """اگر گارد تستِ سالم را هم ببندد، فردا کسی خاموشش می‌کند و ما به نقطهٔ صفر
    برمی‌گردیم. ایزوله‌سازیِ درست باید کاملاً بی‌اصطکاک بماند."""
    out = _run(
        f"import sys; sys.path.insert(0, r'{_HERE}')\n"
        "import harness\n"
        "ENV = harness.setup('guard-inner')\n"
        "import opslib, power\n"
        "from pathlib import Path\n"
        "ok, _ = power.stop_organism()\n"
        "print('OK=', ok)\n"
        "print('SANDBOX=', Path(opslib.STOP_ORGANISM).exists())\n"
    )
    assert "OK= True" in out, out[-500:]
    assert "SANDBOX= True" in out, out[-500:]
    assert not (_LIVE / "STOP-ORGANISM").exists(), "درختِ زنده لمس شد"


def t_d_production_is_never_blocked():
    """بدونِ ORG_ROOT ادعای ایزوله‌بودنی در کار نیست → گارد باید ساکت باشد.

    این مهم‌ترین بندِ فایل است: اگر این بشکند، مالک روزی `/panic` می‌زند و
    هیچ اتفاقی نمی‌افتد.
    """
    out = _run(
        "import os\n"
        "os.environ.pop('ORG_ROOT', None)\n"
        "import power\n"
        "print('MISMATCH=', repr(power._isolation_mismatch()))\n"
    )
    assert "MISMATCH= ''" in out, out[-500:]


def t_e_a_broken_guard_defaults_to_allowing_the_brake():
    """جهتِ fail عمدی است. اگر خودِ گارد بترکد، ترمز باید کار کند."""
    out = _run(
        "import power, opslib, os\n"
        "os.environ['ORG_ROOT'] = 'x'\n"
        "class Boom:\n"
        "    def __fspath__(self): raise RuntimeError('boom')\n"
        "opslib.STOP_ORGANISM = Boom()\n"
        "print('MISMATCH=', repr(power._isolation_mismatch()))\n"
    )
    assert "MISMATCH= ''" in out, out[-500:]


def t_f_the_live_tree_is_clean_after_all_of_this():
    """ناوردیِ ختمِ فایل: هیچ‌کدام از این تست‌ها نباید ردی در درختِ زنده بگذارد."""
    for name in ("STOP-ORGANISM", "RESTART-REQUESTED", "HALT-ALL"):
        assert not (_LIVE / name).exists(), f"نشانگرِ زنده جا ماند: {name}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_power_isolation_guard: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
