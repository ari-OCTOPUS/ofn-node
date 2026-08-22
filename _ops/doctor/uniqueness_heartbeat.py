#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Continuous doctor-heartbeat uniqueness probe (RO / fail-closed).

Called from wiring.doctor_uniqueness_beat on organism Pacemaker cadence.
Never live-sends Telegram. Never restarts telegram_center.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))


def run_uniqueness_heartbeat(
    beat: int = 0,
    *,
    state_dir=None,
    dry_run: bool = True,
    center_pids=None,
    scan_live_pids: bool | None = None,
    require_lock_pid_alive: bool | None = None,
    alert=None,
) -> dict[str, Any]:
    """Execute uniqueness check + receipt. Always live_send=False."""
    import poller_uniqueness as _pu  # noqa: WPS433

    if center_pids is not None:
        _scan = False if scan_live_pids is None else bool(scan_live_pids)
        _alive = False if require_lock_pid_alive is None else bool(require_lock_pid_alive)
    else:
        _scan = True if scan_live_pids is None else bool(scan_live_pids)
        _alive = True if require_lock_pid_alive is None else bool(require_lock_pid_alive)

    try:
        uniq = _pu.check_poller_uniqueness(
            state_dir=state_dir,
            center_pids=center_pids,
            scan_live_pids=_scan,
            require_lock_pid_alive=_alive,
        )
    except Exception as e:  # noqa: BLE001 — fail-closed
        uniq = {
            "ok": False,
            "fail_closed": True,
            "live_send": False,
            "dry_run_safe": True,
            "reasons": [f"check_error:{type(e).__name__}"],
            "checks": {},
            "center_pids": list(center_pids or []),
            "center_pid_count": len(center_pids or []),
            "active_lease_count": None,
            "tg_poller_lock_count": None,
            "paths": {},
            "probe": "poller-uniqueness/1",
        }
        if alert is not None:
            try:
                alert([f"doctor_uniqueness check error: {type(e).__name__}: {e}"])
            except Exception:  # noqa: BLE001
                pass

    receipt = _pu.record_uniqueness_receipt(
        uniq,
        state_dir=state_dir,
        beat=beat,
        source="doctor_uniqueness_beat",
        dry_run=bool(dry_run),
    )
    if not uniq.get("ok") and alert is not None:
        try:
            alert([
                "poller_uniqueness FAIL-CLOSED: "
                + ",".join(str(x) for x in (uniq.get("reasons") or [])[:6])
            ])
        except Exception:  # noqa: BLE001
            pass

    return {
        "poller_uniqueness": uniq,
        "receipt_path": receipt.get("path"),
        "ok": bool(uniq.get("ok")),
        "live_send": False,
        "dry_run": bool(dry_run),
        "beat": int(beat or 0),
    }


__all__ = ["run_uniqueness_heartbeat"]
