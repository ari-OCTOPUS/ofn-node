"""GOV-V6 review gate — the two invariants of the 2026-09-03 owner ruling.

Rule (owner ruling, GOV-V6-two-reviewer-rule-20260903):
  a valid approval is one from Elahe-z OR aram-ui, never the PR author,
  never a bot/App account. Either one alone is sufficient.

The gate itself is JavaScript inside .github/workflows/independent-review-gate.yml.
These tests do two things:
  1. exercise the rule itself via a faithful Python mirror (the executable spec),
     including the five mandatory scenarios of GOV-V6 §6;
  2. lock the workflow file and CODEOWNERS to that rule, so the YAML cannot
     drift from the tested spec without a red test (same pattern as the repo's
     other content-pinning hygiene tests).
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WORKFLOW = REPO / ".github" / "workflows" / "independent-review-gate.yml"
CODEOWNERS = REPO / ".github" / "CODEOWNERS"

VALID_REVIEWERS = ("Elahe-z", "aram-ui")


def gov_v6_approvers(reviews: dict[str, str], author: str) -> list[str]:
    """Mirror of the workflow's filter — the executable spec of GOV-V6."""
    return sorted(
        login
        for login, state in reviews.items()
        if state == "APPROVED"
        and login != author
        and not login.endswith("[bot]")
        and login in VALID_REVIEWERS
    )


# --- GOV-V6 §6: the five mandatory scenarios -------------------------------


def test_author_self_approval_fails() -> None:
    assert gov_v6_approvers({"ari322": "APPROVED"}, author="ari322") == []


def test_bot_approval_fails() -> None:
    assert gov_v6_approvers({"cursor[bot]": "APPROVED"}, author="ari322") == []


def test_aram_ui_approval_passes() -> None:
    assert gov_v6_approvers({"aram-ui": "APPROVED"}, author="ari322") == ["aram-ui"]


def test_elahe_approval_passes() -> None:
    assert gov_v6_approvers({"Elahe-z": "APPROVED"}, author="ari322") == ["Elahe-z"]


def test_aram_ui_cannot_self_approve() -> None:
    assert gov_v6_approvers({"aram-ui": "APPROVED"}, author="aram-ui") == []


def test_commented_reviews_never_count() -> None:
    reviews = {"Elahe-z": "COMMENTED", "aram-ui": "COMMENTED"}
    assert gov_v6_approvers(reviews, author="ari322") == []


# --- content locks: workflow + CODEOWNERS must implement exactly this rule -


def test_workflow_pins_the_v6_invariants() -> None:
    yaml_text = WORKFLOW.read_text(encoding="utf-8")
    assert "const VALID_REVIEWERS = ['Elahe-z', 'aram-ui'];" in yaml_text
    assert "!login.endsWith('[bot]')" in yaml_text
    assert "login !== author" in yaml_text
    assert "Bot/App approvals do not satisfy this check" in yaml_text


def test_codeowners_is_the_v6_two_reviewer_line() -> None:
    lines = [
        ln.strip()
        for ln in CODEOWNERS.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.startswith("#")
    ]
    assert lines == ["* @Elahe-z @aram-ui"]
