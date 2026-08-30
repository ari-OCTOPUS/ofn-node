#!/usr/bin/env python3
"""Thin test adapter for the real ``budget.opslib.kill_seam_denies`` seam."""
from __future__ import annotations

import os
from pathlib import Path

from test_intelligence.trace_schema import TraceSink, make_event


def evaluate(opslib_module, *, stop_path: Path, armed: bool,
             trace_sink: TraceSink | None = None, trace_id: str = "kill-test",
             event_id: str = "kill-check") -> bool:
    """Inject a sandbox STOP path; never create or remove it here."""
    if not hasattr(opslib_module, "kill_seam_denies"):
        raise RuntimeError("opslib SUT lacks kill_seam_denies")
    flag = str(getattr(opslib_module, "KILL_SEAM_FLAG", "OCTOPUS_WIRE_KILL_SEAM"))
    old_stop = opslib_module.STOP_ORGANISM
    old_flag = os.environ.get(flag)
    opslib_module.STOP_ORGANISM = Path(stop_path)
    if armed:
        os.environ[flag] = "1"
    else:
        os.environ.pop(flag, None)
    try:
        denied = bool(opslib_module.kill_seam_denies())
    finally:
        opslib_module.STOP_ORGANISM = old_stop
        if old_flag is None:
            os.environ.pop(flag, None)
        else:
            os.environ[flag] = old_flag

    if trace_sink is not None:
        trace_sink.append(make_event(
            trace_id=trace_id, event_id=event_id,
            component="octopus.budget.kill_seam", kind="kill-check",
            status="blocked" if denied else "ok",
            inputs={"armed": armed, "stop_present": Path(stop_path).exists()},
            outputs={"denied": denied}, attempted=True, authorized=True,
            executed=True, tool_calls=(), state_mutations=(),
            reason_code="stop-organism" if denied else "not-denied",
        ))
    return denied
