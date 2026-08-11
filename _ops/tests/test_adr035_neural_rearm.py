#!/usr/bin/env python3
"""ADR-035 — re-arm NEURAL_LEARNED_APPLY (owner «هردو»).

Dual-mode:
  APPLY=0 → ADR-034 proposal/SHADOW (executable=False)
  APPLY=1 → fold + protective_halt/throttle with executable=True
Consumers (organism/brain_worker) set protective_skip only when executable.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("adr035-rearm")
_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "neural"), str(_OPS / "policy")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import wiring  # noqa: E402


def _env_clean():
    for k in (
        "OCTOPUS_NEURAL_LEARNED_APPLY",
        "OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL",
        "OCTOPUS_PAIN_THRESHOLD_CALIBRATED",
        "OCTOPUS_NEURAL_EFFECT_SHADOW",
    ):
        os.environ.pop(k, None)


def t_apply_off_stays_proposal_only():
    _env_clean()
    try:
        r = wiring.protective_override({"pain": {"level": 0.95}, "reflexes": []})
        assert r["action"] == "protective_proposal"
        assert r["override"] is False and r["executable"] is False
        assert r["shadow_alert"] is True
    finally:
        _env_clean()


def t_apply_on_high_pain_executable_halt():
    _env_clean()
    os.environ["OCTOPUS_NEURAL_LEARNED_APPLY"] = "1"
    try:
        r = wiring.protective_override({"pain": {"level": 0.95}, "reflexes": []})
        assert r["action"] == "protective_halt", r
        assert r["override"] is True and r["executable"] is True
        assert r["suppressible"] is False
        assert r["shadow_alert"] is False
    finally:
        _env_clean()


def t_apply_on_folds_learned_to_halt():
    _env_clean()
    os.environ["OCTOPUS_NEURAL_LEARNED_APPLY"] = "1"
    try:
        # 0.3 + 0.9*0.5 = 0.75 > 0.7
        r = wiring.protective_override({
            "pain": {"level": 0.3},
            "reflexes": [],
            "brain_inputs": {"learned_pressure": 0.9, "learned_top_signal": "k1"},
        })
        assert r["action"] == "protective_halt", r
        assert r["executable"] is True and r["override"] is True
        assert "learned" in (r.get("reason") or "").lower() or "0.7" in (r.get("reason") or "")
    finally:
        _env_clean()


def t_apply_on_critical_throttle_executable():
    _env_clean()
    os.environ["OCTOPUS_NEURAL_LEARNED_APPLY"] = "1"
    try:
        r = wiring.protective_override({
            "pain": {"level": 0.2},
            "reflexes": [{"name": "sigma-throttle", "triggered": True, "severity": "critical"}],
        })
        assert r["action"] == "throttle", r
        assert r["executable"] is True and r["override"] is True
    finally:
        _env_clean()


def t_apply_on_unknown_never_executes():
    _env_clean()
    os.environ["OCTOPUS_NEURAL_LEARNED_APPLY"] = "1"
    try:
        r = wiring.protective_override({"pain": {"level": float("nan")}, "reflexes": []})
        assert r["action"] == "none"
        assert r["executable"] is False and r["override"] is False
    finally:
        _env_clean()


def t_organism_brain_honor_executable_only():
    org = (_OPS / "organism.py").read_text(encoding="utf-8")
    bw = (_OPS / "brain_worker.py").read_text(encoding="utf-8")
    assert '_protective_skip = True' in org
    assert 'self.protective_skip = True' in bw
    assert 'get("executable")' in org and 'get("executable")' in bw
    assert "SHADOW_ALERT neural" in org and "SHADOW_ALERT neural" in bw
    assert "NEURAL OVERRIDE" in org and "NEURAL OVERRIDE" in bw


def t_flags_cmd_apply_armed():
    flags = (_OPS / "OCTOPUS-flags.cmd").read_text(encoding="utf-8", errors="replace")
    assert "set OCTOPUS_NEURAL_LEARNED_APPLY=1" in flags
    assert "ADR-035" in flags


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_adr035_neural_rearm: "
          f"{len(checks) - failed}/{len(checks)}")
    raise SystemExit(failed)
