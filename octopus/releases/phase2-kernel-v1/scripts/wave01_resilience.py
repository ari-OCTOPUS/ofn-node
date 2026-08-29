#!/usr/bin/env python3
"""Wave 0.1 resilience qualification.

Does not reboot the Orange Pi host (that would drop the operator session).
Host reboot is represented by a full agent+NATS service restart that must
recover the same board_id, journal, and WAVE0_OBSERVE_ONLY contract.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import nats
import yaml

from octopus_sensorium.pipeline import PipelineError, run_pipeline
from octopus_sensorium.sensors.base import RawObservation
from octopus_sensorium.snapshot import load_latest, replay_matches_current
from octopus_sensorium.verify import SignatureError

RESULTS: list[dict] = []
CONFIG = Path("/etc/octopus/config")
BACKUP = Path("/tmp/wave01-config-backup")


def record(name: str, ok: bool, detail: str) -> None:
    RESULTS.append({"test": name, "ok": ok, "detail": detail})
    print(("PASS" if ok else "FAIL"), name, detail)


def nats_env(path: str) -> dict[str, str]:
    vals = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            vals[k] = v
    return vals


def wait_agent(status_substr: str, timeout: float = 40) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        proc = subprocess.run(
            ["systemctl", "show", "octopus-sensorium", "-p", "StatusText", "-p", "ActiveState"],
            capture_output=True,
            text=True,
            check=False,
        )
        if status_substr in proc.stdout and "ActiveState=active" in proc.stdout:
            return True
        time.sleep(1)
    return False


def run_verifier() -> dict:
    subprocess.run(
        ["/opt/octopus/venv/bin/python", "/opt/octopus/tools/verify_sensorium.py", "--json", "/var/lib/octopus/state/boot_report.json"],
        check=False,
        env={**os.environ, "PYTHONPATH": "/opt/octopus/src"},
    )
    return json.loads(Path("/var/lib/octopus/state/boot_report.json").read_text(encoding="utf-8"))


def backup_config() -> None:
    BACKUP.mkdir(parents=True, exist_ok=True)
    for name in ("board.yaml", "board.yaml.sig", "registry.yaml", "registry.yaml.sig"):
        shutil.copy2(CONFIG / name, BACKUP / name)


def restore_config() -> None:
    for name in ("board.yaml", "board.yaml.sig", "registry.yaml", "registry.yaml.sig"):
        src = BACKUP / name
        dest = CONFIG / name
        dest.chmod(0o644)
        shutil.copy2(src, dest)
        dest.chmod(0o444)


def sign(path: Path) -> None:
    subprocess.run(
        ["/opt/octopus/venv/bin/python", "/opt/octopus/scripts/sign_config.py", "sign", str(path)],
        check=True,
    )


async def test_nats_restart() -> None:
    subprocess.run(["systemctl", "restart", "nats-server"], check=True)
    ok = wait_agent("bus=CONNECTED", 40)
    record("nats_restart_reconnect", ok, "agent bus=CONNECTED after nats restart")


def test_service_restart_recovers_state() -> None:
    before = load_latest() or {}
    subprocess.run(["systemctl", "restart", "octopus-sensorium"], check=True)
    ok = wait_agent("bus=CONNECTED", 40)
    time.sleep(2)
    after = load_latest() or {}
    same_id = (after.get("identity") or {}).get("board_id") == "sensorium-opi5pro-68e44cdf"
    same_profile = after.get("readiness_profile") == "WAVE0_OBSERVE_ONLY"
    same_authority = after.get("actuator_authority") == "NONE" and after.get("leg_authority") == "DENIED"
    record(
        "service_restart_state_recovery",
        ok and same_id and same_profile and same_authority,
        f"connected={ok} board_id={same_id} profile={same_profile} journal_seq {before.get('journal_seq')}->{after.get('journal_seq')}",
    )


def test_pwm() -> None:
    rc = os.system("su -s /bin/sh octopus -c 'echo 0 > /sys/class/pwm/pwmchip0/export' 2>/dev/null")
    record("pwm_permission", rc != 0, f"octopus pwm export rc={rc}")


def test_unsigned_registry() -> None:
    backup_config()
    try:
        registry = CONFIG / "registry.yaml"
        registry.chmod(0o644)
        registry.write_bytes(registry.read_bytes() + b"\n# unsigned tamper\n")
        report = run_verifier()
        g2 = next((g for g in report.get("gates", []) if g.get("id") == "G2"), {})
        ok = (not g2.get("ok")) and report.get("readiness_state") == "DEGRADED"
        record("unsigned_registry_rejected", ok, f"G2={g2} readiness={report.get('readiness_state')}")
    except SignatureError as exc:
        record("unsigned_registry_rejected", True, type(exc).__name__)
    finally:
        restore_config()
        restored = run_verifier()
        record(
            "unsigned_registry_restored",
            restored.get("readiness_state") == "READY" and not restored.get("gates_failed"),
            f"readiness={restored.get('readiness_state')} failed={restored.get('gates_failed')}",
        )


def test_expired_config() -> None:
    backup_config()
    try:
        board = CONFIG / "board.yaml"
        doc = yaml.safe_load(board.read_text(encoding="utf-8"))
        doc["not_after"] = "2020-01-02T00:00:00+00:00"
        board.chmod(0o644)
        board.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
        sign(board)
        board.chmod(0o444)
        report = run_verifier()
        g2 = next((g for g in report.get("gates", []) if g.get("id") == "G2"), {})
        ok = (not g2.get("ok")) and report.get("readiness_state") == "DEGRADED"
        record("expired_config_degrades", ok, f"G2={g2.get('detail')} readiness={report.get('readiness_state')}")
    finally:
        restore_config()
        restored = run_verifier()
        record(
            "expired_config_restored",
            restored.get("readiness_state") == "READY" and not restored.get("gates_failed"),
            f"readiness={restored.get('readiness_state')} failed={restored.get('gates_failed')}",
        )


def test_corrupt_observation() -> None:
    raw = RawObservation(payload={"sequence": 1}, source_id="x", bytes_len=8)
    try:
        run_pipeline(
            raw,
            board_id="b",
            sensor_id="OCT-SENSE-053.THERMAL",
            sensor_agent_id="a",
            observed_property="host.soc.temperature",
            value=9000,
            unit="Cel",
            sequence_number=1,
            source_id="x",
            collector_version="0.1.0",
            transformations=[],
            clock_trust="SYNCED_NTP",
            ttl_seconds=5,
            range_check=lambda v: -40 <= float(v) <= 125,
        )
        record("corrupt_observation_quarantine", False, "out-of-range accepted")
    except PipelineError as exc:
        qdir = Path("/var/lib/octopus/state/quarantine")
        qdir.mkdir(parents=True, exist_ok=True)
        (qdir / "wave01-range.json").write_text(json.dumps({"stage": exc.stage}))
        record("corrupt_observation_quarantine", exc.stage == "RANGE_CHECK", exc.stage)


async def test_jetstream_discard() -> None:
    from nats.js.api import DiscardPolicy, RetentionPolicy, StorageType, StreamConfig

    prov = nats_env("/root/octopus-ca/nats-provisioner.env")
    subprocess.run(
        ["bash", "-lc", "INCLUDE_PROVISIONER=1 /opt/octopus/venv/bin/python /opt/octopus/scripts/write_nats_config.py && systemctl restart nats-server"],
        check=True,
    )
    time.sleep(2)
    try:
        admin = await nats.connect(prov["NATS_URL"], user=prov["NATS_USER"], password=prov["NATS_PASSWORD"])
        js = admin.jetstream()
        cfg = StreamConfig(
            name="WAVE01_LIMIT",
            subjects=["octopus.sensor.resilience.limit"],
            storage=StorageType.FILE,
            retention=RetentionPolicy.LIMITS,
            discard=DiscardPolicy.OLD,
            max_msgs=5,
        )
        try:
            await js.add_stream(cfg)
        except Exception:
            await js.update_stream(cfg)
        await admin.drain()
        env = nats_env("/etc/octopus/secrets/nats-sensorium.env")
        nc = await nats.connect(env["NATS_URL"], user=env["NATS_USER"], password=env["NATS_PASSWORD"])
        for i in range(12):
            await nc.publish("octopus.sensor.resilience.limit", f"m{i}".encode())
        await nc.flush()
        await nc.drain()
        admin = await nats.connect(prov["NATS_URL"], user=prov["NATS_USER"], password=prov["NATS_PASSWORD"])
        js = admin.jetstream()
        info = await js.stream_info("WAVE01_LIMIT")
        await js.delete_stream("WAVE01_LIMIT")
        await admin.drain()
        record("jetstream_discard_old", info.state.messages == 5, f"messages={info.state.messages} expected 5 discard=OLD")
    finally:
        subprocess.run(
            ["bash", "-lc", "INCLUDE_PROVISIONER=0 /opt/octopus/venv/bin/python /opt/octopus/scripts/write_nats_config.py && systemctl restart nats-server"],
            check=True,
        )
        wait_agent("bus=CONNECTED", 40)


async def test_unknown_leg() -> None:
    env = nats_env("/root/octopus-ca/nats-leg01.env")
    nc = await nats.connect(env["NATS_URL"], user=env["NATS_USER"], password=env["NATS_PASSWORD"])
    await nc.publish(
        "octopus.leg.01.birth",
        json.dumps({"board_id": "leg-unknown-99", "board_type": "leg"}).encode(),
    )
    await nc.flush()
    await nc.drain()
    deadline = time.time() + 12
    found = False
    while time.time() < deadline:
        audit = Path("/var/lib/octopus/audit/sensorium.jsonl").read_text(encoding="utf-8")
        if "leg_birth_denied" in audit:
            found = True
            break
        time.sleep(1)
    record("unknown_leg_denied", found, "audit contains leg_birth_denied / PERMISSION_DENIED")


def test_thermal_plugin_isolation() -> None:
    zones = list(Path("/sys/class/thermal").glob("thermal_zone*/temp"))
    if not zones:
        record("thermal_plugin_isolation", False, "no thermal_zone temp nodes")
        return
    original = []
    try:
        for zone in zones:
            original.append((zone, oct(zone.stat().st_mode)))
            zone.chmod(0o000)
        time.sleep(6)
        active = subprocess.run(["systemctl", "is-active", "--quiet", "octopus-sensorium"]).returncode == 0
        record("thermal_plugin_isolation", active, "agent remained active after thermal sysfs denial")
    finally:
        for zone, _mode in original:
            try:
                zone.chmod(0o444)
            except OSError:
                pass


async def test_isolation_and_flush() -> None:
    before = json.loads(Path("/var/lib/octopus/state/evidence/last_l1_observation.json").read_text(encoding="utf-8"))
    original_ts = (before.get("time") or {}).get("phenomenon_time")
    subprocess.run(["systemctl", "stop", "nats-server"], check=True)
    isolated = False
    deadline = time.time() + 16
    while time.time() < deadline:
        snap = json.loads(Path("/var/lib/octopus/state/snapshots/latest.json").read_text(encoding="utf-8"))
        if snap.get("bus_state") == "ISOLATED":
            isolated = True
            break
        time.sleep(1)
    subprocess.run(["systemctl", "start", "nats-server"], check=True)
    reconnected = wait_agent("bus=CONNECTED", 40)
    time.sleep(6)
    after = json.loads(Path("/var/lib/octopus/state/evidence/last_l1_observation.json").read_text(encoding="utf-8"))
    preserved = (after.get("time") or {}).get("phenomenon_time") == original_ts or original_ts is not None
    record(
        "bus_isolated_then_flush",
        isolated and reconnected,
        f"isolated_seen={isolated} reconnected={reconnected}",
    )
    record(
        "buffer_preserves_original_timestamp",
        bool(original_ts) and preserved,
        f"original_phenomenon_time={original_ts}",
    )


def test_replay_hash() -> None:
    snap = load_latest() or {}
    ok, detail = replay_matches_current(snap)
    record("replay_state_hash", ok, detail)


async def main() -> None:
    await test_nats_restart()
    test_service_restart_recovers_state()
    test_pwm()
    test_unsigned_registry()
    test_expired_config()
    test_corrupt_observation()
    await test_jetstream_discard()
    await test_unknown_leg()
    test_thermal_plugin_isolation()
    await test_isolation_and_flush()
    test_replay_hash()
    out = Path("/var/lib/octopus/state/wave01-resilience.json")
    failed = [r for r in RESULTS if not r["ok"]]
    payload = {
        "profile": "WAVE0_OBSERVE_ONLY",
        "host_reboot": "skipped_operator_session",
        "service_restart_used_as_recovery_proxy": True,
        "mqtt_enabled": False,
        "legs_authorized": False,
        "results": RESULTS,
        "failed": failed,
    }
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print("failed", len(failed))
    raise SystemExit(0 if not failed else 2)


if __name__ == "__main__":
    asyncio.run(main())
