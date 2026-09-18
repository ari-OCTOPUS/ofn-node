"""Council log append + 50-cap. No correlation invented."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from council_decision_log import MODELS, TARGET_N, append_decision, count, remaining  # noqa: E402


def test_append_two_and_count(tmp_path: Path) -> None:
    log = tmp_path / "decisions.jsonl"
    votes = {m: "absent" for m in MODELS}
    votes["GLM"] = "agree"
    votes["DeepSeek"] = "dissent"
    append_decision(log, {"decision_id": "d1", "votes": votes, "outcome": "unresolved"})
    append_decision(log, {"decision_id": "d2", "votes": votes, "outcome": "unresolved"})
    assert count(log) == 2
    assert remaining(log) == TARGET_N - 2


def test_missing_model_rejected(tmp_path: Path) -> None:
    log = tmp_path / "decisions.jsonl"
    try:
        append_decision(
            log,
            {"decision_id": "d1", "votes": {"GLM": "agree"}, "outcome": "unresolved"},
        )
    except ValueError as e:
        assert "missing-vote" in str(e)
    else:
        raise AssertionError("must reject incomplete votes")
    assert count(log) == 0


if __name__ == "__main__":
    import tempfile

    failed = 0
    with tempfile.TemporaryDirectory() as d:
        try:
            test_append_two_and_count(Path(d))
            print("PASS test_append_two_and_count")
        except Exception as e:
            failed += 1
            print("FAIL test_append_two_and_count", e)
    with tempfile.TemporaryDirectory() as d:
        try:
            test_missing_model_rejected(Path(d))
            print("PASS test_missing_model_rejected")
        except Exception as e:
            failed += 1
            print("FAIL test_missing_model_rejected", e)
    raise SystemExit(1 if failed else 0)
