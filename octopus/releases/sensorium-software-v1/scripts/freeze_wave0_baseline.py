#!/usr/bin/env python3
"""Freeze a secret-free Wave 0 observe-only baseline.

READY here means WAVE0_OBSERVE_ONLY, not ARMED / ACTUATOR_READY / LEG_CONTROL_READY.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

BASE = Path("/var/lib/octopus/state/wave0-baseline")
STATE = Path("/var/lib/octopus/state")
MARKER = STATE / "wave_baseline_accepted.json"
FORBIDDEN = re.compile(
    r"(\$2[aby]\$|BEGIN (OPENSSH |RSA )?PRIVATE|NATS_PASSWORD=|"
    r"password:\s*\"?[^\"*]{8}|token=[A-Za-z0-9_\-]{12})",
    re.I,
)


def redact_nats(src: Path) -> str:
    lines = []
    for line in src.read_text(encoding="utf-8").splitlines():
        if "password:" in line.lower() or "$2b$" in line or "$2a$" in line or "$2y$" in line:
            indent = line[: len(line) - len(line.lstrip())]
            lines.append(f'{indent}password: "***REDACTED***"')
        else:
            lines.append(line)
    return "\n".join(lines) + "\n"


def jsz() -> dict:
    import urllib.request

    with urllib.request.urlopen("http://127.0.0.1:8222/jsz?streams=1&consumers=1", timeout=5) as resp:
        return json.load(resp)


def first_jsonl_match(path: Path, predicate) -> dict | None:
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if predicate(rec):
                return rec
    return None


def last_jsonl_match(path: Path, predicate) -> dict | None:
    found = None
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if predicate(rec):
                found = rec
    return found


def assert_no_secrets(root: Path) -> None:
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if path.suffix == ".sig" or path.name == "checksums.sha256":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if FORBIDDEN.search(text):
            raise SystemExit(f"refusing to freeze secret material in {path}")


def main() -> None:
    if BASE.exists():
        shutil.rmtree(BASE)
    BASE.mkdir(parents=True)

    shutil.copy(STATE / "boot_report.json", BASE / "boot_report.json")
    shutil.copy("/etc/octopus/config/board.yaml", BASE / "board.yaml")
    shutil.copy("/etc/octopus/config/board.yaml.sig", BASE / "board.yaml.sig")
    shutil.copy("/etc/octopus/config/registry.yaml", BASE / "registry.yaml")
    shutil.copy("/etc/octopus/config/registry.yaml.sig", BASE / "registry.yaml.sig")
    (BASE / "nats-server.conf.redacted").write_text(redact_nats(Path("/etc/nats/nats-server.conf")))

    data = jsz()
    streams = []
    consumers = []
    for acc in data.get("account_details") or []:
        for stream in acc.get("stream_detail") or []:
            cfg = stream.get("config") or {}
            state = stream.get("state") or {}
            streams.append(
                {
                    "name": stream.get("name"),
                    "messages": state.get("messages"),
                    "bytes": state.get("bytes"),
                    "first_seq": state.get("first_seq"),
                    "last_seq": state.get("last_seq"),
                    "max_bytes": cfg.get("max_bytes"),
                    "discard": cfg.get("discard"),
                    "retention": cfg.get("retention"),
                }
            )
            for cons in stream.get("consumer_detail") or []:
                if isinstance(cons, dict):
                    consumers.append(
                        {
                            "stream": stream.get("name") or cons.get("stream_name"),
                            "name": cons.get("name"),
                            "num_pending": cons.get("num_pending"),
                            "ack_floor": cons.get("ack_floor"),
                        }
                    )
    (BASE / "stream_inventory.json").write_text(json.dumps(streams, indent=2) + "\n")
    (BASE / "consumer_inventory.json").write_text(json.dumps(consumers, indent=2) + "\n")

    parts = []
    for unit, dest in (
        ("nats-server.service", STATE / "nats-security-report.txt"),
        ("octopus-sensorium.service", STATE / "sensorium-security-report.txt"),
    ):
        proc = subprocess.run(
            ["systemd-analyze", "security", unit],
            capture_output=True,
            text=True,
            check=False,
        )
        text = proc.stdout or proc.stderr or ""
        dest.write_text(text)
        parts.append(f"## {unit}\n{text}\n")
    (BASE / "service_security_report.txt").write_text("\n".join(parts))

    obs = STATE / "evidence" / "last_l1_observation.json"
    if obs.exists():
        shutil.copy(obs, BASE / "first_valid_observation.json")
    else:
        (BASE / "first_valid_observation.json").write_text("{}\n")

    snap = json.loads((STATE / "snapshots" / "latest.json").read_text(encoding="utf-8"))
    identity = first_jsonl_match(
        STATE / "events.jsonl",
        lambda r: r.get("kind") == "identity",
    ) or {"identity": snap.get("identity")}
    birth = {
        "event_type": "board_birth",
        "board_id": "sensorium-opi5pro-68e44cdf",
        "readiness_profile": "WAVE0_OBSERVE_ONLY",
        "operational_mode": "OBSERVE_ONLY",
        "actuator_authority": "NONE",
        "leg_authority": "DENIED",
        "safety_state": "SOFTWARE_ONLY",
        "identity": identity.get("identity") or snap.get("identity"),
        "runtime_state": snap.get("runtime_state"),
        "bus_state": snap.get("bus_state"),
        "note": "READY means WAVE0_OBSERVE_ONLY, not ARMED or ACTUATOR_READY",
    }
    (BASE / "board_birth_event.json").write_text(json.dumps(birth, indent=2) + "\n")

    audit = Path("/var/lib/octopus/audit/sensorium.jsonl")
    migration = last_jsonl_match(audit, lambda r: r.get("event_type") == "schema_migration")
    (BASE / "schema_migration_event.json").write_text(json.dumps(migration or {}, indent=2) + "\n")
    shutil.copy(STATE / "snapshots" / "latest.json", BASE / "latest.json")

    marker = {
        "event_type": "wave_baseline_accepted",
        "wave": 0,
        "profile": "WAVE0_OBSERVE_ONLY",
        "board_id": "sensorium-opi5pro-68e44cdf",
        "runtime_state": "ACTIVE",
        "readiness_state": "READY",
        "safety_state": "SOFTWARE_ONLY",
        "actuator_authority": "NONE",
        "gates_failed": [],
        "mqtt_enabled": False,
        "legs_authorized": False,
    }
    MARKER.write_text(json.dumps(marker, indent=2) + "\n")

    assert_no_secrets(BASE)

    subprocess.run(
        [
            "bash",
            "-lc",
            "cd /var/lib/octopus/state/wave0-baseline && "
            "find . -type f ! -name checksums.sha256 -print0 "
            "| sort -z | xargs -0 sha256sum > checksums.sha256",
        ],
        check=True,
    )
    digest = hashlib.sha256(MARKER.read_bytes()).hexdigest()
    print(str(BASE))
    print("marker", MARKER, digest)


if __name__ == "__main__":
    main()
