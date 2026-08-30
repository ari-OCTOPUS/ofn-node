"""
fleet/manager.py — Fleet Manager  (runs on Orange Pi 5 Plus)
=============================================================
Central REST API server that:
  1. Registers worker nodes on first contact
  2. Serves current mining target to all workers
  3. Receives heartbeat / hashrate reports from workers
  4. Exposes fleet health to coordinator and dashboard
  5. Writes fleet_state.json for hashrate_oracle.py to read

Port: 7700 (LAN only — not exposed to internet)

Run:
    python -m fleet.manager          # foreground
    python -m fleet.manager --daemon # background (used by systemd service)

Workers poll: GET  http://192.168.1.100:7700/target
Workers post: POST http://192.168.1.100:7700/report
"""
import argparse
import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Dict, Optional

from flask import Flask, request, jsonify

from fleet.models import MiningTarget, WorkerStatus, FleetStats

# ── Config ────────────────────────────────────────────────────────────────────
ROOT          = Path(__file__).parent.parent
DATA_DIR      = ROOT / "fleet" / "data"
TARGET_FILE   = DATA_DIR / "current_target.json"
FLEET_STATE   = DATA_DIR / "fleet_state.json"
MANAGER_LOG   = DATA_DIR / "manager.log"

BIND_HOST     = "0.0.0.0"
BIND_PORT     = 7700
STALE_TIMEOUT = 120     # seconds before worker considered dead

DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MANAGER] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(MANAGER_LOG),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("fleet.manager")

# ── State (thread-safe via lock) ──────────────────────────────────────────────
_lock:    threading.Lock = threading.Lock()
_workers: Dict[str, WorkerStatus] = {}
_target:  Optional[MiningTarget]  = None

# Load persisted target on startup
if TARGET_FILE.exists():
    try:
        _target = MiningTarget.from_dict(json.loads(TARGET_FILE.read_text()))
        log.info("Loaded persisted target: %s (%s)", _target.symbol, _target.algo)
    except Exception as e:
        log.warning("Could not load target: %s", e)

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask("fleet_manager")


@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok", "ts": time.time()})


@app.route("/target", methods=["GET"])
def get_target():
    """Worker polls this to get current mining target."""
    worker_id = request.args.get("worker_id", "unknown")
    with _lock:
        if _target is None:
            return jsonify({"target": None, "message": "No target set — idle"}), 200
        return jsonify({"target": _target.to_dict()})


@app.route("/report", methods=["POST"])
def post_report():
    """Worker sends periodic heartbeat with hashrate and system stats."""
    data = request.get_json(force=True, silent=True) or {}
    try:
        status = WorkerStatus.from_dict(data)
        status.last_seen = time.time()
        with _lock:
            _workers[status.worker_id] = status
        _save_fleet_state()
        return jsonify({"ok": True})
    except Exception as e:
        log.error("Bad report from %s: %s", request.remote_addr, e)
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/register", methods=["POST"])
def register():
    """Worker registers itself on startup."""
    data  = request.get_json(force=True, silent=True) or {}
    wid   = data.get("worker_id", request.remote_addr)
    role  = data.get("role", "WORKER")
    ip    = data.get("ip", request.remote_addr)
    log.info("Registered: %s  ip=%s  role=%s", wid, ip, role)
    with _lock:
        if wid not in _workers:
            _workers[wid] = WorkerStatus(worker_id=wid, ip=ip, role=role)
    return jsonify({"ok": True, "worker_id": wid})


@app.route("/fleet", methods=["GET"])
def fleet_summary():
    """Dashboard / coordinator reads fleet health here."""
    with _lock:
        stats = _compute_stats()
        workers = [w.to_dict() for w in _workers.values()]
    return jsonify({"stats": stats.to_dict(), "workers": workers})


@app.route("/set_target", methods=["POST"])
def set_target():
    """
    Coordinator or operator sets a new mining target.
    Body: { symbol, algo, pool_url, pool_port, wallet_addr }
    """
    data = request.get_json(force=True, silent=True) or {}
    try:
        t = MiningTarget.from_dict(data)
        with _lock:
            global _target
            _target = t
        TARGET_FILE.write_text(json.dumps(t.to_dict(), indent=2))
        log.info("New target set: %s (%s) @ %s:%s", t.symbol, t.algo, t.pool_url, t.pool_port)
        return jsonify({"ok": True})
    except Exception as e:
        log.error("set_target error: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/clear_target", methods=["POST"])
def clear_target():
    """Stop all workers (set no target)."""
    with _lock:
        global _target
        _target = None
    TARGET_FILE.write_text("null")
    log.info("Target cleared — workers will idle")
    return jsonify({"ok": True})


# ── Helpers ───────────────────────────────────────────────────────────────────

def _compute_stats() -> FleetStats:
    now = time.time()
    alive = [w for w in _workers.values() if (now - w.last_seen) < STALE_TIMEOUT]
    mining = [w for w in alive if w.miner_running]
    total_hr = sum(w.hashrate_hs for w in alive)
    avg_temp = (sum(w.cpu_temp_c for w in alive) / len(alive)) if alive else 0.0
    avg_load = (sum(w.cpu_load_pct for w in alive) / len(alive)) if alive else 0.0
    return FleetStats(
        total_workers=len(_workers),
        alive_workers=len(alive),
        mining_workers=len(mining),
        total_hashrate_hs=total_hr,
        avg_cpu_temp_c=round(avg_temp, 1),
        avg_cpu_load_pct=round(avg_load, 1),
        current_target=_target.symbol if _target else None,
        current_algo=_target.algo if _target else None,
    )


def _save_fleet_state():
    """Write fleet_state.json for hashrate_oracle.py."""
    with _lock:
        stats = _compute_stats()
        state = {
            "stats": stats.to_dict(),
            "workers": {k: v.to_dict() for k, v in _workers.items()},
        }
    FLEET_STATE.write_text(json.dumps(state, indent=2))


def _stale_checker():
    """Background thread: log stale workers every 60s."""
    while True:
        time.sleep(60)
        now = time.time()
        with _lock:
            stale = [wid for wid, w in _workers.items()
                     if (now - w.last_seen) > STALE_TIMEOUT]
        if stale:
            log.warning("Stale workers (no heartbeat >%ds): %s", STALE_TIMEOUT, stale)
        _save_fleet_state()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Fleet Manager API server")
    parser.add_argument("--host", default=BIND_HOST)
    parser.add_argument("--port", type=int, default=BIND_PORT)
    args = parser.parse_args()

    checker = threading.Thread(target=_stale_checker, daemon=True)
    checker.start()

    log.info("Fleet Manager starting on %s:%d", args.host, args.port)
    app.run(host=args.host, port=args.port, threaded=True)


if __name__ == "__main__":
    main()
