"""
fleet/watchdog.py — Hardware Watchdog  (runs on Raspberry Pi 3B)
================================================================
Monitors the Orange Pi 5 Plus (main brain) and the worker fleet.
If the main bot stops responding, sends a Telegram alert and
optionally SSH-restarts the coordinator service.

Config via /etc/watchdog-agent.env:
    MAIN_URL          http://192.168.1.100:7700
    COORDINATOR_HOST  192.168.1.100
    COORDINATOR_USER  pi
    TELEGRAM_TOKEN    ...
    TELEGRAM_CHAT_ID  ...
    CHECK_INTERVAL    60
    ALERT_AFTER_FAILS 3
    SSH_RESTART       false   (set true to enable SSH restart)

Run:
    python -m fleet.watchdog
    # or via systemd (see deploy/systemd/watchdog.service)
"""
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

# ── Config ────────────────────────────────────────────────────────────────────
MAIN_URL         = os.getenv("MAIN_URL",          "http://192.168.1.100:7700")
COORD_HOST       = os.getenv("COORDINATOR_HOST",  "192.168.1.100")
COORD_USER       = os.getenv("COORDINATOR_USER",  "pi")
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN",    "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID",  "")
CHECK_INTERVAL   = int(os.getenv("CHECK_INTERVAL",   "60"))
ALERT_AFTER      = int(os.getenv("ALERT_AFTER_FAILS", "3"))
SSH_RESTART      = os.getenv("SSH_RESTART", "false").lower() == "true"
LOG_FILE         = os.getenv("WATCHDOG_LOG", "/var/log/fleet-watchdog.log")

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WATCHDOG] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, errors="ignore"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("fleet.watchdog")

# ── State ─────────────────────────────────────────────────────────────────────
_fail_count   = 0
_last_alert   = 0.0
_alert_cooldown = 3600   # 1 hour between repeat alerts


# ── Checks ────────────────────────────────────────────────────────────────────

def check_manager_alive() -> bool:
    try:
        r = requests.get(f"{MAIN_URL}/ping", timeout=5)
        return r.status_code == 200 and r.json().get("status") == "ok"
    except Exception:
        return False


def check_fleet_health() -> dict:
    try:
        r = requests.get(f"{MAIN_URL}/fleet", timeout=5)
        return r.json().get("stats", {})
    except Exception:
        return {}


# ── Alerts ────────────────────────────────────────────────────────────────────

def _send_telegram(msg: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        log.warning("Telegram not configured — alert: %s", msg)
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=5)
        log.info("Telegram alert sent")
    except Exception as e:
        log.error("Telegram error: %s", e)


def alert_main_down():
    global _last_alert
    now = time.time()
    if now - _last_alert < _alert_cooldown:
        return
    _last_alert = now
    msg = (
        "🚨 FLEET WATCHDOG ALERT\n"
        f"Main brain (OPi5+) at {COORD_HOST} is NOT responding.\n"
        f"Fleet Manager ping failed {_fail_count}× in a row.\n"
        f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        "Action: check power / network / service status."
    )
    _send_telegram(msg)
    log.error("MAIN DOWN — alert sent")


def alert_main_recovered():
    msg = (
        "✅ FLEET WATCHDOG: Main brain recovered\n"
        f"OPi5+ at {COORD_HOST} is responding again.\n"
        f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    _send_telegram(msg)
    log.info("Main recovered — alert sent")


def alert_workers_stale(stats: dict):
    alive   = stats.get("alive_workers", 0)
    total   = stats.get("total_workers", 0)
    now = time.time()
    if now - _last_alert < _alert_cooldown:
        return
    msg = (
        f"⚠️ FLEET WATCHDOG: Only {alive}/{total} workers alive\n"
        f"Mining: {stats.get('mining_workers', 0)} active\n"
        f"Hashrate: {stats.get('total_hashrate_hs', 0):.0f} H/s\n"
        f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    _send_telegram(msg)


# ── SSH restart (optional) ────────────────────────────────────────────────────

def ssh_restart_coordinator():
    if not SSH_RESTART:
        log.info("SSH restart disabled — skipping")
        return
    log.info("Attempting SSH restart of coordinator on %s", COORD_HOST)
    cmd = [
        "ssh", "-o", "ConnectTimeout=10",
        "-o", "StrictHostKeyChecking=no",
        f"{COORD_USER}@{COORD_HOST}",
        "sudo systemctl restart coordinator.service fleet-manager.service",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            log.info("SSH restart succeeded")
            _send_telegram(f"🔄 Watchdog restarted coordinator service on OPi5+ ({COORD_HOST})")
        else:
            log.error("SSH restart failed: %s", result.stderr)
    except Exception as e:
        log.error("SSH restart exception: %s", e)


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    global _fail_count
    log.info("Watchdog starting — monitoring %s every %ds", MAIN_URL, CHECK_INTERVAL)
    was_down = False

    while True:
        alive = check_manager_alive()

        if alive:
            if was_down:
                alert_main_recovered()
                was_down = False
            _fail_count = 0

            # Check fleet health
            stats = check_fleet_health()
            total   = stats.get("total_workers", 0)
            workers = stats.get("alive_workers", 0)
            if total > 0 and workers < total * 0.5:
                log.warning("Fleet degraded: %d/%d workers alive", workers, total)
                alert_workers_stale(stats)
            else:
                log.debug("Fleet healthy: %d/%d workers, %.0f H/s",
                          workers, total, stats.get("total_hashrate_hs", 0))
        else:
            _fail_count += 1
            log.warning("Manager ping failed (%d/%d)", _fail_count, ALERT_AFTER)
            if _fail_count >= ALERT_AFTER:
                was_down = True
                alert_main_down()
                if _fail_count == ALERT_AFTER:   # Only attempt restart once
                    ssh_restart_coordinator()

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
