#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""evidence_chain.py — Tracks and verifies content hash through the memory lifecycle.

Closes the gap: no formal evidence chain verification exists. This module:
  1. Records content_hash at each lifecycle stage (write, read-back, conclude)
  2. Verifies chain integrity: all hashes must match
  3. Supports restart recovery: chain data persists across process restarts
  4. Returns structured chain reports for auditing

Lifecycle stages:
  write       — hypothesis created, hash computed at write time
  readback    — hypothesis retrieved from consumer path, hash recomputed
  conclude    — hypothesis used in conclusion, context hash recorded
  verify      — full chain verification, all hashes compared

Data model (append-only JSONL):
  Each entry records one stage transition. The full chain for a hypothesis_id
  is reconstructed by querying all entries for that ID.

Security: append-only audit. No mutations. No deletions. Kill-switch compatible.
$0 | stdlib-only | no network | read-only on hypothesis DB, append-only on chain DB.
"""
from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "evidence-chain.v1"

# Valid lifecycle stages (ordered)
_STAGES = ("write", "readback", "conclude", "verify")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _content_hash(content: str) -> str:
    """SHA-256 hash of content string."""
    return hashlib.sha256(str(content).encode("utf-8")).hexdigest()


def _default_db_path() -> Path:
    """Default path for the evidence chain database."""
    import os
    base = os.environ.get("OCTOPUS_STATE_DIR", "")
    if base:
        root = Path(base)
    else:
        root = Path(__file__).resolve().parent.parent / "state"
    return root / "memory" / "evidence_chain.db"


class EvidenceChain:
    """Tracks content hash through memory lifecycle stages.

    Usage:
        chain = EvidenceChain(db_path="/path/to/evidence_chain.db")
        chain.record_write(hypothesis_id=42, content="test hypothesis",
                          source="llm:think", writer_agent="automation")
        chain.record_readback(hypothesis_id=42, content="test hypothesis")
        chain.record_conclude(hypothesis_id=42, context_text="test hypothesis")
        report = chain.verify(hypothesis_id=42)
        # report = {"ok": True, "stages": [...], "all_hashes_match": True}
    """

    def __init__(self, db_path: Path | str | None = None):
        self._path = Path(db_path) if db_path else _default_db_path()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self._path), timeout=30)

    def _init_db(self) -> None:
        conn = self._conn()
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS evidence_chain (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hypothesis_id INTEGER NOT NULL,
                    stage TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    content_preview TEXT,
                    source TEXT,
                    writer_agent TEXT,
                    timestamp TEXT NOT NULL,
                    schema_version TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_evidence_hyp_id
                ON evidence_chain(hypothesis_id, stage)
            """)
            conn.commit()
        finally:
            conn.close()

    def record_write(
        self,
        hypothesis_id: int,
        content: str,
        source: str = "",
        writer_agent: str = "",
    ) -> dict[str, Any]:
        """Record the write stage: compute and store content hash."""
        chash = _content_hash(content)
        conn = self._conn()
        try:
            conn.execute(
                "INSERT INTO evidence_chain "
                "(hypothesis_id, stage, content_hash, content_preview, "
                "source, writer_agent, timestamp, schema_version) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (hypothesis_id, "write", chash, str(content)[:200],
                 source, writer_agent, _utc_now_iso(), SCHEMA_VERSION),
            )
            conn.commit()
        finally:
            conn.close()
        return {
            "stage": "write", "hypothesis_id": hypothesis_id,
            "content_hash": chash, "ok": True,
        }

    def record_readback(
        self,
        hypothesis_id: int,
        content: str,
    ) -> dict[str, Any]:
        """Record the readback stage: recompute hash and compare with write."""
        chash = _content_hash(content)
        conn = self._conn()
        try:
            conn.execute(
                "INSERT INTO evidence_chain "
                "(hypothesis_id, stage, content_hash, content_preview, "
                "timestamp, schema_version) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (hypothesis_id, "readback", chash, str(content)[:200],
                 _utc_now_iso(), SCHEMA_VERSION),
            )
            conn.commit()
        finally:
            conn.close()

        # Immediate comparison with write hash
        write_hash = self._get_stage_hash(hypothesis_id, "write")
        match = (write_hash is not None and write_hash == chash)
        return {
            "stage": "readback", "hypothesis_id": hypothesis_id,
            "content_hash": chash, "write_hash": write_hash,
            "match": match, "ok": match,
        }

    def record_conclude(
        self,
        hypothesis_id: int,
        context_text: str,
    ) -> dict[str, Any]:
        """Record the conclude stage: hash the context used in conclusion."""
        chash = _content_hash(context_text)
        conn = self._conn()
        try:
            conn.execute(
                "INSERT INTO evidence_chain "
                "(hypothesis_id, stage, content_hash, content_preview, "
                "timestamp, schema_version) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (hypothesis_id, "conclude", chash, str(context_text)[:200],
                 _utc_now_iso(), SCHEMA_VERSION),
            )
            conn.commit()
        finally:
            conn.close()

        # Compare with write and readback
        write_hash = self._get_stage_hash(hypothesis_id, "write")
        readback_hash = self._get_stage_hash(hypothesis_id, "readback")
        match = (
            write_hash is not None
            and chash == write_hash
            and (readback_hash is None or chash == readback_hash)
        )
        return {
            "stage": "conclude", "hypothesis_id": hypothesis_id,
            "content_hash": chash, "write_hash": write_hash,
            "readback_hash": readback_hash, "match": match, "ok": match,
        }

    def verify(self, hypothesis_id: int) -> dict[str, Any]:
        """Full chain verification: all hashes must be identical.

        Returns:
            ok: bool - True if all recorded hashes match
            stages: list of recorded stages with hashes
            all_hashes_match: bool
            distinct_hashes: set of distinct hashes found
        """
        conn = self._conn()
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT stage, content_hash, content_preview, source, "
                "writer_agent, timestamp "
                "FROM evidence_chain WHERE hypothesis_id = ? "
                "ORDER BY id ASC",
                (hypothesis_id,),
            ).fetchall()
        finally:
            conn.close()

        if not rows:
            return {
                "ok": False, "hypothesis_id": hypothesis_id,
                "reason": "no evidence chain entries",
                "stages": [], "all_hashes_match": False,
                "distinct_hashes": set(),
            }

        stages = []
        hashes = set()
        for r in rows:
            entry = {
                "stage": r["stage"],
                "content_hash": r["content_hash"],
                "content_preview": r["content_preview"],
                "source": r["source"],
                "writer_agent": r["writer_agent"],
                "timestamp": r["timestamp"],
            }
            stages.append(entry)
            hashes.add(r["content_hash"])

        all_match = len(hashes) == 1
        return {
            "ok": all_match,
            "hypothesis_id": hypothesis_id,
            "stages": stages,
            "all_hashes_match": all_match,
            "distinct_hashes": hashes,
            "reason": ("all hashes identical" if all_match
                       else f"hash divergence: {len(hashes)} distinct hashes"),
        }

    def _get_stage_hash(self, hypothesis_id: int, stage: str) -> str | None:
        """Get the most recent hash for a hypothesis at a given stage."""
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT content_hash FROM evidence_chain "
                "WHERE hypothesis_id = ? AND stage = ? "
                "ORDER BY id DESC LIMIT 1",
                (hypothesis_id, stage),
            ).fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def close(self) -> None:
        """Checkpoint and close. No-op if not using persistent connection."""
        pass

    @classmethod
    def verify_content_chain(
        cls,
        original_content: str,
        readback_content: str,
        conclude_content: str | None = None,
    ) -> dict[str, Any]:
        """Static method: verify content hash chain without DB.

        Useful for inline verification in tests.
        """
        h_original = _content_hash(original_content)
        h_readback = _content_hash(readback_content)

        result: dict[str, Any] = {
            "original_hash": h_original,
            "readback_hash": h_readback,
            "write_readback_match": h_original == h_readback,
        }

        if conclude_content is not None:
            h_conclude = _content_hash(conclude_content)
            result["conclude_hash"] = h_conclude
            result["conclude_match"] = h_conclude == h_original
            result["all_match"] = (
                h_original == h_readback == h_conclude
            )
        else:
            result["all_match"] = h_original == h_readback

        return result


if __name__ == "__main__":
    import sys
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "evidence.db"
        chain = EvidenceChain(db_path=db)

        hid = 42
        content = "test hypothesis for evidence chain"

        # Record full lifecycle
        chain.record_write(hid, content, source="llm:think", writer_agent="test")
        rb = chain.record_readback(hid, content)
        assert rb["match"], "readback hash should match write hash"

        chain.record_conclude(hid, content)

        # Verify full chain
        report = chain.verify(hid)
        assert report["ok"], f"Chain verification failed: {report}"
        assert report["all_hashes_match"]

        # Verify static method
        static = EvidenceChain.verify_content_chain(
            content, content, content,
        )
        assert static["all_match"]

        # Detect tampering
        tampered = EvidenceChain.verify_content_chain(
            content, "tampered content", content,
        )
        assert not tampered["write_readback_match"]

        chain.close()

    print("OK evidence_chain smoke test")
    sys.exit(0)
