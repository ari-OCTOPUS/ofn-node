"""The inert wire flag must stay deleted (F-10 lock, 2026-09-03).

OFN_WIRE_OUTBOUND / wire_outbound never gated a single send — config.py:78-81
said so itself — while the live node.env carried =1 since ~Aug 22. A flag an
observer mistakes for a control is worse than no flag. This pins the removal
against quiet re-introduction."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_config_has_no_wire_outbound_field_or_alias() -> None:
    src = (ROOT / "ofn" / "config.py").read_text(encoding="utf-8")
    assert "wire_outbound" not in re.sub(r"#.*", "", src), \
        "wire_outbound reappeared in code — decorative wire flags are banned"


def test_no_production_module_reads_the_alias() -> None:
    for pkg in ("ofn", "octopus_survival", "octopus_observation",
                "octopus_recovery"):
        base = ROOT / pkg
        if not base.is_dir():
            continue
        for p in base.rglob("*.py"):
            src = p.read_text(encoding="utf-8")
            code = re.sub(r'(""".*?"""|\'\'\'.*?\'\'\'|#.*)', "", src,
                          flags=re.S)
            assert "OFN_WIRE_OUTBOUND" not in code, \
                f"{p.relative_to(ROOT)} reads the deleted alias"
