"""
Audit Log — Brushline (KB-06)
Hash-chained, append-only. Every external action produces one entry.

Chain structure:
  entry_hash = SHA-256(prev_hash + event_type + entity_id + payload + timestamp)

Genesis: prev_hash = "0" * 64
PII policy (INV-2): phone/email NEVER in payload — use hash references.
"""
import hashlib
import json
import threading
import uuid
from datetime import datetime

from .database import get_connection

# Serialises the read-prev-hash + insert so concurrent appends cannot compute
# the same prev_hash and fork the chain (P9). Ordering is by rowid (true insert
# order), not timestamp, so same-millisecond appends still link correctly.

GENESIS_HASH = "0" * 64
PII_FIELDS = {"phone", "email", "name", "full_name", "full_address", "tax_file_number"}
_append_lock = threading.Lock()


def _sanitise_payload(payload: dict) -> dict:
    """Strip raw PII from payload. Use hash references instead."""
    clean = {}
    for k, v in payload.items():
        if k in PII_FIELDS:
            # Replace with a hash reference so PII is never in the log
            hashed = hashlib.sha256(str(v).encode()).hexdigest()[:16]
            clean[f"{k}_ref"] = f"sha256:{hashed}..."
        else:
            clean[k] = v
    return clean


def _last_hash() -> str:
    """Hash of the most recent audit entry (or genesis if chain is empty)."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT entry_hash FROM audit_entries ORDER BY rowid DESC LIMIT 1"
        ).fetchone()
        return row["entry_hash"] if row else GENESIS_HASH
    finally:
        conn.close()


def _compute_hash(prev_hash: str, event_type: str, entity_id: str,
                  payload: dict, timestamp: str) -> str:
    """Deterministic SHA-256 of the entry's canonical content."""
    canonical = json.dumps({
        "prev_hash": prev_hash,
        "event_type": event_type,
        "entity_id": entity_id,
        "payload": payload,
        "timestamp": timestamp,
    }, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def append(event_type: str, entity_id: str, payload: dict) -> str:
    """
    Append one immutable entry to the audit chain.

    Args:
        event_type: AuditEventType string (e.g. "GATE_CHECK", "APPROVAL_DECISION")
        entity_id:  ID of the entity being audited (draft_id, lead_id, etc.)
        payload:    Dict of context — NO raw PII (auto-sanitised)

    Returns:
        entry_id (UUID string)
    """
    safe_payload = _sanitise_payload(payload)
    entry_id = str(uuid.uuid4())

    # One connection + one lock for the whole read-modify-write: prevents two
    # concurrent appends from reading the same prev_hash and forking the chain.
    with _append_lock:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT entry_hash FROM audit_entries ORDER BY rowid DESC LIMIT 1"
            ).fetchone()
            prev_hash = row["entry_hash"] if row else GENESIS_HASH
            timestamp = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
            entry_hash = _compute_hash(prev_hash, event_type, entity_id,
                                       safe_payload, timestamp)
            conn.execute(
                """INSERT INTO audit_entries
                   (id, prev_hash, entry_hash, event_type, entity_id, payload, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (entry_id, prev_hash, entry_hash, event_type, entity_id,
                 json.dumps(safe_payload, ensure_ascii=False), timestamp)
            )
            conn.commit()
        finally:
            conn.close()

    return entry_id


def verify_chain() -> tuple[bool, str]:
    """
    Walk the entire chain and verify every hash link.

    Returns:
        (True, "Chain intact. N entries verified.")
        (False, "Chain broken at entry I: reason.")
    """
    conn = get_connection()
    try:
        entries = conn.execute(
            "SELECT * FROM audit_entries ORDER BY rowid ASC"
        ).fetchall()
    finally:
        conn.close()

    if not entries:
        return True, "Chain is empty (genesis state)."

    prev_hash = GENESIS_HASH
    for i, entry in enumerate(entries):
        payload = json.loads(entry["payload"])
        expected = _compute_hash(
            prev_hash,
            entry["event_type"],
            entry["entity_id"],
            payload,
            entry["timestamp"],
        )
        if entry["entry_hash"] != expected:
            return False, (
                f"Chain broken at entry {i} (id={entry['id']}): "
                f"hash mismatch. Expected {expected[:16]}… got {entry['entry_hash'][:16]}…"
            )
        if entry["prev_hash"] != prev_hash:
            return False, (
                f"Chain broken at entry {i} (id={entry['id']}): prev_hash mismatch."
            )
        prev_hash = entry["entry_hash"]

    return True, f"Chain intact. {len(entries)} entries verified."


def query(event_type: str = None, entity_id: str = None,
          limit: int = 100) -> list[dict]:
    """
    Query audit entries (for compliance reporting).
    Returns list of entry dicts. Does NOT return raw PII.
    """
    conn = get_connection()
    try:
        conditions = []
        params = []
        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)
        if entity_id:
            conditions.append("entity_id = ?")
            params.append(entity_id)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = conn.execute(
            f"SELECT id, event_type, entity_id, payload, timestamp, entry_hash "
            f"FROM audit_entries {where} ORDER BY timestamp DESC LIMIT ?",
            params + [limit]
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
