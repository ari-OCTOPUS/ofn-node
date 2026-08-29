"""Sensorium board agent entrypoint. Never issues actuator commands."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import signal
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from octopus_sensorium import AGENT_ID, __version__
from octopus_sensorium.audit import AuditLog
from octopus_sensorium.boot import evaluate_gates
from octopus_sensorium.clock import probe_clock
from octopus_sensorium.config_loader import load_board_and_registry
from octopus_sensorium.evidence.store import persist_derived, persist_observation
from octopus_sensorium.identity import load_identity
from octopus_sensorium.isolation import IsolationViolation, assert_no_pwm_write, assert_watchdog_not_opened_by_agent, reject_actuator_manifest
from octopus_sensorium.kernel.lifecycle import PluginLifecycle, PluginState
from octopus_sensorium.messaging.offline_buffer import OfflineBuffer
from octopus_sensorium.messaging.nats_client import connect as nats_connect
from octopus_sensorium.messaging.nats_client import publish_json
from octopus_sensorium.pipeline import PipelineError, run_pipeline
from octopus_sensorium.policy.command_gate import ALLOWED_COMMANDS, FORBIDDEN_COMMANDS, REQUIRED_COMMAND_FIELDS
from octopus_sensorium.schema_ids import SensorIdCollision, assert_no_sensor_id_collision, is_runtime_enabled
from octopus_sensorium.sdnotify import ready as sd_ready
from octopus_sensorium.sdnotify import status as sd_status
from octopus_sensorium.sdnotify import stopping as sd_stopping
from octopus_sensorium.sdnotify import watchdog as sd_watchdog
from octopus_sensorium.meta.anomaly import AnomalySensor
from octopus_sensorium.meta.contradiction import ContradictionSensor
from octopus_sensorium.sensors.filesystem_watch import FilesystemSensor
from octopus_sensorium.sensors.process.process_sensor import ProcessSensor
from octopus_sensorium.sensors.system_resources import SystemResourcesSensor
from octopus_sensorium.sensors.thermal import ThermalSensor
from octopus_sensorium.sensors.base import SensorError
from octopus_sensorium.snapshot import append_event, load_latest, replay, save_snapshot
from octopus_sensorium.state_machine import AgentState, StateMachine
from octopus_sensorium.status import BoardStatus

LOG = logging.getLogger("sensorium")

PLUGIN_TYPES = {
    "system_resources": SystemResourcesSensor,
    "thermal": ThermalSensor,
    "filesystem": FilesystemSensor,
    "process": ProcessSensor,
    "anomaly": AnomalySensor,
    "contradiction": ContradictionSensor,
}


class SensoriumApp:
    def __init__(self) -> None:
        self.sm = StateMachine()
        self.audit = AuditLog()
        self.identity = load_identity()
        self.nc = None
        self.plugins: dict[str, Any] = {}
        self.health: dict[str, str] = {}
        self.recent: list[dict[str, Any]] = []
        self.seen_hashes: set[str] = set()
        self.observations_published = 0
        self.invalid_observations = 0
        self.streams: list[str] = []
        self.birth_published = False
        self.stop_event = asyncio.Event()
        self.board_doc: dict[str, Any] = {}
        self.registry_doc: dict[str, Any] = {}
        self.clock = probe_clock()
        self.readiness_state = "UNVERIFIED"
        self.migration_published = False
        self.offline_buffer = OfflineBuffer()
        self.observation_hashes: list[str] = []
        self.lifecycle = PluginLifecycle()

    def _board_status(self) -> BoardStatus:
        nats_up = bool(self.nc and self.nc.is_connected)
        acquiring = any(h == "healthy" for h in self.health.values())
        safety = self.board_doc.get("safety", {})
        if self.sm.state == AgentState.FAILED_SAFE:
            safety_state = "FAILED_SAFE"
        else:
            safety_state = safety.get("safety_state", "SOFTWARE_ONLY")
        return BoardStatus(
            runtime_state="ACTIVE",
            readiness_state=self.readiness_state,  # type: ignore[arg-type]
            bus_state="CONNECTED" if nats_up else "ISOLATED",
            acquisition_state="ACTIVE" if acquiring else "IDLE",
            safety_state=safety_state,  # type: ignore[arg-type]
            actuator_authority=safety.get("actuator_authority", "NONE"),
        )

    def _status_payload(self) -> dict[str, Any]:
        status = self._board_status()
        return {
            "board_id": self.identity.board_id,
            "hostname": self.identity.hostname,
            "soc": self.identity.soc,
            "machine_id": self.identity.machine_id,
            "serial": self.identity.serial,
            **status.as_dict(),
            "uptime_seconds": float(open("/proc/uptime", encoding="utf-8").read().split()[0]),
            "nats_connected": status.bus_state == "CONNECTED",
            "active_sensors": sum(1 for s in self.health.values() if s == "healthy"),
            "degraded_sensors": sum(1 for s in self.health.values() if s == "degraded"),
            "quarantined_sensors": sum(1 for s in self.health.values() if s == "quarantine"),
            "connected_leg_boards": 0,
            "observation_rate_per_second": 0,
            "queue_depth": 0,
            "power_state": self.board_doc.get("power", {}).get("power_state", "NOT_INSTRUMENTED"),
            "readiness_source": {
                "type": "deterministic_verifier",
                "report": "/var/lib/octopus/state/boot_report.json",
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _restore_journal_state(self) -> None:
        restored = replay(after_seq=0, initial={})
        self.observation_hashes = list(restored.get("observation_hashes") or [])
        self.observations_published = int(restored.get("observations_published") or 0)
        self.invalid_observations = int(restored.get("invalid_observations") or 0)
        if restored.get("health"):
            self.health = dict(restored["health"])

    def _snapshot_state(self) -> dict[str, Any]:
        return {
            "identity": self.identity.as_dict(),
            **self._board_status().as_dict(),
            "health": self.health,
            "clock": self.clock.as_dict(),
            "safety": self.board_doc.get("safety", {}),
            "power": self.board_doc.get("power", {}),
            "observations_published": self.observations_published,
            "invalid_observations": self.invalid_observations,
            "observation_hashes": self.observation_hashes,
            "readiness_profile": "WAVE0_OBSERVE_ONLY",
            "leg_authority": "DENIED",
        }

    def _persist_snapshot(self) -> None:
        save_snapshot(self._snapshot_state())

    def _quarantine_record(self, sensor_id: str, stage: str) -> None:
        qdir = Path("/var/lib/octopus/state/quarantine")
        try:
            qdir.mkdir(parents=True, exist_ok=True)
            (qdir / f"{sensor_id}-{stage}.json").write_text(
                json.dumps({"sensor_id": sensor_id, "stage": stage}, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            self.audit.append("quarantine_write_failed", sensor_id=sensor_id, error=type(exc).__name__)

    async def _publish(self, subject: str, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        if not self.nc or not self.nc.is_connected:
            self.offline_buffer.append(subject, payload)
            return
        try:
            await publish_json(self.nc, subject, data)
        except Exception:
            self.offline_buffer.append(subject, payload)

    def _observation_fresh(self, payload: dict[str, Any]) -> bool:
        valid_until = ((payload.get("time") or {}).get("valid_until")) if isinstance(payload, dict) else None
        if not valid_until:
            return True
        try:
            stamp = datetime.fromisoformat(valid_until)
        except ValueError:
            return True
        return stamp >= datetime.now(timezone.utc)

    async def _flush_offline_buffer(self) -> None:
        if not self.nc or not self.nc.is_connected:
            return
        pending = self.offline_buffer.drain()
        for subject, payload in pending:
            if subject.startswith("octopus.sensor.observation.") and not self._observation_fresh(payload):
                self.audit.append("buffer_drop_stale", subject=subject)
                continue
            await self._publish(subject, payload)

    async def _on_leg_birth(self, msg) -> None:  # noqa: ANN001
        try:
            body = json.loads(msg.data.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            body = {}
        board_id = str(body.get("board_id") or "unknown")
        denied = {
            "request_id": body.get("request_id"),
            "status": "PERMISSION_DENIED",
            "reason": "WAVE0_OBSERVE_ONLY legs unauthorized",
            "leg_authority": "DENIED",
            "board_id": self.identity.board_id,
        }
        self.audit.append("leg_birth_denied", requester=board_id)
        await self._publish(f"octopus.leg.{board_id}.response", denied)
        await self._publish("octopus.sensorium.alert", denied)

    async def load_signed(self) -> None:
        board, registry = load_board_and_registry()
        self.board_doc = board.document
        self.registry_doc = registry.document
        cfg_id = self.board_doc.get("board", {}).get("board_id")
        if cfg_id != self.identity.board_id:
            raise RuntimeError(f"signed board_id {cfg_id} != live {self.identity.board_id}")
        self.audit.append("config_loaded", board_hash=board.payload_hash, registry_hash=registry.payload_hash)

    def _instantiate_wave1(self) -> None:
        sensors = self.registry_doc.get("sensors", [])
        assert_no_sensor_id_collision(sensors)
        for spec in sensors:
            if not is_runtime_enabled(spec):
                continue
            if not spec.get("plugin"):
                continue
            reject_actuator_manifest(spec)
            plugin_meta = spec.get("plugin") or {}
            cls = PLUGIN_TYPES.get(plugin_meta.get("type"))
            if cls is None:
                LOG.warning("unknown plugin type skipped: %s", spec.get("sensor_id"))
                continue
            try:
                plugin = cls(spec)
            except SensorError as exc:
                LOG.error("plugin refused to start %s: %s", spec.get("sensor_id"), exc)
                self.health[spec["sensor_id"]] = "quarantine"
                self.audit.append("sensor_quarantine", sensor_id=spec["sensor_id"], reason=str(exc))
                try:
                    self.lifecycle.mark(spec["sensor_id"], PluginState.DISCOVERED)
                    self.lifecycle.mark(spec["sensor_id"], PluginState.QUARANTINED)
                except Exception:
                    pass
                continue
            self.plugins[spec["sensor_id"]] = plugin
            try:
                self.lifecycle.mark(spec["sensor_id"], PluginState.DISCOVERED)
                self.lifecycle.mark(spec["sensor_id"], PluginState.VERIFIED)
            except Exception:
                pass

    async def boot(self) -> None:
        sd_status("BOOTING")
        self._restore_journal_state()
        self.audit.append("boot_start", identity=self.identity.as_dict(), version=__version__)
        append_event({"kind": "identity", "identity": self.identity.as_dict()})
        assert_watchdog_not_opened_by_agent()
        try:
            await self.load_signed()
        except Exception as exc:
            self.audit.append("boot_signed_config_failed", error=type(exc).__name__)
            self.sm.transition(AgentState.DEGRADED)
            sd_ready()
            return

        self.sm.transition(AgentState.SELF_TEST)
        sd_status("SELF_TEST")
        try:
            assert_no_pwm_write()
        except IsolationViolation as exc:
            self.audit.append("isolation_fail", error=str(exc))
            self.sm.transition(AgentState.FAILED_SAFE)
            sd_ready()
            return

        try:
            self._instantiate_wave1()
        except SensorIdCollision as exc:
            self.audit.append("schema_collision", error=str(exc))
            self.sm.transition(AgentState.DEGRADED)
            sd_status(self._board_status().systemd_status())
            sd_ready()
            return
        tested: list[str] = []
        for sensor_id, plugin in list(self.plugins.items()):
            discovery = await plugin.discover()
            if not discovery.present:
                self.health[sensor_id] = "unavailable"
                append_event({"kind": "health", "sensor_id": sensor_id, "status": "unavailable"})
                continue
            await plugin.initialise(plugin.manifest)
            try:
                self.lifecycle.mark(sensor_id, PluginState.INITIALISED)
            except Exception:
                pass
            result = await plugin.self_test()
            if result.passed:
                self.health[sensor_id] = "healthy"
                tested.append(sensor_id)
                append_event({"kind": "health", "sensor_id": sensor_id, "status": "healthy"})
                try:
                    self.lifecycle.mark(sensor_id, PluginState.SELF_TESTED)
                    self.lifecycle.mark(sensor_id, PluginState.ACTIVE)
                except Exception:
                    pass
            else:
                self.health[sensor_id] = "quarantine"
                append_event({"kind": "health", "sensor_id": sensor_id, "status": "quarantine"})
                self.audit.append("sensor_quarantine", sensor_id=sensor_id, reason=result.message)
                try:
                    self.lifecycle.mark(sensor_id, PluginState.QUARANTINED)
                except Exception:
                    pass

        self.sm.transition(AgentState.CONNECTING)
        sd_status("CONNECTING")
        try:
            async def _disconnected() -> None:
                self.audit.append("nats_disconnected")
                self._persist_snapshot()

            async def _reconnected() -> None:
                self.audit.append("nats_reconnected")
                await self._flush_offline_buffer()
                self._persist_snapshot()

            self.nc = await asyncio.wait_for(
                nats_connect(disconnected_cb=_disconnected, reconnected_cb=_reconnected),
                timeout=8,
            )
            await self.nc.subscribe("octopus.command.sensorium", cb=self._on_command)
            await self.nc.subscribe("octopus.leg.*.birth", cb=self._on_leg_birth)
            await self._flush_offline_buffer()
        except Exception as exc:
            self.audit.append("nats_connect_failed", error=type(exc).__name__)
            self.nc = None

        self._persist_snapshot()
        audit_ok = True
        try:
            self.audit.append("snapshot_saved")
        except OSError:
            audit_ok = False

        if self.nc and self.nc.is_connected:
            birth = {
                **self.identity.as_dict(),
                "agent_id": AGENT_ID,
                "software_version": __version__,
                **self._board_status().as_dict(),
                "safety": self.board_doc.get("safety", {}),
                "power": self.board_doc.get("power", {}),
                "clock": self.clock.as_dict(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await self._publish("octopus.sensorium.birth", birth)
            caps = {
                "board_id": self.identity.board_id,
                "capabilities": sorted({c for p in self.plugins.values() for c in p.capabilities}),
                "sensors": list(self.plugins),
                "max_autonomy_level": "OBSERVE_ONLY",
                "leg_attach_allowed": False,
            }
            await self._publish("octopus.sensorium.capabilities", caps)
            self.birth_published = True
            await self._publish_schema_migration()

        report = evaluate_gates(
            nats_connected=bool(self.nc and self.nc.is_connected),
            streams=self.streams,
            sensors_self_tested=tested,
            observations_published=self.observations_published,
            snapshot_present=load_latest() is not None,
            birth_published=self.birth_published,
            audit_writable=audit_ok,
        )
        self.audit.append("boot_gates", report=report.as_dict())
        self.readiness_state = "UNVERIFIED"
        sd_status(self._board_status().systemd_status())
        sd_ready()

    async def _on_command(self, msg) -> None:  # noqa: ANN001
        try:
            body = json.loads(msg.data.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.audit.append("command_rejected", reason="invalid_json")
            return
        name = str(body.get("command", ""))
        if name in FORBIDDEN_COMMANDS:
            self.audit.append("command_forbidden", command=name, sender=body.get("sender_id"))
            return
        required = REQUIRED_COMMAND_FIELDS
        if any(k not in body for k in required):
            self.audit.append("command_rejected", reason="unsigned_or_incomplete", command=name)
            return
        if name not in ALLOWED_COMMANDS:
            self.audit.append("command_rejected", reason="not_allowlisted", command=name)
            return
        # Wave 0: signature verification of commands requires a command-signing key in trust/.
        # Until that key is present, no command is executed.
        self.audit.append("command_deferred", command=name, reason="command_trust_root_not_bound")

    async def _publish_schema_migration(self) -> None:
        if self.migration_published:
            return
        events = [
            {
                "event_type": "schema_migration",
                "from": {"sensor_id": "OCT-SENSE-002", "semantic": "board_thermal"},
                "to": {"sensor_id": "OCT-SENSE-053.THERMAL", "semantic": "host.soc.temperature"},
                "reason": "sensor identifier collision with SENSORIUM-100 OCT-SENSE-054 logs",
                "preserve_original_evidence": True,
            },
            {
                "event_type": "schema_migration",
                "from": {"sensor_id": "OCT-SENSE-054", "semantic": "board_thermal"},
                "to": {"sensor_id": "OCT-SENSE-053.THERMAL", "semantic": "host.soc.temperature"},
                "reason": "sensor identifier collision",
                "preserve_original_evidence": True,
            },
            {
                "event_type": "schema_migration",
                "from": {"sensor_id": "OCT-SENSE-001", "semantic": "system_resources"},
                "to": {"sensor_id": "OCT-SENSE-053", "semantic": "host.system_resources"},
                "reason": "SENSORIUM-100 host sensor numbering",
                "preserve_original_evidence": True,
            },
            {
                "event_type": "schema_migration",
                "from": {"sensor_id": "OCT-SENSE-003", "semantic": "filesystem"},
                "to": {"sensor_id": "OCT-SENSE-051", "semantic": "filesystem"},
                "reason": "SENSORIUM-100 host sensor numbering",
                "preserve_original_evidence": True,
            },
        ]
        for event in events:
            self.audit.append(
                "schema_migration",
                source=event["from"],
                destination=event["to"],
                reason=event["reason"],
                preserve_original_evidence=event["preserve_original_evidence"],
            )
            await self._publish("octopus.audit.sensorium", event)
        self.migration_published = True

    async def _emit(self, sensor_id: str, obs: dict[str, Any]) -> None:
        self.recent.append(obs)
        self.recent = self.recent[-64:]
        digest = (obs.get("provenance") or {}).get("content_hash")
        if digest:
            self.observation_hashes.append(digest)
            self.observation_hashes = self.observation_hashes[-512:]
        append_event({"kind": "obs", "sensor_id": sensor_id, "content_hash": digest})
        persist_observation(sensor_id, obs)
        await self._publish(f"octopus.sensor.observation.{sensor_id}", obs)
        self.observations_published += 1
        await self._feed_meta("observation", obs, f"octopus.sensor.observation.{sensor_id}")

    async def _feed_meta(self, kind: str, payload: dict[str, Any], subject: str = "") -> None:
        anomaly = self.plugins.get("OCT-SENSE-092")
        contra = self.plugins.get("OCT-SENSE-095")
        if kind != "anomaly" and anomaly is not None and hasattr(anomaly, "ingest"):
            anomaly.ingest(kind, payload, subject)
        if contra is not None and hasattr(contra, "ingest"):
            contra.ingest(kind, payload, subject)

    async def _emit_derived(self, sensor_id: str, event: dict[str, Any], subject: str) -> None:
        pub = (self.plugins.get(sensor_id).manifest.get("publication") if self.plugins.get(sensor_id) else {}) or {}
        if pub.get("can_change_readiness") or pub.get("can_quarantine") or pub.get("can_execute"):
            self.audit.append("shadow_enforcement_block", sensor_id=sensor_id)
            return
        event.setdefault("policy", {})
        event["policy"].update(
            {
                "shadow_mode": True,
                "actionable": False,
                "may_change_readiness": False,
                "may_quarantine": False,
            }
        )
        persist_derived(sensor_id, event)
        await self._publish(subject, event)
        if sensor_id == "OCT-SENSE-092":
            await self._feed_meta("anomaly", event, subject)

    async def _tick_sensor(self, sensor_id: str, plugin: Any) -> None:
        if self.health.get(sensor_id) != "healthy":
            return
        try:
            async for raw in plugin.observe():
                interval = int(plugin.manifest.get("freshness", {}).get("ttl_seconds", 30))
                if plugin.sensor_type == "thermal":
                    zones = raw.payload.get("zones_celsius") or {}
                    soc = zones.get("soc-thermal", next(iter(zones.values()), None))
                    obs = run_pipeline(
                        raw,
                        board_id=self.identity.board_id,
                        sensor_id="OCT-SENSE-053.THERMAL",
                        sensor_agent_id="agent://sensor/OCT-SENSE-053.THERMAL",
                        observed_property="host.soc.temperature",
                        value=soc,
                        unit="Cel",
                        sequence_number=raw.payload["sequence"],
                        source_id=raw.source_id,
                        collector_version=__version__,
                        transformations=["milliC_to_C"],
                        clock_trust=self.clock.clock_trust,
                        ttl_seconds=interval,
                        range_check=lambda v: v is not None and -40 <= float(v) <= 125,
                        seen_hashes=self.seen_hashes,
                    )
                    obs["scope"] = "board_internal"
                    obs["is_environment_feature"] = False
                    obs["subsensor_id"] = "OCT-SENSE-053.THERMAL"
                    await self._emit("OCT-SENSE-053.THERMAL", obs)
                elif plugin.sensor_type == "system_resources":
                    seq = raw.payload["sequence"]
                    parts = [
                        ("OCT-SENSE-053.CPU", "host.cpu.load1", raw.payload["load1"], "1", lambda v: float(v) >= 0),
                        ("OCT-SENSE-053.MEMORY", "host.memory.percent", raw.payload["memory_percent"], "percent", lambda v: 0.0 <= float(v) <= 100.0),
                        ("OCT-SENSE-053.STORAGE", "host.storage.percent", raw.payload["storage_percent"], "percent", lambda v: 0.0 <= float(v) <= 100.0),
                    ]
                    for offset, (sid, prop, value, unit, check) in enumerate(parts):
                        obs = run_pipeline(
                            raw,
                            board_id=self.identity.board_id,
                            sensor_id=sid,
                            sensor_agent_id=f"agent://sensor/{sid}",
                            observed_property=prop,
                            value=value,
                            unit=unit,
                            sequence_number=seq * 10 + offset,
                            source_id=raw.source_id,
                            collector_version=__version__,
                            transformations=["procfs_normalise"],
                            clock_trust=self.clock.clock_trust,
                            ttl_seconds=interval,
                            range_check=check,
                            seen_hashes=self.seen_hashes,
                        )
                        obs["scope"] = "board_internal"
                        obs["is_environment_feature"] = False
                        obs["subsensor_id"] = sid
                        await self._emit(sid, obs)
                elif plugin.sensor_type == "process":
                    items = list((raw.payload.get("observations") or [])[:20])
                    seq = int(raw.payload.get("sequence") or 1)
                    for offset, item in enumerate(items):
                        value = item.get("value")
                        obs = run_pipeline(
                            raw,
                            board_id=self.identity.board_id,
                            sensor_id="OCT-SENSE-052",
                            sensor_agent_id="agent://sensor/OCT-SENSE-052",
                            observed_property=str(item.get("observed_property") or "system.process.count"),
                            value=value,
                            unit=item.get("unit"),
                            sequence_number=seq * 100 + offset,
                            source_id=raw.source_id,
                            collector_version=__version__,
                            transformations=["procfs_and_systemd", "cmdline_redacted"],
                            clock_trust=self.clock.clock_trust,
                            ttl_seconds=interval,
                            seen_hashes=self.seen_hashes,
                        )
                        obs["observation_type"] = item.get("observation_type") or "measurement"
                        obs["scope"] = "board_internal"
                        obs["is_environment_feature"] = False
                        obs["subsensor_id"] = "OCT-SENSE-052"
                        if item.get("hypothesis"):
                            obs["quality"]["hypothesis"] = True
                            obs["uncertainty"]["method"] = "HYPOTHESIS"
                        await self._emit("OCT-SENSE-052", obs)
                    if plugin.manifest.get("publication", {}).get("feature_enabled"):
                        await self._publish(
                            "octopus.sensor.feature.OCT-SENSE-052",
                            {
                                "sensor_id": "OCT-SENSE-052",
                                "count": len(items),
                                "sequence": seq,
                                "board_id": self.identity.board_id,
                            },
                        )
                elif plugin.sensor_type == "anomaly":
                    for event in raw.payload.get("events") or []:
                        await self._emit_derived("OCT-SENSE-092", event, "octopus.sensor.anomaly.OCT-SENSE-092")
                elif plugin.sensor_type == "contradiction":
                    plugin.registry_sensors = self.registry_doc.get("sensors")  # type: ignore[attr-defined]
                    for event in raw.payload.get("events") or []:
                        await self._emit_derived("OCT-SENSE-095", event, "octopus.world.contradiction")
                else:
                    obs = run_pipeline(
                        raw,
                        board_id=self.identity.board_id,
                        sensor_id="OCT-SENSE-051",
                        sensor_agent_id="agent://sensor/OCT-SENSE-051",
                        observed_property="host.filesystem.mtime",
                        value=raw.payload.get("snapshot"),
                        unit=None,
                        sequence_number=raw.payload["sequence"],
                        source_id=raw.source_id,
                        collector_version=__version__,
                        transformations=["posix_stat"],
                        clock_trust=self.clock.clock_trust,
                        ttl_seconds=interval,
                        seen_hashes=self.seen_hashes,
                    )
                    obs["scope"] = "board_internal"
                    obs["is_environment_feature"] = False
                    await self._emit("OCT-SENSE-051", obs)
                plugin.consecutive_failures = 0
        except PipelineError as exc:
            self.invalid_observations += 1
            plugin.consecutive_failures += 1
            self.audit.append("pipeline_drop", sensor_id=sensor_id, stage=exc.stage)
            append_event({"kind": "invalid_obs", "sensor_id": sensor_id, "stage": exc.stage})
            if not (plugin.manifest.get("publication") or {}).get("shadow_only"):
                self._quarantine_record(sensor_id, exc.stage)
        except Exception as exc:
            plugin.consecutive_failures += 1
            self.audit.append("sensor_error", sensor_id=sensor_id, error=type(exc).__name__)
            if plugin.consecutive_failures >= 3:
                self.health[sensor_id] = "degraded"
            can_quarantine = (plugin.manifest.get("publication") or {}).get("can_quarantine")
            if plugin.consecutive_failures >= 10 and can_quarantine is not False:
                self.health[sensor_id] = "quarantine"

    async def run_forever(self) -> None:
        await self.boot()
        interval = 5.0
        while not self.stop_event.is_set():
            sd_watchdog()
            self.clock = probe_clock()
            if self.nc and self.nc.is_connected:
                await self._flush_offline_buffer()
            report_path = "/var/lib/octopus/state/boot_report.json"
            try:
                external = json.loads(open(report_path, encoding="utf-8").read())
                ext_ready = external.get("readiness_state")
                if ext_ready in {"READY", "DEGRADED", "UNVERIFIED"} and isinstance(external.get("gates_failed"), list):
                    self.readiness_state = ext_ready
                await self._feed_meta("boot_report", external)
            except (OSError, ValueError):
                self.readiness_state = "UNVERIFIED"
            await self._feed_meta("health", self._status_payload())
            for sensor_id, plugin in self.plugins.items():
                try:
                    await self._tick_sensor(sensor_id, plugin)
                except Exception:
                    LOG.exception("plugin tick failed sensor_id=%s", sensor_id)
                    self.audit.append("plugin_tick_failed", sensor_id=sensor_id)
            status = self._status_payload()
            await self._publish("octopus.sensorium.heartbeat", status)
            await self._publish("octopus.sensorium.health", status)
            self._persist_snapshot()
            sd_status(self._board_status().systemd_status())
            try:
                await asyncio.wait_for(self.stop_event.wait(), timeout=interval)
            except asyncio.TimeoutError:
                continue
        sd_stopping()
        if self.nc:
            await self.nc.drain()


async def _amain() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    app = SensoriumApp()

    def _stop() -> None:
        app.stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _stop)
    await app.run_forever()


def main() -> None:
    parser = argparse.ArgumentParser(prog="octopus-sensorium")
    parser.add_argument("--once-status", action="store_true")
    args = parser.parse_args()
    if args.once_status:
        identity = load_identity()
        clock = probe_clock()
        print(
            json.dumps(
                {"identity": identity.as_dict(), "clock": clock.as_dict(), "pid": os.getpid()},
                indent=2,
            )
        )
        return
    asyncio.run(_amain())


if __name__ == "__main__":
    main()
