#!/usr/bin/env python3
"""Root hygiene regression (phase 1). Fails on NEW root MEGAPROMPT-*/AGENT-NEXT-*
files; reports (does not fail) on phase-2 items."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ALLOWED_ROOT_ENTRYPOINTS = {"AGENT.md", "CLAUDE.md", "README.md"}
def main():
    root_files = {p.name for p in ROOT.iterdir() if p.is_file()}
    phase1 = sorted(n for n in root_files
                    if n.startswith(("MEGAPROMPT-", "AGENT-NEXT-")) and n.endswith(".md"))
    phase2 = sorted(n for n in root_files
                    if ".bak-" in n or n == "saba_rag_seed.txt"
                    or any(p.name in (".obsidian", ".tmp-test", ".tmp-test-run")
                           for p in ROOT.iterdir()))
    if phase1:
        print("ROOT_HYGIENE_PHASE1_FAIL:", phase1); return 1
    print("ROOT_HYGIENE_PHASE1_PASS")
    print("ROOT_HYGIENE_PHASE2_PENDING:", bool(phase2))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
