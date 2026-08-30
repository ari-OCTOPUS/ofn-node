#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_notify_budget — سقفِ ۵ اعلانِ قطع‌کننده در روز (منشور §۳).

    حسابِ سقف با گذر از نیمه‌شب · معافیتِ بحرانی با شمارشِ جدا ·
    محیطی هرگز بودجه نمی‌خورد · سرریز **واقعاً** در بافرِ digest می‌نشیند
    (فایل assert می‌شود، نه فقط خروجیِ تابع) · جملهٔ اعلام صادق است ·
    صفر ارسال از خودِ ماژول
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import harness

ENV = harness.setup("tg-notify-budget")

_OPS = Path(__file__).resolve().parent.parent
_TC = str(_OPS / "telegram_center")
if _TC not in sys.path:
    sys.path.insert(0, _TC)

import hold_policy as hp  # noqa: E402
import notify_budget as nb  # noqa: E402


def _ts(*a) -> float:
    return datetime(*a).timestamp()


NOW = _ts(2026, 8, 5, 10, 0)                 # چهارشنبه ۱۰:۰۰
LATE = _ts(2026, 8, 5, 23, 50)               # ده دقیقه به نیمه‌شب
AFTER = _ts(2026, 8, 6, 0, 10)               # ده دقیقه بعدِ نیمه‌شب


def _fresh():
    for p in (nb._path(), hp._buffer_path()):
        try:
            p.unlink()
        except OSError:
            pass


# ── سقف ────────────────────────────────────────────────────────────────────
def t_five_interrupts_pass_then_the_sixth_is_refused_with_a_reason():
    _fresh()
    for i in range(5):
        d = nb.allow("card", NOW + i)
        assert d["allow"] is True, (i, d)
        assert d["reason"] == "within-budget", d
        assert d["used"] == i + 1 and d["cap"] == 5, d
        assert d["remaining"] == 4 - i, d
    sixth = nb.allow("card", NOW + 10)
    assert sixth["allow"] is False, sixth
    assert sixth["reason"] == "budget-exhausted", sixth
    assert sixth["used"] == 5 and sixth["remaining"] == 0, sixth
    # ردِ سرریز نباید شمارنده را جلو ببرد (وگرنه گزارش دروغ می‌شود)
    assert nb.summary(NOW + 11)["used"] == 5


def t_every_interrupting_class_shares_the_same_five():
    """سقف روی **کلِ قطع‌کننده‌ها**ست، نه هر طبقه پنج‌تا."""
    _fresh()
    for k in ("card", "reminder", "question", "brief", "lead"):
        assert nb.allow(k, NOW)["allow"] is True, k
    d = nb.allow("reminder", NOW)
    assert d["allow"] is False and d["reason"] == "budget-exhausted", d
    assert nb.summary(NOW)["by_kind"] == {"card": 1, "reminder": 1,
                                          "question": 1, "brief": 1,
                                          "lead": 1}


def t_an_unknown_class_is_treated_as_interrupting():
    """ناشناخته باید بودجه بخورد — دورزدنِ بی‌صدای سقف بدترین حالت است."""
    _fresh()
    d = nb.allow("چیزِ-نو", NOW)
    assert d["class"] == nb.INTERRUPTING and d["used"] == 1, d


def t_the_store_is_durable_across_a_fresh_read():
    """شمارنده در فایل است، نه در حافظهٔ پروسه (ری‌استارت آن را صفر نکند)."""
    _fresh()
    nb.allow("card", NOW)
    nb.allow("alert", NOW)
    raw = json.loads(nb._path().read_text("utf-8"))
    assert raw["used"] == 1 and raw["exempt_used"] == 1, raw
    assert raw["day"] == "2026-08-05", raw


# ── نیمه‌شب ────────────────────────────────────────────────────────────────
def t_midnight_rollover_resets_the_day_and_keeps_history():
    _fresh()
    for i in range(5):
        assert nb.allow("card", LATE + i)["allow"] is True
    nb.allow("alert", LATE + 6, critical=True)
    assert nb.allow("card", LATE + 7)["allow"] is False, "سقفِ دیروز نشکست"

    d = nb.allow("card", AFTER)
    assert d["allow"] is True and d["used"] == 1, d
    s = nb.summary(AFTER)
    assert s["day"] == "2026-08-06" and s["exempt_used"] == 0, s
    # روزِ کهنه گم نشد — گزارشِ هفتگی رویش سوار است
    assert s["week"]["used"] == 6 and s["week"]["days"] == 2, s
    raw = json.loads(nb._path().read_text("utf-8"))
    assert raw["history"]["2026-08-05"]["used"] == 5, raw["history"]


# ── معافیت و محیطی ────────────────────────────────────────────────────────
def t_exempt_classes_are_never_blocked_and_counted_separately():
    _fresh()
    for i in range(5):
        nb.allow("card", NOW + i)                 # سقف پر شد
    for k in ("alert", "cortisol", "heart", "halt", "panic"):
        d = nb.allow(k, NOW + 20)
        assert d["allow"] is True, (k, d)
        assert d["reason"] == "exempt" and d["class"] == nb.EXEMPT, d
    # و مالکِ صریح: هر طبقه‌ای با critical=True معاف است
    d = nb.allow("card", NOW + 21, critical=True)
    assert d["allow"] is True and d["class"] == nb.EXEMPT, d
    s = nb.summary(NOW + 22)
    assert s["used"] == 5, "معاف نباید سقفِ عادی را بخورد"
    assert s["exempt_used"] == 6, s
    assert s["exhausted"] is True and s["remaining"] == 0, s


def t_ambient_streams_never_touch_the_budget():
    _fresh()
    for k in ("ambient", "edit", "digest", "pulse", "health", "receipt"):
        d = nb.allow(k, NOW)
        assert d["allow"] is True and d["reason"] == "ambient-never-counted", d
    s = nb.summary(NOW)
    assert s["used"] == 0 and s["exempt_used"] == 0 and s["by_kind"] == {}, s
    # و بعدش هنوز هر ۵ اعلانِ واقعی سرِ جایشان هستند
    for i in range(5):
        assert nb.allow("card", NOW + i)["allow"] is True


def t_peek_does_not_consume():
    _fresh()
    for _ in range(4):
        assert nb.peek("card", NOW)["allow"] is True
    assert nb.summary(NOW)["used"] == 0, "peek بودجه خورد"
    for i in range(5):
        nb.allow("card", NOW + i)
    assert nb.peek("card", NOW + 9)["allow"] is False


def t_refund_gives_back_a_slot_when_the_send_failed():
    _fresh()
    for i in range(5):
        nb.allow("card", NOW + i)
    assert nb.allow("card", NOW + 6)["allow"] is False
    assert nb.refund("card", NOW + 7) is True
    d = nb.allow("card", NOW + 8)
    assert d["allow"] is True and d["used"] == 5, d


# ── سرریز → دایجست ────────────────────────────────────────────────────────
def t_overflow_really_lands_in_the_hold_policy_buffer_never_dropped():
    """گاردِ اصلی: نه خروجیِ تابع، خودِ **فایلِ بافر** سنجیده می‌شود — و
    همان فایلی که hold_policy می‌گوید، نه مسیرِ بازساخته."""
    _fresh()
    for i in range(5):
        nb.allow("reminder", NOW + i)
    text = "یادآوری: زنگ بزن به بروکرِ سیدنی"
    assert nb.allow("reminder", NOW + 6)["allow"] is False
    assert nb.defer("reminder", text, NOW + 6) is True

    buf = hp._buffer_path()
    assert buf.exists(), f"بافرِ digest ساخته نشد: {buf}"
    rows = [json.loads(x) for x in buf.read_text("utf-8").splitlines() if x.strip()]
    assert len(rows) == 1, rows
    assert rows[0]["stream"] == "notify:reminder", rows[0]
    assert "بروکرِ سیدنی" in rows[0]["head"], rows[0]
    assert nb.summary(NOW + 7)["deferred"] == 1

    # و مصرف‌کنندهٔ واقعی (flush ِ ساعتیِ مرکز) همان ردیف را می‌بیند
    txt = hp.flush_digest(now=NOW + 4000)
    assert txt and "notify:reminder" in txt, txt


def t_defer_is_honest_when_the_buffer_cannot_be_written():
    """ننشستن در بافر باید False برگرداند — صداکننده باید بلند شکست بخورد،
    نه اینکه خیال کند آیتم جا افتاده."""
    _fresh()
    orig = hp._buffer_append
    try:
        hp._buffer_append = lambda *a, **k: False
        assert nb.defer("card", "متنِ مهم", NOW) is False
    finally:
        hp._buffer_append = orig
    assert nb.summary(NOW)["deferred"] == 0
    assert nb.defer("card", "   ", NOW) is False, "متنِ خالی دایجست نمی‌شود"


def t_route_makes_dropping_an_overflow_structurally_impossible():
    """`route` نقطهٔ ورودِ سیم‌کشی است: یک فراخوان، سه مقصدِ صادق."""
    _fresh()
    for i in range(5):
        r = nb.route("card", f"کارتِ {i}", NOW + i)
        assert r["route"] == "send" and r["allow"] is True, r
    over = nb.route("card", "کارتِ ششم", NOW + 6)
    assert over["route"] == "digest" and over["deferred_ok"] is True, over
    assert over["announce"] is True, "اولین سرریز باید اعلام بخواهد"
    rows = [json.loads(x) for x in
            hp._buffer_path().read_text("utf-8").splitlines() if x.strip()]
    assert any("ششم" in r["head"] for r in rows), rows

    # بافر نشد ⇒ **بفرست**، نه سکوت
    orig = hp._buffer_append
    try:
        hp._buffer_append = lambda *a, **k: False
        r2 = nb.route("card", "کارتِ هفتم", NOW + 7)
    finally:
        hp._buffer_append = orig
    assert r2["route"] == "send-anyway" and r2["deferred_ok"] is False, r2


# ── اعلامِ صادقانه ─────────────────────────────────────────────────────────
def t_announce_line_is_honest_in_both_states():
    _fresh()
    line = nb.announce_line(NOW)
    assert "۰ از ۵" in line and "پر شد" not in line, line
    for i in range(5):
        nb.allow("card", NOW + i)
    nb.allow("alert", NOW + 6)
    nb.defer("card", "کارتِ سرریز", NOW + 7)
    full = nb.announce_line(NOW + 8)
    assert "پر شد" in full and "۵ از ۵" in full, full
    assert "۱ موردِ بحرانی" in full, "معاف‌ها باید صادقانه اعلام شوند"
    assert "دایجست" in full and "۱ مورد" in full, full
    assert "دور" in full, "باید بگوید دور ریخته نشده"


def t_announce_fires_once_a_day_and_only_after_a_real_overflow():
    _fresh()
    assert nb.announce_due(NOW) is False, "بی‌سرریز، اعلام نویز است"
    for i in range(5):
        nb.allow("card", NOW + i)
    assert nb.announce_due(NOW + 6) is False
    nb.defer("card", "سرریزِ اول", NOW + 7)
    assert nb.announce_due(NOW + 8) is True
    nb.mark_announced(NOW + 9)
    assert nb.announce_due(NOW + 10) is False, "دو بار در روز اعلام شد"
    nb.defer("card", "سرریزِ دوم", NOW + 11)
    assert nb.announce_due(NOW + 12) is False
    assert nb.announce_due(AFTER) is False, "روزِ نو بدونِ سرریزِ نو"


def t_summary_carries_what_the_weekly_report_needs():
    _fresh()
    nb.allow("card", NOW)
    nb.allow("alert", NOW)
    nb.defer("card", "چیزی", NOW)
    s = nb.summary(NOW)
    for k in ("day", "cap", "used", "remaining", "exempt_used", "deferred",
              "by_kind", "exhausted", "week", "line"):
        assert k in s, (k, s)
    assert s["cap"] == nb.CAP == 5
    assert s["week"]["avg_used"] == 1.0, s["week"]


# ── مرزها ──────────────────────────────────────────────────────────────────
def t_the_module_never_sends_anything():
    import ast
    tree = ast.parse(Path(nb.__file__).read_text("utf-8"))
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (imported & {"requests", "urllib", "socket", "http",
                            "subprocess"}), imported
    called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for bad in ("send", "send_text", "post", "sendMessage", "urlopen"):
        assert bad not in called, f"notify_budget خودش می‌فرستد: {bad}"


def t_there_is_exactly_one_digest_buffer():
    """گاردِ «بافرِ دوم نساز»: مسیرِ بافر فقط از hold_policy پرسیده می‌شود."""
    src = Path(nb.__file__).read_text("utf-8")
    assert "digest-buffer" not in src, "مسیرِ بافر این‌جا بازسازی شده"
    assert "_buffer_path" not in src, "notify_budget مسیرِ بافر را خودش می‌سازد"


def t_state_stays_inside_the_isolated_tree():
    live = str(harness.REAL_VAULT / "_ops" / "state").lower()
    assert not str(nb._path()).lower().startswith(live), nb._path()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items())
              if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_notify_budget: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
