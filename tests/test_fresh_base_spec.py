"""require-fresh-base — executable spec mirror + content pins (F-06/F-07/F-08).

#73 and #108 sat on bases older than the GOV-V6 rule and thereby executed the
OLD gate. The workflow now carries a `require-fresh-base` job; this module
mirrors its decision function as pure Python (so the rule is testable without
GitHub) and pins the workflow content so the YAML cannot drift from the spec
without a red test (same pattern as test_gov_v6_gate.py)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / ".github" / "workflows" / "independent-review-gate.yml"


def fresh_base_verdict(compare_status: str, behind_by: int = 0) -> tuple[bool, str]:
    """Pure mirror of the job's decision: ('ahead'|'identical') pass; else fail.

    diverged/behind = the PR does not contain the current base head = it runs
    pre-rule gates = red until synced.
    """
    if compare_status in {"ahead", "identical"}:
        return True, f"fresh base: {compare_status}"
    return False, (f"Stale base: {behind_by} commit(s) behind — "
                   "run `git fetch origin && git merge origin/<base>` and push")


def test_passes_when_ahead_or_identical() -> None:
    assert fresh_base_verdict("ahead")[0]
    assert fresh_base_verdict("identical")[0]


def test_fails_when_behind_or_diverged() -> None:
    ok, msg = fresh_base_verdict("behind", behind_by=4)
    assert not ok and "4" in msg
    ok, msg = fresh_base_verdict("diverged", behind_by=0)
    assert not ok


def test_gate_workflow_carries_the_fresh_base_job() -> None:
    src = GATE.read_text(encoding="utf-8")
    assert "require-fresh-base:" in src
    assert "compareCommits" in src
    assert "Stale base" in src
    # a green must never read as approval — the job's failure speaks for itself
    assert "cancel-in-progress: true" in src


def test_all_pull_request_workflows_cancel_superseded_runs() -> None:
    wf_dir = ROOT / ".github" / "workflows"
    pr_workflows = [p for p in wf_dir.glob("*.yml")
                    if "pull_request" in p.read_text(encoding="utf-8")]
    assert len(pr_workflows) >= 5
    for p in pr_workflows:
        src = p.read_text(encoding="utf-8")
        assert "concurrency:" in src, f"{p.name} lacks a concurrency group (F-07/F-08)"
        assert "cancel-in-progress: true" in src, p.name
