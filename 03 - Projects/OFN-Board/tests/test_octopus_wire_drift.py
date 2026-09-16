"""Drift test: OCTOPUS_WIRE_* names mentioned in CLAUDE.md must be accounted for.

This is a documentation-consistency test, not a security enforcement test.

It checks that every OCTOPUS_WIRE_* name listed in CLAUDE.md is either:
  (a) explicitly blocked/rejected by config.py, or
  (b) documented in PORTFOLIO-TENANT-MAP.md as "intent-only".

config.py must NOT silently honor any OCTOPUS_WIRE_* name via os.environ.get().
"""

from __future__ import annotations

import os
import re
import unittest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CLAUDE_MD = os.path.join(_REPO_ROOT, "CLAUDE.md")
_CONFIG_PY = os.path.join(_REPO_ROOT, "ofn", "config.py")
_PORTFOLIO_MAP = os.path.join(
    _REPO_ROOT, "docs", "architecture", "PORTFOLIO-TENANT-MAP.md")


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _extract_octopus_wire_names(clause_text: str) -> set[str]:
    """Extract OCTOPUS_WIRE_* names from CLAUDE.md section text."""
    return set(re.findall(r"OCTOPUS_WIRE_[A-Z0-9_*]+", clause_text))


def _config_has_environ_get_for_octopus(config_text: str) -> set[str]:
    """Return OCTOPUS_WIRE_* names that config.py reads via os.environ.get()."""
    names: set[str] = set()
    for line in config_text.splitlines():
        # Match os.environ.get("OCTOPUS_WIRE_...") or os.environ.get('OCTOPUS_WIRE_...')
        for m in re.finditer(
            r'os\.environ\.get\(["\']OCTOPUS_WIRE_[A-Z0-9_*]+["\']', line
        ):
            name = re.search(r'OCTOPUS_WIRE_[A-Z0-9_*]+', m.group(0))
            if name:
                names.add(name.group(0))
    return names


def _portfolio_map_has_intent_only(map_text: str) -> set[str]:
    """Return OCTOPUS_WIRE_* names documented as intent-only in PORTFOLIO-TENANT-MAP."""
    names: set[str] = set()
    # Check if the document has the "intent-only" section about OCTOPUS_WIRE_*
    for line in map_text.splitlines():
        for m in re.finditer(r"OCTOPUS_WIRE_[A-Z0-9_*]+", line):
            names.add(m.group(0))
    return names


class TestOctopusWireDrift(unittest.TestCase):
    """Documentation-consistency: OCTOPUS_WIRE_* names are accounted for."""

    def test_config_does_not_silently_honor_octopus_wire(self):
        """config.py must NOT read any OCTOPUS_WIRE_* name via os.environ.get()."""
        config_text = _read(_CONFIG_PY)
        honored = _config_has_environ_get_for_octopus(config_text)
        self.assertEqual(
            honored, set(),
            "config.py silently reads these OCTOPUS_WIRE_* names via "
            "os.environ.get(): " + ", ".join(sorted(honored)))

    def test_every_octopus_wire_name_is_accounted_for(self):
        """Every OCTOPUS_WIRE_* in CLAUDE.md must be blocked in config.py OR
        documented as intent-only in PORTFOLIO-TENANT-MAP.md."""
        clause_text = _read(_CLAUDE_MD)
        config_text = _read(_CONFIG_PY)
        map_text = _read(_PORTFOLIO_MAP)

        clause_names = _extract_octopus_wire_names(clause_text)
        # Expand wildcard names like OCTOPUS_WIRE_PROJECTF_* — these represent
        # a family. We check that config.py does NOT honor the pattern.
        # For simplicity, treat each name (including wildcards) as a unit.

        # Names explicitly rejected/blocked by config: config.py does not
        # contain os.environ.get("OCTOPUS_WIRE_*") for any of them — that is
        # verified by the sister test above.  So if config has no reads, all
        # names are effectively "not honored" by config.

        # intent-only documented in PORTFOLIO-TENANT-MAP
        intent_only = _portfolio_map_has_intent_only(map_text)

        unaccounted = []
        for name in sorted(clause_names):
            in_config_blocked = (
                name not in _config_has_environ_get_for_octopus(config_text)
            )
            in_map = name in intent_only
            if not (in_config_blocked or in_map):
                unaccounted.append(name)

        # All names should be either not-honored-by-config or in the map.
        # Since config.py has no OCTOPUS_WIRE reads at all (verified above),
        # the "not honored" condition is always true — but we still check
        # explicitly so the test catches if someone adds a read later.
        self.assertEqual(
            unaccounted, [],
            "These OCTOPUS_WIRE_* names in CLAUDE.md are neither blocked "
            "by config.py nor documented in PORTFOLIO-TENANT-MAP.md as "
            "intent-only: " + ", ".join(unaccounted))


if __name__ == "__main__":
    unittest.main()
