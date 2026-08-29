
import json
import time

from ofn.organism import ORGANISM_ID
from ofn.organism.identity.ledger import (
    IdentityChainError,
    append_identity_event,
    ensure_identity_genesis,
    verify_identity_chain,
)
from ofn.organism.persistence.db import DB_LOCK

def beat(con, extra=None):
    extra = extra or {}
    payload = {
        "organism_id": ORGANISM_ID,
        "boot_id": extra.get("boot_id") if extra else None,
        "age_seconds": extra.get("age_seconds", 0) if extra else 0,
        "health_state": extra.get("health_state", "OBSERVING") if extra else "OBSERVING",
        "autonomy_state": "PROPOSE_ONLY",
        "last_event_sequence": extra.get("last_event_sequence", 0) if extra else 0,
        "local_cortex": extra.get("local_cortex", "STARTING") if extra else "STARTING",
        "external_api": "DISABLED",
        "memory_status": "AVAILABLE",
        "unknowns": extra.get("unknowns", []) if extra else [],
        "current_experiment": "board-life-001",
    }
    chain_write_error = None
    try:
        with DB_LOCK:
            ledger_entries = int(
                con.execute("SELECT COUNT(*) FROM identity_ledger").fetchone()[0]
            )
        if ledger_entries == 0:
            ensure_identity_genesis(con, payload["boot_id"])
        chain = append_identity_event(
            con,
            payload["boot_id"],
            "identity_heartbeat",
            payload,
        )
    except IdentityChainError as exc:
        chain_write_error = str(exc)
        chain = verify_identity_chain(con)
    body = dict(payload)
    body.update({
        "identity_chain_valid": chain["valid"],
        "identity_chain_entries": chain["entries"],
        "identity_chain_last_hash": chain["last_hash"],
        "identity_chain_error": chain_write_error or chain["error"],
        "identity_chain_scope": "identity_ledger_v1_from_genesis_forward",
        "identity_chain_verification_scope": chain["verification_scope"],
        "identity_chain_external_anchor": chain["external_anchor"],
        "identity_chain_tail_truncation_detectable": chain[
            "tail_truncation_detectable"
        ],
        "legacy_heartbeats_in_chain": False,
    })
    with DB_LOCK:
        con.execute(
            "INSERT INTO identity_heartbeat(ts, body_json) VALUES (?,?)",
            (time.time(), json.dumps(body, sort_keys=True)),
        )
    return body
