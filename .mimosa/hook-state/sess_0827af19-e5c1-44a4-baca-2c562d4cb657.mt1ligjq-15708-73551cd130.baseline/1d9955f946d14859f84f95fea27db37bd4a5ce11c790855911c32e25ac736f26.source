# -*- coding: utf-8 -*-
"""Append-only Reality Ledger. Findings are not truth without evidence hash."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

KINDS = ("finding", "claim", "verification")
STATUSES = ("open", "confirmed", "superseded", "resolved", "stale", "candidate")
SCHEMA = "reality-ledger/1"


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def evidence_fingerprint(evidence: list[dict]) -> str:
    blob = json.dumps(evidence or [], ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def event_dedupe_key(finding_id: str, evidence: list[dict]) -> str:
    return hashlib.sha256(
        f"{finding_id}|{evidence_fingerprint(evidence)}".encode("utf-8")
    ).hexdigest()


class RealityLedger:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _seen_keys(self) -> set[str]:
        keys: set[str] = set()
        if not self.path.exists():
            return keys
        with self.path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                keys.add(str(row.get("dedupe_key") or ""))
        keys.discard("")
        return keys

    def append(self, event: dict[str, Any]) -> dict[str, Any]:
        kind = str(event.get("kind") or "")
        if kind not in KINDS:
            raise ValueError(f"kind must be one of {KINDS}")
        status = str(event.get("status") or "open")
        if status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}")
        fid = str(event.get("finding_id") or "").strip()
        if not fid:
            raise ValueError("finding_id required")
        evidence = list(event.get("evidence") or [])
        if status == "resolved" and not evidence:
            raise ValueError("resolved requires evidence")
        key = event_dedupe_key(fid, evidence)
        if key in self._seen_keys():
            return {"appended": False, "reason": "duplicate", "dedupe_key": key}
        rec = {
            "schema": SCHEMA,
            "kind": kind,
            "finding_id": fid,
            "source_agent": str(event.get("source_agent") or "nervous-recovery"),
            "observed_at": str(event.get("observed_at") or _utc()),
            "severity": str(event.get("severity") or "INFO"),
            "status": status,
            "evidence": evidence,
            "supersedes": list(event.get("supersedes") or []),
            "confidence": float(event.get("confidence") or 0.0),
            "dedupe_key": key,
            "recorded_at": _utc(),
            "ttl_hours": event.get("ttl_hours"),
            "notes": event.get("notes"),
        }
        line = json.dumps(rec, ensure_ascii=False)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        prior = self.path.read_text("utf-8") if self.path.exists() else ""
        tmp.write_text(prior + line + "\n", encoding="utf-8")
        os.replace(tmp, self.path)
        return {"appended": True, "dedupe_key": key, "record": rec}

    def mark_stale(self, *, older_than_hours: float, now: datetime | None = None) -> int:
        """Return count of events that *would* be stale. Does not rewrite history."""
        now = now or datetime.now(timezone.utc)
        n = 0
        if not self.path.exists():
            return 0
        with self.path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                ttl = row.get("ttl_hours")
                if ttl is None:
                    continue
                try:
                    obs = datetime.fromisoformat(str(row["observed_at"]).replace("Z", "+00:00"))
                except (KeyError, ValueError):
                    continue
                age_h = (now - obs).total_seconds() / 3600.0
                if age_h > float(ttl) and row.get("status") not in ("resolved", "superseded"):
                    n += 1
        return n
