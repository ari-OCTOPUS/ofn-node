"""Evolutionary Doctor harness (weekly health + propose-only adjudication).

Reads METRIC events (from perception/guardian) and PROPOSALs (from creativity/
guardian), compares health against the FROZEN genome metrics, red-teams each
proposal against the genome, and emits a Markdown report + owner-gate PROPOSALs.
It never APPLIES anything. The evaluator it scores against lives in the genome,
so the Doctor cannot move its own goalposts (anti reward-hacking).

Deep red-team is the LLM's job (see agents/evolutionary-doctor.md, premium tier);
the code here does the deterministic guardrails: thresholds + genome-distance.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
for _sub in ("ledger", "common"):
    sys.path.insert(0, str(_ROOT / _sub))

from config import Genome           # noqa: E402
from ledger import Ledger           # noqa: E402

_CMP = re.compile(r"^\s*(<=|>=|<|>)\s*([0-9.]+)\s*$")
_GENOME_WORDS = ("genome", "evaluator", "invariant", "budget cap",
                 "monthly_hard_cap", "approve-first", "approve_first")


def _latest(ledger: Ledger, key: str):
    val = None
    for rec in ledger.filter(event_type="METRIC"):
        if key in rec.get("payload", {}):
            val = rec["payload"][key]
    return val


def _check(value: Any, good: Any) -> str:
    if value is None:
        return "no-data"
    m = _CMP.match(str(good or ""))
    if not m or not isinstance(value, (int, float)):
        return "see-note"
    op, thr = m.group(1), float(m.group(2))
    ok = {"<": value < thr, "<=": value <= thr,
          ">": value > thr, ">=": value >= thr}[op]
    return "ok" if ok else "WARN"


class Doctor:
    def __init__(self, genome: Genome, ledger: Ledger) -> None:
        self.genome = genome
        self.ledger = ledger

    def _distance_from_genome(self, proposal: dict[str, Any]) -> int:
        """0 = safe to forward. >0 = touches an invariant -> reject."""
        if proposal.get("touches_genome"):
            return 1
        blob = " ".join(str(proposal.get(k, "")) for k in
                        ("idea", "why_it_might_be_genius", "why_it_might_be_insane")).lower()
        return 1 if any(w in blob for w in _GENOME_WORDS) else 0

    def _open_proposals(self) -> list[dict[str, Any]]:
        """Only real agent proposals -- skip the Doctor's own past reports so it
        does not re-adjudicate its own output every run."""
        out = []
        for rec in self.ledger.filter(event_type="PROPOSAL"):
            if rec.get("actor") == "doctor":
                continue
            p = rec.get("payload", {})
            if p.get("doctor_report") or not p.get("idea"):
                continue
            out.append(p)
        return out

    def run(self) -> str:
        lines = ["# Doctor — Health Report", "", "## Health"]
        for name in self.genome.metrics.get("metrics", {}):
            val = _latest(self.ledger, name)
            good = self.genome.metric_good(name)
            lines.append(f"- {name}: {val}  (good: {good}) -> {_check(val, good)}")

        lines += ["", "## Proposals adjudicated"]
        accepted = []
        proposals = self._open_proposals()
        if not proposals:
            lines.append("- none open this cycle")
        for p in proposals:
            dist = self._distance_from_genome(p)
            reversible = bool(p.get("reversible", False))
            verdict = "accept->owner-gate" if (dist == 0 and reversible) else "reject"
            if verdict.startswith("accept"):
                accepted.append(p)
            lines.append(f"- \"{str(p.get('idea', ''))[:70]}\" "
                         f"— distance_from_genome={dist}, reversible={reversible} "
                         f"=> {verdict}")

        lines += ["", "## Recommendations for the owner (propose-only)"]
        if not accepted:
            lines.append("- none this cycle")
        for p in accepted[:3]:
            lines.append(f"1. {p.get('idea')} — test: {p.get('smallest_test')} "
                         f"— kill: {p.get('kill_criteria')}")

        report = "\n".join(lines)
        self.ledger.append("PROPOSAL",
                           {"doctor_report": True, "accepted": len(accepted),
                            "summary": report[:400]},
                           actor="doctor", to="owner")
        return report


if __name__ == "__main__":
    gen = Genome.load(sys.argv[1] if len(sys.argv) > 1 else _ROOT / "genome")
    lg = Ledger(sys.argv[2] if len(sys.argv) > 2 else _ROOT / "ledger" / "ledger.jsonl")
    print(Doctor(gen, lg).run())
