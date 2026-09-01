"""Owner-only job and answer store for the owner → brain loop.

Round 1 showed why this file must exist: the worker's `result.text` was
dropped on the floor after the ledger event was written, so a successful
brain call still left the owner with nothing to read. The ledger stays
metadata-only (ids, hashes, counts) — it is cross-tenant readable history,
not a place for answers. This store is the answers' home:

  * one JSONL file, owner-private, under the node's own state directory;
  * the raw prompt is never written here — only its SHA-256;
  * the response is written only after scrubbing, and the stored hash is
    computed over exactly the stored bytes, so what is delivered is what
    was verified;
  * terminal states are immutable, so a restart cannot turn a COMPLETED
    job into anything else, and a duplicate request id cannot create a
    second answer.

Retention: every record carries `expires_at`; expired records are pruned
lazily on read. Keeping answers for a week is a policy dial, not a law of
nature — the constant below is the whole policy.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Mapping

RETENTION_S = 7 * 24 * 60 * 60

# Statuses and the only transitions they allow. Anything else is a bug in
# the caller and is refused rather than recorded.
_TERMINAL = {"COMPLETED", "FAILED", "PARKED", "REJECTED"}
_TRANSITIONS: dict[str, set[str]] = {
    "SUBMITTED": {"QUEUED", "REJECTED"},
    "QUEUED": {"RUNNING", "FAILED", "PARKED"},
    "RUNNING": {"COMPLETED", "FAILED", "PARKED", "RETRY_WAIT"},
    "RETRY_WAIT": {"RUNNING"},
}


class OwnerAskError(Exception):
    """A lifecycle rule was violated. Raised, never absorbed."""


class OwnerAskStore:
    """Append-only JSONL of ask records with an in-memory index."""

    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._lock = threading.Lock()
        self._index: dict[str, dict] = {}
        self._by_request: dict[tuple[str, str], str] = {}
        self._path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            os.chmod(self._path.parent, 0o700)
        except OSError:
            pass  # POSIX-only; the mode was applied at creation where it works
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        with self._path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                self._index[rec["job_id"]] = rec
                if rec.get("request_id"):
                    self._by_request[(rec["owner_principal_digest"],
                                      rec["request_id"])] = rec["job_id"]

    def _append(self, rec: Mapping) -> None:
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, sort_keys=True, ensure_ascii=False))
            fh.write("\n")

    # ── lifecycle ─────────────────────────────────────────────────────────
    def create(self, *, job_id: str, request_id: str, principal_digest: str,
               target_scope: str, prompt_sha256: str, quote: Mapping,
               created_at: str, expires_at: str, now_epoch_s: int) -> dict:
        rec = {
            "job_id": job_id,
            "request_id": request_id,
            "owner_principal_digest": principal_digest,
            "target_scope": target_scope,
            "prompt_sha256": prompt_sha256,
            "status": "SUBMITTED",
            "created_at": created_at,
            "created_epoch": now_epoch_s,
            "started_at": None,
            "completed_at": None,
            "expires_epoch": now_epoch_s + RETENTION_S,
            "expires_at": expires_at,
            "not_before": 0,
            "quote": dict(quote),
            "estimated_input": quote["estimated_input"],
            "reserved_output": quote["reserved_output"],
            "request_estimate": quote["request_estimate"],
            "projected_billed": quote["request_estimate"],
            "ceiling": quote["ceiling"],
            "attempts": 0,
            "retryable": None,
            "billed_tokens": None,
            "rung": None,
            "elapsed_ms": None,
            "response_id": None,
            "response_sha256": None,
            "response_bytes": None,
            "response_text_scrubbed": None,
            "error_code": None,
            "error_detail_safe": None,
        }
        with self._lock:
            key = (principal_digest, request_id)
            existing = self._by_request.get(key)
            if existing is not None:
                return dict(self._index[existing])
            self._index[job_id] = rec
            self._by_request[key] = job_id
            self._append(rec)
        return dict(rec)

    def mark(self, job_id: str, status: str, *, at: str,
             **fields) -> dict:
        """Move a job to `status`. Terminal states are immutable."""
        with self._lock:
            rec = self._index.get(job_id)
            if rec is None:
                raise OwnerAskError(f"unknown job {job_id!r}")
            current = rec["status"]
            if current in _TERMINAL:
                raise OwnerAskError(
                    f"job {job_id!r} is terminal ({current}); "
                    f"refusing to move to {status!r}")
            if status not in _TRANSITIONS.get(current, set()):
                raise OwnerAskError(
                    f"illegal transition {current!r} → {status!r} "
                    f"for job {job_id!r}")
            rec["status"] = status
            for key, value in fields.items():
                rec[key] = value
            if status == "RUNNING" and rec.get("started_at") is None:
                rec["started_at"] = at
            if status in _TERMINAL:
                rec["completed_at"] = at
            self._append(rec)
        return dict(rec)

    # ── reading ───────────────────────────────────────────────────────────
    def get(self, job_id: str, *, now_epoch_s: int | None = None) -> dict | None:
        rec = self._index.get(job_id)
        if rec is None:
            return None
        if now_epoch_s is not None and rec.get("expires_epoch") and \
                now_epoch_s > rec["expires_epoch"]:
            return None
        return dict(rec)

    def find_by_request(self, principal_digest: str,
                        request_id: str) -> dict | None:
        job_id = self._by_request.get((principal_digest, request_id))
        return self.get(job_id) if job_id else None
