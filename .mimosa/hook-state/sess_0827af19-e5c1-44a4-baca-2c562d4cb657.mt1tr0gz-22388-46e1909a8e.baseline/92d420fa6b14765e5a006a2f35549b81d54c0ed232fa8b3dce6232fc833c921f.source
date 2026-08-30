"""test_leg_rooms.py — پاها در گروه صدا دارند، ولی فقط وقتی حرفی دارند.

رأیِ مالک ۲۰۲۶-۰۷-۲۸: «گروه و پاها همه‌رو اتصالات رو کدنویسی کن پروژه‌هارو».

چیزی که این فایل قفل می‌کند، بیشترش دربارهٔ **نفرستادن** است:

  · فلگ خاموش → صفر ارسال، بایت‌به‌بایت مثلِ امروز.
  · وضعیتِ عوض‌نشده → سکوت. گزارشِ دوره‌ای همان چیزی است که گروه را به لولهٔ
    سروصدا تبدیل کرد (۶۲٪ از ۱۷۶ ارسالِ دو روز در General افتاده بود).
  · گذشتِ زمان ≠ تغییرِ وضعیت. `age_days` هر روز عوض می‌شود؛ اگر واردِ هش شود
    هر پا هر روز حرف می‌زند و ما اسمش را می‌گذاریم «تغییر». این باگ ۰۷-۲۸ سه
    بار در سه جای مختلف پیدا شد — این‌جا با تستِ صریح بسته می‌شود.
  · ارسالِ شکست‌خورده mark نمی‌شود، پس گم نمی‌شود.
  · پایی که داده ندارد ساکت می‌ماند؛ کارتِ «داده‌ای نیست» خودش سروصداست.
"""
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness  # noqa: E402
ENV = harness.setup("leg-rooms")

sys.path.insert(0, str(_HERE.parent / "legs"))
import os                       # noqa: E402
import leg_room_report as lrr   # noqa: E402
import wiring                   # noqa: E402

T0 = 1_800_000_000.0


def _on():
    os.environ[lrr.FLAG] = "1"


def _off():
    os.environ.pop(lrr.FLAG, None)


def _clean():
    try:
        lrr.STATE.unlink()
    except OSError:
        pass


def _legs(**over):
    base = {
        "lead": {"leg": "lead", "live": True, "signal": "ok",
                 "confirmed_revenue_aud": 120.0, "inbox": [1, 2], "age_days": 0},
        "mining": {"leg": "mining", "live": False, "signal": "idle", "age_days": 3},
    }
    base.update(over)
    return base


class _Ch:
    wired = True

    def __init__(self, fail=False):
        self.sent = []
        self.fail = fail

    def send_text(self, text, kb=None, stream=None):
        self.sent.append((stream, text))
        return not self.fail


# ── فلگ ──────────────────────────────────────────────────────────────────────
def t_a_flag_off_sends_nothing():
    _off()
    _clean()
    ch = _Ch()
    out = wiring.leg_rooms_beat(1, channel=ch, legs=_legs(), now=T0)
    assert out["sent"] == 0 and out.get("flag") == "off", out
    assert ch.sent == []


# ── تغییر، نه زمان ───────────────────────────────────────────────────────────
def t_b_first_run_speaks_then_stays_quiet():
    _on()
    _clean()
    try:
        ch = _Ch()
        first = wiring.leg_rooms_beat(1, channel=ch, legs=_legs(), now=T0)
        assert first["sent"] == 2, first
        assert {s for s, _ in ch.sent} == {"lead", "mining"}, ch.sent
        ch2 = _Ch()
        again = wiring.leg_rooms_beat(2, channel=ch2, legs=_legs(), now=T0 + 60)
        assert again["sent"] == 0 and again["due"] == 0, again
        assert ch2.sent == []
    finally:
        _off()


def t_c_age_days_alone_is_not_a_change():
    """قلبِ ماجرا. اگر `age_days` واردِ هش شود، هر پا هر روز یک‌بار «تغییر»
    می‌کند و گاردِ سکوت صفر اثر دارد — دقیقاً باگی که سه بار در یک روز پیدا شد
    و بعد از حذفِ شمارنده نرخِ حرف‌زدن ۱.۴۰ → ۰.۱۵ در دقیقه شد."""
    _on()
    _clean()
    try:
        wiring.leg_rooms_beat(1, channel=_Ch(), legs=_legs(), now=T0)
        aged = _legs()
        for cell in aged.values():
            cell["age_days"] = int(cell.get("age_days", 0)) + 9
        ch = _Ch()
        out = wiring.leg_rooms_beat(2, channel=ch, legs=aged, now=T0 + 40 * 3600)
        assert out["sent"] == 0, f"فقط زمان گذشته، وضعیت عوض نشده: {out}"
        assert ch.sent == []
    finally:
        _off()


def t_d_a_real_change_does_speak():
    _on()
    _clean()
    try:
        wiring.leg_rooms_beat(1, channel=_Ch(), legs=_legs(), now=T0)
        changed = _legs(mining={"leg": "mining", "live": True,
                                "signal": "hashrate recovered", "age_days": 3})
        ch = _Ch()
        out = wiring.leg_rooms_beat(2, channel=ch, legs=changed,
                                    now=T0 + 7 * 3600)
        assert out["sent"] == 1 and out["legs"] == ["mining"], out
        assert ch.sent[0][0] == "mining"
        assert "hashrate recovered" in ch.sent[0][1]
    finally:
        _off()


def t_e_a_flapping_signal_cannot_flood_the_room():
    """تغییرِ واقعی ولی خیلی زود — کفِ زمانی باید نگهش دارد."""
    _on()
    _clean()
    try:
        wiring.leg_rooms_beat(1, channel=_Ch(), legs=_legs(), now=T0)
        changed = _legs(mining={"leg": "mining", "live": True,
                                "signal": "flap", "age_days": 3})
        ch = _Ch()
        out = wiring.leg_rooms_beat(2, channel=ch, legs=changed,
                                    now=T0 + 60)          # یک دقیقه بعد
        assert out["sent"] == 0, out
        assert ch.sent == []
    finally:
        _off()


# ── شکست ─────────────────────────────────────────────────────────────────────
def t_f_a_failed_send_is_never_marked_as_done():
    """«انجام شد» فلگ نیست، اثر است. اگر ارسال شکست بخورد و ما mark کنیم، آن
    خبر برای همیشه گم می‌شود و هیچ‌کس نمی‌فهمد."""
    _on()
    _clean()
    try:
        bad = _Ch(fail=True)
        out = wiring.leg_rooms_beat(1, channel=bad, legs=_legs(), now=T0)
        assert out["sent"] == 0 and out["due"] == 2, out
        good = _Ch()
        retry = wiring.leg_rooms_beat(2, channel=good, legs=_legs(),
                                      now=T0 + 60)
        assert retry["sent"] == 2, f"خبرِ نرسیده باید دوباره تلاش شود: {retry}"
    finally:
        _off()


def t_g_no_channel_means_nothing_is_lost():
    _on()
    _clean()
    try:
        out = wiring.leg_rooms_beat(1, channel=None, legs=_legs(), now=T0)
        assert out["sent"] == 0 and out.get("no_channel") is True, out
        ch = _Ch()
        later = wiring.leg_rooms_beat(2, channel=ch, legs=_legs(), now=T0 + 60)
        assert later["sent"] == 2, later
    finally:
        _off()


# ── سکوتِ درست ───────────────────────────────────────────────────────────────
def t_h_a_leg_with_no_data_stays_silent():
    _on()
    _clean()
    try:
        ch = _Ch()
        out = wiring.leg_rooms_beat(
            1, channel=ch, legs={"crypto": {"leg": "crypto"}}, now=T0)
        assert out["sent"] == 0, out
        assert ch.sent == []
    finally:
        _off()


def t_i_an_unknown_leg_is_never_broadcast():
    """پایی که در `LABEL` نیست یعنی اتاقی هم ندارد؛ فرستادنش یعنی افتادن در
    General — همان‌جا که ۶۲٪ ارسال‌ها می‌افتاد."""
    _on()
    _clean()
    try:
        ch = _Ch()
        out = wiring.leg_rooms_beat(
            1, channel=ch,
            legs={"totally_new_leg": {"live": True, "signal": "x"}}, now=T0)
        assert out["sent"] == 0, out
        assert ch.sent == []
    finally:
        _off()


# ── مسیر ─────────────────────────────────────────────────────────────────────
def t_j_every_reported_leg_has_a_room_to_go_to():
    """هر پایی که این ماژول می‌شناسد باید در `LEG_TOPIC` مقصد داشته باشد،
    وگرنه کارتش ساخته می‌شود و بی‌صدا در General می‌افتد."""
    sys.path.insert(0, str(_HERE.parent / "telegram_center"))
    import surface_policy as sp
    missing = [k for k in lrr.LABEL if k not in sp.LEG_TOPIC]
    assert not missing, f"پای بی‌اتاق: {missing}"


def t_ja_the_labels_come_from_one_place_only():
    """دو جدول برای یک نام یعنی یکی‌شان همیشه کهنه است.

    ۲۰۲۶-۰۷-۲۸: نام‌های `chat_room` با نامِ واقعیِ اتاق‌های گروه هم‌تراز شد، ولی
    این ماژول جا ماند و کارت‌هایش «⛏ Mining» می‌گفتند در حالی که اتاق «بازوی
    معدن» بود. آزمونِ زندهٔ همان دقیقه نشانش داد. حالا `chat_room` منبعِ
    حقیقت است و این تست جلوی واگرا شدنِ دوباره را می‌گیرد.
    """
    sys.path.insert(0, str(_HERE.parent / "telegram_center"))
    import chat_room as cr
    for key, label in lrr.LABEL.items():
        assert key in cr.LEGS, f"پایی که chat_room نمی‌شناسد: {key}"
        assert label == cr.LEGS[key][0], (key, label, cr.LEGS[key][0])
    assert set(lrr.LABEL) == set(cr.LEGS), (
        f"واگرایی: {set(lrr.LABEL) ^ set(cr.LEGS)}")
    # و fallback باید همان کلیدها را داشته باشد، وگرنه نبودِ ماژول بی‌صدا
    # چند پا را از گزارش حذف می‌کند.
    assert set(lrr._FALLBACK) == set(cr.LEGS), (
        f"fallback کهنه است: {set(lrr._FALLBACK) ^ set(cr.LEGS)}")


def t_jb_the_beat_has_a_production_caller():
    """گاردِ «ساخته شد، وصل نشد».

    قبل از مسلح‌کردنِ فلگ، AST نشان داد `leg_rooms_beat` **۱۶ صداکننده** دارد و
    هر ۱۶ تا در همین فایلِ تست است — یعنی فلگ روشن می‌شد و هیچ اتفاقی نمی‌افتاد.
    همان الگویی که کلِ این جلسه دنبالش بودم، این بار در کدِ خودم.
    """
    import ast
    ops = _HERE.parent
    prod = []
    for p in ops.rglob("*.py"):
        if "__pycache__" in p.parts or "tests" in p.parts:
            continue
        try:
            tree = ast.parse(p.read_text("utf-8", errors="replace"))
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                nm = getattr(n.func, "attr", None) or getattr(n.func, "id", None)
                if nm == "leg_rooms_beat":
                    prod.append(f"{p.name}:{n.lineno}")
    assert prod, "صفر صداکنندهٔ تولیدی — فلگ روشن هم بی‌اثر است"


def t_k_the_state_survives_a_restart():
    """حالت روی دیسک است نه در حافظه: بوتِ تازه نباید همهٔ پاها را با هم شلیک
    کند. همان رگبارِ کادنس که ۰۷-۲۸ در ۱۸ جا فیکس شد."""
    _on()
    _clean()
    try:
        wiring.leg_rooms_beat(1, channel=_Ch(), legs=_legs(), now=T0)
        assert lrr.STATE.exists(), "حالت روی دیسک ننشست"
        import importlib
        importlib.reload(lrr)              # شبیه‌سازیِ پروسهٔ تازه
        assert lrr.due(_legs(), now=T0 + 99 * 3600) == [], "بوتِ تازه دوباره شلیک کرد"
    finally:
        _off()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_leg_rooms: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
