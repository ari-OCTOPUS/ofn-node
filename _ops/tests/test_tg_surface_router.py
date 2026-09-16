"""test_tg_surface_router.py — انتخابِ مقصدِ ارسالِ تلگرام برایِ مرکز (دنیای A).

آیتم ۱ و ۳ِ TG-P2: surface_router برایِ هر جریان ``(client, chat_id, topic_id)`` را
از رویِ ``surface-routing.json`` انتخاب می‌کند. flag-off = ارسالِ تک-کلاینتِ outer،
بایت‌به‌بایت مثلِ امروز. flag-on = جریان‌ها به inner/dm منتقل می‌شوند.

قیدهای این‌جا:
  · flag-off → هر جریان = ``(outer, chat_id گروه, topic_id پا)`` = امروز.
  · flag-on + surface=dm → topic_id همیشه None (message_thread_id در DM = ۴۰۰).
  · flag-on + bot=inner → کلاینتِ inner انتخاب می‌شود.
  · هر شکست (فایلِ نبود/خراب، کلاینتِ غایب) → سقوط به outer، نه سکوت.

صفر شبکه: کلاینت‌های fake فقط ``wired()`` را دارند و ``resolve`` فقط انتخاب می‌کند.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("tg-surface-router")

sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import surface_router as sr   # noqa: E402

OWNER = 777
CENTER = -1009999
TOPICS = {"lead": 22, "mining": 33, "system": 28, "studio_pf": 55, "legs-all": 66}


class FakeClient:
    """کلاینتِ fake با owner/center — فقط ``wired()`` و خصیصه‌ها."""

    def __init__(self, name, wired=True, owner=OWNER, center=CENTER):
        self.name = name
        self._wired = wired
        self.owner_chat_id = owner
        self.center_chat_id = center

    def wired(self):
        return self._wired

    def __repr__(self):
        return f"<Fake {self.name} wired={self._wired}>"


def _clients(outer_wired=True, inner_wired=True):
    return {"outer": FakeClient("outer", outer_wired), "inner": FakeClient("inner", inner_wired)}


def _cfg():
    return {"chat_id": CENTER, "topics": dict(TOPICS)}


def _flag(on):
    if on:
        os.environ[sr.FLAG] = "1"
    else:
        os.environ.pop(sr.FLAG, None)


# ─── flag-off: پاریتیِ بایت‌به‌بایت با امروز ──────────────────────────────────
def t_flag_off_uses_current_block_from_file():
    """فلگِ خاموش → از بلوکِ `current` خوانده می‌شود (واقعیتِ امروز در فایل).

    توجه: در فایلِ امروز، approvals-organism در current هست inner (چون تولیدش در
    پروسهٔ organism است). پس این جریان در flag-off هم inner می‌گیرد — این پاریتیِ
    درست با فایل است، نه یک hardcode. جریان‌های دیگر در current outer هستند."""
    _flag(False)
    cl = _clients()
    cfg = _cfg()
    # جریان‌هایی که در current امروز outer هستند
    for stream in ("chat", "doctor-intent", "critical-alerts", "money-pulse", "legs-all"):
        client, chat, topic = sr.resolve(stream, clients=cl, cfg=cfg)
        assert client is cl["outer"], f"{stream}: باید outer باشد نه {client}"
        assert chat == CENTER, f"{stream}: chat_id باید گروه باشد"
    # approvals-organism در current امروز inner است (واقعیتِ فایل)
    client, chat, topic = sr.resolve("approvals-organism", clients=cl, cfg=cfg)
    assert client is cl["inner"], "approvals-organism در current امروزش inner است"


def t_flag_off_topic_for_legs_all_group():
    """flag-off + jaryan-e legs-all (current=group) → topic_id از config."""
    _flag(False)
    cl = _clients()
    client, chat, topic = sr.resolve("legs-all", clients=cl, cfg=_cfg())
    assert topic == TOPICS["legs-all"], f"legs-all باید topic بگیرد: {topic}"


def t_flag_off_intuition_is_silenced_in_current_too():
    """flag-off: intuition در current امروز bot=none است → (None, None, None).
    واقعیتِ فایل: این جریان هنوز در هیچ باتی فعال نیست (تا سخت‌افزار [UNKNOWN])."""
    _flag(False)
    cl = _clients()
    client, chat, topic = sr.resolve("intuition", clients=cl, cfg=_cfg())
    assert client is None and chat is None and topic is None, \
        "intuition در current امروزش none است"


# ─── flag-on: انتقالِ جریان به inner/dm ──────────────────────────────────────
def t_flag_on_inner_streams_use_inner_client():
    """flag-on + target bot=inner → کلاینتِ inner انتخاب می‌شود."""
    _flag(True)
    try:
        cl = _clients()
        # doctor-daily target = inner/dm
        client, chat, topic = sr.resolve("doctor-daily", clients=cl, cfg=_cfg())
        assert client is cl["inner"], f"doctor-daily باید inner باشد: {client}"
    finally:
        _flag(False)


def t_flag_on_dm_surface_drops_topic_id():
    """flag-on + surface=dm → topic_id همیشه None (آیتم ۳: message_thread_id در DM = ۴۰۰)."""
    _flag(True)
    try:
        cl = _clients()
        for stream in ("chat", "doctor-intent", "doctor-daily", "critical-alerts",
                       "money-pulse", "approvals-organism"):
            client, chat, topic = sr.resolve(stream, clients=cl, cfg=_cfg())
            assert topic is None, f"{stream} (target dm) نباید topic بگیرد: {topic}"
            assert chat == OWNER, f"{stream} (target dm) باید owner chat باشد: {chat}"
    finally:
        _flag(False)


def t_flag_on_outer_dm_uses_outer_client():
    """flag-on + bot=outer/dm → کلاینتِ outer ولی مقصدِ DMِ owner."""
    _flag(True)
    try:
        cl = _clients()
        client, chat, topic = sr.resolve("chat", clients=cl, cfg=_cfg())
        assert client is cl["outer"]
        assert chat == OWNER
        assert topic is None
    finally:
        _flag(False)


def t_flag_on_legs_all_stays_group_with_per_leg_topic():
    """flag-on + legs-all (target group/topic=per-leg) → topic از config، نه DM."""
    _flag(True)
    try:
        cl = _clients()
        client, chat, topic = sr.resolve("legs-all", clients=cl, cfg=_cfg())
        assert client is cl["outer"], "legs-all باید outer باشد"
        assert chat == CENTER, "legs-all باید گروه باشد نه DM"
        assert topic == TOPICS["legs-all"], f"legs-all topic: {topic}"
    finally:
        _flag(False)


# ─── سقوطِ fail-soft ─────────────────────────────────────────────────────────
def t_inner_unwired_falls_back_to_outer():
    """flag-on + bot=inner ولی inner وصل نیست → سقوط به outer (نه سکوت)."""
    _flag(True)
    try:
        cl = _clients(inner_wired=False)
        client, chat, topic = sr.resolve("doctor-daily", clients=cl, cfg=_cfg())
        assert client is cl["outer"], "نباید سقوط کند به outer وقتی inner وصل نیست"
        # مقصد همچنان DM است چون block همچنان inner/dm است؛ فقط کلاینت عوض شد
        assert chat == OWNER
    finally:
        _flag(False)


def t_intuition_bot_none_in_current_silenced():
    """flag-off: intuition در current امروز bot=none → (None, None, None) — جریانِ خاموش.

    توجه: در target، intuition به outer/dm منتقل می‌شود (وقتی سخت‌افزار فعال شود)،
    ولی در current (واقعیتِ امروز) هنوز none است. این تست پاریتیِ current را قفل می‌کند."""
    _flag(False)
    cl = _clients()
    client, chat, topic = sr.resolve("intuition", clients=cl, cfg=_cfg())
    assert client is None and chat is None and topic is None


def t_unknown_stream_falls_back_to_outer_not_silence():
    """جریانِ ناشناس → سقوط به outer (نه None) — پیامِ گم‌شده بدتر از در جایِ اشتباه."""
    _flag(True)
    try:
        cl = _clients()
        client, chat, topic = sr.resolve("no-such-stream", clients=cl, cfg=_cfg())
        assert client is cl["outer"], "جریانِ ناشناس نباید سکوت کند"
    finally:
        _flag(False)


# ─── گاردِ DM روی topic (آیتم ۳): تنگ و مستقیم ───────────────────────────────
def t_dm_surface_never_returns_topic_even_with_spec():
    """گاردِ سختِ آیتم ۳: حتی اگر block صریحاً surface=dm و topic بگوید، topic_id=None.

    این مستقیماً روی ``_topic_id_for`` صدا زده می‌شود تا تنگ باشد — در فایلِ امروز
    جریان‌های dm هیچ spec ندارند، پس این سناریو از بیرونِ تابع دیده نمی‌شود. اما اگر
    روزی کسی یک جریانِ group (با topic) را به dm منتقل کند و spec را جا بگذارد، این
    گارد جلویِ یک ۴۰۰ در DM را می‌گیرد. جهش (حذفِ ``if surface != 'group'``) قرمز می‌کند."""
    cfg = {"topics": {"lead": 22}}
    # blockِ dm که عمداً topic spec هم دارد — گارد باید آن را نادیده بگیرد
    assert sr._topic_id_for("lead", {"surface": "dm", "topic": "lead"}, cfg) is None
    assert sr._topic_id_for("lead", {"surface": "none", "topic": "lead"}, cfg) is None
    # ولی group با همان spec → topic برمی‌گرداند (پاریتیِ گروه سالم است)
    assert sr._topic_id_for("lead", {"surface": "group", "topic": "lead"}, cfg) == 22


# ─── گاردِ کارتِ دکمه‌دار (۰۷-۳۱، inner-bot-7 / BLOCK_CARD_EMISSION) ─────────
def t_interactive_never_selects_send_only_inner():
    """resolve(interactive=True) هرگز کلاینتِ inner را برنمی‌گرداند — inner
    هرگز poll نمی‌کند، پس دکمهٔ روی پیامش برای همیشه مرده است. chat/topic
    resolution دست‌نخورده می‌ماند (فقط کلاینت عوض می‌شود). جهش (حذفِ گارد)
    ⇒ client is inner ⇒ قرمز."""
    # flag-off: approvals-organism در current، inner/group است
    _flag(False)
    cl = _clients()
    client, chat, topic = sr.resolve("approvals-organism", clients=cl,
                                     cfg=_cfg(), interactive=True)
    assert client is cl["outer"], f"دکمه‌دار نباید inner بگیرد: {client}"
    assert chat == CENTER, "مقصدِ group باید دست‌نخورده بماند"
    # flag-on: doctor-daily در target، inner/dm است
    _flag(True)
    try:
        client, chat, topic = sr.resolve("doctor-daily", clients=cl,
                                         cfg=_cfg(), interactive=True)
        assert client is cl["outer"], f"دکمه‌دار نباید inner بگیرد: {client}"
        assert chat == OWNER and topic is None, "مقصدِ dm دست‌نخورده"
        # پیش‌فرض (interactive نداده) = رفتارِ دیروز بایت‌به‌بایت: inner
        client2, _, _ = sr.resolve("doctor-daily", clients=cl, cfg=_cfg())
        assert client2 is cl["inner"], "پیش‌فرض نباید عوض شده باشد"
    finally:
        _flag(False)


def t_interactive_inner_alert_is_throttled_not_silent():
    """هشدارِ گارد باید بیاید (سکوت ممنوع) ولی throttled باشد (۱/ساعت/جریان)."""
    import opslib
    _flag(False)
    cl = _clients()
    alerts = []
    orig = opslib.alert
    opslib.alert = lambda msgs: alerts.append(list(msgs))
    sr._last_kb_alert.clear()
    try:
        sr.resolve("approvals-organism", clients=cl, cfg=_cfg(), interactive=True)
        sr.resolve("approvals-organism", clients=cl, cfg=_cfg(), interactive=True)
        assert len(alerts) == 1, f"باید دقیقاً یک هشدارِ throttled باشد: {alerts}"
    finally:
        opslib.alert = orig
        sr._last_kb_alert.clear()


# ─── جهش‌های قرمزکننده ──────────────────────────────────────────────────────
def t_mutation_hardcoding_bot_breaks_parity():
    """جهش: اگر bot همیشه outer شود، flag-on نباید inner برگرداند.
    این تست با کدِ درست سبز است (چون فعلاً inner را برمی‌گرداند) و فقط مستند می‌کند
    که پاریتیِ flag-off واقعاً به خواندنِ `current` وابسته است — نه به hardcode."""
    _flag(True)
    try:
        cl = _clients()
        client, _, _ = sr.resolve("doctor-daily", clients=cl, cfg=_cfg())
        # اگر کسی bot را هاردکدِ outer کند، این برمی‌داردِ inner و تستِ زیر قرمز:
        assert client is cl["inner"]
    finally:
        _flag(False)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_surface_router: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
