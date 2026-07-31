"""test_funnel_cmd — مالک واقعیتِ بازار را می‌گوید و گفته‌اش می‌ماند (D3b).

`outcomes/funnel_store.py` سربرگِ خودش می‌گفت «دستوراتِ مالک در D3b؛ این store
صفر caller دارد تا wiring بعداً» — و آن wiring هرگز ساخته نشد. یعنی ارگانیسمی که
مأموریتش پول است، هیچ‌وقت نمی‌فهمید کدام لید **برنده** شد: لید می‌ساخت، امتیاز
می‌داد، پیشنهاد می‌نوشت، و بعد سکوت. بدونِ سیگنالِ برگشتی، هیچ چیزی قابلِ
یادگیری نبود.

سه مرزی که این تست محافظت می‌کند — و همه‌شان از یک جنس‌اند: **گزارش ≠ عمل**:
  ۱) `/paid` هیچ پولی جابه‌جا نمی‌کند و به هیچ درآمدِ تأییدشده‌ای وصل نیست.
  ۲) هیچ‌کدام از افعال چیزی به مشتری نمی‌فرستند.
  ۳) فعلِ ناشناخته دادهٔ مبهم نمی‌سازد — چون دادهٔ مبهم بعداً از دادهٔ واقعی
     جدا نمی‌شود.
"""
import ast
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("funnel-cmd")

# ⚠️ ۲۰۲۶-۰۷-۳۱: این خط `harness.REAL_VAULT / "_ops"` بود — یعنی سوییت کدِ
# **درختِ زنده** را می‌سنجید، نه کدی که در این checkout تغییر کرده. نتیجه:
# هر تغییرِ worktree نامرئی بود و جهشِ عمدی هم قرمز نمی‌شد (گاردِ بی‌دندانِ
# ساختاری). دکترینِ harness: «کدِ تحتِ آزمون = همین درخت، هرگز REAL_VAULT».
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "telegram_center"), str(_OPS / "outcomes"),
           str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import funnel_cmd as fc   # noqa: E402


def _on(v=True):
    if v:
        os.environ[fc.FLAG] = "1"
    else:
        os.environ.pop(fc.FLAG, None)


# ─── ۱: حلقه واقعاً بسته است ──────────────────────────────────────────────
def t_a_win_is_actually_recorded():
    """قلبِ D3b: «بردیم» باید در store بنشیند، نه فقط در یک پیام."""
    _on()
    try:
        r = fc.record("won", "lead-t1")
        assert r["ok"] and r["event"] == "quote.won", r
        import funnel_store
        st = funnel_store.FunnelStore()
        try:
            evs = st.events_for_lead("lead-t1")
        finally:
            st.close()
        # `events_for_lead` تاپل برمی‌گرداند نه dict — پس دنبالِ رشته در خودِ
        # ردیف می‌گردیم، نه کلیدی که وجود ندارد.
        assert any("quote.won" in str(e) for e in evs), evs
    finally:
        _on(False)


def t_every_verb_maps_to_a_contract_event():
    """فعلی که به رویدادِ قراردادی نگاشت نشود، در store رد می‌شود."""
    import funnel_store
    for verb, (et, label) in fc.VERBS.items():
        assert et in funnel_store.EVENT_TYPES, (verb, et)
        assert label.strip(), verb


def t_recording_twice_is_idempotent():
    """append-only یعنی تکرار، نه تکثیر — دوبار تپ نباید دو برد بسازد."""
    _on()
    try:
        a = fc.record("won", "lead-dup")
        b = fc.record("won", "lead-dup")
        assert a["ok"] and b["ok"]
        assert a.get("fresh") is True and b.get("fresh") is False, (a, b)
    finally:
        _on(False)


# ─── ۲: گزارش ≠ عمل ──────────────────────────────────────────────────────
def t_paid_moves_no_money_and_sends_nothing():
    """مهم‌ترین مرز: `/paid` یک **گزارش** است، نه تراکنش."""
    src = Path(fc.__file__).read_text("utf-8")
    tree = ast.parse(src)
    banned = {"subprocess", "urllib", "requests", "socket", "smtplib"}
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (banned & imported), sorted(banned & imported)
    called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for d in ("send", "send_text", "settle", "release_effect", "pay",
              "record_revenue", "apply", "transfer"):
        assert d not in called, f"ماژولِ گزارش عمل می‌کند: {d}"


def t_the_card_says_plainly_that_nothing_moved():
    """اگر جواب مبهم باشد، مالک فکر می‌کند پولی ثبت شده."""
    _on()
    try:
        out = fc.handle("/paid lead-x")
        assert "نه پولی جابه‌جا شد" in out and "نه پیامی رفت" in out, out
    finally:
        _on(False)


def t_the_module_never_touches_confirmed_revenue():
    """⚠️ روی **کد** می‌سنجد نه متن. نسخهٔ اول کلِ فایل را گرپ می‌کرد و کلمهٔ
    «ledger» را از docstringِ خودِ ماژول می‌گرفت — جایی که دقیقاً نوشته «به هیچ
    ledgerی وصل نیست». یعنی تست، جمله‌ای که بی‌گناهی را اعلام می‌کرد به‌عنوان
    مدرکِ جرم خواند."""
    tree = ast.parse(Path(fc.__file__).read_text("utf-8"))
    banned = {"attribution", "confirmed_revenue", "_revenue_confirmed",
              "outcome_store", "ledger"}
    used = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name):
            used.add(n.id)
        elif isinstance(n, ast.Attribute):
            used.add(n.attr)
        elif isinstance(n, ast.Import):
            used.update(a.name.split(".")[-1] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            used.add(n.module.split(".")[-1])
    hit = banned & used
    assert not hit, f"قیف به {sorted(hit)} دست زده"


# ─── ۳: ابهام ممنوع ──────────────────────────────────────────────────────
def t_an_unknown_verb_creates_no_data():
    _on()
    try:
        for bad in ("maybe", "", None, "won2", "برنده", "../x"):
            r = fc.record(bad, "lead-x")
            assert r["ok"] is False, bad
    finally:
        _on(False)


def t_a_missing_lead_id_is_refused_with_a_hint():
    _on()
    try:
        assert fc.record("won", "")["ok"] is False
        out = fc.handle("/won")
        assert "شناسهٔ لید" in out and "نکنی:" in out, out
    finally:
        _on(False)


# ─── ۴: فلگ ──────────────────────────────────────────────────────────────
def t_flag_off_records_nothing_but_says_how_to_turn_it_on():
    """کارتِ خاموشی که راهِ روشن‌کردن را نگوید، بن‌بست است."""
    _on(False)
    r = fc.record("won", "lead-off")
    assert r["ok"] is False and r["msg"] == "flag-off"
    out = fc.handle("/won lead-off")
    assert f"OWNER_AUTH: ARM FLAG {fc.FLAG}" in out, out


def t_the_dark_card_admits_what_is_lost():
    _on(False)
    body = fc.card()
    assert "هرگز" in body and "برنده" in body, body


# ─── ۵: کشف‌پذیری ────────────────────────────────────────────────────────
def t_every_verb_is_reachable_and_never_advertised_in_the_dm_menu():
    """هر فعلِ قیف باید **قابلِ اجرا** باشد، و طبقِ رأیِ ۴ منشور
    (TG-UI-CHARTER-2026-07-31) هیچ‌کدام نباید در منوی DM تبلیغ شود.

    ⚠️ تغییرِ قرارداد ۲۰۲۶-۰۷-۳۱: نسخهٔ قبلی «ثبت در COMMANDS» را الزام
    می‌کرد. مالک صریح رأی داد بلوکِ ۹تاییِ قیف از منوی DM برود («بیزنس هرگز
    در DM») در حالی که فرمانِ تایپی زنده بماند — دفترِ حذف:
    `_ops/telegram_contract/REMOVED-BUTTONS-2026-07-31.md`. پس گارد جهتش
    برعکس شد: دندانش روی **دسترس‌پذیری** است، و علاوه بر آن نگهبانِ رأیِ
    مالک است که کسی دوباره منو را شلوغ نکند."""
    center = (_OPS / "telegram_center" / "center.py").read_text("utf-8")
    import re as _re
    m = _re.search(r"^COMMANDS[^=\n]*=\s*[\[(](.*?)^[\])]", center, _re.S | _re.M)
    assert m, "بلوکِ COMMANDS در center.py پیدا نشد"
    menu = m.group(1)
    for verb in fc.VERBS:
        assert f'"/{verb}"' in center, f"/{verb} به handler وصل نیست"
        assert f'("{verb}"' not in menu, \
            f"/{verb} دوباره به منوی DM برگشت — نقضِ رأیِ ۴ منشور"


def t_the_card_lists_the_verbs_for_the_owner():
    _on()
    try:
        body = fc.card()
        for verb in ("won", "lost", "paid"):
            assert f"/{verb}" in body, verb
    finally:
        _on(False)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_funnel_cmd: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
