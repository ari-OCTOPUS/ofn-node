"""Mint a witness request: a receipt that an artifact existed, hashed.

A witness request is the node's half of "prove what you ran". It binds five
things together — the run, the artifact's bytes, the payload's bytes, the
policy version and the schema version — into one id, and appends that
binding to an append-only JSONL file. The id is deterministic: the SHA-256
of the binding tuple itself, so the same run minted twice is the same
request, not two.

STRUCTURAL_PASS vs EXECUTABLE_PASS, stated once so nobody has to guess:

  * STRUCTURAL_PASS is what this module mints. It says "the artifact with
    this hash, bound to this run and these versions, was recorded". It is a
    statement about shape and identity, and it is complete the moment the
    line is written.

  * EXECUTABLE_PASS says more: "and a human owner approved executing it."
    That extra claim is not this module's to make. It requires a separate
    owner approval reference (see `ofn.adapters.owner_decision`), recorded
    by whatever process the owner actually said yes in. There is deliberately
    no function here that mints an EXECUTABLE_PASS; a witness that could
    upgrade itself would be a rubber stamp with a hash on it.

Idempotency is by request_id, checked against the file before appending, so
a retried mint adds no second line and returns the original record with its
original `created_at`. The clock is injectable for the same reason every
timestamp in this spine is: a test must be able to freeze time.

This module writes one file and reads it back. It sends nothing, anywhere.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

SCHEMA_NAME = "witness_request.v1"
REQUESTS_FILENAME = "witness_requests.jsonl"

# The two pass types a witness can carry. Minting emits STRUCTURAL_PASS only;
# see the module docstring for why EXECUTABLE_PASS is not ours to grant.
STRUCTURAL_PASS = "STRUCTURAL_PASS"
EXECUTABLE_PASS = "EXECUTABLE_PASS"
PASS_TYPES = (STRUCTURAL_PASS, EXECUTABLE_PASS)


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256_hex(data: bytes) -> str:
    """Digest of bytes, as lowercase hex. Public because tests and callers
    both need the exact same definition of the bound value."""
    return hashlib.sha256(data).hexdigest()


def request_id_for(run_id: str, artifact_bytes: bytes, payload_bytes: bytes,
                   policy_version: str, schema_version: str) -> str:
    """Deterministic id: SHA-256 over the binding tuple.

    The unit separator keeps adjacent fields from ever concatenating into a
    third value that was in neither (`("ab", "c")` vs `("a", "bc")`).
    """
    material = "\x1f".join((
        run_id,
        sha256_hex(artifact_bytes),
        sha256_hex(payload_bytes),
        policy_version,
        schema_version,
    ))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _existing(path: Path, request_id: str) -> dict | None:
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue          # a torn write years ago must not stop
                if isinstance(record, dict) and \
                        record.get("request_id") == request_id:
                    return record
    except OSError:
        return None
    return None


def mint_witness_request(run_id: str, artifact_bytes: bytes,
                         payload_bytes: bytes, policy_version: str,
                         schema_version: str, state_dir: str,
                         *, now_utc: str = "") -> dict:
    """Record the binding once; return the record (existing one if repeated).

    `now_utc` is the injectable clock: pass it and the record is frozen to
    it, leave it out and the wall clock is read. The returned dict is the
    stored record plus `created` (True when this call appended it) and
    `path` (the JSONL file it lives in).
    """
    artifact_sha = sha256_hex(artifact_bytes)
    payload_sha = sha256_hex(payload_bytes)
    request_id = request_id_for(run_id, artifact_bytes, payload_bytes,
                                policy_version, schema_version)
    record = {
        "schema": SCHEMA_NAME,
        "request_id": request_id,
        "run_id": run_id,
        "artifact_sha256": artifact_sha,
        "payload_sha256": payload_sha,
        "policy_version": policy_version,
        "schema_version": schema_version,
        "pass_type": STRUCTURAL_PASS,
        "created_at": now_utc or _now_iso(),
    }
    state = Path(state_dir)
    state.mkdir(parents=True, exist_ok=True)
    path = state / REQUESTS_FILENAME
    prior = _existing(path, request_id)
    if prior is not None:
        return {**prior, "created": False, "path": str(path)}
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    return {**record, "created": True, "path": str(path)}
