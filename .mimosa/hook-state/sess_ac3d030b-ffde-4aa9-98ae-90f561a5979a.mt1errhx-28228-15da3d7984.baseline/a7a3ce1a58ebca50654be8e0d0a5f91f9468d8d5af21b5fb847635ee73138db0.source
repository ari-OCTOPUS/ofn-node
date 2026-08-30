#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_selfknow_unknown_bridge.py — WS-A · «نمی‌دانم» که به جایی می‌رسد (۲۰۲۶-۰۷-۲۸).

چهار شکافِ اندازه‌گیری‌شده که این تست قفلشان می‌کند:
  (a) `_heuristic` پارامترِ `prev` را می‌گرفت و **صفر بار** استفاده می‌کرد، و
      `owner_corrections` را که خودِ `snapshot()` می‌سازد نمی‌خواند. سنجه: بعد از
      تصحیحِ ۲۰۲۶-۰۷-۲۷T۱۳:۲۱، llm:secondary در ۵ از ۵ نسخه چرخید، heuristic در ۰ از ۸.
  (b) `"confidence": 0.4` هاردکد بود — هر ۱۵ رکوردِ heuristic از ۴۷ دقیقاً ۰.۴.
  (c) `_trajectory` دلتای اطمینان را بینِ **دو مغزِ متفاوت** حساب می‌کرد: ۲۸ از ۴۶.
  (d) تنها پلِ عدم‌قطعیت→کنش روی `is_llm` گیت بود، پس شاخه‌ای که «نامعلوم» تولید
      می‌کند هرگز نمی‌توانست کاوش را ماشه بکشد؛ و ریشهٔ نامعلوم به هیچ صفی نمی‌رفت.

هر چهار فلگ پیش‌فرض خاموش‌اند و تستِ اولِ هر بخش ثابت می‌کند خاموش = رفتارِ دیروز.
$0 · sandbox · صفر شبکه (`_ask_llm` همیشه monkeypatch است).
"""
import ast
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("selfknow-unknown-bridge")

_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "doctor"),
           str(_OPS / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402
import self_knowledge as sk  # noqa: E402
import c6_producer as cp  # noqa: E402
import initiative as iv  # noqa: E402

_SB = Path(ENV["ops"]) / "state"
_QUEUE = _SB / "c6" / "hypothesis-queue.jsonl"

_FLAGS = (sk._STEER_FLAG, sk._PROBE_FLAG, sk._UNKNOWN_C6_FLAG, iv.UNKNOWNS_FLAG)

# متنِ تصحیحِ مالک — شکلش عیناً همان چیزی است که اتاقِ آینه روی دیسک می‌نویسد
# (نقلِ داخلِ گیومه + نشانگرِ نفی)، ولی محتوایش ساختگی و بی‌PII است.
_CORR_REJECT_FEAR = "«mining» مهم نیست، من میخوام روی timeouterror تمرکز کنی"
_CORR_REJECT_ERRORS = "نه، «خطای پرتکرار» مهم نیست، من میخوام روی درآمدِ نقاشی تمرکز کنی"


def _clear_flags():
    for f in _FLAGS:
        os.environ.pop(f, None)


def _arm(*flags):
    for f in flags:
        os.environ[f] = "1"


def _snap(*, errors=None, fear=None, alive=True, corrections=None):
    legs = {"ziman": {"live": bool(alive), "money_link": "active" if alive else None}}
    s = {"legs": legs, "stress": {"in_fear": fear or []},
         "recent_errors": errors if errors is not None else {"TimeoutError": 4},
         "innervation": {}, "money": {"musd": 100}, "revenue": 0.0, "wire_on": []}
    if corrections:
        s["owner_corrections"] = list(corrections)
    return s


def _seed_state(*, errors_line=True):
    (_SB / "cortex").mkdir(parents=True, exist_ok=True)
    (_SB / "pulse").mkdir(parents=True, exist_ok=True)
    (_SB / "doctor").mkdir(parents=True, exist_ok=True)
    (_SB / "ORGANISM-STATE.json").write_text(json.dumps(
        {"started": "2026-07-28T08:00:00", "chrono": {"beat": 9001},
         "month": {"musd": 7}, "wiring": {"wire_doctor": True},
         "business_legs": {"ziman": {"live": True, "money_link": "active"}}}), "utf-8")
    (_SB / "cortex" / "stress-latest.json").write_text(
        json.dumps({"level": "🟢", "in_fear": [], "organism_stress": 0.1}), "utf-8")
    if errors_line:
        opslib.ALERTS_MD.parent.mkdir(parents=True, exist_ok=True)
        opslib.ALERTS_MD.write_text("- 09:00 lane crashed: TimeoutError x4\n", "utf-8")


def _write_corrections(*texts):
    (_SB / "doctor").mkdir(parents=True, exist_ok=True)
    (_SB / "doctor" / "owner-corrections.jsonl").write_text(
        "".join(json.dumps({"ts": "2026-07-28T10:0%d:00" % i,
                            "schema": "owner-correction.v1", "text": t},
                           ensure_ascii=False) + "\n"
                for i, t in enumerate(texts)), "utf-8")


def _fresh_doctor():
    """فقط نسخه‌های فهم را پاک کن — تصحیح‌های مالک باید بمانند."""
    for n in ("self-knowledge-latest.json", "self-knowledge.jsonl"):
        p = _SB / "doctor" / n
        if p.exists():
            p.unlink()


def _no_llm():
    sk._ask_llm = lambda p, s, max_tokens=700: (None, "router-down-in-test")


def _fake_llm(payload, tier="think"):
    sk._ask_llm = lambda p, s, max_tokens=700: (payload, tier)


# ══ (a) سوگیری با حرفِ مالک ═══════════════════════════════════════════════════
def t_a0_flag_off_is_yesterday():
    _clear_flags()
    snap = _snap(corrections=[_CORR_REJECT_ERRORS])
    u = sk._heuristic(snap, {"focus": "خطای پرتکرار TimeoutError ×4"})
    assert u["focus"] == "خطای پرتکرار TimeoutError ×4", u["focus"]
    assert u["confidence"] == 0.4, "خاموش باید همان ۰.۴ دیروز را بدهد"
    for k in ("focus_source", "owner_steer", "evidence", "confidence_basis"):
        assert k not in u, f"فلگ خاموش ولی کلیدِ تازهٔ {k} نشت کرد"


def t_a1_rejected_symptom_loses_focus():
    """تصحیحِ مالک نشانه‌ای را رد می‌کند → همان نشانه دیگر focus نیست."""
    _clear_flags(); _arm(sk._STEER_FLAG)
    try:
        snap = _snap(corrections=[_CORR_REJECT_ERRORS])
        before = sk._heuristic(_snap(corrections=None), {})["focus"]
        u = sk._heuristic(snap, {})
        assert before == "خطای پرتکرار TimeoutError ×4", before
        assert u["focus"] != before, "تمرکز با وجودِ تصحیحِ مالک عوض نشد"
        assert u["focus"].startswith("(خواستهٔ مالک)"), u["focus"]
        assert u["focus_source"] == "owner_correction", u.get("focus_source")
        assert "پرتکرار" in (u["owner_steer"]["rejected"]), u["owner_steer"]
    finally:
        _clear_flags()


def t_a2_wanted_symptom_wins_focus():
    """وقتی یکی از نشانه‌های واقعی همانی است که مالک خواسته، همان بالا می‌آید."""
    _clear_flags(); _arm(sk._STEER_FLAG)
    try:
        snap = _snap(fear=["mining"], corrections=[_CORR_REJECT_FEAR])
        plain = sk._heuristic(_snap(fear=["mining"]), {})["focus"]
        u = sk._heuristic(snap, {})
        assert plain.startswith("ترس روی"), plain
        assert u["focus"] == "خطای پرتکرار TimeoutError ×4", u["focus"]
        assert u["focus_source"] == "pathology+owner", u.get("focus_source")
    finally:
        _clear_flags()


def t_a3_prev_is_actually_read():
    """`prev` دیگر پارامترِ تزئینی نیست — هم در AST، هم در رفتار."""
    src = (_OPS / "doctor" / "self_knowledge.py").read_text("utf-8")
    tree = ast.parse(src)
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "_heuristic")
    names = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}
    assert "prev" in names, "_heuristic هنوز prev را در بدنه نمی‌خواند"
    _clear_flags(); _arm(sk._STEER_FLAG)
    try:
        # تمرکزِ دورِ قبل دقیقاً همانی است که مالک رد کرده
        prev = {"focus": "خطای پرتکرار TimeoutError ×4"}
        u = sk._heuristic(_snap(corrections=[_CORR_REJECT_ERRORS]), prev)
        assert u.get("prev_focus_rejected") is True, u.get("prev_focus_rejected")
        assert u["focus"] != prev["focus"], "تمرکزِ ردشدهٔ دورِ قبل دوباره تحویل شد"
    finally:
        _clear_flags()


def t_a4_end_to_end_heuristic_run_obeys_the_owner():
    """معیارِ پذیرشِ ۱: تصحیحِ ساختگی → اجرای شاخهٔ heuristic → تمرکز عوض شد."""
    _clear_flags()
    _orig = sk._ask_llm
    try:
        _seed_state(); _write_corrections(_CORR_REJECT_ERRORS); _no_llm()
        _fresh_doctor()
        off = sk.run(persist=True)
        assert off["source"] == "heuristic", off["source"]
        _arm(sk._STEER_FLAG)
        _fresh_doctor()
        on = sk.run(persist=True)
        assert on["source"] == "heuristic", on["source"]
        assert on["focus"] != off["focus"], (off["focus"], on["focus"])
        assert on["understanding"].get("focus_source") == "owner_correction", on["focus"]
    finally:
        sk._ask_llm = _orig
        _clear_flags()


# ══ (b) عددِ اطمینانِ ساختگی ═══════════════════════════════════════════════════
def t_b1_no_more_hardcoded_confidence():
    _clear_flags(); _arm(sk._STEER_FLAG)
    try:
        u = sk._heuristic(_snap(), {})
        assert u["confidence"] is None, f"هنوز عددِ ساختگی می‌دهد: {u['confidence']}"
        ev = u.get("evidence") or {}
        assert isinstance(ev.get("readable"), int) and isinstance(ev.get("total"), int)
        assert ev["total"] > 0 and 0 <= ev["readable"] <= ev["total"]
        assert 0.0 <= ev["coverage"] <= 1.0, ev
        assert isinstance(ev.get("blind"), list)
    finally:
        _clear_flags()


def t_b2_evidence_counts_what_is_really_readable():
    """شاهد باید **سنجیده** باشد نه ثابت: با یک ورودیِ بیشتر، عدد بالا می‌رود."""
    _clear_flags(); _arm(sk._STEER_FLAG)
    try:
        p = _SB / "cortex" / "innervation-latest.json"
        if p.exists():
            p.unlink()
        low = sk._heuristic(_snap(), {})["evidence"]["readable"]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"coverage_pct": 50}), "utf-8")
        high = sk._heuristic(_snap(), {})["evidence"]["readable"]
        assert high == low + 1, (low, high)
        assert "innervation" not in sk._heuristic(_snap(), {})["evidence"]["blind"]
    finally:
        _clear_flags()


# ══ (c) مقایسهٔ بین دو مغز ═════════════════════════════════════════════════════
def t_c0_flag_off_trajectory_shape_unchanged():
    _clear_flags()
    tj = sk._trajectory({"focus": "legs", "source": "llm:secondary",
                         "understanding": {"confidence": 0.85}},
                        {"focus": "legs", "confidence": 0.4}, backend="heuristic")
    assert set(tj) == {"focus_stable", "prev_focus", "confidence_delta", "converging"}
    assert tj["confidence_delta"] == -0.45, tj


def t_c1_cross_backend_is_refused():
    _clear_flags(); _arm(sk._STEER_FLAG)
    try:
        tj = sk._trajectory({"focus": "legs", "source": "llm:secondary",
                             "understanding": {"confidence": 0.85}},
                            {"focus": "legs", "confidence": 0.4}, backend="heuristic")
        assert tj["comparable"] is False, tj
        assert tj["confidence_delta"] is None, "دلتای بین دو مغز هنوز تولید می‌شود"
        assert tj["incomparable_reason"] == "backend-changed", tj
        assert tj["converging"] is None, tj
        assert tj["focus_stable"] is True, "پایداریِ تمرکز backend-independent است"
    finally:
        _clear_flags()


def t_c2_same_backend_still_compares():
    _clear_flags(); _arm(sk._STEER_FLAG)
    try:
        tj = sk._trajectory({"focus": "legs", "source": "llm:local",
                             "understanding": {"confidence": 0.5}},
                            {"focus": "legs", "confidence": 0.7}, backend="llm:local")
        assert tj["comparable"] is True and tj["confidence_delta"] == 0.2, tj
        assert tj["converging"] is True, tj
    finally:
        _clear_flags()


def t_c3_unknown_confidence_reports_unknown():
    _clear_flags(); _arm(sk._STEER_FLAG)
    try:
        tj = sk._trajectory({"focus": "legs", "source": "heuristic",
                             "understanding": {"confidence": None}},
                            {"focus": "legs", "confidence": None}, backend="heuristic")
        assert tj["comparable"] is False and tj["confidence_delta"] is None, tj
        assert tj["incomparable_reason"] == "unknown-confidence", tj
    finally:
        _clear_flags()


def t_c4_legacy_guard_stays_green_under_the_flag():
    """گاردِ pin‌شدهٔ موجود (test_doctor_selfknowledge:t_trajectory_converging) نباید
    با روشن‌شدنِ فلگ قرمز شود — backendِ نامعلوم «نمی‌دانم» است، نه «متفاوت»."""
    _clear_flags(); _arm(sk._STEER_FLAG)
    try:
        tj = sk._trajectory({"focus": "legs", "understanding": {"confidence": 0.5}},
                            {"focus": "legs", "confidence": 0.7})
        assert tj["focus_stable"] is True and tj["confidence_delta"] == 0.2, tj
        assert tj["converging"] is True and tj["comparable"] is None, tj
    finally:
        _clear_flags()


# ══ (d1) شاخهٔ heuristic هم می‌تواند کاوش را ماشه بکشد ═════════════════════════
def t_d1_probe_gate_off_is_yesterday():
    _clear_flags()
    _orig = sk._ask_llm
    try:
        _seed_state(); _fresh_doctor(); _no_llm()
        r = sk.run(persist=True)
        assert r["source"] == "heuristic" and r["deep_dive_ran"] is False, r["deep_dive_ran"]
        assert r["deep_dive"] == {}, r["deep_dive"]
    finally:
        sk._ask_llm = _orig
        _clear_flags()


def t_d2_heuristic_can_now_trigger_the_probe():
    _clear_flags(); _arm(sk._PROBE_FLAG, sk._STEER_FLAG)
    _orig = sk._ask_llm
    try:
        _seed_state(); _fresh_doctor()
        calls = {"n": 0}

        def _ask(prompt, system, max_tokens=700):
            calls["n"] += 1
            if calls["n"] == 1:
                return None, "router-down"        # مرحلهٔ ۱ → heuristic
            return '{"topic":"t","cause_chain":["a","b"],"smallest_fix":"x"}', "think"

        sk._ask_llm = _ask
        r = sk.run(persist=True)
        assert r["source"] == "heuristic", r["source"]
        assert r["deep_dive_ran"] is True, "شاخهٔ heuristic هنوز نمی‌تواند کاوش کند"
        assert r["deep_dive"].get("cause_chain") == ["a", "b"], r["deep_dive"]
        assert calls["n"] == 2, calls
    finally:
        sk._ask_llm = _orig
        _clear_flags()


def t_d3_unknown_confidence_is_a_reason_to_probe():
    _clear_flags()
    prev = {"focus": "legs", "deep_dive": {"topic": "legs"}}
    u = {"focus": "legs", "confidence": None, "pathology": []}
    assert sk._should_deep_dive(u, prev, "legs") is False, "خاموش نباید رفتار عوض کند"
    _arm(sk._PROBE_FLAG)
    try:
        assert sk._should_deep_dive(u, prev, "legs") is True
    finally:
        _clear_flags()


# ══ (d2) ریشهٔ نامعلوم → ردیفِ صفِ C6 ══════════════════════════════════════════
_UNKNOWN_REC = {
    "version": 42, "source": "heuristic", "focus": "خطای پرتکرار TimeoutError ×4",
    "understanding": {"pathology": [
        {"symptom": "خطای پرتکرار TimeoutError ×4",
         "root_cause": "نامعلوم (نیاز به کاوش)", "severity": "medium"},
        {"symptom": "درآمد صفر", "root_cause": "هیچ لِگی وصل نیست", "severity": "high"},
    ], "open_questions": ["چرا خطاهای پرتکرار رخ می‌دهند؟"]},
}


def _reset_queue():
    _QUEUE.parent.mkdir(parents=True, exist_ok=True)
    if _QUEUE.exists():
        _QUEUE.unlink()


def _rows():
    if not _QUEUE.exists():
        return []
    return [json.loads(x) for x in _QUEUE.read_text("utf-8").splitlines() if x.strip()]


def t_e0_flag_off_writes_nothing():
    _clear_flags(); _reset_queue()
    r = cp.produce_from_unknown(_QUEUE, record=_UNKNOWN_REC)
    assert r == {"produced": False, "reason": "flag-off"}, r
    assert not _QUEUE.exists(), "با فلگِ خاموش ردیف نوشته شد"


def t_e1_unknown_root_cause_becomes_a_queue_row():
    """معیارِ پذیرشِ ۲: یک ریشهٔ نامعلوم → یک ردیفِ قابل‌ابطال در صف."""
    _clear_flags(); _arm(sk._UNKNOWN_C6_FLAG); _reset_queue()
    try:
        r = cp.produce_from_unknown(_QUEUE, record=_UNKNOWN_REC)
        assert r.get("produced") is True, r
        rows = _rows()
        assert len(rows) == 1, rows
        row = rows[0]
        assert row["status"] == "PENDING" and row["kind"] == "unknown_root_cause", row
        assert row["probe"] == cp.UNKNOWN_PROBE and row["id"].startswith("c6-"), row
        assert "TimeoutError" in row["subject"], row["subject"]
        assert len(row["falsification_criteria"]) >= 2, row
        assert row["baseline_count"] == -1, "ردیفِ نامعلوم نباید عددِ سنجیده جا بزند"
        assert row["origin"]["selfknow_version"] == 42, row["origin"]
        assert row["measured"]["count"] == -1, row["measured"]
    finally:
        _clear_flags()


def t_e2_idempotent_across_cycles():
    _clear_flags(); _arm(sk._UNKNOWN_C6_FLAG)
    try:
        n0 = len(_rows())
        r = cp.produce_from_unknown(_QUEUE, record=_UNKNOWN_REC)
        assert r.get("produced") is False and r["reason"] == "all-already-queued", r
        assert len(_rows()) == n0, "همان نشانه دو بار صف شد"
    finally:
        _clear_flags()


def t_e3_known_root_cause_makes_no_row():
    _clear_flags(); _arm(sk._UNKNOWN_C6_FLAG); _reset_queue()
    try:
        rec = {"version": 1, "understanding": {"pathology": [
            {"symptom": "درآمد صفر", "root_cause": "هیچ لِگی وصل نیست"}]}}
        r = cp.produce_from_unknown(_QUEUE, record=rec)
        assert r.get("produced") is False and r["reason"] == "no-unknown-root-cause", r
        assert not _QUEUE.exists() or not _rows(), "ریشهٔ معلوم نباید ردیف بسازد"
    finally:
        _clear_flags()


def t_e4_open_questions_do_not_pollute_the_lab():
    """پرسشِ باز ابطال‌پذیر نیست — مقصدش مالک است نه صفِ آزمایش."""
    _clear_flags(); _arm(sk._UNKNOWN_C6_FLAG); _reset_queue()
    try:
        rec = {"version": 2, "understanding": {
            "pathology": [], "open_questions": ["چرا خطاها رخ می‌دهند؟"]}}
        r = cp.produce_from_unknown(_QUEUE, record=rec)
        assert r.get("produced") is False, r
        assert not _rows(), _rows()
    finally:
        _clear_flags()


def t_e5_the_live_run_writes_the_row():
    """پلِ واقعی: `run()` — نه فقط تابعِ producer — ردیف را در صف می‌گذارد."""
    _clear_flags(); _reset_queue()
    _orig = sk._ask_llm
    try:
        _seed_state(); _fresh_doctor(); _no_llm()
        off = sk.run(persist=True)
        assert "c6_unknown" not in off, "فلگ خاموش ولی پل کار کرد"
        assert not _QUEUE.exists(), "فلگ خاموش ولی صف نوشته شد"
        _arm(sk._UNKNOWN_C6_FLAG)
        _fresh_doctor()
        on = sk.run(persist=True)
        assert on.get("c6_unknown", {}).get("produced") is True, on.get("c6_unknown")
        rows = _rows()
        assert len(rows) == 1 and rows[0]["kind"] == "unknown_root_cause", rows
        assert rows[0]["origin"]["selfknow_version"] == on["version"], rows[0]["origin"]
    finally:
        sk._ask_llm = _orig
        _clear_flags()


def t_e6_flag_names_agree_across_the_bridge():
    assert sk._UNKNOWN_C6_FLAG == cp.UNKNOWN_FLAG, (sk._UNKNOWN_C6_FLAG, cp.UNKNOWN_FLAG)


def t_e7_a_production_caller_exists():
    """گاردِ «فیچرِ مرده»: خارج از _ops/tests باید حداقل یک صداکنندهٔ واقعی باشد."""
    callers = []
    for p in _OPS.rglob("*.py"):
        rel = p.relative_to(_OPS).as_posix()
        if rel.startswith("tests/") or "_Archive" in rel:
            continue
        try:
            tree = ast.parse(p.read_text("utf-8", errors="replace"))
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                    and n.func.attr == "produce_from_unknown":
                callers.append(f"{rel}:{n.lineno}")
    assert callers, "produce_from_unknown صفر صداکنندهٔ تولیدی دارد — فیچرِ مرده"
    assert any(c.startswith("doctor/self_knowledge.py") for c in callers), callers


# ══ initiative: اولین مصرف‌کنندهٔ نام‌بردهٔ open_questions ══════════════════════
def t_f0_initiative_context_flag_off():
    _clear_flags()
    (_SB / "doctor").mkdir(parents=True, exist_ok=True)
    (_SB / "doctor" / "self-knowledge-latest.json").write_text(
        json.dumps(_UNKNOWN_REC, ensure_ascii=False), "utf-8")
    ctx = iv._context()
    assert "فهمِ_من" in ctx, ctx.keys()
    assert "نمی‌دانم‌ها" not in ctx, "فلگ خاموش ولی بلوکِ تازه آمد"


def t_f1_initiative_names_the_unknowns():
    _clear_flags(); _arm(iv.UNKNOWNS_FLAG)
    try:
        ctx = iv._context()
        blk = ctx.get("نمی‌دانم‌ها")
        assert blk, ctx.keys()
        assert blk["پرسش‌های_باز_که_فقط_تو_جواب_داری"] == \
            ["چرا خطاهای پرتکرار رخ می‌دهند؟"], blk
        assert blk["ریشه‌های_نامعلومی_که_خودم_دارم_می‌کاوم"] == \
            ["خطای پرتکرار TimeoutError ×4"], blk
    finally:
        _clear_flags()


def t_f2_the_record_now_carries_what_initiative_reads():
    """دو شاخهٔ خواندنِ مردهٔ `_context`: رکورد هرگز این کلیدها را نداشت."""
    _clear_flags()
    _orig = sk._ask_llm
    try:
        _seed_state(); _write_corrections(_CORR_REJECT_ERRORS); _fresh_doctor(); _no_llm()
        off = sk.run(persist=True)
        assert "owner_corrections" not in off, "فلگ خاموش ولی کلید اضافه شد"
        _arm(sk._STEER_FLAG)
        _fresh_doctor()
        on = sk.run(persist=True)
        assert on.get("owner_corrections"), "رکورد هنوز تصحیح‌های مالک را حمل نمی‌کند"
        iv_ctx_src = (_OPS / "initiative.py").read_text("utf-8")
        assert 'sk.get("owner_corrections")' in iv_ctx_src
    finally:
        sk._ask_llm = _orig
        _clear_flags()


def t_g_no_dangerous_primitives_added():
    src = (_OPS / "c6_producer.py").read_text("utf-8")
    assert "subprocess" not in src and "urlopen(" not in src and "requests." not in src
    assert "model_router" not in src, "producer نباید مصرف‌کنندهٔ مغز شود"


CHECKS = [
    ("(a0) فلگ خاموش = رفتارِ دیروز", t_a0_flag_off_is_yesterday),
    ("(a1) نشانهٔ ردشده تمرکز را از دست می‌دهد", t_a1_rejected_symptom_loses_focus),
    ("(a2) نشانهٔ خواسته‌شده تمرکز می‌گیرد", t_a2_wanted_symptom_wins_focus),
    ("(a3) prev واقعاً خوانده می‌شود", t_a3_prev_is_actually_read),
    ("(a4) اجرای کاملِ heuristic از مالک اطاعت می‌کند", t_a4_end_to_end_heuristic_run_obeys_the_owner),
    ("(b1) عددِ ۰.۴ هاردکد رفت", t_b1_no_more_hardcoded_confidence),
    ("(b2) شاهد سنجیده می‌شود نه ثابت", t_b2_evidence_counts_what_is_really_readable),
    ("(c0) شکلِ trajectory با فلگ خاموش", t_c0_flag_off_trajectory_shape_unchanged),
    ("(c1) مقایسهٔ بین دو مغز رد می‌شود", t_c1_cross_backend_is_refused),
    ("(c2) هم‌مغز هنوز مقایسه می‌شود", t_c2_same_backend_still_compares),
    ("(c3) اطمینانِ نامعلوم = نامعلوم", t_c3_unknown_confidence_reports_unknown),
    ("(c4) گاردِ قدیمی زیرِ فلگ سبز می‌ماند", t_c4_legacy_guard_stays_green_under_the_flag),
    ("(d1) گیتِ کاوش خاموش = دیروز", t_d1_probe_gate_off_is_yesterday),
    ("(d2) heuristic می‌تواند کاوش را ماشه بکشد", t_d2_heuristic_can_now_trigger_the_probe),
    ("(d3) اطمینانِ نامعلوم دلیلِ کاوش است", t_d3_unknown_confidence_is_a_reason_to_probe),
    ("(e0) فلگ خاموش هیچ ردیفی نمی‌نویسد", t_e0_flag_off_writes_nothing),
    ("(e1) ریشهٔ نامعلوم → ردیفِ صف", t_e1_unknown_root_cause_becomes_a_queue_row),
    ("(e2) idempotent بینِ چرخه‌ها", t_e2_idempotent_across_cycles),
    ("(e3) ریشهٔ معلوم ردیف نمی‌سازد", t_e3_known_root_cause_makes_no_row),
    ("(e4) پرسشِ باز صف را آلوده نمی‌کند", t_e4_open_questions_do_not_pollute_the_lab),
    ("(e5) خودِ run() ردیف را می‌نویسد", t_e5_the_live_run_writes_the_row),
    ("(e6) نامِ فلگ در دو طرفِ پل یکی است", t_e6_flag_names_agree_across_the_bridge),
    ("(e7) صداکنندهٔ تولیدی وجود دارد", t_e7_a_production_caller_exists),
    ("(f0) contextِ ابتکار با فلگ خاموش", t_f0_initiative_context_flag_off),
    ("(f1) ابتکار نمی‌دانم‌ها را نام می‌برد", t_f1_initiative_names_the_unknowns),
    ("(f2) رکورد چیزی را که خوانده می‌شود حمل می‌کند", t_f2_the_record_now_carries_what_initiative_reads),
    ("(g) هیچ primitive خطرناکی اضافه نشد", t_g_no_dangerous_primitives_added),
]

if __name__ == "__main__":
    print("── test_selfknow_unknown_bridge ──")
    assert len(CHECKS) == 27, f"شمارِ چک‌ها عوض شده: {len(CHECKS)}"
    _failed = harness.run(CHECKS)
    print(f"{len(CHECKS) - _failed}/{len(CHECKS)} pass")
    print("FAIL" if _failed else "PASS", "— test_selfknow_unknown_bridge")
    sys.exit(1 if _failed else 0)
