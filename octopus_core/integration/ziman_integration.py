"""ziman_integration.py — اتصال control-brain و ziman-agent به هستهٔ اختاپوس.

این فایل adaptor/wrapper است برای:
  • ProjectManager (control-brain) → event_bus + telemetry + health
  • ziman-agent/worker.py → telemetry + health + capability registry

Usage (در app.py):
    from octopus_core.integration.ziman_integration import attach_to_control_brain
    adapter = attach_to_control_brain(manager, persist_dir=state_dir / ".octopus")
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional

OCTOPUS_ROOT = Path(__file__).resolve().parent.parent.parent
if str(OCTOPUS_ROOT) not in sys.path:
    sys.path.insert(0, str(OCTOPUS_ROOT))

from octopus_core.event_bus import EventBus
from octopus_core.capability_registry import CapabilityRegistry
from octopus_core.telemetry import Telemetry
from octopus_core.health import OrganismHealth, HeartBeat
from octopus_core.actuator import Actuator, ActuatorMode


class ControlBrainAdapter:
    """adaptor: ProjectManager ↔ OctopusCore.

    وظایف:
      1) هر start/stop/test به event_bus publish + telemetry
      2) health heartbeat برای هر پروژه
      3) actuator به‌جای subprocess.Popen برای actionهای بیرونی (future)
    """

    def __init__(self, manager, persist_dir: Path):
        self.manager = manager
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.bus = EventBus(persist_dir=self.persist_dir / "bus")
        self.telemetry = Telemetry(self.persist_dir / "telemetry.jsonl")
        self.health = OrganismHealth(self.persist_dir / "health", bus=self.bus)
        self.actuator = Actuator(
            mode=ActuatorMode.SHADOW,  # فعلاً shadow — تا approval wiring
            persist_dir=self.persist_dir / "actuator",
        )

        # ثبت قابلیت‌های control-brain
        self._registry = CapabilityRegistry(path=self.persist_dir / "capabilities.json")
        for name in ("status", "start", "stop", "test", "halt", "resume", "queue"):
            self._registry.register(name, category="api", organ="control_brain",
                                    executable=True)

        self._heartbeat = HeartBeat(self.health, "control_brain", interval_sec=60.0)
        self._heartbeat.tick(status="attached")

    def wrap_start(self, pid: str, actor=None) -> dict:
        """start را telemetry + event می‌کند."""
        start = time.time()
        result = self.manager.start(pid, actor)
        dur_ms = (time.time() - start) * 1000
        cid = f"ZIM-{int(time.time()*1000)}-{pid}"
        self.bus.publish("brain.goal", {"action": "start", "pid": pid,
                                         "state": result.state.value,
                                         "detail": result.detail},
                         correlation_id=cid, source="control_brain")
        self.telemetry.record(job_id=cid, worker="control_brain", intent="start",
                              duration_ms=dur_ms, cost_aud=0.0,
                              outcome={"pid": pid, "state": result.state.value},
                              correlation_id=cid)
        self.health.beat(f"project_{pid}", status="running" if result.state.value == "running" else "stopped")
        self._heartbeat.tick(status="active")
        return {"result": result, "correlation_id": cid}

    def wrap_stop(self, pid: str, actor=None) -> dict:
        start = time.time()
        result = self.manager.stop(pid, actor)
        dur_ms = (time.time() - start) * 1000
        cid = f"ZIM-{int(time.time()*1000)}-{pid}"
        self.bus.publish("brain.goal", {"action": "stop", "pid": pid,
                                         "state": result.state.value},
                         correlation_id=cid, source="control_brain")
        self.telemetry.record(job_id=cid, worker="control_brain", intent="stop",
                              duration_ms=dur_ms, cost_aud=0.0,
                              outcome={"pid": pid, "state": result.state.value},
                              correlation_id=cid)
        self.health.beat(f"project_{pid}", status="stopped")
        self._heartbeat.tick(status="active")
        return {"result": result, "correlation_id": cid}

    def wrap_test(self, pid: str, actor=None) -> dict:
        start = time.time()
        ok, out = self.manager.test(pid, actor)
        dur_ms = (time.time() - start) * 1000
        cid = f"ZIM-{int(time.time()*1000)}-{pid}"
        self.bus.publish("brain.goal", {"action": "test", "pid": pid, "ok": ok},
                         correlation_id=cid, source="control_brain")
        self.telemetry.record(job_id=cid, worker="control_brain", intent="test",
                              duration_ms=dur_ms, cost_aud=0.0,
                              outcome={"pid": pid, "ok": ok},
                              correlation_id=cid)
        self._heartbeat.tick(status="active")
        return {"ok": ok, "out": out, "correlation_id": cid}


class ZimanWorkerAdapter:
    """adaptor: ziman-agent/worker.py ↔ OctopusCore.

    وظایف:
      1) هر draft generation → telemetry + event
      2) health heartbeat برای worker
      3) capability registry برای worker capabilities
    """

    def __init__(self, worker_root: Path, persist_dir: Path):
        self.worker_root = Path(worker_root)
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.bus = EventBus(persist_dir=self.persist_dir / "bus")
        self.telemetry = Telemetry(self.persist_dir / "telemetry.jsonl")
        self.health = OrganismHealth(self.persist_dir / "health", bus=self.bus)
        self.registry = CapabilityRegistry(path=self.persist_dir / "capabilities.json")

        for name in ("generate_draft", "generate_dms", "generate_posts",
                     "campaign_check", "selftest"):
            self.registry.register(name, category="arm", organ="ziman_worker", executable=True)

        self._heartbeat = HeartBeat(self.health, "ziman_worker", interval_sec=60.0)
        self._heartbeat.tick(status="attached")

    def on_draft(self, kind: str, mode: str, duration_ms: float, cost_aud: float = 0.0) -> str:
        cid = f"ZMW-{int(time.time()*1000)}"
        self.bus.publish("arm.action", {"kind": kind, "mode": mode},
                         correlation_id=cid, source="ziman_worker")
        self.telemetry.record(job_id=cid, worker="ziman_worker", intent=f"draft_{kind}",
                              duration_ms=duration_ms, cost_aud=cost_aud,
                              correlation_id=cid)
        self._heartbeat.tick(status="active")
        return cid

    def on_selftest(self, ok: bool, duration_ms: float) -> str:
        cid = f"ZMW-{int(time.time()*1000)}"
        self.bus.publish("arm.health", {"ok": ok}, correlation_id=cid, source="ziman_worker")
        self.telemetry.record(job_id=cid, worker="ziman_worker", intent="selftest",
                              duration_ms=duration_ms, cost_aud=0.0,
                              outcome={"ok": ok}, correlation_id=cid)
        self._heartbeat.tick(status="healthy" if ok else "unhealthy")
        return cid


def attach_to_control_brain(manager, persist_dir: Optional[Path] = None) -> ControlBrainAdapter:
    if persist_dir is None:
        persist_dir = Path(__file__).resolve().parent.parent.parent / ".octopus"
    return ControlBrainAdapter(manager, persist_dir)


def attach_to_ziman_worker(worker_root: Optional[Path] = None,
                           persist_dir: Optional[Path] = None) -> ZimanWorkerAdapter:
    if persist_dir is None:
        persist_dir = Path(__file__).resolve().parent.parent.parent / ".octopus"
    if worker_root is None:
        worker_root = Path(__file__).resolve().parent.parent.parent / "ziman-agent"
    return ZimanWorkerAdapter(worker_root, persist_dir)
