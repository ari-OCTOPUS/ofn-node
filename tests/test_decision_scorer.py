"""C-1 + AMEND-1 D-1 tests — scorer contract and the anti-wireheading reward."""
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from tools import decision_scorer as ds  # noqa: E402


def test_preregister_then_resolve_roundtrip(tmp_path):
    rec = ds.preregister("send-quote-variant-A", 0.18, 0.10, 72,
                          expected_cash_delta_cents=150000,
                          runway_impact_days=0.5, store=tmp_path / "d.jsonl")
    ds.resolve(rec["decision_id"], 1, store=tmp_path / "d.jsonl")
    d = ds.dashboard(store=tmp_path / "d.jsonl")
    assert d["n_decisions_scored"] == 1
    assert d["brier_octopus"] == round((0.18 - 1) ** 2, 4)


def test_theoretical_no_loop_label(tmp_path):
    rec = ds.preregister("refactor-for-elegance", 0.5, 0.5, 24, store=tmp_path / "d.jsonl")
    assert "THEORETICAL-NO-LOOP" in rec["labels"]


def test_double_resolve_forbidden(tmp_path):
    rec = ds.preregister("x", 0.3, 0.3, 1, store=tmp_path / "d.jsonl")
    ds.resolve(rec["decision_id"], 0, store=tmp_path / "d.jsonl")
    with pytest.raises(ds.ScorerError):
        ds.resolve(rec["decision_id"], 1, store=tmp_path / "d.jsonl")


def test_rate_without_denominator_raises():
    with pytest.raises(ds.ScorerError):
        ds.rate(3, 0)


def test_reward_rejects_fake_rows(tmp_path):
    # a row WITHOUT payout_id must contribute zero + a warning event
    bad = tmp_path / "ledger.jsonl"
    bad.write_text(json.dumps({"kind": "verified_cash",
                               "settled_amount_cents": 99999}) + "\n",
                   encoding="utf-8")
    r = ds.reward(bad)
    assert r["verified_cash_cents"] == 0
    assert r["valid_rows"] == 0
    assert any("rejected" in w for w in r["warnings"])


def test_reward_accepts_six_condition_row(tmp_path):
    lp = tmp_path / "ledger.jsonl"
    lp.write_text(json.dumps({
        "kind": "verified_cash", "payout_id": "PO-1",
        "settled_amount_cents": 25000, "prev_hash": "aa",
        "payload_sha256": "bb", "ato_reserve_cents": 7500}) + "\n",
        encoding="utf-8")
    assert ds.reward(lp)["verified_cash_cents"] == 25000


def test_disempowerment_rule(tmp_path):
    # a domain where octopus is confidently WRONG on 10 decisions
    for i in range(10):
        rec = ds.preregister(f"confident-wrong-{i}", 0.9, 0.5, 1,
                             domain="bad-brain", store=tmp_path / "d.jsonl")
        ds.resolve(rec["decision_id"], 0, store=tmp_path / "d.jsonl")
    d = ds.dashboard(store=tmp_path / "d.jsonl")
    assert "bad-brain" in d["disempowered_domains"]
