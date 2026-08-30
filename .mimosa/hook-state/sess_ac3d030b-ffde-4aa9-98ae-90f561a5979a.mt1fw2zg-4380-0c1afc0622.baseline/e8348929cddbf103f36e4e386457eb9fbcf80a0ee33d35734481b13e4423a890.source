#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_telegram_silence.py — انضباطِ سکوتِ event_bridge (build-spec §4، ۲۰۲۶-۰۷-۲۵).

زمینه: قبل از این فیکس، event_bridge هیچ ضدِتکرارِ محتوایی نداشت. با byte-offset کار
می‌کرد: اگر governor-alerts.md همان خط را ۳۴۸ بار می‌نوشت (مشاهدۀ زندهٔ ۲۰۲۶-۰۷-۲۵)،
۳۴۸ push رخ می‌داد. و سقف فقط ۱۰/ساعت بود (۲۴۰/روز) — نه سقفِ روزانه. مالک صریح
گفت: «رباتی که زیاد پیام بدهد را mute می‌کنم و کل سیستم می‌میرد.»

این فیکس سه چیز اضافه می‌کند و این تست آن‌ها را قفل می‌کند:
  ۱) ضدِ تکرارِ امضای محتوا: همان متن در ۲۴ ساعت فقط یک‌بار push می‌شود.
  ۲) سقفِ روزانهٔ سراسری MAX_PUSH_PER_DAY=6.
  ۳) (دایجستِ ادغام‌شده در center.py جداگانه؛ این تست فقط event_bridge را پوشش می‌دهد.)

آزمایش‌های حیاتیِ build-spec §7:
  - «۵۰ هشدارِ هم‌امضا → دقیقاً ۱ push» (تستِ t1).
  - «رسیدن به سقفِ روزانه = لاگ، نه pushِ بیشتر» (تستِ t2).

$0 و آفلاین. صفر تماسِ واقعیِ Telegram (centerِ جعلی شمارش می‌کند).
"""
import os
import sys
import time as _t
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("tg-silence")
_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402
import event_bridge as eb  # noqa: E402

# event_bridge در import-time، CURSOR = STATE_DIR / "telegram" / "event-bridge-cursor.json"
# را ست کرده. STATE_DIR در sandboxِ harness است. مطمئن شو مسیر داراست.
eb.CURSOR.parent.mkdir(parents=True, exist_ok=True)


class _FakeCenter:
    """centerِ جعلی: شمارشِ pushها بدونِ تماسِ واقعیِ Telegram."""
    def __init__(self):
        self.pushed = []

    def push_alert(self, text: str) -> bool:
        self.pushed.append(text)
        return True


def _fresh():
    """پاک‌کردنِ cursor و state شمارنده برای هر چکِ مستقل."""
    if eb.CURSOR.exists():
        try:
            eb.CURSOR.unlink()
        except OSError:
            pass


# ═══ ۱) ۵۰ هشدارِ هم‌امضا → دقیقاً ۱ push (آزمایشِ حیاتیِ §7) ════════════════
def t1_50_same_signature_one_push():
    """مستقیم قراردادِ _push را شبیه‌سازی می‌کنیم (نه beatِ کامل) تا از خواندنِ
    فایل‌های زندهٔ governor-alerts.md مستقل باشد — این تست باید hermetic باشد."""
    _fresh()
    eb.flag_on = lambda: True   # فلگِ سختِ on
    fc = _FakeCenter()
    text = "⚠️ circuit OPEN for orchestr (fail_count=3) TimeoutError"
    cur = eb._load_cursor()
    now = _t.time()
    pushed_count = 0
    # ۵۰ تلاش با همان متن (امضای یکسان)
    for _ in range(50):
        if not eb._rate_ok(cur, now):
            continue
        if not eb._dedup_ok(cur, now, text):
            continue
        fc.push_alert(eb._scrub(text))
        cur["push_count"] = cur.get("push_count", 0) + 1
        cur["day_push_count"] = cur.get("day_push_count", 0) + 1
        pushed_count += 1
    assert pushed_count == 1, \
        f"۵۰ هشدارِ هم‌امضا باید دقیقاً ۱ push بدهد (got {pushed_count})"
    assert len(fc.pushed) == 1, \
        f"فیک‌سنتر فقط یک push باید دیده باشد (got {len(fc.pushed)})"
    assert "circuit OPEN" in fc.pushed[0], \
        "متنِ push باید محتوای هشدار را داشته باشد"


# ═══ ۲) ۵۰ هشدارِ متفاوت → فقط سقفِ روزانه (۶) ═════════════════════════════
def t2_daily_cap_blocks_after_six():
    _fresh()
    eb.flag_on = lambda: True
    fc = _FakeCenter()
    # مستقیماً حلقهٔ _push را شبیه‌سازی می‌کنیم (beat() فایل‌های زنده را می‌خواند،
    # که در sandbox ممکن است غایب باشند و push صفر بدهند — این تست قراردادِ _push است).
    cur = eb._load_cursor()
    now = _t.time()
    pushed_count = 0
    for i in range(50):
        # هر بار متنِ متفاوت (امضای متفاوت)
        text = f"⚠️ incident.opened #{i}: یک رویدادِ متفاوت {i}"
        # شبیه‌سازیِ _push درونِ beat
        if not text:
            continue
        if not eb._rate_ok(cur, now):
            continue
        if not eb._dedup_ok(cur, now, text):
            continue
        fc.push_alert(eb._scrub(text))
        cur["push_count"] = cur.get("push_count", 0) + 1
        cur["day_push_count"] = cur.get("day_push_count", 0) + 1
        pushed_count += 1
    assert pushed_count == eb.MAX_PUSH_PER_DAY, \
        f"۵۰ هشدارِ متفاوت باید دقیقاً MAX_PUSH_PER_DAY={eb.MAX_PUSH_PER_DAY} push بدهد (got {pushed_count})"
    assert eb.MAX_PUSH_PER_DAY == 6, \
        f"build-spec §4: MAX_PUSH_PER_DAY باید ۶ باشد (got {eb.MAX_PUSH_PER_DAY})"


# ═══ ۳) امضاهای متفاوت در دو پنجرهٔ متفاوت ═════════════════════════════════
def t3_different_signatures_allowed_within_window():
    _fresh()
    eb.flag_on = lambda: True
    fc = _FakeCenter()
    cur = eb._load_cursor()
    now = _t.time()
    # سه متنِ متفاوت، همهٔ مجاز
    for i in range(3):
        text = f"⚠️ رویدادِ متفاوت {i}"
        assert eb._rate_ok(cur, now), f"rate باید ok باشد #{i}"
        assert eb._dedup_ok(cur, now, text), f"امضایِ متفاوت نباید dedup شود #{i}"
        fc.push_alert(text)
        cur["push_count"] = cur.get("push_count", 0) + 1
        cur["day_push_count"] = cur.get("day_push_count", 0) + 1
    assert len(fc.pushed) == 3, \
        f"سه امضای متفاوت باید هر سه push شوند (got {len(fc.pushed)})"


# ═══ ۴) فلگِ خاموش = هیچ push ════════════════════════════════════════════════
def t4_flag_off_no_push():
    _fresh()
    eb.flag_on = lambda: False
    fc = _FakeCenter()
    out = eb.beat(center=fc)
    assert out.get("reason") == "flag-off", \
        f"فلگِ خاموش باید flag-off بدهد (got {out})"
    assert out.get("pushed", 0) == 0, "فلگِ خاموش = صفر push"
    assert len(fc.pushed) == 0, "فلگِ خاموش = صفر push واقعی"


# ═══ ۵) constants درست‌اند ═══════════════════════════════════════════════════
def t5_constants_match_build_spec():
    assert eb.MAX_PUSH_PER_DAY == 6, \
        f"build-spec §4: MAX_PUSH_PER_DAY=6 (got {eb.MAX_PUSH_PER_DAY})"
    assert eb.DEDUP_WINDOW_S == 86400.0, \
        f"build-spec §4: DEDUP_WINDOW_S=86400 (got {eb.DEDUP_WINDOW_S})"
    assert eb.MAX_PUSH_PER_HOUR == 10, \
        f"سقفِ ساعتی حفظ شد: ۱۰ (got {eb.MAX_PUSH_PER_HOUR})"


# ═══ ۶+ (۲۰۲۶-۰۸-۰۷) notif_inbox — فقط دو منبعِ کم‌فوریت reroute می‌شوند ═══════
import notif_inbox as _ni  # noqa: E402


def _reset_ni_store():
    try:
        _ni._STORE_PATH.unlink()
    except OSError:
        pass


def _reset_sources():
    """۴ منبع + cursor را کاملاً پاک کن — هر تستِ notif_inbox باید hermetic
    باشد. _fresh() فقط cursor را پاک می‌کند؛ بدونِ این، محتوایِ باقی‌ماندهٔ
    تستِ قبلی وقتی cursor صفر می‌شود دوباره خوانده می‌شود (دیده‌شده: تستِ ۷ با
    ۲ push به‌جای ۱)."""
    _fresh()
    for p in (eb.ALERTS_MD, eb.EVENTS, eb.C6_JOURNAL):
        try:
            p.unlink()
        except OSError:
            pass
    try:
        eb.STATE.parent.mkdir(parents=True, exist_ok=True)
        eb.STATE.write_text("{}", encoding="utf-8")
    except OSError:
        pass


def t6_notif_inbox_flag_on_routes_critical_alert_line():
    """خطِ critical ِ governor-alerts.md (منبعِ ۱) → صندوق، صفر push مستقیم."""
    _reset_sources()
    _reset_ni_store()
    eb.flag_on = lambda: True
    os.environ[_ni.FLAG] = "1"
    try:
        eb.ALERTS_MD.parent.mkdir(parents=True, exist_ok=True)
        eb.ALERTS_MD.write_text(
            "## 2026-08-07T00:00:00 (metabolism)\n"
            "- ⚠️ circuit OPEN for orchestr (fail_count=3)\n", encoding="utf-8")
        fc = _FakeCenter()
        out = eb.beat(center=fc)
    finally:
        os.environ.pop(_ni.FLAG, None)
    assert fc.pushed == [], f"نباید مستقیم push شود: {fc.pushed}"
    assert out["pushed"] == 1, out
    items = _ni.list_items()
    assert len(items) == 1 and items[0]["category"] == "tech_alert", items


def t7_notif_inbox_flag_on_routes_task_failed():
    """رویدادِ task.failed (منبعِ ۲، کم‌فوریت) → صندوق، صفر push مستقیم."""
    _reset_sources()
    _reset_ni_store()
    eb.flag_on = lambda: True
    os.environ[_ni.FLAG] = "1"
    try:
        eb.EVENTS.parent.mkdir(parents=True, exist_ok=True)
        eb.EVENTS.write_text(
            '{"event_name": "task.failed", "summary": "تستِ شکستِ کار"}\n',
            encoding="utf-8")
        fc = _FakeCenter()
        out = eb.beat(center=fc)
    finally:
        os.environ.pop(_ni.FLAG, None)
    assert fc.pushed == [], f"نباید مستقیم push شود: {fc.pushed}"
    assert out["pushed"] == 1, out
    assert len(_ni.list_items()) == 1


def t8_notif_inbox_flag_on_never_routes_incident_opened():
    """رویدادِ incident.opened (منبعِ ۲، فوری) → همیشه مستقیم push، حتی با فلگِ
    notif_inbox روشن — عمداً هرگز به صندوق نمی‌رود."""
    _reset_sources()
    _reset_ni_store()
    eb.flag_on = lambda: True
    os.environ[_ni.FLAG] = "1"
    try:
        eb.EVENTS.parent.mkdir(parents=True, exist_ok=True)
        eb.EVENTS.write_text(
            '{"event_name": "incident.opened", "summary": "تستِ رخدادِ باز"}\n',
            encoding="utf-8")
        fc = _FakeCenter()
        out = eb.beat(center=fc)
    finally:
        os.environ.pop(_ni.FLAG, None)
    assert len(fc.pushed) == 1, f"incident.opened باید مستقیم push شود: {fc.pushed}"
    assert "incident.opened" in fc.pushed[0], fc.pushed
    assert _ni.list_items() == [], "incident.opened هرگز نباید به صندوق برود"


def t9_notif_inbox_flag_on_never_routes_protective_halt():
    """گذارِ protective-halt (منبعِ ۳) → همیشه مستقیم push، حتی با فلگِ
    notif_inbox روشن — پنل poll ندارد؛ یک halt واقعی نباید دیرک بیفتد."""
    _reset_sources()
    _reset_ni_store()
    eb.flag_on = lambda: True
    os.environ[_ni.FLAG] = "1"
    try:
        eb.STATE.parent.mkdir(parents=True, exist_ok=True)
        eb.STATE.write_text(
            '{"protective_mode": true, "protective_reason": "تستِ محافظتی"}',
            encoding="utf-8")
        fc = _FakeCenter()
        out = eb.beat(center=fc)
    finally:
        os.environ.pop(_ni.FLAG, None)
    assert len(fc.pushed) == 1, f"protective-halt باید مستقیم push شود: {fc.pushed}"
    assert "protective-halt" in fc.pushed[0], fc.pushed
    assert _ni.list_items() == [], "protective-halt هرگز نباید به صندوق برود"


def t10_notif_inbox_flag_off_critical_alert_still_direct():
    """فلگِ notif_inbox خاموش (پیش‌فرض) → حتی خطِ critical هم مستقیم push
    می‌شود، دقیقاً رفتارِ امروز."""
    _reset_sources()
    _reset_ni_store()
    eb.flag_on = lambda: True
    os.environ.pop(_ni.FLAG, None)
    eb.ALERTS_MD.parent.mkdir(parents=True, exist_ok=True)
    eb.ALERTS_MD.write_text(
        "## 2026-08-07T00:00:00 (metabolism)\n"
        "- ⚠️ circuit OPEN for orchestr (fail_count=3)\n", encoding="utf-8")
    fc = _FakeCenter()
    out = eb.beat(center=fc)
    assert len(fc.pushed) == 1, fc.pushed
    assert _ni.list_items() == []


if __name__ == "__main__":
    failed = harness.run([
        ("۱ ۵۰ هم‌امضا → ۱ push", t1_50_same_signature_one_push),
        ("۲ ۵۰ متفاوت → سقفِ روزانه", t2_daily_cap_blocks_after_six),
        ("۳ امضاهای متفاوت مجاز", t3_different_signatures_allowed_within_window),
        ("۴ فلگِ خاموش = صفر push", t4_flag_off_no_push),
        ("۵ constants با build-spec", t5_constants_match_build_spec),
        ("۶ notif_inbox: خطِ critical → صندوق", t6_notif_inbox_flag_on_routes_critical_alert_line),
        ("۷ notif_inbox: task.failed → صندوق", t7_notif_inbox_flag_on_routes_task_failed),
        ("۸ notif_inbox: incident.opened همیشه مستقیم", t8_notif_inbox_flag_on_never_routes_incident_opened),
        ("۹ notif_inbox: protective-halt همیشه مستقیم", t9_notif_inbox_flag_on_never_routes_protective_halt),
        ("۱۰ notif_inbox خاموش → مستقیم مثلِ همیشه", t10_notif_inbox_flag_off_critical_alert_still_direct),
    ])
    sys.exit(1 if failed else 0)
