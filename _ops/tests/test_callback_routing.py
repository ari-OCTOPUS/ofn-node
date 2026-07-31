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


_AC = (_HERE.parent / "budget" / "approval_channel.py").read_text("utf-8")


def _center_routed() -> set:
    """افعالی که `center._handle_callback` (باتِ مرکزِ گروه) می‌سپارد."""
    out = set(_BASE_VERBS)
    i = _CENTER.index("def _handle_callback")
    # کلِ بدنهٔ تابع، نه پنجرهٔ ثابت — پنجرهٔ ۴۰۰۰کاراکتری با رشدِ تابع (rm/qb ِ
    # ۰۷-۳۱) جدولِ dispatch را بیرون می‌انداخت و ۱۳ فعلِ سالم «بی‌مسیر» می‌شد
    # (همان درسِ پنجرهٔ ۳۰۰۰کاراکتریِ qt در موجِ نجاتِ ۰۷-۳۱).
    _j = _CENTER.find("\n    def ", i + 1)
    body = _CENTER[i:_j if _j != -1 else len(_CENTER)]
    for m in re.finditer(r'verb\s+in\s+\(([^)]*)\)', body):
        out.update(re.findall(r'"([a-z_]+)"', m.group(1)))
    for m in re.finditer(r'verb\s*==\s*"([a-z_]+)"', body):
        out.add(m.group(1))
    return out


def _organism_routed() -> set:
    """افعالی که `approval_channel.dispatch_callback` (باتِ ارگانیسم) می‌سپارد.

    دو شکلِ نگارش وجود دارد و هر دو باید خوانده شوند: `parts[0] == "x"` و
    `parts[0] != "x"` (شکلِ نگهبانی، مثلِ `if ... parts[0] != "app": return رد`).
    نسخه‌ای که فقط شکلِ اول را می‌دید، `app` را «بی‌مسیر» می‌خواند در حالی که
    مسیرِ اصلیِ پولِ همین فایل است."""
    out = set(re.findall(r'parts\[0\]\s*[=!]=\s*"([a-z_]+)"', _AC))
    # فهرستِ صریحِ schemeهای owner-gated هم اعلامِ مسیر است
    m = re.search(r'_callback_requires_owner[\s\S]{0,400}?\(([^)]*)\)', _AC)
    if m:
        out.update(re.findall(r'"([a-z_]+)"', m.group(1)))
    return out


def _routed_verbs() -> set:
    """⚠️ این سیستم **دو بات** دارد، با دو پروسه و دو توکنِ جدا.

    نسخهٔ اولِ این گارد فقط `center.py` را می‌شناخت. آن فرض دو خطا می‌ساخت، در
    هر دو جهت: افعالِ باتِ ارگانیسم را «مرده» می‌خواند (هشدارِ کاذب)، و — بدتر —
    دکمه‌ای را که از باتِ **الف** فرستاده می‌شود ولی فقط باتِ **ب** می‌شناسدش،
    سبز می‌دید. دقیقاً همین اتفاق برای `iv:q` افتاد: کارتش از باتِ ارگانیسم
    می‌رفت، handlerش فقط در مرکز بود، و کلیک به هیچ‌جا نمی‌رسید."""
    return _center_routed() | _organism_routed()


def _emitted_verbs() -> dict:
    """افعالی که کدِ تولید در `callback_data` می‌سازد → فایل‌هایی که می‌سازندشان."""
    # ⚠️ ۲۰۲۶-۰۷-۲۷ — این اسکن فقط `telegram_center/` را می‌دید. ولی سه
    # تولیدکنندهٔ واقعیِ دکمه بیرونِ آن پوشه‌اند (`initiative.py`،
    # `decision_gate.py`، `capability_registry.py`) — یعنی گاردی که کارش
    # «هیچ دکمه‌ای مرده نماند» است، دقیقاً همان دکمه‌هایی را نمی‌دید که همان روز
    # ساخته شدند. سبز می‌ماند در حالی که دکمه مرده است: بدترین حالتِ یک گارد.
    #
    # ریشهٔ اسکن حالا کلِ `_ops` است. اگر دکمه‌ای از هر جای بدن بیاید، دیده می‌شود.
    found: dict = {}
    for py in sorted(_TC.parent.rglob("*.py")):
        if py.name.startswith("test_") or set(py.parts) & {
                "tests", "_code", "__pycache__", "_Archive"}:
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
    # ماژولِ یتیم (صفر صداکنندهٔ تولیدی) دکمه‌اش هم مرده است، ولی علتش «فعلِ
    # بی‌مسیر» نیست — کلِ ماژول هرگز اجرا نمی‌شود. `orphan_scan` جای درستِ آن
    # است؛ این‌جا شمردنش نویز می‌سازد و گارد را بی‌اثر می‌کند.
    _DEAD_MODULES = {"approval_channel_merge.py"}
    orphan = {v: sorted(f) for v, f in emitted.items()
              if v not in routed and set(f) - _DEAD_MODULES}
    assert not orphan, (
        "دکمه‌هایی با فعلِ بی‌مسیر — کلیک می‌شوند و به هیچ handlerی نمی‌رسند: "
        f"{orphan}")


def t_the_two_verbs_that_were_dead_are_now_routed():
    """گاردِ رگرسیونِ نمونه‌ایِ همان باگ."""
    routed = _routed_verbs()
    for v in ("ng", "mr"):
        assert v in routed, f"فعلِ «{v}» دوباره از جدولِ dispatch افتاد"


def t_a_card_sent_by_the_organism_bot_is_routed_by_the_organism_bot():
    """تلهٔ دو-باتی: کارتی که باتِ الف می‌فرستد باید همان بات جوابش را بدهد.

    `organism.py` کارتِ ابتکار را از `approval_channel` (باتِ ارگانیسم)
    می‌فرستد. اگر فعلش فقط در `center.py` شناخته شود، دکمه ساخته می‌شود،
    فرستاده می‌شود، کلیک می‌شود — و به هیچ‌جا نمی‌رسد."""
    org = (_HERE.parent / "organism.py").read_text("utf-8")
    assert "_iv.card(" in org and "_chan.send_text" in org,         "مسیرِ ارسالِ کارتِ ابتکار عوض شده — این گارد را به‌روز کن"
    assert "iv" in _organism_routed(),         "کارتِ ابتکار از باتِ ارگانیسم می‌رود ولی آن بات فعلِ iv را نمی‌شناسد"


def t_the_center_callback_handler_actually_knows_them():
    """مسیر داشتن کافی نیست — handler هم باید شاخه‌اش را داشته باشد."""
    # ⚠️ نسخهٔ اول ۶۰۰۰ کاراکترِ بعد از نامِ تابع را برش می‌زد. با اضافه‌شدنِ یک
    # شاخهٔ تازه، شاخه‌های پایین‌تر از پنجره بیرون افتادند و تست قرمز شد در حالی
    # که کد **درست** بود. پنجرهٔ ثابت روی کدی که رشد می‌کند، گاردِ کاذب می‌سازد.
    # حالا مرز از خودِ ساختار می‌آید: تا تعریفِ متدِ بعدی.
    i = _CENTER.index("def _handle_center_callback")
    rest = _CENTER[i + 1:]
    j = rest.find("\n    def ")
    body = rest if j < 0 else rest[:j]
    for v in ("ng", "mr", "qt", "iv", "dg", "x"):
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
