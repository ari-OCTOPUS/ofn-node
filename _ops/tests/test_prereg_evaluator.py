#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_prereg_evaluator — پیش‌ثبتِ fail-closed + ارزیابِ مستقلی که target را جابه‌جا نمی‌کند.

گاردها ↔ تهدیدهای فاز ۲:
  T18 «scorecard که threshold را پس از نتیجه تغییر دهد» → target فقط در prereg،
      و evaluator پیش‌ثبت را بایت‌به‌بایت دست‌نخورده می‌گذارد (ناوردی سنجیده می‌شود).
  T3  «گزارشِ موفقیت بدونِ runtime effect» → حکم فقط از دیسک؛ سنجهٔ ناخوانا
      BLOCKED است نه PASS (absence of evidence ≠ success).
  T12 «fail-open» → شکستِ نوشتنِ پیش‌ثبت = ok=False؛ صداکننده حقِ اجرا ندارد.
"""
import datetime as dt
import json
import sys

import harness

ENV = harness.setup("prereg-eval")        # env قبل از import ِ opslib — ترتیب مهم است

import opslib          # noqa: E402
import prereg          # noqa: E402
import cycle_evaluator as ce  # noqa: E402
import goal_generator as gg   # noqa: E402


def _ts(day: str, h: int):
    return dt.datetime.combine(dt.date.fromisoformat(day), dt.time(h)).timestamp()


def _write_fitness(claimed=0):
    p = opslib.STATE_DIR / "fitness-latest.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"attribution": {"claimed": claimed}}), "utf-8")


def _fresh():
    for rel in ("test_cycle/prereg.jsonl", "test_cycle/verdicts.jsonl",
                "fitness-latest.json"):
        try:
            (opslib.STATE_DIR / rel).unlink()
        except OSError:
            pass


def _proposal(**over):
    p = {"goal": "اولین پولِ مطالبه‌شده", "goal_key": "abc123def456",
         "method": "روشِ شمارهٔ صفر", "method_index": 0,
         "metric_path": "fitness-latest.json", "metric_key": "attribution.claimed",
         "baseline": 0, "target": {"op": ">", "value": 0},
         "deadline_cycles": 2, "direction": "- پولِ مطالبه‌شده", "why": "آزمون"}
    p.update(over)
    return p


# ── ایزولاسیون ──────────────────────────────────────────────────────────────
def t_state_is_isolated_from_the_live_tree():
    assert str(ENV["ops"]) in str(prereg.LEDGER), prereg.LEDGER
    assert r"F:\backup\_ops\state" not in str(prereg.LEDGER), prereg.LEDGER


# ── پیش‌ثبت ─────────────────────────────────────────────────────────────────
def t_register_rejects_missing_target():
    _fresh()
    r = prereg.register(_proposal(target=None), cycle="2026-07-30#0")
    assert r["ok"] is False, r
    assert not prereg.LEDGER.exists() or len(prereg.rows()) == 0


def t_register_rejects_gamed_target_op():
    _fresh()
    r = prereg.register(_proposal(target={"op": "!=", "value": 0}),
                        cycle="2026-07-30#0")
    assert r["ok"] is False and r["reason"] == "bad-target", r


def t_register_writes_once_per_cycle():
    _fresh()
    r1 = prereg.register(_proposal(), cycle="2026-07-30#0")
    r2 = prereg.register(_proposal(goal="هدفِ دیگری"), cycle="2026-07-30#0")
    assert r1["ok"] and r2["ok"]
    assert r2.get("idempotent") is True
    assert len(prereg.rows()) == 1          # دوبار-شلیک = یک پیش‌ثبت
    row = prereg.rows()[0]
    assert row["target"] == {"op": ">", "value": 0}
    assert row["forbidden_actions"], row     # scope/ممنوع صریح ثبت شد
    assert row["allowed_scope"], row


def t_register_write_failure_is_fail_closed():
    _fresh()
    orig = prereg.opslib.append_jsonl

    def _boom(path, rec):
        raise OSError("disk-broken")

    prereg.opslib.append_jsonl = _boom
    try:
        r = prereg.register(_proposal(), cycle="2026-07-30#1")
    finally:
        prereg.opslib.append_jsonl = orig
    assert r["ok"] is False and r["reason"] == "write-failed", r
    assert prereg.for_cycle("2026-07-30#1") is None


# ── حکمِ خالص ───────────────────────────────────────────────────────────────
def t_judge_pass_partial_fail_blocked():
    row = _proposal(target={"op": ">", "value": 2}, baseline=0)
    assert ce.judge(row, 3)["verdict"] == "PASS"
    assert ce.judge(row, 1)["verdict"] == "PARTIAL"      # حرکت بود، target نه
    assert ce.judge(row, 0)["verdict"] == "FAIL"
    assert ce.judge(row, -1)["verdict"] == "FAIL"
    b = ce.judge(row, None)
    assert b["verdict"] == "BLOCKED" and b["verdict"] != "PASS"


def t_judge_blocked_on_corrupt_prereg():
    assert ce.judge({"target": {"op": "!=", "value": "x"}, "baseline": 0},
                    5)["verdict"] == "BLOCKED"


# ── ارزیابِ معوق ────────────────────────────────────────────────────────────
def t_evaluate_waits_for_the_deadline():
    _fresh()
    _write_fitness(claimed=0)
    prereg.register(_proposal(goal_key=gg._goal_key("g1")), cycle="2026-07-30#0")
    # همان روز، همان اسلات → elapsed=0 < deadline=2 → هیچ حکمی
    r = ce.evaluate_pending(now=_ts("2026-07-30", 9))
    assert r["evaluated"] == 0, r
    # یک روز بعد، اسلاتِ صفر → elapsed=2 ≥ 2 → حکم صادر می‌شود
    r2 = ce.evaluate_pending(now=_ts("2026-07-31", 9))
    assert r2["evaluated"] == 1, r2
    assert r2["verdicts"][0]["verdict"] == "FAIL"        # claimed نجنبید
    assert r2["verdicts"][0]["value_now"] == 0


def t_evaluate_is_idempotent():
    _fresh()
    _write_fitness(claimed=0)
    prereg.register(_proposal(goal_key="k-idem"), cycle="2026-07-30#0")
    r1 = ce.evaluate_pending(now=_ts("2026-07-31", 9))
    assert r1["evaluated"] == 1, r1
    r2 = ce.evaluate_pending(now=_ts("2026-07-31", 9))
    assert r2["evaluated"] == 0, r2                      # حکمِ تکراری صادر نمی‌شود
    assert len(ce.rows()) == 1


def t_pass_when_metric_moved_past_target():
    _fresh()
    _write_fitness(claimed=0)
    prereg.register(_proposal(goal_key="k-pass"), cycle="2026-07-30#0")
    _write_fitness(claimed=5)                            # سنجه واقعاً جابه‌جا شد
    r = ce.evaluate_pending(now=_ts("2026-07-31", 9))
    assert r["evaluated"] == 1 and r["verdicts"][0]["verdict"] == "PASS", r
    assert r["verdicts"][0]["value_now"] == 5
    assert r["verdicts"][0]["baseline"] == 0


def t_blocked_when_metric_vanishes():
    """ترازوی گم‌شده حکمِ موفقیت نیست — BLOCKED است (T3)."""
    _fresh()
    _write_fitness(claimed=0)
    prereg.register(_proposal(goal_key="k-gone"), cycle="2026-07-30#0")
    (opslib.STATE_DIR / "fitness-latest.json").unlink()
    r = ce.evaluate_pending(now=_ts("2026-07-31", 9))
    assert r["evaluated"] == 1 and r["verdicts"][0]["verdict"] == "BLOCKED", r


def t_evaluator_never_mutates_the_preregistration():
    """T18: target پس از نتیجه دست‌نخورده — بایت‌به‌بایت."""
    _fresh()
    _write_fitness(claimed=0)
    prereg.register(_proposal(goal_key="k-inv"), cycle="2026-07-30#0")
    before = prereg.LEDGER.read_bytes()
    ce.evaluate_pending(now=_ts("2026-07-31", 9))
    assert prereg.LEDGER.read_bytes() == before


def t_verdict_carries_evidence_reference():
    _fresh()
    _write_fitness(claimed=0)
    prereg.register(_proposal(goal_key="k-evid"), cycle="2026-07-30#0")
    ce.evaluate_pending(now=_ts("2026-07-31", 9))
    rows = ce.rows()
    assert rows, "حکم باید صادر شده باشد"
    for r in rows:
        assert r["evidence"]["metric_path"], r
        assert r["evidence"]["metric_key"], r
        assert r.get("evaluated_at_cycle"), r


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_prereg_evaluator: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
