#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sync_studio_pf_adapter.py — honest StudioPF adapter for LEG-SYNC.

Reality check: the current repo has Project-F/studio code and human workflow notes, but no
callable `buildModule` / `getBuildStatus` API. The correct fail-closed adapter therefore
blocks with a precise human next_action and never fabricates `module_id`.

The public shape deliberately mirrors the megaprompt contract while staying stdlib-only and
safe. The methods are synchronous; sync_agent can call them from async code because they do
no network or long-running work.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
_BUDGET = _OPS / "budget"
for _p in (str(_OPS), str(_BUDGET)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
try:
    import opslib  # noqa: E402
except Exception:  # noqa: BLE001
    opslib = None  # type: ignore


ERROR_CODE = "STUDIO_NO_BUILD_API"
HUMAN_LABEL = "build skeleton from _Templates (per PROJECT.md)"


def _now_iso() -> str:
    try:
        return opslib.now_iso() if opslib is not None else ""
    except Exception:  # noqa: BLE001
        return ""


class StudioPFAdapter:
    """No-op-on-purpose adapter: real contract surface, honest blocked result."""

    def __init__(self, event_sink=None):
        self.event_sink = event_sink

    def _event(self, trace_id: str, idempotency_key: str, method: str, extra=None) -> None:
        if not callable(self.event_sink):
            return
        try:
            self.event_sink({
                "at": _now_iso(),
                "source": "studio_pf",
                "type": "STUDIO_PF_BLOCKED_NO_API",
                "payload": {
                    "method": method,
                    "trace_id": str(trace_id or ""),
                    "idempotency_key": str(idempotency_key or ""),
                    **(extra or {}),
                },
            })
        except Exception:  # noqa: BLE001
            pass

    def buildModule(self, spec: dict, trace_id: str, idempotency_key: str) -> dict:  # noqa: N802
        self._event(trace_id, idempotency_key, "buildModule", {"spec_name": (spec or {}).get("name")})
        return {
            "ok": False,
            "state": "blocked",
            "error": ERROR_CODE,
            "message": "studio_pf has no callable buildModule/status API in this repo.",
            "next_action": {"type": "human_authorization", "label": HUMAN_LABEL},
            "idempotency_key": str(idempotency_key or ""),
        }

    def getBuildStatus(self, build_id: str, trace_id: str) -> dict:  # noqa: N802
        self._event(trace_id, f"status:{build_id}", "getBuildStatus", {"build_id": str(build_id or "")})
        return {
            "ok": False,
            "build_id": str(build_id or ""),
            "state": "blocked",
            "error": ERROR_CODE,
            "message": "No automated studio_pf status endpoint exists; human build/registration is required.",
            "next_action": {"type": "human_authorization", "label": HUMAN_LABEL},
        }


# snake_case aliases for callers that prefer Python naming.
def build_module(spec: dict, trace_id: str, idempotency_key: str) -> dict:
    return StudioPFAdapter().buildModule(spec, trace_id, idempotency_key)


def get_build_status(build_id: str, trace_id: str) -> dict:
    return StudioPFAdapter().getBuildStatus(build_id, trace_id)


if __name__ == "__main__":
    import json
    print(json.dumps(build_module({"name": "demo"}, "trace", "run:studio_build"),
                     ensure_ascii=False, indent=2))
