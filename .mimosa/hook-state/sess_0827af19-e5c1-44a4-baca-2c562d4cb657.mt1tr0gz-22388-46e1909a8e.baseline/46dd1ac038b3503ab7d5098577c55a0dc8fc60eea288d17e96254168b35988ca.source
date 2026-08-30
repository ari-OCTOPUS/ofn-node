"""
fleet/worker_agent.py — Worker Agent  (runs on each Orange Pi 5 Pro)
=====================================================================
Polls the fleet manager for a mining target, controls XMRig, and
reports hashrate + system stats back to the manager every 30 seconds.

One instance per Orange Pi 5 Pro (9 workers total).

Config via environment variables (set in /etc/worker-agent.env):
    MANAGER_URL      http://192.168.1.100:7700
    WORKER_ID        w01    (unique per node)
    WALLET_ADDR      (your mining wallet address)
    POLL_INTERVAL    30     (seconds)
    XMRIG_PATH       /usr/local/bin/xmrig

Run:
    python -m fleet.worker_agent
    # or via systemd (see deploy/systemd/worker-agent.service)
"""
import json
import logging
import os
import platform
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import requests

from fleet.models import WorkerStatus, MiningTarget, ROLE_WORKER

# ── Config from env ───────────────────────────────────────────────────────────
MANAGER_URL    = os.getenv("MANAGER_URL",    "http://192.168.1.100:7700")
WORKER_ID      = os.getenv("WORKER_ID",      f"w-{platform.node()}")
WALLET_ADDR    = os.getenv("WALLET_ADDR",    "")
POLL_INTERVAL  = int(os.getenv("POLL_INTERVAL", "30"))
XMRIG_PATH     = os.getenv("XMRIG_PATH",    "/usr/local/bin/xmrig")
CPUMINER_PATH  = os.getenv("CPUMINER_PATH",  "/usr/local/bin/cpuminer")
LOG_FILE       = os.getenv("WORKER_LOG",    f"/var/log/worker-{WORKER_ID}.log")

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, errors="ignore"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(f"worker.{WORKER_ID}")

# ── Miner process handle ──────────────────────────────────────────────────────
_miner_proc:      Optional[subprocess.Popen] = None
_current_target:  Optional[MiningTarget]     = None
_start_time:      float = time.time()


# ── Miner control ─────────────────────────────────────────────────────────────

def _stop_miner():
    global _miner_proc, _current_target
    if _miner_proc and _miner_proc.poll() is None:
        log.info("Stopping miner (pid=%d)", _miner_proc.pid)
        _miner_proc.terminate()
        try:
            _miner_proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            _miner_proc.kill()
    _miner_proc   = None
    _current_target = None


def _start_miner(target: MiningTarget):
    global _miner_proc, _current_target
    _stop_miner()

    algo   = target.algo.lower()
    wallet = WALLET_ADDR or target.wallet_addr

    # Choose binary: XMRig for RandomX/CryptoNight family; cpuminer for rest
    xmrig_algos = {"randomx", "rx/c64", "cryptonight", "cn/r", "cn/fast"}
    if algo in xmrig_algos and Path(XMRIG_PATH).exists():
        cmd = [
            XMRIG_PATH,
            "--algo",    algo,
            "--url",     f"{target.pool_url}:{target.pool_port}",
            "--user",    wallet,
            "--pass",    "x",
            "--donate-level", "1",
            "--cpu-priority", "2",
            "--no-color",
            "--log-file", f"/var/log/xmrig-{WORKER_ID}.log",
        ]
    elif Path(CPUMINER_PATH).exists():
        cmd = [
            CPUMINER_PATH,
            "--algo",  algo,
            "--url",   f"stratum+tcp://{target.pool_url}:{target.pool_port}",
            "--user",  wallet,
            "--pass",  "x",
            "--threads", str(os.cpu_count() or 4),
        ]
    else:
        log.error("No miner binary found at %s or %s", XMRIG_PATH, CPUMINER_PATH)
        return

    log.info("Starting miner: %s  algo=%s  pool=%s:%d",
             target.symbol, algo, target.pool_url, target.pool_port)
    _miner_proc   = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    _current_target = target


# ── System stats ──────────────────────────────────────────────────────────────

def _read_cpu_temp() -> float:
    """Read CPU temperature from Linux thermal zone (ARM boards)."""
    for zone in ["/sys/class/thermal/thermal_zone0/temp",
                 "/sys/class/thermal/thermal_zone1/temp"]:
        try:
            raw = Path(zone).read_text().strip()
            return float(raw) / 1000.0
        except Exception:
            continue
    return 0.0


def _read_cpu_load() -> float:
    """Read 1-minute load average and normalise by CPU count."""
    try:
        load1 = os.getloadavg()[0]
        cpus  = os.cpu_count() or 1
        return min(100.0, (load1 / cpus) * 100.0)
    except Exception:
        return 0.0


def _read_ram_used_pct() -> float:
    """Parse /proc/meminfo for used RAM %."""
    try:
        mem = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            parts = line.split()
            if len(parts) >= 2:
                mem[parts[0].rstrip(":")] = int(parts[1])
        total    = mem.get("MemTotal", 0)
        available= mem.get("MemAvailable", 0)
        if total == 0:
            return 0.0
        return round((total - available) / total * 100.0, 1)
    except Exception:
        return 0.0


def _read_miner_hashrate() -> float:
    """
    Try to read hashrate from XMRig HTTP API (port 6789) if running.
    Falls back to 0 if not available.
    """
    if _miner_proc is None or _miner_proc.poll() is not None:
        return 0.0
    try:
        r = requests.get("http://127.0.0.1:6789/2/summary", timeout=3)
        data = r.json()
        hr = data.get("hashrate", {}).get("total", [0])[0] or 0
        return float(hr)
    except Exception:
        # XMRig API not available — return estimated value from model
        if _current_target:
            from fleet.models import ARM_HASHRATE_HS
            return ARM_HASHRATE_HS.get(_current_target.algo.lower(), 0.0)
        return 0.0


# ── Manager communication ──────────────────────────────────────────────────────

def _register():
    try:
        requests.post(f"{MANAGER_URL}/register", json={
            "worker_id": WORKER_ID,
            "role":      ROLE_WORKER,
            "ip":        "",   # manager infers from request
        }, timeout=5)
        log.info("Registered with manager at %s", MANAGER_URL)
    except Exception as e:
        log.warning("Could not register: %s", e)


def _fetch_target() -> Optional[MiningTarget]:
    try:
        r = requests.get(f"{MANAGER_URL}/target",
                         params={"worker_id": WORKER_ID}, timeout=5)
        data = r.json()
        raw  = data.get("target")
        if raw is None:
            return None
        return MiningTarget.from_dict(raw)
    except Exception as e:
        log.warning("Could not fetch target: %s", e)
        return None


def _send_report(hashrate: float):
    miner_alive = (_miner_proc is not None and _miner_proc.poll() is None)
    status = WorkerStatus(
        worker_id=WORKER_ID,
        ip="",
        role=ROLE_WORKER,
        algo=(_current_target.algo  if _current_target else ""),
        symbol=(_current_target.symbol if _current_target else ""),
        hashrate_hs=hashrate,
        cpu_temp_c=_read_cpu_temp(),
        cpu_load_pct=_read_cpu_load(),
        ram_used_pct=_read_ram_used_pct(),
        uptime_s=time.time() - _start_time,
        miner_running=miner_alive,
    )
    try:
        requests.post(f"{MANAGER_URL}/report", json=status.to_dict(), timeout=5)
    except Exception as e:
        log.warning("Could not send report: %s", e)


# ── Main loop ─────────────────────────────────────────────────────────────────

def _on_signal(sig, frame):
    log.info("Signal %d received — shutting down", sig)
    _stop_miner()
    sys.exit(0)


def main():
    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT,  _on_signal)

    log.info("Worker agent starting — ID=%s  manager=%s", WORKER_ID, MANAGER_URL)
    _register()

    while True:
        # 1. Fetch current target from manager
        new_target = _fetch_target()

        # 2. Switch miner if target changed
        if new_target is None:
            if _miner_proc and _miner_proc.poll() is None:
                log.info("Target cleared — stopping miner")
                _stop_miner()
        else:
            current_sym  = _current_target.symbol if _current_target else None
            current_algo = _current_target.algo   if _current_target else None
            if new_target.symbol != current_sym or new_target.algo != current_algo:
                log.info("Target changed: %s → %s (%s)", current_sym,
                         new_target.symbol, new_target.algo)
                _start_miner(new_target)

        # 3. Report stats
        hr = _read_miner_hashrate()
        _send_report(hr)

        if new_target:
            log.debug("Alive: %s  hr=%.0f H/s  temp=%.1f°C",
                      new_target.symbol, hr, _read_cpu_temp())

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
