#!/usr/bin/env python3
"""Cross-node probe — writes one JSON status file for the other units to read.

Checks (TCP connect only, no auth, no payloads):
  legs board .138  port 22  (SSH/dropbear)
  laptop     .191  port 445 (SMB germline/vault shares)
  laptop     .191  port 8801(board-cp API — the command channel)

This unit NEEDS network (unlike the exchange/daily units which are
PrivateNetwork). It writes ONLY /opt/octopus-agent/REPORTS/crossnode-status.json.
"""
import datetime
import socket
import json
from pathlib import Path

OUT = Path("/opt/octopus-agent/REPORTS/crossnode-status.json")
CHECKS = {
    "legs_board_138_ssh": ("192.168.0.138", 22),
    "laptop_191_smb": ("192.168.0.191", 445),
    "laptop_191_board_cp_8801": ("192.168.0.191", 8801),
}


def probe(host: str, port: int, timeout: float = 2.5) -> str:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return "open"
    except OSError:
        return "closed"


def main() -> int:
    nodes = {name: probe(*hp) for name, hp in CHECKS.items()}
    doc = {
        "schema": "octopus.sensorium.crossnode-probe.v1",
        "ts_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
        "nodes": nodes,
        "notes": {
            "legs_138": "alive-if-ssh-open; sync state = germline ofn/heartbeat branch freshness",
            "laptop_8801": "board-cp command channel; closed => board cannot pull/ack",
        },
        "may_authorize": False,
    }
    OUT.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    print(json.dumps(doc["nodes"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
