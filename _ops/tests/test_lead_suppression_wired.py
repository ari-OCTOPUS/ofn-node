"""test_lead_suppression_wired.py — قفلِ قانونی فقط وقتی معنا دارد که **وصل** باشد.

زمینه، و چرا این فایل جدا از `test_lead_suppression.py` است
──────────────────────────────────────────────────────────
آن فایل ماژول را می‌سنجد و ۱۲/۱۲ سبز است. این فایل **درزها** را می‌سنجد — و
هر دو درز روزِ ساخت شکسته بودند، در حالی که هر دو طرف جداگانه سبز بودند.

درزِ ۱ — ورودی. پیامِ خروجیِ خودمان قول می‌دهد «reply with the word STOP». ولی
یک STOP ِ ورودی در گاردِ ۴ ِ `classify` (`no_service_term`) می‌مرد و
«unsubscribe» در گاردِ ۳ (`marketing_marks`) — هر دو **بی هیچ ردی**. یعنی
سیستم لغوِ اشتراک را وعده می‌داد و ساختاراً کر بود. Spam Act 2003 دقیقاً همین
را جریمه می‌کند، و `OCTOPUS_WIRE_LEAD_OUTBOUND` امروز در هر چهار پروسه مسلح
است — پس این فرضی نیست.

درزِ ۲ — خروجی، و این بدترین بود چون **در جهتِ ایمنیِ کاذب** بود:

    نویسنده  lead_suppression.record_optout   → کلید = 'e1:' + هشِ pbkdf2
    خواننده  transport._store_suppressed(x)   → جست‌وجوی متنِ سادهٔ آدرس

هرگز همدیگر را پیدا نمی‌کردند. مشتری STOP می‌زد، رکورد ثبت می‌شد، گاردِ ارسال
متنِ ساده می‌گشت، چیزی نمی‌یافت، و **می‌فرستاد**. هش‌کردن برای حریمِ خصوصی
درست بود؛ نگاه‌نکردن به هش، باگ. این دقیقاً الگوی «سبز در تست، گرسنه در تولید»
است — با این تفاوت که اینجا عارضه‌اش حقوقی است، نه فقط سکوت.

ناوردیِ حاکم: **هر که opt-out کرده باید در همان مسیری پیدا شود که ارسال از آن
عبور می‌کند** — نه در مسیری که تست ساخته.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness  # noqa: E402
ENV = harness.setup("lead-suppression-wired")

sys.path.insert(0, str(_HERE.parent / "legs"))
import os                          # noqa: E402
import lead_email_intake as ie     # noqa: E402
import lead_suppression as ls      # noqa: E402
import lead_outbound_transport as tx  # noqa: E402

_ADDR = "sam.jones@customer.test"


def _armed():
    os.environ[ls.FLAG] = "1"


def _disarmed():
    os.environ.pop(ls.FLAG, None)


def _msg(body: str, addr: str = _ADDR, subject: str = "") -> dict:
    return {"message_id": f"<{abs(hash(body)) % 10**8}@x>",
            "from": f"Sam Jones <{addr}>", "subject": subject,
            "body": body, "date": "2026-08-01"}


_INQUIRY = "Hi, I need my 3 bedrooms painted in Carlingford. When can you visit?"


# ── درزِ ۱ · ورودی: STOP باید شنیده شود ─────────────────────────────────────
def t_a_the_beat_hears_stop_before_the_inquiry_guards():
    """قلبِ ماجرا: پیش از این تغییر، هر سه مورد `is_inquiry=False` می‌شدند و
    از هم قابلِ تفکیک نبودند — یعنی رد شدن و لغو کردن یک شکل داشتند."""
    for body in ("STOP", "stop", "Please unsubscribe me", "REMOVE ME from your list"):
        v = ie._classify_hearing_optout(_msg(body))
        assert v.get("opt_out") is True, (body, v)
        assert v.get("is_inquiry") is False, (body, v)


def t_b_a_real_inquiry_is_untouched():
    """ناوردیِ رگرسیون — و مهم‌تر از خودِ فیچر: اگر یک استعلامِ سالم به‌اشتباه
    opt-out شود، آن مشتری **برای همیشه** از دست می‌رود (suppression ابدی است)."""
    v = ie._classify_hearing_optout(_msg(_INQUIRY, subject="painting quote"))
    assert not v.get("opt_out"), v
    assert v["is_inquiry"] is True, v
    assert v["channel"], v


def t_c_our_own_footer_quoted_back_is_not_an_optout():
    """بدترین مثبتِ کاذبِ ممکن.

    پاورقیِ خودمان کلمهٔ STOP را دارد. هر پاسخِ عادیِ مشتری آن را نقل می‌کند.
    اسکنِ سادهٔ کلِ متن، **هر مشتریِ واقعی که جواب می‌دهد** را برای همیشه
    suppress می‌کرد.
    """
    quoted = (_INQUIRY + "\n\n"
              "On Fri, 1 Aug 2026 at 09:00, Master Painting wrote:\n"
              "> Thanks for your enquiry - a couple of quick questions\n"
              "> If you'd rather not hear from us again, just reply with the word STOP\n")
    v = ie._classify_hearing_optout(_msg(quoted, subject="Re: your enquiry"))
    assert not v.get("opt_out"), f"نقلِ پاورقیِ خودمان opt-out خوانده شد\n{v}"


def t_d_the_beat_counts_optouts_separately_from_drops():
    """«رد شد» و «لغو کرد» دو چیزِ کاملاً متفاوت‌اند و نباید در یک شمارنده
    قاطی شوند — وگرنه هیچ‌کس نمی‌فهمد چند نفر دارند می‌روند."""
    _armed()
    try:
        msgs = [_msg("STOP"), _msg("just a newsletter about shoes"),
                _msg(_INQUIRY, subject="painting quote")]
        os.environ[ie.FLAG] = "1"
        os.environ[ie.DOWNSTREAM_FLAG] = "1"
        res = ie.beat(fetch_fn=lambda **k: msgs, submit_fn=lambda c, s: {"status": "accepted",
                                                                        "lead_id": "L1"})
        assert res.get("opt_outs") == 1, res
        assert res.get("dropped") == 1, res
        assert res.get("inquiries") == 1, res
    finally:
        os.environ.pop(ie.FLAG, None)
        os.environ.pop(ie.DOWNSTREAM_FLAG, None)
        _disarmed()


# ── درزِ ۲ · خروجی: نویسنده و خواننده باید همدیگر را پیدا کنند ──────────────
def t_e_the_send_gate_finds_what_the_writer_wrote():
    """**مهم‌ترین تستِ این فایل.**

    نویسنده هش می‌نویسد، خواننده باید هش را هم بپرسد. پیش از فیکس این تست
    قرمز بود و عارضه‌اش این: کسی که STOP زده، ایمیل می‌گرفت.
    """
    _armed()
    try:
        rec = ls.record_optout(_ADDR, reason=ls.REASON_STOP, lead_id="L1")
        # ⚠️ کدها را از خودِ ماژول بگیر، نه از حافظه. اولین نسخهٔ این تست
        # `("recorded", "already")` را حدس زد و قرمز شد، در حالی که کدِ واقعی
        # `CODE_ALREADY = "already-suppressed"` بود — پروبِ من غلط بود نه کد.
        assert rec.get("code") in (ls.CODE_RECORDED, ls.CODE_ALREADY), rec
        assert rec.get("recorded") is True, rec
        hit = tx._store_suppressed(ls.normalize_address(_ADDR))
        assert hit, "گاردِ ارسال رکوردی را که خودِ سیستم نوشت پیدا نکرد"
    finally:
        _disarmed()


def t_f_a_clean_address_is_not_suppressed():
    """جفتِ متضاد: اگر همه‌چیز suppressed برگردد، گارد بی‌معنی است."""
    assert not tx._store_suppressed("someone.else@customer.test")


def t_g_the_raw_address_is_never_on_disk():
    """حریمِ خصوصی — و دلیلِ وجودِ هش. اگر روزی کسی برای «ساده‌ترشدن» متنِ ساده
    بنویسد، این تست می‌گیردش."""
    _armed()
    try:
        ls.record_optout(_ADDR, reason=ls.REASON_STOP)
        root = Path(os.environ["ORG_ROOT"]) / "_ops" / "state"
        needles = [_ADDR.encode(), _ADDR.split("@")[0].encode(),
                   _ADDR.encode("utf-16-le")]
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            try:
                blob = p.read_bytes()
            except OSError:
                continue
            for n in needles:
                assert n not in blob, f"آدرسِ خام در {p.name} پیدا شد"
    finally:
        _disarmed()


def t_h_end_to_end_stop_then_send_is_refused():
    """سناریوی واقعی، از مسیرِ تولیدی: مشتری استعلام می‌دهد، بعد STOP می‌زند،
    بعد سیستم می‌خواهد بفرستد. باید رد شود."""
    _armed()
    try:
        v = ie._classify_hearing_optout(_msg("STOP"))
        assert v.get("opt_out")
        ls.record_optout(_ADDR, reason=ls.REASON_STOP, lead_id="L9")
        out = tx.send({"lead_id": "L9", "contact": {"email": _ADDR}},
                      {"subject": "s", "body": "b"},
                      send_impl=lambda *a, **k: (_ for _ in ()).throw(
                          AssertionError("ارسال اتفاق افتاد — گارد شکست")))
        assert out.get("sent") is False, out
        assert out.get("status") == "SUPPRESSED", out
    finally:
        _disarmed()


def t_i_hearing_is_never_gated_by_the_flag():
    """شنیدن هرگز نباید خاموش‌شدنی باشد.

    فلگ فقط **نوشتن** را گیت می‌کند. اگر شنیدن هم گیت شود، خاموش‌بودنِ فلگ
    یعنی برگشت به همان حالتی که STOP بی‌صدا دور ریخته می‌شد — و آن دقیقاً
    وضعیتِ غیرقانونی است.
    """
    _disarmed()
    v = ie._classify_hearing_optout(_msg("STOP"))
    assert v.get("opt_out") is True, v


def t_j_a_broken_suppression_module_never_kills_intake():
    """fail-soft: اگر ماژول بترکد، `classify` ِ امروز اجرا می‌شود — لیدِ
    ازدست‌رفته از استثنا بهتر نیست، ولی سکوتِ کاملِ لوله بدتر است."""
    orig = ls.classify_with_optout
    ls.classify_with_optout = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    try:
        v = ie._classify_hearing_optout(_msg(_INQUIRY, subject="painting quote"))
        assert v["is_inquiry"] is True, v
    finally:
        ls.classify_with_optout = orig


def t_ja_no_salt_and_no_hashed_rows_must_not_block_everything():
    """گاردِ ایمنی نباید به قطعِ سراسریِ سرویس تبدیل شود.

    نسخهٔ اولِ سیم‌کشیِ من دقیقاً همین را کرد: هر ردیفِ suppression ِ قدیمی +
    نبودِ نمک ⇒ `salt-unavailable` ⇒ **هر** ارسالی بسته شد، و سه تستِ
    `test_lead_outbound_transport` قرمز شدند.

    استدلالِ اصلاح: نمک در اولین نوشتنِ ما ساخته می‌شود، پس نبودش یعنی هرگز
    ردیفِ هش‌داری ننوشته‌ایم، پس چیزی برای ازدست‌دادن نیست و جست‌وجوی متنِ ساده
    قطعی است. fail-closed فقط برای ابهامِ **واقعی**.
    """
    _disarmed()
    store_p = Path(os.environ["ORG_ROOT"]) / "_ops" / "state" / "legs" / "no-salt.db"
    store_p.parent.mkdir(parents=True, exist_ok=True)
    import consent_store as cs
    st = cs.ConsentStore(store_p)
    st.insert_suppression("someone.legacy@customer.test", "email", "manual_dnc")
    st.close()
    res = ls.is_suppressed("brand.new@customer.test", store_path=store_p)
    assert res["suppressed"] is False, f"بدونِ ردیفِ هش‌دار نباید ببندد: {res}"
    hit = ls.is_suppressed("someone.legacy@customer.test", store_path=store_p)
    assert hit["suppressed"] is True, f"ردیفِ قدیمیِ متنِ ساده باید پیدا شود: {hit}"


def t_jb_a_real_hashed_row_with_no_salt_is_still_fail_closed():
    """جفتِ متضاد: ابهامِ **واقعی** باید همچنان ببندد.

    اگر ردیفِ `e1:` وجود دارد ولی نمک رفته، ممکن است همان آدرس باشد و
    نمی‌دانیم — آن‌جا سکوت جایز نیست.
    """
    _disarmed()
    store_p = Path(os.environ["ORG_ROOT"]) / "_ops" / "state" / "legs" / "lost-salt.db"
    store_p.parent.mkdir(parents=True, exist_ok=True)
    import consent_store as cs
    st = cs.ConsentStore(store_p)
    st.insert_suppression(ls.FP_PREFIX + "0" * 64, "email", "stop_reply")
    st.close()
    salt = Path(os.environ["ORG_ROOT"]) / "_ops" / "state" / "legs" / "lead-suppression.salt"
    if salt.exists():
        salt.unlink()
    os.environ.pop(ls.SALT_ENV, None)
    res = ls.is_suppressed("anyone@customer.test", store_path=store_p)
    assert res["suppressed"] is True, f"ابهامِ واقعی باید ببندد: {res}"
    assert res["reason"] == ls.CODE_SALT_UNAVAILABLE, res


def t_k_the_wire_actually_exists_in_production():
    """گاردِ کدِ مرده.

    این ماژول روزِ ساختش **صفر صداکنندهٔ تولیدی** داشت با ۱۲ تستِ سبز — سومین
    بارِ همین الگو در یک هفته. اگر کسی سیم را بردارد، این تست باید قرمز شود،
    نه اینکه سوییت سبز بماند و قابلیت بی‌صدا بمیرد.
    """
    import ast
    seen = set()
    for name in ("lead_email_intake.py", "lead_outbound_transport.py"):
        src = (_HERE.parent / "legs" / name).read_text("utf-8", errors="replace")
        for n in ast.walk(ast.parse(src)):
            if isinstance(n, ast.Import):
                for a in n.names:
                    if a.name.split(".")[-1] == "lead_suppression":
                        seen.add(name)
            elif isinstance(n, ast.ImportFrom) and (n.module or "").endswith("lead_suppression"):
                seen.add(name)
    assert seen == {"lead_email_intake.py", "lead_outbound_transport.py"}, (
        f"سیمِ suppression در {sorted({'lead_email_intake.py', 'lead_outbound_transport.py'} - seen)} نیست")


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_lead_suppression_wired: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
