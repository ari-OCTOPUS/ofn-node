#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_reminders — موتورِ یادآوریِ NL (لِین E؛ منشور رأی‌های ۵–۸).

    parser ِ فارسیِ قطعی · store ِ اتمیک · شلیک در beat با ساعتِ تزریقی ·
    پنجرهٔ سکوتِ ۲۳–۷ (معوق، نه حذف؛ بحرانی رد می‌شود) · صفر ارسالِ مستقیم ·
    **سکوتِ تطبیقی**: روی دادهٔ نازک تکان نمی‌خورد، روی دادهٔ پُر حرکت می‌کند،
    کفِ ۵ ساعت را نمی‌شکند، و رأیِ دستیِ مالک همیشه برنده است
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import harness

ENV = harness.setup("tg-reminders")

_OPS = Path(__file__).resolve().parent.parent
_TC = str(_OPS / "telegram_center")
if _TC not in sys.path:
    sys.path.insert(0, _TC)

import reminders as rm  # noqa: E402


def _ts(*a) -> float:
    return datetime(*a).timestamp()


NOW = _ts(2026, 8, 5, 10, 0)          # ۲۰۲۶-۰۸-۰۵ = چهارشنبه، ۱۰:۰۰ صبح


def _fresh():
    for p in (rm._file(), rm._cfg_file()):
        try:
            p.unlink()
        except OSError:
            pass


# ── parser ─────────────────────────────────────────────────────────────────
def t_parse_when_understands_the_owner_language():
    """جدولِ ≥۱۵ حالت — رقمِ فارسی، روزِ هفته با wrap، لنگرِ صبح/شب."""
    assert datetime.fromtimestamp(NOW).weekday() == 2, "پیش‌فرضِ تقویمِ تست"
    cases = [
        ("فردا ساعت ۹ زنگ بزن", _ts(2026, 8, 6, 9, 0)),
        ("امروز ساعت 18 جلسه", _ts(2026, 8, 5, 18, 0)),
        ("پس‌فردا صبح دارو", _ts(2026, 8, 7, 8, 0)),
        ("۵ دقیقه دیگه چای دم کن", NOW + 300),
        ("۲ ساعت دیگه", NOW + 7200),
        ("۳ روز دیگه پیگیری کن", NOW + 3 * 86400),
        ("جمعه ساعت ۱۰ جلسه", _ts(2026, 8, 7, 10, 0)),
        ("چهارشنبه ساعت ۹", _ts(2026, 8, 12, 9, 0)),   # همان روز ⇒ هفتهٔ بعد
        ("شنبه", _ts(2026, 8, 8, 8, 0)),               # روزِ بی‌ساعت = ۰۸:۰۰
        ("یکشنبه ساعت ۷ عصر", _ts(2026, 8, 9, 19, 0)),
        ("ساعت ۹ شب قرص", _ts(2026, 8, 5, 21, 0)),
        ("ساعت ۸ صبح ورزش", _ts(2026, 8, 6, 8, 0)),    # گذشته ⇒ فردا
        ("ساعت ۱۱ صبح", _ts(2026, 8, 5, 11, 0)),
        ("شب قرص بخور", _ts(2026, 8, 5, 21, 0)),       # «شب» ِ تنها = ۲۱:۰۰
        ("صبح", _ts(2026, 8, 6, 8, 0)),                # ۰۸:۰۰ گذشته ⇒ فردا
        ("ساعت ۱۷:۳۰ تماس", _ts(2026, 8, 5, 17, 30)),
        ("ساعت ۱۲ ظهر ناهار", _ts(2026, 8, 5, 12, 0)),
    ]
    for text, want in cases:
        due, _cleaned = rm.parse_when(text, now=NOW)
        assert due is not None, text
        assert abs(due - want) < 1.0, (text, due, want)


def t_parse_when_no_match_returns_none_and_untouched_text():
    for text in ("این یک متنِ ساده است", "لید جدید از سایت آمد", "چطوری؟"):
        due, cleaned = rm.parse_when(text, now=NOW)
        assert due is None and cleaned == text, (text, due, cleaned)


def t_parse_when_strips_the_time_phrase_from_the_text():
    due, cleaned = rm.parse_when("فردا ساعت ۹ زنگ بزن به علی", now=NOW)
    assert due is not None and cleaned == "زنگ بزن به علی", cleaned
    _d, c2 = rm.parse_when("۵ دقیقه دیگه چای دم کن", now=NOW)
    assert c2 == "چای دم کن", c2


# ── store ──────────────────────────────────────────────────────────────────
def t_store_roundtrip_add_fire_done_snooze():
    _fresh()
    it = rm.add("قرصِ شب", due_ts=NOW + 60, now=NOW)
    assert it and it["id"] == "RM-1" and not it["fired"] and not it["done"]
    assert [x["id"] for x in rm.list_open(now=NOW)] == ["RM-1"]

    sent = []
    n = rm.beat(now=NOW + 120,
                send_dm_fn=lambda t, rid: sent.append((t, rid)),
                send_leg_fn=lambda leg, t: None)
    assert n == 1 and sent[0][1] == "RM-1" and "قرص" in sent[0][0], sent
    n2 = rm.beat(now=NOW + 180,
                 send_dm_fn=lambda t, rid: sent.append((t, rid)),
                 send_leg_fn=lambda leg, t: None)
    assert n2 == 0 and len(sent) == 1, "دبل-شلیک از یک یادآوری"

    s = rm.snooze("RM-1", 600, now=NOW + 200)
    assert s and not s["fired"] and s["due"] >= NOW + 799, s
    n3 = rm.beat(now=NOW + 900,
                 send_dm_fn=lambda t, rid: sent.append((t, rid)),
                 send_leg_fn=lambda leg, t: None)
    assert n3 == 1 and len(sent) == 2, "snooze دوباره شلیک نشد"

    d = rm.done("RM-1")
    assert d and d["done"] and rm.list_open() == []


def t_leg_scope_fires_into_the_leg_not_dm():
    """رأی ۶: شخصی در DM، بیزنسی در تاپیکِ همان پا."""
    _fresh()
    rm.add("پیگیری لید سیدنی", due_ts=NOW + 10, scope="leg", leg="lead",
           now=NOW)
    dm, lg = [], []
    rm.beat(now=NOW + 20, send_dm_fn=lambda t, rid: dm.append(t),
            send_leg_fn=lambda leg, t: lg.append((leg, t)))
    assert not dm and lg and lg[0][0] == "lead" and "لید" in lg[0][1], lg


def t_a_failed_send_does_not_mark_fired():
    _fresh()
    rm.add("مهم", due_ts=NOW + 5, now=NOW)

    def _boom(t, rid):
        raise RuntimeError("network")

    n = rm.beat(now=NOW + 10, send_dm_fn=_boom, send_leg_fn=lambda a, b: None)
    assert n == 0
    ok = []
    n2 = rm.beat(now=NOW + 20, send_dm_fn=lambda t, rid: ok.append(rid),
                 send_leg_fn=lambda a, b: None)
    assert n2 == 1 and ok, "ارسالِ ناموفق باید ضربانِ بعد جبران شود"


# ── پنجرهٔ سکوت (رأی ۸ — شروعِ محافظه‌کار ۲۳–۷) ────────────────────────────
def t_quiet_window_defers_normal_but_lets_critical_through():
    _fresh()
    late = _ts(2026, 8, 5, 23, 30)
    rm.add("یادِ معمولی", due_ts=late - 60, now=late - 3600)
    rm.add("بحرانی: سرور خوابید", due_ts=late - 60, now=late - 3600)
    sent = []
    n = rm.beat(now=late, send_dm_fn=lambda t, rid: sent.append(t),
                send_leg_fn=lambda leg, t: None)
    assert n == 1 and len(sent) == 1 and "بحرانی" in sent[0], sent

    deep = _ts(2026, 8, 6, 3, 0)              # وسطِ پنجره هم ساکت
    n_mid = rm.beat(now=deep, send_dm_fn=lambda t, rid: sent.append(t),
                    send_leg_fn=lambda leg, t: None)
    assert n_mid == 0 and len(sent) == 1, "معمولی وسطِ پنجره شلیک شد"

    morning = _ts(2026, 8, 6, 7, 0)           # پایانِ پنجره — معوقه می‌رسد
    n2 = rm.beat(now=morning, send_dm_fn=lambda t, rid: sent.append(t),
                 send_leg_fn=lambda leg, t: None)
    assert n2 == 1 and len(sent) == 2 and "معمولی" in sent[1], \
        "معوقِ شب سرِ ۰۷:۰۰ نرسید (حذف شده؟)"


# ══ سکوتِ تطبیقی (رأی ۸ — «بعد خودتنظیم») ═════════════════════════════════
#
# ⚠️ همهٔ seedها **مهرِ واقعی** می‌سازند (`fired_ts`/`done_ts`) — چون خودِ
# یادگیرنده هم دقیقاً همان مهرها را می‌خوانَد. آیتمِ done ِ بی‌مهر عمداً
# «غیرقابلِ سنجش» است و اگر seed بی‌مهر بسازیم، تست روی مکانیزمِ مرده سبز
# می‌شود (درسِ «خواننده و نویسنده را با هم بسنج»).

DAY = (2026, 8, 3)                     # دوشنبه — روزِ مرجعِ نمونه‌ها


def _seed_hours(spec: dict, *, base_day=DAY) -> None:
    """spec: {ساعت: (تعدادِ فایر، تعدادِ «سریع عمل کرد»)} → storeِ واقعی."""
    d = {"seq": 0, "items": []}
    for h, (n, fast) in sorted(spec.items()):
        for i in range(n):
            fired = _ts(*base_day, h, 0) + i * 60
            d["seq"] += 1
            it = {"id": f"RM-{d['seq']}", "text": f"نمونه {h}-{i}",
                  "due": fired, "scope": "dm", "leg": None,
                  "created": fired - 600, "fired": True, "fired_ts": fired,
                  "done": False}
            if i < fast:                        # جوابِ سریع: ۵ دقیقه
                it["done"] = True
                it["done_ts"] = fired + 300
            d["items"].append(it)
    rm._save(d)


def _seed_send_log(rows_per_hour: dict, *, base_day=DAY) -> None:
    """ردیف‌های DM ِ tg-send-log — تنها شکلی که یادگیرنده می‌پذیرد."""
    p = rm._send_log_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for h, n in sorted(rows_per_hour.items()):
        for i in range(n):
            lines.append(json.dumps({"ts": _ts(*base_day, h, 0) + i * 30,
                                     "chat": 1, "topic": None, "sha": "x",
                                     "chars": 10, "ok": True, "state": "sent",
                                     "bot_role": "outer", "surface": "dm"}))
    p.write_text("\n".join(lines) + "\n", "utf-8")


# دادهٔ پُر: ۲۳ و ۶ بیدار (سریع جواب می‌دهد)، ۰–۵ خواب — ۸ ساعتِ حکم‌دار
RICH = {23: (5, 5), 6: (5, 5), 0: (5, 0), 1: (5, 0), 2: (5, 0), 3: (5, 0),
        4: (5, 0), 5: (5, 0)}
LATER = _ts(2026, 8, 4, 12, 0)         # بعد از روزِ نمونه‌ها


def _clear_send_log():
    try:
        rm._send_log_path().unlink()
    except OSError:
        pass


def t_learner_refuses_to_move_on_thin_data_and_says_so():
    _fresh()
    _clear_send_log()
    _seed_hours({23: (3, 0), 0: (3, 0)})          # ۶ نمونه، خیلی کمتر از ۲۰
    v = rm.learn(LATER)
    assert v["samples"] == 6, v
    assert (v["quiet_from"], v["quiet_to"]) == (23, 7), v
    assert v["changed"] is False and v["confidence"] < rm.CONFIDENCE_BAR, v
    assert "دادهٔ کم" in v["why"], v["why"]
    assert rm.adapt_quiet(LATER)["applied"] is False
    assert rm.load_config()["quiet_from"] == 23, "با دادهٔ نازک پنجره تکان خورد"


def t_learner_moves_on_rich_data_and_writes_the_window():
    """۲۳ و ۶ ثابت می‌کنند مالک بیدار است ⇒ سکوت به ۰–۶ جمع می‌شود."""
    _fresh()
    _clear_send_log()
    _seed_hours(RICH)
    v = rm.learn(LATER)
    assert v["samples"] == 40 and v["judged_hours"] == 8, v
    assert (v["quiet_from"], v["quiet_to"]) == (0, 6), v
    assert v["changed"] is True and v["confidence"] >= rm.CONFIDENCE_BAR, v
    out = rm.adapt_quiet(LATER)
    assert out["applied"] is True, out
    cfg = rm.load_config()
    assert (cfg["quiet_from"], cfg["quiet_to"]) == (0, 6), cfg
    # و پنجرهٔ نو واقعاً رفتارِ beat را عوض می‌کند: ۲۳:۳۰ دیگر ساکت نیست
    rm.add("یادِ معمولی", due_ts=_ts(2026, 8, 4, 23, 0), now=LATER)
    sent = []
    n = rm.beat(now=_ts(2026, 8, 4, 23, 30),
                send_dm_fn=lambda t, rid: sent.append(t),
                send_leg_fn=lambda leg, t: None)
    assert n == 1 and sent, "پنجرهٔ یادگرفته روی شلیک اثر نکرد"
    # شفافیت: مالک باید بتواند بپرسد «چرا؟»
    assert cfg.get("quiet_learned_why") and cfg.get("quiet_learned_conf")


def t_learner_never_produces_a_window_shorter_than_the_floor():
    """۲۳ تا ۳ همه بیدار ⇒ باقی‌ماندهٔ سکوت ۳ ساعت است؛ کف ۵ ساعت است پس
    یادگیرنده **حرکت نمی‌کند** (نه اینکه پنجرهٔ ۳ساعته بسازد)."""
    _fresh()
    _clear_send_log()
    _seed_hours({23: (5, 5), 0: (5, 5), 1: (5, 5), 2: (5, 5), 3: (5, 5)})
    v = rm.learn(LATER)
    assert v["samples"] == 25, v
    assert (v["quiet_from"], v["quiet_to"]) == (23, 7), v
    assert v["changed"] is False, v
    assert "کف" in v["why"], v["why"]
    assert len(rm.quiet_hours(v)) >= rm.QUIET_FLOOR_H, v
    assert rm.adapt_quiet(LATER)["applied"] is False
    assert rm.load_config()["quiet_from"] == 23


def t_a_manual_window_wins_forever_even_against_rich_data():
    _fresh()
    _clear_send_log()
    rm._write_config({rm.MANUAL_KEY: True, "quiet_from": 22, "quiet_to": 6})
    _seed_hours(RICH)
    _seed_send_log({h: 4 for h in range(24)})     # حتی با تأییدِ کاملِ لاگ
    v = rm.learn(LATER)
    assert v["manual"] is True, v
    assert (v["quiet_from"], v["quiet_to"]) == (22, 6), v
    assert v["confidence"] == 0.0 and v["changed"] is False, v
    assert rm.MANUAL_KEY in v["why"], v["why"]
    out = rm.adapt_quiet(LATER)
    assert out["applied"] is False, out
    cfg = rm.load_config()
    assert (cfg["quiet_from"], cfg["quiet_to"]) == (22, 6), cfg
    assert cfg[rm.MANUAL_KEY] is True
    assert "quiet_learned_day" not in cfg, "قفلِ دستی حتی مهرِ روز هم نمی‌خورد"
    # و beat هم آن را نمی‌شکند
    rm.beat(now=LATER, send_dm_fn=lambda t, rid: None,
            send_leg_fn=lambda leg, t: None)
    assert rm.load_config()["quiet_from"] == 22, "beat قفلِ دستی را شکست"


def t_send_log_dm_rows_are_the_corroboration_that_tips_the_bar():
    """گاردِ «tg-send-log واقعاً خوانده می‌شود»: همان دادهٔ یادآوری، یک‌بار
    بدونِ ردیفِ DM (زیرِ میله ⇒ فقط گزارش) و یک‌بار با آن (بالای میله ⇒ اعمال)."""
    _fresh()
    _clear_send_log()
    marginal = {23: (7, 7), 6: (7, 7), 0: (7, 0), 1: (7, 0), 2: (7, 0),
                3: (7, 0)}                        # ۶ ساعتِ حکم‌دار، ۴۲ نمونه
    _seed_hours(marginal)
    v0 = rm.learn(LATER)
    assert v0["dm_rows"] == 0, v0
    assert v0["changed"] is True and v0["confidence"] < rm.CONFIDENCE_BAR, v0
    assert rm.adapt_quiet(LATER)["applied"] is False
    assert rm.load_config()["quiet_from"] == 23

    _seed_send_log({9: 10, 14: 10, 20: 5})
    v1 = rm.learn(LATER)
    assert v1["dm_rows"] == 25, v1
    assert v1["confidence"] > v0["confidence"], (v0, v1)
    assert v1["confidence"] >= rm.CONFIDENCE_BAR, v1
    assert rm.adapt_quiet(LATER)["applied"] is True
    assert (rm.load_config()["quiet_from"],
            rm.load_config()["quiet_to"]) == (0, 6)


def t_send_log_rows_that_are_not_owner_dm_are_ignored():
    """ردیفِ گروه/held/بی‌surface هرگز «رسیدن به مالک» شمرده نمی‌شود."""
    _fresh()
    _clear_send_log()
    p = rm._send_log_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    base = _ts(*DAY, 9, 0)
    p.write_text("\n".join(json.dumps(r) for r in [
        {"ts": base, "surface": "group", "state": "sent", "ok": True},
        {"ts": base + 1, "surface": "dm", "state": "held", "ok": True},
        {"ts": base + 2, "surface": "dm", "state": "sent", "ok": False},
        {"ts": base + 3, "state": "sent", "ok": True},          # بی‌surface
        {"ts": base + 4, "surface": "dm", "state": "sent", "ok": True},
        "خطِ خراب",
    ]) + "\n", "utf-8")
    assert rm._dm_by_hour(LATER)[1] == 1, rm._dm_by_hour(LATER)
    # و ردیفِ کهنه‌تر از پنجره هم شمرده نمی‌شود
    assert rm._dm_by_hour(base + 100 + rm.SEND_LOG_WINDOW_S)[1] == 0


def t_done_stamps_the_time_the_learner_needs():
    """بدونِ `done_ts` کلِ یادگیری حدس است — پس مهر باید واقعاً نوشته شود."""
    _fresh()
    rm.add("قرص", due_ts=NOW + 10, now=NOW)
    rm.beat(now=NOW + 20, send_dm_fn=lambda t, rid: None,
            send_leg_fn=lambda leg, t: None)
    it = rm.done("RM-1", now=NOW + 200)
    assert it["done"] is True and it["done_ts"] == NOW + 200, it
    fresh = rm._find(rm._load(), "RM-1")
    assert fresh["done_ts"] == NOW + 200 and fresh["fired_ts"] == NOW + 20
    n, fast, total = rm._act_samples()
    assert total == 1 and fast[datetime.fromtimestamp(NOW + 20).hour] == 1


def t_legacy_items_without_a_stamp_are_unmeasurable_not_slow():
    """آیتمِ done ِ بی‌مهر (میراثِ قبل از ۰۷-۳۱) نباید به «کندی» تعبیر شود —
    وگرنه یادگیرنده از نبودِ داده، شبِ دروغین می‌سازد."""
    _fresh()
    _clear_send_log()
    d = {"seq": 2, "items": [
        {"id": "RM-1", "text": "کهنه", "due": 0, "scope": "dm", "leg": None,
         "created": 0, "fired": True, "fired_ts": _ts(*DAY, 2, 0),
         "done": True},                                   # بی‌done_ts
        {"id": "RM-2", "text": "نو", "due": 0, "scope": "dm", "leg": None,
         "created": 0, "fired": True, "fired_ts": _ts(*DAY, 2, 30),
         "done": True, "done_ts": _ts(*DAY, 2, 35)},
    ]}
    rm._save(d)
    n, fast, total = rm._act_samples()
    assert total == 1 and n[2] == 1 and fast[2] == 1, (n[2], fast[2], total)


def t_beat_runs_the_learner_once_a_day_by_itself():
    """گاردِ سیم‌کشی: center.py قفل است، پس beat خودش یادگیری را می‌دواند.
    بدونِ این، قابلیت «اعلام‌شده ولی مرده» می‌ماند."""
    _fresh()
    _clear_send_log()
    _seed_hours(RICH)
    rm.beat(now=LATER, send_dm_fn=lambda t, rid: None,
            send_leg_fn=lambda leg, t: None)
    cfg = rm.load_config()
    assert (cfg["quiet_from"], cfg["quiet_to"]) == (0, 6), cfg
    assert cfg["quiet_learned_day"] == "2026-08-04", cfg
    # دومین ضربانِ همان روز دوباره یاد نمی‌گیرد (نشانگرِ روز)
    rm._write_config({"quiet_from": 23, "quiet_to": 7})
    rm.beat(now=LATER + 60, send_dm_fn=lambda t, rid: None,
            send_leg_fn=lambda leg, t: None)
    assert rm.load_config()["quiet_from"] == 23, "یادگیری هر ضربان دوید"
    # و فردا دوباره می‌دود
    rm.beat(now=LATER + 86400, send_dm_fn=lambda t, rid: None,
            send_leg_fn=lambda leg, t: None)
    assert rm.load_config()["quiet_from"] == 0


def t_the_learner_writes_nothing_and_preserves_the_owner_keys():
    _fresh()
    _clear_send_log()
    rm._write_config({"brief_hour": 6.25, "wrap_hour": 22.0, "topics": {"x": 1}})
    _seed_hours(RICH)
    before = rm._cfg_file().read_text("utf-8")
    v = rm.learn(LATER)
    assert v["changed"] is True
    assert rm._cfg_file().read_text("utf-8") == before, "learn نوشت!"
    rm.adapt_quiet(LATER)
    cfg = rm.load_config()
    assert cfg["brief_hour"] == 6.25 and cfg["wrap_hour"] == 22.0, cfg
    assert cfg["topics"] == {"x": 1}, "کلیدِ ناشناختهٔ مالک پاک شد"


def t_the_adaptive_learner_can_be_switched_off_by_the_owner():
    _fresh()
    _clear_send_log()
    _seed_hours(RICH)
    os.environ[rm.ADAPT_FLAG] = "0"
    try:
        assert rm.adapt_enabled() is False
        rm.beat(now=LATER, send_dm_fn=lambda t, rid: None,
                send_leg_fn=lambda leg, t: None)
        assert rm.load_config()["quiet_from"] == 23, "فلگِ خاموش رعایت نشد"
    finally:
        os.environ.pop(rm.ADAPT_FLAG, None)
    assert rm.adapt_enabled() is True, "پیش‌فرض باید روشن باشد"


# ── انضباط ─────────────────────────────────────────────────────────────────
def t_flag_is_default_off():
    os.environ.pop("OCTOPUS_TG_REMINDERS", None)
    assert not rm.enabled()


def t_keyboard_verbs_are_the_documented_contract():
    kb = rm.reminder_keyboard("RM-7")
    data = [b["callback_data"] for row in kb for b in row]
    assert "rm:done:RM-7" in data and "rm:snz:RM-7" in data, data
    assert all(len(x.encode()) <= 64 for x in data)


def t_the_module_has_no_external_effectors():
    import ast
    tree = ast.parse(Path(rm.__file__).read_text("utf-8"))
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (imported & {"requests", "urllib", "socket", "http",
                            "subprocess"}), imported


def t_state_stays_inside_the_isolated_tree():
    live = str(harness.REAL_VAULT / "_ops" / "state").lower()
    assert not str(rm._file()).lower().startswith(live), rm._file()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items())
              if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_reminders: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
