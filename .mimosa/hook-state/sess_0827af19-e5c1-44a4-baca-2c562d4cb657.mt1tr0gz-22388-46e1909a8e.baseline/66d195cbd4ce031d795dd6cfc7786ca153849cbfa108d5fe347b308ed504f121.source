# -*- coding: utf-8 -*-
"""Kill switch overlay that COMPOSES with existing STOP files (INV-3).

Default: never writes live `_ops/STOP-ORGANISM`. Tests inject overlay + compose
paths under tempfile. Live compose is read-only unless write_live_stop=True
AND the owner sets OCTOPUS_V3_KILL_WRITES_STOP=1.
"""
from __future__ import annotations

import enum
import os
import time
from pathlib import Path

from .exceptions import KillEngaged
from .ledger import IntentLedger


class KillState(enum.Enum):
    DISARMED = "disarmed"
    ARMED = "armed"
    TRIGGERED = "triggered"


class KillSwitch:
    def __init__(
        self,
        overlay_path: Path,
        compose_paths: tuple[Path, ...] = (),
        *,
        write_live_stop: bool = False,
        live_stop_path: Path | None = None,
        ledger: IntentLedger | None = None,
    ) -> None:
        self.overlay_path = Path(overlay_path)
        self.compose_paths = tuple(Path(p) for p in compose_paths)
        env_ok = str(os.environ.get("OCTOPUS_V3_KILL_WRITES_STOP", "0")).strip() in ("1", "true", "yes")
        self.write_live_stop = bool(write_live_stop) and env_ok
        self.live_stop_path = Path(live_stop_path) if live_stop_path else None
        self.ledger = ledger

    def state(self) -> KillState:
        try:
            if self.overlay_path.exists():
                text = self.overlay_path.read_text("utf-8", errors="replace").strip().lower()
                if text == KillState.TRIGGERED.value:
                    return KillState.TRIGGERED
                if text == KillState.ARMED.value:
                    return KillState.ARMED
        except OSError:
            return KillState.TRIGGERED  # unreadable overlay = fail-closed halt
        return KillState.DISARMED

    def composed_stop_reason(self) -> str | None:
        for p in self.compose_paths:
            try:
                if p.exists():
                    return str(p)
            except OSError:
                return f"unreadable:{p}"
        return None

    def engaged(self) -> bool:
        return self.state() is KillState.TRIGGERED or self.composed_stop_reason() is not None

    def assert_clear(self) -> None:
        if self.engaged():
            raise KillEngaged(self.composed_stop_reason() or "v3 overlay TRIGGERED")

    def arm(self) -> None:
        self.overlay_path.parent.mkdir(parents=True, exist_ok=True)
        self.overlay_path.write_text(KillState.ARMED.value + "\n", encoding="utf-8")
        if self.ledger is not None:
            self.ledger.append("KILL_ARM", {"state": KillState.ARMED.value})

    def trigger(self, reason: str = "owner") -> float:
        """Engage halt. Returns elapsed seconds of the trigger write itself."""
        t0 = time.perf_counter()
        self.overlay_path.parent.mkdir(parents=True, exist_ok=True)
        self.overlay_path.write_text(KillState.TRIGGERED.value + "\n", encoding="utf-8")
        if self.write_live_stop and self.live_stop_path is not None:
            self.live_stop_path.parent.mkdir(parents=True, exist_ok=True)
            self.live_stop_path.write_text(f"v3-kill:{reason}\n", encoding="utf-8")
        if self.ledger is not None:
            self.ledger.append("KILL", {"reason": reason, "wrote_live_stop": self.write_live_stop})
        return time.perf_counter() - t0
