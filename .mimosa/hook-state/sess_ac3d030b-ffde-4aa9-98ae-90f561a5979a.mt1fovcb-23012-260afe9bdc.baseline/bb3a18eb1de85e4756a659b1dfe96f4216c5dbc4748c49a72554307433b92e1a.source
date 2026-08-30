#!/usr/bin/env python3
"""No-network adapter around the real deterministic Collaborator handler."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from test_intelligence.trace_schema import TraceSink, make_event


def run(collaborator_module, *, text: str, enabled: bool = True,
        state_dir: Path | None = None, trace_sink: TraceSink | None = None,
        trace_id: str = "collab-test", event_id: str = "collab-turn") -> dict[str, Any]:
    """Invoke production ``handle`` while forcing its unconnected model path off."""
    if not hasattr(collaborator_module, "handle"):
        raise RuntimeError("collaborator SUT lacks handle")
    names = ("OCTOPUS_WIRE_COLLAB", "OCTOPUS_COLLAB_USE_MODEL",
             "OCTOPUS_WIRE_COLLAB_MEMORY", "OCTOPUS_STATE_DIR")
    previous = {name: os.environ.get(name) for name in names}
    if enabled:
        os.environ["OCTOPUS_WIRE_COLLAB"] = "1"
    else:
        os.environ.pop("OCTOPUS_WIRE_COLLAB", None)
    os.environ.pop("OCTOPUS_COLLAB_USE_MODEL", None)
    os.environ.pop("OCTOPUS_WIRE_COLLAB_MEMORY", None)
    if state_dir is not None:
        os.environ["OCTOPUS_STATE_DIR"] = str(Path(state_dir).resolve())
    try:
        reply = dict(collaborator_module.handle(text, state_dir=state_dir))
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    if trace_sink is not None:
        trace_sink.append(make_event(
            trace_id=trace_id, event_id=event_id,
            component="octopus.owner_console.collaborator", kind="collab-turn",
            status="ok" if reply.get("schema") == "owner-console.reply.v1" else "failed",
            inputs={"input_kind": "owner-text", "input_length": len(str(text))},
            outputs={"schema": reply.get("schema"), "kind": reply.get("kind"),
                     "external_effect": reply.get("external_effect"),
                     "estimated_cost": reply.get("estimated_cost"),
                     "send_attempted": reply.get("send_attempted")},
            attempted=True, authorized=True, executed=True,
            tool_calls=(), state_mutations=(), reason_code=str(reply.get("kind") or "reply"),
        ))
    return reply
