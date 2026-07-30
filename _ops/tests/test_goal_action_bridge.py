#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_goal_action_bridge — پلِ اقدامِ SGC-14: exact prereg → mission → A0 → receipt.

می‌سنجد که پل **از اجزای موجود** ساخته شده (prepare_records ِ unified_control،
planner/executor ِ action_bridge، envelope ِ mission_contract) و هیچ گیتی را
دور نمی‌زند. جهش‌های اجباریِ ممیزی (§۱۷.۲): missing-prereg→execute،
receipt-failure→success، illegal-transition→accepted، متن→مجوز.
"""
import json
import os
import sys
import time
from pathlib import Path

import harness

ENV = harness.setup("goal-action-bridge")

# ⚠️ گاردِ نشت — `harness` امروز `OCTOPUS_STATE_DIR` را pin **نمی‌کند**، و
# `memory_store._default_path()` بدونِ آن به `_ops/state/memory/memory.db` ِ
# **زنده** می‌رود. اولین اجرای اشکال‌زداییِ همین فایل سه ردیف در DB ِ زنده
# نوشت (retract شدند، حذف نه). هر تستی که حافظه را لمس می‌کند باید خودش
# این را pin کند تا آن اشتباه تکرار نشود. ثبت‌شده: VQ-HARNESS-STATEDIR-001.
os.environ["OCTOPUS_STATE_DIR"] = str(Path(ENV["ORG_ROOT"]) / "_ops" / "state")

_OPS = Path(__file__).resolve().parent.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

import goal_action_bridge as gab  # noqa: E402
import prereg  # noqa: E402

NOW = 1_785_400_000.0


def _flag(on: bool):
    if on:
        os.environ[gab.FLAG] = "1"
    else:
        os.environ.pop(gab.FLAG, None)


def _fresh():
    for p in (gab._missions_path(), gab._state_dir() / "action-ledger.jsonl",
              gab._state_dir() / "memory-consolidated.json",
              gab._state_dir() / "verdicts.jsonl",
              Path(str(prereg.PATH)) if hasattr(prereg, "PATH") else None):
        try:
            if p:
                p.unlink()
        except OSError:
            pass
    # فایلِ prereg ِ ایزوله را هم پاک کن (نامش را از خودِ ماژول بگیر)
    try:
        for f in gab._state_dir().glob("prereg.jsonl"):
            f.unlink()
    except OSError:
        pass


def _proposal(kind: str = "recall") -> dict:
    """پیشنهادِ معتبرِ prereg — همان هویتی که register می‌خواهد."""
    if kind == "recall":
        goal = "رخدادِ بازیابی در تصمیم دیده شود"
        mpath = "state/neural/recall-trend.jsonl"
        mkey = "events"
    else:                                    # money → A3 (کارتِ مالک)
        goal = "اولین پولِ مطالبه‌شده"
        mpath = "state/heart/attribution.json"
        mkey = "attribution.claimed"
    return {"goal": goal, "goal_key": "k" + kind, "goal_source": "self",
            "direction": "جهتِ آزمون", "method": "روشِ آزمونِ ۱",
            "method_index": 0, "metric_path": mpath, "metric_key": mkey,
            "baseline": 0.0, "target": {"op": ">", "value": 0.0},
            "candidate_key": "money-claimed" if kind == "money" else "recall-events",
            "deadline_cycles": 2}


def _register(cycle: str, kind: str = "recall") -> dict:
    p = prereg.register(_proposal(kind), cycle=cycle, now=NOW)
    assert p.get("ok"), p
    return p


# ── fail-closed ها ──────────────────────────────────────────────────────────
def t_flag_off_is_a_total_noop():
    _fresh()
    _flag(False)
    r = gab.run_for_cycle("2026-07-30#9", now=NOW)
    assert r == {"schema": gab.SCHEMA, "cycle_id": "2026-07-30#9",
                 "ok": False, "reason": "flag-off"}, r
    assert not gab._missions_path().exists(), "flag-off نوشت!"


def t_missing_prereg_blocks_execution_entirely():
    """جهشِ اجباری #۴: missing prereg → execute باید قرمز شود."""
    _fresh()
    _flag(True)
    rdir = gab._state_dir() / "action_receipts"
    before = len(list(rdir.iterdir())) if rdir.exists() else 0
    try:
        r = gab.run_for_cycle("2026-07-30#8", now=NOW)
        assert r["ok"] is False and r["reason"] == "missing-prereg", r
        assert "mission_id" not in r, "بدونِ پیش‌ثبت mission ساخته شد!"
        assert not gab._missions_path().exists()
        after = len(list(rdir.iterdir())) if rdir.exists() else 0
        assert after == before, "بدونِ پیش‌ثبت receipt ساخته شد!"
    finally:
        _flag(False)


# ── زنجیرهٔ کامل: A0 ِ واقعی با receipt ─────────────────────────────────────
def t_the_full_chain_runs_a_real_a0_and_writes_the_mission_ledger():
    """exact prereg → prepare_records → ALLOW → execute → receipt → دفتر.
    شناسه‌ها در همهٔ حلقه‌ها یکی‌اند: cycle_id در task_id، prereg در ورودی."""
    _fresh()
    _flag(True)
    try:
        cyc = "2026-07-30#1"
        _register(cyc, "recall")
        r = gab.run_for_cycle(cyc, now=NOW)
        assert r.get("classification") == "A0", r
        assert r.get("receipt_status") == "EXECUTED", r
        assert r.get("ok") is True, r
        assert r.get("mission_id") and r.get("trace_id"), r
        rows = [json.loads(x) for x in
                gab._missions_path().read_text("utf-8").splitlines()]
        assert len(rows) == 1, rows
        m = rows[0]
        assert m["status"] == "done" and m["task_id"], m
        assert m["trace_id"] == r["trace_id"], "trace در دفتر با خروجی یکی نیست"
        assert m["output_refs"] and m["output_refs"][0].startswith("receipt:"), m
        # رسیدِ واقعی روی دیسک:
        rec_dir = gab._state_dir() / "action_receipts"
        assert rec_dir.exists() and any(rec_dir.iterdir()), "receipt نوشته نشد"
    finally:
        _flag(False)


def t_a3_candidates_stop_at_the_planner_and_never_execute():
    """§۸.۳: money-claimed فقط کارتِ مالک است — planner اجازهٔ اجرا نمی‌دهد و
    پل صادقانه همان حکم را گزارش می‌کند؛ هیچ receipt ِ EXECUTED ای."""
    _fresh()
    _flag(True)
    try:
        cyc = "2026-07-30#2"
        _register(cyc, "money")
        r = gab.run_for_cycle(cyc, now=NOW)
        assert r["ok"] is False, r
        assert r.get("receipt_status") != "EXECUTED", r
        assert r.get("classification") in ("A3", None), r
    finally:
        _flag(False)


def t_a_non_allow_plan_never_even_reaches_the_executor():
    """⚠️ بعد از **جهشِ سبز** نوشته شد: برداشتنِ گیتِ `decision != ALLOW` هیچ
    تستی را قرمز نکرد، چون خودِ executor هم A3 را BLOCK می‌کند (EXECUTABLE =
    {A0,A1}). یعنی بندِ بالا نمی‌توانست «گیتِ پل» را از «گیتِ executor» جدا
    کند — دو محافظ، یک سنجه.

    این بند مستقیم می‌سنجد که executor **اصلاً صدا زده نشود**: با جاسوسی روی
    خودِ تابع. دفاعِ لایه‌ای خوب است، ولی هر لایه باید سنجهٔ خودش را داشته
    باشد وگرنه بی‌صدا می‌پوسد."""
    _fresh()
    _flag(True)
    sys.path.insert(0, str(_OPS / "action_bridge"))
    import executor as _ex
    calls = []
    real = _ex.execute
    _ex.execute = lambda *a, **k: (calls.append(1), real(*a, **k))[1]
    try:
        cyc = "2026-07-30#5"
        _register(cyc, "money")
        r = gab.run_for_cycle(cyc, now=NOW)
        assert r["ok"] is False, r
        assert not calls, ("executor برای نقشهٔ non-ALLOW صدا زده شد", r)
    finally:
        _ex.execute = real
        _flag(False)


def t_text_is_never_authorization_the_map_is():
    """متنِ روش هرچه باشد، action_type از جدولِ بازبینی‌شده می‌آید — پیشنهادی
    با متنِ «ارسال کن و خرج کن» ولی سنجهٔ recall همچنان A0 ِ مشاهده است."""
    _fresh()
    _flag(True)
    try:
        cyc = "2026-07-30#3"
        prop = _proposal("recall")
        prop["method"] = "برو برای همه ایمیل بفرست و پول خرج کن همین حالا"
        p = prereg.register(prop, cycle=cyc, now=NOW)
        assert p.get("ok"), p
        r = gab.run_for_cycle(cyc, now=NOW)
        assert r.get("classification") == "A0", r
        assert r.get("receipt_status") == "EXECUTED", r
    finally:
        _flag(False)


# ── دفترِ mission: گذار و شکستِ نوشتن ───────────────────────────────────────
def t_an_illegal_transition_is_rejected_not_recorded():
    """جهشِ اجباری #۸: گذارِ غیرقانونی نباید پذیرفته شود."""
    env = {"status": "done"}
    assert gab._transition(env, "running") is False
    assert env["status"] == "done", "گذارِ غیرقانونی state را دست زد"
    env2 = {"status": "queued"}
    assert gab._transition(env2, "running") is True


def t_a_mission_that_fails_validation_is_never_appended():
    _fresh()
    bad = {"mission_id": "x"}                  # فیلدهای لازم غایب
    assert gab._append_mission(bad) is False
    assert not gab._missions_path().exists()


def t_ledger_write_failure_is_never_reported_as_success():
    """جهشِ اجباری #۷ (نسخهٔ دفتر): receipt خوب ولی دفتر ننوشت ⇒ ok=False."""
    _fresh()
    _flag(True)
    real = gab._append_mission
    gab._append_mission = lambda env: False
    try:
        cyc = "2026-07-30#4"
        _register(cyc, "recall")
        r = gab.run_for_cycle(cyc, now=NOW)
        assert r["ok"] is False, r
        assert r["reason"] == "mission-ledger-write-failed", r
        assert r.get("receipt_status") == "EXECUTED", \
            "این سنجه فقط وقتی معناست که receipt واقعاً موفق بوده"
    finally:
        gab._append_mission = real
        _flag(False)


# ── حافظه: فقط از حکمِ مستقل، هرگز authority ────────────────────────────────
def t_consolidation_skips_cleanly_when_the_memory_gate_is_off():
    _fresh()
    (gab._state_dir()).mkdir(parents=True, exist_ok=True)
    (gab._state_dir() / "verdicts.jsonl").write_text(
        json.dumps({"cycle_id": "2026-07-30#1", "goal_key": "k",
                    "verdict": "PASS"}) + "\n", "utf-8")
    os.environ.pop("OCTOPUS_WIRE_MEMORY_GATE", None)
    r = gab.consolidate_new_verdicts(now=NOW)
    assert r["ok"] and r["consolidated"] == 0, r
    assert r.get("reason") == "gate-flag-off", r
    assert not (gab._state_dir() / "memory-consolidated.json").exists(), \
        "skip نباید نشانگر بخورد — وگرنه بعد از روشن‌شدنِ گیت گم می‌شوند"


def t_consolidation_is_outcome_bound_and_idempotent_when_the_gate_is_on():
    _fresh()
    (gab._state_dir()).mkdir(parents=True, exist_ok=True)
    (gab._state_dir() / "verdicts.jsonl").write_text(
        json.dumps({"cycle_id": "2026-07-30#1", "goal_key": "k",
                    "verdict": "PASS"}) + "\n", "utf-8")
    os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "1"
    try:
        r1 = gab.consolidate_new_verdicts(now=NOW)
        assert r1["ok"] and r1["consolidated"] == 1, r1
        r2 = gab.consolidate_new_verdicts(now=NOW + 10)
        assert r2["consolidated"] == 0, ("idempotent نیست", r2)
    finally:
        os.environ.pop("OCTOPUS_WIRE_MEMORY_GATE", None)


# ── exact-row در دفترِ چرخه ─────────────────────────────────────────────────
def t_the_journal_row_now_carries_the_exact_prereg_id():
    """شکافِ کشف‌شدهٔ ممیزی: دفتر به تصادفِ cycle_id تکیه می‌کرد. حالا beat
    شناسهٔ دقیق را پاس می‌دهد و ردیف حملش می‌کند؛ نبودش = رفتارِ قدیم."""
    import test_cycle as tc
    rec = tc.record(goal="هدفِ آزمون", method="روش", cycle="2026-07-30#7",
                    prereg_id="2026-07-30#7:kx", now=NOW)
    assert rec.get("ok") and rec.get("prereg_id") == "2026-07-30#7:kx", rec
    rec2 = tc.record(goal="هدفِ دوم", method="روش", cycle="2026-07-30#6", now=NOW)
    assert rec2.get("ok") and "prereg_id" not in {
        k: v for k, v in rec2.items() if k == "prereg_id" and not v}, rec2


def t_the_seam_in_run_is_flag_off_silent():
    """⚠️ بازنویسی بعد از **جهشِ سبز**: نسخهٔ اول فقط `"_gab.enabled()" in src`
    را می‌سنجید — و آن رشته **دو بار** در فایل هست (یکی برای پل، یکی برای
    consolidation). پس برداشتنِ گیتِ یکی، تست را قرمز نمی‌کرد: گاردِ رشته‌ای
    با حضورِ نمونهٔ دیگر سبز می‌ماند. حالا سنجهٔ **رفتاری** است.

    فلگ خاموش ⇒ `run()` هرگز کلیدِ `action` نمی‌سازد و پل صدا نمی‌خورد."""
    import test_cycle as tc
    _flag(False)
    # ⚠️ پایه باید **زیرِ** سطحِ هدف بنشیند: بدونِ فلگِ خودِ چرخه، `run()` در
    # خطِ اول برمی‌گردد و هرگز به درز نمی‌رسد — آن‌وقت «action ساخته نشد»
    # تصادفی درست است و جهش سبز می‌ماند (همین اتفاق افتاد).
    os.environ["OCTOPUS_WIRE_TEST_CYCLE"] = "1"
    calls = []
    real = gab.run_for_cycle
    gab.run_for_cycle = lambda *a, **k: (calls.append(1), {"ok": False})[1]
    try:
        out = tc.run(goal="هدفِ آزمونِ سیم", method="روش",
                     prereg_id="p:x", now=NOW, force=True)
        assert out.get("journal"), ("run به درز نرسید — پایه بی‌معناست", out)
        assert "action" not in out, ("فلگ خاموش ولی action ساخته شد", out)
        assert not calls, "فلگ خاموش ولی پل صدا زده شد"
    finally:
        gab.run_for_cycle = real
        os.environ.pop("OCTOPUS_WIRE_TEST_CYCLE", None)


def t_the_seam_is_actually_present_in_the_source():
    """جدا از رفتار: سیم باید **وجود** داشته باشد — وگرنه تستِ بالا با یک
    فایلِ بی‌سیم هم سبز است (سبز به‌خاطرِ غیاب)."""
    import ast
    tree = ast.parse((_OPS / "test_cycle.py").read_text("utf-8"))
    called = {getattr(n.func, "attr", None) for n in ast.walk(tree)
              if isinstance(n, ast.Call)
              and getattr(getattr(n.func, "value", None), "id", None) == "_gab"}
    assert "run_for_cycle" in called, "پل از test_cycle صدا نمی‌خورد"
    assert "consolidate_new_verdicts" in called, "consolidation وصل نیست"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_goal_action_bridge: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
