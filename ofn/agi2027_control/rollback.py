#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rollback.py — restore files from a patch-backup directory.

Usage:
    python F:\\backup\\_ops\\agi2027_control\\rollback.py <backup_dir>

This is additive tooling; it only copies files back that exist in the backup dir.
It does NOT delete anything the backup didn't capture.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # _ops/agi2027_control -> F:\backup


def restore(backup_dir: str):
    src = Path(backup_dir)
    restored = []
    if not src.exists():
        raise SystemExit(f"Backup not found: {src}")
    for p in src.rglob("*"):
        if p.is_file():
            rel = p.relative_to(src)
            dst = ROOT / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)
            restored.append(str(rel))
    return restored


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python F:\\backup\\_ops\\agi2027_control\\rollback.py <backup_dir>")
        raise SystemExit(2)
    items = restore(sys.argv[1])
    print("restored", len(items), "files")
    for item in items:
        print(" ", item)
