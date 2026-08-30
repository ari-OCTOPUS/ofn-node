"""test_tg_topic_reply_quiet.py — دو قیدِ سطحِ تلگرام که ۲۰۲۶-۰۷-۲۶ اضافه شدند.

۱) جواب در همان تاپیکی بیفتد که مالک پرسیده (`OCTOPUS_TG_TOPIC_REPLY`).
   باگِ اصلی: گروهِ مرکز فوروم است و جوابِ بی‌`message_thread_id` در **General**
   می‌افتد. یعنی بات جواب می‌داد، مالک نمی‌دید، و هیچ خطایی هم لاگ نمی‌شد —
   «فرستادم» راست بود و «رسید» دروغ. این دقیقاً همان بیماریِ «ادعایی که نمی‌تواند
   غلط باشد» است، پس آزمونش باید روی *مقصدِ واقعی* باشد نه روی موفقیتِ send.

۲) کارتِ اطلاعاتیِ خلوت (`OCTOPUS_TG_QUIET`) — بریفِ مالک: «خلوت و برای ذهنِ ADHD».
   `/live` قبلاً ۱۷۴۶ کاراکتر بود چون کلِ `/id` و `/box` را در خود تکرار می‌کرد.

صفر شبکه، صفر نوشتن بیرون از harness: ماژول‌های دادهٔ زنده با fake جایگزین می‌شوند.
"""
import os
import sys
import types
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("tg-topic-quiet")

sys.path.insert(0, str(_HERE.parent / "telegram_center"))
sys.path.insert(0, str(_HERE.parent / "tg"))

import card_render as cr      # noqa: E402
import center                 # noqa: E402
import live_commands as lc    # noqa: E402

FLAG = center.TOPIC_REPLY_FLAG


class FakeClient:
    """فقط ثبتِ فراخوان — صفر شبکه."""

    def __init__(self, owner_id=777):
        self.owner_id = owner_id
        self.sent: list = []

    def wired(self):
        return True

    def send(self, text, *, topic_id=None, keyboard=None, chat_id=None, pin=False):
        self.sent.append({"text": text, "topic_id": topic_id, "chat_id": chat_id})
        return 1

    def is_owner(self, update):
        frm = ((update.get("message") or {}).get("from")
               or (update.get("callback_query") or {}).get("from") or {})
        return frm.get("id") == self.owner_id

    def answer_callback(self, callback_id, text=""):
        return True


def _msg(*, topic=None, chat=-1004475788460, text="/now"):
    m = {"message_id": 5, "from": {"id": 777}, "chat": {"id": chat}, "text": text}
    if topic is not None:
        m["is_topic_message"] = True
        m["message_thread_id"] = topic
    return m


def _flag(on: bool):
    if on:
        os.environ[FLAG] = "1"
    else:
        os.environ.pop(FLAG, None)


# ─── ۱) مسیرِ تاپیک ──────────────────────────────────────────────────────────
def t_topic_reply_off_by_default():
    _flag(False)
    assert center.Center._reply_thread(_msg(topic=28)) is None, \
        "فلگ خاموش باید رفتارِ امروز را بایت‌به‌بایت حفظ کند"


def t_topic_reply_on_returns_thread():
    _flag(True)
    try:
        assert center.Center._reply_thread(_msg(topic=28)) == 28
    finally:
        _flag(False)


def t_general_topic_gets_no_thread():
    """در Generalِ فوروم تلگرام `is_topic_message` نمی‌فرستد — و ارسالِ
    thread_idِ ساختگی خطای ۴۰۰ می‌دهد. پس None درست است، نه محتاطانه."""
    _flag(True)
    try:
        assert center.Center._reply_thread(_msg()) is None
        # حتی اگر thread_id باشد ولی پرچمِ تاپیک نباشد (پاسخ‌زنجیره در گروهِ ساده)
        m = _msg()
        m["message_thread_id"] = 99
        assert center.Center._reply_thread(m) is None
    finally:
        _flag(False)


def t_private_chat_gets_no_thread():
    _flag(True)
    try:
        assert center.Center._reply_thread(_msg(chat=777)) is None
    finally:
        _flag(False)


def t_malformed_update_never_raises():
    _flag(True)
    try:
        for bad in ({}, {"is_topic_message": True}, {"is_topic_message": True,
                                                     "message_thread_id": "x"}):
            assert center.Center._reply_thread(bad) is None
    finally:
        _flag(False)


def t_handle_message_lands_in_the_asking_topic():
    """قیدِ واقعی: مقصدِ send، نه اینکه send موفق شد."""
    _flag(True)
    try:
        fc = FakeClient()
        c = center.Center(client=fc, render_mod=types.SimpleNamespace(
            collect_feeds=lambda: {}, render_status=lambda f: "STATUS"))
        c.handle_update({"update_id": 1, "message": _msg(topic=28)})
        assert fc.sent, "باید جواب فرستاده باشد"
        assert fc.sent[-1]["topic_id"] == 28, \
            f"جواب در تاپیکِ ۲۸ نیفتاد: {fc.sent[-1]['topic_id']!r} (همان باگِ General)"
    finally:
        _flag(False)


def t_handle_message_general_stays_unthreaded():
    _flag(True)
    try:
        fc = FakeClient()
        c = center.Center(client=fc, render_mod=types.SimpleNamespace(
            collect_feeds=lambda: {}, render_status=lambda f: "STATUS"))
        c.handle_update({"update_id": 2, "message": _msg()})
        assert fc.sent and fc.sent[-1]["topic_id"] is None
    finally:
        _flag(False)


# ─── ۲) کارتِ اطلاعاتیِ خلوت ────────────────────────────────────────────────
def t_info_card_requires_a_lead():
    """گزارشی که نتیجه‌اش ته متن است خوانده نمی‌شود — قید عمدی است."""
    try:
        cr.render_info(headline="سرخط", lead="  ")
        raise AssertionError("کارتِ بی‌سرنخ نباید ساخته شود")
    except cr.CardDesignError:
        pass


def t_info_card_enforces_length_cap():
    try:
        cr.render_info(headline="سرخط", lead="x" * (cr.MAX_TEXT_CHARS + 50))
        raise AssertionError("سقفِ طول اعمال نشد")
    except cr.CardDesignError:
        pass


def t_info_card_enforces_row_cap():
    try:
        cr.render_info(headline="س", lead="l",
                       rows=[f"r{i}" for i in range(cr.MAX_INFO_ROWS + 1)])
        raise AssertionError("سقفِ ردیف اعمال نشد")
    except cr.CardDesignError:
        pass


def t_info_card_rejects_machine_id_and_jargon():
    for bad in ({"lead": "وضعیت", "rows": ["job deadbeefcafe در صف"]},
                {"lead": "پیشنهاد با flag روشن شد"}):
        try:
            cr.render_info(headline="س", **bad)
            raise AssertionError(f"باید رد می‌شد: {bad}")
        except cr.CardDesignError:
            pass


def t_info_card_happy_path_is_short():
    card = cr.render_info(headline="🐙 زنده‌ام", lead="۸ توانایی خاموش",
                          rows=["یادگیرنده 0.36", "پول‌ساز 0.04"],
                          next_step="کاملش: /id")
    assert card["reply_markup"] is None, "کارتِ اطلاعاتی دکمه ندارد"
    assert card["plain_len"] <= cr.MAX_TEXT_CHARS
    assert card["text"].splitlines()[0].startswith("<b>")


# ─── ۳) حالتِ خلوتِ /live و /box ─────────────────────────────────────────────
def _fake_identity():
    return types.SimpleNamespace(evaluate=lambda: {
        "signals": {"delta": -0.003942, "n_delta": 1, "missing": ["sigma"]},
        "identities": {
            "organism": {"label": "ارگانیسم", "value": 0.38},
            "learner": {"label": "یادگیرنده", "value": 0.36},
            "earner": {"label": "پول‌ساز", "value": 0.0435},
        }})


def _with_fake(name, mod, fn):
    orig = sys.modules.get(name)
    sys.modules[name] = mod
    try:
        return fn()
    finally:
        if orig is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = orig


def t_quiet_live_is_short_and_keeps_the_numbers():
    out = _with_fake("identity_equations", _fake_identity(), lc._quiet_live)
    assert out, "کارتِ خلوت خالی برنگشت"
    plain = out.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "")
    assert len(plain) <= cr.MAX_TEXT_CHARS, f"{len(plain)} > {cr.MAX_TEXT_CHARS}"
    # محتوا ساده نمی‌شود: عددها باید بمانند (IQ140 — تحقیر هزینه دارد)
    assert "0.38" in out and "0.36" in out, "عددها نباید حذف شوند"
    assert "-0.0039" in out, "Δِ منفی باید صادقانه دیده شود"


def t_quiet_never_returns_silence_on_failure():
    """قیدِ سختِ امروز: شکستِ رندر هرگز نباید به سکوت ختم شود — سکوت همان باگی
    است که ۲۰۲۶-۰۷-۲۵ ساعت ۲۲:۰۳ دستورِ مالک را بی‌جواب گذاشت."""
    def boom():
        raise RuntimeError("داده خراب")
    broken = types.SimpleNamespace(evaluate=boom)
    assert _with_fake("identity_equations", broken, lc._quiet_live) == "", \
        "شکست باید «» بدهد تا dispatch به نسخهٔ کامل برگردد، نه None/استثنا"


def t_quiet_flag_is_off_by_default():
    os.environ.pop(lc.QUIET_FLAG, None)
    assert lc.quiet_on() is False
    os.environ[lc.QUIET_FLAG] = "1"
    try:
        assert lc.quiet_on() is True
    finally:
        os.environ.pop(lc.QUIET_FLAG, None)


def t_dejargon_translates_instead_of_hiding():
    """«flag-off» ترجمه می‌شود، حذف نمی‌شود — اطلاعات نباید کم شود."""
    assert lc._dejargon("coherence flag-off = unused organ") == \
        "coherence خاموش = اندامِ بی‌استفاده"
    assert "flag" not in lc._dejargon("بدون PRODUCER flag = seed").lower()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_topic_reply_quiet: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
