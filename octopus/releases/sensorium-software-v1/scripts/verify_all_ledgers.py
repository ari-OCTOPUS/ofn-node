#!/usr/bin/env python3
"""Hourly read-only verify of all hash chains. Does not repair."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/opt/octopus/cognition/src")

from octopus_cognition.doctor.change import ChangeLedger  # noqa: E402
from octopus_cognition.doctor.findings import DoctorFindingsLedger  # noqa: E402
from octopus_cognition.ledger import ChainedLedger  # noqa: E402

OUT_DIR = Path("/var/lib/octopus/evidence/ledger")
STATE = Path("/var/lib/octopus/state")


def main() -> int:
    now = datetime.now(timezone.utc)
    chains = {
        "octopus-prediction": ChainedLedger(STATE / "world_model", "octopus.prediction-ledger.head.v1").verify(),
        "octopus-metacontrol": ChainedLedger(STATE / "metacontrol", "octopus.metacontrol-ledger.head.v1").verify(),
        "octopus-reflex-advisory": ChainedLedger(STATE / "reflex", "octopus.reflex-ledger.head.v1").verify(),
        "octopus-doctor-findings": DoctorFindingsLedger().verify(),
        "octopus-audit-change": ChangeLedger().verify(),
    }
    ok = all(item[0] for item in chains.values())
    doc = {
        "schema": "octopus.ledger-verify.v1",
        "timestamp": now.isoformat(),
        "ok": ok,
        "chains": {name: {"ok": v[0], "break_seq": v[1], "detail": v[2]} for name, v in chains.items()},
        "not_this_chain": "octopus-audit-ledger checkpoint anchored at seq=266",
        "repairs_attempted": 0,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"verify-{now.strftime('%Y-%m-%dT%H%M')}.json"
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    latest = OUT_DIR / "latest.json"
    latest.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": ok, "path": str(path)}, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
