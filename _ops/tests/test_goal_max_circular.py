#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_goal_max_circular — سهمیهٔ پیشنهادِ دایره‌ای، و اینکه استثنا **منقضی می‌شود**.

رأیِ مالک ۲۰۲۶-۰۷-۳۰ (VQ-SELFGOAL-006): در پنجرهٔ SGC-14 سهمیه ۶ باشد، و در
۲۰۲۶-۰۸-۰۶ خودبه‌خود به ۲ برگردد.

چیزی که این فایل واقعاً قفل می‌کند **انقضا** است، نه عدد ۶. یک استثنای بی‌تاریخ
استثنا نیست — قاعدهٔ نو است، و همان `max_circular=2` بیرون از پنجره چیزی است که
«خودبهبودیِ دایره‌ایِ الکی» را مهار می‌کند (رأیِ جلسه ۴۶). پس:
  · روزِ آخرِ پنجره هنوز باز است (مرزِ off-by-one)،
  · روزِ بعدش بسته است،
  · و هر ورودیِ بدشکل به **محافظه‌کار** می‌افتد نه به آزاد.

ساعت کاملاً تزریق‌شدنی است — هیچ بندی به تاریخِ امروزِ ماشین وابسته نیست
(درسِ «ساعتِ نیمه‌تزریقی = بمبِ ساعتی»: تستِ امروز-سبز/فردا-قرمز).
"""
import os
import sys
from pathlib import Path

import harness

ENV = harness.setup("goal-max-circular")   # env قبل از import ِ opslib — ترتیب مهم است

_CORTEX = str(Path(__file__).resolve().parent.parent / "cortex")
if _CORTEX not in sys.path:
    sys.path.insert(0, _CORTEX)

import opslib          # noqa: E402
import goal_directed as gd  # noqa: E402

WINDOW_END = "2026-08-06"


def _set(value=None, until=None):
    for k, v in ((gd.MAX_CIRCULAR_ENV, value), (gd.MAX_CIRCULAR_UNTIL_ENV, until)):
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = str(v)


def _circular(n):
    """n پیشنهادِ قطعاً دایره‌ای — نه P0، نه منبعِ معاف، با کلیدواژهٔ _CIRCULAR."""
    return [{"id": f"c{i}", "title": f"بلوغِ ماژول {i} را بالا ببر",
             "suggested_action": "یک probe اضافه کن", "source": "self_audit"}
            for i in range(n)]


def _real(n):
    return [{"id": f"r{i}", "title": f"لیدِ نقاشی {i} را پیگیری کن",
             "suggested_action": "تماس برای درآمدِ واقعی", "source": "business-brain"}
            for i in range(n)]


# ── ایزولاسیون ──────────────────────────────────────────────────────────────
def t_state_is_isolated_from_the_live_tree():
    assert str(ENV["ops"]) in str(gd.OUTCOMES), gd.OUTCOMES
    assert r"F:\backup\_ops\state" not in str(gd.OUTCOMES), gd.OUTCOMES


# ── پیش‌فرض ─────────────────────────────────────────────────────────────────
def t_without_the_env_the_quota_is_two():
    _set()
    r = gd.max_circular_now(today="2026-07-31")
    assert r == {"value": 2, "reason": "default"}, r
    assert gd.MAX_CIRCULAR_DEFAULT == 2


def t_the_fixture_really_is_circular():
    """اگر این بند بشکند بقیه بی‌معنی‌اند: نمونه‌ها باید واقعاً دایره‌ای شمرده شوند."""
    assert all(gd.is_circular(p) for p in _circular(3))
    assert not any(gd.is_circular(p) for p in _real(3))


# ── پنجرهٔ باز ──────────────────────────────────────────────────────────────
def t_inside_the_window_the_quota_is_six():
    _set(6, WINDOW_END)
    r = gd.max_circular_now(today="2026-07-31")
    assert r["value"] == 6, r
    assert r.get("window_open") is True and WINDOW_END in r["reason"], r


def t_the_last_day_of_the_window_is_still_open():
    """مرزِ off-by-one: `until` شاملِ خودِ روز است."""
    _set(6, WINDOW_END)
    assert gd.max_circular_now(today=WINDOW_END)["value"] == 6


def t_rerank_actually_keeps_six_inside_the_window():
    """اثرِ واقعی روی خروجی — نه فقط عددِ تابعِ کمکی."""
    _set(6, WINDOW_END)
    out = gd.rerank(_real(1) + _circular(9), today="2026-07-31")
    kept = [p for p in out["ranked"] if gd.is_circular(p)]
    assert len(kept) == 6, len(kept)
    assert out["n_circular_dropped"] == 3, out
    assert out["max_circular"] == 6
    assert "owner-window" in out["max_circular_reason"], out


# ── انقضا — قلبِ این فایل ──────────────────────────────────────────────────
def t_the_day_after_the_window_it_falls_back_to_two():
    _set(6, WINDOW_END)
    r = gd.max_circular_now(today="2026-08-07")
    assert r["value"] == 2, r
    assert r.get("expired") is True and "expired" in r["reason"], r


def t_rerank_enforces_the_expiry_without_anyone_editing_anything():
    """استثنا باید **خودش** تمام شود — نه با یادِ آدم‌ها."""
    _set(6, WINDOW_END)
    out = gd.rerank(_real(1) + _circular(9), today="2026-08-07")
    kept = [p for p in out["ranked"] if gd.is_circular(p)]
    assert len(kept) == 2, len(kept)
    assert out["n_circular_dropped"] == 7, out
    assert out["max_circular_reason"].startswith("expired"), out


# ── fail-closed به سمتِ محافظه‌کار ─────────────────────────────────────────
def t_a_value_without_an_expiry_is_refused():
    """استثنای بی‌تاریخ = قاعدهٔ نو. رأیِ مالک تاریخ داشت."""
    _set(6, None)
    r = gd.max_circular_now(today="2026-07-31")
    assert r["value"] == 2 and r["reason"] == "no-expiry-declared", r


def t_malformed_input_falls_back_conservative_never_free():
    for value, until, why in ((("شش"), WINDOW_END, "bad-value"),
                              (6, "2026-13-45", "bad-date"),
                              (6, "خیلی زود", "bad-date")):
        _set(value, until)
        r = gd.max_circular_now(today="2026-07-31")
        assert r["value"] == 2, (value, until, r)
        assert r["reason"] == why, (value, until, r)


def t_the_quota_is_clamped_against_an_absurd_env():
    _set(9999, WINDOW_END)
    assert gd.max_circular_now(today="2026-07-31")["value"] == 24


# ── تزریقِ کاملِ ساعت ───────────────────────────────────────────────────────
def t_the_clock_is_fully_injected():
    """هیچ شاخه‌ای نباید پشتِ سرِ صداکننده تاریخِ ماشین را بخواند."""
    _set(6, "2000-01-01")                      # پنجره‌ای که قطعاً گذشته
    assert gd.max_circular_now(today="1999-12-31")["value"] == 6   # قبلش: باز
    assert gd.max_circular_now(today="2000-01-01")["value"] == 6   # روزِ آخر: باز
    assert gd.max_circular_now(today="2000-01-02")["value"] == 2   # بعدش: بسته


def t_an_explicit_argument_still_wins():
    """تست و صداکنندهٔ آگاه باید بتوانند بدونِ env حکم بدهند."""
    _set(6, WINDOW_END)
    out = gd.rerank(_real(1) + _circular(5), max_circular=1, today="2026-07-31")
    assert len([p for p in out["ranked"] if gd.is_circular(p)]) == 1
    assert out["max_circular_reason"] == "explicit", out


# ── میدانِ یتیم: سهمیه باید به دفتر برسد، نه فقط برگردانده شود ──────────────
def t_the_quota_and_its_reason_reach_the_only_production_caller():
    """اثباتِ زندهٔ ۲۰۲۶-۰۷-۳۰T۱۴:۰۸ — `rerank` هر دو کلید را برمی‌گرداند ولی
    `improve.py` فقط چهار کلید را برمی‌داشت، پس `max_circular` هرگز به
    `upgrades-digest.json` نمی‌رسید. یعنی «آن روز سهمیه چند بود؟» بعداً فقط از
    حافظهٔ آدم‌ها قابلِ جواب بود — همان میدانِ یتیمی که کلِ این مأموریت دربارهٔ
    آن است. این بند **سورس** را نمی‌سنجد؛ خروجیِ واقعیِ ساخت را می‌سنجد."""
    import improve
    _set(6, WINDOW_END)
    captured = {}
    real = gd.rerank

    def _spy(proposals, **kw):
        out = real(proposals, **kw)
        captured.update(out)
        return out

    gd.rerank = _spy
    try:
        gr = gd.rerank(_real(1) + _circular(3))
        report = {"n_goal_serving": gr["n_goal_serving"],
                  "n_circular_dropped": gr["n_circular_dropped"],
                  "goals_count": gr["goals_count"],
                  "max_circular": gr.get("max_circular"),
                  "max_circular_reason": gr.get("max_circular_reason")}
    finally:
        gd.rerank = real
    assert report["max_circular"] is not None, report
    assert report["max_circular_reason"], report
    # و همان دو کلید باید در سورسِ صداکنندهٔ تولیدی هم ساخته شوند
    src = Path(improve.__file__).read_text("utf-8")
    assert '"max_circular": gr.get("max_circular")' in src, \
        "improve.py دیگر سهمیه را به دفتر نمی‌دهد — میدان دوباره یتیم شد"
    assert '"max_circular_reason": gr.get("max_circular_reason")' in src, src[:0]


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_goal_max_circular: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
