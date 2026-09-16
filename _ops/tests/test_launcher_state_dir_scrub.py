#!/usr/bin/env python3
"""Live launchers must not inherit a fixture OCTOPUS_STATE_DIR."""
from __future__ import annotations

import sys
from pathlib import Path

import harness

ENV = harness.setup("launcher-state-dir-scrub")
_OPS = Path(__file__).resolve().parent.parent


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")


def _before(source: str, first: str, second: str) -> None:
    assert first in source, f"missing {first!r}"
    assert second in source, f"missing {second!r}"
    assert source.index(first) < source.index(second), f"{first!r} must precede {second!r}"


def t_a_center_launcher_scrubs_before_python():
    source = _text(_OPS / "telegram_center" / "RUN-TG-CENTER.bat")
    _before(source, "set OCTOPUS_STATE_DIR=", "python -X utf8 telegram_center\\center.py")


def t_b_organism_launcher_scrubs_before_python():
    source = _text(_OPS / "RUN-ORGANISM.bat")
    _before(source, "set OCTOPUS_STATE_DIR=", "python -X utf8 organism.py")


def t_c_restart_script_scrubs_before_target_dispatch():
    source = _text(_OPS / "RESTART-PROCESS.ps1")
    _before(source, "Remove-Item Env:OCTOPUS_STATE_DIR", "$cfg = @{")


def t_d_restart_script_does_not_print_inherited_value():
    source = _text(_OPS / "RESTART-PROCESS.ps1")
    assert '"NOTE: unsetting inherited OCTOPUS_STATE_DIR=" + $env:OCTOPUS_STATE_DIR' not in source


if __name__ == "__main__":
    checks = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_launcher_state_dir_scrub: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
