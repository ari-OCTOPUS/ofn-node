#!/usr/bin/env python3
"""Measure partner voice receipts. Does not declare observation.

partner_voices_independently_observed flips only when this tool reports
ready=true: three partners, each with a 64-hex media_sha256, and the
receipt's independently_observed field is true. Missing media is not
forged. A receipt without media_sha256 is incomplete.
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ATTEST_REL = os.path.join("docs", "octopus-surgery", "attestations")
REQUIRED = ("maliheh", "abbas", "saba")
SCHEMA = "octopus.partner_attestation.v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class AttestationError(ValueError):
    """A receipt is present but not a complete independent observation."""


def _load(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise AttestationError(f"{path}: not an object")
    return data


def list_receipts(root: str = ROOT) -> list[dict[str, Any]]:
    folder = os.path.join(root, ATTEST_REL)
    if not os.path.isdir(folder):
        return []
    rows = []
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".json"):
            continue
        rows.append(_load(os.path.join(folder, name)))
    return rows


def independently_observed(receipts: list[dict[str, Any]]) -> dict[str, Any]:
    """Independent record. Absence of three complete files is false, not yes."""
    by_partner: dict[str, dict[str, Any]] = {}
    incomplete: list[str] = []
    for row in receipts:
        if row.get("schema") != SCHEMA:
            incomplete.append("schema")
            continue
        partner = row.get("partner_id")
        digest = row.get("media_sha256") or ""
        observed = bool(row.get("independently_observed"))
        if partner not in REQUIRED:
            incomplete.append(f"unknown:{partner}")
            continue
        if not _SHA256.match(str(digest).lower()):
            incomplete.append(f"hash:{partner}")
            continue
        if not observed:
            incomplete.append(f"not-observed:{partner}")
            continue
        by_partner[str(partner)] = row
    ready = all(p in by_partner for p in REQUIRED) and not incomplete
    return {
        "schema": "octopus.partner_attestation.measure.v1",
        "required": list(REQUIRED),
        "complete": sorted(by_partner),
        "incomplete": incomplete,
        "independently_observed": ready,
        "ready": ready,
    }


def main(argv: list[str] | None = None) -> int:
    del argv
    report = independently_observed(list_receipts())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
