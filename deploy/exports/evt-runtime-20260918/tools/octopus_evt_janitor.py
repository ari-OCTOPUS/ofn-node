#!/usr/bin/env python3
"""octopus_evt_janitor — archive stale event files of kinds with NO path-unit consumer.

DEEPSCAN-7D D1 (2026-09-18): the event gate (octopus_event_gate.sh) only drains
dirs watched by octopus-evt-*.path units. The informational kinds below are
emitted into state/events/inbox/ for the ledger but no path unit watches them,
so their files accumulated forever (154 packet_staged files on day one).

This janitor MOVEs (never deletes) files older than MAX_AGE_H (default 24h)
from inbox/<kind>/ to archive-inbox/<kind>/, appending one receipt row per run.
The durable ledger record (state/events/ledger.jsonl, sha256-chained) is the
source of truth and is never touched.

Usage:
  octopus_evt_janitor.py [--root DIR] [--max-age-h HOURS] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from pathlib import Path

# Kinds verified (2026-09-18) to have NO consumer path unit on 138:
# path units watch card_resolved, idle, inbound_reply/quote_requested/
# quote_accepted/opted_out/bounce, lead_found, mail_seen, mesh, order_seen/
# payment_seen/stock_changed, tg-inbox/go_b3 spool, draft_ready, lead_enriched.
NO_CONSUMER_KINDS = (
    "packet_staged",
    "packet_sent",
    "packet_failed",
    "revenue_review",
    "traffic_seen",
    "selftest",
    "orders",
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/home/ari/ofn/state/events")
    ap.add_argument("--max-age-h", type=float, default=24.0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = Path(args.root)
    inbox = root / "inbox"
    archive = root / "archive-inbox"
    receipts = root / "janitor-receipts.jsonl"
    cutoff = time.time() - args.max_age_h * 3600.0
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    moved: dict[str, int] = {}
    scanned = 0
    for kind in NO_CONSUMER_KINDS:
        src = inbox / kind
        if not src.is_dir():
            continue
        for f in sorted(src.glob("*.json")):
            scanned += 1
            try:
                mtime = f.stat().st_mtime
            except OSError:
                continue
            if mtime >= cutoff:
                continue  # still fresh; a consumer may still appear
            dst_dir = archive / kind
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst = dst_dir / f.name
            if dst.exists():
                dst = dst_dir / (f.name + "." + str(int(mtime)))
            if not args.dry_run:
                shutil.move(str(f), str(dst))
            moved[kind] = moved.get(kind, 0) + 1

    row = {
        "schema": "octopus.evt-janitor.v1",
        "at": now,
        "max_age_h": args.max_age_h,
        "dry_run": args.dry_run,
        "scanned": scanned,
        "moved": moved,
        "total_moved": sum(moved.values()),
        "root": str(root),
    }
    if not args.dry_run:
        with receipts.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps(row, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
