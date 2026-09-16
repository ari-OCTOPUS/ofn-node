#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_callback_emitter_parity — هر دکمه‌ای که فرستاده می‌شود، handler دارد.

شکافِ سومِ بستهٔ `telegram_contract` (VQ-TG-GAP-EMITTER-001).

تاریخچهٔ این پروژه **دو کارتِ مرده** دارد: `iv:q` و `tr:*` هر دو ساخته و
فرستاده شدند در حالی که handler ِ verbشان روی باتِ دیگری بود — مالک دکمه را
می‌زد و هیچ اتفاقی نمی‌افتاد. هر بار هم دستی کشف شد، نه با گارد.

قاعدهٔ این فایل: **هر verb ای که در `callback_data` تولید می‌شود باید روی
دیسپچرِ همان باتی که کارت را می‌فرستد شناخته باشد.**

روشِ سنجش **نحوی** است نه رشته‌ای: `ast` روی سورس، تا جمله‌ای در یک کامنت که
اسمِ یک verb را برده به‌عنوان handler شمرده نشود (درسِ «grep کامنت را می‌شمارد»).

── ۲۰۲۶-۰۸-۰۶ (تعمیم) ──────────────────────────────────────────────────────
نسخهٔ قبلیِ این فایل فقط ۴ فایلِ hardcode‌شده را می‌دید: center.py،
approval_channel.py، tool_request.py، test_cycle.py. همان شب، دقیقاً به همین
دلیل، باگی در wiring.py (تابعِ `brain_digest_beat`) کشف‌نشده ماند: دکمه‌ای با
`callback_data="mn:ap"` ساخته شد که فقط center.py هندلرش را می‌شناخت، درحالی‌که
این کارت از کانالِ organism (approval_channel.TelegramApprovalChannel روی
@Robo2725_bot) می‌رود — تلهٔ دو-باتی، نمونهٔ سوم. اسکنر چون wiring.py را اصلاً
نمی‌دید، این را رد کرد؛ کشفش دستی و بعد از گزارشِ مالک بود.

فیکسِ واقعیِ آن شب (تبدیلِ دکمه به `url`، نه `callback_data`) در wiring.py
ماند. فیکسِ این فایل، **تعمیمِ خودِ اسکنر** است: به‌جای ۴ فایل، همهٔ
`_ops/**/*.py` اسکن می‌شود (موتورِ AST در `tg_callback_scanner.py`، همسایهٔ
همین فایل) — همراه با تشخیصِ اینکه هر فایل کارتش را از کدام بات می‌فرستد
(«producing bot»، بر پایهٔ گراف importِ درون‌ـ_ops، نه حدس). جزئیاتِ کاملِ
مکانیزم و چرا محافظه‌کارانه است: بالای `tg_callback_scanner.py`.

دکمه‌های `url` (نه `callback_data`) عمداً از این چک بیرون‌اند — هرگز به هیچ
دیسپچرِ باتی نمی‌رسند (خودِ تلگرام سمتِ کلاینت چتِ بات دیگر را باز می‌کند).
همان نکته‌ای که شبِ ۰۸-۰۶ در fix ِ wiring.py و در
`test_organ_dialogue.py:t_brain_digest_beat_keyboard_has_no_dead_cross_bot_button`
مستند شد. `tg_callback_scanner.emitted_verbs` اصلاً دنبالِ کلیدِ `"url"`
نمی‌گردد — پس فیلترِ صریح لازم نیست، نبودِ کلید یعنی بیرون از دامنه."""
import sys
from pathlib import Path

import harness

ENV = harness.setup("tg-emitter-parity")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tg_callback_scanner as scanner   # noqa: E402 — بعد از sys.path (هم‌پوشه)

_OPS = scanner.OPS
CENTER = scanner.CENTER
APPROVAL = scanner.APPROVAL
TOOL_REQUEST = _OPS / "tool_request.py"
TEST_CYCLE = _OPS / "test_cycle.py"

# verbهایی که عمداً بی‌handler اند و دلیلش ثبت شده. هر افزودنی به این مجموعه
# باید دلیل داشته باشد — وگرنه همان کارتِ مرده است با نامِ دیگر.
KNOWN_HANDLERLESS = {
    "noop",       # دکمهٔ تزئینی/جداکننده
}

# ── شکاف‌های واقعی و کشف‌شده — نه طراحیِ عمدی ────────────────────────────────
# این با KNOWN_HANDLERLESS فرق دارد: آن‌جا «این verb عمداً بی‌handler است»
# است (تصمیم)، این‌جا «باگِ واقعیِ تلهٔ دو-باتی، همین تعمیم کشفش کرد، هنوز رفع
# نشده» است. رفعش دست‌کاریِ approval_channel.py می‌خواهد که خارج از دامنهٔ این
# جلسه است (فقط ابزارِ دفاعی، نه تغییرِ production). ثبت می‌شود تا اسکنر نه
# رویش کور بماند و نه بی‌دلیل CI را بشکند — سکوت درباره‌اش دقیقاً همان اشتباهی
# است که این فایل قرار است جلویش را بگیرد.
KNOWN_OPEN_GAPS = {
    # ۲۰۲۶-۰۹-۱۰ — ورودیِ ("initiative.py", "mr") بسته شد: approval_channel.py شاخهٔ
    # `mr` گرفت (_dispatch_mirror). ۳۵ روز این شکاف معاف بود در حالی که مالک روی
    # «🪞 آینه» می‌زد و «نادیده» می‌گرفت (رسیدِ زنده: update_id 732409706،
    # ۲۰۲۶-۰۹-۱۰T20:28:31). درس: معافیتِ یک دکمهٔ مرده = دکمهٔ مرده با نامِ دیگر؛
    # تستِ رفتاری‌اش: tests/test_inner_mirror_callback.py.
}


def _apply_known_gaps(path: Path, bot: str, missing: set, used: set) -> set:
    """missing منهایِ آنچه در KNOWN_OPEN_GAPS برای این (فایل، verb) ثبت شده."""
    out = set()
    for v in missing:
        key = (path.name, v)
        if key in KNOWN_OPEN_GAPS:
            used.add(key)
            continue
        out.add(v)
    return out


# ── سنجه‌ها ────────────────────────────────────────────────────────────────
def t_the_scanner_actually_finds_something():
    """اگر این بند بشکند بقیه بی‌معنی‌اند — اسکنرِ خالی همیشه سبز است."""
    emitted = scanner.emitted_verbs(CENTER) | scanner.emitted_verbs(APPROVAL)
    assert len(emitted) >= 3, f"اسکنرِ emit چیزی پیدا نکرد: {emitted}"
    handled = scanner.handled_verbs(CENTER) | scanner.handled_verbs(APPROVAL)
    assert len(handled) >= 3, f"اسکنرِ handler چیزی پیدا نکرد: {handled}"
    # تعمیمِ ۰۸-۰۶: اسکنرِ فایل باید بیش از ۴ فایلِ قدیمی ببیند، وگرنه تعمیم
    # اسمی است — همان کوریِ wiring.py دوباره رخ می‌دهد.
    all_emitters = scanner.all_emitters()
    assert len(all_emitters) >= 15, (
        f"اسکنرِ عمومی فقط {len(all_emitters)} فایل دید — کمتر از انتظار؛ "
        "دامنه‌اش دارد به همان محدودیتِ ۴-فایلیِ قدیم برمی‌گردد؟")
    assert any(f.name == "wiring.py" for f in all_emitters), (
        "wiring.py دیگر emitter شمرده نمی‌شود — دقیقاً همان فایلی که باگِ "
        "۰۸-۰۶ در آن بود و این تعمیم قرار بود ببیندش.")


def t_every_emitted_verb_is_handled_by_its_producing_bots_own_router():
    """قاعدهٔ اصلیِ تعمیم‌یافته — جایگزینِ چهار بندِ جداگانهٔ نسخهٔ قبلی.

    برایِ **هر** فایلِ `_ops/**/*.py` که واقعاً یک callback_data می‌سازد
    (`tg_callback_scanner.all_emitters`): بات(هایی) که این فایل کارتش را
    ازش می‌فرستد را پیدا کن (`producing_bots` — گراف importِ درون‌ـ_ops، نه
    حدس)، و verbهای emit‌شده را روی دیسپچرِ **همان** بات(ها) بسنج. اگر
    فایلی بی‌importer است (کدِ orphan/not-wired — مثلِ approval_channel_merge.py
    که خودش «Zero live callers» را در docstring دارد)، هیچ باتِ زنده‌ای این
    کد را اجرا نمی‌کند، پس own-router-check برایش بی‌معناست، رد می‌شود.

    این دقیقاً همان چیزی است که شبِ ۰۸-۰۶ نبود: اسکنری که wiring.py (و هر
    فایلِ دیگری، نه فقط ۴تای hardcode‌شده) را می‌بیند و می‌فهمد کارتش از
    کدام بات می‌رود."""
    stem_map = scanner.build_stem_map()
    bots_by_file = scanner.producing_bots(stem_map)
    # دیسپچرِ owner-console (conversation.callback) از طریق telegram_adapter
    # روی باتِ مرکز اجرا می‌شود؛ پس verbهای «oc:*» جزو رسیدگی‌های مرکزند.
    owner_console_router = scanner.OPS / "owner_console" / "conversation.py"
    handled = {
        "center": (scanner.handled_verbs(CENTER)
                   | scanner.handled_verbs(owner_console_router)),
        "approval": scanner.handled_verbs(APPROVAL),
    }

    violations = []
    used_gaps = set()
    for path, verbs in scanner.all_emitters().items():
        if path == CENTER:
            producing = {"center"}
        elif path == APPROVAL:
            producing = {"approval"}
        else:
            if not scanner.has_any_importer(path, stem_map):
                continue   # orphan/not-wired — هیچ باتی این کد را اجرا نمی‌کند
            producing = set(bots_by_file.get(path, frozenset()))
            if not producing:
                # فایل‌های owner_console کارتِ باتِ مرکزند (از طریق
                # telegram_adapter) — نه shared و نه کارتِ باتِ approval.
                if "owner_console" in getattr(path, "parts", ()):
                    producing = {"center"}
                else:
                    # unknown → محافظه‌کارانه یعنی shared: تا وقتی مطمئن نیستیم
                    # کدام بات می‌فرستد، هر دو باید بشناسند (هرگز به‌خاطرِ ابهام
                    # یک verbِ خطرناک را رد نکن).
                    producing = {"center", "approval"}

        verbs_to_check = verbs - KNOWN_HANDLERLESS
        for bot in sorted(producing):
            missing = verbs_to_check - handled[bot]
            missing = _apply_known_gaps(path, bot, missing, used_gaps)
            for v in sorted(missing):
                violations.append((str(path.relative_to(_OPS)), bot, v))

    assert not violations, (
        "کارتِ مرده — verb ای که یک فایل emit می‌کند ولی روترِ باتی که آن را "
        f"می‌فرستد handler ندارد (فایل، بات، verb): {violations}")

    unused = set(KNOWN_OPEN_GAPS) - used_gaps
    assert not unused, (
        f"KNOWN_OPEN_GAPS شاملِ ورودی‌ای است که دیگر بازتولید نمی‌شود "
        f"(یعنی رفع شده — پاکش کن، وگرنه یک استثنایِ مرده است): {unused}")


def t_approval_channel_merge_is_a_known_orphan_not_a_silent_blind_spot():
    """رگرسیونِ نقطه‌ایِ استثنایِ orphan — اگر approval_channel_merge.py روزی
    واقعاً wire شود (importer پیدا کند)، این بند باید قرمز شود تا کسی
    دوباره نگاهش کند؛ استثنا نباید تا ابد بی‌صدا بماند."""
    stem_map = scanner.build_stem_map()
    merge = scanner.APPROVAL_MERGE
    assert merge.exists(), "approval_channel_merge.py دیگر وجود ندارد؟"
    assert scanner.emitted_verbs(merge), "دیگر callback_data نمی‌سازد؟ استثنا بی‌مصرف شده."
    is_orphan = not scanner.has_any_importer(merge, stem_map)
    assert is_orphan, (
        "approval_channel_merge.py دیگر orphan نیست (importer پیدا کرده) — "
        "own-router-check رویش دوباره باید اجرا شود؛ از استثنای orphan در "
        "t_every_emitted_verb_is_handled_by_its_producing_bots_own_router "
        "خارجش کن و verbهایش (brain/menu) را واقعاً روی دیسپچرِ approval "
        "بسنج.")


def t_every_verb_the_center_emits_is_handled_on_its_own_router():
    """رگرسیونِ نقطه‌ایِ باقی‌مانده از نسخهٔ قبلی — تنگ و مستقیم، فقط برایِ
    خودِ CENTER (زیرمجموعه‌ای از بندِ عمومیِ بالا، ولی خطای دقیق‌تری می‌دهد
    وقتی خودِ روتر می‌شکند)."""
    emitted = scanner.emitted_verbs(CENTER) - KNOWN_HANDLERLESS
    handled_by_center = scanner.handled_verbs(CENTER)
    orphan = sorted(emitted - handled_by_center)
    assert not orphan, (
        f"کارتِ مرده — verb ای که center می‌فرستد ولی روترِ center خودش handler "
        f"ندارد (فقط روی روترِ دیگر است؟): {orphan}")


def t_every_verb_the_approval_channel_emits_is_handled_on_its_own_router():
    """همان قانون برای approval_channel — روترِ فرستنده باید handler داشته باشد."""
    emitted = scanner.emitted_verbs(APPROVAL) - KNOWN_HANDLERLESS
    handled_by_approval = scanner.handled_verbs(APPROVAL)
    orphan = sorted(emitted - handled_by_approval)
    assert not orphan, (
        f"کارتِ مرده — verb ای که approval_channel می‌فرستد ولی روترِ "
        f"approval_channel خودش handler ندارد: {orphan}")


def t_verbs_emitted_by_shared_modules_are_handled_on_both_routers():
    """`tool_request` و `test_cycle` کارتشان از **هر دو** مسیر می‌تواند برود.

    درسِ `tr:`: کارت از کانالِ ارگانیسم رفت ولی handler فقط در مرکز بود. پس
    verbِ ماژولِ مشترک باید در هر دو روتر باشد، نه یکی."""
    shared = set()
    for m in (TOOL_REQUEST, TEST_CYCLE):
        if m.exists():
            shared |= scanner.emitted_verbs(m)
    shared -= KNOWN_HANDLERLESS
    if not shared:
        return                                   # ماژولِ مشترکی کارت نمی‌سازد
    c_h, a_h = scanner.handled_verbs(CENTER), scanner.handled_verbs(APPROVAL)
    missing = {v: [r for r, h in (("center", c_h), ("approval", a_h)) if v not in h]
               for v in sorted(shared)}
    broken = {v: r for v, r in missing.items() if r}
    assert not broken, f"verbِ مشترک روی هر دو روتر نیست: {broken}"


def t_the_tr_verb_is_present_on_both_routers():
    """رگرسیونِ نقطه‌ایِ همان باگِ تاریخی — تنگ و مستقیم."""
    assert "tr" in scanner.handled_verbs(CENTER), "tr در center نیست"
    assert "tr" in scanner.handled_verbs(APPROVAL), "tr در approval_channel نیست"


def t_the_iv_verb_is_present_where_it_is_emitted():
    """دومین کارتِ مرده تاریخی."""
    emitted_anywhere = scanner.emitted_verbs(CENTER) | scanner.emitted_verbs(APPROVAL)
    if "iv" not in emitted_anywhere:
        return
    handled = scanner.handled_verbs(CENTER) | scanner.handled_verbs(APPROVAL)
    assert "iv" in handled, "iv فرستاده می‌شود ولی handler ندارد"


def t_one_poller_per_token():
    """هر توکن دقیقاً یک poller. دو poller روی یک توکن = ۴۰۹ و از دست رفتنِ update.

    سنجهٔ نحوی: `poll_updates`/`getUpdates` فقط از مسیرهای مجاز صدا زده شود."""
    # ⚠️ نسخهٔ اولِ این بند **رشته‌ای** بود و سه فایل را متهم کرد که هر سه فقط
    # در **داکشان** نوشته بودند «`getUpdates` صدا نمی‌زنیم». یعنی گارد دقیقاً
    # همان جمله‌ای را شمرد که می‌گفت این کار انجام نمی‌شود. درسِ «grep کامنت را
    # می‌شمارد»، این‌بار روی گاردِ خودم. حالا AST: فقط **فراخوانیِ واقعی**.
    allowed = {"tg_api.py", "center.py", "organism.py", "approval_channel.py"}
    callers = []
    for f in scanner.iter_py_files():
        try:
            import ast
            tree = ast.parse(f.read_text("utf-8"))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            if name == "poll_updates":
                callers.append(f.name)
                break
            # `_call("getUpdates", ...)` — رشتهٔ متد به‌عنوان **آرگومان**
            for a in node.args:
                if isinstance(a, ast.Constant) and a.value == "getUpdates":
                    callers.append(f.name)
                    break
    unexpected = sorted(set(callers) - allowed)
    assert not unexpected, f"pollerِ ناشناخته (فراخوانیِ واقعی): {unexpected}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_callback_emitter_parity: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
