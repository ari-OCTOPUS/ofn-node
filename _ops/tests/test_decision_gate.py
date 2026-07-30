"""test_decision_gate — WAVE W2، معیارهای پذیرشِ §۸ قراردادِ GENOME LOCK.

LOCK-A می‌گوید AI فقط با «شواهد + بدونِ نابودی + ردهٔ ≤ سقف» اجرا می‌کند، و
HARD-STOPها **هیچ‌وقت** با ۵۱٪ باز نمی‌شوند. سخت‌ترین قیدها این‌جا آن‌هایی‌اند
که نباید ممکن باشند:

  · پول/راز/دیپلوی/تکثیر/ژنوم با شواهدِ کاملِ ۱.۰ هم انسانی بماند.
  · نبودِ شواهد → صفر، نه پیش‌فرضِ خوش‌بینانه.
  · شواهدِ آلوده‌به‌stub جریمه بخورد.
  · و نقطهٔ کورِ ۱۳۸: `params.amount_aud` **تودرتو** باید دیده شود — نسخهٔ
    سطحیِ `autonomy_matrix` دقیقاً همین را نمی‌دید و «آزاد» می‌گفت.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("decision-gate")

_OPS = harness.REAL_VAULT / "_ops"
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib            # noqa: E402
import decision_gate as dg   # noqa: E402

FULL = {"completeness": 1.0, "verifier_pass": True, "consistency": 1.0}


def _on(v=True):
    if v:
        os.environ[dg.FLAG] = "1"
    else:
        os.environ.pop(dg.FLAG, None)


# ─── HARD-STOP: هرگز، حتی با مدرکِ کامل ────────────────────────────────────
def t_every_hard_stop_stays_human_even_with_perfect_evidence():
    """معیارِ پذیرشِ ۶. این تست قلبِ LOCK-A است."""
    _on()
    try:
        cases = [
            ("پرداختِ فاکتور", {}),
            ("spend on ads", {}),
            ("transfer funds", {}),
            ("rotate the api_key", {}),
            ("خواندنِ .env", {}),
            ("git push to master", {}),
            ("deploy master", {}),
            ("restart organism", {}),
            ("spawn a clone", {}),
            ("تکثیرِ سلول", {}),
            ("genome write ring-0", {}),
            ("disable kill-switch", {}),
            ("rm -rf state", {}),
            ("حذفِ انبوهِ رکوردها", {}),
            ("ارسالِ بیرونی به مشتری", {}),
            # و تودرتو — نقطهٔ کورِ ۱۳۸
            ("کارِ بی‌نام", {"params": {"amount_aud": 500}}),
            ("کارِ بی‌نام", {"steps": [{"tool": "pocketsmith", "op": "write"}]}),
            ("کارِ بی‌نام", {"a": {"b": {"c": "api_key"}}}),
        ]
        for action, payload in cases:
            r = dg.decide(action=action, payload=payload, evidence=FULL,
                          risk_class=1)
            assert r["executor"] == "owner_required", (action, payload, r)
            assert r["destruction_risk"] is True, (action, payload)
            assert r["evidence_score"] == 1.0, "شواهد کامل بود — تست بی‌معنی می‌شود"
    finally:
        _on(False)


def t_the_nested_money_field_is_the_138_blindspot():
    """گاردِ صریحِ نقطهٔ کورِ ۱۳۸: نسخهٔ سطحی این را «آزاد» می‌خواند."""
    _on()
    try:
        payload = {"title": "کارِ ساده", "params": {"amount_aud": 500}}
        assert "amount_aud" in dg.flatten(payload), "تخت‌کردن تودرتو را ندید"
        r = dg.decide(action="کارِ ساده", payload=payload, evidence=FULL, risk_class=1)
        assert r["executor"] == "owner_required", r
    finally:
        _on(False)


def t_flatten_reaches_keys_values_and_lists():
    b = dg.flatten({"a": {"b": ["c", {"d": "payment"}]}})
    for token in ("a", "b", "c", "d", "payment"):
        assert token in b, (token, b)


def t_a_cyclic_or_deep_structure_fails_closed():
    deep = cur = {}
    for _ in range(30):
        cur["n"] = {}
        cur = cur["n"]
    destroy, why = dg.destruction_risk(deep)
    assert destroy is True and "عمیق" in why, (destroy, why)


# ─── شواهد ─────────────────────────────────────────────────────────────────
def t_missing_evidence_scores_zero_not_optimistic():
    """معیارِ پذیرشِ ۶: بدونِ مدرک، AI نمی‌تواند ۵۱٪ ادعا کند."""
    _on()
    try:
        for ev in (None, {}, {"completeness": None}, "نه‌دیکشنری"):
            score, _ = dg.evidence_score(ev)
            assert score == 0.0, (ev, score)
            r = dg.decide(action="کارِ بی‌خطر", evidence=ev, risk_class=1)
            assert r["executor"] == "owner_required", (ev, r)
            assert r["needs_evidence"] is True, r
    finally:
        _on(False)


def t_stub_tainted_evidence_is_rejected():
    """شواهدی که از stub آمده شواهد نیست."""
    _on()
    try:
        tainted = {**FULL, "stub": True}
        score, why = dg.evidence_score(tainted)
        clean, _ = dg.evidence_score(FULL)
        assert score < clean, (score, clean)
        assert any("stub" in w for w in why), why
        r = dg.decide(action="کارِ بی‌خطر", evidence=tainted, risk_class=1)
        assert r["executor"] == "owner_required", r
    finally:
        _on(False)


def t_evidence_score_is_total_and_bounded():
    for ev in (None, {}, {"completeness": "x"}, {"completeness": float("nan")},
               {"completeness": 1e9, "consistency": -1e9},
               {"verifier_pass": "yes"}, {"stub": "no"}):
        s, _ = dg.evidence_score(ev)
        assert 0.0 <= s <= 1.0, (ev, s)


# ─── ردهٔ ریسک ─────────────────────────────────────────────────────────────
def t_risk_class_above_the_ai_ceiling_is_always_human():
    """معیارِ پذیرشِ ۶: L4 پول همیشه مالک."""
    _on()
    try:
        for rc in (dg.AI_MAX_CLASS + 1, 4, 9):
            r = dg.decide(action="کارِ بی‌خطر", evidence=FULL, risk_class=rc)
            assert r["executor"] == "owner_required", (rc, r)
        ok = dg.decide(action="کارِ بی‌خطر", evidence=FULL, risk_class=dg.AI_MAX_CLASS)
        assert ok["executor"] == "ai", ok
    finally:
        _on(False)


def t_an_unreadable_risk_class_becomes_the_highest():
    _on()
    try:
        for rc in (None, "خیلی", float("nan"), [], {}):
            r = dg.decide(action="کارِ بی‌خطر", evidence=FULL, risk_class=rc)
            assert r["risk_class"] == 4 and r["executor"] == "owner_required", (rc, r)
    finally:
        _on(False)


# ─── گیتِ خاموش = رفتارِ امروز ─────────────────────────────────────────────
def t_flag_off_forces_everything_to_propose_only():
    """معیارِ پذیرشِ ۴: خاموش → رفتارِ ارگانیسم بایت‌به‌بایت."""
    _on(False)
    r = dg.decide(action="کاملاً بی‌خطر", evidence=FULL, risk_class=0)
    assert r["executor"] == "owner_required", r
    assert any("خاموش" in x for x in r["reasons"]), r["reasons"]


def t_the_only_path_to_ai_needs_all_three_conditions():
    """و همهٔ نقض‌های تک‌شرطی باید ببندند."""
    _on()
    try:
        assert dg.decide(action="بی‌خطر", evidence=FULL, risk_class=1)["executor"] == "ai"
        assert dg.decide(action="بی‌خطر", evidence={"completeness": 0.5},
                         risk_class=1)["executor"] == "owner_required"
        assert dg.decide(action="پرداخت", evidence=FULL,
                         risk_class=1)["executor"] == "owner_required"
        assert dg.decide(action="بی‌خطر", evidence=FULL,
                         risk_class=4)["executor"] == "owner_required"
    finally:
        _on(False)


# ─── کارت و قرارداد UI ─────────────────────────────────────────────────────
def t_the_card_shows_the_four_required_buttons():
    r = dg.decide(action="کار", evidence=FULL, risk_class=1, trace_id="t123")
    body, kb = dg.card(r)
    verbs = {b["callback_data"].split(":")[0] for row in kb for b in row}
    assert verbs == {"ok", "no", "later", "dg"}, verbs
    for row in kb:
        for b in row:
            assert len(b["callback_data"].encode()) <= 64, b


def t_a_destruction_card_says_it_will_never_be_automatic():
    _on()
    try:
        r = dg.decide(action="پرداختِ فاکتور", evidence=FULL, risk_class=1)
        body, _ = dg.card(r)
        assert "ردهٔ نابودی" in body and "هرگز خودکار" in body, body
    finally:
        _on(False)


def t_the_card_escapes_hostile_text():
    r = dg.decide(action="<script>x</script>", evidence=FULL, risk_class=1)
    body, _ = dg.card(r)
    assert "<script>" not in body and "&lt;script&gt;" in body


def t_every_record_carries_the_vote_math_and_a_trace():
    r = dg.decide(action="کار", evidence=FULL, risk_class=1, trace_id="abc")
    for k in ("ai_weight", "owner_weight", "evidence_score", "threshold",
              "destruction_risk", "risk_class", "executor", "trace_id"):
        assert k in r, k
    assert abs(r["ai_weight"] + r["owner_weight"] - 1.0) < 1e-9
    assert r["ai_weight"] > r["owner_weight"], "۵۱/۴۹ برعکس شد"


# ─── مرزِ ماژول ────────────────────────────────────────────────────────────
def t_the_gate_judges_but_never_acts():
    import ast
    tree = ast.parse(Path(dg.__file__).read_text("utf-8"))
    banned = {"subprocess", "urllib", "requests", "socket", "shutil"}
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (banned & imported), sorted(banned & imported)
    called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for d in ("unlink", "rmtree", "system", "run", "apply_approved"):
        assert d not in called, f"گیت خودش عمل می‌کند: {d}"


def t_records_append_and_never_overwrite():
    try:
        dg.LEDGER.unlink()
    except OSError:
        pass
    for i in range(3):
        assert dg.record(dg.decide(action=f"کار {i}", evidence=FULL, risk_class=1))
    rows = [json.loads(x) for x in dg.LEDGER.read_text("utf-8").splitlines() if x.strip()]
    assert len(rows) == 3, rows


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_decision_gate: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
