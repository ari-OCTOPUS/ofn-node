"""langar_integration.py — اتصال لنگر و استودیوی صبا به هستهٔ اختاپوس.

این فایل نشان می‌دهد که چگونه langar_bot.py و saba_studio.py
باید به event_bus، capability_registry و telemetry وصل شوند.
به‌جای تغییر مستقیم فایل‌های production (که خطر regression دارد)،
این یک adaptor/wrapper است که در import-time به صورت optional attach می‌شود.

Usage (در langar_bot.py):
    from octopus_core.integration.langar_integration import attach_to_langar
    attach_to_langar(bot_instance, persist_dir=HERE / ".octopus")
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional

# مسیر octopus_core را به path اضافه کن (اگر قبلاً نباشد)
OCTOPUS_ROOT = Path(__file__).resolve().parent.parent.parent
if str(OCTOPUS_ROOT) not in sys.path:
    sys.path.insert(0, str(OCTOPUS_ROOT))

from octopus_core.event_bus import EventBus
from octopus_core.capability_registry import CapabilityRegistrySync
from octopus_core.telemetry import Telemetry
from octopus_core.health import OrganismHealth, HeartBeat


class LangarOctopusAdapter:
    """adaptor: LangarBot ↔ OctopusCore.

    وظایف:
      1) هر دستور langar را به event_bus publish کند (correlation_id propagation)
      2) capability_registry را با UI sync کند (dynamic render)
      3) telemetry از cost_spent و proposals بنویسد
      4) health heartbeat برای langar-organ بزند
    """

    def __init__(self, bot, persist_dir: Path):
        self.bot = bot
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.bus = EventBus(persist_dir=self.persist_dir / "bus")
        self.registry = CapabilityRegistrySync(path=self.persist_dir / "capabilities.json")
        self.telemetry = Telemetry(self.persist_dir / "telemetry.jsonl")
        self.health = OrganismHealth(self.persist_dir / "health", bus=self.bus)
        self._heartbeat = HeartBeat(self.health, "langar", interval_sec=60.0)

        self._register_capabilities()
        self._heartbeat.tick(status="attached")

    def _register_capabilities(self) -> None:
        # لنگر: همهٔ دستورات موجود را ثبت کن
        cmds = [
            ("/status", True, ""),
            ("/gates", True, ""),
            ("/verdicts", True, ""),
            ("/saba", True, ""),
            ("/brief", True, ""),       # heuristic ✅ یا offline 🔒 — صادقانه
            ("/think", True, ""),
            ("/upgrade", True, ""),     # propose-only ✅ executable
            ("/rules", True, ""),
            ("/kill", True, ""),
            ("/revive", True, ""),
            ("/kpi", False, "🔒 داشبورد KPI نیازمند دادهٔ post-launch و عبور از GATE 0"),
            ("/report", False, "🔒 گزارش‌گیری خودکار نیازمند دادهٔ واقعی (post-launch)"),
        ]
        for name, ok, reason in cmds:
            self.registry.register(name, category="ui", organ="langar",
                                   executable=ok, reason=reason)

        # صبا: دستورات MAIN_MENU (همه executable) + ADVANCED_MENU (coming-soon)
        saba_cmds = [
            ("s:new", True, ""),
            ("s:drafts", True, ""),
            ("s:today", True, ""),
            ("s:cal", True, ""),
            ("s:cap", True, ""),
            ("s:inbox", True, ""),
            ("s:scope", True, ""),
            ("s:rules", True, ""),
            ("s:brief", True, ""),
            ("s:trend", False, "🔒 brain offline — coming-soon"),
            ("s:ppv", False, "🔒 engine offline — coming-soon"),
            ("s:stats", False, "🔒 pre-launch — coming-soon"),
        ]
        for name, ok, reason in saba_cmds:
            self.registry.register(name, category="ui", organ="saba",
                                   executable=ok, reason=reason)

    def on_command(self, cmd: str, chat_id: int, text: str) -> Optional[dict]:
        """هر دستور langar را bus.publish + telemetry.record می‌کند."""
        start = time.time()
        ok, reason = self.registry.can_execute(cmd)
        if not ok:
            self.bus.publish("ui.command_blocked",
                             {"cmd": cmd, "reason": reason, "chat_id": chat_id},
                             source="langar")
            return {"blocked": True, "reason": reason}

        cid = f"CMD-{int(time.time()*1000)}-{chat_id}"
        self.bus.publish("ui.command", {"cmd": cmd, "text_preview": text[:60],
                                          "chat_id": chat_id},
                         correlation_id=cid, source="langar")
        dur_ms = (time.time() - start) * 1000
        self.telemetry.record(job_id=cid, worker="langar", intent=cmd,
                              duration_ms=dur_ms, cost_aud=0.0,
                              correlation_id=cid)
        self._heartbeat.tick(status="active")
        return {"correlation_id": cid, "blocked": False}

    def on_cost_spent(self, amount_aud: float, cap_aud: float) -> None:
        """وقتی CostMeter تغییر می‌کند، event publish + telemetry."""
        self.bus.publish("heart.energy", {"spent": amount_aud, "cap": cap_aud,
                                           "remaining": max(0, cap_aud - amount_aud)},
                         source="langar")
        self.telemetry.record(job_id=f"cost-{int(time.time()*1000)}",
                              worker="langar", intent="cost_meter_update",
                              duration_ms=0, cost_aud=amount_aud)
        self._heartbeat.tick(status="energy_pulse")


def attach_to_langar(bot, persist_dir: Optional[Path] = None) -> LangarOctopusAdapter:
    """Helper برای attach adaptor به LangarBot instance."""
    if persist_dir is None:
        persist_dir = Path(__file__).resolve().parent.parent.parent / ".octopus"
    return LangarOctopusAdapter(bot, persist_dir)
