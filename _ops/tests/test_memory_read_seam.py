#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_memory_read_seam — بازیابیِ حافظه پیش از برنامه‌ریزیِ canonical (SGC-14 §۱۰.۴).

یافتهٔ نقشهٔ ۰۷-۳۱: حافظهٔ ارگانیسم عملاً write-only است — تنها مصرفِ
تصمیمی، `lead_outcome_recorder` است و planner ِ چرخهٔ خودهدف هیچ حافظه‌ای
نمی‌خواند. این درز retrieval ِ **ساخت‌یافته و مشورتی** را به پلِ اقدام
اضافه می‌کند:

  · فلگِ `OCTOPUS_WIRE_MEMORY_READ` خاموش (پیش‌فرض) = دقیقاً هیچ.
  · خروجی ساخت‌یافته است: memory_id / trust / created_at / why — نه متنِ خام.
  · حافظه **هرگز authority نیست**: plan/receipt با و بدونِ بازیابی یکسان است
    (قانونِ اساسی: memory مجوز نیست). مصرفِ تصمیمیِ واقعی = A/B ِ آینده
    (§۱۰.۵)؛ این درز فقط «خواندن + ثبتِ مشاهده‌پذیر» را می‌بندد تا سنجه
    مشاهده کند، نه فراخوانی (درسِ selfgoal-loop ِ ۰۷-۳۰).
  · شکستِ retrieval هرگز زنجیره را نمی‌کشد (fail-soft ِ صریح با reason).
"""
import json
import os
import time
from pathlib import Path

import harness

ENV = harness.setup("memory-read-seam")

import goal_action_bridge as gab  # noqa: E402

NOW = 1_785_400_000.0


def _flag(name: str, on: bool):
    if on:
        os.environ[name] = "1"
    else:
        os.environ.pop(name, None)


def _row() -> dict:
    return {"prereg_id": "2026-07-30#1:krecall", "cycle_id": "2026-07-30#1",
            "goal": "رخدادِ بازیابی در تصمیم دیده شود", "goal_key": "krecall",
            "candidate_key": "recall-events",
            "metric_path": "state/neural/recall-trend.jsonl", "metric_key": "events"}


def _seed_memory() -> None:
    """دو ردیفِ episodic ِ مرتبط با هدف، از مسیرِ رسمیِ گیت (نه insert ِ خام)."""
    import sys
    _ops = Path(__file__).resolve().parent.parent
    if str(_ops / "memory") not in sys.path:
        sys.path.insert(0, str(_ops / "memory"))
    import gate as memgate
    import memory_store
    _flag("OCTOPUS_WIRE_MEMORY_GATE", True)
    g = memgate.MemoryGate(memory_store.MemoryStore())
    for i, txt in enumerate((
            "SGC cycle 2026-07-28#1: goal=krecall verdict=FAIL — evidence: state/test_cycle/verdicts.jsonl",
            "SGC cycle 2026-07-29#1: goal=krecall verdict=PASS — evidence: state/test_cycle/verdicts.jsonl")):
        r = g.submit({"namespace": "episodic", "source": "deterministic",
                      "producer": "goal_action_bridge", "agent_id": "goal_action_bridge",
                      "scope": "project", "classification": "internal",
                      "task_id": f"seed-{i}", "content": txt})
        assert r.get("verb") in ("commit", "propose"), r


def t_flag_off_is_exactly_nothing():
    _flag(gab.MEMORY_FLAG, False)
    r = gab._recall_for_goal(_row(), cap=3)
    assert r.get("reason") == "flag-off" and r.get("used") == [], r


def t_flag_on_returns_structured_rows_not_raw_dump():
    _seed_memory()
    _flag(gab.MEMORY_FLAG, True)
    try:
        r = gab._recall_for_goal(_row(), cap=3)
        assert r.get("ok") and r.get("used"), r
        for m in r["used"]:
            assert set(m) <= {"memory_id", "namespace", "trust", "created_at", "why"}, m
            assert m.get("memory_id"), m
            assert m.get("why", "").startswith("fts:"), m
        assert r.get("count") == len(r["used"]), r
    finally:
        _flag(gab.MEMORY_FLAG, False)


def t_cap_is_respected():
    _flag(gab.MEMORY_FLAG, True)
    try:
        r = gab._recall_for_goal(_row(), cap=1)
        assert len(r.get("used") or []) <= 1, r
    finally:
        _flag(gab.MEMORY_FLAG, False)


def t_retrieval_failure_is_fail_soft_with_reason():
    _flag(gab.MEMORY_FLAG, True)
    old = os.environ.get("OCTOPUS_STATE_DIR")
    try:
        # مسیرِ state را به یک «فایل» ببر تا mkdir/اتصالِ store واقعاً بشکند.
        blocker = Path(ENV["ops"]) / "state" / "not-a-dir"
        blocker.write_text("x", "utf-8")
        os.environ["OCTOPUS_STATE_DIR"] = str(blocker / "memory")
        r = gab._recall_for_goal(_row(), cap=3)
        assert r.get("ok") is False and r.get("used") == [], r
        assert r.get("reason"), r
    finally:
        if old is not None:
            os.environ["OCTOPUS_STATE_DIR"] = old
        _flag(gab.MEMORY_FLAG, False)


def t_memory_is_never_authority_over_the_plan():
    """plan ِ pipeline با و بدونِ retrieval بایت‌به‌بایت یکسان تصمیم می‌گیرد."""
    import prereg
    _flag(gab.FLAG, True)
    try:
        prop = {"goal": "رخدادِ بازیابی در تصمیم دیده شود", "goal_key": "krecall",
                "goal_source": "self", "direction": "جهتِ آزمون",
                "method": "روشِ آزمونِ ۱", "method_index": 0,
                "metric_path": "state/neural/recall-trend.jsonl", "metric_key": "events",
                "baseline": 0.0, "target": {"op": ">", "value": 0.0},
                "candidate_key": "recall-events", "deadline_cycles": 2}
        p = prereg.register(prop, cycle="2026-07-29#1", now=NOW)
        assert p.get("ok"), p
        _flag(gab.MEMORY_FLAG, False)
        off = gab.run_for_cycle("2026-07-29#1", now=NOW)
        _flag(gab.MEMORY_FLAG, True)
        on = gab.run_for_cycle("2026-07-29#1", now=NOW)
        for k in ("classification", "receipt_status", "ok"):
            assert off.get(k) == on.get(k), (k, off.get(k), on.get(k))
        assert (on.get("memory") or {}).get("ok") is True, on.get("memory")
        assert (off.get("memory") or {}).get("reason") == "flag-off", off.get("memory")
    finally:
        _flag(gab.FLAG, False)
        _flag(gab.MEMORY_FLAG, False)


CHECKS = [(f.__name__, f) for f in (
    t_flag_off_is_exactly_nothing,
    t_flag_on_returns_structured_rows_not_raw_dump,
    t_cap_is_respected,
    t_retrieval_failure_is_fail_soft_with_reason,
    t_memory_is_never_authority_over_the_plan,
)]

if __name__ == "__main__":
    failed = harness.run(CHECKS)
    total = len(CHECKS)
    print(("✅" if not failed else "❌") + f" test_memory_read_seam: {total - failed}/{total}")
    raise SystemExit(1 if failed else 0)
