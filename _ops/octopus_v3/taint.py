# -*- coding: utf-8 -*-
"""G4 task taint latch — not an 'escalate one level' modifier.

Once a task accepts untrusted / injection-class input, network.mode=none for
the remainder of that task. The latch does not reset itself.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TaintRecord:
    tainted: bool = False
    sources: list[str] = field(default_factory=list)


class TaskTaintLatch:
    def __init__(self) -> None:
        self._tasks: dict[str, TaintRecord] = {}

    def mark(self, task_id: str, source: str) -> None:
        rec = self._tasks.setdefault(task_id, TaintRecord())
        rec.tainted = True
        rec.sources.append(source)

    def is_tainted(self, task_id: str) -> bool:
        rec = self._tasks.get(task_id)
        return bool(rec and rec.tainted)

    def network_mode(self, task_id: str, requested: str = "allowlist") -> str:
        """requested is ignored once latched — always none."""
        if self.is_tainted(task_id):
            return "none"
        if requested not in ("none", "allowlist", "open"):
            return "none"  # unknown → fail-closed
        return requested
