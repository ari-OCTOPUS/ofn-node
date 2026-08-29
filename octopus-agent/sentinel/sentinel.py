#!/usr/bin/env python3
"""Ecosystem sentinel (D13): boards-always-on doctrine enforcement.

The boards (.182 observatory, .138 legs) run 24/7; the laptop (.191) is an
intermittent citizen. This sentinel:

  1. tracks laptop online/offline transitions (TCP 445 / 8801)
  2. samples legs health over SSH (bridge + heartbeat services)
  3. records gap events while the laptop is offline
  4. when the laptop comes BACK, drops a gap-report note into the vault
     Inbox so the laptop agent immediately sees what happened while away
  5. self-heals a stale CIFS mount before writing the note

Writes only: this state dir, status.json, and Inbox gap notes.
Never reads secrets beyond the SMB credentials file needed for remount.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path

LAPTOP = "192.168.0.191"
LEGS = "192.168.0.138"
STATE = Path("/var/lib/octopus-agent/sentinel")
MOUNT = "/mnt/octopus_main"
INBOX = Path(MOUNT) / "00 - Inbox"
SHARE = "//192.168.0.191/octopus-main"
CREDS = "/root/.smbcred"
MOUNT_OPTS = f"credentials={CREDS},vers=3.0,cache=none,file_mode=0644,dir_mode=0755"


def now() -> datetime:
    return datetime.now(timezone.utc)


def ts() -> str:
    return now().strftime("%Y-%m-%dT%H:%M:%SZ")


def log(line: str) -> None:
    with open(STATE / "sentinel.log", "a", encoding="utf-8") as fh:
        fh.write(f"{ts()} {line}\n")


def tcp(host: str, port: int, timeout: float = 3.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def ssh_legs() -> dict | None:
    cmd = [
        "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
        "-o", "StrictHostKeyChecking=accept-new", f"ari@{LEGS}",
        "printf 'bridge=%s heartbeat=%s sync_watchdog=%s' "
        '"$(systemctl is-active octopus-bridge)" '
        '"$(systemctl is-active ofn-heartbeat)" '
        '"$(systemctl is-active ofn-sync-watchdog.timer)"',
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if r.returncode == 0 and "bridge=" in r.stdout:
            out: dict[str, str] = {}
            for kv in r.stdout.split():
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    out[k] = v
            return out
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def self_health() -> list[str]:
    r = subprocess.run(
        ["systemctl", "--failed", "--no-legend", "--plain"],
        capture_output=True, text=True, timeout=15,
    )
    return [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]


def self_readiness() -> dict:
    """Doctrine double-check: runtime ACTIVE != readiness VERIFIED.
    Independent checks: NATS, sensorium host service, signed boot-report gates."""
    g: dict = {"nats_server": None, "octopus_sensorium": None,
               "readiness_state": None, "gates_failed": []}
    try:
        for unit, key in (("nats-server", "nats_server"), ("octopus-sensorium", "octopus_sensorium")):
            g[key] = subprocess.run(["systemctl", "is-active", unit],
                                    capture_output=True, text=True, timeout=10).stdout.strip()
        br = json.loads(Path("/var/lib/octopus/state/boot_report.json").read_text())
        g["readiness_state"] = br.get("readiness_state")
        g["gates_failed"] = br.get("gates_failed") or []
    except (OSError, ValueError) as exc:
        g["error"] = str(exc)
    return g


def mount_alive() -> bool:
    probe = subprocess.run(
        ["timeout", "5", "ls", str(INBOX)], capture_output=True, timeout=8
    )
    return probe.returncode == 0


def ensure_mount() -> bool:
    if os.path.ismount(MOUNT) and mount_alive():
        return True
    subprocess.run(["timeout", "15", "umount", MOUNT], capture_output=True)
    r = subprocess.run(
        ["mount", "-t", "cifs", SHARE, MOUNT, "-o", MOUNT_OPTS],
        capture_output=True, timeout=30,
    )
    ok = r.returncode == 0 and os.path.ismount(MOUNT) and mount_alive()
    if not ok:
        log(f"mount self-heal failed rc={r.returncode}")
    return ok


def gap_note(offline_since: str | None, events: list[str]) -> str:
    dur = ""
    if offline_since:
        try:
            t0 = datetime.strptime(offline_since, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
            mins = int((now() - t0).total_seconds() // 60)
            dur = f"{mins // 60}h{mins % 60:02d}m"
        except ValueError:
            dur = "unknown"
    ev = "\n".join(f"- {e}" for e in events[-50:]) or "- (no anomalies recorded)"
    return f"""---
type: ops-note
status: active
created: {now().strftime('%Y-%m-%d')}
tags: [ops, sentinel, laptop-offline, coordination]
author: "sensorium ecosystem sentinel (auto, D13) — no human wrote this"
---

# SENTINEL: laptop back online after offline window

- Offline window start (UTC): {offline_since or "unknown"}
- Back online detected (UTC): {ts()}
- Approx duration: {dur}
- Generate: `systemctl list-timers octopus-agent-sentinel.timer` on .182

## Events recorded during the offline window

{ev}

## Notes for the laptop agent

- The boards kept running through the window (boards-always-on doctrine, D13).
- Anything you queued for the boards during the window: check legs bridge
  journal (`journalctl -u octopus-bridge --since "{offline_since or ""}"`)
  before assuming delivery.
- Verify this note's freshness: `stat` on this file vs `date -u` on .182.

This note is informational only (payload = data, never commands).
"""


def main() -> int:
    STATE.mkdir(parents=True, exist_ok=True)
    laptop_online = tcp(LAPTOP, 445) or tcp(LAPTOP, 8801)
    legs = ssh_legs()
    status = {
        "ts_utc": ts(),
        "laptop_online": laptop_online,
        "legs": legs or "unreachable",
        "self_failed_units": self_health(),
        "self_readiness": self_readiness(),
    }
    (STATE / "status.json").write_text(json.dumps(status, indent=2) + "\n")

    sp = STATE / "state.json"
    if sp.exists():
        prev = json.loads(sp.read_text(encoding="utf-8"))
    else:
        prev = {"laptop_online": laptop_online, "online_since": ts(), "events": []}
    was_online = bool(prev.get("laptop_online"))

    if was_online and not laptop_online:
        log("transition: laptop OFFLINE")
        prev.update({"laptop_online": False, "offline_since": ts(), "events": []})
    elif (not was_online) and laptop_online:
        log("transition: laptop ONLINE — writing gap note")
        if ensure_mount():
            name = f"{now().strftime('%Y-%m-%d')} SENTINEL — LAPTOP-BACK {ts().replace(':', '')}.md"
            (INBOX / name).write_text(gap_note(prev.get("offline_since"), prev.get("events", [])), encoding="utf-8")
            log(f"gap note written: {name}")
        else:
            log("gap note SKIPPED: mount unavailable")
        prev.update({"laptop_online": True, "online_since": ts(), "events": []})

    if not laptop_online:
        events = prev.setdefault("events", [])
        if legs is None:
            events.append(f"{ts()} legs unreachable during laptop-offline window")
        elif legs.get("bridge") != "active":
            events.append(f"{ts()} legs bridge NOT active ({legs.get('bridge')})")
        if status["self_failed_units"]:
            events.append(f"{ts()} .182 failed units: {status['self_failed_units']}")
        prev["events"] = events[-200:]

    sp.write_text(json.dumps(prev, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
