"""
Phase 6 -- eval harness (KB-08). OFFLINE.

Asserts the golden set passes with perfect gate metrics, AND that a deliberately
wrong expectation is detected as a regression (which is what fails CI).
"""
import os
import sys
import tempfile

_TMP_DB = tempfile.mkstemp(suffix="_brushline_p6.db")[1]
os.environ["BRUSHLINE_DB_PATH"] = _TMP_DB
os.environ["KILL_SWITCH_FILE"] = _TMP_DB + ".KILL"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["SERPER_API_KEY"] = ""
os.environ["ALLOWED_OPERATOR_CHAT_IDS"] = ""
os.environ["BUSINESS_NAME"] = "Sister Painting"
os.environ["BUSINESS_ABN"] = "11222333444"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evals.run_eval import evaluate, GOLDEN


def _check(label, cond):
    print(("PASS" if cond else "FAIL") + " :: " + label)
    if not cond:
        raise AssertionError(label)


def main():
    report, passed = evaluate(GOLDEN)
    _check("golden set passes (no regression)", passed is True)
    _check("status accuracy 100%", report["status_accuracy"] == 1.0)
    _check("zero false HARD_BLOCK", report["false_hard_block"] == 0)
    for dim, m in report["dims"].items():
        _check(f"{dim}: precision 1.0", m["precision"] == 1.0)
        _check(f"{dim}: recall 1.0", m["recall"] == 1.0)

    # Regression detection: flip one expected status -> harness must FAIL.
    mutated = []
    for case in GOLDEN:
        if case[0] == "lead_no_consent":       # really a HARD_BLOCK
            case = (case[0], case[1], case[2], case[3], "pass", set(), case[6])
        mutated.append(case)
    _, passed_bad = evaluate(mutated)
    _check("regression in gate is detected (harness fails)", passed_bad is False)

    print("\nALL EVAL (P6) CHECKS PASSED")


if __name__ == "__main__":
    try:
        main()
    finally:
        for p in (_TMP_DB, _TMP_DB + "-wal", _TMP_DB + "-shm", _TMP_DB + ".KILL"):
            try:
                os.remove(p)
            except OSError:
                pass
