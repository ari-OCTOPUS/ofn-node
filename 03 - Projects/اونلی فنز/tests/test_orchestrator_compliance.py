#!/usr/bin/env python3
"""test_orchestrator_compliance.py — regression for the compliance-bypass fix.

Before the fix, orchestrator.py:104 hardcoded all COMPLIANCE_RULES + ETHICS_RULES
to True, which made the guard in dual_brain_v3._checks_pass() always succeed —
a safety bypass (debug report 2026-07-19 §3.2; fixed 2026-07-20 Forced Completion
Sprint, DL-2026-07-20-TESTS).

This test verifies:
  1. When the manifest is present and rules are locked, checks build correctly.
  2. When the manifest is missing/corrupt, checks fail-close (all False).
  3. A rule without a manifest anchor fails closed (unknown rule → False).
  4. The guard actually blocks when a rule is False.
  5. tick() returns a blocked TickResult (no thoughts/messages) when checks fail.

No PII, no network, stdlib-only. Runs from the project root:
    python -m pytest tests/test_orchestrator_compliance.py -q
"""
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parent
for _p in [str(_PROJ), str(_PROJ / "brain")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import orchestrator  # noqa: E402
from dual_brain_v3 import _checks_pass, COMPLIANCE_RULES, ETHICS_RULES  # noqa: E402


def test_manifest_present_yields_locked_checks():
    """When PROJECT-F-CONTROL-MANIFEST.json is intact, all 6 compliance flags
    must be True (rules are still locked)."""
    checks = orchestrator._load_compliance_checks()
    assert set(checks.keys()) == set(COMPLIANCE_RULES + ETHICS_RULES)
    for r in COMPLIANCE_RULES:
        assert checks[r] is True, f"{r} should be True with manifest intact"
    assert _checks_pass(checks) is True


def test_manifest_missing_fail_closes():
    """If the manifest path is unreadable, no rule may be True (fail-closed)."""
    orig = orchestrator._MANIFEST
    try:
        orchestrator._MANIFEST = _PROJ / "NONEXISTENT-MANIFEST.json"
        checks = orchestrator._load_compliance_checks()
        assert all(v is False for v in checks.values()), \
            "missing manifest must fail-close every check"
        assert _checks_pass(checks) is False, \
            "guard must block when manifest is absent"
    finally:
        orchestrator._MANIFEST = orig


def test_manifest_corrupt_fail_closes():
    """A corrupt (invalid JSON) manifest must also fail-close."""
    orig = orchestrator._MANIFEST
    bad = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write("{ this is not valid json,,,")
            bad = Path(f.name)
        orchestrator._MANIFEST = bad
        checks = orchestrator._load_compliance_checks()
        assert all(v is False for v in checks.values())
        assert _checks_pass(checks) is False
    finally:
        orchestrator._MANIFEST = orig
        if bad is not None:
            try:
                bad.unlink()
            except OSError:
                pass


def test_manifest_rules_removed_fail_closes():
    """A manifest whose hard_rules_locked lost an anchor must fail that rule."""
    orig = orchestrator._MANIFEST
    bad = None
    try:
        stripped = {
            "hard_rules_locked": ["2: geo", "3: pay", "4: tos", "5: privacy",
                                  "8: consent"],   # rule 1 (feet-only) missing!
            "hard_rules_mutability": "immutable without explicit human verdict.",
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(stripped, f)
            bad = Path(f.name)
        orchestrator._MANIFEST = bad
        checks = orchestrator._load_compliance_checks()
        assert checks["faceless"] is False
        assert checks["feet_only"] is False
        assert checks["no_explicit"] is False
        assert checks["geo_block_iran"] is True
        assert _checks_pass(checks) is False
    finally:
        orchestrator._MANIFEST = orig
        if bad is not None:
            try:
                bad.unlink()
            except OSError:
                pass


def test_unknown_rule_fails_closed():
    """A brain rule with no manifest anchor must be False (unknown rule)."""
    orig_anchor = orchestrator._RULE_ANCHORS.pop("faceless")
    try:
        checks = orchestrator._load_compliance_checks()
        assert checks["faceless"] is False, "unmapped rule must fail closed"
        assert _checks_pass(checks) is False
    finally:
        orchestrator._RULE_ANCHORS["faceless"] = orig_anchor


def test_guard_still_blocks_on_violation():
    """Sanity: the guard in dual_brain_v3 must still block if any rule is False."""
    checks = {r: True for r in COMPLIANCE_RULES + ETHICS_RULES}
    assert _checks_pass(checks) is True
    checks["faceless"] = False
    assert _checks_pass(checks) is False


def test_tick_blocked_when_manifest_missing(tmp_path, monkeypatch):
    """tick() must return mode='blocked_compliance' with zero advisory output
    when the manifest is unreadable — no thoughts, no messages."""
    monkeypatch.setattr(orchestrator, "_BRAIN_STATE", tmp_path)
    monkeypatch.setenv("PF_STUDIO_DIR", str(tmp_path))
    orig = orchestrator._MANIFEST
    try:
        orchestrator._MANIFEST = tmp_path / "NOPE.json"

        class _NeverBrain:
            def think_and_communicate(self, **_kw):  # pragma: no cover
                raise AssertionError("brain must not run when compliance blocked")

        orch = orchestrator.PFOrchestrator(
            studio=SimpleNamespace(draft_count=0),
            brain=_NeverBrain(),
            acquisition=SimpleNamespace(
                memory=SimpleNamespace(learning_confidence=lambda: 0.0,
                                       tag_performance=lambda: {})),
            data_dir=tmp_path)
        result = orch.tick()
        assert result.mode == "blocked_compliance"
        assert result.thoughts == []
        assert result.messages == []
        assert result.advisory_only is True
    finally:
        orchestrator._MANIFEST = orig


if __name__ == "__main__":
    test_manifest_present_yields_locked_checks()
    test_manifest_missing_fail_closes()
    test_manifest_corrupt_fail_closes()
    test_manifest_rules_removed_fail_closes()
    test_unknown_rule_fails_closed()
    test_guard_still_blocks_on_violation()
    print("OK: orchestrator compliance regression — direct run passed "
          "(tick test needs pytest fixtures)")
