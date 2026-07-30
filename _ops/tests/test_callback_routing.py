"""test_callback_routing.py — هیچ دکمه‌ای نباید به جایی نرسد.

باگِ ۲۰۲۶-۰۷-۲۷ که این فایل را ساخت: پنج دکمهٔ تازه (سه‌تای مذاکره، دوتای اتاقِ
آینه) ساخته و مسلح شدند، ولی افعالشان (`ng`, `mr`) در جدولِ dispatch ِ
`_handle_callback` نبودند. پس کلیک می‌شدند، به هیچ handlerی نمی‌رسیدند، و در
شاخهٔ ok/no/later بی‌صدا «نادیده» می‌شدند.

تستِ آن روز فقط **شکلِ** صفحه‌کلید را می‌سنجید (`callback_data` چه ساختاری دارد)
نه **مسیرش** را. یعنی سبز بود و کار نمی‌کرد — همان «سبز به‌خاطرِ نبودِ خطا».

این فایل کلاسِ باگ را می‌بندد نه یک نمونه‌اش: هر فعلی که در کدِ تولید ساخته
می‌شود، باید در جدولِ dispatch یا در مسیرِ verdictِ پایه شناخته شده باشد.
"""
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import harness   # noqa: E402
ENV = harness.setup("callback-routing")

_TC = _HERE.parent / "telegram_center"
_CENTER = (_TC / "center.py").read_text("utf-8")

# افعالی که مسیرِ پایهٔ verdict خودش می‌گیرد (نه _handle_center_callback)
_BASE_VERBS = {"ok", "no", "later"}


def _routed_verbs() -> set:
    """افعالی که `_handle_callback` واقعاً به یک handler می‌سپارد."""
    out = set(_BASE_VERBS)
    i = _CENTER.index("def _handle_callback")
    body = _CENTER[i:i + 4000]
    for m in re.finditer(r'verb\s+in\s+\(([^)]*)\)', body):
        out.update(re.findall(r'"([a-z_]+)"', m.group(1)))
    for m in re.finditer(r'verb\s*==\s*"([a-z_]+)"', body):
        out.add(m.group(1))
    return out


def _emitted_verbs() -> dict:
    """افعالی که کدِ تولید در `callback_data` می‌سازد → فایل‌هایی که می‌سازندشان."""
    found: dict = {}
    for py in sorted(_TC.glob("*.py")):
        if py.name.startswith("test_"):
            continue
        src = py.read_text("utf-8", errors="replace")
        for m in re.finditer(r'"callback_data"\s*:\s*f?"([a-z_]+):', src):
            found.setdefault(m.group(1), set()).add(py.name)
    return found


def t_every_emitted_callback_verb_is_routed():
    """گاردِ اصلی. اگر روزی دکمه‌ای با فعلِ تازه ساخته شود و جدولِ dispatch
    به‌روز نشود، همین‌جا قرمز می‌شود — نه شش ماه بعد وقتی مالک می‌گوید «کلیک
    می‌کنم هیچی نمی‌شود»."""
    routed = _routed_verbs()
    emitted = _emitted_verbs()
    assert emitted, "هیچ callback_data ای پیدا نشد — اسکنر شکسته است"
    orphan = {v: sorted(f) for v, f in emitted.items() if v not in routed}
    assert not orphan, (
        "دکمه‌هایی با فعلِ بی‌مسیر — کلیک می‌شوند و به هیچ handlerی نمی‌رسند: "
        f"{orphan}")


def t_the_two_verbs_that_were_dead_are_now_routed():
    """گاردِ رگرسیونِ نمونه‌ایِ همان باگ."""
    routed = _routed_verbs()
    for v in ("ng", "mr"):
        assert v in routed, f"فعلِ «{v}» دوباره از جدولِ dispatch افتاد"


def t_the_center_callback_handler_actually_knows_them():
    """مسیر داشتن کافی نیست — handler هم باید شاخه‌اش را داشته باشد."""
    i = _CENTER.index("def _handle_center_callback")
    body = _CENTER[i:i + 6000]
    for v in ("ng", "mr"):
        assert f'verb == "{v}"' in body, f"شاخهٔ «{v}» در handler نیست"


def t_negotiate_and_mirror_emit_the_verbs_they_claim():
    """قرارداد دوطرفه: ماژول همان فعلی را بسازد که handler انتظار دارد."""
    import negotiate as ng
    import mirror_room as mr
    _, kb = ng.card({"id": "of1", "عنوان": "x", "می‌خواهم": "y", "شرط‌ها": []})
    verbs = {b["callback_data"].split(":")[0] for row in kb for b in row}
    assert verbs == {"ng"}, verbs
    _, kb2 = mr.card("x", "fugu")
    verbs2 = {b["callback_data"].split(":")[0] for row in kb2 for b in row}
    assert verbs2 == {"mr"}, verbs2


def t_every_emitted_callback_fits_the_64_byte_cap():
    """درسِ ۰۷-۲۶: رد شدن از سقف یعنی تلگرام کلِ پیام را ۴۰۰ می‌کند و کارت بی‌هیچ
    ردی گم می‌شود. اینجا فقط شکلِ ثابت سنجیده می‌شود؛ بخشِ متغیر جای دیگر."""
    import negotiate as ng
    import mirror_room as mr
    _, kb = ng.card({"id": "o" * 12, "عنوان": "x", "می‌خواهم": "y", "شرط‌ها": []})
    for row in kb:
        for b in row:
            assert len(b["callback_data"].encode()) <= 64, b
    _, kb2 = mr.card("x")
    for row in kb2:
        for b in row:
            assert len(b["callback_data"].encode()) <= 64, b


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_callback_routing: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
