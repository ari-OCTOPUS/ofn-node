"""One cycle of the system. Two modes:

  loop  -> perception + guardian + creativity   (cheap; run several times/day)
  full  -> loop + doctor                          (premium Opus; weekly)

PLAN-GATED: once plan.yaml is complete (or status != active) the loop IDLES --
it logs a NOTE and spends nothing. Nothing is ever APPLIED (propose-only).
Resilient: a failing creativity/LLM call is logged and the cycle continues.

Usage:
  python run.py [loop|full] [vault_dir]
  ANTHROPIC_API_KEY=sk-...  python run.py loop /path/to/vault
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
for sub in ("ledger", "common", "perception", "agents"):
    sys.path.insert(0, str(ROOT / sub))

from config import Genome            # noqa: E402
from ledger import Ledger           # noqa: E402
from indexer import Indexer         # noqa: E402
import watcher                       # noqa: E402
from guardian import Guardian       # noqa: E402
from creativity import Creativity   # noqa: E402
from doctor import Doctor           # noqa: E402


def plan_active(root: Path):
    """The loop's stop condition. Returns (active?, human reason)."""
    p = root / "plan.yaml"
    if not p.exists():
        return True, "no plan.yaml (assume active)"
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if str(data.get("status", "active")).lower() != "active":
        return False, f"status={data.get('status')}"
    pending = [m.get("id") for m in data.get("milestones", []) if not m.get("done")]
    if pending:
        return True, f"{len(pending)} pending: {', '.join(pending)}"
    return False, "all milestones done"


def main():
    args = list(sys.argv[1:])
    mode = args.pop(0) if args and args[0] in ("loop", "full") else "full"
    vault = Path(args[0]) if args else None

    genome = Genome.load(ROOT / "genome")
    ledger = Ledger(ROOT / "ledger" / "ledger.jsonl")

    active, why = plan_active(ROOT)
    if not active:
        ledger.append("NOTE", {"loop": "idle", "reason": why}, actor="scheduler")
        print(f"plan complete -> loop IDLE ({why}); nothing spent.")
        return 0
    print(f"[{mode}] plan active -- {why}")

    if vault and vault.exists():
        ix = Indexer(ROOT / "index.db")
        print("perception:", watcher.reconcile(vault, ix, ledger))

    g = Guardian(genome, ledger).tick()
    print("guardian:", "HALT" if g["halt"] else "ok", g["alerts"] or "")
    if g["halt"]:
        print("halted by guardian -- not proceeding.")
        return 1

    llm_fn = None
    if os.environ.get("ANTHROPIC_API_KEY"):
        from llm import LLMClient, creativity_llm_fn
        llm_fn = creativity_llm_fn(LLMClient(genome, ledger=ledger))
        print("creativity: REAL model (routed by tier)")
    else:
        print("creativity: offline stub (no ANTHROPIC_API_KEY)")
    try:
        prop = Creativity(ledger, vault).propose(topic="cost", llm_fn=llm_fn)
        print("  idea:", str(prop["payload"]["idea"])[:80],
              "| confidence:", prop["payload"]["confidence"])
    except Exception as exc:                      # a bad model reply must not kill the cycle
        ledger.append("NOTE", {"creativity_error": str(exc)[:200]}, actor="creativity")
        print(f"  creativity skipped this cycle: {exc}")

    if mode == "full":
        print("\n" + Doctor(genome, ledger).run())
    return 0


if __name__ == "__main__":
    sys.exit(main())
