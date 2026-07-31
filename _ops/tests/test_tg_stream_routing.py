"""test_tg_stream_routing.py — جریانِ محیطی به تاپیکِ خودش، نه به DMِ مالک.

مسئله (رأی مالک ۲۰۲۶-۰۷-۲۶): approval_channel اصلاً `message_thread_id` نداشت،
پس ۶ تابعِ beat هر تیک به DM می‌نوشتند و ۹ تاپیکِ گروه خالی می‌ماند — جریانِ
محیطی داخلِ کانالِ کمیاب‌ترین منبع (توجهِ مالک).

قیدهای این‌جا:
  · فلگ خاموش → بدنهٔ درخواست **بایت‌به‌بایت** مثل امروز (بدونِ message_thread_id).
  · chat_idِ صریح همیشه برنده است — پاسخِ مستقیم هرگز به تاپیک منحرف نمی‌شود.
  · هر شکستی (configِ نبود/خراب، تاپیکِ ساخته‌نشده، جریانِ ناشناس) → DM،
    **نه سکوت**. گم‌شدنِ پیام بدتر از پیامِ در جای اشتباه است.

صفر شبکه: http_post تزریق می‌شود و فقط بدنه را ثبت می‌کند.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("tg-stream-routing")

import opslib             # noqa: E402
import approval_channel as ac   # noqa: E402

CHAT = -1004475788460
TOPICS = {"system": 28, "knowledge": 29, "cartographer": 65, "lead": 22}


def _write_cfg(chat=CHAT, topics=None):
    p = Path(opslib.STATE_DIR) / "telegram" / "center-config.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"chat_id": chat,
                             "topics": dict(TOPICS if topics is None else topics)},
                            ensure_ascii=False), encoding="utf-8")
    return p


def _flag(on):
    if on:
        os.environ[ac.ROUTE_FLAG] = "1"
    else:
        os.environ.pop(ac.ROUTE_FLAG, None)


class Post:
    """http_postِ تزریقی — فقط بدنه را نگه می‌دارد."""

    def __init__(self):
        self.bodies = []

    def __call__(self, url, body):
        self.bodies.append(body)
        return {"ok": True, "result": {"message_id": 1}}


def _chan(post):
    return ac.TelegramApprovalChannel(token="t" * 10, owner_chat_id=555,
                                      http_post=post)


# ─── مسیریاب ────────────────────────────────────────────────────────────────
def t_route_is_off_by_default():
    _write_cfg(); _flag(False)
    assert ac._stream_route("heart") == (None, None), \
        "فلگ خاموش باید رفتارِ امروز را دست‌نخورده بگذارد"


def t_route_resolves_from_the_centre_config():
    """⚠️ بازنویسیِ مستند (VQ-TG-HOLD-001 §۵، ۰۷-۳۰ شب) — نه برای سبزکردن.

    نسخهٔ قبلی رأیِ ۰۷-۲۶ را pin کرده بود: «قلب → تاپیکِ system». رأیِ تازهٔ
    مالک صریح وارونه‌اش کرد: «هیچ doctor/heart/needs یا پیامِ هسته‌ای به
    General یا topic ِ پا fallback نکند.» جدولِ fallback حالا فقط پاها را
    دارد؛ جریانِ هسته‌ای (None, None) می‌گیرد = DM ِ مالک، نه گروه، نه سکوت.
    وارونه‌کردنِ دوباره رأیِ سومِ ثبت‌شده می‌خواهد."""
    _write_cfg(); _flag(True)
    try:
        for core in ("heart", "doctor", "needs", "brain", "discovery",
                     "cortisol", "alert", "c6", "summary"):
            assert ac._stream_route(core) == (None, None), \
                f"{core} هنوز به تاپیکِ گروه fallback می‌کند"
        # پاها ماندند — حذفِ بیش از حد هم شکست است:
        assert ac._stream_route("map") == (CHAT, 65), "چشم → cartographer"
        assert ac._stream_route("lead") == (CHAT, 22), "لید → تاپیکِ خودش"
    finally:
        _flag(False)


def t_unknown_stream_falls_back_to_dm():
    _write_cfg(); _flag(True)
    try:
        assert ac._stream_route("no-such-stream") == (None, None)
        assert ac._stream_route("") == (None, None)
        assert ac._stream_route(None) == (None, None)
    finally:
        _flag(False)


def t_broken_config_falls_back_to_dm_not_silence():
    _flag(True)
    p = Path(opslib.STATE_DIR) / "telegram" / "center-config.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        p.write_text("{ this is not json", encoding="utf-8")
        assert ac._stream_route("heart") == (None, None)
        p.unlink()
        assert ac._stream_route("heart") == (None, None), "فایلِ نبود هم باید DM بدهد"
        # تاپیکِ ساخته‌نشده
        _write_cfg(topics={"lead": 22})
        assert ac._stream_route("heart") == (None, None)
    finally:
        _flag(False)
        _write_cfg()


# ─── send_text ──────────────────────────────────────────────────────────────
def t_send_text_flag_off_is_byte_identical():
    _write_cfg(); _flag(False)
    p = Post()
    assert _chan(p).send_text("سلام", None, stream="heart") is True
    b = p.bodies[-1]
    assert "message_thread_id" not in b, "فلگ خاموش نباید بدنه را عوض کند"
    assert b["chat_id"] == 555, "باید همان DMِ مالک بماند"


def t_send_text_routes_to_the_topic():
    """⚠️ بازنویسیِ مستند (VQ-TG-HOLD-001 §۵) — جریانِ پا همچنان به تاپیکش
    می‌رود (این نیمهٔ گارد زنده ماند)، ولی جریانِ هسته‌ای دیگر **هرگز** از
    این مسیر به گروه نمی‌رسد — heart حالا از ماشینِ حالت می‌گذرد و اگر به
    ارسالِ مستقیم برسد مقصدش DM ِ مالک است، نه تاپیکِ system."""
    _write_cfg(); _flag(True)
    try:
        p = Post()
        _chan(p).send_text("لیدِ تازه", None, stream="lead")
        b = p.bodies[-1]
        assert b["chat_id"] == CHAT, f"پا به گروه نرفت: {b['chat_id']}"
        assert b["message_thread_id"] == 22, f"به تاپیکِ لید نرفت: {b}"
        # و هسته‌ای: هرچه بشود، chat ِ گروه نمی‌شود.
        p2 = Post()
        _chan(p2).send_text("ضربان", None, stream="heart")
        if p2.bodies:                       # ممکن است HOLD/digest شده باشد — ارسال‌نشدن هم قبول
            assert p2.bodies[-1]["chat_id"] != CHAT, \
                f"هسته‌ای به گروه رفت: {p2.bodies[-1]}"
    finally:
        _flag(False)


def t_explicit_chat_always_wins():
    """پاسخِ مستقیم به یک پیام هرگز نباید به تاپیکِ دیگری منحرف شود.

    ۰۷-۳۱ (گاردِ forum، پاریتی با tg_api / shared-transport-18): همین سایتِ
    شمرده‌شدهٔ audit حالا topic_id ِ صریح هم می‌دهد — chat ِ مثبت (DM) هرگز
    message_thread_id نمی‌گیرد (thread+DM = ۴۰۰ و پیامِ گم). حذفِ گاردِ
    `target < -1000` این تست را قرمز می‌کند. (اتصالِ thread به گروهِ forum را
    t_send_text_routes_to_the_topic قفل کرده است.)"""
    _write_cfg(); _flag(True)
    try:
        p = Post()
        _chan(p).send_text("جواب", None, chat_id=999, stream="heart", topic_id=7)
        b = p.bodies[-1]
        assert b["chat_id"] == 999
        assert "message_thread_id" not in b
    finally:
        _flag(False)


def t_no_stream_still_goes_to_owner():
    _write_cfg(); _flag(True)
    try:
        p = Post()
        _chan(p).send_text("بدونِ جریان")
        b = p.bodies[-1]
        assert b["chat_id"] == 555 and "message_thread_id" not in b
    finally:
        _flag(False)


def t_rfc_card_refuses_an_oversized_callback_loudly():
    """۲۰۲۶-۰۷-۲۶: `rfc_id` بلند → `callback_data` > ۶۴ بایت → تلگرام کلِ پیام را
    ۴۰۰ می‌کند → `send_text` استثنا را می‌بلعد → کارت بی‌هیچ ردی گم می‌شود.
    گارد باید **قبل از ارسال** بایستد و alert بدهد، نه اینکه بی‌صدا False بدهد."""
    p = Post()
    ch = _chan(p)
    alerts = []
    orig = ac.opslib.alert
    ac.opslib.alert = lambda msgs: alerts.append(list(msgs))
    try:
        ok = ch.rfc_card(rfc_id="c6-" + ("x" * 60), summary="خلاصه")
        assert ok is False, "کارتِ خیلی بلند نباید ارسال شود"
        assert not p.bodies, "هیچ درخواستی نباید به تلگرام برود"
        assert alerts, "شکست باید دیده شود، نه بی‌صدا"
        assert "64" in " ".join(alerts[0]), alerts
    finally:
        ac.opslib.alert = orig


def t_every_stream_key_maps_to_a_real_topic_key():
    """گاردِ ضدِ typo: هر جریان باید به کلیدی اشاره کند که مرکز واقعاً می‌سازد."""
    import sys as _s
    _s.path.insert(0, str(_HERE.parent / "telegram_center"))
    import center  # noqa: WPS433
    for stream, topic_key in ac._STREAM_TOPIC.items():
        assert topic_key in center.LEG_KEYS, \
            f"جریانِ {stream!r} به کلیدِ ناشناخته {topic_key!r} می‌رود"


def t_a_keyboard_card_is_never_held_and_never_quiet_dropped():
    """⚠️ یافتهٔ اسکنِ عمیقِ ۰۷-۳۱ + رأیِ مصوبِ VQ-TG-HOLD-001:
    «نیازمندِ تأیید → فوری با کارتِ معتبر». ولی مسیرِ HOLD کیبورد را دور
    می‌ریخت و ledger با delivered=True دروغ می‌گفت — ۹ درخواستِ ابزار
    این‌طور بلعیده شده بودند و مالک عملاً هرگز نتوانسته بود ✅ بزند.
    و ساعتِ سکوت هم کارتِ دکمه‌دار را کامل می‌انداخت (نه حتی HOLD)."""
    _write_cfg(); _flag(True)
    kb = {"inline_keyboard": [[{"text": "✅", "callback_data": "tr:y:x"}]]}
    try:
        # (الف) سیاستِ HOLD ِ تزریقی: بی‌کیبورد = نگه؛ باکیبورد = ارسال به DM.
        # (سیاستِ واقعی در پروسهٔ organism لود می‌شود؛ این‌جا همان قرارداد
        # تزریق می‌شود تا خودِ شاخهٔ send_text سنجیده شود نه لودر.)
        import approval_channel as _ac1
        held = []

        class _SP:
            HOLD = "hold"
            def route(self, stream):
                return ("hold", "x")
            def hold(self, stream, text):
                held.append((stream, text))

        orig_sp = _ac1.load_surface_policy
        _ac1.load_surface_policy = lambda: _SP()
        try:
            p1 = Post()
            r1 = _chan(p1).send_text("درخواستِ ابزار", None, stream="needs")
            assert not p1.bodies and held, "مسیرِ HOLD ِ تزریقی کار نکرد"
            p2 = Post()
            r2 = _chan(p2).send_text("درخواستِ ابزار", kb, stream="needs")
            assert p2.bodies, "کارتِ دکمه‌دار هم بلعیده شد — رأیِ HOLD-001 نقض"
            assert p2.bodies[-1].get("reply_markup") is not None,                 "کیبورد باز هم دور ریخته شد"
            assert p2.bodies[-1]["chat_id"] == 555,                 f"کارت به DM ِ مالک نرفت: {p2.bodies[-1]['chat_id']}"
        finally:
            _ac1.load_surface_policy = orig_sp
        # (ب) ساعتِ سکوت: پیامِ عادی می‌افتد، کارتِ دکمه‌دار هرگز
        import approval_channel as _ac2
        orig = _ac2._quiet_now
        _ac2._quiet_now = lambda: True
        try:
            p3 = Post()
            _chan(p3).send_text("محیطیِ عادی", None, stream="discovery")
            assert not p3.bodies, "ساعتِ سکوت پیامِ عادی را باید بیندازد"
            p4 = Post()
            _chan(p4).send_text("کارتِ تأیید", kb, stream="discovery")
            assert p4.bodies, "ساعتِ سکوت کارتِ دکمه‌دار را خورد"
        finally:
            _ac2._quiet_now = orig
    finally:
        _flag(False)


def t_b_quiet_hours_hold_not_drop_with_receipt():
    """رأی ۰۷-۳۱ (inner-bot-14): ساعتِ سکوت = HOLD نه DROP.

    پیامِ محیطیِ غیرِدکمه‌دار در بازهٔ سکوت (۱) فرستاده نمی‌شود، (۲) از همان
    ماشینِ hold می‌گذرد (طبقه‌بندِ فوری/digest/آرشیو — سکوت ≠ فراموشی)، و
    (۳) رسیدِ سه‌حالتیِ d="held" می‌گذارد. جهش (برگرداندنِ return False ِ
    لخت) هر سه assert را قرمز می‌کند. معافیت‌ها (دکمه‌دار، _NEVER_QUIET)
    را t_a قفل کرده است."""
    _write_cfg(); _flag(False)
    import approval_channel as _ac
    held = []

    class _SP:
        HOLD = "hold"

        def route(self, stream):
            return (None, None)     # مسیرِ route این تست را منحرف نکند

        def hold(self, stream, text):
            held.append((str(stream), str(text)))
            return True

    log_p = Path(opslib.STATE_DIR) / "tg-send-log.jsonl"
    if log_p.exists():
        log_p.unlink()
    orig_quiet = _ac._quiet_now
    orig_sp = _ac.load_surface_policy
    _ac._quiet_now = lambda: True
    _ac.load_surface_policy = lambda: _SP()
    os.environ["OCTOPUS_TG_SEND_LOG"] = "1"
    try:
        p = Post()
        r = _chan(p).send_text("گزارشِ نیمه‌شب", None, stream="discovery")
        assert r is False and not p.bodies, "ساعتِ سکوت نباید بفرستد"
        assert held and held[0][0] == "discovery", \
            "پیامِ ساعتِ سکوت باید واردِ ماشینِ hold شود، نه دور ریخته"
        rows = [json.loads(x) for x in
                log_p.read_text("utf-8").splitlines() if x.strip()]
        assert rows, "رسیدِ held نوشته نشد"
        last = rows[-1]
        assert last["state"] == "held" and last["ok"] is False, last
        assert last["bot_role"] == "inner" and last["surface"] == "hold", last
    finally:
        os.environ.pop("OCTOPUS_TG_SEND_LOG", None)
        _ac._quiet_now = orig_quiet
        _ac.load_surface_policy = orig_sp


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_stream_routing: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
