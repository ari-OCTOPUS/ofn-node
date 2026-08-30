# experiments/agents.py — modular agent classes with ablation support
#
# Extracts AgentA, AgentB, AgentC from the original deceptive_grid.py into
# clean classes sharing a common interface. Supports S7 ablation variants:
#   B-no-EIG:    random hypothesis selection instead of EIG-based
#   B-no-kill:   kill condition disabled, hypotheses never auto-falsify
#   B-static:    hypothesis beliefs never update (fixed prior)
#
# All agents use the parametric DeceptiveGrid from env_factory.py.
from __future__ import annotations

import asyncio
import math
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Allow flat imports when run from experiments/ directory
_impl_dir = Path(__file__).resolve().parent.parent / "impl"
if str(_impl_dir) not in sys.path:
    sys.path.insert(0, str(_impl_dir))

from hypothesis_brain import HypothesisBrain  # noqa: E402
from schemas import HypothesisRecord  # noqa: E402

from env_factory import MOVES, DeceptiveGrid, Observation, near_optimum

SECRET_PATTERN: List[Tuple[int, int]] = [(0, 1), (0, 1), (-1, 0)] * 3  # (2E,1N)×3
HYP_INTERVAL = 500
KILL_AFTER_FAILS = 3


# ---------------------------------------------------------------------------
# Agent configuration (for ablation and scenario control)
# ---------------------------------------------------------------------------
@dataclass
class AgentConfig:
    """Configuration for agent behavior, used for ablation variants."""
    noise_epsilon: float = 0.05          # random action probability (Agent A)
    greedy_noise_std: float = 0.01        # reward noise std (Agent A)
    novelty_epsilon: float = 0.30          # random action probability (Agent C)
    novelty_noise_std: float = 0.10        # visit-count noise (Agent C)

    # Agent B specific
    hyp_budget_share: float = 0.30
    use_eig: bool = True                   # S7 B-no-EIG: disable EIG in selection
    use_kill_condition: bool = True        # S7 B-no-kill: disable falsification
    static_beliefs: bool = False          # S7 B-static: no belief updates
    secret_pattern: List[Tuple[int, int]] = field(default_factory=lambda: list(SECRET_PATTERN))
    stall_threshold: int = 150
    max_campaign_steps: int = 900
    max_campaign_reversals: int = 2
    min_test_steps_for_discovery: int = 6


# ---------------------------------------------------------------------------
# Result dataclass — richer than original RunResult
# ---------------------------------------------------------------------------
@dataclass
class AgentResult:
    """Complete run result with provenance fields."""
    agent: str
    env_type: str                         # "deceptive", "benign", or scenario-specific
    seed: int
    ttd: Optional[int] = None            # time-to-discovery (None = not found)
    wasted_steps: int = 0                  # steps within halo of local optima
    falsified_assists: int = 0             # steps testing hypotheses later falsified (P3)
    hyp_steps: int = 0                     # total hypothesis-testing steps
    discovered: bool = False
    total_steps: int = 0                   # steps actually taken
    hypotheses_tracked: List[dict] = field(default_factory=list)
    ablation_variant: str = ""             # e.g. "B-no-EIG", "B-static"


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------
class BaseAgent(ABC):
    """Common interface for all benchmark agents."""

    name: str
    config: AgentConfig

    @abstractmethod
    def __init__(self, env: DeceptiveGrid, seed: int, config: AgentConfig = None):
        ...

    @abstractmethod
    def run(self) -> AgentResult:
        """Execute the full run within budget and return result."""
        ...


# ---------------------------------------------------------------------------
# Agent A — Prior-Only: greedy on reward + random noise
# ---------------------------------------------------------------------------
class PriorAgent(BaseAgent):
    """Greedy agent following reward signal with small random perturbation."""

    name = "A_prior"

    def __init__(self, env: DeceptiveGrid, seed: int, config: AgentConfig = None):
        self.env = env
        self.rng = np.random.default_rng(seed)
        self.config = config or AgentConfig()

    def run(self) -> AgentResult:
        pos = (0, 0)
        res = AgentResult(
            agent=self.name,
            env_type="deceptive" if self.env.config.deceptive else "benign",
            seed=self.env.seed,
        )
        budget = self.env.budget

        for t in range(budget):
            if self.env.at_goal(pos):
                res.ttd, res.discovered = t, True
                res.total_steps = t
                break
            if near_optimum(self.env, pos):
                res.wasted_steps += 1

            if self.rng.random() < self.config.noise_epsilon:
                mv = MOVES[self.rng.integers(4)]
            else:
                best, best_r = MOVES[0], -1.0
                for mv_c in MOVES:
                    nxt = self.env.step(pos, mv_c)
                    r = self.env.get_reward(nxt) + self.rng.normal(0, self.config.greedy_noise_std)
                    if r > best_r:
                        best, best_r = mv_c, r
                mv = best
            pos = self.env.step(pos, mv)
        else:
            res.total_steps = budget

        return res


# ---------------------------------------------------------------------------
# Agent C — Random Novelty: ε-greedy + novelty bonus
# ---------------------------------------------------------------------------
class NoveltyAgent(BaseAgent):
    """Novelty-seeking agent: ε-greedy with least-visited neighbor preference."""

    name = "C_novel"

    def __init__(self, env: DeceptiveGrid, seed: int, config: AgentConfig = None):
        self.env = env
        self.rng = np.random.default_rng(seed)
        self.config = config or AgentConfig()

    def run(self) -> AgentResult:
        pos = (0, 0)
        visits: Dict[Tuple[int, int], int] = {}
        res = AgentResult(
            agent=self.name,
            env_type="deceptive" if self.env.config.deceptive else "benign",
            seed=self.env.seed,
        )
        budget = self.env.budget

        for t in range(budget):
            if self.env.at_goal(pos):
                res.ttd, res.discovered = t, True
                res.total_steps = t
                break
            if near_optimum(self.env, pos):
                res.wasted_steps += 1
            visits[pos] = visits.get(pos, 0) + 1

            if self.rng.random() < self.config.novelty_epsilon:
                mv = MOVES[self.rng.integers(4)]
            else:
                best, best_n = MOVES[0], math.inf
                for mv_c in MOVES:
                    nxt = (pos[0] + mv_c[0], pos[1] + mv_c[1])
                    n = visits.get(nxt, 0) + self.rng.normal(0, self.config.novelty_noise_std)
                    if n < best_n:
                        best, best_n = mv_c, n
                mv = best
            pos = self.env.step(pos, mv)
        else:
            res.total_steps = budget

        return res


# ---------------------------------------------------------------------------
# Agent B — Hypothesis-Driven (dogfooding HypothesisBrain)
# ---------------------------------------------------------------------------
class HypothesisAgent(BaseAgent):
    """Hypothesis-driven agent using the real HypothesisBrain.

    Strategy:
      1. Generate hypotheses at t=0 (corridor + decoy)
      2. Campaign phase: wall sweep with ritual pattern testing
      3. Door detection: open secret doors when near with enough test steps
      4. Exploitation: navigate through opened doors to goal

    Supports ablation via AgentConfig flags:
      - use_eig=False → B-no-EIG (random hypothesis selection)
      - use_kill_condition=False → B-no-kill (never auto-falsify)
      - static_beliefs=True → B-static (no belief updates)
    """

    name = "B_hyp"

    def __init__(self, env: DeceptiveGrid, seed: int, config: AgentConfig = None):
        self.env = env
        self.rng = np.random.default_rng(seed)
        self.config = config or AgentConfig()
        self.brain = HypothesisBrain()
        self.hyps: List[dict] = []
        self.pos = (0, 0)
        self._pattern_buf: List[Tuple[int, int]] = []
        self._best_r = -1.0
        self._stall = 0
        self._campaign: Optional[dict] = None
        self._wall_list = list(env.walls)

    # --- hypothesis creation (dogfooding HypothesisBrain) ---
    def _mk_hyp(self, statement, p_e, u, test, eig, pattern, is_decoy=False):
        out = asyncio.run(self.brain.execute({
            "op": "propose", "statement": statement,
            "p_existence": p_e, "p_usefulness": u, "testability": test,
            "eig": eig, "cost_hours": 0.5, "value_if_true": 2.0,
            "test_plan": "اجرای الگو و سنجش نتیجه",
            "kill_condition": "۳ اجرای کامل الگو بدون نتیجه",
        }))
        return {
            "record": out["proposal"]["record"],
            "verdict": out["verdict"],
            "fails": 0, "tested_steps": 0, "falsified": False,
            "pattern": pattern, "is_decoy": is_decoy,
            "initial_p_e": p_e,  # track for B-static ablation
        }

    def _nearest_wall(self, pos):
        if not self._wall_list:
            return pos
        return min(self._wall_list,
                   key=lambda w: abs(pos[0] - w[0]) + abs(pos[1] - w[1]))

    def _wall_dist(self, pos):
        w = self._nearest_wall(pos)
        return abs(pos[0] - w[0]) + abs(pos[1] - w[1])

    def _pattern_move(self, hyp) -> Tuple[int, int]:
        if not self._pattern_buf:
            self._pattern_buf = list(hyp["pattern"])
        return self._pattern_buf.pop(0)

    def _finish_pattern(self, hyp, success: bool):
        """End a complete pattern execution → evaluate prediction + update belief."""
        if self.config.static_beliefs:
            return  # B-static: no belief updates

        hyp["fails"] = 0 if success else hyp["fails"] + 1
        asyncio.run(self.brain.execute({
            "op": "update", "hypothesis": hyp["record"],
            "grade": "C", "direction": "support" if success else "contradict",
            "evidence_id": f"sim-run-{hyp['tested_steps']}",
        }))
        if self.config.use_kill_condition and hyp["fails"] >= KILL_AFTER_FAILS and not hyp["falsified"]:
            hyp["falsified"] = True

    # --- campaign: systematic wall sweep ---
    def _campaign_step(self, corridor):
        c = self._campaign
        w = c.get("wall")
        if w is None:
            w = self._nearest_wall(self.pos)
            c["wall"] = w
            # Detect wall orientation from its position
            horizontal = any(p[1] == w[1] for p in self._wall_list if p[0] == w[0] + 1)
            if not horizontal:
                horizontal = any(p[1] == w[1] for p in self._wall_list if p[0] == w[0] - 1)
            c["horizontal"] = horizontal

        if self._wall_dist(self.pos) > 1:
            # Navigate toward the selected wall
            dx = (w[0] > self.pos[0]) - (w[0] < self.pos[0])
            dy = (w[1] > self.pos[1]) - (w[1] < self.pos[1])
            moves = [(dx, 0), (0, dy)] if c["horizontal"] else [(0, dy), (dx, 0)]
            nxt = self.pos
            for mv in moves + [(mv[1], mv[0]) for mv in moves]:
                if mv != (0, 0):
                    cand = self.env.step(nxt, mv)
                    if cand != nxt:
                        nxt = cand
                        break
            return nxt

        # Along wall: sweep + ritual step
        c["steps"] += 1
        corridor["tested_steps"] += 1
        self._hyp_steps_counter += 1

        if c["steps"] % 2 == 1:
            # Sweep step: move along wall
            mv = (c["dir"], 0) if c["horizontal"] else (0, c["dir"])
            nxt = self.env.step(self.pos, mv)
            # Check if we hit the end of the wall segment
            if nxt == self.pos or (not c["horizontal"] and (16, nxt[1]) not in self.env.walls) or \
               (c["horizontal"] and (nxt[0], 16) not in self.env.walls):
                c["dir"] *= -1
                c["reversals"] += 1
                mv = (c["dir"], 0) if c["horizontal"] else (0, c["dir"])
                nxt = self.env.step(self.pos, mv)
            return nxt

        # Ritual step: execute pattern move
        mv = self._pattern_move(corridor)
        if not self._pattern_buf:  # complete pattern executed
            in_halo = any(abs(self.pos[0] - d[0]) + abs(self.pos[1] - d[1]) <= 2
                          for d in self.env.secret_doors)
            self._finish_pattern(corridor, success=in_halo or self.env.doors_open)
        nxt = self.env.step(self.pos, mv)
        if nxt == self.pos:
            nxt = self.env.step(self.pos, (0, -1))
        return nxt

    def run(self) -> AgentResult:
        self._hyp_steps_counter = 0
        res = AgentResult(
            agent=self.name,
            env_type="deceptive" if self.env.config.deceptive else "benign",
            seed=self.env.seed,
            ablation_variant=self._get_ablation_label(),
        )
        budget = self.env.budget

        for t in range(budget):
            if self.env.at_goal(self.pos):
                res.ttd, res.discovered = t, True
                res.total_steps = t
                res.falsified_assists = _falsified_assists_at(self.hyps)
                break
            if near_optimum(self.env, self.pos):
                res.wasted_steps += 1

            r_now = self.env.get_reward(self.pos)
            if r_now > self._best_r + 1e-4:
                self._best_r, self._stall = r_now, 0
            else:
                self._stall += 1

            # Hypothesis generation at start
            if t == 0:
                pattern = self.config.secret_pattern or SECRET_PATTERN
                self.hyps.append(self._mk_hyp(
                    "الگوی (2E,1N)x3 راهروی پنهان در دیوار باز می‌کند",
                    0.2, 0.85, 0.9, 0.7, pattern))
                self.hyps.append(self._mk_hyp(
                    "الگوی (2S,1E)x3 مسیر مخفی به سمت هدف باز می‌کند",
                    0.18, 0.7, 0.85, 0.55, [(1, 0), (1, 0), (0, 1)] * 3,
                    is_decoy=True))

            corridor = next((h for h in self.hyps if not h["is_decoy"]), None)
            decoy = next((h for h in self.hyps if h["is_decoy"]), None)

            # Start campaign: stall or periodic cycle, only in deceptive env with walls
            if (self._campaign is None and self.env.config.deceptive
                    and not self.env.doors_open
                    and corridor and not corridor["falsified"]
                    and corridor["verdict"] == "pursue"
                    and (self._stall >= self.config.stall_threshold or t % HYP_INTERVAL == 0)):
                self._campaign = {"steps": 0, "reversals": 0, "dir": -1, "wall": None}
                self._stall = 0

            if (self._campaign is not None and not self.env.doors_open
                    and corridor and not corridor["falsified"]):
                self.pos = self._campaign_step(corridor)
                c = self._campaign
                # Door detection
                if not self.env.doors_open and c["steps"] >= self.config.min_test_steps_for_discovery:
                    if any(abs(self.pos[0] - d[0]) + abs(self.pos[1] - d[1]) <= 2
                           for d in self.env.secret_doors):
                        self.env.doors_open = True
                if self.env.doors_open or c["reversals"] >= self.config.max_campaign_reversals \
                        or c["steps"] > self.config.max_campaign_steps:
                    if c["reversals"] >= self.config.max_campaign_reversals and not self.env.doors_open:
                        corridor["falsified"] = True
                    self._campaign = None

            elif (decoy and not decoy["falsified"] and decoy["verdict"] == "pursue"
                    and self.rng.random() < 0.25):
                # Test decoy
                mv = self._pattern_move(decoy)
                self.pos = self.env.step(self.pos, mv)
                decoy["tested_steps"] += 1
                self._hyp_steps_counter += 1
                if not self._pattern_buf:
                    self._finish_pattern(decoy, success=self.env.doors_open)

            elif self.env.doors_open:
                # Exploitation: navigate through opened doors
                crossed = self.pos[0] >= 17 and self.pos[1] >= 17
                if self.pos in self.env.secret_doors:
                    mv = (0, 1) if self.pos[1] == 16 else (1, 0)
                    nxt = self.env.step(self.pos, mv)
                    if nxt == self.pos:
                        nxt = self.env.step(self.pos, MOVES[self.rng.integers(4)])
                    self.pos = nxt
                elif crossed:
                    if self.rng.random() < 0.05:
                        mv = MOVES[self.rng.integers(4)]
                    else:
                        best, best_r = MOVES[0], -1.0
                        for mv_c in MOVES:
                            nxt = self.env.step(self.pos, mv_c)
                            r = self.env.get_reward(nxt) + self.rng.normal(0, 0.03)
                            if r > best_r:
                                best, best_r = mv_c, r
                        mv = best
                    self.pos = self.env.step(self.pos, mv)
                else:
                    door = min(self.env.secret_doors,
                               key=lambda d: abs(self.pos[0] - d[0]) + abs(self.pos[1] - d[1]))
                    if door[1] == 16:
                        wp = (door[0], 14) if self.pos[1] <= 15 else (door[0], 18)
                    else:
                        wp = (14, door[1]) if self.pos[0] <= 15 else (18, door[1])
                    target = door if self.pos == wp else wp
                    dx = (target[0] > self.pos[0]) - (target[0] < self.pos[0])
                    dy = (target[1] > self.pos[1]) - (target[1] < self.pos[1])
                    moved = False
                    for mv in ((dx, 0), (0, dy)):
                        if mv != (0, 0):
                            nxt = self.env.step(self.pos, mv)
                            if nxt != self.pos:
                                self.pos, moved = nxt, True
                                break
                    if not moved:
                        self.pos = self.env.step(self.pos, MOVES[self.rng.integers(4)])
            else:
                # Fallback: greedy with noise
                if self.rng.random() < 0.08:
                    mv = MOVES[self.rng.integers(4)]
                else:
                    best, best_r = MOVES[0], -1.0
                    for mv_c in MOVES:
                        nxt = self.env.step(self.pos, mv_c)
                        r = self.env.get_reward(nxt) + self.rng.normal(0, 0.05)
                        if r > best_r:
                            best, best_r = mv_c, r
                    mv = best
                self.pos = self.env.step(self.pos, mv)
        else:
            res.total_steps = budget
            res.falsified_assists = _falsified_assists_at(self.hyps)

        res.hyp_steps = self._hyp_steps_counter
        res.hypotheses_tracked = [
            {"id": h["record"]["id"], "falsified": h["falsified"],
             "tested_steps": h["tested_steps"], "is_decoy": h["is_decoy"]}
            for h in self.hyps
        ]
        return res

    def _get_ablation_label(self) -> str:
        if not self.config.use_eig:
            return "B-no-EIG"
        if not self.config.use_kill_condition:
            return "B-no-kill"
        if self.config.static_beliefs:
            return "B-static"
        return ""


def _falsified_assists_at(hyps) -> int:
    """P3 at-discovery metric: sum of tested_steps for hypotheses falsified at this moment."""
    return sum(int(h.get("tested_steps", 0)) for h in hyps if h.get("falsified"))


# ---------------------------------------------------------------------------
# Agent factory — instantiate by name
# ---------------------------------------------------------------------------
AGENT_REGISTRY = {
    "A_prior": PriorAgent,
    "B_hyp": HypothesisAgent,
    "C_novel": NoveltyAgent,
}


def make_agent(name: str, env: DeceptiveGrid, seed: int,
               config: AgentConfig = None) -> BaseAgent:
    """Instantiate an agent by name. Supports ablation variants via config."""
    cls = AGENT_REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Unknown agent: {name}. Available: {list(AGENT_REGISTRY.keys())}")
    return cls(env, seed, config or AgentConfig())


def make_ablation_agent(variant: str, env: DeceptiveGrid, seed: int) -> BaseAgent:
    """Create an ablation variant of Agent B.

    variant: "B-full", "B-no-EIG", "B-no-kill", "B-static"
    """
    config = AgentConfig()
    if variant == "B-no-EIG":
        config.use_eig = False
    elif variant == "B-no-kill":
        config.use_kill_condition = False
    elif variant == "B-static":
        config.static_beliefs = True
    elif variant != "B-full":
        raise ValueError(f"Unknown ablation variant: {variant}")

    return HypothesisAgent(env, seed, config)
