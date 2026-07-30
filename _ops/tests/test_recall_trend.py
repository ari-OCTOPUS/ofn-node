#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_recall_trend — «به یاد می‌آورد؟» باید یک سری باشد، نه یک عکس.

چرا این گارد لازم است: `recall_reach` سنجهٔ درستی بود که **صفر صداکنندهٔ تولیدی**
داشت. یک عدد روند نیست؛ بی‌سری، «بهتر شدن» قابلِ اثبات نیست. پس دو چیز سنجیده
می‌شود: (۱) نمونه واقعاً روی دیسک می‌نشیند، (۲) حکمِ روند در جهتِ درست می‌چرخد —
`self_ratio` تنها سنجه‌ای است که **کمتر = بهتر** و اگر جهتش برعکس خوانده شود،
سیستمی که فقط خودش را بازتاب می‌دهد «بهتر» نمره می‌گیرد.

مرزِ سختِ این ماژول: هرگز به `consolidation.json` نمی‌نویسد — فقط می‌خواند.
"""
import json
import sys

import harness

ENV = harness.setup("recall-trend")     # env قبل از import — ترتیب مهم است

import opslib             # noqa: E402
import recall_trend as rt  # noqa: E402


def _on():
    import os
    os.environ["OCTOPUS_WIRE_RECALL_TREND"] = "1"


def _off():
    import os
    os.environ["OCTOPUS_WIRE_RECALL_TREND"] = "0"


def _fresh():
    try:
        rt.TREND.unlink()
    except OSError:
        pass
    _on()


def _seed_history(rows):
    """یک `consolidation.json` ِ ساختگی در سندباکس بنویس."""
    import consolidation as c
    c._DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    c._DATA_PATH.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")


def _row(cycle, similar):
    return {"cycle": cycle, "similar_keys": similar}


def t_state_is_isolated_and_consolidation_is_never_written():
    assert str(ENV["ops"]) in str(rt.TREND), rt.TREND
    import consolidation as c
    assert str(ENV["ops"]) in str(c._DATA_PATH), c._DATA_PATH
    # ناوردیِ فقط‌خواندنی: بعد از نمونه‌گیری، فایلِ منبع بایت‌به‌بایت همان است.
    _fresh()
    _seed_history([_row(10, ["cycle-8:x"]), _row(11, ["cycle-9:y"])])
    before = c._DATA_PATH.read_bytes()
    rt.sample(cycle="c1")
    assert c._DATA_PATH.read_bytes() == before, "منبع را نوشت — باید فقط‌خواندنی باشد"


def t_a_sample_lands_on_disk_with_a_timestamp():
    _fresh()
    _seed_history([_row(10, ["cycle-8:x"])])
    out = rt.sample(cycle="c1")
    assert out["ok"] is True, out
    assert out["ts"], "مهرِ زمان نخورد — روند بی‌زمان قابلِ سنجش نیست"
    assert out["rows"] == 1
    assert rt.TREND.exists()
    assert len(rt._rows()) == 1


def t_a_dark_flag_writes_nothing():
    _fresh()
    _seed_history([_row(10, ["cycle-8:x"])])
    _off()
    try:
        assert rt.sample()["reason"] == "flag-off"
    finally:
        _on()
    assert not rt.TREND.exists() or len(rt._rows()) == 0


def t_measure_is_pure_and_writes_nothing():
    _fresh()
    _seed_history([_row(10, ["cycle-8:x"])])
    m = rt.measure()
    assert m.get("events") == 1, m
    assert not rt.TREND.exists(), "measure نباید بنویسد — فقط sample می‌نویسد"


def t_one_sample_is_not_a_trend():
    """یک نمونه حکم نمی‌دهد — و باید صریح بگوید، نه صفر برگرداند.

    صفرِ ساکت شبیهِ «بدتر شد» به‌نظر می‌آید و همان green-lie ِ معکوس است."""
    _fresh()
    _seed_history([_row(10, ["cycle-8:x"])])
    rt.sample()
    t = rt.trend()
    assert t["ok"] is False and t["reason"] == "not-enough-samples", t
    assert t["samples"] == 1


def t_reach_growing_reads_as_better():
    _fresh()
    # نمونهٔ اول: بردِ ۲
    _seed_history([_row(10, ["cycle-8:x"])])
    rt.sample()
    # نمونهٔ دوم: بردِ ۹ — حافظهٔ بلندمدت‌تر
    _seed_history([_row(10, ["cycle-8:x"]), _row(20, ["cycle-11:y"])])
    rt.sample()
    t = rt.trend(window=1)
    assert t["ok"] is True, t
    assert t["verdict"]["reach_median"] == "better", t["deltas"]
    assert t["overall"] in ("better", "mixed"), t["overall"]


def t_self_reflection_is_scored_in_reverse():
    """`self_ratio` بالا رفتن **بدتر** است — سیستمی که همین سیکل را بازتاب
    می‌دهد به یاد نمی‌آورد. اگر جهت برعکس خوانده شود، بازتاب «پیشرفت» نمره
    می‌گیرد و کلِ آزمون فریب می‌خورد."""
    _fresh()
    # اول: بازیابی از گذشتهٔ دور (self_ratio پایین)
    _seed_history([_row(20, ["cycle-5:x"])])
    rt.sample()
    # بعد: بازیابیِ خودِ همان سیکل (self_ratio بالا = بازتاب)
    _seed_history([_row(20, ["cycle-5:x"]), _row(30, ["cycle-30:z"])])
    rt.sample()
    t = rt.trend(window=1)
    d = t["deltas"].get("self_ratio")
    assert d is not None, t["deltas"]
    assert d["last"] > d["first"], d
    assert t["verdict"]["self_ratio"] == "worse", \
        "بازتابِ بیشتر «بهتر» خوانده شد — جهتِ سنجه برعکس است"


def t_overall_is_conservative():
    """«بهتر» فقط وقتی که هیچ سنجه‌ای بدتر نشده باشد."""
    _fresh()
    _seed_history([_row(20, ["cycle-5:x"])])
    rt.sample()
    _seed_history([_row(20, ["cycle-5:x"]), _row(30, ["cycle-30:z"])])
    rt.sample()
    t = rt.trend(window=1)
    assert t["overall"] != "better" or t["worsened"] == 0, t


def t_a_missing_subsystem_is_fail_soft():
    _fresh()
    import consolidation as c
    try:
        c._DATA_PATH.unlink()
    except OSError:
        pass
    assert rt.measure() == {} or rt.measure().get("rows") == 0
    out = rt.sample()
    assert out["ok"] is False or out.get("rows") == 0, out


def t_the_card_is_zero_arg_for_registry_discovery():
    import inspect
    sig = inspect.signature(rt.card)
    assert all(p.default is not inspect.Parameter.empty or
               p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
               for p in sig.parameters.values()), str(sig)
    assert isinstance(getattr(rt, "CARD_TITLE", None), str)
    _fresh()
    _seed_history([_row(10, ["cycle-8:x"])])
    body, kb = rt.card()
    assert "بردِ بازیابی" in body
    assert "کمتر بهتر" in body, "جهتِ self_ratio در کارت توضیح داده نشده"


# ── ضدِ نویز: سری باید سریِ *تغییر* باشد (اندازه‌گیریِ زندهٔ ۲۰۲۶-۰۷-۳۰) ──────
def t_an_unchanged_measurement_writes_no_row():
    """صداکنندهٔ `organism` هر تیک (~۴۳s) نمونه می‌گیرد. بدونِ این گارد، ۷ روز
    ≈ ۱۴٬۰۰۰ ردیفِ بایت‌به‌بایت یکسان می‌شد و «روند» معنایش را از دست می‌داد."""
    _fresh()
    _seed_history([_row(10, ["cycle-8:x"]), _row(11, ["cycle-9:y"])])
    r1 = rt.sample(cycle="c1", now=1000.0)
    assert r1["ok"] is True and r1.get("written") is True, r1
    n1 = len(rt._rows())
    r2 = rt.sample(cycle="c2", now=1043.0)      # یک تیکِ بعد، منبع دست‌نخورده
    assert r2["ok"] is True, r2
    assert r2.get("unchanged") is True and r2.get("written") is False, r2
    assert len(rt._rows()) == n1, "ردیفِ تکراری نوشته شد"


def t_a_changed_measurement_always_writes():
    """dedupe نباید تغییرِ واقعی را ببلعد — وگرنه گارد، سنجه را کور می‌کند."""
    _fresh()
    _seed_history([_row(10, ["cycle-8:x"]), _row(11, ["cycle-9:y"])])
    rt.sample(cycle="c1", now=1000.0)
    n1 = len(rt._rows())
    _seed_history([_row(10, ["cycle-8:x"]), _row(11, ["cycle-9:y"]),
                   _row(12, ["cycle-10:z", "cycle-11:w"])])   # منبع عوض شد
    r = rt.sample(cycle="c2", now=1043.0)
    assert r.get("written") is True, r
    assert len(rt._rows()) == n1 + 1, rt._rows()


def t_a_flat_stretch_still_gets_a_six_hour_pulse():
    """«سنجیده شد و ثابت بود» نباید با «اصلاً سنجیده نشد» یکی شود."""
    _fresh()
    _seed_history([_row(10, ["cycle-8:x"]), _row(11, ["cycle-9:y"])])
    rt.sample(cycle="c1", now=1000.0)
    n1 = len(rt._rows())
    assert rt.sample(cycle="c2", now=1000.0 + 6 * 3600 - 5).get("written") is False
    assert len(rt._rows()) == n1
    r = rt.sample(cycle="c3", now=1000.0 + 6 * 3600 + 5)
    assert r.get("written") is True, r
    assert len(rt._rows()) == n1 + 1


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_recall_trend: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
