"""test_lead_suppression.py — دروازهٔ حقوقیِ opt-out، جوری که یک رگولاتور بخواندش.

آن‌چه پیش از این تغییر روی این درخت **قابلِ سنجش** بود (بازسازیِ رفتارِ پیشین در t_b):
  · `lead_email_intake.classify({'body': 'STOP'})`      → reason='no_service_term'
  · `lead_email_intake.classify({'body': 'unsubscribe'})` → reason='marketing_marks'
هر دو `is_inquiry=False` و **بدونِ هیچ ردی**؛ جدولِ `suppression` در `consent.db` ِ زنده
از ۲۰۲۶-۰۷-۲۲ تا امروز صفر ردیف دارد (خودم read-only شمردم). یعنی پیامِ خروجی قول
«reply with the word STOP» می‌دهد (`lead_first_reply.py:376`) و ماشین کر است. با
`OCTOPUS_WIRE_LEAD_OUTBOUND=1` و `OCTOPUS_SMTP_USE_GMAIL=1` ِ مسلح، این بدترین ترکیبِ
ممکن زیرِ Spam Act 2003 (Cth) است.

سه پذیرشِ لِین، و کجا اثبات می‌شوند:
  (الف) STOP **پیش از** گاردهای استعلام شناخته می‌شود  → t_b
  (ب)  آدرس هرگز plaintext ذخیره نمی‌شود              → t_f
  (ج)  مخاطبِ suppressشده در **زمانِ ارسال** رد می‌شود،
       حتی وقتی effectِ معتبرِ authorizeشده وجود دارد   → t_g

هیچ تستی اینجا شبکه نمی‌زند، ایمیل نمی‌فرستد و به درختِ زنده دست نمی‌زند: کلِ state
داخلِ `harness.setup` است و transport اصلاً import نمی‌شود.
"""
import ast
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness  # noqa: E402
ENV = harness.setup("lead-suppression")

sys.path.insert(0, str(_HERE.parent / "legs"))
import consent_store as cs          # noqa: E402
import lead_effect_gate as leg      # noqa: E402
import lead_email_intake as ie      # noqa: E402
import lead_suppression as ls       # noqa: E402
import opslib                       # noqa: E402

SRC = (Path(ls.__file__)).read_text("utf-8")

OPTOUT_ADDR = "sam.jones@optout-lane1.test"
KEEP_ADDR = "wants.quote@customer-lane1.test"

# پاورقیِ واقعیِ خودمان (lead_first_reply.py:376-377) — عیناً، چون تلهٔ اصلی همین است.
OWN_FOOTER = ("If you'd rather not hear from us again, just reply with the word STOP "
              "and we won't contact you again.")


def _arm():
    os.environ[ls.FLAG] = "1"


def _disarm():
    os.environ.pop(ls.FLAG, None)


def _msg(body="", subject="", frm=f"Sam Jones <{OPTOUT_ADDR}>", **over):
    m = {"message_id": "<m1@optout-lane1.test>", "from": frm, "subject": subject,
         "body": body, "date": "2026-08-01"}
    m.update(over)
    return m


def _snapshot(root: Path):
    """امضایِ کاملِ درختِ state — (مسیر، اندازه، mtime_ns) برای هر فایل."""
    out = {}
    if not root.exists():
        return out
    for p in sorted(root.rglob("*")):
        if p.is_file():
            st = p.stat()
            out[str(p.relative_to(root))] = (st.st_size, st.st_mtime_ns)
    return out


def _store_bytes() -> bytes:
    """همهٔ بایت‌های storeِ روی دیسک — شاملِ -wal و -shm.

    خواندنِ فقطِ `consent.db` یک سبزِ دروغین می‌سازد: در حالتِ WAL نوشته‌های تازه
    در `consent.db-wal` می‌نشینند و ممکن است هنوز checkpoint نشده باشند.
    """
    p = ls.db_path()
    blob = b""
    for suffix in ("", "-wal", "-shm", "-journal"):
        f = Path(str(p) + suffix)
        if f.exists():
            blob += f.read_bytes()
    return blob


# ── (خاموشی) ───────────────────────────────────────────────────────────────────
def t_a_flag_off_is_byte_identical_and_still_refuses_to_call_the_guards():
    """فلگِ خاموش = هیچ بایتی روی دیسک عوض نمی‌شود.

    این تست **اول** می‌دود (ترتیبِ الفبایی) چون هنوز هیچ‌چیز نوشته نشده؛ ولی
    مستقل از ترتیب هم معتبر است: امضایِ کلِ درختِ state را قبل و بعد می‌سنجد.
    """
    _disarm()
    root = Path(opslib.STATE_DIR)
    before = _snapshot(root)

    r = ls.record_optout(OPTOUT_ADDR, ls.REASON_STOP)
    assert r["code"] == ls.CODE_FLAG_OFF, r
    assert r["recorded"] is False

    seen = []
    v = ls.classify_with_optout(_msg(body="STOP"), inner=lambda m: seen.append(m))
    assert v["reason"] == "opt_out", v
    assert v["recorded"] is False and v["record_code"] == ls.CODE_FLAG_OFF, v
    assert seen == [], "با فلگِ خاموش هم opt-out نباید به گاردهای استعلام برسد"

    after = _snapshot(root)
    assert before == after, (
        "فلگِ خاموش باید بایت‌به‌بایتِ دیروز باشد؛ تفاوت: "
        f"{sorted(set(after) ^ set(before)) or 'محتوا/mtime'}")
    assert not ls._salt_path().exists(), "چکِ خاموش نباید نمک بسازد"


# ── (الف) ترتیب: opt-out قبل از گاردهای استعلام ────────────────────────────────
def t_b_stop_is_recognised_before_the_inquiry_guards_run():
    """پذیرشِ (الف).

    دو نیمه: (۱) بازسازیِ رفتارِ پیشین — همان گاردها امروز STOP و unsubscribe را
    بی‌رد می‌بلعند؛ (۲) رَپِر ثابت می‌کند طبقه‌بندِ استعلام **اصلاً صدا زده نمی‌شود**.
    """
    stop_msg = _msg(body="STOP")
    unsub_msg = _msg(body="Please unsubscribe me from your list.")

    # (۱) رفتارِ پیشین، از خودِ ماژولِ تولیدی (نه از fixture):
    a = ie.classify(stop_msg)
    b = ie.classify(unsub_msg)
    assert a["is_inquiry"] is False and a["reason"] == "no_service_term", a
    assert b["is_inquiry"] is False and b["reason"] == "marketing_marks", b
    assert "opt_out" not in a and "opt_out" not in b, (
        "گاردهای امروز opt-out را نمی‌شناسند — همین نبودِ کلید، خودِ شکاف است")

    # (۲) دندانِ ترتیب: inner یک جاسوس است که اگر صدا شود لو می‌رود.
    called = []

    def spy(m):
        called.append(m)
        return ie.classify(m)

    for m, expected in ((stop_msg, ls.REASON_STOP), (unsub_msg, ls.REASON_UNSUB)):
        v = ls.classify_with_optout(m, inner=spy, record=False)
        assert v["opt_out"] is True and v["reason"] == "opt_out", v
        assert v["suppression_reason"] == expected, v
    assert called == [], "opt-out هرگز نباید به گاردهای استعلام برسد"

    # و برعکس: استعلامِ واقعی حتماً باید به گاردها برسد (وگرنه رَپِر لید می‌خورد).
    real = _msg(frm=f"Ann <{KEEP_ADDR}>",
                subject="Painting quote",
                body="Hi, I'd like a quote to repaint my house in Carlingford.")
    out = ls.classify_with_optout(real, inner=spy, record=False)
    assert len(called) == 1, "استعلامِ عادی باید به طبقه‌بندِ پایین‌دست تحویل شود"
    assert out is ie.classify(real) or out["is_inquiry"] == ie.classify(real)["is_inquiry"]


def t_c_optout_vocabulary_covers_english_and_persian():
    """واژگان — و مهم‌تر، چیزهایی که **نباید** opt-out شمرده شوند."""
    yes = {
        "STOP": ls.REASON_STOP,
        "stop.": ls.REASON_STOP,
        "Please STOP": ls.REASON_STOP,
        "UNSUBSCRIBE": ls.REASON_UNSUB,
        "Remove me": ls.REASON_UNSUB,
        "take me off": ls.REASON_UNSUB,
        "opt out": ls.REASON_UNSUB,
        "Please stop emailing me about this.": ls.REASON_STOP,
        "Please remove me from your mailing list, thanks.": ls.REASON_UNSUB,
        "Do not contact me again.": ls.REASON_UNSUB,
        "توقف": ls.REASON_STOP,
        "لغو اشتراک": ls.REASON_UNSUB,
        "لغو‌اشتراک": ls.REASON_UNSUB,     # با نیم‌فاصله
        "مرا حذف کنید": ls.REASON_UNSUB,
        "دیگر تماس نگیرید": ls.REASON_STOP,
        "لطفا ایمیل نفرستید": ls.REASON_UNSUB,
    }
    for text, reason in yes.items():
        v = ls.classify_optout(_msg(body=text))
        assert v is not None, f"شناخته نشد: {text!r}"
        assert v["reason"] == reason, (text, v)

    no = [
        "Can you stop by tomorrow and give me a quote?",
        "The last painter left a mess, I had to remove it myself.",
        "Hi, I'd like a quote to repaint my 3 bedroom house in Carlingford.",
        "سلام، برای رنگ‌آمیزی داخل خانه‌ام قیمت می‌خواهم",
        "",
    ]
    for text in no:
        assert ls.classify_optout(_msg(body=text)) is None, f"مثبتِ کاذب: {text!r}"


def t_d_our_own_quoted_footer_never_suppresses_a_real_customer():
    """دندان — و پرهزینه‌ترین مثبتِ کاذبِ ممکن.

    پاورقیِ خودمان شاملِ «reply with the word STOP» است. هر مشتری‌ای که به نامهٔ ما
    جواب بدهد، آن جمله را نقل می‌کند. اسکنِ سادهٔ کلِ بدنه یعنی **هر پاسخِ واقعی**
    برای همیشه خاموش می‌شود — و suppression برگشت‌ناپذیر است.
    """
    reply = ("Hi Ari, that sounds good — can you come Tuesday morning?\n\n"
             "On Fri, 1 Aug 2026 at 09:00, M P Design <x@y.test> wrote:\n"
             f"> {OWN_FOOTER}\n")
    naive = "reply with the word stop" in reply.lower()
    assert naive is True, "بازسازیِ رفتارِ ساده‌لوحانه باید واقعاً match بدهد"
    assert ls.classify_optout(_msg(body=reply)) is None, (
        "پاسخِ مشتری که پاورقیِ خودمان را نقل کرده هرگز نباید opt-out شود")

    # ولی STOPِ واقعی با همان پاورقیِ نقل‌شده در زیرش، باید شناخته شود.
    real_stop = f"STOP\n\nOn Fri, 1 Aug 2026 at 09:00, M P Design wrote:\n> {OWN_FOOTER}\n"
    v = ls.classify_optout(_msg(body=real_stop))
    assert v is not None and v["reason"] == ls.REASON_STOP, v

    # قراردادِ خودِ جداکننده هم مستقیم پین می‌شود. چرا جداگانه: در پاسخِ متنی، چند
    # قاعدهٔ برش هم‌زمان آتش می‌کنند (`>` و «On … wrote:») و همدیگر را می‌پوشانند؛
    # ولی در پاسخِ **HTML** (Gmail: blockquote) پس از حذفِ تگ‌ها نه `>` می‌ماند نه
    # «wrote:» — آن‌جا تنها چیزی که پاورقیِ خودمان را بیرون می‌کشد همان sentinel است.
    plain = ls.unquoted(reply)
    assert "Tuesday" in plain and "stop" not in plain.lower(), plain
    html_reply = (f"<div>Thanks, Tuesday works.</div><blockquote>{OWN_FOOTER}</blockquote>")
    html_stripped = ls.unquoted(html_reply)
    assert "stop" not in html_stripped.lower(), html_stripped
    assert ls.classify_optout(_msg(body=html_reply)) is None


def t_e_bulk_and_pasted_newsletters_are_not_optout_requests_but_long_humans_are():
    """سه مرزِ مثبتِ کاذب — و مرزی که در جهتِ دیگر نباید قربانی شود.

    یادآوری: suppression برگشت‌ناپذیر است، پس هر مثبتِ کاذب یک مشتریِ واقعیِ
    برای‌همیشه‌خاموش است. ولی سخت‌گیریِ بیش‌ازحد هم یک شکافِ حقوقی است.
    """
    # (۱) خبرنامهٔ دیگران: پاورقیِ **خودشان** درخواستِ ما نیست. هدرِ انبوه فیصله می‌دهد.
    news = _msg(subject="Winter deals!",
                body="Big sale this week — click here to unsubscribe me from this list.",
                headers={"List-Unsubscribe": "<mailto:x@vendor.test>"})
    assert ls.classify_optout(news) is None, "خبرنامه نباید فرستنده‌اش را خاموش کند"

    # (۲) همان متن **بدونِ** هدرِ انبوه ولی کپی‌شده داخلِ یک ایمیلِ بلند: سقفِ طول.
    pasted = _msg(body=("Premium coatings, trade prices, next-day delivery. " * 45)
                       + " click here to unsubscribe me from this list.")
    assert len(pasted["body"]) > ls.MAX_OPTOUT_CHARS
    assert ls.classify_optout(pasted) is None, "پاورقیِ کپی‌شده نباید مشتری را خاموش کند"

    # (۳) ولی یک آدمِ واقعی که مفصل می‌نویسد و آخرش درخواستِ opt-out دارد، **هست**.
    #     سقفِ کوتاه اینجا یک شکافِ Spam Act می‌ساخت.
    human = _msg(body=(
        "Hi, thanks for getting back to me last week. We ended up going with "
        "another painter because the timing worked better for us, and honestly "
        "the kitchen job turned out fine. I appreciate you taking the time to "
        "come out and look at the place, it was good of you. Anyway I don't "
        "need anything else at the moment and I'd rather not keep getting these "
        "emails, so please remove me from your list. All the best, Ann."))
    assert 400 < len(human["body"]) <= ls.MAX_OPTOUT_CHARS
    v = ls.classify_optout(human)
    assert v is not None and v["reason"] == ls.REASON_UNSUB, (v, len(human["body"]))


# ── (ب) هرگز plaintext ─────────────────────────────────────────────────────────
def t_f_the_store_never_holds_the_plaintext_address():
    """پذیرشِ (ب) — grep روی خودِ فایلِ store (و -wal/-shm)."""
    _arm()
    try:
        r = ls.record_optout(OPTOUT_ADDR, ls.REASON_STOP, lead_id="LEAD-SUPP-1")
    finally:
        _disarm()
    assert r["ok"] and r["recorded"] and r["new"], r
    assert r["code"] == ls.CODE_RECORDED, r

    blob = _store_bytes()
    assert blob, "store باید روی دیسک وجود داشته باشد"
    local, _, domain = OPTOUT_ADDR.partition("@")
    for needle in (OPTOUT_ADDR, local, domain):
        assert needle.encode("utf-8") not in blob, f"plaintext در store پیدا شد: {needle!r}"
        assert needle.encode("utf-16-le") not in blob, f"plaintext (utf-16) پیدا شد: {needle!r}"

    # اثرِ انگشت واقعاً یک هشِ نمک‌دار است، نه آدرسِ نرمال‌شده.
    fp = ls.fingerprint(OPTOUT_ADDR)
    assert fp and fp.startswith(ls.FP_PREFIX) and len(fp) == len(ls.FP_PREFIX) + 64, fp
    assert OPTOUT_ADDR not in fp and local not in fp
    assert fp.encode("utf-8") in blob, "کلیدِ هش‌شده باید همانی باشد که در store نشسته"

    # نمک هم آدرس ندارد و کنارِ store روی دیسک است.
    assert ls._salt_path().exists()
    assert OPTOUT_ADDR.encode("utf-8") not in ls._salt_path().read_bytes()

    # ⚠️ نتیجهٔ ساختاریِ همین طراحی، صریح نوشته می‌شود چون handoff به آن وابسته است:
    # هر صداکننده‌ای که با مقدارِ **plaintext** پرس‌وجو کند (امروز
    # `consent_gate.suppression_hit_for` و `lead_outbound_transport._store_suppressed`)
    # کور است و باید به `lead_suppression.is_suppressed` سوییچ شود.
    store = cs.ConsentStore(ls.db_path())
    try:
        assert store.suppression_active(OPTOUT_ADDR.lower()) is None
        assert store.suppression_active(fp) == ls.REASON_STOP
    finally:
        store.close()


# ── (ج) رد در زمانِ ارسال ──────────────────────────────────────────────────────
def t_g_suppressed_is_refused_at_send_even_when_a_valid_authorized_effect_exists():
    """پذیرشِ (ج) — با effectِ **واقعیِ** authorizeشده از `lead_effect_gate`."""
    _arm()
    try:
        ls.record_optout(OPTOUT_ADDR, ls.REASON_STOP, lead_id="LEAD-SUPP-1")
    finally:
        _disarm()

    ok = leg.authorize("EFF-LANE1", "LEAD-SUPP-1", "tok-owner-tap")
    assert ok["ok"] and leg.is_authorized("EFF-LANE1"), ok
    authz = Path(opslib.STATE_DIR) / "legs" / "lead-effect-authz.json"
    assert authz.exists(), "effect باید واقعاً authorize شده باشد (نه ادعا)"
    assert str(authz).startswith(str(Path(opslib.STATE_DIR))), "باید در stateِ ایزوله باشد"

    suppressed_cand = {"lead_id": "LEAD-SUPP-1", "contact": {"email": OPTOUT_ADDR}}
    res = ls.check_send(suppressed_cand, effect_id="EFF-LANE1", authorized=True)
    assert res["allow"] is False, res
    assert res["code"] == ls.CODE_SUPPRESSED, res
    assert ls.REASON_STOP in res["reason"], res
    assert OPTOUT_ADDR not in str(res), "آدرسِ کامل هرگز در خروجی نمی‌نشیند"

    # بازسازیِ رفتارِ پیشینِ زمانِ ارسال: تنها چیزی که امروز جلوی release را می‌گیرد
    # authorization است — و آن **هست**. پس بدونِ این گارد، ارسال مجاز بود.
    clean_cand = {"lead_id": "LEAD-SUPP-2", "contact": {"email": KEEP_ADDR}}
    allowed = ls.check_send(clean_cand, effect_id="EFF-LANE1", authorized=True)
    assert allowed["allow"] is True, allowed
    assert allowed["code"] == ls.CODE_OK, allowed

    # و suppression هرگز به authorization رأی نمی‌دهد: با authorized=False هم همان.
    assert ls.check_send(suppressed_cand, authorized=False)["allow"] is False


def t_h_suppression_is_forever_and_idempotent():
    """دوبار حذف‌کردن بی‌ضرر است؛ برداشتنش قابلیت نیست."""
    _arm()
    try:
        first = ls.record_optout(OPTOUT_ADDR, ls.REASON_STOP)
        second = ls.record_optout(OPTOUT_ADDR, ls.REASON_UNSUB)
    finally:
        _disarm()
    assert first["recorded"] and second["recorded"], (first, second)
    assert second["new"] is False and second["code"] == ls.CODE_ALREADY, second
    assert ls.is_suppressed(OPTOUT_ADDR)["suppressed"] is True

    tree = ast.parse(SRC)
    names = [n.name for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for n in names:
        low = n.lower()
        assert not any(w in low for w in ("unsuppress", "unsupress", "lift", "purge",
                                          "delete", "unblock")), f"API لغو ساخته شده: {n}"
    up = SRC.upper()
    for sql in ("DELETE FROM", "DROP TABLE", "UPDATE SUPPRESSION"):
        assert sql not in up, f"SQLِ مخرب در ماژول: {sql}"


def t_i_rows_exist_but_salt_is_gone_fails_closed():
    """گم‌شدنِ نمک نباید بی‌صدا در را باز کند — باید ارسال را متوقف کند."""
    assert ls.is_suppressed(OPTOUT_ADDR)["suppressed"] is True, "پیش‌شرط: ردیف وجود دارد"
    salt = ls._salt_path()
    stash = salt.with_suffix(".salt.stash")
    salt.rename(stash)
    try:
        r = ls.is_suppressed(KEEP_ADDR)
        assert r["suppressed"] is True and r["code"] == ls.CODE_UNVERIFIABLE, r
        g = ls.check_send({"contact": {"email": KEEP_ADDR}}, effect_id="EFF-LANE1",
                          authorized=True)
        assert g["allow"] is False and g["code"] == ls.CODE_UNVERIFIABLE, g
    finally:
        stash.rename(salt)
    assert ls.check_send({"contact": {"email": KEEP_ADDR}})["allow"] is True


def t_j_every_refusal_carries_a_reason_code_and_never_returns_silence():
    """«رد» باید بلند باشد: هیچ None، هیچ استثنا، هیچ dictِ بی‌کُد."""
    probes = [
        ls.check_send({}),
        ls.check_send({"contact": {"email": "not-an-address"}}),
        ls.check_send({"contact": {"email": KEEP_ADDR, "opt_out": True}}),
        ls.check_send({"contact": {"email": KEEP_ADDR}, "unsubscribed": 1}),
        ls.check_send(None),
    ]
    for p in probes:
        assert isinstance(p, dict) and p.get("code"), p
        assert p["allow"] is False, p
    assert probes[0]["code"] == ls.CODE_NO_RECIPIENT
    assert probes[1]["code"] == ls.CODE_NO_RECIPIENT
    assert probes[2]["reason"] == "candidate-marker:opt_out", probes[2]
    assert probes[3]["reason"] == "candidate-marker:unsubscribed", probes[3]

    for bad in (None, "", "nonsense", 12345, {"a": 1}):
        assert isinstance(ls.is_suppressed(bad), dict)
        assert isinstance(ls.record_optout(bad), dict)
    st = ls.status()
    assert st["plaintext_stored"] is False and st["kdf_rounds"] == ls.KDF_ROUNDS
    assert st["active_suppressions"] >= 1


def t_k_it_reuses_consent_store_and_builds_no_second_store():
    """بندِ صریحِ لِین: primitiveهای موجود دوباره استفاده شوند، نه یک storeِ دوم."""
    assert "CREATE TABLE" not in SRC.upper(), "این ماژول نباید هیچ schemaای بسازد"
    called = set()
    for node in ast.walk(ast.parse(SRC)):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            called.add(node.func.attr)
    for prim in ("insert_suppression", "suppression_active", "record_event"):
        assert prim in called, f"primitiveِ موجود صدا زده نشده: {prim}"
    # و مسیرِ ما واقعاً همان فایلِ consent_store است، نه یک DB ِ موازی.
    assert ls.db_path() == Path(cs._default_path())
    assert ls.db_path().name == "consent.db"


def t_l_the_audit_trail_exists_and_carries_no_address():
    """رگولاتور ردِ append-only می‌خواهد — ولی ردی که خودش PII نباشد."""
    store = cs.ConsentStore(ls.db_path())
    try:
        rows = store.events_for_lead("LEAD-SUPP-1")
    finally:
        store.close()
    kinds = [r[1] for r in rows]
    assert "consent.suppressed" in kinds, kinds
    payloads = " ".join(str(r[6]) for r in rows)
    assert OPTOUT_ADDR not in payloads and OPTOUT_ADDR.split("@")[0] not in payloads
    assert "fp_prefix" in payloads and ls.FP_PREFIX in payloads


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_lead_suppression: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
