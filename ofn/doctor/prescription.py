#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""prescription — validates the contract's `prescription_required.output_shape`.

LAB-DOCTOR-CONTRACT.yaml marks falsifiable prescriptions as PROPOSED_EXTENSION.
This module turns that shape into executable, test-enforced validation: a
prescription that does not carry every mandated field — including the
falsification condition and the rollback — is rejected with named violations.
Validation only; nothing is ever applied here.
"""
from __future__ import annotations

__all__ = ["ZONES", "PRESCRIPTION_KEYS", "COST_KEYS", "validate_prescription"]

ZONES = ("B1", "B2", "unresolved")
PRESCRIPTION_KEYS = (
    "observed_symptom",
    "causal_hypothesis",
    "proposed_mutation",
    "falsification_condition",
    "expected_cost",
    "rollback",
    "evidence_refs",
)
COST_KEYS = ("tokens", "calls", "risk_weight", "time_s")


def _nonempty(d: dict, key: str, out: list[str]) -> None:
    v = d.get(key)
    if not isinstance(v, str) or not v.strip():
        out.append(f"{key}: must be a non-empty string")


def validate_prescription(presc: dict) -> list[str]:
    """Return a list of contract violations ([] = valid)."""
    v: list[str] = []
    if not isinstance(presc, dict):
        return ["prescription: must be a mapping"]
    for key in PRESCRIPTION_KEYS:
        if key not in presc:
            v.append(f"{key}: required by contract output_shape")
    if v:
        return v
    _nonempty(presc, "observed_symptom", v)
    _nonempty(presc, "causal_hypothesis", v)
    _nonempty(presc, "falsification_condition", v)
    _nonempty(presc, "rollback", v)

    mut = presc.get("proposed_mutation")
    if not isinstance(mut, dict):
        v.append("proposed_mutation: must be a mapping")
    else:
        _nonempty(mut, "description", v)
        target = mut.get("target_path")
        if not isinstance(target, str) or not target.strip():
            v.append("proposed_mutation.target_path: must be a non-empty string")
        if mut.get("target_zone") not in ZONES:
            v.append(f"proposed_mutation.target_zone: must be one of {ZONES}")

    cost = presc.get("expected_cost")
    if not isinstance(cost, dict):
        v.append("expected_cost: must be a mapping")
    else:
        for k in COST_KEYS:
            val = cost.get(k)
            if not isinstance(val, (int, float)) or isinstance(val, bool) or val < 0:
                v.append(f"expected_cost.{k}: must be a non-negative number")

    refs = presc.get("evidence_refs")
    if not isinstance(refs, list) or not refs or not all(isinstance(r, str) and r for r in refs):
        v.append("evidence_refs: must be a non-empty list of strings")
    return v
