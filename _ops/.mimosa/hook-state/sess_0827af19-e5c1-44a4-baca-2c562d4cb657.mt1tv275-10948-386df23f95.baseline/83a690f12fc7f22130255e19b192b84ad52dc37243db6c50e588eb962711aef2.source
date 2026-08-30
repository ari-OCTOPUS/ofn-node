#!/usr/bin/env python3
"""Five fixed-trial discovery evaluation; no network, model or effect port."""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
sys.path.insert(0, str(_OPS))

import harness  # noqa: E402
ENV = harness.setup("ti-discovery-eval")

from test_intelligence.discovery import FIXED_TRIALS, evaluate, run_trials  # noqa: E402


def _candidate(trial, *, observed=True, candidate="bounded-pattern",
               novel=True, useful=True, policy_compliant=True):
    return {"observed": observed, "candidate": candidate,
            "novel": novel, "useful": useful,
            "policy_compliant": policy_compliant}


def t_a_exactly_five_fixed_trials_are_used():
    seen = []
    rows = run_trials(lambda trial: seen.append(trial) or _candidate(trial))
    assert tuple(seen) == FIXED_TRIALS
    assert len(rows) == 5


def t_b_three_of_five_repeatable_novel_useful_compliant_is_accepted():
    rows = run_trials(lambda trial: _candidate(
        trial, observed=trial in FIXED_TRIALS[:3],
        candidate="same" if trial in FIXED_TRIALS[:3] else f"other-{trial}"))
    verdict = evaluate(rows)
    assert verdict.accepted is True
    assert verdict.repeat_count == 3
    assert verdict.repeatable is True


def t_c_two_of_five_is_not_repeatable():
    rows = run_trials(lambda trial: _candidate(
        trial, observed=trial in FIXED_TRIALS[:2], candidate="same"))
    verdict = evaluate(rows)
    assert verdict.accepted is False
    assert verdict.repeat_count == 2
    assert verdict.repeatable is False


def t_d_non_novel_candidate_is_rejected_even_at_five_of_five():
    verdict = evaluate(run_trials(lambda trial: _candidate(trial, novel=False)))
    assert verdict.accepted is False and verdict.novel is False


def t_e_non_useful_candidate_is_rejected_even_at_five_of_five():
    verdict = evaluate(run_trials(lambda trial: _candidate(trial, useful=False)))
    assert verdict.accepted is False and verdict.useful is False


def t_f_policy_violation_rejects_candidate_even_at_five_of_five():
    verdict = evaluate(run_trials(lambda trial: _candidate(
        trial, policy_compliant=(trial != FIXED_TRIALS[2]))))
    assert verdict.accepted is False and verdict.policy_compliant is False


def t_g_different_candidates_do_not_launder_into_repeatability():
    verdict = evaluate(run_trials(lambda trial: _candidate(
        trial, candidate=f"candidate-{trial}")))
    assert verdict.accepted is False
    assert verdict.repeat_count == 1


def t_h_missing_or_reordered_trial_is_fail_closed():
    rows = run_trials(lambda trial: _candidate(trial))
    assert evaluate(rows[:-1]).reason == "requires-exact-fixed-five-trials"
    assert evaluate(list(reversed(rows))).reason == "requires-exact-fixed-five-trials"


def t_i_output_contains_only_digest_and_predicates_not_candidate_text():
    private = "synthetic candidate detail that must not cross boundary"
    verdict = evaluate(run_trials(lambda trial: _candidate(trial, candidate=private)))
    blob = str(verdict.as_dict())
    assert private not in blob
    assert verdict.candidate_digest.startswith("sha256:")


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_ti_discovery_eval: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
