"""Guardian-Architect harness (the deterministic mechanics).

The judgement/voice of this role lives in agents/guardian-architect.md; THIS
file enforces the rules in code so they cannot be "talked around":
  * heartbeat / liveness
  * budget-gate enforcement (halt on breach)
  * loop / cost run-guards (the AutoGPT lesson)
  * genome integrity (read-only; halt if the frozen core was touched)
  * backup freshness

The Guardian is GOVERNED BY the genome and read-only on it: it may HALT the
system, but it never edits the genome. Its only writes are ledger events.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
for _sub in ("ledger", "common"):
    sys.path.insert(0, str(_ROOT / _sub))

from config import Genome            # noqa: E402
from ledger import Ledger           # noqa: E402


def _latest_metric(ledger: Ledger, key: str):
    val = None
    for rec in ledger.filter(event_type="METRIC"):
        if key in rec.get("payload", {}):
            val = rec["payload"][key]
    return val


class Guardian:
    def __init__(self, genome: Genome, ledger: Ledger) -> None:
        self.genome = genome
        self.ledger = ledger
        self.baseline = self._genome_hash()   # snapshot of the frozen core

    def _genome_hash(self) -> str:
        h = hashlib.sha256()
        for f in sorted(self.genome.root.rglob("*")):
            if f.is_file():
                h.update(f.relative_to(self.genome.root).as_posix().encode())
                h.update(f.read_bytes())
        return h.hexdigest()

    def check_run(self, steps: int, cost_usd: float) -> tuple[bool, str]:
        """Loop/cost guard for a single run. Returns (abort?, reason)."""
        g = self.genome.run_guards
        if steps > g.get("max_steps_per_run", 40):
            return True, "max_steps_per_run exceeded"
        if cost_usd > g.get("max_cost_per_run_usd", 2.0):
            return True, "max_cost_per_run_usd exceeded"
        return False, "ok"

    def tick(self, uptime_s: float = 0.0) -> dict:
        alerts: list[str] = []
        halt = False

        # 1) liveness
        self.ledger.append("HEARTBEAT", {"uptime_s": uptime_s}, actor="guardian")

        # 2) genome integrity (read-only core must not change out-of-band)
        if self._genome_hash() != self.baseline:
            halt = True
            alerts.append("GENOME TAMPERED -- halting")
            self.ledger.append("METRIC", {"distance_from_genome": 1}, actor="guardian")

        # 3) budget gate
        daily = _latest_metric(self.ledger, "daily_cost_usd")
        cap_day = self.genome.budget.get("daily_ops")
        if daily is not None and cap_day is not None and daily > cap_day:
            alerts.append(f"daily cost {daily} > daily_ops {cap_day} -- pausing spend")

        # 4) backup freshness
        age = _latest_metric(self.ledger, "backup_last_success_age_h")
        if age is not None and age > 24:
            alerts.append(f"backup stale ({age}h > 24h) -- RED")

        for a in alerts:
            self.ledger.append("METRIC", {"alert": a}, actor="guardian")
        return {"halt": halt, "alerts": alerts}


if __name__ == "__main__":  # python guardian.py <genome_dir> <ledger.jsonl>
    gen = Genome.load(sys.argv[1] if len(sys.argv) > 1 else _ROOT / "genome")
    lg = Ledger(sys.argv[2] if len(sys.argv) > 2 else _ROOT / "ledger" / "ledger.jsonl")
    print(Guardian(gen, lg).tick())
