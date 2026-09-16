#!/usr/bin/env python3
"""Default-OFF poll-path attach for owner-gated SenderBridge (arch-loop slice).

Enable only when OCTOPUS_TG_CENTER_SENDER_BRIDGE_ATTACH is truthy OR
_ops/TG-CENTER-SENDER-BRIDGE-ATTACH.flag exists. Even then, actual send is
refused by live_telegram_gate unless active writer-lock send_exceptions exist.
Never opens a network socket by itself.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

ENV = "OCTOPUS_TG_CENTER_SENDER_BRIDGE_ATTACH"
FLAG_NAME = "TG-CENTER-SENDER-BRIDGE-ATTACH.flag"


def _ops_root() -> Path:
    return Path(__file__).resolve().parents[1]


def attach_enabled(*, flag_path: Path | None = None) -> bool:
    env = str(os.environ.get(ENV, "")).strip().lower()
    if env in {"1", "true", "yes", "on"}:
        return True
    p = Path(flag_path) if flag_path is not None else (_ops_root() / FLAG_NAME)
    return p.is_file()


def maybe_run_after_poll(
    *,
    queue=None,
    send_fn: Callable[[dict], dict] | None = None,
    limit: int = 10,
    flag=None,
    lock=None,
    now=None,
    flag_path: Path | None = None,
) -> dict[str, Any]:
    """Call from center poll loop. Default: skip (attach off)."""
    if not attach_enabled(flag_path=flag_path):
        return {
            "ran": False,
            "skipped": True,
            "reason": "attach_default_off",
            "env": ENV,
        }
    if queue is None or send_fn is None:
        return {
            "ran": False,
            "skipped": False,
            "blocked": True,
            "reason": "missing_queue_or_send_fn",
        }
    import center_sender_bridge as csb

    bridge = csb.build_bridge(queue, send_fn)
    out = csb.run_once_if_allowed(bridge, limit=limit, flag=flag, lock=lock, now=now)
    out = dict(out)
    out["attach_enabled"] = True
    out["skipped"] = False
    return out
