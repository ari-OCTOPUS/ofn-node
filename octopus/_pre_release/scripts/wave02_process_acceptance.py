#!/usr/bin/env python3
"""OCT-SENSE-052 acceptance. Does not claim GAP-001 cold boot or GAP-002 signatures."""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import time
from pathlib import Path

from octopus_sensorium.audit import verify_chain
from octopus_sensorium.config_loader import load_board_and_registry
from octopus_sensorium.sensors.process.process_sensor import ProcessSensor

RESULTS: list[dict] = []
EVIDENCE = Path("/var/lib/octopus/state/evidence")


def record(name: str, ok: bool, detail: str) -> None:
    RESULTS.append({"name": name, "ok": ok, "detail": detail})
    print(("PASS" if ok else "FAIL"), name, detail)


def manifest() -> dict:
    _, registry = load_board_and_registry()
    return next(s for s in registry.document["sensors"] if s["sensor_id"] == "OCT-SENSE-052")


def wait_file(path: Path, timeout: float = 25) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if path.exists() and path.stat().st_size > 2:
            return True
        time.sleep(0.5)
    return False


def verifier() -> dict:
    subprocess.run(
        ["/opt/octopus/venv/bin/python", "/opt/octopus/tools/verify_sensorium.py", "--json", "/var/lib/octopus/state/boot_report.json"],
        check=False,
        env={**os.environ, "PYTHONPATH": "/opt/octopus/src"},
    )
    return json.loads(Path("/var/lib/octopus/state/boot_report.json").read_text(encoding="utf-8"))


async def main() -> int:
    spec = manifest()
    sensor = ProcessSensor(spec)
    st = await sensor.self_test()
    record("self_test_three_units", st.passed and len(st.measurements.get("units_found") or []) == 3, st.message)

    t0 = time.monotonic()
    items = sensor._observations()
    dt = time.monotonic() - t0
    record("cpu_share_under_8_percent", dt < 0.4, f"observe_seconds={dt:.4f} vs 8% of 5s cycle")
    record("obs_rate_under_20", len(items) <= 20, f"count={len(items)}")
    blob = json.dumps(items)
    record(
        "no_command_line",
        not re.search(r'"command_line"\s*:', blob) and not re.search(r'"command_args"\s*:', blob),
        "published fields scanned",
    )

    wait_file(EVIDENCE / "last_OCT-SENSE-052.json")
    live = json.loads((EVIDENCE / "last_OCT-SENSE-052.json").read_text(encoding="utf-8")) if (EVIDENCE / "last_OCT-SENSE-052.json").exists() else {}
    live_blob = json.dumps(live)
    record(
        "live_no_command_line",
        not re.search(r'"command_line"\s*:', live_blob) and not re.search(r'"command_args"\s*:', live_blob),
        live.get("observed_property", "missing"),
    )

    event_path = EVIDENCE / "last_OCT-SENSE-052_event.json"
    if event_path.exists():
        event_path.unlink()
    before = Path("/run/systemd/units/invocation:nats-server.service")
    prev = os.readlink(before) if before.exists() else ""
    subprocess.run(["systemctl", "restart", "nats-server"], check=True)
    event_seen = False
    deadline = time.time() + 20
    while time.time() < deadline:
        if event_path.exists():
            obs = json.loads(event_path.read_text(encoding="utf-8"))
            if "restart" in json.dumps(obs):
                event_seen = True
                break
        time.sleep(1)
    after = os.readlink(before) if before.exists() else ""
    record("nats_restart_event", event_seen, f"event_seen={event_seen} invocation_changed={after != prev}")

    subprocess.run(["systemctl", "stop", "systemd-timesyncd"], check=True)
    time.sleep(8)
    items = sensor._observations()
    timesync = next((i for i in items if (i.get("value") or {}).get("unit") == "systemd-timesyncd.service" and i["observed_property"] == "octopus.unit.healthy"), None)
    unhealthy = bool(timesync) and (timesync.get("value") or {}).get("healthy") == 0
    subprocess.run(["systemctl", "start", "systemd-timesyncd"], check=False)
    record("timesyncd_unhealthy_when_stopped", unhealthy, str(timesync))

    zones = list(Path("/sys/class/thermal").glob("thermal_zone*/temp"))
    try:
        for z in zones:
            z.chmod(0o000)
        time.sleep(6)
        active = subprocess.run(["systemctl", "is-active", "--quiet", "octopus-sensorium"]).returncode == 0
        still_052 = (EVIDENCE / "last_OCT-SENSE-052.json").exists()
        record("thermal_fault_does_not_stop_052", active and still_052, f"agent_active={active}")
    finally:
        for z in zones:
            try:
                z.chmod(0o444)
            except OSError:
                pass

    rc = subprocess.run(
        ["su", "-s", "/bin/sh", "octopus", "-c", "systemctl restart nats-server.service"],
        capture_output=True,
        text=True,
    )
    record("octopus_cannot_restart_units", rc.returncode != 0, rc.stderr.strip()[:200] or f"rc={rc.returncode}")

    chain_ok, chain_detail = verify_chain()
    record("audit_hash_chain", chain_ok, chain_detail)

    report = verifier()
    record("verifier_gates_failed_empty", not report.get("gates_failed"), f"failed={report.get('gates_failed')} readiness={report.get('readiness_state')}")

    out = {
        "sensor_id": "OCT-SENSE-052",
        "gaps_not_claimed": ["GAP-001", "GAP-002"],
        "results": RESULTS,
        "failed": [r for r in RESULTS if not r["ok"]],
    }
    Path("/var/lib/octopus/state/wave02-process-acceptance.json").write_text(json.dumps(out, indent=2) + "\n")
    print("failed", len(out["failed"]))
    return 0 if not out["failed"] else 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
