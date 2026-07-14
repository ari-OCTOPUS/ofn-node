#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_telegram_commands.py — CH-15b: Telegram Command Registry Extractor

Reads:
  • _ops/telegram_center/center.py          → center COMMANDS registry + handle_update
  • _ops/budget/approval_channel.py         → TelegramApprovalChannel menu + handlers
  • _ops/state/telegram/center-config.json  → config (chat_id, topics, commands_set)
  • _ops/state/telegram_offset.json         → poll offset health
  • _ops/state/pulse/telegram-poll.json     → poll pulse health

Emits:
  nervous-system/telegram-commands-data.js → window.TELEGRAM_COMMANDS_DATA

Schema contract (for verify_schema.py):
  .bot: {wired, live, mode, owner_chat_id_masked, center_chat_id_masked, health_score, health_label}
  .commands: [{command, description, mode, wired, handler_location, safety_label, example}]
  .modes: {read_only[], propose_only[], owner_verdict[], not_yet_wired[]}
  .summary: {total, wired_count, read_only_count, propose_only_count, not_yet_wired_count}
  .generated: ISO timestamp

Safety: $0 offline, stdlib-only, read-only. No secrets emitted.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

OPS_DIR = Path("F:/backup/_ops")
NS_DIR = Path("F:/backup/nervous-system")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_json(path: Path, default: dict | None = None) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else (default or {})
    except (OSError, ValueError):
        return default or {}


def _mask_id(v: int | str | None) -> str:
    """Mask chat ID: show last 4 digits only."""
    s = str(v or "")
    if len(s) <= 4:
        return "****"
    return "****" + s[-4:]


def _parse_center_commands(text: str) -> list[dict]:
    """Parse center.py COMMANDS list."""
    cmds: list[dict] = []
    m = re.search(r"COMMANDS:\s*list\[.*?\]\s*=\s*(\[.*?\])", text, re.DOTALL)
    if not m:
        return cmds
    try:
        raw = eval(m.group(1), {"__builtins__": {}}, {})
        for item in raw:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                cmds.append({
                    "command": str(item[0]).lstrip("/"),
                    "description": str(item[1]),
                    "source": "center.py",
                })
    except Exception:
        pass
    return cmds


def _parse_approval_channel_menu(text: str) -> list[dict]:
    """Parse approval_channel.py _set_my_commands menu."""
    cmds: list[dict] = []
    m = re.search(r"def\s+_set_my_commands\(self\).*?(commands\s*=\s*\[.*?\])", text, re.DOTALL)
    if not m:
        return cmds
    block = m.group(1)
    for match in re.finditer(r'\{\s*"command"\s*:\s*"([^"]+)"\s*,\s*"description"\s*:\s*"([^"]+)"\s*\}', block):
        cmds.append({
            "command": match.group(1).lstrip("/"),
            "description": match.group(2),
            "source": "approval_channel.py:_set_my_commands",
        })
    return cmds


def _parse_approval_channel_handlers(text: str) -> set[str]:
    """Find which commands have actual handler branches in handle_command."""
    wired: set[str] = set()
    for match in re.finditer(r'if\s+t\s*==\s*"/(\w+)"', text):
        wired.add(match.group(1))
    for match in re.finditer(r'if\s+t\s+in\s+\(([^)]+)\)', text):
        inner = match.group(1)
        for cm in re.finditer(r'"/(\w+)"', inner):
            wired.add(cm.group(1))
    if 'if t.startswith("/lead ")' in text:
        wired.add("lead")
    if 'if t.startswith("/claim ")' in text:
        wired.add("claim")
    if 'if t.startswith("/conflict ")' in text:
        wired.add("conflict")
    if 'if t == "/reveal" or t.startswith("/reveal ")' in text:
        wired.add("reveal")
    return wired


def _build_wave6_safe_surface(center_py_text: str) -> list[dict]:
    """The Wave 6 SAFE command surface — reflects actual center.py handler reality."""
    # Detect which commands have real _cmd_* handlers in center.py
    has_handler = {}
    for cmd in ("status", "queue", "approvals", "risk", "help", "refresh", "now"):
        has_handler[cmd] = f"def _cmd_{cmd}(" in center_py_text
    # callback verdicts are also wired
    callbacks_wired = "_handle_callback" in center_py_text

    def _mode(cmd: str) -> str:
        if cmd in ("status", "queue", "approvals", "risk", "help", "now"):
            return "READ-ONLY"
        if cmd == "refresh":
            return "PROPOSE-ONLY"
        if cmd in ("ok", "no", "later"):
            return "OWNER VERDICT"
        return "NOT YET WIRED"

    def _wired(cmd: str) -> str:
        if has_handler.get(cmd, False):
            return "implemented"
        if cmd == "refresh" and has_handler.get("refresh", False):
            return "implemented"
        return "stub"

    def _safety(cmd: str) -> str:
        if _mode(cmd) == "READ-ONLY":
            return "فقط‌خواندنی — هیچ اثری اجرا نمی‌شود"
        if _mode(cmd) == "PROPOSE-ONLY":
            return "فقط پیشنهاد — ثبتِ intent در لاگ؛ هیچ اثری اجرا نمی‌شود"
        if _mode(cmd) == "OWNER VERDICT":
            return "نیاز به تأییدِ مالک — هیچ اثری خودکار اجرا نمی‌شود"
        return "هنوز سیم‌کشی نشده"

    def _handler_loc(cmd: str) -> str:
        if has_handler.get(cmd, False):
            return f"center.py:_cmd_{cmd}"
        if cmd in ("ok", "no", "later") and callbacks_wired:
            return "center.py:_handle_callback"
        return "none"

    cmds = []
    for cmd in ("status", "queue", "approvals", "risk", "help", "refresh", "now"):
        cmds.append({
            "command": cmd,
            "description": {
                "status": "📊 وضعیتِ ارگانیسم — خلاصهٔ یک‌نگاه",
                "queue": "📥 صفِ تأیید — آیتم‌های در انتظارِ مالک",
                "approvals": "📋 تاریخچهٔ تأییدها — آخرین verdictهای مالک",
                "risk": "🛡 رادارِ ریسک — blockers + health score",
                "help": "❓ راهنمای دستورات — با برچسبِ ایمنی",
                "refresh": "🔄 درخواستِ تازه‌سازیِ داده — ثبتِ intent",
                "now": "📊 وضعیت — همین حالا (legacy)",
            }.get(cmd, cmd),
            "mode": _mode(cmd),
            "wired": _wired(cmd),
            "handler_location": _handler_loc(cmd),
            "safety_label": _safety(cmd),
        })

    if callbacks_wired:
        for v in ("ok", "no", "later"):
            cmds.append({
                "command": v,
                "description": f"verdict callback: {v}",
                "mode": "OWNER VERDICT",
                "wired": "implemented",
                "handler_location": "center.py:_handle_callback",
                "safety_label": "نیاز به تأییدِ مالک — هیچ اثری خودکار اجرا نمی‌شود",
            })
    return cmds


def main() -> None:
    os.makedirs(NS_DIR, exist_ok=True)
    generated = _now_iso()

    center_cfg = _read_json(OPS_DIR / "state" / "telegram" / "center-config.json")
    offset_data = _read_json(OPS_DIR / "state" / "telegram_offset.json")
    poll_pulse = _read_json(OPS_DIR / "state" / "pulse" / "telegram-poll.json")

    center_py_text = ""
    try:
        center_py_text = (OPS_DIR / "telegram_center" / "center.py").read_text("utf-8")
    except OSError:
        pass

    approval_py_text = ""
    try:
        approval_py_text = (OPS_DIR / "budget" / "approval_channel.py").read_text("utf-8")
    except OSError:
        pass

    center_cmds = _parse_center_commands(center_py_text)
    menu_cmds = _parse_approval_channel_menu(approval_py_text)
    wired_cmds = _parse_approval_channel_handlers(approval_py_text)

    command_map: dict[str, dict] = {}

    for cmd in _build_wave6_safe_surface(center_py_text):
        command_map[cmd["command"]] = cmd

    for cmd in _build_wave6_safe_surface(center_py_text):
        command_map[cmd["command"]] = cmd

    for c in center_cmds:
        key = c["command"]
        if key not in command_map and has_handler.get(key, False):
            command_map[key] = {
                "command": key,
                "description": c["description"],
                "mode": "READ-ONLY",
                "wired": "implemented",
                "handler_location": "center.py:_cmd_" + key,
                "safety_label": "فقط‌خواندنی — هیچ اثری اجرا نمی‌شود",
            }

    for c in menu_cmds:
        key = c["command"]
        is_wired = key in wired_cmds
        if key not in command_map:
            mode = "OWNER VERDICT" if key in ("stop",) else ("PROPOSE-ONLY" if key in ("lead", "claim", "conflict", "reveal") else "READ-ONLY")
            command_map[key] = {
                "command": key,
                "description": c["description"],
                "mode": mode,
                "wired": "implemented" if is_wired else "menu-only",
                "handler_location": f"approval_channel.py:handle_command" if is_wired else "approval_channel.py:_set_my_commands (no handler)",
                "safety_label": "فقط‌خواندنی — هیچ اثری اجرا نمی‌شود" if mode == "READ-ONLY" else "نیاز به تأییدِ مالک — هیچ اثری خودکار اجرا نمی‌شود",
                "example": f"/{key} → {c['description']}",
            }

    commands_set = bool(center_cfg.get("commands_set"))
    chat_id = center_cfg.get("chat_id")
    last_offset = offset_data.get("offset")
    offset_saved_at = offset_data.get("saved_at")
    poll_ts = poll_pulse.get("ts")

    score = 0
    score += 30 if commands_set else 0
    score += 30 if chat_id is not None else 0

    offset_age_ok = False
    if offset_saved_at and isinstance(offset_saved_at, str):
        try:
            dt = datetime.fromisoformat(offset_saved_at.replace("Z", "+00:00"))
            age_h = (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0
            offset_age_ok = age_h < 24
        except Exception:
            pass
    score += 20 if offset_age_ok else 0

    poll_age_ok = False
    if poll_ts and isinstance(poll_ts, str):
        try:
            dt = datetime.fromisoformat(poll_ts.replace("Z", "+00:00"))
            age_h = (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0
            poll_age_ok = age_h < 2
        except Exception:
            pass
    score += 20 if poll_age_ok else 0

    health_label = "سالم" if score >= 80 else ("هشدار" if score >= 50 else "بحرانی")

    commands_list = list(command_map.values())
    commands_list.sort(key=lambda x: (
        0 if x["mode"] == "READ-ONLY" else (
            1 if x["mode"] == "PROPOSE-ONLY" else (
                2 if x["mode"] == "OWNER VERDICT" else 3
            )
        ),
        x["command"],
    ))

    read_only = [c["command"] for c in commands_list if c["mode"] == "READ-ONLY"]
    propose_only = [c["command"] for c in commands_list if c["mode"] == "PROPOSE-ONLY"]
    owner_verdict = [c["command"] for c in commands_list if c["mode"] == "OWNER VERDICT"]
    not_yet_wired = [c["command"] for c in commands_list if c["wired"] in ("stub", "menu-only")]

    payload = {
        "generated": generated,
        "bot": {
            "wired": chat_id is not None,
            "live": commands_set and chat_id is not None,
            "connection_health": {
                "connected": commands_set and chat_id is not None,
            },
            "mode": "SHADOW / PROPOSE-ONLY" if score < 80 else "READ-ONLY + PROPOSE-ONLY",
            "owner_chat_id_masked": _mask_id(center_cfg.get("owner_chat_id")),
            "center_chat_id_masked": _mask_id(chat_id),
            "health_score": score,
            "health_label": health_label,
            "commands_set": commands_set,
            "offset_age_ok": offset_age_ok,
            "poll_age_ok": poll_age_ok,
        },
        "commands": commands_list,
        "modes": {
            "read_only": read_only,
            "propose_only": propose_only,
            "owner_verdict": owner_verdict,
            "not_yet_wired": not_yet_wired,
        },
        "safety_summary": {
            "read_only_count": len(read_only),
            "propose_only_count": len(propose_only),
            "not_yet_wired_count": len(not_yet_wired),
            "unsafe_count": len(owner_verdict),
        },
        "summary": {
            "total": len(commands_list),
            "wired_count": sum(1 for c in commands_list if c["wired"] == "implemented"),
            "partial_count": sum(1 for c in commands_list if c["wired"] == "partial"),
            "stub_count": sum(1 for c in commands_list if c["wired"] == "stub"),
            "menu_only_count": sum(1 for c in commands_list if c["wired"] == "menu-only"),
            "read_only_count": len(read_only),
            "propose_only_count": len(propose_only),
            "owner_verdict_count": len(owner_verdict),
            "not_yet_wired_count": len(not_yet_wired),
        },
    }

    js_path = NS_DIR / "telegram-commands-data.js"
    js = "window.TELEGRAM_COMMANDS_DATA = " + json.dumps(payload, ensure_ascii=False, default=str) + ";\n"
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(js)

    print(f"telegram-commands-data.js refreshed: {len(js)} chars, {len(commands_list)} commands")


if __name__ == "__main__":
    main()
