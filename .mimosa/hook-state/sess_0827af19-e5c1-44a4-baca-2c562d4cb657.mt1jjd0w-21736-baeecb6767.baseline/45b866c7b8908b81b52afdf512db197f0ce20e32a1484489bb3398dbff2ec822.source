#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json

ROOT = Path(r"F:/backup")
cands = [
    ROOT / "4d_system/outputs/self_evolved/consolidation.json",
    ROOT / "4d_system/outputs/self_evolved/consolidation.r18-marks.json",
    ROOT / "4d_system/outputs/daemon_state.json",
    ROOT / "_ops/neural/consolidation.json",
    ROOT / "_ops/state/telegram-pep-shadow.jsonl",
    ROOT / "_ops/state/tg-send-log.jsonl",
    ROOT / "_ops/state/paid-calls.jsonl",
    ROOT / "_ops/state/ORGANISM-STATE.json",
    ROOT / "06-EVIDENCE/POISONING-WATCH-4d.md",
]
print("=== FILES ===")
for p in cands:
    if not p.exists():
        print("MISS", p.as_posix())
        continue
    st = p.stat()
    mt = datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")
    print(f"OK {p.relative_to(ROOT).as_posix()} bytes={st.st_size} mtime={mt}")
