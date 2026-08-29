#!/usr/bin/env python3
"""Export an unsigned audit checkpoint. GAP-002 stays open until a Windows signature is verified."""

from __future__ import annotations

import json
from pathlib import Path

from octopus_sensorium.audit import export_checkpoint

OUT = Path("/var/lib/octopus/staging/sensorium-software-v1/bundles/audit-checkpoint/checkpoint.unsigned.json")


def main() -> int:
    doc = export_checkpoint()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT), "sequence": doc["sequence"], "signed": False, "gap": "GAP-002"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
