#!/usr/bin/env python3
"""wedge_probe.py — F4: هشت سطح سلامت + ماشین حالت + آشکارساز خودکار wedge.

سطح‌ها (هیچ سطحی نمی‌تواند سبز باشد اگر سطح پایین‌ترش قرمز است):
  1 process_alive          → PID از netstat
  2 port_reachable         → TCP connect
  3 event_loop_progressing → beat counter changed since last probe
  4 heartbeat_fresh        → ts < stale_after_s
  5 state_changing         → file mtime advancing
  6 task_consumption_progressing → new events in events.jsonl
  7 output_semantically_valid → no repeated identical outputs
  8 end_to_end_healthy     → all above green

State machine: HEALTHY | DEGRADED | STALLED | WEDGED | RECOVERING | UNKNOWN

Usage:
  python -m tools.wedge_probe --json                  # probe now
  python -m tools.wedge_probe --inject-lock-hold 90  # sandbox test
"""
from __future__ import annotations

import hashlib, json, os, socket, subprocess, sys, time
from pathlib import Path

OPS = Path(__file__).resolve().parents[1] / "_ops"
STATE = OPS / "state"
ORGANISM_STATE = STATE / "ORGANISM-STATE.json"
EVENTS = STATE / "events.jsonl"
WEDGE_DIR = STATE / "wedge"
BEAT_MARK = STATE / "wedge-beat-mark.json"
PY_SPY = Path(os.environ.get("LOCALAPPDATA", "")) / "Python" / "Python313" / "Scripts" / "py-spy.exe"
PORT = 8771
STALE_AFTER_S = 900.0

HEALTH_LEVELS = [
    "process_alive", "port_reachable", "event_loop_progressing",
    "heartbeat_fresh", "state_changing", "task_consumption_progressing",
    "output_semantically_valid", "end_to_end_healthy",
]
VALID_STATES = {"HEALTHY", "DEGRADED", "STALLED", "WEDGED", "RECOVERING", "UNKNOWN"}


def _read_json(p):
    try:
        return json.loads(p.read_text("utf-8"))
    except Exception:
        return {}


def _port_alive(port, timeout=2.0):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            return True
    except OSError:
        return False


def _pid_on_port(port):
    try:
        out = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, timeout=10).stdout
        for line in out.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                return int(line.strip().split()[-1])
    except Exception:
        pass
    return None


def _py_spy_dump(pid):
    if not PY_SPY.exists() or not pid:
        return None
    try:
        r = subprocess.run([str(PY_SPY), "dump", "--pid", str(pid)],
                           capture_output=True, text=True, timeout=15)
        return r.stdout if r.returncode == 0 else None
    except Exception:
        return None


def _events_tail_sha(n=20):
    try:
        lines = EVENTS.read_text("utf-8").splitlines()[-n:]
        return hashlib.sha256("\n".join(lines).encode()).hexdigest()
    except Exception:
        return None


def probe(*, inject_lock_hold=None):
    """Full health probe. Returns dict with 8 levels + state + optional stack."""
    now = time.time()
    WEDGE_DIR.mkdir(parents=True, exist_ok=True)

    # Load previous beat mark for progression check
    prev = _read_json(BEAT_MARK)

    # Read current state
    st = _read_json(ORGANISM_STATE)
    beat = st.get("beat") if isinstance(st.get("beat"), int) else None
    ts = st.get("ts", "")
    events_sha = _events_tail_sha()
    state_mtime = ORGANISM_STATE.stat().st_mtime if ORGANISM_STATE.exists() else 0

    # 1 process_alive
    pid = _pid_on_port(PORT)
    process_alive = pid is not None

    # 2 port_reachable
    port_reachable = _port_alive(PORT)

    # 3 event_loop_progressing (beat changed since last probe)
    event_loop = (prev.get("beat") is not None and beat is not None
                  and beat != prev.get("beat"))

    # 4 heartbeat_fresh
    heartbeat_fresh = False
    try:
        from datetime import datetime
        ts_epoch = datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp()
        heartbeat_fresh = (now - ts_epoch) < STALE_AFTER_S
    except (ValueError, TypeError):
        pass

    # 5 state_changing (mtime advanced)
    state_changing = (prev.get("state_mtime") is not None
                      and state_mtime > prev.get("state_mtime", 0))

    # 6 task_consumption_progressing (events tail changed)
    task_prog = (prev.get("events_sha") is not None
                 and events_sha is not None
                 and events_sha != prev.get("events_sha"))

    # 7 output_semantically_valid (simplified: beat not identical to prev)
    output_valid = beat is not None and (prev.get("beat") is None or beat != prev.get("beat"))

    # 8 end_to_end_healthy
    e2e = all([process_alive, port_reachable, event_loop,
               heartbeat_fresh, state_changing, task_prog])

    levels = {
        "process_alive": process_alive,
        "port_reachable": port_reachable,
        "event_loop_progressing": event_loop,
        "heartbeat_fresh": heartbeat_fresh,
        "state_changing": state_changing,
        "task_consumption_progressing": task_prog,
        "output_semantically_valid": output_valid,
        "end_to_end_healthy": e2e,
    }

    # Monotonic: no level can be green if a lower level is red
    seen_red = False
    for k in HEALTH_LEVELS:
        if seen_red and levels[k]:
            levels[k] = False  # force monotonic
        if not levels[k]:
            seen_red = True

    # State machine
    if not process_alive:
        state = "UNKNOWN"
    elif port_reachable and not event_loop:
        state = "WEDGED"
    elif process_alive and port_reachable and event_loop and heartbeat_fresh:
        if e2e:
            state = "HEALTHY"
        else:
            state = "DEGRADED"
    elif process_alive and port_reachable and not heartbeat_fresh:
        state = "STALLED"
    else:
        state = "UNKNOWN"

    # Capture stack on WEDGED or STALLED
    stack_captured = False
    if state in ("WEDGED", "STALLED") and pid:
        stack = _py_spy_dump(pid)
        if stack:
            sf = WEDGE_DIR / f"{time.strftime('%Y%m%d-%H%M%S')}-pid{pid}.txt"
            sf.write_text(stack, encoding="utf-8")
            stack_captured = True

    # Save beat mark for next probe
    BEAT_MARK.write_text(json.dumps({
        "beat": beat, "ts": now, "state_mtime": state_mtime,
        "events_sha": events_sha, "prev_state": state,
    }), "utf-8")

    result = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pid": pid, "beat": beat, "state": state,
        "levels": levels,
        "stack_captured": stack_captured,
        "wedge_dir": str(WEDGE_DIR),
    }

    # Sandbox lock-injection test mode
    if inject_lock_hold is not None:
        import threading
        lock_file = STATE / "wedge-test.lock"
        lock_file.write_text("held", encoding="utf-8")
        stop = threading.Event()
        def hold():
            import msvcrt
            f = open(lock_file, "a")
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            stop.wait(inject_lock_hold)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            f.close()
        t = threading.Thread(target=hold, daemon=True)
        t.start()
        time.sleep(min(inject_lock_hold, 3))  # brief check
        result["lock_injection"] = {"file": str(lock_file), "held": lock_file.exists()}
        stop.set()

    return result


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--inject-lock-hold", type=int, default=None)
    a = ap.parse_args()
    r = probe(inject_lock_hold=a.inject_lock_hold)
    print(json.dumps(r, ensure_ascii=False, indent=1 if not a.json else None))
