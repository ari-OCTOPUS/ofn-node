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
    _write_cfg(); _flag(True)
    try:
        assert ac._stream_route("heart") == (CHAT, 28), "قلب → تاپیکِ system"
        assert ac._stream_route("doctor") == (CHAT, 28)
        assert ac._stream_route("needs") == (CHAT, 28)
        assert ac._stream_route("brain") == (CHAT, 29), "مغز → تاپیکِ knowledge"
        assert ac._stream_route("discovery") == (CHAT, 29)
        assert ac._stream_route("map") == (CHAT, 65), "چشم → تاپیکِ cartographer"
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
    _write_cfg(); _flag(True)
    try:
        p = Post()
        _chan(p).send_text("ضربان", None, stream="heart")
        b = p.bodies[-1]
        assert b["chat_id"] == CHAT, f"به گروه نرفت: {b['chat_id']}"
        assert b["message_thread_id"] == 28, f"به تاپیکِ قلب نرفت: {b}"
    finally:
        _flag(False)


def t_explicit_chat_always_wins():
    """پاسخِ مستقیم به یک پیام هرگز نباید به تاپیکِ دیگری منحرف شود."""
    _write_cfg(); _flag(True)
    try:
        p = Post()
        _chan(p).send_text("جواب", None, chat_id=999, stream="heart")
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


def t_every_stream_key_maps_to_a_real_topic_key():
    """گاردِ ضدِ typo: هر جریان باید به کلیدی اشاره کند که مرکز واقعاً می‌سازد."""
    import sys as _s
    _s.path.insert(0, str(_HERE.parent / "telegram_center"))
    import center  # noqa: WPS433
    for stream, topic_key in ac._STREAM_TOPIC.items():
        assert topic_key in center.LEG_KEYS, \
            f"جریانِ {stream!r} به کلیدِ ناشناخته {topic_key!r} می‌رود"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_stream_routing: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
