# -*- coding: utf-8 -*-
"""تستهای آرشیو بدایع — گیت ماشینی فاز ۲ (Novelty Archive)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "novelty"))

from novelty.archive import (  # noqa: E402
    NoveltyArchive, BehaviorVector, evaluate, vector_from_proposal,
    cohort_summary, exact_key, jaccard, shingles, normalize_text,
    EXACT_DUPLICATE, VARIATION_CANDIDATE, NOVELTY_CANDIDATE, LEARNABLE,
    ADMITTED, INCOMPLETE,
)
from novelty.debate_hook import pre_budget_gate  # noqa: E402


def _proposal(text, **kw):
    p = {"text": text, "problem_class": "test", "replay_recipe": "r",
         "receipt_refs": ["x"], "expected_observable_delta": "d", "falsifier": "f"}
    p.update(kw)
    return p


def test_exact_duplicate_rejected():
    a = vector_from_proposal(_proposal("استفاده از شبکه عصبی برای پیشبینی بازار"))
    arc = [a]
    r = evaluate(_proposal("استفاده از شبکه عصبی برای پیشبینی بازار"), arc)
    assert r["state"] == EXACT_DUPLICATE
    assert r["allow"] is False


def test_variation_rejected_at_threshold():
    base = vector_from_proposal(_proposal("استفاده از شبکههای عصبی مصنوعی برای پیشبینی حرکات بازار"))
    r = evaluate(_proposal("استفاده از شبکههای عصبی مصنوعی برای پیشبینی بازار"), [base])
    assert r["state"] == VARIATION_CANDIDATE
    assert r["allow"] is False
    assert r["nearest"]["jaccard_char3"] >= 0.80


def test_novel_but_not_learnable():
    r = evaluate(_proposal("یک معماری کاملاً تازه برای رلهٔ رویدادهای شبکهای",
                           replay_recipe="", receipt_refs=[]), [])
    assert r["state"] == NOVELTY_CANDIDATE
    assert r["allow"] is True
    assert r["learnable"] is False


def test_learnable_without_evidence_pending():
    r = evaluate(_proposal("یک معماری کاملاً تازه برای رلهٔ رویدادهای شبکهای"), [])
    assert r["state"] == LEARNABLE
    assert r["learnable"] is True


def test_admitted_needs_independent_evidence():
    r = evaluate(_proposal("یک معماری کاملاً تازه برای رلهٔ رویدادهای شبکهای",
                           independent_evidence_ref="receipt-123"), [])
    assert r["state"] == ADMITTED


def test_incomplete_no_text():
    r = evaluate({}, [])
    assert r["state"] == INCOMPLETE
    assert r["allow"] is False


def test_cohort_numbers_consistent_with_pipeline():
    ideas = ["ایدهٔ آلفا", "ایدهٔ آلفا", "ایدهٔ بتا", "ایدهٔ گاما"]
    s = cohort_summary(ideas)
    assert s["total"] == 4
    assert s["exact_unique"] == 3
    assert s["exact_repeat_records"] == 1


def test_near_dup_pair_count_from_real_pair():
    ideas = [
        "استفاده از شبکههای عصبی مصنوعی برای پیشبینی حرکات بازار",
        "استفاده از شبکههای عصبی مصنوعی برای پیشبینی بازار",
        "ایدهٔ کاملاً دیگر دربارهٔ رنگ سالن نقاشی",
    ]
    s = cohort_summary(ideas)
    assert s["near_duplicate_candidate_pairs"] == 1


def test_archive_append_only_grows():
    p = Path(__file__).resolve().parent / "_tmp_archive_test.jsonl"
    if p.exists():
        p.unlink()
    a = NoveltyArchive(p)
    n1 = a.append({"kind": "x", "v": 1})
    n2 = a.append({"kind": "x", "v": 2})
    rows = [json.loads(l) for l in p.read_text("utf-8").splitlines() if l.strip()]
    assert len(rows) == 2
    assert rows[0]["v"] == 1 and rows[1]["v"] == 2   # ردیف قبلی دستنخورده
    assert n2["line"] == 2
    p.unlink()


def test_hook_failsoft_when_archive_missing():
    r = pre_budget_gate("هر ایدهای", "t1",
                        archive_path=Path(__file__).resolve().parent / "_no_such_archive.jsonl")
    assert r["allow"] is True
    assert r["state"] == "ARCHIVE_EMPTY"


def test_novelty_gate_enabled_env_wins():
    import os
    from novelty.debate_hook import novelty_gate_enabled
    old = os.environ.get("OCTOPUS_WIRE_NOVELTY_GATE")
    os.environ["OCTOPUS_WIRE_NOVELTY_GATE"] = "1"
    try:
        assert novelty_gate_enabled() is True
    finally:
        if old is None:
            os.environ.pop("OCTOPUS_WIRE_NOVELTY_GATE", None)
        else:
            os.environ["OCTOPUS_WIRE_NOVELTY_GATE"] = old
    os.environ["OCTOPUS_WIRE_NOVELTY_GATE"] = "0"
    assert novelty_gate_enabled() is False
    os.environ.pop("OCTOPUS_WIRE_NOVELTY_GATE", None)


def test_hook_blocks_duplicate():
    p = Path(__file__).resolve().parent / "_tmp_hook_archive.jsonl"
    if p.exists():
        p.unlink()
    a = NoveltyArchive(p)
    a.append({"kind": "cohort-idea", "text": "ایدهٔ تکراری ثابت", "behavior_id": exact_key("ایدهٔ تکراری ثابت")})
    r = pre_budget_gate("ایدهٔ تکراری ثابت", "t1", archive_path=p)
    assert r["allow"] is False
    assert r["state"] == EXACT_DUPLICATE
    p.unlink()


def test_jaccard_math():
    s1 = shingles("abcdef")
    s2 = shingles("abcdef")
    assert jaccard(s1, s2) == 1.0
    assert normalize_text("  AB!cd  ") == "ab cd"
    assert normalize_text(normalize_text("x!y  z")) == normalize_text("x!y  z")
