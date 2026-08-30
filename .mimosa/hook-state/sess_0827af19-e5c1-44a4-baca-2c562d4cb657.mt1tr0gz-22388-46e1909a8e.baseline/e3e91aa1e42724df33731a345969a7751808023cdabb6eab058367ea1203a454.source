#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_safety_flags_stay_armed.py — نگهبانِ tracked برای فایلِ untracked.

`_ops/OCTOPUS-flags.cmd` در `.gitignore` است. یعنی هر رأیی که در آن فایل ثبت
می‌شود **تاریخچهٔ گیت ندارد**: نه می‌شود فهمید کِی عوض شد، نه چه کسی، نه
برگرداندش. این دقیقاً همان چیزی است که ۰۸-۰۳ دربارهٔ همین فایل ثبت شد.

مرزِ gitignore شکسته نمی‌شود (فایل ممکن است روزی مقدارِ حساس بگیرد). به‌جایش
دو نگرانی جدا می‌شوند: **فایلِ زنده** جای مقدار می‌ماند، و **این تستِ tracked**
جای حافظه. اگر فایل بازتولید، ویرایش یا خراب شود و یکی از فلگ‌های زیر خاموش
گردد، این تست قرمز می‌شود و رأی برمی‌گردد.

چرا نامِ فلگ کافی نیست: `test_phantom_guards.py` قبلاً اثبات می‌کند هر نامی که
کد می‌خواند در این فایل **ظاهر** شود (جهشِ M4، ۰۸-۰۴). ولی `=0` هم نام را
حفظ می‌کند. آن گارد اعلان را می‌پاید، این یکی **مقدار** را.

⚠️ صداقتِ منشأ — این دو رأی یک‌جور نیستند و عمداً برچسبشان فرق دارد:
  · DECISION_GATE : رأیِ صریحِ مالک، ۲۰۲۶-۰۸-۰۳، «decision_gate رو مسلح کن».
  · KILL_SEAM     : زیرِ مأموریتِ کلیِ «بقیه شکاف‌های اسکن رو هم رفع کن»
                    مسلح شد، نه با یک رأیِ جداگانه دربارهٔ خودش. جهتش
                    fail-safe است (فقط deny اضافه می‌کند) و برگرداندنش یک
                    خط است. اگر مالک نخواستش، همین خط را بردارد و این تست
                    را هم به‌روز کند — نه اینکه تست وانمود کند رأی داشت.
"""
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

ENV = harness.setup("safety-flags-armed")

#: فایلِ **زنده** موضوعِ تست است، نه یک کپیِ فیکسچری — چون سؤال دقیقاً این است
#: که «چیزی که واقعاً بوت می‌شود چه می‌گوید». فقط خوانده می‌شود.
FLAGS = harness.REAL_VAULT / "_ops" / "OCTOPUS-flags.cmd"

#: فلگ → (مقدارِ لازم، منشأ). منشأ در پیامِ خطا چاپ می‌شود تا هر کسی که این
#: قرمز را می‌بیند بداند دارد رأیِ چه کسی را برمی‌گرداند.
MUST_BE_ARMED = {
    "OCTOPUS_WIRE_DECISION_GATE": ("1", "رأیِ صریحِ مالک ۲۰۲۶-۰۸-۰۳"),
    "OCTOPUS_WIRE_KILL_SEAM": ("1", "مأموریتِ کلیِ رفعِ شکاف ۲۰۲۶-۰۸-۰۴ (نه رأیِ جداگانه)"),
}

#: فلگ‌هایی که خاموش‌بودنشان جهتِ امن است — هیچ‌کدام نباید بی‌صدا روشن شوند.
MUST_NOT_BE_ARMED = {
    # بازکردنِ endpointهای خواندنیِ مینی‌اپ روی هر کاربرِ تلگرام. پیش‌فرضِ کد
    # «1» است؛ تنها راهِ بازکردنش یک خطِ صریحِ `=0` در همین فایل است.
    "OCTOPUS_MINIAPP_READ_OWNER_GATE": "0",
}

_ACTIVE_SET = re.compile(r"^\s*set\s+([A-Z0-9_]+)\s*=\s*(.*?)\s*$", re.IGNORECASE)


def _active_assignments():
    """فقط خطوطِ `set` ِ **اجراشونده**. خطی که با `::` یا `rem` شروع شود کامنت
    است و cmd.exe اجرایش نمی‌کند — پس ارزشی که اعلام می‌کند واقعی نیست."""
    out = {}
    raw = FLAGS.read_bytes().decode("utf-8", errors="replace")
    for line in raw.split("\r\n"):
        s = line.strip()
        if not s or s.startswith("::") or s.lower().startswith("rem "):
            continue
        m = _ACTIVE_SET.match(s)
        if m:
            out[m.group(1).upper()] = m.group(2)
    return out


def t_a_the_flags_file_is_readable_and_substantial():
    """گاردِ «اسکنر خراب است»: فایلِ غایب یا نصفه نباید سبز بدهد.

    عددِ کف از واقعیت می‌آید (۱۴۷ خطِ فعال در ۰۸-۰۴)؛ ۱۰۰ یعنی «حتماً همان
    فایل است»، نه یک stub یا یک نسخهٔ نصفه‌خوانده‌شدهٔ CRLF-خراب."""
    assert FLAGS.exists(), f"محلِ اعلام غایب است: {FLAGS}"
    got = _active_assignments()
    assert len(got) > 100, (
        f"فقط {len(got)} انتساب خوانده شد — فایل نصفه است یا پایان‌خطش شکسته "
        "(حادثهٔ ۰۸-۰۱: LF ⇒ cmd.exe یک‌درمیان خواند ⇒ ۵۹ از ۱۵۶ فلگ)")


def t_b_safety_flags_are_still_armed():
    """قلبِ گارد. اگر فایلِ untracked بازتولید شود و یکی از این‌ها بیفتد،
    تنها چیزی که خبر می‌دهد همین قرمز است."""
    got = _active_assignments()
    for name, (want, origin) in sorted(MUST_BE_ARMED.items()):
        assert name in got, (
            f"«{name}» دیگر خطِ `set` ِ فعال ندارد — مسلح‌سازی گم شد. "
            f"منشأ: {origin}")
        assert got[name] == want, (
            f"«{name}» حالا `{got[name]}` است، نه `{want}`. منشأ: {origin}")


def t_c_fail_safe_flags_did_not_get_armed_silently():
    """قرینه: خاموشی هم می‌تواند رأی باشد. بازکردنِ گیتِ خواندنِ مینی‌اپ روی
    تونلِ عمومی باید یک تصمیمِ نوشته‌شده باشد، نه یک خطِ سرگردان."""
    got = _active_assignments()
    for name, forbidden in sorted(MUST_NOT_BE_ARMED.items()):
        if name in got:
            assert got[name] != forbidden, (
                f"«{name}={forbidden}» فعال شد — این جهتِ ناامن است و رأیِ "
                "صریحِ مالک می‌خواهد؛ اگر عمدی است این گارد را هم به‌روز کن")


def t_d_the_kill_seam_is_not_in_the_absence_means_on_list():
    """قاعدهٔ خانه، از سمتِ دیگر. `apply_profile` هر عضوِ `PAPER_FULL_FLAGS` را
    که در env نباشد ۱ می‌کند. یک فلگِ ایمنی که آن‌جا برود، دیگر «مسلح‌شده با
    رأی» نیست — خودبه‌خود روشن است، و روزی که کسی از آن فهرست برش دارد بی‌صدا
    خاموش می‌شود. مسلح‌سازی باید یک خطِ صریح بماند."""
    raw = FLAGS.read_bytes().decode("utf-8", errors="replace")
    idx = raw.find("PAPER_FULL_FLAGS")
    if idx < 0:
        return  # این فایل آینهٔ profile ندارد — گاردِ اصلی در test_kill_seam_wire
    block = raw[idx:idx + 4000]
    for name in MUST_BE_ARMED:
        assert name not in block, (
            f"«{name}» داخلِ بلوکِ PAPER_FULL_FLAGS رفت — آن‌جا «غیاب = روشن» "
            "است و مسلح‌سازی از دستِ مالک درمی‌آید")


def t_e_this_test_never_writes_to_the_flags_file():
    """گاردِ خودم. با AST نه زیررشته: نسخهٔ زیررشته‌ای خودش را می‌گیرد، چون
    نامِ توابعِ ممنوعه داخلِ فهرستِ ممنوعه‌اش ظاهر می‌شود."""
    import ast
    banned = {"write_text", "write_bytes", "unlink", "mkdir", "rename"}
    hits = []
    for node in ast.walk(ast.parse(Path(__file__).read_text("utf-8"))):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Attribute) and fn.attr in banned:
                hits.append(fn.attr)
            if isinstance(fn, ast.Name) and fn.id == "open" and len(node.args) > 1:
                hits.append("open(mode)")
    assert not hits, ("این تست فقط می‌خواند", hits)


def main():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("t_") and callable(v)]
    passed, failed = 0, []
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  OK  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append(t.__name__)
            print(f"  FAIL {t.__name__}: {e}")
    print(f"\ntest_safety_flags_stay_armed: {passed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
