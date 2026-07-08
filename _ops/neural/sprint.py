#!/usr/bin/env python3
"""sprint.py — NI-7: SprintContract (Anthropic Harness).

هر sprint = scope + budget + deadline + context_reset.
Anthropic's pattern: bounded task unit with context clear.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class SprintContract:
    """یک sprintِ کران‌دار (Anthropic Harness pattern)."""
    sprint_id: str
    scope: str              # «چه سوال/گلوگاهی»
    budget_beats: int = 10  # max beats
    budget_tokens: int = 100
    deadline_ts: float = 0.0
    context_reset: bool = True  # بعد از sprint، context پاک

    def __post_init__(self):
        if self.deadline_ts == 0.0:
            self.deadline_ts = time.time() + self.budget_beats * 60


@dataclass
class SprintResult:
    """خروجیِ یک sprint."""
    sprint_id: str
    completed: bool
    timed_out: bool
    budget_exhausted: bool
    beats_used: int
    tokens_used: int
    insights: list[str] = field(default_factory=list)
    context_cleared: bool = False


class SprintRunner:
    """اجرای sprint با کران. context_reset بعد از هر sprint."""

    def __init__(self):
        self._current: SprintContract | None = None
        self._beats_used = 0
        self._tokens_used = 0
        self._insights: list[str] = []
        self._hooks: "HookBus | None" = None

    def set_hooks(self, hooks: "HookBus") -> None:
        self._hooks = hooks

    def start(self, contract: SprintContract) -> None:
        self._current = contract
        self._beats_used = 0
        self._tokens_used = 0
        self._insights = []
        if self._hooks:
            self._hooks.fire("pre_sprint", {"sprint_id": contract.sprint_id,
                                             "scope": contract.scope})

    def tick(self, tokens: int = 0, insight: str = "") -> bool:
        """یک beat از sprint. خروجی: continue؟ False = sprint تمام."""
        if self._current is None:
            return False
        self._beats_used += 1
        self._tokens_used += tokens
        if insight:
            self._insights.append(insight)

        if self._beats_used >= self._current.budget_beats:
            return False
        if self._tokens_used >= self._current.budget_tokens:
            return False
        if time.time() > self._current.deadline_ts:
            return False
        return True

    def finish(self) -> SprintResult:
        """پایانِ sprint. context reset."""
        if self._current is None:
            return SprintResult(sprint_id="none", completed=False,
                                timed_out=False, budget_exhausted=False,
                                beats_used=0, tokens_used=0)
        c = self._current
        result = SprintResult(
            sprint_id=c.sprint_id,
            completed=(self._beats_used < c.budget_beats
                       and self._tokens_used < c.budget_tokens),
            timed_out=(time.time() > c.deadline_ts),
            budget_exhausted=(self._tokens_used >= c.budget_tokens),
            beats_used=self._beats_used, tokens_used=self._tokens_used,
            insights=list(self._insights),
            context_cleared=c.context_reset)
        if self._hooks:
            self._hooks.fire("post_sprint", {"sprint_id": c.sprint_id,
                                              "result": result.completed})
        self._current = None  # context reset
        self._beats_used = 0
        self._tokens_used = 0
        self._insights = []
        return result

    @property
    def is_active(self) -> bool:
        return self._current is not None
