#!/usr/bin/env python3
"""Daily Reflex ledger chain gate. Broken chain locks Reflex advisory forever."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/opt/octopus/scripts")
from reflex_ledger import lock_advisory_forever, verify  # noqa: E402

OUT = Path("/var/lib/octopus/state/reflex/chain_verify.json")


def main() -> int:
    ok, seq, detail = verify()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "schema": "octopus.reflex-ledger.verify.v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ok": ok,
        "break_seq": seq,
        "detail": detail,
        "gate": "G-LEDGER",
    }
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    if not ok:
        lock_advisory_forever(f"ledger_break seq={seq} {detail}")
    print(json.dumps(doc))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
