#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ledger — EconomicLearningLedger: append-only, idempotent, tamper-evident.

No record may exist without a destiny: every append carries a terminal
`outcome`; a crash mid-flight is healed fail-closed on the next load
(interrupted records are marked ESCALATED_TO_OWNER, never left dangling).
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

from .receipts import canonical_json, sha256_text  # reuse LB receipt primitives

__all__ = ["EconomicLearningLedger"]

TERMINAL_OUTCOMES = ("PR_CREATED", "QUEUED_WITH_REASON", "REJECTED_WITH_REASON",
                     "ESCALATED_TO_OWNER", "RECORDED")


def _utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class EconomicLearningLedger:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()
        self.recover()

    # ---------------------------------------------------------------- append
    def append(self, record: dict) -> str:
        rid = record.get("record_id", "")
        if not rid:
            raise ValueError("record_id is required — anonymous records are forbidden")
        if self._seen_ids is None:
            self._load()
        if rid in self._seen_ids:
            return "duplicate-skipped"          # idempotent by stable record_id
        if record.get("outcome") not in TERMINAL_OUTCOMES:
            record = {**record, "outcome": "ESCALATED_TO_OWNER",
                      "outcome_note": "fail-closed: record reached ledger without destiny"}
        row = {"ts": _utcnow(), **record}
        row["line_sha256"] = sha256_text(canonical_json(row))
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(canonical_json(row) + "\n")
        self._seen_ids.add(rid)
        if hasattr(self, "_rows") and self._rows is not None:
            self._rows.append(row)
        return "appended"

    # ----------------------------------------------------------------- state
    def _load(self):
        self._seen_ids = set()
        self._rows = []
        for raw in self.path.read_text(encoding="utf-8").splitlines():
            if raw.strip():
                row = json.loads(raw)
                self._rows.append(row)
                if "record_id" in row:
                    self._seen_ids.add(row["record_id"])

    def rows(self) -> list[dict]:
        if not hasattr(self, "_rows") or self._rows is None:
            self._load()
        return list(self._rows)

    def counts(self) -> dict:
        rows = self.rows()
        by_kind: dict[str, int] = {}
        for r in rows:
            by_kind[r.get("kind", "?")] = by_kind.get(r.get("kind", "?"), 0) + 1
        return {"total": len(rows), "by_kind": by_kind,
                "unique_ids": len({r.get("record_id") for r in rows})}

    # ---------------------------------------------------------------- verify
    def verify(self) -> dict:
        bad = []
        n = 0
        for raw in self.path.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            n += 1
            try:
                rec = json.loads(raw)
                claimed = rec.pop("line_sha256", None)
                if claimed != sha256_text(canonical_json(rec)):
                    bad.append(n)
            except (ValueError, TypeError):
                bad.append(n)
        return {"lines": n, "bad_lines": bad, "valid": not bad}

    def orphans(self) -> int:
        rows = self.rows()
        superseded = {r.get("supersedes_line_sha256") for r in rows
                      if r.get("supersedes_line_sha256")}
        return sum(1 for r in rows
                   if r.get("outcome") not in TERMINAL_OUTCOMES
                   and r.get("line_sha256") not in superseded)

    # --------------------------------------------------------------- recover
    def recover(self) -> list[dict]:
        """Heal interrupted appends: any row without a terminal outcome is
        rewritten fail-closed (a fresh line, append-only, superseding the
        interrupted one)."""
        self._load()
        healed = []
        fixes = []
        for row in self._rows:
            if row.get("outcome") not in TERMINAL_OUTCOMES:
                fixed = {**row, "outcome": "ESCALATED_TO_OWNER",
                         "outcome_note": "recovered: interrupted_mid_flight",
                         "supersedes_line_sha256": row.get("line_sha256")}
                fixed["line_sha256"] = sha256_text(canonical_json(
                    {k: v for k, v in fixed.items() if k != "line_sha256"}))
                fixes.append(fixed)
                healed.append({"record_id": row.get("record_id"),
                               "fixed_outcome": "ESCALATED_TO_OWNER"})
        if fixes:
            with open(self.path, "a", encoding="utf-8") as fh:
                for f in fixes:
                    fh.write(canonical_json(f) + "\n")
            self._load()
        return healed
