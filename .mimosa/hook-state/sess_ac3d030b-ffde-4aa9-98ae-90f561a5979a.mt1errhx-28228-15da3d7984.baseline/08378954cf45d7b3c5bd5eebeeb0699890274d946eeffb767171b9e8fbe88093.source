"""Load the frozen genome (read-only) into typed, convenient access.

Every agent reads its rules from here. Nothing writes back -- the genome is
changed only through genome/genome_change_protocol.md. Requires PyYAML.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Genome:
    root: Path
    values: dict[str, Any]
    gates: dict[str, Any]
    metrics: dict[str, Any]
    backup: dict[str, Any]

    @classmethod
    def load(cls, genome_dir: str | Path) -> "Genome":
        p = Path(genome_dir)

        def y(name: str) -> dict[str, Any]:
            f = p / name
            if not f.exists():
                return {}
            return yaml.safe_load(f.read_text(encoding="utf-8")) or {}

        return cls(p, y("values.yaml"), y("gates.yaml"),
                   y("metrics.yaml"), y("backup.yaml"))

    # --- convenience accessors -------------------------------------------
    @property
    def budget(self) -> dict[str, Any]:
        return self.gates.get("budget_usd", {})

    @property
    def run_guards(self) -> dict[str, Any]:
        return self.gates.get("run_guards", {})

    @property
    def approve_first(self) -> bool:
        return bool(self.gates.get("approve_first", True))

    def metric_good(self, name: str) -> Any:
        m = self.metrics.get("metrics", {}).get(name, {}) or {}
        return m.get("good")

    def invariant_ids(self) -> list[str]:
        return [p.get("id") for p in self.values.get("invariant_principles", [])]
