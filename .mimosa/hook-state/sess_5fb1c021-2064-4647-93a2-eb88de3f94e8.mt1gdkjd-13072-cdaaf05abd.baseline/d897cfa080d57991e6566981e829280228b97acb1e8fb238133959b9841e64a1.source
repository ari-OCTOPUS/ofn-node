"""Guardian-Architect harness (the deterministic mechanics).

The judgement/voice of this role lives in agents/guardian-architect.md; THIS
file enforces the rules in code so they cannot be "talked around":
  * heartbeat / liveness
  * budget gate: sums TODAY's real LLM cost and alerts if it breaches daily_ops
  * loop / cost run-guards (the AutoGPT lesson)
  * genome integrity (read-only; halt if the frozen core was touched)
  * backup freshness: computes real age from the last backup event

The Guardian is GOVERNED BY the genome and read-only on it: it may HALT the
system, but it never edits the genome. Its only writes are ledger events.

Reuse one Guardian instance across a loop so its genome baseline is captured
ONCE at start -- constructing a fresh Guardian every tick would reset the
baseline to "now" and never detect tampering.
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
for _sub in ("ledger", "common"):
    sys.path.insert(0, str(_ROOT / _sub))

from config import Genome            # noqa: E402
from ledger import Ledger           # noqa: E402


def _today_llm_cost(ledger: Ledger) -> float:
    """Sum of llm_cost_usd METRICs logged today (UTC)."""
    today = datetime.now(timezone.utc).date().isoformat()
    total = 0.0
    for rec in ledger.filter(event_type="METRIC"):
        p = rec.get("payload", {})
        if "llm_cost_usd" in p and str(rec.get("ts", "")).startswith(today):
            try:
                total += float(p["llm_cost_usd"] or 0)
            except (TypeError, ValueError):
                pass
    return total


def _last_backup_age_h(ledger: Ledger) -> float | None:
    """Hours since the last backup event, or None if there has never been one."""
    last_ts = None
    for rec in ledger.iter_events():
        if rec.get("actor") == "backup" or "backup_last_success_age_h" in rec.get("payload", {}):
            last_ts = rec.get("ts")
    if not last_ts:
        return None
    try:
        t = datetime.fromisoformat(last_ts)
        return (datetime.now(timezone.utc) - t).total_seconds() / 3600.0
    except (ValueError, TypeError):
        return None


class Guardian:
    def __init__(self, genome: Genome, ledger: Ledger) -> None:
        self.genome = genome
        self.ledger = ledger
        self.baseline = self._genome_hash()   # captured ONCE; reuse the instance

    def _genome_hash(self) -> str:
        h = hashlib.sha256()
        for f in sorted(self.genome.root.rglob("*")):
            if f.is_file() and f.suffix != ".lock":
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

        self.ledger.append("HEARTBEAT", {"uptime_s": uptime_s}, actor="guardian")

        # genome integrity (read-only core must not change out-of-band)
        if self._genome_hash() != self.baseline:
            halt = True
            alerts.append("GENOME TAMPERED -- halting")
            self.ledger.append("METRIC", {"distance_from_genome": 1}, actor="guardian")

        # budget gate: today's actual LLM spend vs the daily cap
        cap_day = self.genome.budget.get("daily_ops")
        if cap_day is not None:
            spent = _today_llm_cost(self.ledger)
            if spent > cap_day:
                alerts.append(f"today's LLM cost ${spent:.4f} > daily_ops ${cap_day} -- pause spend")

        # backup freshness (real age)
        age = _last_backup_age_h(self.ledger)
        if age is not None and age > 24:
            alerts.append(f"backup stale ({age:.0f}h > 24h) -- RED")

        for a in alerts:
            self.ledger.append("METRIC", {"alert": a}, actor="guardian")
        return {"halt": halt, "alerts": alerts}


if __name__ == "__main__":
    gen = Genome.load(sys.argv[1] if len(sys.argv) > 1 else _ROOT / "genome")
    lg = Ledger(sys.argv[2] if len(sys.argv) > 2 else _ROOT / "ledger" / "ledger.jsonl")
    print(Guardian(gen, lg).tick())
