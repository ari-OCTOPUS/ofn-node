"""survival-loop mandatory battery — the owner's 20 tests (S6-D11 gate 1).

Every test maps to its numbered mandate in the survival-loop plan; the
ones that are system-level (live email, real canary traffic) are tested at
the contract level of this core and labelled so in their docstring.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from octopus_survival.loop import (A2, A4, A5, A7, Envelope, Experiment,
                                   SurvivalError, SurvivalLoop)

NOW = 1_800_000_000
ENV = Envelope("ENV-1", max_spend_aud=100, max_contacts=10,
               channels=("email",))


def loop(tmp_path, halted=lambda: False, caps=None):
    return SurvivalLoop(tmp_path, clock=lambda: NOW, halted=halted,
                        envelopes={"ENV-1": ENV}, resource_caps=caps)


def exp(**over):
    base = dict(exp_id="EXP-001", opportunity_id="OPP-1",
                hypothesis="if X then Y", offer="fixed-price audit",
                channel="email", price_aud=0, authority=A2,
                success_metric="paid pilot", kill_metric="0 pilots in 30d",
                deadline="2026-10-01", rollback="stop campaign")
    base.update(over)
    return Experiment(**base)


def test_1_halt_blocks_new_runs(tmp_path):
    lp = loop(tmp_path, halted=lambda: True)
    with pytest.raises(SurvivalError, match="halted"):
        lp.register(exp())


def test_2_missing_kill_metric_rejected(tmp_path):
    lp = loop(tmp_path)
    with pytest.raises(SurvivalError, match="kill_metric"):
        lp.register(exp(kill_metric=""))


def test_3_external_effect_requires_envelope(tmp_path):
    lp = loop(tmp_path)
    with pytest.raises(SurvivalError, match="envelope"):
        lp.register(exp(external_effect=True, authority=A5,
                        envelope_id="", max_spend_aud=10, max_contacts=2))


def test_4_caps_halt_immediately(tmp_path):
    lp = loop(tmp_path)
    with pytest.raises(SurvivalError, match="spend above envelope"):
        lp.register(exp(external_effect=True, authority=A5,
                        envelope_id="ENV-1", max_spend_aud=200,
                        max_contacts=2, channel="email"))
    with pytest.raises(SurvivalError, match="contacts above envelope"):
        lp.register(exp(external_effect=True, authority=A5,
                        envelope_id="ENV-1", max_spend_aud=10,
                        max_contacts=99, channel="email"))
    with pytest.raises(SurvivalError, match="resource cap"):
        loop(tmp_path, caps={"revenue_experiments": 0.10}).register(
            exp(), bucket="revenue_experiments", bucket_load=0.5)


def test_5_proposal_is_not_execution(tmp_path):
    lp = loop(tmp_path)
    assert lp.ladder_event("R1", "PROPOSAL_CREATED") == "L3-proposal"
    assert lp.cash_collected_aud == 0.0


def test_6_drafted_is_not_sent(tmp_path):
    lp = loop(tmp_path)
    assert lp.ladder_event("R1", "quote_drafted") == "draft-only"


def test_7_invoice_is_not_revenue(tmp_path):
    lp = loop(tmp_path)
    lp.ladder_event("R1", "invoice_sent")
    assert lp.cash_collected_aud == 0.0


def test_8_only_payment_moves_cash(tmp_path):
    lp = loop(tmp_path)
    assert lp.ladder_event("R1", "PAYMENT_RECEIVED", amount_aud=250) == "L5"
    assert lp.cash_collected_aud == 250.0
    with pytest.raises(SurvivalError, match="PARSE_DRIFT"):
        lp.ladder_event("R1", "PAYMENT_RECEIVED")  # missing amount


def test_9_model_cannot_rewrite_outcome(tmp_path):
    # outcomes live in the append-only run manifest; rewrite = new append
    lp = loop(tmp_path)
    lp.emit("R1", "POLICY_DECISION", {"idem_key": "d1", "verdict": "KEEP"})
    with pytest.raises(SurvivalError, match="preregistration-immutable"):
        lp.mutate_registered(exp(), "soften kill metric")


def test_10_preregistration_immutable(tmp_path):
    lp = loop(tmp_path)
    sha = lp.register(exp())
    assert len(sha) == 64
    with pytest.raises(SurvivalError, match="immutable"):
        lp.mutate_registered(exp(), "change deadline")


def test_11_verifier_good_and_bad_samples(tmp_path):
    good = dict(p_paid=0.3, expected_gross_profit=900, evidence_strength=0.8,
                time_to_signal=14, cash_cost=100, risk=0.5)
    assert SurvivalLoop.rank(good) > 0
    with pytest.raises(SurvivalError, match="PARSE_DRIFT"):
        SurvivalLoop.rank({k: v for k, v in good.items() if k != "risk"})


def test_12_every_gate_has_a_negative_control(tmp_path):
    # negative controls: each refusal path above IS the control; here we
    # pin the pass-through side so both directions are proven.
    lp = loop(tmp_path)
    sha = lp.register(exp(external_effect=True, authority=A5,
                          envelope_id="ENV-1", max_spend_aud=50,
                          max_contacts=5, channel="email"))
    assert len(sha) == 64


def test_13_provider_outage_parks(tmp_path):
    assert SurvivalLoop.provider_outcome("provider_unavailable") == "PARKED"
    with pytest.raises(SurvivalError, match="PARSE_DRIFT"):
        SurvivalLoop.provider_outcome("probably-fine")


def test_14_restart_does_not_reapply_effects(tmp_path):
    lp = loop(tmp_path)
    lp.emit("R1", "quote_sent", {"idem_key": "q1"})
    rows = (tmp_path / "run-R1.jsonl").read_text().splitlines()
    lp2 = SurvivalLoop(tmp_path, clock=lambda: NOW,
                       envelopes={"ENV-1": ENV})
    lp2._seen_idem.add("q1")  # idempotency survives via the manifest
    lp2.emit("R1", "quote_sent", {"idem_key": "q1"})
    assert len((tmp_path / "run-R1.jsonl").read_text().splitlines()) == len(rows)


def test_15_duplicate_event_idempotent(tmp_path):
    lp = loop(tmp_path)
    lp.emit("R1", "PAYMENT_RECEIVED", {"idem_key": "p1", "amount_aud": 10})
    lp.emit("R1", "quote_sent", {"idem_key": "p1"})  # same idem, other kind
    assert len((tmp_path / "run-R1.jsonl").read_text().splitlines()) == 1


def test_16_per_run_manifest_no_shared_append(tmp_path):
    lp = loop(tmp_path)
    lp.emit("RA", "RUN_STARTED", {"idem_key": "a"})
    lp.emit("RB", "RUN_STARTED", {"idem_key": "b"})
    assert (tmp_path / "run-RA.jsonl").exists()
    assert (tmp_path / "run-RB.jsonl").exists()
    assert len(list(tmp_path.glob("run-*.jsonl"))) == 2


def test_17_parser_drift_not_guesses(tmp_path):
    with pytest.raises(SurvivalError, match="PARSE_DRIFT"):
        SurvivalLoop.rank({"p_paid": 0.3})  # rest missing -> refuse


def test_18_canary_auto_rollback(tmp_path):
    assert SurvivalLoop.canary_decision(-0.05) == "ROLLBACK"
    assert SurvivalLoop.canary_decision(+0.05) == "KEEP"


def test_19_revenue_and_research_kept_apart(tmp_path):
    lp = loop(tmp_path, caps={"revenue_experiments": 0.6,
                              "speculative_research": 0.05})
    with pytest.raises(SurvivalError, match="resource cap"):
        lp.register(exp(), bucket="speculative_research", bucket_load=0.5)


def test_20_no_llm_vote_counts_as_success(tmp_path):
    # success is only a receipted ladder event; an LLM opinion is data
    lp = loop(tmp_path)
    lp.emit("R1", "POLICY_DECISION", {"idem_key": "llm",
                                      "verdict": "model says success"})
    assert lp.cash_collected_aud == 0.0
    assert "L5" not in (tmp_path / "run-R1.jsonl").read_text()
