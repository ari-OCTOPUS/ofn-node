#!/usr/bin/env python3
"""Ingest a buy.nsw harvester batch file into the node's painting store.

Usage (from the repo root, on board138 or wherever the node's DB lives):

    python tools/ingest_buynsw_batch.py buynsw-harvest-20260902-093000.json

DB resolution order: --db argument, OFN_PAINTING_DB environment variable,
then the node's default state directory (ofn.config.Config.painting_path).

Exit codes: 0 = DONE (read the accounting), 2 = REJECTED (bad batch,
nothing was written), 1 = operational error (unreadable file, locked DB).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ofn.agents.h1_buysw_dom import ingest_batch          # noqa: E402
from ofn.adapters.lead_store import LeadStore              # noqa: E402


def default_db() -> str:
    env = os.environ.get("OFN_PAINTING_DB")
    if env:
        return env
    from ofn.config import load
    return load().painting_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ingest a buy.nsw harvester batch JSON into the "
                    "painting tender store (same gates as the API path).")
    parser.add_argument("file", help="batch JSON exported by the extension")
    parser.add_argument("--db", default=None,
                        help="painting.sqlite path (default: OFN_PAINTING_DB "
                             "or the node state dir)")
    args = parser.parse_args(argv)

    try:
        with open(args.file, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "ERROR", "reason": str(exc)},
                         ensure_ascii=False))
        return 1

    store = LeadStore(args.db or default_db())
    try:
        result = ingest_batch(payload, store)
    finally:
        store.close()

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "DONE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
