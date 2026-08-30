# -*- coding: utf-8 -*-
"""Lane-safe paths. Telegram trees are listed so writers can refuse them."""
from __future__ import annotations

import os
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
VAULT = _OPS.parent
# Unit 4 (2026-08-21): state باید env-override را ببیند (همان الگوی
# tg_api._poll_health_path) تا تست‌های ایزوله و run_all (با live-state guard)
# به temp خودشان بنویسند؛ درخت زنده فقط وقتی env خالی است هدف می‌شود.
_base = str(os.environ.get("OCTOPUS_STATE_DIR", "") or "").strip()
STATE = Path(_base) if _base else (_OPS / "state")
ORGANS_STATE = STATE / "organs"
INBOX = STATE / "cognition_inbox"
EVIDENCE = VAULT / "06-EVIDENCE" / "ORGAN-MAP-2026-08-20"

TELEGRAM_LANE_MARKERS = (
    "telegram_center",
    "telegram_cockpit",
    "state/telegram",
    "state\\telegram",
    "telegram_offset",
    "miniapp_gateway",
    "approval_channel.py",
    "pulse/telegram",
    "pulse\\telegram",
    "pulse/tg-center",
    "pulse\\tg-center",
)

SKIP_DIR_NAMES = {
    ".git", "_Archive", "_Duplicates", "_code", "__pycache__",
    "node_modules", ".claude", "worktrees", "venv", ".venv",
    "امواج مغزی", "Neuro-HRV-Nof1", "08 - Partner (PII)",
    "secrets-export",
}
SKIP_NAME_FRAGMENTS = (
    "MyHeritage", "23andme", "armin_dna", "OWNER-PROFILE",
    "GenomeInsight", "wallet", ".pem", ".env",
)


def is_telegram_lane(path: Path | str) -> bool:
    s = str(path).replace("\\", "/").lower()
    return any(m.replace("\\", "/").lower() in s for m in TELEGRAM_LANE_MARKERS)


def assert_not_telegram(path: Path | str) -> None:
    if is_telegram_lane(path):
        raise PermissionError(f"telegram-lane-forbidden: {path}")


def skip_path(path: Path) -> bool:
    parts = set(path.parts)
    if parts & SKIP_DIR_NAMES:
        return True
    name = path.name
    low = str(path).lower()
    if any(frag.lower() in low for frag in SKIP_NAME_FRAGMENTS):
        return True
    if name.endswith((".env", ".pem", ".key")):
        return True
    return False
