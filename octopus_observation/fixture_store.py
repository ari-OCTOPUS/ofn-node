"""JSONL fixture store for claim.v1. Not evidence.db. Not YAML.

derived_resolved_count is a store count, not an official n.

S2b lane B hardening (2026-09-01):
- F6: only ``.jsonl`` is accepted. ``.json`` is rejected — the store has
  exactly one writer and it writes JSON Lines; a two-row ``.json`` file
  would not be valid JSON, so the suffix is refused rather than half-loved.
- F7: a malformed line raises ObservationContractError("fixture-line-not-json")
  carrying the 1-based physical line number and never the line content.
- F8: duplicate claim_ids are refused on append AND on load, so
  derived_resolved_count cannot be inflated by an accidental double-write.
"""
from __future__ import annotations

import json
from pathlib import Path

from .claim_record import ClaimV1, claim_from_mapping
from .observation_record import ObservationContractError


class FixtureClaimStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        suffix = self.path.suffix.lower()
        if suffix in {".yaml", ".yml"}:
            raise ObservationContractError("fixture-yaml-forbidden")
        if suffix == ".db":
            raise ObservationContractError("fixture-db-forbidden")
        if suffix == ".json":
            raise ObservationContractError("fixture-suffix-not-jsonl")
        if suffix != ".jsonl":
            raise ObservationContractError("fixture-suffix-not-jsonl")

    def append(self, claim: ClaimV1) -> None:
        claim.validate()
        seen = {c.claim_id for c in self.load()}
        if claim.claim_id in seen:
            raise ObservationContractError(
                f"claim-duplicate-id:{claim.claim_id}")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(claim.to_dict(), sort_keys=True, ensure_ascii=False) + "\n"
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(line)

    def load(self) -> list[ClaimV1]:
        if not self.path.exists():
            return []
        records: list[ClaimV1] = []
        seen: set[str] = set()
        for lineno, raw in enumerate(
                self.path.read_text(encoding="utf-8").splitlines(), start=1):
            if not raw.strip():
                continue
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                # Line number only — the content never travels into the error.
                raise ObservationContractError(
                    f"fixture-line-not-json:{lineno}") from None
            claim = claim_from_mapping(data)
            if claim.claim_id in seen:
                raise ObservationContractError(
                    f"claim-duplicate-id:{claim.claim_id}")
            seen.add(claim.claim_id)
            records.append(claim)
        return records

    def store_line_count(self) -> int:
        """Number of claim rows in this store file. Not an official n."""
        return len(self.load())

    def derived_resolved_count(self) -> int:
        """Count resolved rows in this store. Not an official n."""
        return sum(1 for claim in self.load() if claim.is_resolved())
