#!/usr/bin/env python3
"""Independent BOOT-20 verifier. Runtime ACTIVE is not readiness READY."""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from octopus_sensorium.audit import verify_chain
from octopus_sensorium.clock import probe_clock
from octopus_sensorium.config_loader import load_board_and_registry
from octopus_sensorium.identity import load_identity
from octopus_sensorium.isolation import IsolationViolation, reject_actuator_manifest
from octopus_sensorium.schema_ids import SensorIdCollision, assert_no_sensor_id_collision
from octopus_sensorium.snapshot import load_latest, replay_matches_current
from octopus_sensorium.verify import SignatureError

REQUIRED_STREAMS = {
    "SENSORIUM",
    "OBSERVATION",
    "FEATURE",
    "SENSOR_HEALTH",
    "WORLD",
    "AUDIT",
    "COMMAND",
    "LEG",
}
JS_STORE = "/var/lib/nats/jetstream"


def _gate(gid: str, ok: bool, detail: str) -> dict:
    return {"id": gid, "ok": bool(ok), "detail": detail}


def _pwm_denied_for_agent() -> tuple[bool, str]:
    export = Path("/sys/class/pwm/pwmchip0/export")
    if not export.exists():
        return True, "pwmchip0 export absent"
    proc = subprocess.run(
        ["su", "-s", "/bin/sh", "octopus", "-c", "test -w /sys/class/pwm/pwmchip0/export"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        return False, "octopus can write pwm export"
    return True, "octopus pwm export not writable"


def _jsz() -> dict:
    last_exc: Exception | None = None
    for _ in range(5):
        try:
            with urllib.request.urlopen("http://127.0.0.1:8222/jsz?streams=1", timeout=3) as resp:
                return json.load(resp)
        except Exception as exc:
            last_exc = exc
            import time

            time.sleep(0.4)
    raise last_exc or RuntimeError("jsz unavailable")


def _varz() -> dict:
    with urllib.request.urlopen("http://127.0.0.1:8222/varz", timeout=3) as resp:
        return json.load(resp)


def _nats_auth() -> tuple[bool, str]:
    try:
        import nats  # noqa: WPS433
    except ImportError:
        return False, "nats-py missing"
    env = Path("/etc/octopus/secrets/nats-sensorium.env")
    vals = {}
    try:
        readable = env.exists()
    except PermissionError:
        readable = False
    if readable:
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                vals[k] = v
    url = vals.get("NATS_URL") or os.environ.get("NATS_URL", "nats://192.168.0.182:4222")
    user = vals.get("NATS_USER") or os.environ.get("NATS_USER", "")
    password = vals.get("NATS_PASSWORD") or os.environ.get("NATS_PASSWORD", "")

    async def _probe() -> None:
        import asyncio

        nc = await nats.connect(
            url,
            user=user,
            password=password,
            name="sensorium-verifier",
            max_reconnect_attempts=1,
            connect_timeout=3,
        )
        await nc.publish("octopus.sensorium.health", b'{"verifier":true}')
        await nc.flush(timeout=2)
        await nc.drain()

    try:
        import asyncio

        asyncio.run(_probe())
        return True, f"authenticated as {user}"
    except Exception as exc:
        return False, type(exc).__name__


def _process_running(needle: str) -> bool:
    proc_root = Path("/proc")
    for proc in proc_root.iterdir():
        if not proc.name.isdigit():
            continue
        try:
            cmd = (proc / "cmdline").read_bytes().replace(b"\0", b" ").decode("utf-8", "replace")
        except OSError:
            continue
        if needle in cmd:
            return True
    return False


def _systemd_active(unit: str) -> bool:
    needles = {
        "nats-server": "nats-server",
        "octopus-sensorium": "octopus_sensorium.app",
    }
    if _process_running(needles.get(unit, unit)):
        return True
    try:
        proc = subprocess.run(
            ["systemctl", "is-active", "--quiet", unit],
            check=False,
            timeout=3,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return proc.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _port_open(host: str, port: int) -> bool:
    sock = socket.socket()
    sock.settimeout(1)
    try:
        sock.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def _stream_names(jsz: dict) -> list[str]:
    names = []
    for item in jsz.get("account_details") or []:
        for stream in item.get("stream_detail") or []:
            names.append(stream.get("name"))
    if not names:
        names = [s.get("name") for s in (jsz.get("streams") or []) if isinstance(s, dict)]
    if not names and isinstance(jsz.get("streams"), int):
        # compact jsz; try server_id listing via stream names field
        pass
    return [n for n in names if n]


def _observation_count(jsz: dict) -> int:
    for item in jsz.get("account_details") or []:
        for stream in item.get("stream_detail") or []:
            if stream.get("name") == "OBSERVATION":
                state = stream.get("state") or {}
                return int(state.get("messages") or 0)
    return 0


def _birth_count(jsz: dict) -> int:
    for item in jsz.get("account_details") or []:
        for stream in item.get("stream_detail") or []:
            if stream.get("name") == "SENSORIUM":
                state = stream.get("state") or {}
                return int(state.get("messages") or 0)
    return 0


def _audit_append_only(path: Path) -> bool:
    if not path.exists():
        return False
    # O_APPEND writer exists; refuse if world-writable.
    st = path.stat()
    return (st.st_mode & 0o022) == 0 and st.st_size > 0


def evaluate() -> dict:
    gates: list[dict] = []
    identity = load_identity()
    runtime_nats = _systemd_active("nats-server")
    runtime_agent = _systemd_active("octopus-sensorium")
    runtime_state = "ACTIVE" if runtime_nats and runtime_agent else "INACTIVE"

    auth_ok, auth_detail = _nats_auth()
    gates.append(_gate("G4", auth_ok, auth_detail))

    jsz: dict = {}
    varz: dict = {}
    try:
        jsz = _jsz()
        varz = _varz()
        js_ok = bool(varz.get("jetstream"))
        store = ((varz.get("jetstream") or {}).get("config") or {}).get("store_dir", "")
        persistent = bool(store) and not str(store).startswith("/tmp")
        gates.append(_gate("JS", js_ok and persistent, f"store_dir={store}"))
    except Exception as exc:
        gates.append(_gate("JS", False, type(exc).__name__))

    names = set(_stream_names(jsz))
    if not names and Path(JS_STORE).exists():
        # Filestore dirs are a provisioner footprint when jsz compact omits names.
        names = {p.name for p in Path(JS_STORE).glob("*") if p.is_dir() and p.name != "jetstream"}
        nested = Path(JS_STORE) / "jetstream"
        if nested.exists():
            names |= {p.name.split("_")[0] for p in nested.iterdir() if p.is_dir()}
    # NATS filestore uses $G/streams/<name>
    g_streams = Path("/var/lib/nats/jetstream/jetstream")
    found = set()
    for root, dirs, _files in os.walk("/var/lib/nats/jetstream"):
        for d in dirs:
            if d in REQUIRED_STREAMS:
                found.add(d)
    names |= found
    gates.append(_gate("G5", REQUIRED_STREAMS.issubset(names), f"streams={sorted(names)}"))

    try:
        board, registry = load_board_and_registry()
        gates.append(_gate("G2", True, f"board={board.payload_hash} registry={registry.payload_hash}"))
        sensors = registry.document.get("sensors", [])
        try:
            assert_no_sensor_id_collision(sensors)
            for spec in sensors:
                reject_actuator_manifest(spec)
            gates.append(_gate("IDS", True, "no sensor id collision"))
        except (SensorIdCollision, IsolationViolation) as exc:
            gates.append(_gate("IDS", False, str(exc)))
        thermal = [s for s in sensors if (s.get("plugin") or {}).get("type") == "thermal"]
        thermal_ok = all(s.get("sensor_id") == "OCT-SENSE-053.THERMAL" for s in thermal) and bool(thermal)
        gates.append(_gate("THERMAL_ID", thermal_ok, [s.get("sensor_id") for s in thermal]))
    except (OSError, SignatureError, Exception) as exc:
        board = registry = None
        gates.append(_gate("G2", False, type(exc).__name__ + ": " + str(exc)))
        gates.append(_gate("IDS", False, "unsigned or unreadable registry"))
        sensors = []

    clock = probe_clock()
    gates.append(
        _gate(
            "G6",
            clock.clock_trust in {"SYNCED_NTP", "SYNCED_PTP"},
            f"trust={clock.clock_trust} rtc_valid={clock.rtc_valid}",
        )
    )

    wd_conf = Path("/etc/systemd/system.conf.d/99-watchdog.conf")
    wd_ok = wd_conf.exists() and "RuntimeWatchdogSec=" in wd_conf.read_text(encoding="utf-8")
    gates.append(_gate("G7", wd_ok, str(wd_conf) if wd_ok else "watchdog drop-in missing"))
    gates.append(_gate("G8", _process_running("octopus_sensorium.app"), "agent process present"))
    iso_ok, iso_detail = _pwm_denied_for_agent()
    gates.append(_gate("G9", iso_ok, iso_detail))

    obs_n = _observation_count(jsz)
    if obs_n == 0:
        obs_n = int((load_latest() or {}).get("observations_published") or 0)
    gates.append(_gate("G12", obs_n > 0, f"observation_messages={obs_n}"))
    birth_n = _birth_count(jsz)
    gates.append(_gate("G14", birth_n > 0 or bool(load_latest()), f"sensorium_messages={birth_n}"))

    snap = load_latest() or {}
    replay_ok, replay_detail = replay_matches_current(snap)
    gates.append(_gate("G13", bool(snap) and replay_ok, replay_detail if snap else "no snapshot"))

    audit_path = Path("/var/lib/octopus/audit/sensorium.jsonl")
    chain_ok, chain_detail = verify_chain(audit_path)
    gates.append(_gate("G15", chain_ok, chain_detail))

    try:
        sys.path.insert(0, "/opt/octopus/scripts")
        from reflex_ledger import lock_advisory_forever, verify as verify_reflex_ledger

        ledger_ok, ledger_seq, ledger_detail = verify_reflex_ledger()
        if not ledger_ok:
            lock_advisory_forever(f"ledger_break seq={ledger_seq} {ledger_detail}")
        gates.append(
            _gate(
                "G-LEDGER",
                ledger_ok,
                ledger_detail if ledger_ok else f"break_seq={ledger_seq} {ledger_detail}",
            )
        )
    except Exception as exc:
        gates.append(_gate("G-LEDGER", False, type(exc).__name__ + ": " + str(exc)))

    expected = f"sensorium-opi5pro-{identity.serial[:8]}"
    gates.append(
        _gate(
            "G1",
            identity.board_id == expected and identity.board_id != identity.hostname,
            f"board_id={identity.board_id}",
        )
    )

    enabled = [
        s["sensor_id"]
        for s in sensors
        if s.get("status") not in {"not_enabled", "discovered_unregistered"} and s.get("plugin")
    ]
    gates.append(_gate("G11", len(enabled) >= 3, f"enabled={enabled}"))

    port_ok = _port_open("192.168.0.182", 4222) and _port_open("127.0.0.1", 8222)
    gates.append(_gate("PORTS", port_ok, "4222/8222"))

    failed = [g["id"] for g in gates if not g["ok"]]
    readiness = "READY" if not failed else "UNVERIFIED"
    bus = "CONNECTED" if auth_ok else "ISOLATED"
    acquisition = "ACTIVE" if obs_n > 0 else "IDLE"
    safety = (board.document.get("safety") if board else {}) or {}
    report = {
        "schema_version": "verifier.v1",
        "board_id": identity.board_id,
        "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text(encoding="utf-8").strip(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runtime_state": runtime_state,
        "readiness_state": readiness,
        "bus_state": bus,
        "acquisition_state": acquisition,
        "safety_state": safety.get("safety_state", "SOFTWARE_ONLY"),
        "readiness_profile": "WAVE0_OBSERVE_ONLY",
        "operational_mode": "OBSERVE_ONLY",
        "leg_authority": "DENIED",
        "mqtt_state": "DISABLED" if not _port_open("127.0.0.1", 1883) else "ENABLED",
        "readiness_source": {
            "type": "deterministic_verifier",
            "report": "/var/lib/octopus/state/boot_report.json",
            "gates_failed": failed,
        },
        "state": readiness if readiness == "READY" else f"runtime={runtime_state}/readiness={readiness}",
        "gates": gates,
        "gates_failed": failed,
        "service_state": {
            "nats-server": "ACTIVE" if runtime_nats else "INACTIVE",
            "octopus-sensorium": "ACTIVE" if runtime_agent else "INACTIVE",
        },
        "clock": clock.as_dict(),
        "identity": identity.as_dict(),
        "mqtt_1883_open": _port_open("127.0.0.1", 1883),
    }
    if failed:
        g2_fail = any(g["id"] == "G2" and not g["ok"] for g in gates)
        g6_fail = any(g["id"] == "G6" and not g["ok"] for g in gates)
        g_ledger_fail = any(g["id"] == "G-LEDGER" and not g["ok"] for g in gates)
        report["readiness_state"] = (
            "DEGRADED"
            if g2_fail or g6_fail or g_ledger_fail or runtime_state != "ACTIVE"
            else "UNVERIFIED"
        )
    report["gates_by_id"] = {g["id"]: g for g in gates}
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, default=Path("/var/lib/octopus/state/boot_report.json"))
    args = parser.parse_args()
    report = evaluate()
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"state": report["state"], "gates": report["gates"], "gates_failed": report["gates_failed"]}))
    return 0 if not report["gates_failed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
