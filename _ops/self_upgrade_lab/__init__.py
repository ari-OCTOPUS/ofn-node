# -*- coding: utf-8 -*-
"""Autonomous self-upgrade lab — observe → diagnose → patch in a worktree → test → verify → learn.

Never writes experimental patches onto the live production tree. Paid API calls are
forbidden until the owner sets an explicit daily budget.
"""
from __future__ import annotations

__all__ = ["LAB_DIR", "STATE_DIR", "ROOT"]

from pathlib import Path

LAB_DIR = Path(__file__).resolve().parent
OPS_DIR = LAB_DIR.parent
ROOT = OPS_DIR.parent
STATE_DIR = LAB_DIR / "state"
