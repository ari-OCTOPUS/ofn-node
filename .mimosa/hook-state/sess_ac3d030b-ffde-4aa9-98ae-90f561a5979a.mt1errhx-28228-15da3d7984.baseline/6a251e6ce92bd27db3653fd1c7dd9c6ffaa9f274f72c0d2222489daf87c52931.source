#!/usr/bin/env python3
"""M3 — cortex_symmetric_revive: give cortex (port 8772) the same revive-after-
unplanned-death protection the watchdog already gives the organism (8771) — but
crash-safe. Additive · default-OFF · read-only by default (dry-run).

Fixes (audit): the root cause of FM-1 (cortex dead 36h). Investigation confirmed it
was a SUPERVISION GAP, not a crash: state/watchdog.log has 0 cortex/8772 mentions
vs 10 organism/8771 revivals (the watchdog is cortex-blind), and the OCTOPUS-Cortex
ONLOGON task was never registered — so after cortex's console ended, nothing
restarted it. This module supplies the missing external reviver.

WHY A STANDALONE WATCHER (not a call-site hook)
  The organism reviver is a PowerShell ONE-SHOT (04 - Architect System/scripts/
  organism-watchdog.ps1) fired by a Scheduled Task; the python twin _ops/watchdog.py
  is PROPOSE-ONLY with no loop. There is NO python supervision loop with a seam to
  gate. So M3 mirrors the organism reviver as a NEW one-shot the owner registers as
  its own Scheduled Task — and mirrors the now_moves M1 pattern (module + RUN-*.bat).
  It adds ZERO edits to any existing file → the running system is byte-identical
  until the owner registers the task AND sets the flag.

CRASH-SAFETY (the owner's condition: "revive only if it won't loop")
  Three belts, so a genuinely crashing cortex can never spin:
   1. BACKOFF   — refuse to relaunch within OCTOPUS_CORTEX_REVIVE_MIN_INTERVAL_S
                  (default 90s) of the last revive.
   2. RESTART-CAP — if > OCTOPUS_CORTEX_REVIVE_CAP_MAX (default 5) revives happen
                  within OCTOPUS_CORTEX_REVIVE_CAP_WINDOW_S (default 3600s), STOP
                  reviving and open ONE incident (crash-loop suspected → owner).
   3. RUN-CORTEX.bat self-guards port 8772 (exits :already if a cortex is alive),
                  so even a double-fire can never spawn a duplicate.

KILL-SWITCH HONORED (senior to everything)
  Refuses to revive if ANY of these exist: _ops/STOP-CORTEX, _ops/STOP-ORGANISM,
  04 - Architect System/STOP (parent). A STOP is an owner decision, not an anomaly.
  Also refuses if cortex was never born (no cortex-state.json) — never auto-births.

FLAG (default OFF — with it unset revive_cortex never launches)
  OCTOPUS_WIRE_CORTEX_REVIVE=1   allow an actual relaunch (owner activation).
  Even with the flag set, dry_run=True (the CLI default) only REPORTS. Actual
  relaunch needs BOTH the flag AND dry_run=False (i.e. the scheduled task runs it
  with --revive). All state writes (revive history, incident) are gated the same.

CLI
  RUN-CORTEX-REVIVE.bat            → dry-run verdict (no launch, no writes).
  RUN-CORTEX-REVIVE.bat --revive   → actually relaunch a dead 8772 (needs the flag).

ROLLBACK
  Delete _ops/now_moves/cortex_symmetric_revive.py (+ RUN-CORTEX-REVIVE.bat) and, if
  registered, `schtasks /Delete /TN OCTOPUS-Cortex-Revive`. No existing file changes.

$0 · stdlib-only · fail-soft.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # _ops/now_moves
_OPS = _HERE.parent                              # _ops

FLAG = "OCTOPUS_WIRE_CORTEX_REVIVE"
PORT = 8772
_DEF_MIN_INTERVAL_S = 90
_DEF_CAP_WINDOW_S = 3600
_DEF_CAP_MAX = 5
_INCIDENT_THROTTLE_S = 3600


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default


def _opslib():
    try:
        p = str(_OPS / "budget")
        if p not in sys.path:
            sys.path.insert(0, p)
        import opslib
        return opslib
    except Exception:
        return None


def _stop_active() -> str:
    """First STOP reason or '' (checked senior to persistence)."""
    ops = _opslib()
    candidates = [(_OPS / "STOP-CORTEX", "STOP-CORTEX"),
                  (_OPS / "STOP-ORGANISM", "STOP-ORGANISM")]
    if ops is not None:
        candidates.append((ops.STOP_ARCHITECT, "STOP(architect)"))
    for p, label in candidates:
        try:
            if Path(p).exists():
                return label
        except Exception:
            pass
    return ""


def _cortex_state_exists() -> bool:
    ops = _opslib()
    if ops is None:
        return False
    try:
        return (ops.STATE_DIR / "cortex" / "cortex-state.json").exists()
    except Exception:
        return False


def _port_alive(port: int = PORT, host: str = "127.0.0.1", timeout: float = 1.5) -> bool:
    import socket
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def should_revive_cortex(port_alive=None, stop_reason=None, state_exists=None) -> tuple:
    """(should, reason). Mirrors watchdog.should_revive() for port 8772. STOP is
    senior; never revive an alive port; never auto-birth a cortex that never ran."""
    stop = _stop_active() if stop_reason is None else stop_reason
    if stop:
        return False, f"{stop} present — owner decision, not reviving"
    alive = _port_alive() if port_alive is None else port_alive
    if alive:
        return False, "cortex alive on 8772"
    born = _cortex_state_exists() if state_exists is None else state_exists
    if not born:
        return False, "cortex never born (no cortex-state.json) — not reviving"
    return True, "cortex dead on 8772, no STOP, was born → revive"


# ── backoff + restart-cap persistence (state/now_moves/cortex-revive.json) ──────
def _state_dir() -> "Path | None":
    ops = _opslib()
    if ops is None:
        return None
    try:
        return ops.STATE_DIR / "now_moves"
    except Exception:
        return None


def _hist_path():
    d = _state_dir()
    return (d / "cortex-revive.json") if d else None


def _load_state() -> dict:
    import json
    p = _hist_path()
    if not p or not p.exists():
        return {"revives": [], "last_incident": 0}
    try:
        d = json.loads(p.read_text("utf-8"))
        return {"revives": [float(x) for x in d.get("revives", [])],
                "last_incident": float(d.get("last_incident", 0) or 0)}
    except Exception:
        return {"revives": [], "last_incident": 0}


def _save_state(state: dict) -> bool:
    import json
    p = _hist_path()
    if not p:
        return False
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def _recent(revives, now: float, window_s: int) -> list:
    return [t for t in revives if 0 <= now - t <= window_s]


def _backoff_ok(revives, now: float, min_interval_s: int) -> bool:
    return not revives or (now - max(revives)) >= min_interval_s


def _cap_ok(revives, now: float, window_s: int, cap_max: int) -> bool:
    return len(_recent(revives, now, window_s)) < cap_max


def _log_line(text: str) -> None:
    d = _state_dir()
    if not d:
        return
    try:
        d.mkdir(parents=True, exist_ok=True)
        with open(d / "cortex-revive.log", "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {text}\n")
    except Exception:
        pass


def _default_launch() -> bool:
    """Relaunch cortex via the self-guarding RUN-CORTEX.bat, detached + hidden.
    RUN-CORTEX.bat exits :already if 8772 is alive, so this is duplicate-safe."""
    import subprocess
    bat = _OPS / "RUN-CORTEX.bat"
    if not bat.exists():
        return False
    flags = 0
    for attr in ("DETACHED_PROCESS", "CREATE_NEW_PROCESS_GROUP"):
        flags |= getattr(subprocess, attr, 0)
    try:
        subprocess.Popen(["cmd", "/c", str(bat)], cwd=str(_OPS), creationflags=flags,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, close_fds=True)
        return True
    except Exception:
        return False


def _default_incident(reason: str) -> bool:
    try:
        if str(_OPS) not in sys.path:
            sys.path.insert(0, str(_OPS))
        import events
        events.open_incident("cortex", what="cortex revive cap hit — crash-loop suspected",
                             where="port 8772", risk="R4-pending",
                             policy="owner-only: investigate why cortex keeps dying",
                             evidence=str(reason)[:160],
                             next_action="بررسیِ مالک — cortex مکرر می‌میرد",
                             summary=f"cortex revive cap hit: {reason}"[:200])
        return True
    except Exception:
        return False


def revive_cortex(dry_run: bool = True, *, port_alive=None, stop_reason=None,
                  state_exists=None, now=None, launch_fn=None, incident_fn=None) -> dict:
    """Decide + (only if flag ON and dry_run False) relaunch cortex. Crash-safe:
    STOP → backoff → cap. Pure report when dry_run or flag OFF (no writes)."""
    now = time.time() if now is None else now
    active = os.environ.get(FLAG) == "1"
    will_act = active and not dry_run
    min_iv = _int_env("OCTOPUS_CORTEX_REVIVE_MIN_INTERVAL_S", _DEF_MIN_INTERVAL_S)
    window = _int_env("OCTOPUS_CORTEX_REVIVE_CAP_WINDOW_S", _DEF_CAP_WINDOW_S)
    cap_max = _int_env("OCTOPUS_CORTEX_REVIVE_CAP_MAX", _DEF_CAP_MAX)

    should, reason = should_revive_cortex(port_alive, stop_reason, state_exists)
    r = {"should_revive": should, "reason": reason, "flag_active": active,
         "dry_run": dry_run, "launched": False, "alerted": False, "action": "none"}
    if not should:
        r["action"] = "no-op"
        return r

    st = _load_state()
    revives = st.get("revives", [])
    if not _backoff_ok(revives, now, min_iv):
        r["action"] = f"backoff (<{min_iv}s since last revive) — skipped"
        return r
    if not _cap_ok(revives, now, window, cap_max):
        r["action"] = f"cap hit (>{cap_max} in {window}s) — crash-loop suspected, refusing"
        if will_act and (now - st.get("last_incident", 0)) >= _INCIDENT_THROTTLE_S:
            fn = incident_fn or _default_incident
            r["alerted"] = bool(fn(r["action"]))
            st["last_incident"] = now
            _save_state(st)
        return r

    if not will_act:
        r["action"] = "would-revive (dry-run)" if dry_run else "would-revive (flag OFF)"
        return r

    fn = launch_fn or _default_launch
    launched = bool(fn())
    r["launched"] = launched
    r["action"] = "revived" if launched else "launch-failed"
    if launched:
        st.setdefault("revives", []).append(now)
        st["revives"] = _recent(st["revives"], now, window)
        _save_state(st)
        _log_line("revived cortex (port 8772 was dead, no STOP flags)")
    return r


def main(argv=None) -> int:
    import json
    argv = list(sys.argv[1:] if argv is None else argv)
    dry = "--revive" not in argv
    r = revive_cortex(dry_run=dry)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
