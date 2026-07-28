"""test_command_discoverability — دستوری که کار می‌کند ولی دیده نمی‌شود، نیست.

تا ۲۰۲۶-۰۷-۲۷ فهرستِ ثبت‌شدهٔ دستورها ۹ تا بود در حالی که handlerها ۲۰ تا
بودند. یعنی نصفِ توانایی‌های تلگرام **کار می‌کردند ولی در منوی بات دیده
نمی‌شدند**: مالک باید از قبل می‌دانست وجود دارند تا بتواند تایپشان کند.

این دقیقاً همان کژیِ کارت‌های نامرئی است، یک لایه بالاتر — و مثل آن، **ساختاری**
است: هر دستورِ تازه‌ای که کسی اضافه کند، پیش‌فرضاً نامرئی است مگر یادش بماند دو
جا بنویسدش. یادِ آدم‌ها گارد نیست.
"""
import ast
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("command-discoverability")

_OPS = harness.REAL_VAULT / "_ops"
_CENTER_PATH = _OPS / "telegram_center" / "center.py"
_CENTER = _CENTER_PATH.read_text("utf-8")

# دستورهایی که عمداً در منو نیستند، هرکدام با دلیلِ مکتوب. اگر این فهرست بی‌دلیل
# بزرگ شود، خودِ گارد بی‌معنی می‌شود — پس سقف دارد.
INTENTIONALLY_HIDDEN = {
    "start": "معادلِ /menu — تلگرام خودش دکمهٔ Start را نشان می‌دهد",
    "panel": "پشتِ فلگِ OCTOPUS_WIRE_MENU_V2؛ وقتی خاموش است اصلاً وجود ندارد",
    "توان": "نامِ فارسیِ /x — همان دستور، دو نام",
    "رفتار": "نامِ فارسیِ مسیرِ live",
    "کد": "نامِ فارسیِ /code",
    "flags": "دستورِ introspection/debug (_introspect) — پشتِ /menu، نه خودِ منو",
    "insight": "دستورِ introspection/debug (_introspect) — پشتِ /menu، نه خودِ منو",
    "scan": "دستورِ introspection/debug (_introspect) — پشتِ /menu، نه خودِ منو",
    "trace": "دستورِ introspection/debug (_introspect) — پشتِ /menu، نه خودِ منو",
}


def _handler_commands() -> set:
    """کلیدهای دیکشنریِ handlers در `_handle_message` — منبعِ حقیقتِ «چه کار می‌کند»."""
    i = _CENTER.index("handlers = {")
    j = _CENTER.index("fn = handlers.get(cmd)", i)
    return {m.group(1) for m in re.finditer(r'"/([^"]+)"\s*:', _CENTER[i:j])}


def _command_rows() -> list:
    """ردیف‌های COMMANDS به‌شکلِ [(نام، توضیح)].

    ⚠️ `COMMANDS: list[...] = [...]` یک **AnnAssign** است نه Assign. نسخهٔ اولِ
    این فایل دو خوانندهٔ جدا داشت و یکی‌شان فقط Assign را می‌دید → «فهرست خالی».
    یک خوانندهٔ واحد، تا این تله دوباره تکرار نشود."""
    tree = ast.parse(_CENTER)
    for node in tree.body:
        target = None
        if isinstance(node, ast.AnnAssign):
            target = node.target
        elif isinstance(node, ast.Assign) and node.targets:
            target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id != "COMMANDS":
            continue
        rows = []
        for el in (node.value.elts if isinstance(node.value, (ast.List, ast.Tuple)) else []):
            if isinstance(el, (ast.Tuple, ast.List)) and len(el.elts) == 2:
                a, b = el.elts
                rows.append((a.value if isinstance(a, ast.Constant) else "",
                             b.value if isinstance(b, ast.Constant) else ""))
        return rows
    raise AssertionError("COMMANDS پیدا نشد")


def _registered_commands() -> set:
    """فهرستِ COMMANDS که به تلگرام معرفی می‌شود — منبعِ حقیقتِ «چه دیده می‌شود»."""
    return {str(c) for c, _ in _command_rows()}


# ─── ناوردیِ اصلی ──────────────────────────────────────────────────────────
def t_every_working_command_is_discoverable():
    """اگر این بشکند، توانایی‌ای ساخته شده که مالک راهی برای پیداکردنش ندارد."""
    handled = _handler_commands()
    shown = _registered_commands()
    missing = handled - shown - set(INTENTIONALLY_HIDDEN)
    assert not missing, (
        f"این دستورها کار می‌کنند ولی در منوی تلگرام نیستند: {sorted(missing)} — "
        "یا به COMMANDS اضافه‌شان کن یا با دلیل در INTENTIONALLY_HIDDEN")


def t_no_command_is_advertised_without_a_handler():
    """جهتِ عکس: دستوری که در منو هست ولی کار نمی‌کند، بدتر از نبودن است."""
    handled = _handler_commands()
    shown = _registered_commands()
    ghosts = shown - handled
    assert not ghosts, f"در منو هست ولی handler ندارد: {sorted(ghosts)}"


def t_the_hidden_list_stays_small_and_justified():
    """فهرستِ استثنا اگر بی‌دلیل رشد کند، خودِ گارد را بی‌معنی می‌کند."""
    assert len(INTENTIONALLY_HIDDEN) <= 9, len(INTENTIONALLY_HIDDEN)
    for cmd, why in INTENTIONALLY_HIDDEN.items():
        assert len(why) >= 15, f"«{cmd}» بدونِ دلیلِ واقعی پنهان شده"


# ─── سلامتِ خودِ فهرست ─────────────────────────────────────────────────────
def t_every_entry_has_a_useful_description():
    """توضیحِ خالی یعنی مالک اسم را می‌بیند ولی نمی‌داند چه می‌کند."""
    rows = _command_rows()
    assert rows, "فهرست خالی خوانده شد"
    for cmd, desc in rows:
        assert cmd and cmd == cmd.lower(), f"نامِ دستور باید کوچک باشد: {cmd}"
        assert len(str(desc)) >= 8, f"«{cmd}» توضیحِ معنادار ندارد"
        # سقفِ تلگرام برای توضیحِ دستور ۲۵۶ کاراکتر است
        assert len(str(desc)) <= 256, cmd


def t_there_are_no_duplicates():
    names = [c for c, _ in _command_rows()]
    assert names, "فهرست خالی خوانده شد"
    assert len(names) == len(set(names)), [n for n in names if names.count(n) > 1]


def t_the_registration_trigger_reacts_to_a_changed_list():
    """بوت با `commands_set != len(COMMANDS)` دوباره ثبت می‌کند — پس اضافه‌کردنِ
    دستور باید ثبتِ مجدد را ماشه بزند. بدونِ این، فهرستِ نو تا ری‌استارتِ بعدیِ
    اتفاقی روی بات نمی‌نشیند."""
    assert "cfg.get(\"commands_set\") != len(COMMANDS)" in _CENTER


def t_the_new_commands_of_today_are_present():
    """گاردِ رگرسیونِ صریح برای همان هفت دستوری که ۲۰۲۶-۰۷-۲۷ نامرئی بودند."""
    shown = _registered_commands()
    for c in ("x", "stuck", "verdicts", "lead", "deal", "doctrine", "eq"):
        assert c in shown, c


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_command_discoverability: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
