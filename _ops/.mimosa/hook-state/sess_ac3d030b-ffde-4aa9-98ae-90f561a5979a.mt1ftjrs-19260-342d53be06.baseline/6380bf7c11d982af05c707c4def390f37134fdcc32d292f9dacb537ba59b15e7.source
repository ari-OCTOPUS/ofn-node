#!/usr/bin/env python3
"""hooks.py — NI-8: HookBus (Anthropic patterns — lifecycle callbacks).

hooks بین فازها: pre_sprint, post_sprint, pre_think, post_think,
pre_publish, post_publish, on_error, on_verdict.
fail-soft: hook خراب = log + continue.
"""
from __future__ import annotations
from collections import defaultdict
from typing import Callable

VALID_HOOKS = frozenset({
    "pre_sprint", "post_sprint",
    "pre_think", "post_think",
    "pre_publish", "post_publish",
    "on_error", "on_verdict",
})


class HookBus:
    """registry برای lifecycle callbacks. fail-soft."""

    def __init__(self):
        self._hooks: dict[str, list[Callable]] = defaultdict(list)
        self._errors: list[dict] = []
        self._fired: list[str] = []

    def register(self, event: str, callback: Callable) -> None:
        if event not in VALID_HOOKS:
            self._errors.append({"event": event, "error": "invalid hook name"})
            return
        self._hooks[event].append(callback)

    def fire(self, event: str, data: dict | None = None) -> None:
        """صدا زدنِ همهٔ hookهای یک event. fail-soft."""
        self._fired.append(event)
        for cb in self._hooks.get(event, []):
            try:
                cb(data or {})
            except Exception as e:  # noqa: BLE001
                self._errors.append({"event": event, "error": str(e)[:100]})

    @property
    def errors(self) -> list[dict]:
        return list(self._errors)

    @property
    def fired_events(self) -> list[str]:
        return list(self._fired)

    @property
    def has_errors(self) -> bool:
        return len(self._errors) > 0
