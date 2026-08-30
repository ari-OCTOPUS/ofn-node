#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_bcm_hebbian_shadow_e2e.py — shadow channels; no production state touch."""
from __future__ import annotations

import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "tests"))

import harness  # noqa: E402
from signals.shadow_channels import BCMShadowChannel, HebbianShadowChannel  # noqa: E402


def t_bcm_threshold_high_grows():
    ch = BCMShadowChannel(w_cap=1.0, beta=0.01, eta=0.5)
    r = ch.run(activations=[0.9, 0.9, 0.9], run_id="e2e-bcm-hi")
    assert r.external_effects == ()
    assert r.evidence_level == "SHADOW"
    assert r.weight is not None and r.initial_weight is not None
    assert r.weight > r.initial_weight


def t_bcm_low_activation_does_not_grow():
    ch = BCMShadowChannel(w_cap=1.0, beta=0.05, eta=0.1)
    r = ch.run(activations=[0.05, 0.05, 0.05], run_id="e2e-bcm-lo")
    assert r.weight is not None and r.initial_weight is not None
    assert r.weight <= r.initial_weight + 1e-9


def t_bcm_forgetting_decays_idle():
    ch = BCMShadowChannel(w_cap=1.0, beta=0.05, eta=0.5)
    warm = ch.run(activations=[0.9] * 5, run_id="e2e-bcm-decay")
    cooled = ch.run(
        activations=[0.0] * 20, run_id="e2e-bcm-decay", initial_weight=warm.weight
    )
    assert cooled.weight is not None and warm.weight is not None
    assert cooled.weight < warm.weight


def t_bcm_rejects_nonfinite():
    ch = BCMShadowChannel()
    r = ch.run(activations=[float("nan")], run_id="e2e-bcm-nan")
    assert r.status == "UNKNOWN"
    assert r.external_effects == ()


def t_hebbian_prune_below_threshold():
    ch = HebbianShadowChannel()
    r = ch.run(pair=("a", "b"), co_occurrences=1, absent_ticks=5000)
    assert r.strength is not None and r.strength < 0.005
    assert r.association_exists is False


def t_hebbian_replay_deterministic():
    r1 = HebbianShadowChannel().run(
        pair=("a", "b"), co_occurrences=3, absent_ticks=10, run_id="r"
    )
    r2 = HebbianShadowChannel().run(
        pair=("a", "b"), co_occurrences=3, absent_ticks=10, run_id="r"
    )
    assert r1.trace_digest == r2.trace_digest


def t_untrusted_cannot_write_association():
    ch = HebbianShadowChannel()
    r = ch.run(
        pair=("a", "b"),
        co_occurrences=1,
        absent_ticks=0,
        trust_level="untrusted",
    )
    assert r.association_written is False
    assert r.quarantined is True


CHECKS = [
    ("bcm-high-grows", t_bcm_threshold_high_grows),
    ("bcm-low-no-grow", t_bcm_low_activation_does_not_grow),
    ("bcm-forgetting", t_bcm_forgetting_decays_idle),
    ("bcm-nan-unknown", t_bcm_rejects_nonfinite),
    ("hebbian-prune", t_hebbian_prune_below_threshold),
    ("hebbian-deterministic", t_hebbian_replay_deterministic),
    ("hebbian-untrusted", t_untrusted_cannot_write_association),
]

failed = harness.run(CHECKS)
sys.exit(1 if failed else 0)
