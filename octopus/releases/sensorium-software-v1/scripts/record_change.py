#!/usr/bin/env python3
"""Append a change record. Never called by Doctor."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/opt/octopus/cognition/src")

from octopus_cognition.doctor.change import ChangeLedger  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="JSON change body")
    args = parser.parse_args()
    body = json.loads(Path(args.file).read_text(encoding="utf-8"))
    body.setdefault("written_at", datetime.now(timezone.utc).isoformat())
    entry = ChangeLedger().append(body)
    print(json.dumps({"seq": entry["seq"], "hash": entry["hash"], "change_id": body.get("change_id")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
