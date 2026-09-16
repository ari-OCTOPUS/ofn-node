#!/usr/bin/env python3
"""Fix lead_enrich.py cursor stall (2026-09-17 funnel day).

Defect: `start = cursor` with `batch = todo[start:start+MAX]` silently yields an
empty batch once the cursor has advanced past the (now shorter) todo list — the
funnel reports attempted:0/remaining:0 forever. Fix: clamp the cursor into range
and rescan from 0 when it has run past the end (idempotent: results dedupe by
business_name via the `have` set).

Preimage written next to the file. Additive, single-hunk change.
"""
import shutil
import sys
from pathlib import Path

P = Path("/home/ari/ofn/state/revenue-drive/lead_enrich.py")
PRE = Path("/home/ari/ofn/state/revenue-drive/lead_enrich.py.pre-cursor-fix-20260917")

OLD = """start = int(CURSOR.read_text().strip() or 0) if CURSOR.exists() else 0
batch = todo[start:start + MAX_PER_CYCLE]"""
NEW = """start = int(CURSOR.read_text().strip() or 0) if CURSOR.exists() else 0
# 2026-09-17 fix: a cursor past the end of todo made every later cycle a silent
# no-op (attempted:0/remaining:0). Clamp it and rescan from the top; the `have`
# set keeps re-processing idempotent.
if todo and start >= len(todo):
    start = 0
batch = todo[start:start + MAX_PER_CYCLE]"""


def main() -> int:
    src = P.read_text(encoding="utf-8")
    if "2026-09-17 fix" in src:
        print("already patched")
        return 0
    if src.count(OLD) != 1:
        print(f"ABORT: anchor count={src.count(OLD)}")
        return 2
    if not PRE.exists():
        shutil.copyfile(P, PRE)
        print("preimage_written")
    P.write_text(src.replace(OLD, NEW), encoding="utf-8", newline="\n")
    import py_compile
    py_compile.compile(str(P), doraise=True)
    body = P.read_text(encoding="utf-8")
    ok = "if todo and start >= len(todo):" in body and "attempted" in body
    print("PATCH_OK" if ok else "CHECK_FAILED")
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
