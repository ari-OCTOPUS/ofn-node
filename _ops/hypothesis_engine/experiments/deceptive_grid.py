# experiments/deceptive_grid.py — backward-compatible CLI wrapper
#
# Thin wrapper over the new modular benchmark framework.
# Preserves the original CLI interface:
#   python deceptive_grid.py --runs 100 --out results.csv
#
# All logic now delegates to env_factory.py + agents.py.
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import List

# Ensure imports work from experiments/ directory
_experiments_dir = Path(__file__).resolve().parent
if str(_experiments_dir) not in sys.path:
    sys.path.insert(0, str(_experiments_dir))
_impl_dir = _experiments_dir.parent / "impl"
if str(_impl_dir) not in sys.path:
    sys.path.insert(0, str(_impl_dir))

from env_factory import DeceptiveGrid, make_S0_reference
from agents import (
    AgentResult,
    HypothesisAgent,
    NoveltyAgent,
    PriorAgent,
    _falsified_assists_at,
)

# Re-export for backward compat (some test imports may use these)
from env_factory import MOVES, DEFAULT_SECRET_PATTERN as SECRET_PATTERN


# ---------------------------------------------------------------------------
# Legacy RunResult — compatible with original output format
# ---------------------------------------------------------------------------
class RunResult:
    """Backward-compatible RunResult matching original CSV schema."""
    __slots__ = ("agent", "env", "seed", "ttd", "wasted_steps",
                 "falsified_assists", "hyp_steps", "discovered")

    def __init__(self, agent: str, env: str, seed: int, ttd=None,
                 wasted_steps=0, falsified_assists=0, hyp_steps=0,
                 discovered=False):
        self.agent = agent
        self.env = env
        self.seed = seed
        self.ttd = ttd
        self.wasted_steps = wasted_steps
        self.falsified_assists = falsified_assists
        self.hyp_steps = hyp_steps
        self.discovered = discovered


def _to_legacy_result(r: AgentResult) -> RunResult:
    """Convert new AgentResult to legacy RunResult."""
    return RunResult(
        agent=r.agent,
        env=r.env_type,
        seed=r.seed,
        ttd=r.ttd,
        wasted_steps=r.wasted_steps,
        falsified_assists=r.falsified_assists,
        hyp_steps=r.hyp_steps,
        discovered=r.discovered,
    )


def falsified_assists_at(hyps) -> int:
    """Backward-compatible public name for the canonical P3 accounting helper."""
    return _falsified_assists_at(hyps)


# ---------------------------------------------------------------------------
# Legacy functions — now thin wrappers around agents.py
# ---------------------------------------------------------------------------

def _make_env(deceptive: bool, seed: int) -> DeceptiveGrid:
    """Create environment using the new factory."""
    return make_S0_reference(seed, deceptive=deceptive)


def run_prior_only(env: DeceptiveGrid, seed: int) -> RunResult:
    """Agent A — Prior-Only (legacy interface)."""
    agent = PriorAgent(env, seed)
    return _to_legacy_result(agent.run())


def run_novelty(env: DeceptiveGrid, seed: int) -> RunResult:
    """Agent C — Random Novelty (legacy interface)."""
    agent = NoveltyAgent(env, seed)
    return _to_legacy_result(agent.run())


class AgentB:
    """Agent B — Hypothesis Engine (legacy interface)."""

    def __init__(self, env: DeceptiveGrid, seed: int):
        self._agent = HypothesisAgent(env, seed)

    def run(self) -> RunResult:
        return _to_legacy_result(self._agent.run())


# ---------------------------------------------------------------------------
# Legacy main — preserves original CLI and CSV output
# ---------------------------------------------------------------------------
def run_all(n_runs: int, out_path: Path):
    rows: List[RunResult] = []
    for env_name in ("deceptive", "benign"):
        dec = env_name == "deceptive"
        for seed in range(n_runs):
            env = _make_env(dec, seed)
            rows.append(run_prior_only(env, seed))
            env = _make_env(dec, seed)
            rows.append(run_novelty(env, seed))
            env = _make_env(dec, seed)
            rows.append(AgentB(env, seed).run())
            if seed % 10 == 0:
                print(f"  {env_name} seed={seed} done", flush=True)

    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["agent", "env", "seed", "ttd", "discovered",
                     "wasted_steps", "falsified_assists", "hyp_steps"])
        for r in rows:
            w.writerow([r.agent, r.env, r.seed, r.ttd if r.ttd is not None else "",
                        int(r.discovered), r.wasted_steps, r.falsified_assists,
                        r.hyp_steps])
    print(f"ذخیره شد: {out_path} ({len(rows)} run)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=100)
    ap.add_argument("--out", type=Path, default=Path("results.csv"))
    args = ap.parse_args()
    run_all(args.runs, args.out)
