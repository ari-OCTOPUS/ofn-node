#!/usr/bin/env python3
"""splice_obsidian.py — insert the three additive blocks, RTL-safe.

Conventions (from prior syncs):
  * VITAL-DATA : block inserted directly AFTER the H1 line; `updated:` bumped.
  * CURRENT-TRUTH (canonical) : block appended at the TAIL.
  * ACTIVE-SEASON : block appended at the BOTTOM.
Per-file newline detection; block files are already newline-correct.
"""
import datetime
import pathlib

ROOT = pathlib.Path("F:/backup")
BLOCKS = ROOT / "09-LANES/API-BUDGET-ACTIVATION-20260913/evidence/obsidian_blocks"

TARGETS = [
    (ROOT / "01 - Dashboard/OCTOPUS-VITAL-DATA-2026-09-08.md", BLOCKS / "vital.md", "after_h1"),
    (ROOT / "06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/CURRENT-TRUTH.md", BLOCKS / "truth.md", "tail"),
    (ROOT / "ACTIVE-SEASON-REVENUE-ON-LIVE-LOOP-20260907.md", BLOCKS / "season.md", "tail"),
]

today = datetime.date.today().isoformat()

for path, block_path, mode in TARGETS:
    if not path.exists():
        print("MISSING:", path)
        continue
    raw = path.read_bytes()
    nl = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8")
    lines = text.split(nl)
    if any("MULTI_PROVIDER_COGNITION_ACTIVE" in ln for ln in lines):
        print("ALREADY PRESENT, skipped:", path.name)
        continue
    block = block_path.read_text(encoding="utf-8").rstrip("\n").split("\n")

    if mode == "after_h1":
        idx = next((i for i, ln in enumerate(lines) if ln.startswith("# ")), 0)
        insert_at = idx + 1
        new = lines[:insert_at] + [""] + block + lines[insert_at:]
        # bump frontmatter `updated:`
        for i, ln in enumerate(new[:20]):
            if ln.startswith("updated:"):
                new[i] = "updated: " + today
                break
    else:
        while lines and lines[-1].strip() == "":
            lines.pop()
        new = lines + ["", ""] + block

    path.write_text(nl.join(new) + nl, encoding="utf-8")
    print("spliced %-8s -> %s" % (mode, path.name))
