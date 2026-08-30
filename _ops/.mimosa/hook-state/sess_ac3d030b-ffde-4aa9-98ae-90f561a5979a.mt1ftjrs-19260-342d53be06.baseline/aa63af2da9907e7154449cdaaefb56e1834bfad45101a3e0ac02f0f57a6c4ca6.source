#!/usr/bin/env python3
"""test_d2_halt_coverage — D2: every python beat/loop honors the canonical hard-halt.

Two guards:
 1. STATIC (regression-proof): every `*_beat / *_tick / *_cycle` in wiring.py references a
    canonical halt gate (opslib.halted/master_halted/STOP_ORGANISM/force_closed/_protective_skip
    or the shared `_tg_halt_reason` helper). A future beat added without one FAILS here.
 2. FUNCTIONAL: the shared `_tg_halt_reason()` returns a reason under HALT-ALL and under the
    architect STOP, and None when clear — proving the beats that route through it (and the
    canonical oracle they share) actually short-circuit on the global boundary.

Static-parse only for guard #1 (no import, no side-effects). Hermetic, no live DB/network.
Run: python -X utf8 test_d2_halt_coverage.py
"""
import ast
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
import harness   # noqa: E402
ENV = harness.setup("d2-halt-coverage")
import opslib    # noqa: E402
import wiring     # noqa: E402

_FAILED = 0
_HALT_MARKERS = ("halt", "STOP_ORGANISM", "force_closed", "_protective_skip",
                 "master_halted", "_tg_halt", "stopped(")


def check(name, cond):
    global _FAILED
    print(("PASS" if cond else "FAIL"), "-", name)
    if not cond:
        _FAILED += 1


def _set(path, on):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("test", "utf-8") if on else path.unlink(missing_ok=True)


def t_a_every_beat_has_a_halt_gate():
    """گاردِ static: هیچ beat بدونِ ارجاعِ halt نباشد (ضدِ regression)."""
    src = (_HERE.parent / "wiring.py").read_text("utf-8")
    tree = ast.parse(src)
    missing = []
    total = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.endswith(("_beat", "_tick", "_cycle")):
            total += 1
            body = ast.get_source_segment(src, node) or ""
            if not any(m in body for m in _HALT_MARKERS):
                missing.append(node.name)
    print(f"    (audited {total} beats/ticks/cycles in wiring.py)")
    check(f"every wiring beat references a canonical halt gate — {total} audited, "
          f"{len(missing)} missing", not missing)
    if missing:
        print("    MISSING halt gate:", ", ".join(missing))


def t_b_tg_halt_reason_honors_halt_all():
    _set(opslib.HALT_ALL, False)
    _set(opslib.STOP_ORGANISM, False)
    check("clear → _tg_halt_reason() is None", wiring._tg_halt_reason() is None)
    _set(opslib.HALT_ALL, True)
    try:
        check("HALT-ALL → _tg_halt_reason() returns a reason (not None)",
              bool(wiring._tg_halt_reason()))
    finally:
        _set(opslib.HALT_ALL, False)


def t_c_tg_halt_reason_honors_stop_organism():
    _set(opslib.STOP_ORGANISM, True)
    try:
        check("STOP-ORGANISM → _tg_halt_reason() returns 'STOP'",
              wiring._tg_halt_reason() == "STOP")
    finally:
        _set(opslib.STOP_ORGANISM, False)


def t_d_cockpit_beat_skips_under_halt():
    """functional: نمایندهٔ effect-capable beat زیرِ HALT-ALL کار نمی‌کند."""
    os.environ["OCTOPUS_TG_EXEC"] = "1"          # flag on so it would otherwise run
    _set(opslib.HALT_ALL, True)
    try:
        r = wiring.cockpit_requests_beat()
        check("cockpit_requests_beat under HALT-ALL → skipped='halt' (no queue processing)",
              isinstance(r, dict) and r.get("skipped") == "halt")
    finally:
        _set(opslib.HALT_ALL, False)
        os.environ.pop("OCTOPUS_TG_EXEC", None)


def t_e_master_halted_is_the_single_oracle():
    """canonical oracle: HALT-ALL و architect STOP هر دو از master_halted می‌آیند."""
    _set(opslib.HALT_ALL, False)
    _set(opslib.STOP_ARCHITECT, False)
    check("clear → master_halted() None", opslib.master_halted() is None)
    _set(opslib.HALT_ALL, True)
    try:
        check("HALT-ALL → master_halted() truthy", bool(opslib.master_halted()))
    finally:
        _set(opslib.HALT_ALL, False)
    _set(opslib.STOP_ARCHITECT, True)
    try:
        check("architect STOP → master_halted() truthy", bool(opslib.master_halted()))
    finally:
        _set(opslib.STOP_ARCHITECT, False)


if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("t_"):
            try:
                f()
            except Exception as e:  # noqa: BLE001
                _FAILED += 1
                print("FAIL -", n, repr(e))
    print(f"\n== {_FAILED} failure(s) ==")
    print("OK test_d2_halt_coverage" if _FAILED == 0 else "FAIL test_d2_halt_coverage")
    sys.exit(1 if _FAILED else 0)
