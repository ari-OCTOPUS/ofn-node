#!/usr/bin/env python3
"""Build deterministic, content-free Test Intelligence evidence artifacts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
for _p in (_OPS, _OPS / "budget"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import dark_capabilities  # noqa: E402
from test_intelligence.dark_inventory import inventory  # noqa: E402


def build(output_dir: Path | None = None) -> Path:
    target = Path(output_dir or (_OPS / "test_intelligence" / "evidence"))
    target.mkdir(parents=True, exist_ok=True)
    artifact = inventory(dark_capabilities.scan(_OPS))
    out = target / "dark-inventory.json"
    out.write_text(json.dumps(artifact, ensure_ascii=False, sort_keys=True,
                              indent=2) + "\n", "utf-8")
    return out


if __name__ == "__main__":
    print(build())
