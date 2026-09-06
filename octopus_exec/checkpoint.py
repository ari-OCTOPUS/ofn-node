"""Durable derived files and ledger-authoritative replay cursor."""
import os
from pathlib import Path
from shadow_homeostasis.canonical import canonical
from shadow_homeostasis.evidence_store import ZERO
from .snapshot_reader import no_reparse, read_json


def atomic_bytes(path, data, budget=None):
    path = no_reparse(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = no_reparse(path.with_suffix(path.suffix + ".pending"))
    # Include simultaneous old and temporary bytes in the storage budget.
    if budget:
        budget.require(len(data))
    with temp.open("wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def atomic_json(path, value, budget=None):
    atomic_bytes(path, (canonical(value) + "\n").encode("utf-8"), budget)


def verify_checkpoint(path, fingerprint, records):
    if not Path(path).exists():
        return 0
    checkpoint, _ = read_json(path)
    if checkpoint["run_fingerprint"] != fingerprint:
        raise ValueError("checkpoint source/input/time mismatch")
    seq = checkpoint["committed_seq"]
    if type(seq) is not int or seq < 0 or seq > len(records):
        raise ValueError("checkpoint ahead of ledger")
    expected = records[seq - 1]["record_hash"] if seq else ZERO
    if checkpoint["committed_head_hash"] != expected:
        raise ValueError("checkpoint hash mismatch")
    index = checkpoint["next_input_index"]
    if type(index) is not int or index < 0:
        raise ValueError("checkpoint cursor invalid")
    if index != sum(record["kind"] == "decision" for record in records[:seq]):
        raise ValueError("checkpoint cursor ahead of committed decisions")
    # Cursor is advisory; caller reconciles every stable event ID against ledger.
    return index


def save_checkpoint(path, fingerprint, index, store, budget=None):
    records = store.records
    atomic_json(path, {"run_fingerprint": fingerprint, "next_input_index": index,
                      "committed_seq": len(records),
                      "committed_head_hash": records[-1]["record_hash"] if records else ZERO}, budget)
