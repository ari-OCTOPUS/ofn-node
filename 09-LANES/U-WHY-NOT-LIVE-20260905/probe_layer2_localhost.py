"""Layer 2 this-host only: classify 8791-8796. Does not SSH. Does not start ofn.run."""
from __future__ import annotations

import json
import socket
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent / "LAYER2-LOCALHOST.json"
PORTS = (8791, 8792, 8793, 8794, 8796)


def _listen(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex((host, port)) == 0


def main() -> int:
    rows = []
    for port in PORTS:
        loop = _listen("127.0.0.1", port)
        rows.append({"port": port, "loopback_open": loop, "role_on_this_host": "unknown"})
    # This-host prior: 8791 is harvest ingest, not ofn.run (HARVEST-VS-RUN + prior listen).
    for row in rows:
        if row["port"] == 8791 and row["loopback_open"]:
            row["role_on_this_host"] = "harvest_or_other_not_classified_here"
        elif row["port"] in (8792, 8793, 8794, 8796) and not row["loopback_open"]:
            row["role_on_this_host"] = "ofn_leg_absent_this_host"
        elif not row["loopback_open"]:
            row["role_on_this_host"] = "absent_this_host"
    ofn_legs = [r for r in rows if r["port"] in (8792, 8793, 8794) and r["loopback_open"]]
    receipt = {
        "schema": "octopus.layer2-localhost.v1",
        "measured_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "measured_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "vantage": "this_host_only",
        "scope": "this_host_only",
        "claim_type": "observation",
        "live_organism_claim": False,
        "layer": 2,
        "ssh_to_138": False,
        "node138_status": "unverified",
        "ports": rows,
        "ofn_run_legs_listen_this_host": len(ofn_legs),
        "mesh_tunnel_present_inference": False,
        "note": "Missing LAN/loopback ofn ports is not evidence 138 APIs are down.",
        "source": "probe_layer2_localhost.py",
    }
    OUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "out": str(OUT),
        "ofn_legs_open": receipt["ofn_run_legs_listen_this_host"],
        "8791": rows[0]["loopback_open"],
        "node138": "unverified",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
