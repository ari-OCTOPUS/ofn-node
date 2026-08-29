"""Boot gates G1–G15. READY is illegal until every gate is OK."""

from __future__ import annotations

import os
import pathlib
from dataclasses import dataclass, field
from typing import Any

from octopus_sensorium.clock import probe_clock
from octopus_sensorium.config_loader import load_board_and_registry
from octopus_sensorium.identity import load_identity
from octopus_sensorium.isolation import IsolationViolation, assert_no_pwm_write, reject_actuator_manifest
from octopus_sensorium.verify import SignatureError


@dataclass
class Gate:
    id: str
    ok: bool
    detail: str


@dataclass
class BootReport:
    gates: list[Gate] = field(default_factory=list)
    extras: dict[str, Any] = field(default_factory=dict)

    @property
    def ready_allowed(self) -> bool:
        return all(g.ok for g in self.gates)

    def as_dict(self) -> dict[str, Any]:
        return {
            "ready_allowed": self.ready_allowed,
            "gates": [{"id": g.id, "ok": g.ok, "detail": g.detail} for g in self.gates],
            "extras": self.extras,
        }


def _gate(report: BootReport, gid: str, ok: bool, detail: str) -> None:
    report.gates.append(Gate(gid, ok, detail))


def evaluate_gates(
    *,
    nats_connected: bool = False,
    streams: list[str] | None = None,
    agent_notify_socket: bool | None = None,
    sensors_self_tested: list[str] | None = None,
    observations_published: int = 0,
    snapshot_present: bool = False,
    birth_published: bool = False,
    audit_writable: bool = False,
) -> BootReport:
    report = BootReport()
    identity = load_identity()
    report.extras["identity"] = identity.as_dict()
    expected = f"sensorium-opi5pro-{identity.serial[:8]}"
    _gate(
        report,
        "G1",
        identity.board_id == expected and identity.board_id != identity.hostname,
        f"board_id={identity.board_id} hostname={identity.hostname}",
    )

    board = registry = None
    try:
        board, registry = load_board_and_registry()
        _gate(report, "G2", True, f"board={board.payload_hash} registry={registry.payload_hash}")
    except (OSError, SignatureError, Exception) as exc:
        _gate(report, "G2", False, type(exc).__name__ + ": " + str(exc))

    trust = pathlib.Path("/etc/octopus/trust")
    root_pub = trust / "root.pub"
    writable = os.access(str(trust), os.W_OK) and os.geteuid() != 0
    # root bootstrap may still own the tree; agent user must not be able to write.
    agent_uid_writable = False
    try:
        st = root_pub.stat()
        agent_uid_writable = bool(st.st_mode & 0o222)
    except OSError:
        agent_uid_writable = True
    _gate(
        report,
        "G3",
        root_pub.exists() and not agent_uid_writable,
        f"root.pub exists={root_pub.exists()} world/group-writable={agent_uid_writable} agent_dir_w={writable}",
    )

    _gate(report, "G4", nats_connected, "NATS connected" if nats_connected else "NATS down")
    required_streams = {"SENSORIUM", "OBSERVATION", "FEATURE", "SENSOR_HEALTH", "WORLD", "AUDIT", "COMMAND", "LEG"}
    have = set(streams or [])
    _gate(report, "G5", required_streams.issubset(have), f"streams={sorted(have)}")

    clock = probe_clock()
    report.extras["clock"] = clock.as_dict()
    _gate(
        report,
        "G6",
        clock.clock_trust in {"SYNCED_NTP", "SYNCED_PTP"},
        f"trust={clock.clock_trust} rtc_valid={clock.rtc_valid}",
    )

    wd_conf = pathlib.Path("/etc/systemd/system.conf.d/99-watchdog.conf")
    wd_ok = False
    if wd_conf.exists():
        text = wd_conf.read_text(encoding="utf-8")
        wd_ok = "RuntimeWatchdogSec=" in text and "WatchdogDevice=" in text
    _gate(report, "G7", wd_ok, str(wd_conf) if wd_ok else "runtime watchdog drop-in missing")

    notify = os.environ.get("NOTIFY_SOCKET") if agent_notify_socket is None else agent_notify_socket
    _gate(report, "G8", bool(notify), "NOTIFY_SOCKET present" if notify else "not started as Type=notify")

    iso_ok = True
    iso_detail = "pwm export not writable"
    try:
        assert_no_pwm_write()
        if registry:
            for sensor in registry.document.get("sensors", []):
                reject_actuator_manifest(sensor)
    except IsolationViolation as exc:
        iso_ok = False
        iso_detail = str(exc)
    _gate(report, "G9", iso_ok, iso_detail)

    safety = (board.document.get("safety") if board else None) or {}
    safety_ok = safety.get("safety_state") in {"SOFTWARE_ONLY", "MCU_BOUND"} and safety.get("safety_mcu") in {
        "ABSENT",
        "BOUND",
    }
    report.extras["safety"] = safety
    _gate(report, "G10", bool(safety_ok), str(safety.get("safety_state")))

    tested = sensors_self_tested or []
    _gate(report, "G11", len(tested) >= 3, f"self_tested={tested}")
    _gate(report, "G12", observations_published > 0, f"published={observations_published}")
    _gate(report, "G13", snapshot_present, "snapshot present" if snapshot_present else "no snapshot")
    _gate(report, "G14", birth_published, "birth published" if birth_published else "birth not published")
    _gate(report, "G15", audit_writable, "audit writable" if audit_writable else "audit not writable")
    return report
