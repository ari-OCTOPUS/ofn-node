#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_callback_emitter_parity — هر دکمه‌ای که فرستاده می‌شود، handler دارد.

شکافِ سومِ بستهٔ `telegram_contract` (VQ-TG-GAP-EMITTER-001).

تاریخچهٔ این پروژه **دو کارتِ مرده** دارد: `iv:q` و `tr:*` هر دو ساخته و
فرستاده شدند در حالی که handler ِ verbشان روی باتِ دیگری بود — مالک دکمه را
می‌زد و هیچ اتفاقی نمی‌افتاد. هر بار هم دستی کشف شد، نه با گارد.

قاعدهٔ این فایل: **هر verb ای که در `callback_data` تولید می‌شود باید در
روترِ همان مسیر شناخته شده باشد.** و چون کارت‌ها از دو مسیر می‌روند
(`organism` از طریق `approval_channel`، و `telegram_center`)، verbهای مشترک
باید در **هر دو** روتر باشند — همان درسی که `tr:` بعد از افتادن یاد داد.

روشِ سنجش **نحوی** است نه رشته‌ای: `ast` روی سورس، تا جمله‌ای در یک کامنت که
اسمِ یک verb را برده به‌عنوان handler شمرده نشود (درسِ «grep کامنت را می‌شمارد»).
"""
import ast
import re
import sys
from pathlib import Path

import harness

ENV = harness.setup("tg-emitter-parity")

_OPS = Path(__file__).resolve().parent.parent
CENTER = _OPS / "telegram_center" / "center.py"
APPROVAL = _OPS / "budget" / "approval_channel.py"
TOOL_REQUEST = _OPS / "tool_request.py"
TEST_CYCLE = _OPS / "test_cycle.py"

# verbهایی که عمداً بی‌handler اند و دلیلش ثبت شده. هر افزودنی به این مجموعه
# باید دلیل داشته باشد — وگرنه همان کارتِ مرده است با نامِ دیگر.
KNOWN_HANDLERLESS = {
    "noop",       # دکمهٔ تزئینی/جداکننده
}

_VERB = re.compile(r"^([A-Za-z][A-Za-z0-9_]{0,15}):")


def _emitted_verbs(path: Path) -> set:
    """verbهایی که در `callback_data` **ساخته** می‌شوند — از AST، نه grep.

    دو شکل پوشش داده می‌شود: رشتهٔ ثابت (`"tr:list"`) و f-string
    (`f"tr:y:{rid}"`) که در AST یک `JoinedStr` با اولین جزءِ ثابت است."""
    out = set()
    try:
        tree = ast.parse(path.read_text("utf-8"))
    except (OSError, SyntaxError):
        return out
    for node in ast.walk(tree):
        # {"callback_data": <expr>}
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if not (isinstance(k, ast.Constant) and k.value == "callback_data"):
                    continue
                lit = None
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    lit = v.value
                elif isinstance(v, ast.JoinedStr) and v.values:
                    first = v.values[0]
                    if isinstance(first, ast.Constant) and isinstance(first.value, str):
                        lit = first.value
                if lit:
                    m = _VERB.match(lit)
                    if m:
                        out.add(m.group(1))
    return out


def _handled_verbs(path: Path) -> set:
    """verbهایی که روتر **می‌شناسد** — مقایسه‌های `verb == "x"` / `in {...}` /
    `parts[0] == "x"`، همه از AST."""
    out = set()
    try:
        tree = ast.parse(path.read_text("utf-8"))
    except (OSError, SyntaxError):
        return out
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            left = node.left
            is_verbish = (
                (isinstance(left, ast.Name) and left.id in ("verb", "v", "kind"))
                or (isinstance(left, ast.Subscript)
                    and isinstance(left.value, ast.Name)
                    and left.value.id in ("parts", "p"))
            )
            if not is_verbish:
                continue
            for comp in node.comparators:
                if isinstance(comp, ast.Constant) and isinstance(comp.value, str):
                    out.add(comp.value)
                elif isinstance(comp, (ast.Set, ast.Tuple, ast.List)):
                    for e in comp.elts:
                        if isinstance(e, ast.Constant) and isinstance(e.value, str):
                            out.add(e.value)
    return out
    # ⚠️ عمداً مجموعه‌های سطحِ ماژول (مثلِ `_MUTATING = frozenset({"app","tr"})`)
    # **شمرده نمی‌شوند**. نسخهٔ اول می‌شمرد و گارد بی‌دندان شد: برداشتنِ کاملِ
    # شاخهٔ `verb == "tr"` از center هیچ تستی را قرمز نکرد، چون نامِ `tr` از
    # همان مجموعهٔ عضویت برداشته می‌شد. عضویت در یک لیستِ «این verb جهش‌زاست»
    # یعنی **دسته‌بندی**، نه **رسیدگی**. فقط شاخهٔ dispatch حساب است.


# ── سنجه‌ها ────────────────────────────────────────────────────────────────
def t_the_scanner_actually_finds_something():
    """اگر این بند بشکند بقیه بی‌معنی‌اند — اسکنرِ خالی همیشه سبز است."""
    emitted = _emitted_verbs(CENTER) | _emitted_verbs(APPROVAL)
    assert len(emitted) >= 3, f"اسکنرِ emit چیزی پیدا نکرد: {emitted}"
    handled = _handled_verbs(CENTER) | _handled_verbs(APPROVAL)
    assert len(handled) >= 3, f"اسکنرِ handler چیزی پیدا نکرد: {handled}"


def t_every_verb_the_center_emits_is_handled_somewhere():
    emitted = _emitted_verbs(CENTER) - KNOWN_HANDLERLESS
    handled = _handled_verbs(CENTER) | _handled_verbs(APPROVAL)
    orphan = sorted(emitted - handled)
    assert not orphan, f"کارتِ مرده — verb بی‌handler از center: {orphan}"


def t_every_verb_the_approval_channel_emits_is_handled_somewhere():
    emitted = _emitted_verbs(APPROVAL) - KNOWN_HANDLERLESS
    handled = _handled_verbs(CENTER) | _handled_verbs(APPROVAL)
    orphan = sorted(emitted - handled)
    assert not orphan, f"کارتِ مرده — verb بی‌handler از approval_channel: {orphan}"


def t_verbs_emitted_by_shared_modules_are_handled_on_both_routers():
    """`tool_request` و `test_cycle` کارتشان از **هر دو** مسیر می‌تواند برود.

    درسِ `tr:`: کارت از کانالِ ارگانیسم رفت ولی handler فقط در مرکز بود. پس
    verbِ ماژولِ مشترک باید در هر دو روتر باشد، نه یکی."""
    shared = set()
    for m in (TOOL_REQUEST, TEST_CYCLE):
        if m.exists():
            shared |= _emitted_verbs(m)
    shared -= KNOWN_HANDLERLESS
    if not shared:
        return                                   # ماژولِ مشترکی کارت نمی‌سازد
    c_h, a_h = _handled_verbs(CENTER), _handled_verbs(APPROVAL)
    missing = {v: [r for r, h in (("center", c_h), ("approval", a_h)) if v not in h]
               for v in sorted(shared)}
    broken = {v: r for v, r in missing.items() if r}
    assert not broken, f"verbِ مشترک روی هر دو روتر نیست: {broken}"


def t_the_tr_verb_is_present_on_both_routers():
    """رگرسیونِ نقطه‌ایِ همان باگِ تاریخی — تنگ و مستقیم."""
    assert "tr" in _handled_verbs(CENTER), "tr در center نیست"
    assert "tr" in _handled_verbs(APPROVAL), "tr در approval_channel نیست"


def t_the_iv_verb_is_present_where_it_is_emitted():
    """دومین کارتِ مرده تاریخی."""
    emitted_anywhere = _emitted_verbs(CENTER) | _emitted_verbs(APPROVAL)
    if "iv" not in emitted_anywhere:
        return
    handled = _handled_verbs(CENTER) | _handled_verbs(APPROVAL)
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
    for f in sorted(_OPS.rglob("*.py")):
        if any(p in f.parts for p in ("tests", "__pycache__", "_Archive",
                                      "_agent_reports")):
            continue
        try:
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
