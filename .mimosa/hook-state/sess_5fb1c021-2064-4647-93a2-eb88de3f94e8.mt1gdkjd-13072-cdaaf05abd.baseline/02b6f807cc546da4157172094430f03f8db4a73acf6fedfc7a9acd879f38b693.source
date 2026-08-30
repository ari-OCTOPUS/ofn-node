#!/usr/bin/env python3
"""Network-impossible adapter around the real ``cortex.model_router`` decision path.

The adapter does not simulate routing. It calls the production ``_ask_impl``
while replacing every model/provider seam with deterministic callables for the
duration of one invocation. Production globals are restored in ``finally``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import os
from typing import Any, Mapping

from test_intelligence.trace_schema import TraceSink, make_event


class _AbsentStop:
    def exists(self) -> bool:
        return False


@dataclass
class RouterScenario:
    keys: Mapping[str, bool] = field(default_factory=dict)
    local_result: Mapping[str, Any] | None = None
    paid_results: Mapping[str, Mapping[str, Any] | None] = field(default_factory=dict)
    paid_gate_open: bool = True
    paid_gate_reason: str = "mock-open"


@dataclass(frozen=True)
class RouterObservation:
    result: dict[str, Any]
    paid_attempts: tuple[str, ...]
    local_attempts: int

    def snapshot(self) -> dict[str, Any]:
        return {
            "ok": bool(self.result.get("ok")),
            "tier": self.result.get("tier"),
            "model": self.result.get("model"),
            "fallback_from": self.result.get("fallback_from"),
            "reason": self.result.get("reason"),
            "paid_attempts": list(self.paid_attempts),
            "local_attempts": self.local_attempts,
        }


def run(router_module, *, task: str, prompt: str, system: str = "",
        max_tokens: int = 128, tier: str | None = None,
        scenario: RouterScenario | None = None, trace_sink: TraceSink | None = None,
        trace_id: str = "router-test", event_id: str = "router-decision") -> RouterObservation:
    """Call the real route selector with local and paid provider seams mocked."""
    scenario = scenario or RouterScenario()
    required = ("_ask_impl", "local_llm", "keys_present", "paid_gate", "_ask_paid", "opslib")
    missing = [name for name in required if not hasattr(router_module, name)]
    if missing:
        raise RuntimeError("model_router SUT missing: " + ",".join(missing))

    paid_attempts: list[str] = []
    local_attempts = [0]

    def fake_local(*args, **kwargs):
        local_attempts[0] += 1
        return dict(scenario.local_result) if scenario.local_result is not None else None

    def fake_paid(which, *args, **kwargs):
        # Production `_ask_paid` checks paid_gate before constructing a client.
        # Preserve that boundary: a closed gate is not a provider attempt.
        if not scenario.paid_gate_open:
            return None
        paid_attempts.append(str(which))
        out = scenario.paid_results.get(str(which))
        return dict(out) if isinstance(out, Mapping) else None

    originals = {
        "local_ask": router_module.local_llm.ask,
        "keys_present": router_module.keys_present,
        "paid_gate": router_module.paid_gate,
        "ask_paid": router_module._ask_paid,
        "stop": router_module.opslib.STOP_ORGANISM,
        "halted": router_module.opslib.halted,
        "alert": router_module.opslib.alert,
        "context_fence": os.environ.get("OCTOPUS_WIRE_CONTEXT_FENCE"),
        "route_scorer": os.environ.get("CORTEX_ROUTE_SCORER"),
        "route_shadow": os.environ.get("OCTOPUS_WIRE_ROUTE_SHADOW"),
        "local_first": os.environ.get("CORTEX_LOCAL_FIRST"),
    }
    router_module.local_llm.ask = fake_local
    router_module.keys_present = lambda: {
        "fugu": bool(scenario.keys.get("fugu")),
        "glm": bool(scenario.keys.get("glm") or scenario.keys.get("deepseek")),
        "deepseek": bool(scenario.keys.get("deepseek")),
    }
    router_module.paid_gate = lambda: (bool(scenario.paid_gate_open),
                                        str(scenario.paid_gate_reason))
    router_module._ask_paid = fake_paid
    router_module.opslib.STOP_ORGANISM = _AbsentStop()
    router_module.opslib.halted = lambda *args, **kwargs: None
    router_module.opslib.alert = lambda *args, **kwargs: None
    for name in ("OCTOPUS_WIRE_CONTEXT_FENCE", "CORTEX_ROUTE_SCORER",
                 "OCTOPUS_WIRE_ROUTE_SHADOW", "CORTEX_LOCAL_FIRST"):
        os.environ.pop(name, None)
    try:
        result = router_module._ask_impl(task, prompt, system, max_tokens,
                                         tier=tier, opener=None, quality=None)
    finally:
        router_module.local_llm.ask = originals["local_ask"]
        router_module.keys_present = originals["keys_present"]
        router_module.paid_gate = originals["paid_gate"]
        router_module._ask_paid = originals["ask_paid"]
        router_module.opslib.STOP_ORGANISM = originals["stop"]
        router_module.opslib.halted = originals["halted"]
        router_module.opslib.alert = originals["alert"]
        for name, key in (("OCTOPUS_WIRE_CONTEXT_FENCE", "context_fence"),
                          ("CORTEX_ROUTE_SCORER", "route_scorer"),
                          ("OCTOPUS_WIRE_ROUTE_SHADOW", "route_shadow"),
                          ("CORTEX_LOCAL_FIRST", "local_first")):
            value = originals[key]
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    observation = RouterObservation(dict(result), tuple(paid_attempts), local_attempts[0])
    if trace_sink is not None:
        trace_sink.append(make_event(
            trace_id=trace_id, event_id=event_id,
            component="octopus.cortex.model_router", kind="route-decision",
            status="ok" if result.get("ok") else "failed",
            inputs={"task_class": str(task), "prompt_length": len(str(prompt)),
                    "system_present": bool(system), "max_tokens": max_tokens,
                    "tier_override": tier},
            outputs=observation.snapshot(), attempted=True, authorized=True,
            executed=True,
            tool_calls=[{"tier": value} for value in paid_attempts] +
                       ([{"tier": "local"}] * local_attempts[0]),
            state_mutations=(),
            reason_code=("fallback" if result.get("fallback_from") else
                         "failure" if result.get("reason") else "selected"),
        ))
    return observation
