#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_funnel_sent — کارتِ قیف باید نیمهٔ **رفت** را هم بگوید، صادقانه.

شکافی که این تست قفل می‌کند (۲۰۲۶-۰۸-۰۱، سومین شکافِ پیش از arming):

  `/funnel` فقط برده/باخته/پول‌رسیده را نشان می‌داد — یعنی فقط چیزهایی که
  **مالک خودش** تایپ کرده بود. هیچ‌جای تلگرام نمی‌شد فهمید ارگانیسم امروز
  چند پیام بیرون فرستاده. بعد از arming این یعنی سقفِ روزانهٔ ۱۰ ارسال
  می‌سوخت و مالک حتی یک عدد از آن نمی‌دید.

قواعدی که این‌جا گارد می‌شوند:
  · «امروز صفر رفت» و «نمی‌دانم چند رفت» هرگز یک متن نمی‌شوند. شمارندهٔ
    غایب/خراب = «نامعلوم»، نه ۰. صفرِ مطمئن فقط وقتی مجاز است که شمارنده
    **خوانده شده باشد** و مالِ روزِ دیگری باشد (rollover واقعی).
  · `outbound_worker.sends_today()` عمداً fail-closed است (فایلِ خراب ⇒ خودِ
    سقف). آن عدد برای **جلوگیری از ارسال** درست است و برای **گزارش** دروغ:
    «۱۰ تا رفت» در حالی که هیچ‌کس نمی‌داند. کارت نباید از آن بخورد.
  · روزِ «امروز» از خودِ تابعِ نویسنده گرفته می‌شود — نه ساعتِ مستقلِ خواننده.
  · کارت هیچ شناسه/آدرس/نامِ مشتری نشان نمی‌دهد؛ فقط شمار.
  · خواندنِ شمارنده هرگز آن را عوض نمی‌کند (کارت گزارش است، نه عمل).
  · بخش‌های قدیمیِ کارت سرِ جایشان می‌مانند — و یکی از آن‌ها همین‌جا از
    خوابِ ۴روزه بیدار شد: کارت `by_event` را می‌خواند در حالی که `metrics()`
    کلیدش `events_by_type` است، پس «برده» **همیشه** ۰ بود.
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("funnel-sent")     # قبل از هر importی که مسیرِ state را می‌بندد

# کدِ تحتِ آزمون = همین درخت (worktree)، هرگز REAL_VAULT.
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "telegram_center"), str(_OPS / "outcomes"),
           str(_OPS / "budget"), str(_OPS / "legs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import funnel_cmd as fc        # noqa: E402
import funnel_store            # noqa: E402
import outbound_worker as ow   # noqa: E402

# ساعتِ ثابت: تستِ ساعتِ‌دیواری‌خوان فقط بعضی روزها سبز است.
NOW = 1_800_000_000.0
TODAY = ow._day_str(NOW)
CAP = ow.LEAD_DAILY_SEND_CAP


def _on(v=True):
    import os
    if v:
        os.environ[fc.FLAG] = "1"
    else:
        os.environ.pop(fc.FLAG, None)


def _counter(payload=None, *, raw=None):
    """شمارنده را در همان مسیری می‌نویسد که نویسندهٔ واقعی می‌نویسد."""
    p = ow._counter_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    if raw is not None:
        p.write_text(raw, "utf-8")
    else:
        p.write_text(json.dumps(payload, ensure_ascii=False), "utf-8")
    return p


def _no_counter():
    p = ow._counter_path()
    if p.exists():
        p.unlink()
    return p


def _authz(entries=None, *, raw=None):
    """دفترِ مجوزِ ارسال را در همان مسیرِ گیت بنویس."""
    p = fc._authz_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    if raw is not None:
        p.write_text(raw, "utf-8")
    else:
        p.write_text(json.dumps(entries, ensure_ascii=False), "utf-8")
    return p


def _no_authz():
    p = fc._authz_path()
    if p.exists():
        p.unlink()
    return p


def _record(event_type, lead_id, **kw):
    st = funnel_store.FunnelStore()
    try:
        st.record({"event_type": event_type, "lead_id": lead_id,
                   "source_component": "test", **kw})
    finally:
        st.close()


def _fresh_ledger(name):
    """دفترِ قیفِ نو برای این تست — تستی که رویدادِ تستِ قبلی را بشمارد،
    ترتیبِ اجرا را می‌سنجد نه کد را. مسیرِ شمارنده/مجوز از `opslib.STATE_DIR` ِ
    سرِ import می‌آید و دست‌نخورده می‌مانَد."""
    import os
    d = Path(ENV["root"]) / f"ledger-{name}"
    (d / "outcomes").mkdir(parents=True, exist_ok=True)
    os.environ["OCTOPUS_STATE_DIR"] = str(d)


def _break_db():
    """funnel.db را واقعاً ناخوانا کن (بایتِ زباله) — نه mock ِ خوش‌بین.

    روی یک state ِ یک‌بارمصرف، نه دفترِ خودِ تست: `FunnelStore.__init__` وقتی
    روی فایلِ خراب می‌ترکد، connection ِ نیمه‌ساخته‌اش هرگز close نمی‌شود و
    ویندوز فایل را قفل نگه می‌دارد (تمیزکاری بعدی PermissionError می‌گیرد).
    مسیرِ شمارنده از `opslib.STATE_DIR` ِ سرِ import می‌آید، پس دست‌نخورده
    می‌مانَد — دقیقاً شرطی که این تست می‌خواهد: دفتر مرده، شمارنده زنده."""
    import os
    d = Path(ENV["root"]) / "broken-state"
    (d / "outcomes").mkdir(parents=True, exist_ok=True)
    (d / "outcomes" / "funnel.db").write_bytes(b"this is not a database at all")
    os.environ["OCTOPUS_STATE_DIR"] = str(d)


def _heal_db():
    import os
    os.environ["OCTOPUS_STATE_DIR"] = ENV["OCTOPUS_STATE_DIR"]


# ─── ۱: عددِ ارسالِ امروز از منبعِ واقعی ────────────────────────────────────
def t_a_sent_today_renders_from_the_real_counter():
    """قلبِ شکاف: عددِ ارسال باید روی کارت بیاید — از فایلِ خودِ worker."""
    _on()
    try:
        _counter({"date": TODAY, "sent": 3})
        body = fc.card(now=NOW)
        assert f"ارسالِ امروز: 3 از {CAP}" in body, body
        assert fc.outbound_snapshot(now=NOW)["today"] == 3
    finally:
        _on(False)


def t_a2_a_full_cap_says_so_out_loud():
    """سقفِ پرشده یعنی «تا فردا هیچ» — عددِ تنها این را نمی‌گوید."""
    _on()
    try:
        _counter({"date": TODAY, "sent": CAP})
        body = fc.card(now=NOW)
        assert f"ارسالِ امروز: {CAP} از {CAP}" in body, body
        assert "سقفِ امروز پر شده" in body, body
    finally:
        _on(False)


# ─── ۲: ندانستن هرگز صفر گزارش نمی‌شود ─────────────────────────────────────
def t_b_a_corrupt_counter_is_unknown_never_zero():
    """فایلِ خراب: نه ۰ (دروغِ خوش‌بین)، نه ۱۰ (دروغِ fail-closed ِ worker)."""
    _on()
    try:
        _counter(raw="{این جیسون نیست")
        snap = fc.outbound_snapshot(now=NOW)
        assert snap["today"] is None, snap
        body = fc.card(now=NOW)
        assert "ارسالِ امروز: نامعلوم" in body, body
        assert "ارسالِ امروز: 0" not in body, body
        # همان فایل در worker عددِ سقف را می‌دهد (fail-closed). کارت نباید آن را
        # به‌عنوان «۱۰ تا رفت» نشان دهد — این تفاوت خودِ گارد است.
        assert ow.sends_today(now=NOW) == CAP, "قراردادِ fail-closed ِ worker عوض شده"
        assert f"ارسالِ امروز: {CAP} از" not in body, body
    finally:
        _on(False)


def t_c_a_missing_counter_is_unknown_never_zero():
    """شمارندهٔ نساخته: شاید هیچ‌وقت چیزی نرفته، شاید مسیرِ state عوض شده.
    این دو از بیرون یک شکل‌اند ⇒ کارت حق ندارد یکی‌شان را انتخاب کند."""
    _on()
    try:
        _no_counter()
        snap = fc.outbound_snapshot(now=NOW)
        assert snap["today"] is None and snap["why"] == "no-counter", snap
        body = fc.card(now=NOW)
        assert "ارسالِ امروز: نامعلوم" in body, body
        assert "ارسالِ امروز: 0" not in body, body
        assert "شمارندهٔ ارسال هنوز ساخته نشده" in body, body
    finally:
        _on(False)


def t_d_a_counter_from_another_day_is_an_honest_zero():
    """طرفِ دیگرِ همان سکه: اگر شمارنده **خوانده شد** و مالِ دیروز بود، امروز
    واقعاً صفر است و باید صفر بگوید. «نامعلوم»ِ همیشگی هم بی‌مصرف است."""
    _on()
    try:
        _counter({"date": ow._day_str(NOW - 3 * 86400), "sent": 7})
        snap = fc.outbound_snapshot(now=NOW)
        assert snap["today"] == 0 and snap["why"] == "rollover", snap
        body = fc.card(now=NOW)
        assert f"ارسالِ امروز: 0 از {CAP}" in body, body
        assert "ارسالِ امروز: نامعلوم" not in body, body
    finally:
        _on(False)


# ─── ۳: دفترِ قیف — کل ارسال و صف ──────────────────────────────────────────
def t_e_the_ledger_and_the_queue_render_from_the_funnel_db():
    """«چند تا تأیید شد» و «چند تا منتظر است» از رویدادهای واقعیِ funnel.db."""
    _on()
    try:
        _fresh_ledger("e")
        _counter({"date": TODAY, "sent": 1})
        _record("communication.sent", "L-sent-1")
        _record("effect.released", "L-wait-1")
        _record("effect.released", "L-wait-2")
        _record("communication.failed", "L-bad-1")
        body = fc.card(now=NOW)
        assert "در دفتر: 1 ارسالِ تأییدشده · 1 ناموفق" in body, body
        assert "در صف: 2 منتظرِ ارسال" in body, body
    finally:
        _heal_db()
        _on(False)


def t_e2_the_authorized_queue_renders_from_the_gates_own_store():
    """«چند تا مجازِ ارسال شده» از دفترِ مجوزِ خودِ گیت — و کارت بیش از آن
    چیزی که این دفتر می‌داند ادعا نمی‌کند («تا حالا»، نه «الان در صف»)."""
    _on()
    try:
        _counter({"date": TODAY, "sent": 1})
        _authz({"eff-1": {"lead_id": "L1"}, "eff-2": {"lead_id": "L2"},
                "eff-3": {"lead_id": "L3"}})
        body = fc.card(now=NOW)
        assert "مجازِ ارسال: 3 تا حالا" in body, body
        assert fc._authorized_count() == (3, "ok")
    finally:
        _on(False)


def t_e3_a_missing_or_broken_authz_store_is_unknown_never_zero():
    _on()
    try:
        _counter({"date": TODAY, "sent": 1})
        _no_authz()
        body = fc.card(now=NOW)
        assert "مجازِ ارسال: نامعلوم" in body, body
        assert "مجازِ ارسال: 0" not in body, body
        assert "دفترِ مجوزِ ارسال هنوز ساخته نشده" in body, body
        _authz(raw="[]")             # dict نیست ⇒ ندانستن، نه ۰
        assert fc._authorized_count()[0] is None, fc._authorized_count()
        _authz(raw="{نه جیسون")
        assert fc._authorized_count() == (None, "corrupt")
        assert "مجازِ ارسال: نامعلوم" in fc.card(now=NOW)
    finally:
        _no_authz()
        _on(False)


def t_e4_the_queue_line_never_prints_a_zero_nobody_can_back_up():
    """امروز هیچ‌کس `effect.released` را در funnel.db نمی‌نویسد (گیت آن را در
    `events.jsonl` می‌زند). پس «در صف: 0» یعنی «دفتر صف را نمی‌شناسد» که به
    چشمِ مالک می‌شود «هیچی در صف نیست» — همان صفرِ مطمئنِ ممنوع."""
    _on()
    try:
        _fresh_ledger("e4")
        _counter({"date": TODAY, "sent": 1})
        _record("communication.sent", "L-only-sent")
        body = fc.card(now=NOW)
        assert "در دفتر: 1 ارسالِ تأییدشده" in body, body
        assert "در صف: 0" not in body, body
    finally:
        _heal_db()
        _on(False)


def t_e5_our_authz_path_is_the_gates_authz_path():
    """کارت مسیرِ دفترِ مجوز را برای ارزانی کپی کرده (تا `lead_effect_gate` و
    زنجیرهٔ `consent_firewall` در حلقهٔ poll import نشود). این تست همان کپی را
    قفل می‌کند: هر جابه‌جاییِ مسیر در گیت، این‌جا قرمز می‌شود."""
    sys.path.insert(0, str(_OPS / "legs"))
    import lead_effect_gate as leg
    assert Path(fc._authz_path()) == Path(leg._authz_store()), \
        (fc._authz_path(), leg._authz_store())


def t_f_an_unreadable_ledger_never_claims_zero_sends():
    """دفترِ ناخوانا = نامعلوم. «۰ ارسال» روی دیتابیسِ خراب یعنی خواباندنِ مالک."""
    _on()
    try:
        _counter({"date": TODAY, "sent": 2})
        _break_db()
        body = fc.card(now=NOW)
        assert "نامعلوم" in body, body
        assert "در دفتر: 0" not in body, body
        assert "در صف: 0" not in body, body
        # شمارنده منبعِ جداگانه‌ای است: مرگِ دفتر نباید عددِ امروز را هم بکشد.
        assert f"ارسالِ امروز: 2 از {CAP}" in body, body
    finally:
        _heal_db()
        _on(False)


def t_g_the_dark_card_still_shows_the_outbound_reality():
    """فلگِ قیف خاموش ≠ ارسال خاموش. اگر کارتِ خاموش عددِ ارسال را قایم کند،
    مالک می‌تواند ۱۰ ارسال در روز داشته باشد و کارت بگوید «هیچ»."""
    _on(False)
    _counter({"date": TODAY, "sent": 4})
    body = fc.card(now=NOW)
    assert f"ارسالِ امروز: 4 از {CAP}" in body, body


# ─── ۴: کارتِ قدیمی نباید رگرس کند ─────────────────────────────────────────
def t_h_every_old_section_of_the_card_survives():
    _on()
    try:
        _counter({"date": TODAY, "sent": 1})
        body = fc.card(now=NOW)
        for piece in ("📈 <b>قیفِ لید</b>", "برده:", "باخته:", "پول رسیده:",
                      "<b>افعال:</b>", "<code>/won lead-123</code>", "▸ نکنی:"):
            assert piece in body, (piece, body)
        for verb in fc.VERBS:
            assert f"/{verb}" in body, verb
    finally:
        _on(False)


def t_i_the_old_dark_card_keeps_its_confession():
    _on(False)
    body = fc.card(now=NOW)
    assert "هرگز" in body and "برنده" in body, body
    assert "▸ نکنی: همین‌طور می‌ماند." in body, body


def t_j_a_recorded_win_finally_shows_up_on_the_card():
    """رگرسیونِ ۰۷-۲۷ تا ۰۸-۰۱: کارت `by_event` را می‌خواند و `metrics()`
    کلیدش `events_by_type` بود — خواننده و نویسنده هرگز همدیگر را ندیدند، پس
    «برده» **همیشه** ۰ بود، حتی با بردِ ثبت‌شده. عددِ صفرِ مطمئنِ ساکت."""
    _on()
    try:
        _counter({"date": TODAY, "sent": 1})
        r = fc.record("won", "L-win-vis")
        assert r["ok"], r
        body = fc.card(now=NOW)
        assert "برده: 0" not in body, body
        assert "هنوز هیچ نتیجه‌ای نگفته‌ای" not in body, body
    finally:
        _on(False)


# ─── ۵: کارت گزارش است، نه عمل ─────────────────────────────────────────────
def t_k_rendering_the_card_never_touches_the_counter():
    """خواندنِ شمارنده نباید آن را جلو ببرد — وگرنه نگاه‌کردن به کارت سقفِ
    روزانه را می‌خورد."""
    _on()
    try:
        p = _counter({"date": TODAY, "sent": 5})
        before = p.read_bytes()
        for _ in range(3):
            fc.card(now=NOW)
        assert p.read_bytes() == before, "کارت شمارنده را عوض کرد"
    finally:
        _on(False)


def t_l_the_card_never_calls_the_sender():
    """گاردِ ساختاری: قیف به هیچ‌کدام از افعالِ ارسال/شمارش‌افزایی دست نمی‌زند.
    (تستِ قدیمی `send/settle/...` را می‌بست؛ این‌ها اسم‌های تازهٔ همان خطرند.)"""
    import ast
    tree = ast.parse(Path(fc.__file__).read_text("utf-8"))
    called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for danger in ("send_one", "drive_outbound", "record_send",
                   "release_and_settle", "_receipt"):
        assert danger not in called, f"کارتِ گزارشی عمل می‌کند: {danger}"


def t_n_the_real_writer_and_this_reader_still_speak_the_same_shape():
    """round-trip از مسیرِ **تولیدی**: خودِ `record_send` می‌نویسد، کارت می‌خواند.

    این تست فیکسچرِ دست‌ساز نمی‌سازد — چون دقیقاً همان‌جا بود که کارت چهار روز
    دروغ گفت: خواننده `by_event` می‌خواست و نویسنده `events_by_type` می‌نوشت و
    هیچ تستی این دو را کنارِ هم نگذاشته بود. اگر فردا شکلِ شمارنده عوض شود
    (کلید، تاریخ، مسیر)، این‌جا قرمز می‌شود نه در تلگرامِ مالک.
    """
    _on()
    try:
        _no_counter()
        assert fc.outbound_snapshot(now=NOW)["today"] is None, "شروع باید نامعلوم باشد"
        assert ow.record_send(now=NOW) == 1
        assert ow.record_send(now=NOW) == 2
        snap = fc.outbound_snapshot(now=NOW)
        assert snap["today"] == 2 and snap["why"] == "ok", snap
        assert f"ارسالِ امروز: 2 از {CAP}" in fc.card(now=NOW)
        # و همان فایل، یک روز بعد، صفرِ صادق است (نه ۲ ِ چسبیده).
        assert fc.outbound_snapshot(now=NOW + 86400)["today"] == 0
    finally:
        _on(False)


def t_o_the_card_never_leaks_an_authorization_token():
    """کارت اولین خوانندهٔ دفترِ مجوز بیرون از خودِ گیت است — و آن دفتر
    `token` ِ رأیِ مالک را نگه می‌دارد (خودِ گیت: «token هرگز بیرون داده
    نمی‌شود»). t_m فقط funnel.db را پر می‌کند، پس نشتِ این دفتر را نمی‌بیند.

    این‌جا با **شکلِ واقعیِ نویسنده** (`lead_effect_gate.authorize`) پر می‌شود،
    نه دیکشنریِ خالی: token و lead_id و زمان. کارت باید فقط «۲ تا حالا»
    بگوید و هیچ‌کدام از این سه را چاپ نکند.
    """
    _on()
    try:
        _counter({"date": TODAY, "sent": 1})
        _authz({"eff-a": {"lead_id": "lead-reza-9911",
                          "token": "rel-ref-7f3c9d2b41a8",
                          "authorized_at": 1_800_000_000_000},
                "eff-b": {"lead_id": "lead-sara-2277",
                          "token": "rel-ref-0e5b8c1147da",
                          "authorized_at": 1_800_000_000_500}})
        body = fc.card(now=NOW)
        assert "مجازِ ارسال: 2 تا حالا" in body, body
        for leak in ("rel-ref-7f3c9d2b41a8", "rel-ref-0e5b8c1147da",
                     "lead-reza-9911", "lead-sara-2277",
                     "eff-a", "eff-b", "1800000000000"):
            assert leak not in body, (leak, body)
        # و خودِ شمارنده هم فقط عدد برمی‌گرداند، نه محتوا.
        assert fc._authorized_count() == (2, "ok")
    finally:
        _no_authz()
        _on(False)


def t_m_the_card_shows_counts_not_customers():
    """PII: نه آدرس، نه شناسهٔ لید. کارت فقط شمار می‌گوید."""
    _on()
    try:
        _counter({"date": TODAY, "sent": 1})
        _record("communication.sent", "lead-ali-0412",
                payload={"note": "ali@example.com", "to": "ali@example.com"})
        body = fc.card(now=NOW)
        assert "@" not in body, body
        assert "lead-ali-0412" not in body and "ali" not in body, body
    finally:
        _on(False)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_funnel_sent: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
