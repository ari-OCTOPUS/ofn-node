#!/usr/bin/env python3
"""test_d4_launcher_halt — D4: watchdog/launcher halt parity.

Proves (hermetic; static content checks execute nothing):
  * every RUN-*/RESTART-* launcher .bat carries the boot-time GLOBAL halt guard
    (HALT-ALL + architect STOP) BEFORE its first python/start launch line —
    no boot, and no boot-and-exit churn, under a global halt;
  * RUN-ORGANISM.bat still never deletes the owner STOP-ORGANISM flag (P2 pin);
  * organism-watchdog.ps1 delegates the decision to watchdog.py and launches
    only on an explicit REVIVE verdict (no independent flag logic to drift);
  * watchdog.py STOP_FLAGS is exactly the three canonical flags from opslib
    (HALT-ALL, architect STOP, STOP-ORGANISM) — BLOCKER-3 split-brain pin;
  * should_revive functional matrix: any STOP flag → yield; port alive → no-op;
    no prior state → first-birth owner-only; all clear → revive.

Run: python -X utf8 test_d4_launcher_halt.py
"""
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "budget"))
import harness   # noqa: E402
ENV = harness.setup("d4-launcher-halt")
import opslib    # noqa: E402
import watchdog  # noqa: E402

_FAILED = 0


def check(name, cond):
    global _FAILED
    print(("PASS" if cond else "FAIL"), "-", name)
    if not cond:
        _FAILED += 1


# ── 1) static: boot-time global-halt guard in every launcher ────────────────────
_LAUNCHERS = ["RUN-ORGANISM.bat", "RUN-CORTEX.bat", "RUN-LIVE.bat",
              "run-live-headless.bat", "RUN-CODE-AUTONOMY.bat", "RESTART-ORGANISM.bat"]
for bat in _LAUNCHERS:
    src = (_OPS / bat).read_text("utf-8", errors="replace")
    lines = src.splitlines()
    launch_idx = next((i for i, ln in enumerate(lines)
                       if ("python -X utf8" in ln) or ln.strip().lower().startswith("start ")), None)
    halt_idx = next((i for i, ln in enumerate(lines)
                     if "HALT-ALL" in ln and ln.strip().lower().startswith("if exist")), None)
    stop_idx = next((i for i, ln in enumerate(lines)
                     if "04 - Architect System" in ln and "STOP" in ln
                     and ln.strip().lower().startswith("if exist")), None)
    check(f"{bat}: HALT-ALL guard exists before first launch",
          halt_idx is not None and launch_idx is not None and halt_idx < launch_idx)
    check(f"{bat}: architect-STOP guard exists before first launch",
          stop_idx is not None and launch_idx is not None and stop_idx < launch_idx)

# P2 pin: the organism launcher never deletes the owner kill-switch
src_org = (_OPS / "RUN-ORGANISM.bat").read_text("utf-8", errors="replace")
check("RUN-ORGANISM.bat never deletes STOP-ORGANISM (P2 invariant)",
      not any((ln.strip().lower().startswith("del ") and "stop-organism" in ln.lower())
              for ln in src_org.splitlines()))

# ── 2) static: PS1 watchdog delegates to watchdog.py, acts only on REVIVE ───────
ps1 = (_OPS / "organism-watchdog.ps1").read_text("utf-8", errors="replace")
check("organism-watchdog.ps1 delegates the decision to watchdog.py",
      "watchdog.py" in ps1)
check("organism-watchdog.ps1 launches only on an explicit REVIVE verdict",
      'like "REVIVE*"' in ps1.replace("-", "").replace("  ", " ") or '-like "REVIVE*"' in ps1)

# ── 3) STOP_FLAGS identity — BLOCKER-3 split-brain pin ──────────────────────────
check("watchdog.STOP_FLAGS == [HALT_ALL, STOP_ARCHITECT, STOP_ORGANISM] (canonical)",
      watchdog.STOP_FLAGS == [opslib.HALT_ALL, opslib.STOP_ARCHITECT, opslib.STOP_ORGANISM])

# ── 4) functional should_revive matrix (injected flags — deterministic) ─────────
td = Path(tempfile.mkdtemp(prefix="d4-flags-"))
f_halt = td / "HALT-ALL"
f_stop = td / "STOP"
f_org = td / "STOP-ORGANISM"
flags = [f_halt, f_stop, f_org]

for f in flags:
    f.write_text("x", "utf-8")
    should, reason = watchdog.should_revive(port_alive=False, stop_flags=flags,
                                            state_exists=True)
    check(f"should_revive yields under {f.name}",
          should is False and "yield" in reason)
    f.unlink()

should, reason = watchdog.should_revive(port_alive=True, stop_flags=flags,
                                        state_exists=True)
check("alive port → no revive", should is False and "alive" in reason)
should, reason = watchdog.should_revive(port_alive=False, stop_flags=flags,
                                        state_exists=False)
check("no prior state → first-birth is owner-only", should is False and "first-birth" in reason)
should, reason = watchdog.should_revive(port_alive=False, stop_flags=flags,
                                        state_exists=True)
check("port dead + no STOP + prior state → revive", should is True)


if __name__ == "__main__":
    print(f"\n== {_FAILED} failure(s) ==")
    print("OK test_d4_launcher_halt" if _FAILED == 0 else "FAIL test_d4_launcher_halt")
    sys.exit(1 if _FAILED else 0)
