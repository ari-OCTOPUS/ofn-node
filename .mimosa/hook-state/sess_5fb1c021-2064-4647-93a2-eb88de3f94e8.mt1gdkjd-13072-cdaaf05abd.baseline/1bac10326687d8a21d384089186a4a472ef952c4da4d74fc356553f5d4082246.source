"""Creativity Black-Box harness.

Read-only over the whole project (ledger = experience, vault = knowledge). It
assembles context and asks an LLM for a bold, madness-or-genius idea, then
ENFORCES the humility contract in code: every proposal MUST carry a confidence,
a kill-criteria, and a smallest-test, or it is rejected before it can be written.

The idea generation itself is an injected `llm_fn(context)->dict`. A deterministic
offline stub is used by default so the whole pipeline runs without an API key.
The agent's only write is a PROPOSAL event addressed to the Doctor -- never the
vault, never the genome, never code.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

_ROOT = Path(__file__).resolve().parents[1]
for _sub in ("ledger",):
    sys.path.insert(0, str(_ROOT / _sub))

from ledger import Ledger           # noqa: E402

REQUIRED = ("idea", "why_it_might_be_genius", "why_it_might_be_insane",
            "confidence", "kill_criteria", "smallest_test", "reversible")


def _stub_llm(context: dict[str, Any]) -> dict[str, Any]:
    """Offline placeholder so the pipeline runs end-to-end. Replace with a real
    LLM call (default tier = Sonnet) that receives `context` and returns the
    same schema."""
    return {
        "idea": "Route the nightly digest through Haiku and only escalate "
                "notes the digest flags as 'surprising' to Sonnet.",
        "why_it_might_be_genius": "cuts digest cost ~5x while keeping quality "
                                  "on the few notes that matter",
        "why_it_might_be_insane": "'surprising' is fuzzy; a bad classifier could "
                                  "hide important changes",
        "confidence": 0.35,
        "kill_criteria": "if >1 important note/week is missed, revert",
        "smallest_test": "shadow-run for 7 days; compare against full-Sonnet digest",
        "reversible": True,
        "context_seen": {"ledger_events": context.get("n_events"),
                         "vault_hits": context.get("n_hits")},
    }


class Creativity:
    def __init__(self, ledger: Ledger, vault: str | Path | None = None) -> None:
        self.ledger = ledger
        self.vault = Path(vault) if vault else None

    def gather_context(self, topic: str | None = None, limit: int = 40) -> dict[str, Any]:
        events = self.ledger.tail(limit)
        hits = 0
        if self.vault and self.vault.exists():
            hits = sum(1 for _ in self.vault.rglob("*.md"))
        return {"n_events": len(events), "n_hits": hits, "topic": topic,
                "recent_types": sorted({e.get("type") for e in events})}

    def propose(self, topic: str | None = None,
                llm_fn: Callable[[dict], dict] | None = None) -> dict[str, Any]:
        ctx = self.gather_context(topic)
        idea = (llm_fn or _stub_llm)(ctx)

        # ENFORCE the humility contract -- no exceptions.
        missing = [k for k in REQUIRED if k not in idea]
        if missing:
            raise ValueError(f"creativity output missing required fields: {missing}")
        if not str(idea.get("kill_criteria", "")).strip():
            raise ValueError("proposal rejected: empty kill_criteria (un-falsifiable)")
        idea["confidence"] = max(0.0, min(1.0, float(idea["confidence"])))

        rec = self.ledger.append("PROPOSAL", idea, actor="creativity",
                                 to="doctor", topic=topic)
        return rec


if __name__ == "__main__":  # python creativity.py <ledger.jsonl>
    lg = Ledger(sys.argv[1] if len(sys.argv) > 1 else _ROOT / "ledger" / "ledger.jsonl")
    r = Creativity(lg).propose(topic="cost")
    print("proposed:", r["payload"]["idea"], "| confidence:", r["payload"]["confidence"])
