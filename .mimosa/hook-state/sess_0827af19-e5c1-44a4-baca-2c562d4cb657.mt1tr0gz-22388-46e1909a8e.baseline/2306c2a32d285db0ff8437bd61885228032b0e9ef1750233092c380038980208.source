#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""write_gate_enforcer.py — Enforces Write Gate rules on any memory write (EQUIP G2).

Closes the gap: the 4d brain writes hypotheses through memory.store.save_hypothesis()
which bypasses the graded MemoryGate entirely. This module provides a lightweight
enforcement layer that can wrap ANY write path:

  1. Content hash (SHA-256) computation and verification
  2. Source classification: trusted (owner, deterministic) vs untrusted (llm, tool, web)
  3. Provenance stamping: schema_version, source, timestamp, confidence, evidence_ref,
     writer_agent, content_hash
  4. Quarantine: untrusted source writes are quarantined (admission_state=QUARANTINED)
     instead of directly committed

This module is a BRIDGE, not a replacement for gate.py. It adds gate-like validation
to writes that happen outside the graded MemoryStore (e.g., 4d hypotheses table).

Security: follows Tool Contract principles:
  - Typed input/output
  - Least privilege (only validates, does not grant)
  - Idempotent (same content + same source = same decision)
  - Audit trace (every decision is logged)
  - Kill-switch compatible (no side effects beyond DB)

$0 | stdlib-only | no network | no external writes | SQLite/JSONL append-only audit.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Schema version for all records passing through this gate
SCHEMA_VERSION = "memory-write-gate.v1"

# Sources classified as trusted (can bypass quarantine)
_TRUSTED_SOURCES = frozenset({
    "owner", "verdict_recorder", "approval_channel",
    "tg_center", "telegram_center", "deterministic",
})

# Sources classified as untrusted (must be quarantined before commit)
_UNTRUSTED_SOURCES = frozenset({
    "llm:think", "llm:reason", "llm:create", "llm:conclude",
    "tool:web", "tool:search", "tool:api",
    "web:scrape", "web:fetch",
    "prompt:external", "model:auto",
})

# Admission states for quarantined writes
_QUARANTINE_STATE = "QUARANTINED"
_APPROVED_STATE = "APPROVED"
_REJECTED_STATE = "REJECTED"

# Secret/PII patterns (same as gate.py for consistency)
_SECRET_RX = None


def _get_secret_rx():
    global _SECRET_RX
    if _SECRET_RX is None:
        import re
        _SECRET_RX = re.compile(
            r"(sk-[A-Za-z0-9]{12,}|AKIA[0-9A-Z]{12,}|-----BEGIN|"
            r"xox[baprs]-|\bpassword\b\s*[:=]|\bseed\b\s*[:=]|"
            r"\bapi[_-]?key\b\s*[:=]|0x[a-fA-F0-9]{40}|"
            r"ghp_[a-zA-Z0-9]{36,}|gho_[a-zA-Z0-9]{36,}|"
            r"ghu_[a-zA-Z0-9]{36,})", re.I)
    return _SECRET_RX


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _content_hash(content: str) -> str:
    """Compute SHA-256 hash of content. Used for dedup and evidence chain."""
    return hashlib.sha256(str(content).encode("utf-8")).hexdigest()


def classify_source(source: str) -> str:
    """Classify a write source as 'trusted' or 'untrusted'.

    Unknown sources default to 'untrusted' (fail-closed).
    """
    s = str(source or "").strip().lower()
    if s in _TRUSTED_SOURCES:
        return "trusted"
    if s in _UNTRUSTED_SOURCES:
        return "untrusted"
    # Default: unknown = untrusted (fail-closed)
    return "untrusted"


def validate_content(content: str) -> tuple[bool, str]:
    """Validate content for secrets/PII. Returns (ok, reason)."""
    if not content or not str(content).strip():
        return False, "empty content"
    if _get_secret_rx().search(str(content)):
        return False, "secret/PII pattern detected"
    return True, ""


def build_provenance(
    source: str,
    writer_agent: str = "",
    model: str = "",
    inputs_sha: str = "",
    evidence_ref: str = "",
) -> dict[str, Any]:
    """Build a provenance record for a memory write.

    Provenance is immutable once created.
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "source": str(source or "unknown"),
        "source_class": classify_source(source),
        "writer_agent": str(writer_agent or "unknown"),
        "model": str(model or ""),
        "inputs_sha": str(inputs_sha or ""),
        "evidence_ref": str(evidence_ref or ""),
        "timestamp": _utc_now_iso(),
    }


class WriteGateEnforcer:
    """Enforces Write Gate rules on any memory write.

    Usage:
        enforcer = WriteGateEnforcer(audit_path="/path/to/audit.jsonl")
        result = enforcer.evaluate(candidate)
        # result = {"verb": "commit"|"quarantine"|"reject", "reason": ..., ...}

    The enforcer does NOT write to any database itself. It evaluates and returns
    a verdict. The caller is responsible for the actual write, incorporating
    the enforcer's metadata (content_hash, provenance, admission_state).
    """

    def __init__(self, audit_path: Path | str | None = None):
        self._audit_path = Path(audit_path) if audit_path else None
        self._contradiction_checker = None

    def set_contradiction_checker(self, checker) -> None:
        """Set an optional contradiction checker (injected for testability)."""
        self._contradiction_checker = checker

    def evaluate(self, candidate: dict[str, Any]) -> dict[str, Any]:
        """Evaluate a memory write candidate through the gate.

        Input (candidate):
            content: str (required)
            source: str (required)
            writer_agent: str (optional, default "unknown")
            domain: str (optional)
            confidence: float (optional)
            model: str (optional)
            evidence_ref: str (optional)

        Output:
            verb: "commit" | "quarantine" | "reject"
            reason: str
            content_hash: str
            provenance: dict
            admission_state: str
            contradictions: list (if checker is set)
        """
        if not isinstance(candidate, dict):
            reject_result = {"verb": "reject", "reason": "candidate must be dict",
                    "content_hash": "", "provenance": {}, "admission_state": _REJECTED_STATE}
            self._audit(reject_result, "")
            return reject_result

        content = str(candidate.get("content") or "")
        source = str(candidate.get("source") or "unknown")
        writer_agent = str(candidate.get("writer_agent") or "unknown")
        model = str(candidate.get("model") or "")
        evidence_ref = str(candidate.get("evidence_ref") or "")

        # (1) Validate content
        ok, reason = validate_content(content)
        if not ok:
            reject_result = {"verb": "reject", "reason": reason, "content_hash": "",
                    "provenance": {}, "admission_state": _REJECTED_STATE}
            self._audit(reject_result, content)
            return reject_result

        # (2) Compute content hash
        chash = _content_hash(content)

        # (3) Build provenance
        provenance = build_provenance(
            source=source,
            writer_agent=writer_agent,
            model=model,
            evidence_ref=evidence_ref,
        )

        # (4) Classify source
        source_class = classify_source(source)

        # (5) Check contradictions (if checker is set)
        contradictions = []
        if self._contradiction_checker is not None:
            try:
                contradictions = self._contradiction_checker(content, source) or []
            except Exception as e:
                logger.warning("contradiction check failed: %s", e)
                contradictions = []

        # (6) Decision
        if source_class == "trusted":
            admission_state = _APPROVED_STATE
            verb = "commit"
        else:
            admission_state = _QUARANTINE_STATE
            verb = "quarantine"

        # (7) Audit
        result = {
            "verb": verb,
            "reason": f"source_class={source_class}" + (
                f"; {len(contradictions)} contradiction(s)" if contradictions else ""),
            "content_hash": chash,
            "provenance": provenance,
            "admission_state": admission_state,
            "contradictions": contradictions,
            "schema_version": SCHEMA_VERSION,
        }
        self._audit(result, content)

        return result

    def verify_readback_hash(
        self, original_hash: str, retrieved_content: str
    ) -> dict[str, Any]:
        """Verify that retrieved content matches original hash.

        Evidence chain link: write -> readback.
        """
        if not original_hash or not retrieved_content:
            return {"ok": False, "reason": "missing hash or content",
                    "recomputed_hash": ""}
        recomputed = _content_hash(retrieved_content)
        return {
            "ok": recomputed == original_hash,
            "original_hash": original_hash,
            "recomputed_hash": recomputed,
            "match": recomputed == original_hash,
        }

    def _audit(self, result: dict, content: str) -> None:
        """Append-only audit log (JSONL). Never throws."""
        if not self._audit_path:
            return
        try:
            self._audit_path.parent.mkdir(parents=True, exist_ok=True)
            entry = {
                "ts": _utc_now_iso(),
                "verb": result["verb"],
                "reason": result["reason"],
                "content_hash": result.get("content_hash", ""),
                "source_class": (result.get("provenance") or {}).get("source_class", ""),
                "writer_agent": (result.get("provenance") or {}).get("writer_agent", ""),
                "content_preview": str(content)[:200] if content else "",
            }
            with open(self._audit_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
        except OSError:
            pass  # audit failure must never block the write path


# ── Convenience: stamp a hypothesis dict with gate metadata ──────────────────

def stamp_hypothesis_with_gate(
    hypothesis_id: int,
    content: str,
    source: str,
    writer_agent: str = "automation",
    db_path: Path | str | None = None,
    audit_path: Path | str | None = None,
    contradiction_checker=None,
) -> dict[str, Any]:
    """Evaluate a hypothesis through the Write Gate and return verdict.

    This is the integration point: called after save_hypothesis() to add
    gate metadata. The hypothesis row is already in the DB; this function
    computes the hash, provenance, and admission state.

    Returns the full gate verdict dict.
    """
    enforcer = WriteGateEnforcer(audit_path=audit_path)
    if contradiction_checker is not None:
        enforcer.set_contradiction_checker(contradiction_checker)

    candidate = {
        "content": content,
        "source": source,
        "writer_agent": writer_agent,
    }
    result = enforcer.evaluate(candidate)
    return result


if __name__ == "__main__":
    # Quick smoke test
    import sys
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        audit = Path(td) / "audit.jsonl"
        enf = WriteGateEnforcer(audit_path=audit)

        # Trusted write
        r1 = enf.evaluate({"content": "test trusted", "source": "owner"})
        assert r1["verb"] == "commit", r1
        assert r1["provenance"]["source_class"] == "trusted"

        # Untrusted write
        r2 = enf.evaluate({"content": "test untrusted", "source": "llm:think"})
        assert r2["verb"] == "quarantine", r2
        assert r2["provenance"]["source_class"] == "untrusted"

        # Secret rejection
        r3 = enf.evaluate({"content": "sk-ABCDEFGHIJKL123 leak", "source": "owner"})
        assert r3["verb"] == "reject", r3

        # Hash verification
        content = "hello world"
        h = _content_hash(content)
        assert enf.verify_readback_hash(h, content)["ok"]
        assert not enf.verify_readback_hash(h, "tampered")["ok"]

        # Audit exists
        lines = audit.read_text("utf-8").strip().split("\n")
        assert len(lines) == 3

    print("OK write_gate_enforcer smoke test")
    sys.exit(0)
