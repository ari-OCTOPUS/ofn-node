#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pulse_shadow_compare.py — shadow divergence for pulse arbiter (additive).

Compares production period vs shadow/advisory period WITHOUT changing
age_tick, hash-chain, or live period. Flag: OCTOPUS_WIRE_PULSE_ARBITER_SHADOW
(default OFF). Evidence level SHADOW until 7-day gate + owner vote.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
SINK = _OPS / "state" / "pulse" / "arbiter-shadow-divergence.jsonl"
FLAG = "OCTOPUS_WIRE_PULSE_ARBITER_SHADOW"
POLICY_VERSION = "pulse-shadow-compare.v1"


@dataclass(frozen=True)
class PulseShadowRecord:
    run_id: str
    tick: int
    production_period: float
    shadow_period: float
    abs_difference: float
    pct_difference: float
    inputs_digest: str
    policy_version: str = POLICY_VERSION
    evidence_level: str = "SHADOW"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def shadow_enabled() -> bool:
    return os.environ.get(FLAG, "0") == "1"


def shadow_compare(
    production_period: float,
    shadow_period: float,
    run_id: str,
    tick: int,
    inputs_digest: str,
) -> PulseShadowRecord:
    denominator = max(abs(float(production_period)), 1e-9)
    return PulseShadowRecord(
        run_id=str(run_id),
        tick=int(tick),
        production_period=float(production_period),
        shadow_period=float(shadow_period),
        abs_difference=abs(float(production_period) - float(shadow_period)),
        pct_difference=abs(float(production_period) - float(shadow_period)) / denominator,
        inputs_digest=str(inputs_digest)[:64],
    )


def inputs_digest_from(obj: dict | None) -> str:
    raw = json.dumps(obj or {}, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def record_divergence(
    *,
    production_period: float,
    shadow_period: float,
    run_id: str,
    tick: int,
    inputs: dict | None = None,
) -> PulseShadowRecord | None:
    """Append divergence if flag on. Never mutates production period."""
    if not shadow_enabled():
        return None
    dig = inputs_digest_from(inputs)
    rec = shadow_compare(production_period, shadow_period, run_id, tick, dig)
    row = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        **rec.as_dict(),
        "metrics": {
            "octopus.pulse.shadow_divergence_pct": rec.pct_difference,
            "octopus.pulse.shadow_divergence_abs": rec.abs_difference,
        },
    }
    try:
        SINK.parent.mkdir(parents=True, exist_ok=True)
        with SINK.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass
    return rec
