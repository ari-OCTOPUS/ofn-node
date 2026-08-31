"""JSONL fixture store for claim.v1. Not evidence.db. Not YAML.

derived_resolved_count is a store count, not an official n.
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
        if suffix not in {".jsonl", ".json"}:
            raise ObservationContractError("fixture-suffix-not-json")

    def append(self, claim: ClaimV1) -> None:
        claim.validate()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(claim.to_dict(), sort_keys=True, ensure_ascii=False) + "\n"
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(line)

    def load(self) -> list[ClaimV1]:
        if not self.path.exists():
            return []
        records: list[ClaimV1] = []
        for raw in self.path.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            records.append(claim_from_mapping(json.loads(raw)))
        return records

    def derived_resolved_count(self) -> int:
        """Count resolved rows in this store. Not an official n."""
        return sum(1 for claim in self.load() if claim.is_resolved())
