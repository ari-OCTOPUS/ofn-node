#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_goal_generator — مولدِ هدف: هدفِ بی‌ترازو هرگز ساخته نمی‌شود.

گاردهای این فایل همان تهدیدهای فاز ۲ مأموریت‌اند:
  T17 «goal generator که metric ناموجود اختراع کند» → سنجهٔ غایب = کاندیدای رد.
  T21 «repeated method که pivot جا زده شود» → چرخش فقط بعد از FAIL ِ ارزیابِ مستقل.
  «غیاب یعنی روشن، نه خاموش» → read_metric روی فایلِ غایب None می‌دهد، نه صفر —
  صفرِ ساختگی baseline ِ جعلی می‌سازد و «absence → success» را باز می‌کند.
"""
import datetime as dt
import json
import sys

import harness

ENV = harness.setup("goal-generator")     # env قبل از import ِ opslib — ترتیب مهم است

# مولدِ هدف در `_ops/cortex/` است (دامنهٔ مصوبِ L3)؛ harness فقط `_ops`، `budget` و
# `debate` را روی مسیر می‌گذارد، پس cortex را خودمان اضافه می‌کنیم — همان ریشه‌ای
# که harness انتخاب کرده (worktree، نه درختِ زنده).
from pathlib import Path  # noqa: E402
_CORTEX = str(Path(__file__).resolve().parent.parent / "cortex")
if _CORTEX not in sys.path:
    sys.path.insert(0, _CORTEX)

import opslib          # noqa: E402
import goal_generator as gg  # noqa: E402

_TODAY = dt.date.today()


def _at(h, m=0):
    return dt.datetime.combine(_TODAY, dt.time(h, m)).timestamp()


def _write_fitness(claimed=0):
    p = opslib.STATE_DIR / "fitness-latest.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"attribution": {"claimed": claimed, "confirmed": 0}}),
                 "utf-8")


def _write_goals():
    (opslib.OPS / "GOALS-OCTOPUS.md").write_text(
        "# GOALS\n- اولین پولِ مطالبه‌شده: attribution.claimed از صفر دربیاید\n"
        "- حافظهٔ ماندگار: با خاموش/روشن هیچ‌چیز گم نشود\n", "utf-8")


def _fresh():
    for rel in ("fitness-latest.json", "neural/recall-trend.jsonl",
                "telegram/tool-requests.jsonl", "test_cycle/verdicts.jsonl"):
        try:
            (opslib.STATE_DIR / rel).unlink()
        except OSError:
            pass


# ── ایزولاسیون ──────────────────────────────────────────────────────────────
def t_state_is_isolated_from_the_live_tree():
    assert str(ENV["ops"]) in str(opslib.STATE_DIR), opslib.STATE_DIR
    assert r"F:\backup\_ops\state" not in str(opslib.STATE_DIR), opslib.STATE_DIR


# ── T17: سنجهٔ غایب = هدفِ غایب (fail-closed) ──────────────────────────────
def t_no_metric_on_disk_means_no_goal():
    _fresh()
    r = gg.propose(now=_at(9))
    assert r["ok"] is False, r
    assert r["reason"] == "no-valid-goal"
    reasons = {s["key"]: s["reason"] for s in r["skipped"]}
    assert reasons.get("money-claimed") == "metric-not-on-disk", reasons


def t_absent_file_reads_none_not_zero():
    """صفرِ ساختگی از غیاب = baseline ِ جعلی. None تنها جوابِ صادق است."""
    _fresh()
    assert gg.read_metric("fitness-latest.json", "attribution.claimed") is None


def t_money_goal_wins_when_its_metric_exists():
    _fresh()
    _write_fitness(claimed=0)
    _write_goals()
    r = gg.propose(now=_at(9))
    assert r["ok"] is True, r
    assert r["candidate_key"] == "money-claimed"
    assert r["baseline"] == 0
    assert r["target"] == {"op": ">", "value": 0}
    assert r["direction"] != "هیچ‌کدام", r["direction"]   # به خطِ GOALS لینک شد
    assert r["goal_source"] == "self"
    assert isinstance(r["deadline_cycles"], int) and r["deadline_cycles"] >= 1


def t_direction_is_explicit_none_when_goals_file_empty():
    """سکوت ممنوع: بی‌لینک باید صریح «هیچ‌کدام» بگوید (VQ-SELFGOAL-003)."""
    _fresh()
    _write_fitness()
    try:
        (opslib.OPS / "GOALS-OCTOPUS.md").unlink()
    except OSError:
        pass
    r = gg.propose(now=_at(9))
    assert r["ok"] is True
    assert r["direction"] == "هیچ‌کدام", r["direction"]


# ── اعتبار ──────────────────────────────────────────────────────────────────
def t_validate_fails_closed_on_bad_target():
    _fresh()
    _write_fitness()
    good = gg.propose(now=_at(9))
    bad = dict(good)
    bad["target"] = {"op": "!=", "value": "زیاد"}
    v = gg.validate(bad)
    assert v["ok"] is False and "bad:target" in v["errors"], v
    bad2 = dict(good)
    bad2.pop("baseline")
    v2 = gg.validate(bad2)
    assert v2["ok"] is False, v2


def t_bool_metric_becomes_a_ratio():
    _fresh()
    p = opslib.STATE_DIR / "telegram" / "tool-requests.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    rowset = [{"schema": "tool_request.v1", "precise": True},
              {"schema": "tool_request.v1", "precise": False},
              {"schema": "tool_request.v1", "precise": True},
              {"schema": "tool_request.v1", "precise": True}]
    p.write_text("\n".join(json.dumps(r) for r in rowset) + "\n", "utf-8")
    assert gg.read_metric("telegram/tool-requests.jsonl", "precise") == 0.75


# ── T21: چرخشِ روش فقط بعد از FAIL — و مکانیکی، نه ادعایی ───────────────────
def t_first_cycle_holds_method_zero():
    _fresh()
    _write_fitness()
    r = gg.propose(now=_at(9))
    assert r["method_index"] == 0
    assert r["method_note"] == "first", r["method_note"]


def t_pivot_only_after_independent_fail():
    _fresh()
    _write_fitness()
    gkey = gg._goal_key(gg._CANDIDATES[0]["goal"])
    vp = opslib.STATE_DIR / "test_cycle" / "verdicts.jsonl"
    vp.parent.mkdir(parents=True, exist_ok=True)
    # حکمِ PASS → روش نمی‌چرخد
    vp.write_text(json.dumps({"schema": "cycle_verdict.v1", "goal_key": gkey,
                              "verdict": "PASS", "method_index": 0}) + "\n", "utf-8")
    r = gg.propose(now=_at(9))
    assert r["method_index"] == 0 and r["method_note"] == "hold", r
    # حکمِ FAIL → روشِ بعدی، با ردِ صریحِ pivot
    with open(vp, "a", encoding="utf-8") as f:
        f.write(json.dumps({"schema": "cycle_verdict.v1", "goal_key": gkey,
                            "verdict": "FAIL", "method_index": 0}) + "\n")
    r2 = gg.propose(now=_at(9))
    assert r2["method_index"] == 1, r2
    assert "pivot-after-FAIL" in r2["method_note"], r2["method_note"]
    assert r2["method"] != r["method"]          # روش واقعاً فرق کرد، نه فقط شمارنده


def t_goal_key_is_stable_under_whitespace_and_case():
    a = gg._goal_key("  Attribution.Claimed از صفر   دربیاید ")
    b = gg._goal_key("attribution.claimed از صفر دربیاید")
    assert a == b


def _write_recall(events=90):
    p = opslib.STATE_DIR / "neural" / "recall-trend.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"events": events}) + "\n", "utf-8")


def t_one_fail_does_not_exhaust_a_two_cycle_deadline():
    """کنترل منفی: یک FAIL < deadline=2 → money همچنان صدر است."""
    _fresh()
    _write_fitness(claimed=0)
    _write_recall(90)
    _write_goals()
    gkey = gg._goal_key(gg._CANDIDATES[0]["goal"])
    vp = opslib.STATE_DIR / "test_cycle" / "verdicts.jsonl"
    vp.parent.mkdir(parents=True, exist_ok=True)
    vp.write_text(json.dumps({"schema": "cycle_verdict.v1", "goal_key": gkey,
                              "verdict": "FAIL", "method_index": 0}) + "\n", "utf-8")
    r = gg.propose(now=_at(9))
    assert r["ok"] is True, r
    assert r["candidate_key"] == "money-claimed", r
    assert r.get("fail_streak") == 1, r
    assert not any(s.get("reason") == "deadline-exhausted" for s in r.get("skipped") or [])


def t_deadline_exhausted_yields_to_next_candidate_with_a_live_metric():
    """۲۴ FAIL زنده روی money + recall=90 → باید نوبت به recall-events برسد.

    deadline_cycles=2 در کاتالوگ بود ولی propose هرگز آن را نمی‌خواند
    (درز A3، 2026-08-16). دو FAIL کافی است تا کاندیدای گیرکرده کنار برود."""
    _fresh()
    _write_fitness(claimed=0)
    _write_recall(90)
    _write_goals()
    gkey = gg._goal_key(gg._CANDIDATES[0]["goal"])
    vp = opslib.STATE_DIR / "test_cycle" / "verdicts.jsonl"
    vp.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for i in range(2):
        lines.append(json.dumps({"schema": "cycle_verdict.v1", "goal_key": gkey,
                                 "verdict": "FAIL", "method_index": i,
                                 "reason": "no-movement"}))
    vp.write_text("\n".join(lines) + "\n", "utf-8")
    r = gg.propose(now=_at(9))
    assert r["ok"] is True, r
    assert r["candidate_key"] == "recall-events", r
    assert r["baseline"] == 90, r
    reasons = {s["key"]: s["reason"] for s in r.get("skipped") or []}
    assert reasons.get("money-claimed") == "deadline-exhausted", reasons
    assert r.get("fail_streak") == 0, r  # recall هرگز آزموده نشده


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_goal_generator: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
