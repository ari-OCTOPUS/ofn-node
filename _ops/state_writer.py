#!/usr/bin/env python3
from __future__ import annotations
import json, os, tempfile
from pathlib import Path
STATE_DIR = Path(__file__).resolve().parent / "state"

def read_state(key, default=None):
    p = STATE_DIR / f"{key}.json"
    if not p.exists(): return default
    try: return json.loads(p.read_text("utf-8"))
    except Exception: return default

def write_state(key, value, *, writer="unknown"):
    p = STATE_DIR / f"{key}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    vp = STATE_DIR / f".versions/{key}.ver"; vp.parent.mkdir(parents=True, exist_ok=True)
    ver = int(vp.read_text().strip()) if vp.exists() else 0; ver += 1
    data = json.dumps(value, ensure_ascii=False, indent=1)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f: f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, p); vp.write_text(str(ver))
    except OSError:
        try: os.unlink(tmp)
        except OSError: pass
        return False
    return True

def get_version(key):
    vp = STATE_DIR / f".versions/{key}.ver"
    if not vp.exists(): return 0
    try: return int(vp.read_text().strip())
    except ValueError: return 0

if __name__ == "__main__":
    print(f"state_writer: single-writer | STATE_DIR={STATE_DIR}")
