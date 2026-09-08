#!/usr/bin/env python3
"""tools/gap_ledger.py — regenerate ops/GAP-LEDGER.jsonl from ops/gap_sources.yaml.

Machine-generated ledger ("دستی ویرایش نکن"). Preserves the honest-seed header
contract (schema octopus.gap_ledger.v1): rows carry UNVALIDATED status only;
no row is PASS by generation. Verify runs are separate, read-only, receipted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.join(ROOT, "ops", "gap_sources.yaml")
LEDGER = os.path.join(ROOT, "ops", "GAP-LEDGER.jsonl")


def generate(dry_run: bool = False) -> dict:
    with open(SOURCES, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    meta = data["_meta"]
    gaps = data["gaps"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    header = {
        "schema": "octopus.gap_ledger.v1",
        "record_type": "ledger_header",
        "created_at_utc": now,
        "seed": False,
        "generated_from": "ops/gap_sources.yaml",
        "sources_sha256": hashlib.sha256(
            open(SOURCES, "rb").read()).hexdigest(),
        "row_count": len(gaps),
        "unblocked_count": sum(1 for g in gaps if g.get("blocked_by") is None),
        "verified_pass_count": 0,
        "note": "Machine-generated from gap_sources.yaml. All rows UNVALIDATED; "
                "generation never PASSes a row. Verify runs are separate read-only work.",
        "row_schema": {
            "gap_id": "str", "title": "str", "node": "str", "class": "str",
            "blocked_by": "str|null", "verify_command": "str|null",
            "verify_status": "UNVALIDATED|PASS|FAIL|ERROR", "status": "OPEN|CLOSED",
            "evidence": "str|null", "updated_at_utc": "str ISO8601",
        },
        "rules": [
            "Do not invent gap rows without evidence.",
            "Do not mark rows PASS without a node-received verify result.",
            "Do not hand-edit this file; regenerate from sources.",
        ],
    }
    lines = [json.dumps(header, ensure_ascii=False)]
    for g in gaps:
        lines.append(json.dumps({
            "record_type": "gap_row",
            "gap_id": g["gap_id"], "title": g["title"], "node": g["node"],
            "class": g["class"], "blocked_by": g.get("blocked_by"),
            "verify_command": g.get("verify_command"), "expect": g.get("expect"),
            "canary": bool(g.get("canary")),
            "verify_status": "UNVALIDATED", "status": "OPEN",
            "evidence": g.get("evidence"), "updated_at_utc": g["updated_at_utc"],
        }, ensure_ascii=False))
    if not dry_run:
        with open(LEDGER, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    return {"rows": len(gaps),
            "unblocked": header["unblocked_count"],
            "ledger": None if dry_run else LEDGER,
            "sources_sha256": header["sources_sha256"]}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    print(json.dumps(generate(a.dry_run), ensure_ascii=False, indent=1))
