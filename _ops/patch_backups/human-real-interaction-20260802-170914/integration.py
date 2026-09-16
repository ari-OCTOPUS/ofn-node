#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""integration.py — Telegram control-plane entry hook (STAGED, not wired).

The single intended hook point in telegram_center/center.py:
    from agi2027_control.integration import try_handle_control
    res = try_handle_control(text, {"is_owner": is_owner})
    if res is not None:
        # render/send res, then return (do not fall through to other handlers)
        ...

This module is NOT called by any production path today (verified: 0 readers of
OCTOPUS_WIRE_TG_CONTROL / agi2027_control in _ops before this run). Wiring it is
a NEEDS_OWNER_HOOK decision, not something this file does for you.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_ROOT = Path(__file__).resolve().parents[2]  # _ops/agi2027_control -> F:\backup


def control_enabled(root: Path = DEFAULT_ROOT) -> bool:
    if os.getenv("OCTOPUS_WIRE_TG_CONTROL") == "1":
        return True
    flags = Path(root) / "_ops" / "agi2027_runtime" / "managed_flags.json"
    if flags.exists():
        try:
            return json.loads(flags.read_text(encoding="utf-8")).get("OCTOPUS_WIRE_TG_CONTROL") == "1"
        except Exception:
            return False
    return False


def try_handle_control(text: str, actor: Dict[str, Any], root: Path = DEFAULT_ROOT) -> Optional[Dict[str, Any]]:
    """Returns None when the control plane is disabled (so the caller falls through).

    When enabled, dispatches to ControlPlane.handle and returns its result dict.
    Never raises — any internal error is returned as a fail-closed dict.
    """
    if not control_enabled(root):
        return None
    try:
        # import lazily so importing this hook module has no cost when disabled
        import sys
        here = str(Path(__file__).resolve().parents[1])  # _ops
        if here not in sys.path:
            sys.path.insert(0, here)
        from agi2027_control.runtime import ControlPlane  # type: ignore
        return ControlPlane(root).handle(text, actor)
    except Exception as exc:  # noqa: BLE001 — fail-closed, never crash the handler chain
        return {"ok": False, "status": "ERROR", "reason": f"control_plane_exception:{type(exc).__name__}"}


def format_control_result(result: Dict[str, Any]) -> str:
    """Compact owner-facing Telegram text. No secrets; JSON tail is bounded."""
    try:
        ok = "✅" if result.get("ok") else "⚠️"
        status = str(result.get("status") or result.get("state") or "UNKNOWN")
        reason = str(result.get("reason") or result.get("detail") or "")
        lines = [f"{ok} <b>Octopus control</b>: <code>{status}</code>"]
        if reason:
            lines.append(f"علت/جزئیات: <code>{reason[:240]}</code>")
        reps = result.get("repairs")
        if isinstance(reps, list) and reps:
            vals = reps[:8]
            if vals and isinstance(vals[0], dict):
                vals = [str(v.get("action_id") or v.get("summary") or v) for v in vals]
            lines.append("repairها:\n" + "\n".join(f"• <code>{str(v)[:120]}</code>" for v in vals))
        if result.get("flags"):
            lines.append("flags: <code>" + json.dumps(result.get("flags"), ensure_ascii=False)[:500] + "</code>")
        if result.get("fugu"):
            fg = result.get("fugu") or {}
            lines.append(f"Fugu: files=<code>{fg.get('files_with_fugu')}</code> lines=<code>{fg.get('total_lines')}</code>")
        if result.get("impact"):
            im = result.get("impact") or {}
            lines.append(f"Impact {im.get('leg')}: <code>{im.get('verdict')}</code>")
        if result.get("counts") is not None:
            lines.append("Outbound: <code>" + json.dumps(result.get("counts"), ensure_ascii=False)[:500] + "</code>")
            if result.get("flag") is not None:
                lines.append(f"WAL flag: <code>{result.get('flag')}</code>")
        if result.get("projectf"):
            pf = result.get("projectf") or {}
            lines.append(f"Project-F: <code>{pf.get('status')}</code> — <code>{pf.get('reason', '')}</code>")
        return "\n".join(lines)[:3500]
    except Exception as exc:  # noqa: BLE001
        return f"⚠️ control result render failed: <code>{type(exc).__name__}</code>"
