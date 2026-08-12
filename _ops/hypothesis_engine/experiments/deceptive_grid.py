# experiments/deceptive_grid.py — شبیه‌سازی آزمایش سه‌ایجنتی
# طبق DECEPTIVE-ENV-3AGENT-EXPERIMENT.md v1.0
# Agent B از HypothesisBrain واقعی (impl/) استفاده می‌کند — dogfooding.
#
# اجرا:  cd _ops/hypothesis_engine/experiments
#        python deceptive_grid.py --runs 100 --out results.csv
from __future__ import annotations

import argparse
import asyncio
import csv
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "impl"))
from hypothesis_brain import HypothesisBrain  # noqa: E402

GRID = 32
BUDGET = 10_000
HYP_BUDGET_SHARE = 0.30          # سقف ۳۰٪ گام‌ها برای آزمون فرضیه (ضد شکار روح)
HYP_INTERVAL = 500               # هر ۵۰۰ گام یک چرخهٔ فرضیه
MAX_ACTIVE_HYP = 3
KILL_AFTER_FAILS = 3             # ۳ پیش‌بینی غلط متوالی → FALSIFIED


# ---------------------------------------------------------------------------
# محیط: Deceptive Grid با ساختار پنهان
# ---------------------------------------------------------------------------
class DeceptiveGrid:
    """شبکهٔ ۳۲×۳۲. reward فریبنده: gradient به دو بن‌بست محلی می‌رسد.
    راهروهای پنهان با الگوی حرکتی (2E,1N)×3 باز می‌شوند — در نسخهٔ deceptive
    عبور از دیوارها را ممکن می‌کنند."""

    def __init__(self, deceptive: bool, seed: int):
        self.deceptive = deceptive
        self.rng = np.random.default_rng(seed)
        self.goal = (28, 28)
        self.local_optima = [(26, 6), (6, 26)] if deceptive else []
        # دیوارها: دو دیوار بزرگ که مسیر مستقیم را می‌بندند
        self.walls = set()
        if deceptive:
            for i in range(4, 28):
                self.walls.add((i, 16))       # دیوار افقی
                self.walls.add((16, i))       # دیوار عمودی
        # راهروهای پنهان: سلول‌هایی از دیوار که با الگوی حرکتی باز می‌شوند
        # در افقی در (9,16): الگوی (2E,1N)x3 از ردیف 14/15 → (9,16) ✓
        # در عمودی در (16,21): الگوی (2N,1E)x3 از ستون 14/15 → (16,21) ✓
        self.secret_doors = {(9, 16), (22, 16), (16, 8), (16, 21)} if deceptive else set()
        self.doors_open = False

    def reward(self, pos: Tuple[int, int]) -> float:
        d_goal = abs(pos[0] - self.goal[0]) + abs(pos[1] - self.goal[1])
        r = 1.0 / (1.0 + d_goal)
        # فریب: نزدیکی به بن‌بست‌های محلی reward بالای جعلی می‌دهد
        for opt in self.local_optima:
            d_opt = abs(pos[0] - opt[0]) + abs(pos[1] - opt[1])
            r = max(r, 0.85 / (1.0 + d_opt))
        return r

    def step(self, pos: Tuple[int, int], move: Tuple[int, int]) -> Tuple[int, int]:
        nxt = (pos[0] + move[0], pos[1] + move[1])
        if not (0 <= nxt[0] < GRID and 0 <= nxt[1] < GRID):
            return pos
        if nxt in self.walls and not (self.doors_open and nxt in self.secret_doors):
            return pos
        return nxt


MOVES = [(0, 1), (0, -1), (1, 0), (-1, 0)]   # E, W, S, N
SECRET_PATTERN = [(0, 1), (0, 1), (-1, 0)] * 3   # (2E,1N)×3


# ---------------------------------------------------------------------------
# نتیجهٔ run
# ---------------------------------------------------------------------------
@dataclass
class RunResult:
    agent: str
    env: str
    seed: int
    ttd: Optional[int] = None          # time-to-discovery (None = ناموفق)
    wasted_steps: int = 0              # گام‌های داخل halo بن‌بست‌ها
    falsified_assists: int = 0         # گام‌های آزمونِ فرضیه‌هایی که بعداً FALSIFIED شدند
    hyp_steps: int = 0
    discovered: bool = False


def near_optimum(env: DeceptiveGrid, pos, radius: int = 4) -> bool:
    return any(abs(pos[0] - o[0]) + abs(pos[1] - o[1]) <= radius
               for o in env.local_optima)


# ---------------------------------------------------------------------------
# Agent A — Prior-Only: greedy روی reward + تبرید تصادفی کوچک
# ---------------------------------------------------------------------------
def run_prior_only(env: DeceptiveGrid, seed: int) -> RunResult:
    rng = np.random.default_rng(seed)
    pos = (0, 0)
    res = RunResult(agent="A_prior", env="deceptive" if env.deceptive else "benign",
                    seed=seed)
    for t in range(BUDGET):
        if pos == env.goal:
            res.ttd, res.discovered = t, True
            break
        if near_optimum(env, pos):
            res.wasted_steps += 1
        # greedy: بهترین همسایه بر اساس reward؛ گاهی نویز
        if rng.random() < 0.05:
            mv = MOVES[rng.integers(4)]
        else:
            best, best_r = MOVES[0], -1.0
            for mv_c in MOVES:
                nxt = env.step(pos, mv_c)
                r = env.reward(nxt) + rng.normal(0, 0.01)
                if r > best_r:
                    best, best_r = mv_c, r
            mv = best
        pos = env.step(pos, mv)
    return res


# ---------------------------------------------------------------------------
# Agent C — Random Novelty: ε-greedy + پاداش نوآوری
# ---------------------------------------------------------------------------
def run_novelty(env: DeceptiveGrid, seed: int) -> RunResult:
    rng = np.random.default_rng(seed)
    pos = (0, 0)
    visits: Dict[Tuple[int, int], int] = {}
    res = RunResult(agent="C_novel", env="deceptive" if env.deceptive else "benign",
                    seed=seed)
    for t in range(BUDGET):
        if pos == env.goal:
            res.ttd, res.discovered = t, True
            break
        if near_optimum(env, pos):
            res.wasted_steps += 1
        visits[pos] = visits.get(pos, 0) + 1
        if rng.random() < 0.3:
            mv = MOVES[rng.integers(4)]
        else:
            # کمترین دفعات بازدید بین همسایه‌ها
            best, best_n = MOVES[0], math.inf
            for mv_c in MOVES:
                nxt = (pos[0] + mv_c[0], pos[1] + mv_c[1])
                n = visits.get(nxt, 0) + rng.normal(0, 0.1)
                if n < best_n:
                    best, best_n = mv_c, n
            mv = best
        pos = env.step(pos, mv)
    return res


# ---------------------------------------------------------------------------
# Agent B — Hypothesis Engine (dogfood از HypothesisBrain واقعی)
# ---------------------------------------------------------------------------
class AgentB:
    """ایجنت فرضیه‌محور. سازوکار کلیدی — campaign:
    فرضیهٔ راهرو (p_e پایین، usefulness بالا) → هدایت به دیوار → sweep سیستماتیک
    + الگوی آیینی. کشف از مسیر باورِ احتمالاً‌غلطِ آزمون‌پذیر می‌گذرد."""

    def __init__(self, env: DeceptiveGrid, seed: int):
        self.env = env
        self.rng = np.random.default_rng(seed)
        self.brain = HypothesisBrain()
        self.hyps: List[dict] = []
        self.pos = (0, 0)
        self.res = RunResult(agent="B_hyp",
                             env="deceptive" if env.deceptive else "benign",
                             seed=seed)
        self._pattern_buf: List[Tuple[int, int]] = []
        self._best_r = -1.0
        self._stall = 0
        self._campaign: Optional[dict] = None
        self._wall_list = list(env.walls)

    # --- فرضیه‌ها (dogfood از HypothesisBrain واقعی) ---
    def _mk_hyp(self, statement, p_e, u, test, eig, pattern, is_decoy=False):
        out = asyncio.run(self.brain.execute({
            "op": "propose", "statement": statement,
            "p_existence": p_e, "p_usefulness": u, "testability": test,
            "eig": eig, "cost_hours": 0.5, "value_if_true": 2.0,
            "test_plan": "اجرای الگو و سنجش نتیجه",
            "kill_condition": "۳ اجرای کامل الگو بدون نتیجه",
        }))
        return {"record": out["proposal"]["record"], "verdict": out["verdict"],
                "fails": 0, "tested_steps": 0, "falsified": False,
                "pattern": pattern, "is_decoy": is_decoy}

    def _nearest_wall(self, pos):
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
        """پایان یک اجرای کامل الگو → ارزیابی پیش‌بینی + به‌روزرسانی باور."""
        hyp["fails"] = 0 if success else hyp["fails"] + 1
        asyncio.run(self.brain.execute({
            "op": "update", "hypothesis": hyp["record"],
            "grade": "C", "direction": "support" if success else "contradict",
            "evidence_id": f"sim-run-{hyp['tested_steps']}",
        }))
        if hyp["fails"] >= KILL_AFTER_FAILS and not hyp["falsified"]:
            hyp["falsified"] = True

    # --- campaign: sweep سیستماتیک کنار یک دیوار مشخص (commit به دیوار) ---
    def _campaign_step(self, corridor):
        c = self._campaign
        w = c.get("wall")
        if w is None:
            w = self._nearest_wall(self.pos)
            c["wall"] = w
            c["horizontal"] = (w[1] == 16)   # خط دیوار: افقی y=16 / عمودی x=16
        if self._wall_dist(self.pos) > 1:
            # ناوبری یقینی به دیوارِ منتخب
            dx = (w[0] > self.pos[0]) - (w[0] < self.pos[0])
            dy = (w[1] > self.pos[1]) - (w[1] < self.pos[1])
            # حرکت در امتداد دیوار و عمود بر آن به‌ترتیب
            moves = [(dx, 0), (0, dy)] if c["horizontal"] else [(0, dy), (dx, 0)]
            nxt = self.pos
            for mv in moves + [(mv[1], mv[0]) for mv in moves]:
                if mv != (0, 0):
                    cand = self.env.step(nxt, mv)
                    if cand != nxt:
                        nxt = cand
                        break
            return nxt
        # کنار دیوار: sweep — گام در امتداد + گام آیینی
        c["steps"] += 1
        corridor["tested_steps"] += 1
        self.res.hyp_steps += 1
        if c["steps"] % 2 == 1:
            mv = (c["dir"], 0) if c["horizontal"] else (0, c["dir"])
            nxt = self.env.step(self.pos, mv)
            # انتهای سگمنت = مسدودشدن یا تمام‌شدن خط دیوار در کنار مسیر
            adjacent_wall = (16, nxt[1]) if not c["horizontal"] else (nxt[0], 16)
            if nxt == self.pos or adjacent_wall not in self.env.walls:
                c["dir"] *= -1                          # انتهای سگمنت
                c["reversals"] += 1
                mv = (c["dir"], 0) if c["horizontal"] else (0, c["dir"])
                nxt = self.env.step(self.pos, mv)
            return nxt
        # گام زوج: گام آیینی
        mv = self._pattern_move(corridor)
        if not self._pattern_buf:                       # اجرای کامل الگو
            in_halo = any(abs(self.pos[0]-d[0])+abs(self.pos[1]-d[1]) <= 2
                          for d in self.env.secret_doors)
            self._finish_pattern(corridor, success=in_halo or self.env.doors_open)
        nxt = self.env.step(self.pos, mv)
        if nxt == self.pos:                             # الگو به دیوار خورد → جایگزین
            nxt = self.env.step(self.pos, (0, -1))
        return nxt

    def run(self) -> RunResult:
        for t in range(BUDGET):
            if self.pos == self.env.goal:
                self.res.ttd, self.res.discovered = t, True
                break
            if near_optimum(self.env, self.pos):
                self.res.wasted_steps += 1

            # تشخیص بن‌بست
            r_now = self.env.reward(self.pos)
            if r_now > self._best_r + 1e-4:
                self._best_r, self._stall = r_now, 0
            else:
                self._stall += 1

            # فرضیه‌سازی در آغاز
            if t == 0:
                self.hyps.append(self._mk_hyp(
                    "الگوی (2E,1N)x3 راهروی پنهان در دیوار باز می‌کند",
                    0.2, 0.85, 0.9, 0.7, SECRET_PATTERN))
                self.hyps.append(self._mk_hyp(
                    "الگوی (2S,1E)x3 مسیر مخفی به سمت هدف باز می‌کند",
                    0.18, 0.7, 0.85, 0.55, [(1, 0), (1, 0), (0, 1)] * 3,
                    is_decoy=True))

            corridor = next((h for h in self.hyps if not h["is_decoy"]), None)
            decoy = next((h for h in self.hyps if h["is_decoy"]), None)

            # شروع campaign: بن‌بست یا چرخهٔ دوره‌ای، فقط در محیط دارای دیوار
            if (self._campaign is None and self.env.deceptive
                    and not self.env.doors_open
                    and corridor and not corridor["falsified"]
                    and corridor["verdict"] == "pursue"
                    and (self._stall >= 150 or t % HYP_INTERVAL == 0)):
                self._campaign = {"steps": 0, "reversals": 0, "dir": -1, "wall": None}
                self._stall = 0

            if (self._campaign is not None and not self.env.doors_open
                    and corridor and not corridor["falsified"]):
                self.pos = self._campaign_step(corridor)
                c = self._campaign
                # باز شدن در: داخل halo + حداقل ۶ گام آزمون
                if not self.env.doors_open and c["steps"] >= 6:
                    if any(abs(self.pos[0]-d[0])+abs(self.pos[1]-d[1]) <= 2
                           for d in self.env.secret_doors):
                        self.env.doors_open = True
                if self.env.doors_open or c["reversals"] >= 2 or c["steps"] > 900:
                    if c["reversals"] >= 2 and not self.env.doors_open:
                        corridor["falsified"] = True
                    self._campaign = None
            elif (decoy and not decoy["falsified"] and decoy["verdict"] == "pursue"
                    and self.rng.random() < 0.25):
                # آزمون decoy در هر مکان
                mv = self._pattern_move(decoy)
                old_r = self.env.reward(self.pos)
                self.pos = self.env.step(self.pos, mv)
                decoy["tested_steps"] += 1
                self.res.hyp_steps += 1
                if not self._pattern_buf:
                    self._finish_pattern(decoy, success=self.env.doors_open)
            elif self.env.doors_open:
                # فرضیه تأیید شد → بهره‌برداری عمدی از راهروی بازشده
                # مسیر: waypoint راهرو (دور از تقاطع دیوارها) → عبور → greedy
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
                            r = self.env.reward(nxt) + self.rng.normal(0, 0.03)
                            if r > best_r:
                                best, best_r = mv_c, r
                        mv = best
                    self.pos = self.env.step(self.pos, mv)
                else:
                    door = min(self.env.secret_doors,
                               key=lambda d: abs(self.pos[0]-d[0]) + abs(self.pos[1]-d[1]))
                    # waypoint: سلول راهروی آزاد کنار در (نه خود سلول دیواری)
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
                # exploitation: greedy با نویز خفیف
                if self.rng.random() < 0.08:
                    mv = MOVES[self.rng.integers(4)]
                else:
                    best, best_r = MOVES[0], -1.0
                    for mv_c in MOVES:
                        nxt = self.env.step(self.pos, mv_c)
                        r = self.env.reward(nxt) + self.rng.normal(0, 0.05)
                        if r > best_r:
                            best, best_r = mv_c, r
                    mv = best
                self.pos = self.env.step(self.pos, mv)
        # حسابداری P3: کشفی که مسیرش از فرضیهٔ ابطال‌شده گذشته
        if self.res.discovered:
            self.res.falsified_assists = sum(
                h["tested_steps"] for h in self.hyps if h["falsified"])
        return self.res


# ---------------------------------------------------------------------------
# اجرای کامل
# ---------------------------------------------------------------------------
def run_all(n_runs: int, out_path: Path):
    rows: List[RunResult] = []
    for env_name in ("deceptive", "benign"):
        dec = env_name == "deceptive"
        for seed in range(n_runs):
            env = DeceptiveGrid(dec, seed)
            rows.append(run_prior_only(env, seed))
            env = DeceptiveGrid(dec, seed)
            rows.append(run_novelty(env, seed))
            env = DeceptiveGrid(dec, seed)
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
