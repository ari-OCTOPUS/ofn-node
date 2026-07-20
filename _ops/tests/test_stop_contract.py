#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_stop_contract.py — HALT-ALL honored by every supervisor (D-G) + STOP contract.

قیودِ اثبات‌شده: watchdog.should_revive زیرِ HALT-ALL = yield (پیش‌تر بی‌اثر بود) ·
stop_probe.should_yield/global_halt زیرِ HALT-ALL/architect-STOP/STOP-ORGANISM · fail-closed ·
هر دو watchdog `.ps1` حالا HALT-ALL را چک می‌کنند (اثباتِ ساختاری با grep). $0 آفلاین.
"""
import re
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness      # noqa: E402
harness.setup("stop-contract")

import opslib       # noqa: E402
import watchdog     # noqa: E402
import stop_probe   # noqa: E402


def t_a_watchdog_default_flags_include_halt_all():
    """گاردِ پیش‌فرضِ watchdog حالا HALT-ALL را دارد (D-G fix)."""
    names = [p.name for p in watchdog.STOP_FLAGS]
    assert "HALT-ALL" in names, f"HALT-ALL باید در STOP_FLAGS باشد: {names}"
    assert "STOP-ORGANISM" in names


def t_b_should_revive_yields_under_halt():
    with tempfile.TemporaryDirectory() as td:
        halt = Path(td) / "HALT-ALL"
        halt.write_text("panic", "utf-8")
        # پورت مرده + state موجود، ولی HALT-ALL حاضر → yield (نه revive)
        should, reason = watchdog.should_revive(port_alive=False, stop_flags=[halt], state_exists=True)
        assert should is False and "STOP flag" in reason
        # بدونِ halt → revive
        halt.unlink()
        should2, _ = watchdog.should_revive(port_alive=False, stop_flags=[halt], state_exists=True)
        assert should2 is True


def t_c_stop_probe_global_halt(monkeypatch=None):
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        oh, os_org, ost = opslib.HALT_ALL, opslib.STOP_ORGANISM, getattr(opslib, "STOP", None)
        opslib.HALT_ALL = d / "HALT-ALL"
        opslib.STOP_ORGANISM = d / "STOP-ORGANISM"
        try:
            # پاک → proceed
            assert stop_probe.global_halt()[0] is False
            assert stop_probe.should_yield()[0] is False
            # HALT-ALL → global halt + yield
            opslib.HALT_ALL.write_text("panic", "utf-8")
            assert stop_probe.global_halt()[0] is True
            assert stop_probe.should_yield()[0] is True
            opslib.HALT_ALL.unlink()
            # STOP-ORGANISM → yield ولی global_halt نه (کیلِ scoped)
            opslib.STOP_ORGANISM.write_text("kill", "utf-8")
            assert stop_probe.global_halt()[0] is False
            assert stop_probe.should_yield()[0] is True
        finally:
            opslib.HALT_ALL, opslib.STOP_ORGANISM = oh, os_org


def t_d_stop_probe_fail_closed(monkeypatch=None):
    """خطا در اوراکل = فرضِ halt (fail-closed)."""
    orig = opslib.master_halted
    def _boom():
        raise OSError("simulated")
    opslib.master_halted = _boom
    try:
        assert stop_probe.global_halt()[0] is True   # fail-closed
    finally:
        opslib.master_halted = orig


def t_e_watchdog_ps1_honor_halt_all():
    """هر دو watchdogِ `.ps1` حالا HALT-ALL را چک می‌کنند (اثباتِ ساختاریِ D-G)."""
    for f in ("live-watchdog.ps1", "cortex-watchdog.ps1"):
        text = (_HERE.parent / f).read_text("utf-8", errors="replace")
        assert re.search(r"Test-Path[^\n]*HALT-ALL", text), f"{f} باید HALT-ALL را Test-Path کند"
        # و architect STOP (سطحِ والد)
        assert "Split-Path $ops -Parent" in text and "'STOP'" in text, f"{f} باید architect STOP را چک کند"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_stop_contract: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
