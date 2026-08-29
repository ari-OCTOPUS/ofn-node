#!/usr/bin/env python3
"""GAP-001 post-reboot probe. PASS only on a new boot_id with verifier READY and empty gates.

Waits for real Sensorium READY (default 300s) so a boot-order race is not recorded as TESTED_FAIL.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

DIR = Path("/var/lib/octopus/state/gap001")
PRE = DIR / "pre_reboot.json"
REPORT = DIR / "boot_report.json"
GAP = Path("/var/lib/octopus/state/gaps/GAP-001-cold_boot_unverified.json")


def boot_id() -> str:
    return Path("/proc/sys/kernel/random/boot_id").read_text(encoding="utf-8").strip()


def run_verifier(dest: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = "/opt/octopus/current/src"
    subprocess.run(
        ["/opt/octopus/venv/bin/python", "/opt/octopus/current/tools/verify_sensorium.py", "--json", str(dest)],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    if dest.exists():
        return json.loads(dest.read_text(encoding="utf-8"))
    return {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-ready-timeout", type=int, default=300)
    args = parser.parse_args()
    DIR.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc)
    started_iso = started.isoformat()
    pre = json.loads(PRE.read_text(encoding="utf-8")) if PRE.exists() else {}
    new_boot = boot_id()
    cold = bool(pre.get("boot_id") and pre["boot_id"] != new_boot)
    analyze = subprocess.run(["systemd-analyze"], capture_output=True, text=True, check=False)
    blame = subprocess.run(["systemd-analyze", "blame"], capture_output=True, text=True, check=False)
    verifier: dict = {}
    status = ""
    ready = False
    deadline = time.monotonic() + max(1, int(args.wait_ready_timeout))
    while True:
        show = subprocess.run(
            ["systemctl", "show", "octopus-sensorium", "-p", "StatusText", "-p", "ActiveState", "--no-pager"],
            capture_output=True,
            text=True,
            check=False,
        )
        status = show.stdout
        ts = subprocess.run(["systemctl", "is-active", "systemd-timesyncd"], capture_output=True, text=True, check=False)
        verifier = run_verifier(DIR / "verifier.json")
        # gates_failed == [] is a PASS; only a missing field means verifier_missing
        gates = verifier.get("gates_failed")
        if gates is None:
            gates = ["verifier_missing"]
        clock = (verifier.get("clock") or {}).get("clock_trust")
        if (
            verifier.get("readiness_state") == "READY"
            and not gates
            and clock in {"SYNCED_NTP", "SYNCED_PTP"}
            and "ActiveState=active" in status
            and ts.stdout.strip() == "active"
        ):
            ready = True
            break
        if time.monotonic() >= deadline:
            break
        time.sleep(5)
    waited_s = round((datetime.now(timezone.utc) - started).total_seconds(), 1)
    gates = verifier.get("gates_failed")
    if gates is None:
        gates = ["verifier_missing"]
    clock = (verifier.get("clock") or {}).get("clock_trust")
    timeout = not ready
    report = {
        "gap": "GAP-001",
        "probe_started": started_iso,
        "wait_ready_timeout_s": int(args.wait_ready_timeout),
        "probe_waited_s": waited_s,
        "wait_timeout": timeout,
        "pre_boot_id": pre.get("boot_id"),
        "post_boot_id": new_boot,
        "cold_boot_observed": cold,
        "agent_ready": ready,
        "status_text": status.strip(),
        "systemd_analyze": analyze.stdout.strip(),
        "blame_head": "\n".join(blame.stdout.splitlines()[:15]),
        "readiness_state": verifier.get("readiness_state"),
        "gates_failed": gates,
        "clock_trust": clock,
        "timesyncd": subprocess.run(
            ["systemctl", "is-active", "systemd-timesyncd"], capture_output=True, text=True, check=False
        ).stdout.strip(),
        "jetstream_ok": bool((verifier.get("gates_by_id") or {}).get("JS", {}).get("ok")),
        "status": "TESTED_PASS" if cold and ready and not gates else "TESTED_FAIL" if cold else "NOT_A_NEW_BOOT",
        "not_a_power_loss_test": True,
    }
    if report["status"] != "TESTED_PASS":
        report["gap_status"] = "OPEN"
        report["pass"] = False
        if timeout and cold:
            report["fail_class"] = "ready_wait_timeout" if "G8" in gates else "verifier_not_ready"
    else:
        report["gap_status"] = "SOFTWARE_REBOOT_PASS_POWER_LOSS_UNTESTED"
        report["pass"] = True
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    meta = {}
    if GAP.exists():
        try:
            meta = json.loads(GAP.read_text(encoding="utf-8"))
        except ValueError:
            meta = {}
    meta.update(
        {
            "gap_id": "GAP-001",
            "controlled_reboot_retry": report,
            "status": report["gap_status"],
            "untested": ["power_loss_recovery", "rtc_after_power_cycle"],
        }
    )
    GAP.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    subprocess.run(["/opt/octopus/venv/bin/python", "/opt/octopus/scripts/write_laptop_handoff.py"], check=False)
    print(json.dumps({"gap001": report["status"], "cold": cold, "ready": ready, "gates": gates, "clock": clock, "waited_s": waited_s}))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
