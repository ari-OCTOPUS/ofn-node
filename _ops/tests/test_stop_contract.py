#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_stop_contract.py — HALT-ALL honored by every supervisor (D-G) + STOP contract.

قیودِ اثبات‌شده: watchdog.should_revive زیرِ HALT-ALL = yield (پیش‌تر بی‌اثر بود) ·
stop_probe.should_yield/global_halt زیرِ HALT-ALL/architect-STOP/STOP-ORGANISM · fail-closed ·
هر سه watchdogِ `_ops` `.ps1` (live/cortex/tg-center) + توئینِ ثبت‌شدهٔ organism-watchdog
(04-Architect، سرپرستِ organism+cortex) حالا HALT-ALL را چک می‌کنند، بی از دست دادنِ هیچ STOPِ
موجود (اثباتِ ساختاری با grep؛ ADD-only). $0 آفلاین.
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
    # L-06: architect-STOP باید CANONICAL باشد (opslib.STOP_ARCHITECT = «04 - Architect
    # System/STOP»)، نه مسیرِ مردهٔ ریشهٔ repo که watchdog پیش‌تر drift داده بود.
    assert opslib.STOP_ARCHITECT in watchdog.STOP_FLAGS, \
        f"architect STOP باید opslib.STOP_ARCHITECT باشد: {watchdog.STOP_FLAGS}"
    assert opslib.STOP_ARCHITECT.parent.name == "04 - Architect System"


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
        # L-06: مسیرِ CANONICALِ architect را capture/monkeypatch کن (نه opslib.STOP
        # که وجود ندارد) و شاخهٔ آن را واقعاً exercise کن — همه sandboxed، هرگز live.
        oh, os_org, oa = opslib.HALT_ALL, opslib.STOP_ORGANISM, opslib.STOP_ARCHITECT
        opslib.HALT_ALL = d / "HALT-ALL"
        opslib.STOP_ORGANISM = d / "STOP-ORGANISM"
        opslib.STOP_ARCHITECT = d / "STOP-ARCHITECT"
        try:
            # پاک → proceed
            assert stop_probe.global_halt()[0] is False
            assert stop_probe.should_yield()[0] is False
            # HALT-ALL → global halt + yield
            opslib.HALT_ALL.write_text("panic", "utf-8")
            assert stop_probe.global_halt()[0] is True
            assert stop_probe.should_yield()[0] is True
            opslib.HALT_ALL.unlink()
            # architect STOP → global halt (شاخهٔ canonical؛ master_halted آن را می‌بیند)
            opslib.STOP_ARCHITECT.write_text("kill", "utf-8")
            assert stop_probe.global_halt()[0] is True
            assert stop_probe.should_yield()[0] is True
            opslib.STOP_ARCHITECT.unlink()
            # STOP-ORGANISM → yield ولی global_halt نه (کیلِ scoped)
            opslib.STOP_ORGANISM.write_text("kill", "utf-8")
            assert stop_probe.global_halt()[0] is False
            assert stop_probe.should_yield()[0] is True
        finally:
            opslib.HALT_ALL, opslib.STOP_ORGANISM, opslib.STOP_ARCHITECT = oh, os_org, oa


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
    """هر سه watchdogِ `.ops`ِ `.ps1` (live/cortex/tg-center) HALT-ALL را چک می‌کنند و
    هیچ‌کدام off-switchِ scopedِ خود را از دست نداده‌اند (ADD-only، اثباتِ ساختاری)."""
    scoped = {
        "live-watchdog.ps1": "STOP-LIVE",
        "cortex-watchdog.ps1": "STOP-CORTEX",
        "tg-center-watchdog.ps1": "STOP-TG-CENTER",   # D5 (2026-07-21): tg-center زیرِ HALT-ALL آمد
    }
    for f, stop in scoped.items():
        text = (_HERE.parent / f).read_text("utf-8", errors="replace")
        assert re.search(r"Test-Path[^\n]*HALT-ALL", text), f"{f} باید HALT-ALL را Test-Path کند"
        # architect STOP (سطحِ والد) — نباید حذف شده باشد
        assert "Split-Path $ops -Parent" in text and "'STOP'" in text, f"{f} باید architect STOP را چک کند"
        # off-switchِ scopedِ موجود نباید گم شده باشد (گاردِ رگرسیون: هیچ STOP از دست نرود)
        assert stop in text, f"{f} نباید off-switchِ {stop} را از دست بدهد"


def t_f_twin_organism_watchdog_honors_halt_all():
    """توئینِ ثبت‌شده (`04 - Architect System/scripts/organism-watchdog.ps1`) که organism+cortex را
    سرپرستی می‌کند، حالا HALT-ALL را هم honor می‌کند — بدونِ از دست دادنِ architect STOP یا
    STOP-ORGANISM (ADD-only؛ D5 2026-07-21). idiomِ twin با `$VAULT` است نه `$ops`."""
    twin = _HERE.parent.parent / "04 - Architect System" / "scripts" / "organism-watchdog.ps1"
    text = twin.read_text("utf-8", errors="replace")
    assert re.search(r"Test-Path[^\n]*HALT-ALL", text), "twin باید HALT-ALL را Test-Path کند"
    assert "STOP-ORGANISM" in text, "twin نباید STOP-ORGANISM را از دست بدهد"
    assert re.search(r'Join-Path \$VAULT "STOP"', text), "twin باید architect STOP (F:\\backup\\STOP) را نگه دارد"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_stop_contract: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
