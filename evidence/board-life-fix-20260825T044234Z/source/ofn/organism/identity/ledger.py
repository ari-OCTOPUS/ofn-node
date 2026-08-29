from __future__ import annotations

import hashlib
import json
import threading
import time
from typing import Any

from ofn.organism import ORGANISM_ID
from ofn.organism.persistence.db import DB_LOCK


LEDGER_SCHEMA_VERSION = 1
GENESIS_PREVIOUS_HASH = "0" * 64
_LEDGER_LOCK = threading.RLock()


class IdentityChainError(RuntimeError):
    pass


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _entry_material(
    sequence: int,
    organism_id: str,
    boot_id: str,
    event_type: str,
    payload: dict[str, Any],
    created_at_ns: int,
    previous_hash: str,
) -> dict[str, Any]:
    return {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "sequence": sequence,
        "organism_id": organism_id,
        "boot_id": boot_id,
        "event_type": event_type,
        "payload": payload,
        "created_at_ns": created_at_ns,
        "previous_hash": previous_hash,
    }


def _entry_hash(material: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(material)).hexdigest()


def _verify_rows(rows: list[tuple[Any, ...]]) -> dict[str, Any]:
    if not rows:
        return {
            "valid": False,
            "entries": 0,
            "first_hash": None,
            "last_hash": None,
            "error": "EMPTY_CHAIN",
            "verified_schema_version": LEDGER_SCHEMA_VERSION,
            "verification_scope": "INTERNAL_HASH_CHAIN_CONSISTENCY",
            "external_anchor": None,
            "tail_truncation_detectable": False,
        }

    expected_previous = GENESIS_PREVIOUS_HASH
    expected_sequence = 1
    first_hash = None
    for row in rows:
        (
            sequence,
            organism_id,
            boot_id,
            event_type,
            payload_json,
            created_at_ns,
            previous_hash,
            stored_hash,
        ) = row
        try:
            payload = json.loads(payload_json)
        except json.JSONDecodeError:
            return {
                "valid": False,
                "entries": len(rows),
                "first_hash": first_hash,
                "last_hash": rows[-1][7],
                "error": f"INVALID_PAYLOAD_JSON_AT_SEQUENCE_{sequence}",
                "verified_schema_version": LEDGER_SCHEMA_VERSION,
            }
        if expected_sequence == 1 and event_type != "chain_genesis":
            return {
                "valid": False,
                "entries": len(rows),
                "first_hash": first_hash,
                "last_hash": rows[-1][7],
                "error": "FIRST_ENTRY_IS_NOT_CHAIN_GENESIS",
                "verified_schema_version": LEDGER_SCHEMA_VERSION,
            }
        if organism_id != ORGANISM_ID:
            return {
                "valid": False,
                "entries": len(rows),
                "first_hash": first_hash,
                "last_hash": rows[-1][7],
                "error": f"ORGANISM_ID_MISMATCH_AT_SEQUENCE_{sequence}",
                "verified_schema_version": LEDGER_SCHEMA_VERSION,
            }
        if not boot_id:
            return {
                "valid": False,
                "entries": len(rows),
                "first_hash": first_hash,
                "last_hash": rows[-1][7],
                "error": f"EMPTY_BOOT_ID_AT_SEQUENCE_{sequence}",
                "verified_schema_version": LEDGER_SCHEMA_VERSION,
            }
        if sequence != expected_sequence:
            return {
                "valid": False,
                "entries": len(rows),
                "first_hash": first_hash,
                "last_hash": rows[-1][7],
                "error": f"NON_CONTIGUOUS_SEQUENCE_AT_{sequence}",
                "verified_schema_version": LEDGER_SCHEMA_VERSION,
            }
        if previous_hash != expected_previous:
            return {
                "valid": False,
                "entries": len(rows),
                "first_hash": first_hash,
                "last_hash": rows[-1][7],
                "error": f"PREVIOUS_HASH_MISMATCH_AT_SEQUENCE_{sequence}",
                "verified_schema_version": LEDGER_SCHEMA_VERSION,
            }
        material = _entry_material(
            sequence,
            organism_id,
            boot_id,
            event_type,
            payload,
            created_at_ns,
            previous_hash,
        )
        calculated_hash = _entry_hash(material)
        if calculated_hash != stored_hash:
            return {
                "valid": False,
                "entries": len(rows),
                "first_hash": first_hash,
                "last_hash": rows[-1][7],
                "error": f"ENTRY_HASH_MISMATCH_AT_SEQUENCE_{sequence}",
                "verified_schema_version": LEDGER_SCHEMA_VERSION,
            }
        if first_hash is None:
            first_hash = stored_hash
        expected_previous = stored_hash
        expected_sequence += 1

    return {
        "valid": True,
        "entries": len(rows),
        "first_hash": first_hash,
        "last_hash": expected_previous,
        "error": None,
        "verified_schema_version": LEDGER_SCHEMA_VERSION,
        "verification_scope": "INTERNAL_HASH_CHAIN_CONSISTENCY",
        "external_anchor": None,
        "tail_truncation_detectable": False,
    }


def verify_identity_chain(con) -> dict[str, Any]:
    with _LEDGER_LOCK, DB_LOCK:
        rows = con.execute(
            """
            SELECT sequence, organism_id, boot_id, event_type, payload_json,
                   created_at_ns, previous_hash, entry_hash
            FROM identity_ledger
            ORDER BY sequence
            """
        ).fetchall()
        result = _verify_rows(rows)
        result.setdefault(
            "verification_scope",
            "INTERNAL_HASH_CHAIN_CONSISTENCY",
        )
        result.setdefault("external_anchor", None)
        result.setdefault("tail_truncation_detectable", False)
        return result


def append_identity_event(
    con,
    boot_id: str,
    event_type: str,
    payload: dict[str, Any],
    *,
    organism_id: str = ORGANISM_ID,
    created_at_ns: int | None = None,
) -> dict[str, Any]:
    if not boot_id or not event_type:
        raise ValueError("boot_id_and_event_type_required")
    if not isinstance(payload, dict):
        raise ValueError("identity_payload_must_be_object")

    with _LEDGER_LOCK, DB_LOCK:
        con.execute("BEGIN IMMEDIATE")
        try:
            rows = con.execute(
                """
                SELECT sequence, organism_id, boot_id, event_type, payload_json,
                       created_at_ns, previous_hash, entry_hash
                FROM identity_ledger
                ORDER BY sequence
                """
            ).fetchall()
            if rows:
                verification = _verify_rows(rows)
                if not verification["valid"]:
                    raise IdentityChainError(verification["error"])
                sequence = rows[-1][0] + 1
                previous_hash = rows[-1][7]
                first_hash = rows[0][7]
            else:
                if event_type != "chain_genesis":
                    raise IdentityChainError("FIRST_ENTRY_MUST_BE_CHAIN_GENESIS")
                sequence = 1
                previous_hash = GENESIS_PREVIOUS_HASH
                first_hash = None

            timestamp_ns = (
                created_at_ns if created_at_ns is not None else time.time_ns()
            )
            material = _entry_material(
                sequence,
                organism_id,
                boot_id,
                event_type,
                payload,
                timestamp_ns,
                previous_hash,
            )
            digest = _entry_hash(material)
            con.execute(
                """
                INSERT INTO identity_ledger(
                    sequence, organism_id, boot_id, event_type, payload_json,
                    created_at_ns, previous_hash, entry_hash
                ) VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    sequence,
                    organism_id,
                    boot_id,
                    event_type,
                    _canonical(payload).decode("utf-8"),
                    timestamp_ns,
                    previous_hash,
                    digest,
                ),
            )
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
        return {
            "sequence": sequence,
            "entries": sequence,
            "entry_hash": digest,
            "first_hash": first_hash or digest,
            "last_hash": digest,
            "previous_hash": previous_hash,
            "created_at_ns": timestamp_ns,
            "valid": True,
            "error": None,
            "verification_scope": "INTERNAL_HASH_CHAIN_CONSISTENCY",
            "external_anchor": None,
            "tail_truncation_detectable": False,
        }


def ensure_identity_genesis(con, boot_id: str) -> dict[str, Any]:
    with _LEDGER_LOCK, DB_LOCK:
        row = con.execute("SELECT COUNT(*) FROM identity_ledger").fetchone()
        if int(row[0]) > 0:
            verification = verify_identity_chain(con)
            if not verification["valid"]:
                raise IdentityChainError(verification["error"])
            return verification
        legacy_heartbeats = int(
            con.execute("SELECT COUNT(*) FROM identity_heartbeat").fetchone()[0]
        )
        append_identity_event(
            con,
            boot_id,
            "chain_genesis",
            {
                "legacy_identity_heartbeats": legacy_heartbeats,
                "legacy_heartbeats_in_chain": False,
                "scope": "identity_ledger_v1_from_this_entry_forward",
            },
        )
        return verify_identity_chain(con)
