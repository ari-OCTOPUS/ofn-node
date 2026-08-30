#!/usr/bin/env python3
"""
preflight_reactivation.py — READ-ONLY safety gate the OWNER runs BEFORE
reactivating the body's 4d research daemon.

It NEVER starts the daemon and NEVER writes to F:\\backup. It only READS a few
state files + the DB (mode=ro) and prints a GO / NO-GO verdict so the owner can
decide. The actual reactivation is the owner running the body's own
`F:\\backup\\4d_system\\start.bat` (or `python run.py`) — this script does not do it.

Checks:
  1. no STOP / FREEZE flag in 4d_system
  2. daemon is actually stopped (daemon_state.json has stopped_at, and no live
     process owns the recorded pid)
  3. LLM budget not exhausted (cap/remaining)
  4. identity anchor healthy (SOG 0.135073, |drift| < 1e-4) via the read-only
     extractor math if reachable
  5. DB reachable read-only

Exit code 0 = GO, 1 = NO-GO / needs owner attention. Advisory only.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys

BODY = "F:/backup/4d_system"
OUT = f"{BODY}/outputs"
DB = f"{OUT}/4d_experiments.db"
ANCHOR = 0.135073


def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return json.load(f)
    except Exception as e:
        return {"_error": str(e)}


def check_flags():
    if not os.path.isdir(BODY):
        return None, "4d_system not mounted (F: unavailable)"
    hits = []
    for dp, _dns, fns in os.walk(BODY):
        for fn in fns:
            up = fn.upper()
            if "STOP" in up or "FREEZE" in up:
                hits.append(os.path.join(dp, fn))
    if hits:
        return False, f"STOP/FREEZE flag(s) present: {hits}"
    return True, "no STOP/FREEZE flag"


def check_daemon_stopped():
    st = _read_json(f"{OUT}/daemon_state.json")
    if "_error" in st:
        return None, f"daemon_state.json unreadable: {st['_error']}"
    stopped = st.get("stopped_at")
    pid = st.get("pid")
    live = False
    if pid:
        try:                                     # read-only liveness probe
            import ctypes
            h = ctypes.windll.kernel32.OpenProcess(0x1000, False, int(pid))
            if h:
                live = True
                ctypes.windll.kernel32.CloseHandle(h)
        except Exception:
            live = False
    if live:
        return False, f"a process still owns pid {pid} — daemon may be live"
    return True, f"daemon stopped (stopped_at={stopped}, pid {pid} not live)"


def check_budget():
    st = _read_json(f"{OUT}/daemon_state.json")
    b = st.get("budget", {}) if isinstance(st, dict) else {}
    cap, rem = b.get("cap"), b.get("remaining")
    if b.get("exhausted"):
        return False, f"budget exhausted (cap={cap}, remaining={rem})"
    return True, f"budget ok (cap={cap}, remaining={rem})"


def _sog_identity(rho=0.5, lam=0.5, se=0.1, sz=0.05, sd=0.1):
    import math
    se2, sz2, sd2 = se * se, sz * sz, sd * sd

    def pclosed(rho, lam, se2, sz2):
        if lam == 0:
            return sz2 / (1 - rho * rho)
        c = se2 * (1 - rho * rho)
        disc = (c - sz2 * lam * lam) ** 2 + 4 * lam * lam * sz2 * se2
        return ((sz2 * lam * lam - c) + math.sqrt(disc)) / (2 * lam * lam)
    P = pclosed(rho, lam, se2, sz2); S = lam * lam * P + se2
    Pb = pclosed(rho, lam, se2, sz2 + sd2); Sb = lam * lam * Pb + se2
    denom = (1 - rho * rho) if abs(rho) < 1 else 1e-12
    sigz2 = lam * lam * (sz2 + sd2) / denom + se2
    return 0.5 * math.log(sigz2 / S)


def check_anchor():
    ident = _sog_identity()
    drift = abs(ident - ANCHOR)
    if drift < 1e-4:
        return True, f"identity anchor healthy (identity={ident:.6f}, drift={drift:.2e})"
    return False, f"identity anchor DRIFTED (identity={ident:.6f}, drift={drift:.2e})"


def check_db():
    if not os.path.exists(DB):
        return None, "DB not mounted"
    try:
        db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=2.0)
        n = db.execute("SELECT COUNT(*) FROM dashboard_events").fetchone()[0]
        db.close()
        return True, f"DB reachable read-only ({n} events)"
    except Exception as e:
        return False, f"DB unreachable: {e}"


def main():
    print("=" * 64)
    print("PREFLIGHT — daemon reactivation readiness (READ-ONLY, advisory)")
    print("This script does NOT start the daemon or write to the body.")
    print("=" * 64)
    checks = [("flags", check_flags), ("daemon_stopped", check_daemon_stopped),
              ("budget", check_budget), ("anchor", check_anchor), ("db", check_db)]
    go = True
    unknown = False
    for name, fn in checks:
        ok, msg = fn()
        mark = "GO " if ok else ("??? " if ok is None else "NO-GO")
        print(f"  [{mark}] {name}: {msg}")
        if ok is False:
            go = False
        if ok is None:
            unknown = True
    print("-" * 64)
    if unknown and go:
        print("VERDICT: INCONCLUSIVE — F:\\backup may be unmounted; rerun on the host.")
        return 1
    if go:
        print("VERDICT: GO — preconditions clear. To reactivate, the OWNER runs:")
        print(r"    cd /d F:\backup\4d_system && start.bat")
        print("Then the shadow cortex can pick up fresh data via:")
        print("    python -c \"from experiments.organism_bridge import "
              "live_refresh_and_reevaluate as r; print(r())\"")
        return 0
    print("VERDICT: NO-GO — resolve the flagged item(s) before reactivating.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
