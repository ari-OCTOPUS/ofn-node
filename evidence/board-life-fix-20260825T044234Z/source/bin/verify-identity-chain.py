#!/usr/bin/env python3
"""Independent read-only verifier for the OCTOPUS identity ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from typing import Any


SCHEMA_VERSION = 1
GENESIS_PREVIOUS_HASH = "0" * 64
ORGANISM_ID = "board-life-001"


def canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def verify(db_path: str) -> dict[str, Any]:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = con.execute(
            """
            SELECT sequence, organism_id, boot_id, event_type, payload_json,
                   created_at_ns, previous_hash, entry_hash
            FROM identity_ledger
            ORDER BY sequence
            """
        ).fetchall()
    finally:
        con.close()

    result = {
        "db_path": db_path,
        "valid": False,
        "entries": len(rows),
        "first_hash": None,
        "last_hash": None,
        "error": None,
        "verifier": "independent-stdlib-v1",
        "verification_scope": "INTERNAL_HASH_CHAIN_CONSISTENCY",
        "external_anchor": None,
        "tail_truncation_detectable": False,
    }
    if not rows:
        result["error"] = "EMPTY_CHAIN"
        return result

    expected_sequence = 1
    expected_previous = GENESIS_PREVIOUS_HASH
    for row in rows:
        (
            sequence,
            organism_id,
            boot_id,
            event_type,
            payload_json,
            created_at_ns,
            previous_hash,
            entry_hash,
        ) = row
        if sequence != expected_sequence:
            result["error"] = f"NON_CONTIGUOUS_SEQUENCE_AT_{sequence}"
            return result
        if previous_hash != expected_previous:
            result["error"] = f"PREVIOUS_HASH_MISMATCH_AT_SEQUENCE_{sequence}"
            return result
        if expected_sequence == 1 and event_type != "chain_genesis":
            result["error"] = "FIRST_ENTRY_IS_NOT_CHAIN_GENESIS"
            return result
        if organism_id != ORGANISM_ID:
            result["error"] = f"ORGANISM_ID_MISMATCH_AT_SEQUENCE_{sequence}"
            return result
        if not boot_id:
            result["error"] = f"EMPTY_BOOT_ID_AT_SEQUENCE_{sequence}"
            return result
        try:
            payload = json.loads(payload_json)
        except json.JSONDecodeError:
            result["error"] = f"INVALID_PAYLOAD_JSON_AT_SEQUENCE_{sequence}"
            return result
        material = {
            "schema_version": SCHEMA_VERSION,
            "sequence": sequence,
            "organism_id": organism_id,
            "boot_id": boot_id,
            "event_type": event_type,
            "payload": payload,
            "created_at_ns": created_at_ns,
            "previous_hash": previous_hash,
        }
        calculated = hashlib.sha256(canonical(material)).hexdigest()
        if calculated != entry_hash:
            result["error"] = f"ENTRY_HASH_MISMATCH_AT_SEQUENCE_{sequence}"
            return result
        if result["first_hash"] is None:
            result["first_hash"] = entry_hash
        result["last_hash"] = entry_hash
        expected_previous = entry_hash
        expected_sequence += 1

    result["valid"] = True
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db",
        default="/opt/octopus/lab/lab-data/organism.db",
    )
    args = parser.parse_args()
    result = verify(args.db)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
