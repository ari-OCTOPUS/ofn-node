#!/usr/bin/env python3
"""Compare the board-138 runtime snapshot against canonical git.

Two questions, answered with hashes rather than assertions:
  1. Is a live file present in canonical main at all?
  2. If present, is the live content identical to the canonical blob?

The comparison is exact: `git hash-object` of the live file on the node versus
the blob sha GitHub reports for the same path in the canonical tree.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

LANE = Path(__file__).resolve().parent.parent
MANIFEST = LANE / "evidence" / "RUNTIME-SNAPSHOT-MANIFEST.json"
OUT = LANE / "evidence" / "DRIFT-VS-CANONICAL.json"
REPO = "ari-OCTOPUS/ofn-node"


def gh(args: list[str]) -> str:
    proc = subprocess.run(["gh"] + args, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        raise RuntimeError(f"gh failed: {proc.stderr[:300]}")
    return proc.stdout


def main() -> int:
    branch = sys.argv[1] if len(sys.argv) > 1 else "main"
    head = json.loads(gh(["api", f"repos/{REPO}/git/refs/heads/{branch}"]))["object"]["sha"]
    tree = json.loads(gh(["api", f"repos/{REPO}/git/trees/{head}?recursive=1"]))
    canonical = {e["path"]: e["sha"] for e in tree.get("tree", []) if e["type"] == "blob"}

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = []
    for entry in manifest["files"]:
        path = entry["path"]
        live_blob = entry.get("git_blob")
        canon_blob = canonical.get(path)
        if canon_blob is None:
            verdict = "ABSENT_FROM_CANONICAL"
        elif live_blob and live_blob == canon_blob:
            verdict = "IDENTICAL"
        else:
            verdict = "DRIFT"
        rows.append({
            "path": path,
            "label": entry["label"],
            "in_board_head": entry.get("in_head"),
            "diff_vs_board_head": entry.get("diff_vs_head"),
            "live_blob": live_blob,
            "live_sha256": entry.get("sha256"),
            "canonical_blob": canon_blob,
            "verdict": verdict,
        })

    summary = {
        "schema": "drift_report.v1",
        "canonical_repo": REPO,
        "canonical_branch": branch,
        "canonical_head": head,
        "canonical_tree_truncated": tree.get("truncated", False),
        "canonical_blob_count": len(canonical),
        "counts": {},
        "files": rows,
    }
    for r in rows:
        summary["counts"][r["verdict"]] = summary["counts"].get(r["verdict"], 0) + 1

    OUT.write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8", newline="\n")

    print(f"canonical {REPO}@{branch} = {head[:12]} ({len(canonical)} blobs)")
    print()
    print(f"{'verdict':<22} {'path':<48} live_blob")
    for r in rows:
        print(f"{r['verdict']:<22} {r['path']:<48} {str(r['live_blob'])[:12]}")
    print()
    print("counts:", summary["counts"])
    print(f"-> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
