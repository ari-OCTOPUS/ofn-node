"""
Completeness tests for the research-spec-compiler.

Runs with plain `python -m pytest` from the project root, or standalone via
`python tests/test_specs_and_registry.py` (no pytest needed — see __main__).
Covers: (1) every real spec passes the 5 gates; the intentional failures fail;
(2) every registered real experiment is importable and returns a well-formed
(conditions, primary) pair whose primary names an actual condition; (3) the
harness invariants the ADRs rely on (hard error on unknown primary; failure
predicate; decision bands).
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from spec_compiler.model import load_spec                       # noqa: E402
from spec_compiler.validator import validate                    # noqa: E402
from spec_compiler.harness import (                             # noqa: E402
    Condition, check_failure, decide, run_spec)

SPECS_DIR = os.path.join(_ROOT, "specs")

# specs that MUST pass all blocker gates
REAL_SPECS = [
    "debate_extraction", "wm_abstraction", "wm_abstraction_v2",
    "drake_kernels", "geometry_abstraction", "homeostasis",
    "consolidation", "hybrid_organism",
    # wave-2 hypotheses
    "social_mirror", "comparison_metacog", "prospective_memory",
    "memory_policy", "causal_selfmodel", "control_signals",
    # final corpus experiments
    "adaptive_forgetting", "retrieve_compute",
    # completion wave: geometry substrates + v2 follow-ups
    "ontology_shift", "multimetric_memory", "attractor_memory",
    "comparison_metacog_v2", "adaptive_forgetting_v2",
]
# specs that MUST fail (by design)
BROKEN_SPECS = ["drake_multiverse", "_broken_example"]


def _spec(name):
    for ext in (".yaml", ".yml", ".json"):
        p = os.path.join(SPECS_DIR, name + ext)
        if os.path.exists(p):
            return load_spec(p)
    raise AssertionError(f"spec not found: {name}")


def test_real_specs_pass():
    for name in REAL_SPECS:
        rep = validate(_spec(name))
        assert rep.ok, f"{name} should PASS but blocked: " \
            f"{[g.id for g in rep.blockers if not g.ok]}"


def test_broken_specs_fail():
    for name in BROKEN_SPECS:
        rep = validate(_spec(name))
        assert not rep.ok, f"{name} should FAIL the gates but passed"


def test_real_registry_wellformed():
    from experiments import REGISTRY_REAL
    assert REGISTRY_REAL, "real registry is empty"
    for name, fn in REGISTRY_REAL.items():
        conditions, primary = fn()
        assert isinstance(conditions, list) and len(conditions) >= 1, \
            f"{name}: needs >=1 condition"
        assert all(isinstance(c, Condition) for c in conditions), \
            f"{name}: non-Condition in conditions"
        names = [c.name for c in conditions]
        assert primary in names, \
            f"{name}: primary '{primary}' not among conditions {names}"
        # every real experiment must have a spec of the same name that PASSes
        rep = validate(_spec(name))
        assert rep.ok, f"{name}: real experiment lacks a passing spec"


def test_harness_unknown_primary_raises():
    spec = _spec("wm_abstraction")
    conds = [Condition("a", lambda rng: 0.5), Condition("b", lambda rng: 0.6)]
    raised = False
    try:
        run_spec(spec, conds, primary="does_not_exist", seeds=1)
    except ValueError:
        raised = True
    assert raised, "run_spec must hard-error on an unknown primary condition"


def test_decision_bands_and_failure():
    # a canonical rule: <0.4 DISCARD, [0.4,0.7) OPTIMIZE, >=0.7 INTEGRATE
    rule = {"rules": [{"max": 0.4, "verdict": "DISCARD"},
                      {"min": 0.4, "max": 0.7, "verdict": "OPTIMIZE"},
                      {"min": 0.7, "verdict": "INTEGRATE"}]}
    assert decide(0.30, rule) == "DISCARD"
    assert decide(0.55, rule) == "OPTIMIZE"
    assert decide(0.90, rule) == "INTEGRATE"
    fc = {"metric": "m", "op": "<", "threshold": 0.4}
    assert check_failure(0.3, fc) is True
    assert check_failure(0.5, fc) is False


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {fn.__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} tests passed")
    sys.exit(1 if failed else 0)
