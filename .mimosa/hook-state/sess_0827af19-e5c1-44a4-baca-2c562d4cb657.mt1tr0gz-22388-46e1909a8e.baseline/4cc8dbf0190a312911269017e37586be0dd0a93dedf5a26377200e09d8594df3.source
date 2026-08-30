# -*- coding: utf-8 -*-
"""Resolve task_id from caller or explicit run_id→task map. Never infer."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_OPS = Path(__file__).resolve().parent.parent
DEFAULT_CONTEXT = _OPS / "state" / "cortex" / "active-task-context.json"


def load_run_to_task(path: Path | None = None) -> dict[str, str]:
    p = Path(path or DEFAULT_CONTEXT)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    out: dict[str, str] = {}
    if not isinstance(data, dict):
        return out
    mapping = data.get("run_to_task")
    if isinstance(mapping, dict):
        for k, v in mapping.items():
            ks, vs = str(k).strip(), str(v or "").strip()
            if ks and vs:
                out[ks] = vs[:64]
    run = str(data.get("run_id") or "").strip()
    task = str(data.get("task_id") or "").strip()
    if run and task:
        out[run] = task[:64]
    return out


def resolve(*, caller_task: str | None, run_id: str | None = None,
            context_path: Path | None = None,
            environ: dict | None = None) -> dict[str, Any]:
    """Return task_id/run_id/source/status. Does not synthesize IDs.

    Allowed sources: caller argument, explicit map, matching OCTOPUS_TASK_ID
    only when OCTOPUS_RUN_ID is set and equals run_id (process context).
    Forbidden: PID, timestamp, capability, model name.
    """
    env = environ if environ is not None else os.environ
    caller = str(caller_task or "").strip()[:64]
    run = str(run_id or "").strip()[:64]
    if not run:
        run = str(env.get("OCTOPUS_RUN_ID") or "").strip()[:64]
    if caller:
        return {
            "task_id": caller,
            "run_id": run or None,
            "task_id_source": "caller",
            "attribution_status": "resolved",
        }
    mapping = load_run_to_task(context_path)
    if run and run in mapping:
        return {
            "task_id": mapping[run],
            "run_id": run,
            "task_id_source": "context",
            "attribution_status": "resolved",
        }
    env_task = str(env.get("OCTOPUS_TASK_ID") or "").strip()[:64]
    env_run = str(env.get("OCTOPUS_RUN_ID") or "").strip()[:64]
    if env_task and env_run and (not run or run == env_run):
        return {
            "task_id": env_task,
            "run_id": env_run,
            "task_id_source": "context",
            "attribution_status": "resolved",
        }
    return {
        "task_id": None,
        "run_id": run or None,
        "task_id_source": "legacy_missing",
        "attribution_status": "unresolved",
    }
