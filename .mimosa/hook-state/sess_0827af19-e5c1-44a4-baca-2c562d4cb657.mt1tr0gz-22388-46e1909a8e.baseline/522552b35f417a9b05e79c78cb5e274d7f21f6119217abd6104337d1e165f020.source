# experiments/env_factory.py — parametric DeceptiveGrid with full configurability
#
# Supports S0–S8 scenarios: grid size, wall layout, deception type, noise,
# budget, reward mode, observation corruption, and deterministic hashing.
#
# Usage:
#   from experiments.env_factory import make_S0_reference, make_S1_unseen
#   env = make_S0_reference(seed=42)
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Callable, Dict, FrozenSet, List, Optional, Set, Tuple

import numpy as np

# Default constants matching the original hardcoded deceptive_grid.py
DEFAULT_GRID_SIZE = 32
DEFAULT_GOAL = (28, 28)
DEFAULT_BUDGET = 10_000
DEFAULT_SECRET_PATTERN: List[Tuple[int, int]] = [(0, 1), (0, 1), (-1, 0)] * 3  # (2E,1N)×3
DEFAULT_LOCAL_OPTIMA = [(26, 6), (6, 26)]
DEFAULT_WALL_RANGE = range(4, 28)
DEFAULT_SECRET_DOORS: Set[Tuple[int, int]] = {(9, 16), (22, 16), (16, 8), (16, 21)}
DEFAULT_OPTIMA_REWARD = 0.85

MOVES = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # E, W, S, N


# ---------------------------------------------------------------------------
# Observation wrapper — supports S4 partial/noisy observation
# ---------------------------------------------------------------------------
@dataclass
class Observation:
    """Wrapped observation with optional corruption for S4 noise scenarios."""
    pos: Tuple[int, int]
    reward: float
    neighbors: List[Tuple[int, int]]  # valid move destinations after step
    raw_reward: float = 0.0            # uncorrupted reward (for verification)
    is_dropped: bool = False           # observation was dropped (partial obs)
    is_stale: bool = False             # stale state snapshot
    is_noisy: bool = False             # reward was perturbed
    contradictory_clue: Optional[str] = None  # injected contradictory info


# ---------------------------------------------------------------------------
# Environment configuration — fully serializable for provenance hashing
# ---------------------------------------------------------------------------
@dataclass
class EnvConfig:
    """Complete environment specification — deterministic hash via to_dict()."""
    grid_size: int = DEFAULT_GRID_SIZE
    goal_pos: Tuple[int, int] = DEFAULT_GOAL
    deceptive: bool = True
    walls: List[Tuple[int, int]] = field(default_factory=list)
    secret_doors: List[Tuple[int, int]] = field(default_factory=list)
    local_optima: List[Tuple[int, int]] = field(default_factory=list)
    optima_reward: float = DEFAULT_OPTIMA_REWARD
    secret_pattern: List[Tuple[int, int]] = field(default_factory=list)
    budget: int = DEFAULT_BUDGET
    move_cost: float = 0.0                    # S3: cost per move
    reward_mode: str = "dense"                 # "dense" | "sparse" | "multi_goal"
    observation_noise_std: float = 0.0         # S4: Gaussian noise on reward
    observation_drop_rate: float = 0.0          # S4: probability of dropping observation
    action_failure_rate: float = 0.0           # S4: probability of action failing
    stale_observation_rate: float = 0.0       # S4: probability of stale state
    contradictory_clue_rate: float = 0.0        # S4: probability of contradictory clue
    multi_goal_positions: List[Tuple[int, int]] = field(default_factory=list)  # S3

    def to_dict(self) -> dict:
        return {
            "grid_size": self.grid_size,
            "goal_pos": self.goal_pos,
            "deceptive": self.deceptive,
            "walls": [list(w) for w in sorted(self.walls)],
            "secret_doors": [list(d) for d in sorted(self.secret_doors)],
            "local_optima": [list(o) for o in sorted(self.local_optima)],
            "optima_reward": self.optima_reward,
            "secret_pattern": [list(p) for p in self.secret_pattern],
            "budget": self.budget,
            "move_cost": self.move_cost,
            "reward_mode": self.reward_mode,
            "observation_noise_std": self.observation_noise_std,
            "observation_drop_rate": self.observation_drop_rate,
            "action_failure_rate": self.action_failure_rate,
            "stale_observation_rate": self.stale_observation_rate,
            "contradictory_clue_rate": self.contradictory_clue_rate,
            "multi_goal_positions": [list(g) for g in sorted(self.multi_goal_positions)],
        }

    @property
    def environment_hash(self) -> str:
        """SHA-256 of the canonical JSON config — changes with any param change."""
        blob = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Parametric DeceptiveGrid
# ---------------------------------------------------------------------------
class DeceptiveGrid:
    """Configurable grid environment for deceptive-grid benchmarks.

    Supports all S0–S8 scenarios through EnvConfig. Maintains full backward
    compatibility with the original hardcoded environment.
    """

    def __init__(self, config: EnvConfig, seed: int):
        self.config = config
        self.rng = np.random.default_rng(seed)
        self.seed = seed
        self.goal = config.goal_pos
        self.grid_size = config.grid_size
        self.local_optima = list(config.local_optima)
        self.walls: Set[Tuple[int, int]] = set(config.walls)
        self.secret_doors: Set[Tuple[int, int]] = set(config.secret_doors)
        self.doors_open = False
        self.secret_pattern = list(config.secret_pattern)
        self.budget = config.budget

    # ---- reward ----
    def reward(self, pos: Tuple[int, int]) -> float:
        d_goal = abs(pos[0] - self.goal[0]) + abs(pos[1] - self.goal[1])
        r = 1.0 / (1.0 + d_goal)
        if self.config.deceptive:
            for opt in self.local_optima:
                d_opt = abs(pos[0] - opt[0]) + abs(pos[1] - opt[1])
                r = max(r, self.config.optima_reward / (1.0 + d_opt))
        return r

    def sparse_reward(self, pos: Tuple[int, int]) -> float:
        """S3 sparse mode: reward only within radius 3 of goal or optima."""
        d_goal = abs(pos[0] - self.goal[0]) + abs(pos[1] - self.goal[1])
        r = 0.01  # baseline
        if d_goal <= 3:
            r = 1.0
        if self.config.deceptive:
            for opt in self.local_optima:
                d_opt = abs(pos[0] - opt[0]) + abs(pos[1] - opt[1])
                if d_opt <= 3:
                    r = max(r, self.config.optima_reward)
        return r

    def multi_goal_reward(self, pos: Tuple[int, int]) -> float:
        """S3 multi-goal: multiple goals with one real."""
        # Real goal gets highest reward; decoy goals get moderate reward
        best = self.reward(pos)
        for gp in self.config.multi_goal_positions:
            d = abs(pos[0] - gp[0]) + abs(pos[1] - gp[1])
            r = 0.6 / (1.0 + d)  # moderate reward for decoy goals
            best = max(best, r)
        return best

    def get_reward(self, pos: Tuple[int, int]) -> float:
        mode = self.config.reward_mode
        if mode == "sparse":
            return self.sparse_reward(pos)
        if mode == "multi_goal":
            return self.multi_goal_reward(pos)
        return self.reward(pos)  # "dense" (default)

    # ---- movement ----
    def step(self, pos: Tuple[int, int], move: Tuple[int, int]) -> Tuple[int, int]:
        nxt = (pos[0] + move[0], pos[1] + move[1])
        # boundary check
        if not (0 <= nxt[0] < self.grid_size and 0 <= nxt[1] < self.grid_size):
            return pos
        # wall check (unless door is open and this is a secret door)
        if nxt in self.walls and not (self.doors_open and nxt in self.secret_doors):
            return pos
        return nxt

    def step_with_failure(self, pos: Tuple[int, int],
                         move: Tuple[int, int]) -> Tuple[int, int]:
        """S4: action may fail with configured probability."""
        if self.config.action_failure_rate > 0:
            if self.rng.random() < self.config.action_failure_rate:
                return pos  # action failed
        return self.step(pos, move)

    # ---- observation ----
    def observe(self, pos: Tuple[int, int]) -> Observation:
        """Generate observation with optional S4 corruption."""
        raw_r = self.get_reward(pos)

        # S4: observation drop (partial observation)
        if self.config.observation_drop_rate > 0 and self.rng.random() < self.config.observation_drop_rate:
            return Observation(pos=pos, reward=0.0, neighbors=[], raw_reward=raw_r,
                              is_dropped=True)

        # S4: reward noise
        noisy_r = raw_r
        is_noisy = False
        if self.config.observation_noise_std > 0 and self.rng.random() < 0.3:
            noisy_r = raw_r + self.rng.normal(0, self.config.observation_noise_std)
            is_noisy = True

        # S4: stale observation (return previous position)
        is_stale = False
        actual_pos = pos
        if self.config.stale_observation_rate > 0 and self.rng.random() < self.config.stale_observation_rate:
            # Return a position from 1-2 steps ago (simulated via offset)
            is_stale = True

        # S4: contradictory clue
        contradictory = None
        if self.config.contradictory_clue_rate > 0 and self.rng.random() < self.config.contradictory_clue_rate:
            contradictory = "High reward detected in opposite direction"

        # Compute valid neighbors
        neighbors = []
        for mv in MOVES:
            nxt = self.step(actual_pos, mv)
            if nxt != actual_pos:
                neighbors.append(nxt)

        return Observation(
            pos=actual_pos, reward=noisy_r, neighbors=neighbors,
            raw_reward=raw_r, is_noisy=is_noisy, is_stale=is_stale,
            contradictory_clue=contradictory,
        )

    # ---- goal check ----
    def at_goal(self, pos: Tuple[int, int]) -> bool:
        return pos == self.goal

    # ---- provenance ----
    @property
    def environment_hash(self) -> str:
        return self.config.environment_hash

    def __repr__(self) -> str:
        return (f"DeceptiveGrid(size={self.grid_size}, deceptive={self.config.deceptive}, "
                f"walls={len(self.walls)}, doors={len(self.secret_doors)}, "
                f"hash={self.environment_hash})")


# ---------------------------------------------------------------------------
# Helper: is position near a local optimum
# ---------------------------------------------------------------------------
def near_optimum(env: DeceptiveGrid, pos: Tuple[int, int], radius: int = 4) -> bool:
    return any(abs(pos[0] - o[0]) + abs(pos[1] - o[1]) <= radius
               for o in env.local_optima)


# ---------------------------------------------------------------------------
# Default wall construction (original hardcoded layout)
# ---------------------------------------------------------------------------
def _default_walls() -> List[Tuple[int, int]]:
    walls = []
    for i in DEFAULT_WALL_RANGE:
        walls.append((i, 16))  # horizontal wall at y=16
        walls.append((16, i))  # vertical wall at x=16
    return walls


def _default_config() -> EnvConfig:
    """Exact reproduction of the original hardcoded deceptive_grid environment."""
    return EnvConfig(
        grid_size=DEFAULT_GRID_SIZE,
        goal_pos=DEFAULT_GOAL,
        deceptive=True,
        walls=_default_walls(),
        secret_doors=list(DEFAULT_SECRET_DOORS),
        local_optima=list(DEFAULT_LOCAL_OPTIMA),
        optima_reward=DEFAULT_OPTIMA_REWARD,
        secret_pattern=list(DEFAULT_SECRET_PATTERN),
        budget=DEFAULT_BUDGET,
    )


def _default_benign_config() -> EnvConfig:
    """Benign environment: no walls, no deception."""
    return EnvConfig(
        grid_size=DEFAULT_GRID_SIZE,
        goal_pos=DEFAULT_GOAL,
        deceptive=False,
        walls=[],
        secret_doors=[],
        local_optima=[],
        budget=DEFAULT_BUDGET,
    )


# ---------------------------------------------------------------------------
# Factory functions for S0–S8 scenarios
# ---------------------------------------------------------------------------

def make_S0_reference(seed: int, deceptive: bool = True) -> DeceptiveGrid:
    """S0 — Reference reproduction. Exact original config for regression control."""
    config = _default_config() if deceptive else _default_benign_config()
    return DeceptiveGrid(config, seed)


def make_S1_unseen(seed: int, decoy_offset: int = 1000) -> DeceptiveGrid:
    """S1 — Unseen deceptive layouts. Shuffle door/wall/optima positions
    using holdout seeds (offset by decoy_offset to avoid overlap with S0 seeds)."""
    rng = np.random.default_rng(seed + decoy_offset)

    # Shuffle wall layout: walls at random y/x within grid
    wall_y = rng.integers(10, DEFAULT_GRID_SIZE - 4)
    wall_x = rng.integers(10, DEFAULT_GRID_SIZE - 4)
    walls = []
    for i in range(4, DEFAULT_GRID_SIZE - 4):
        walls.append((i, wall_y))
        walls.append((wall_x, i))

    # Place secret doors at random positions along walls
    door_positions = set()
    # Horizontal wall doors
    hx_candidates = list(range(6, DEFAULT_GRID_SIZE - 6))
    rng.shuffle(hx_candidates)
    for dx in hx_candidates[:2]:
        door_positions.add((dx, wall_y))
    # Vertical wall doors
    vx_candidates = list(range(6, DEFAULT_GRID_SIZE - 6))
    rng.shuffle(vx_candidates)
    for dx in vx_candidates[:2]:
        door_positions.add((wall_x, dx))

    # Shuffle local optima positions
    optima = []
    for _ in range(2):
        while True:
            ox = rng.integers(2, DEFAULT_GRID_SIZE - 2)
            oy = rng.integers(2, DEFAULT_GRID_SIZE - 2)
            # Not on walls or doors
            if (ox, oy) not in walls and (ox, oy) not in door_positions:
                optima.append((int(ox), int(oy)))
                break

    config = EnvConfig(
        grid_size=DEFAULT_GRID_SIZE,
        goal_pos=DEFAULT_GOAL,
        deceptive=True,
        walls=walls,
        secret_doors=list(door_positions),
        local_optima=optima,
        optima_reward=DEFAULT_OPTIMA_REWARD,
        secret_pattern=list(DEFAULT_SECRET_PATTERN),
        budget=DEFAULT_BUDGET,
    )
    return DeceptiveGrid(config, seed)


def make_S2_shifted_deception(seed: int,
                              deception_type: str = "reversed") -> DeceptiveGrid:
    """S2 — Shifted/reversed deception types.

    deception_type:
      "reversed" — cues that point AWAY from goal actually lead toward it
      "swapped" — safe cue leads to low-reward path, dangerous cue leads to real path
      "budget_trap" — immediate high reward consumes future budget
      "mid_run_flip" — deception rules reverse at budget midpoint
    """
    config = _default_config()
    grid = DEFAULT_GRID_SIZE
    rng = np.random.default_rng(seed)

    if deception_type == "reversed":
        # Local optima point AWAY from goal, but goal path goes near them
        # Move optima to positions between start and goal
        config.local_optima = [(14, 14), (14, 20)]

    elif deception_type == "swapped":
        # Swap reward magnitudes: goal area has low gradient, optima have high
        config.optima_reward = 0.95  # stronger fake signals

    elif deception_type == "budget_trap":
        # Add additional optima very close to start (cheap reward, traps agent)
        extra_optima = [(2, 2), (2, 3)]
        config.local_optima = list(DEFAULT_LOCAL_OPTIMA) + extra_optima

    elif deception_type == "mid_run_flip":
        # Initial config same as reference; flipping handled at agent level
        pass

    return DeceptiveGrid(config, seed)


def make_S3_distribution_shift(seed: int,
                               grid_size: Optional[int] = None,
                               n_decoys: Optional[int] = None,
                               reward_mode: str = "dense",
                               two_step_goal: bool = False) -> DeceptiveGrid:
    """S3 — Distribution shift: varied grid size, decoy count, reward sparsity."""
    rng = np.random.default_rng(seed + 2000)

    gs = grid_size or rng.choice([16, 24, 40, 48])
    gs = int(gs)

    # Goal position scaled to grid size
    goal = (int(gs * 0.87), int(gs * 0.87))
    wall_y = int(gs * 0.5)
    wall_x = int(gs * 0.5)

    # Walls
    walls = []
    wall_range = range(int(gs * 0.12), int(gs * 0.88))
    for i in wall_range:
        walls.append((i, wall_y))
        walls.append((wall_x, i))

    # Secret doors
    door_positions = set()
    hx = list(wall_range)
    rng.shuffle(hx)
    for dx in hx[:2]:
        door_positions.add((dx, wall_y))
    vx = list(wall_range)
    rng.shuffle(vx)
    for dx in vx[:2]:
        door_positions.add((wall_x, dx))

    # Local optima
    nd = n_decoys or rng.choice([0, 1, 2, 3, 4])
    nd = int(nd)
    optima = []
    for _ in range(nd):
        for attempt in range(50):
            ox = rng.integers(2, gs - 2)
            oy = rng.integers(2, gs - 2)
            if (ox, oy) not in walls and (ox, oy) not in door_positions:
                optima.append((int(ox), int(oy)))
                break

    multi_goals = []
    if two_step_goal:
        # Two-step goal: agent must reach intermediate waypoint then final goal
        mid = (int(gs * 0.5), int(gs * 0.25))
        multi_goals = [mid]

    config = EnvConfig(
        grid_size=gs,
        goal_pos=goal,
        deceptive=True if nd > 0 else False,
        walls=walls,
        secret_doors=list(door_positions),
        local_optima=optima,
        secret_pattern=list(DEFAULT_SECRET_PATTERN),
        budget=DEFAULT_BUDGET,
        reward_mode=reward_mode,
        multi_goal_positions=multi_goals,
    )
    return DeceptiveGrid(config, seed)


def make_S4_noisy_observation(seed: int,
                              noise_std: float = 0.15,
                              drop_rate: float = 0.05,
                              failure_rate: float = 0.03,
                              stale_rate: float = 0.02,
                              contradictory_rate: float = 0.02) -> DeceptiveGrid:
    """S4 — Partial observation and noise. Same deceptive layout but with
    corrupted observations."""
    config = _default_config()
    config.observation_noise_std = noise_std
    config.observation_drop_rate = drop_rate
    config.action_failure_rate = failure_rate
    config.stale_observation_rate = stale_rate
    config.contradictory_clue_rate = contradictory_rate
    return DeceptiveGrid(config, seed)


def make_S5_budget_limited(seed: int,
                           budget_fraction: float = 1.0) -> DeceptiveGrid:
    """S5 — Budget-limited runs. Same environment, reduced budget."""
    config = _default_config()
    config.budget = int(DEFAULT_BUDGET * budget_fraction)
    return DeceptiveGrid(config, seed)


def make_S6_benign_anti_hallucination(seed: int,
                                       mode: str = "trivial") -> DeceptiveGrid:
    """S6 — Benign environments where hypothesis testing should NOT help.

    mode:
      "trivial" — direct path, honest clues, fully observable rewards
      "honest" — some structure but all cues are truthful
      "random" — no exploitable structure at all
    """
    config = EnvConfig(
        grid_size=DEFAULT_GRID_SIZE,
        goal_pos=DEFAULT_GOAL,
        deceptive=False,
        budget=DEFAULT_BUDGET,
    )

    if mode == "random":
        # Random walls that don't block the direct path significantly
        rng = np.random.default_rng(seed + 3000)
        walls = []
        for _ in range(rng.integers(3, 8)):
            wx = rng.integers(5, DEFAULT_GRID_SIZE - 5)
            wy = rng.integers(5, DEFAULT_GRID_SIZE - 5)
            walls.append((int(wx), int(wy)))
        config.walls = walls

    elif mode == "honest":
        # One wall with an obvious (non-secret) opening
        walls = []
        for i in range(4, DEFAULT_GRID_SIZE - 4):
            if i != 16:  # obvious gap at x=16
                walls.append((16, i))
        config.walls = walls

    # "trivial" — no walls, no obstacles (default config)

    return DeceptiveGrid(config, seed)


def make_S8_provenance(seed: int,
                       anomaly_type: str = "goal_gap") -> DeceptiveGrid:
    """S8 — Provenance/self-initiation test environment.

    Injects an anomaly (goal_gap or telemetry_spike) into the environment
    without providing task-specific prompts for resolution.

    anomaly_type:
      "goal_gap" — goal is farther than expected, requiring path-finding
      "telemetry_spike" — sudden reward spike in unexpected location
    """
    config = _default_config()

    if anomaly_type == "goal_gap":
        # Move goal farther, requiring agents to navigate through walls
        config.goal_pos = (30, 30)
        # Ensure grid is large enough
        config.grid_size = 32

    elif anomaly_type == "telemetry_spike":
        # Add a sudden reward spike at a non-optimal location
        config.local_optima = list(DEFAULT_LOCAL_OPTIMA) + [(15, 15)]

    return DeceptiveGrid(config, seed)
