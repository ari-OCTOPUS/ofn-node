"""Read-only mirror of board/snapshot actuator authority for homeo/metacontrol.

Soft-unlock SoT (owner-accepted): PERMITTED_SOFTWARE_A0 + SOFTWARE_LATCH.
Never sets ARMED. Never enables PWM/actuation.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

BOARD = Path("/etc/octopus/config/board.yaml")
SNAP_DIR = Path("/var/lib/octopus/state/snapshots")
ARMED_PATH = Path("/var/lib/octopus/state/reflex/ARMED.json")

SOFT_OK = "PERMITTED_SOFTWARE_A0"
NONE = "NONE"
VALID = {NONE, SOFT_OK}


def _armed() -> bool:
    if not ARMED_PATH.exists():
        return False
    try:
        doc = json.loads(ARMED_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    if isinstance(doc, dict):
        return bool(doc.get("armed") is True or doc.get("ARMED") is True)
    return "true" in ARMED_PATH.read_text(encoding="utf-8").lower()


def _from_board() -> dict[str, Any]:
    if not BOARD.exists():
        return {}
    text = BOARD.read_text(encoding="utf-8")
    out: dict[str, Any] = {"source": "board.yaml"}
    m = re.search(r"^\s*actuator_authority:\s*(\S+)", text, re.M)
    if m:
        out["actuator_authority"] = m.group(1).strip().strip("\"'")
    m = re.search(r"^\s*estop_channel:\s*(\S+)", text, re.M)
    if m:
        out["estop_channel"] = m.group(1).strip().strip("\"'")
    m = re.search(r"^\s*safety_state:\s*(\S+)", text, re.M)
    if m:
        out["safety_state"] = m.group(1).strip().strip("\"'")
    return out


def _from_snapshot() -> dict[str, Any]:
    if not SNAP_DIR.is_dir():
        return {}
    paths = sorted(SNAP_DIR.glob("snapshot-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not paths:
        return {}
    try:
        doc = json.loads(paths[0].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    safety = doc.get("safety") if isinstance(doc.get("safety"), dict) else {}
    return {
        "source": str(paths[0]),
        "actuator_authority": doc.get("actuator_authority") or safety.get("actuator_authority"),
        "estop_channel": safety.get("estop_channel"),
        "safety_state": safety.get("safety_state"),
    }


def resolve_authority_mirror() -> dict[str, Any]:
    """Return mirror fields for homeo/metacontrol labels (observe-only)."""
    snap = _from_snapshot()
    board = _from_board()
    # Prefer live snapshot when present; fall back to signed board.
    auth = snap.get("actuator_authority") or board.get("actuator_authority") or NONE
    estop = snap.get("estop_channel") or board.get("estop_channel")
    safety_state = snap.get("safety_state") or board.get("safety_state")
    if auth not in VALID:
        auth = NONE
    armed = _armed()
    # Soft unlock is valid only with software latch and ARMED=false.
    soft_ok = auth == SOFT_OK and estop == "SOFTWARE_LATCH" and not armed
    if auth == SOFT_OK and not soft_ok:
        # Refuse to mirror a soft permit that violates latch/armed contract.
        auth = NONE
        note = "soft_permit_refused_missing_latch_or_armed"
    else:
        note = "mirrored_soft_unlock" if auth == SOFT_OK else "mirrored_none"
    return {
        "actuator_authority": auth,
        "estop_channel": estop,
        "safety_state": safety_state,
        "ARMED": False if not armed else True,
        "mirror_source": snap.get("source") or board.get("source") or "default",
        "soft_unlock_ok": soft_ok or auth == NONE,
        "note": note,
        "board": board,
        "snapshot": {k: snap.get(k) for k in ("actuator_authority", "estop_channel", "safety_state", "source")},
    }


def is_wave0_authority_ok(authority: str | None, estop_channel: str | None = None, armed: bool | None = None) -> bool:
    auth = authority or NONE
    if armed is None:
        armed = _armed()
    if armed:
        return False
    if auth == NONE:
        return True
    if auth == SOFT_OK and (estop_channel or resolve_authority_mirror().get("estop_channel")) == "SOFTWARE_LATCH":
        return True
    return False
