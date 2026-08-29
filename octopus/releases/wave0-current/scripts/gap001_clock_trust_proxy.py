#!/usr/bin/env python3
"""Session-preserving clock-trust proxy for GAP-001. Not a cold reboot."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

REPORT = Path("/var/lib/octopus/state/boot_report.json")
EVIDENCE = Path("/var/lib/octopus/state/evidence/last_l1_observation.json")
OUT = Path("/var/lib/octopus/state/gaps/GAP-001-clock-trust-proxy.json")


def verifier() -> dict:
    subprocess.run(
        [
            "/opt/octopus/venv/bin/python",
            "/opt/octopus/tools/verify_sensorium.py",
            "--json",
            str(REPORT),
        ],
        check=False,
        env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "PYTHONPATH": "/opt/octopus/src"},
    )
    return json.loads(REPORT.read_text(encoding="utf-8"))


def wait_agent(timeout: float = 40) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        proc = subprocess.run(
            ["systemctl", "is-active", "octopus-sensorium"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.stdout.strip() == "active":
            return True
        time.sleep(1)
    return False


def main() -> int:
    subprocess.run(["systemctl", "stop", "systemd-timesyncd"], check=True)
    try:
        subprocess.run(["systemctl", "restart", "octopus-sensorium"], check=True)
        wait_agent()
        time.sleep(3)
        report = verifier()
        g6 = (report.get("gates_by_id") or {}).get("G6") or {}
        unverified = False
        deadline = time.time() + 20
        while time.time() < deadline:
            if EVIDENCE.exists():
                obs = json.loads(EVIDENCE.read_text(encoding="utf-8"))
                if (obs.get("quality") or {}).get("time_unverified") is True:
                    unverified = True
                    break
            time.sleep(1)
        result = {
            "gap_id": "GAP-001",
            "proxy": "stop_timesyncd_then_restart_agent",
            "not_a_cold_reboot": True,
            "g6_ok": g6.get("ok"),
            "g6_detail": g6.get("detail"),
            "readiness_state": report.get("readiness_state"),
            "acquisition_state": report.get("acquisition_state"),
            "time_unverified_observation": unverified,
            "pass": (g6.get("ok") is False)
            and report.get("readiness_state") == "DEGRADED"
            and report.get("acquisition_state") == "ACTIVE"
            and unverified,
        }
        OUT.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        return 0 if result["pass"] else 2
    finally:
        subprocess.run(["systemctl", "start", "systemd-timesyncd"], check=False)
        deadline = time.time() + 45
        restored = False
        while time.time() < deadline:
            report = verifier()
            if report.get("readiness_state") == "READY" and not report.get("gates_failed"):
                restored = True
                break
            time.sleep(2)
        print("timesync_restored_ready", restored)


if __name__ == "__main__":
    raise SystemExit(main())
