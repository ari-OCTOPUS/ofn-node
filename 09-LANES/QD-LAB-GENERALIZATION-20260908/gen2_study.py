"""OCTOPUS-QD-LAB-GEN-v2 — out-of-family transfer (H6) + fault injection (H7).

Preregistration: results_gen2/study_gen2.json hashed into ledger event 0 BEFORE
any evaluation. Package files are imported, never modified: mazes and faults are
injected by swapping module constants inside context managers, restored after.
"""
import hashlib
import json
import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PKG = HERE / "package" / "octopus_qd_lab"
sys.path.insert(0, str(PKG))

import environment as env  # noqa: E402
from map_elites import Archive  # noqa: E402
from octopus_bridge import ReceiptLedger, verify_ledger  # noqa: E402

OUT = HERE / "results_gen2"
GRID = 64
N_RANDOM = 256

PRIMARY = ["full_seed7", "full_seed11", "full_seed23"]
ROBUST = ["mutation_seed7", "mutation_seed11", "mutation_seed23"]
START = np.array([0.06, 0.06])
START_SHIFTS = [(0.04, 0.06), (0.08, 0.06), (0.06, 0.04), (0.06, 0.08)]

FAMILY_POOL = [201, 202, 203, 204, 205, 206, 207, 208]
PER_FAMILY = 2
SOURCE_FREE_RATIO = 0.8743  # from GEN-v1 ledger event 0 (same package maze)

FAULTS = [
    {"id": "N05", "sigma": 0.05, "speed": 1.0},
    {"id": "N10", "sigma": 0.10, "speed": 1.0},
    {"id": "N20", "sigma": 0.20, "speed": 1.0},
    {"id": "S75", "sigma": 0.0, "speed": 0.75},
    {"id": "S50", "sigma": 0.0, "speed": 0.50},
]


def sha(arr):
    return hashlib.sha256(np.ascontiguousarray(arr, dtype="<f8").tobytes()).hexdigest()


@contextmanager
def maze_ctx(walls, pillars, start):
    saved = (env.WALLS, env.PILLARS, env.START)
    env.WALLS = np.asarray(walls, dtype=np.float64)
    env.PILLARS = np.asarray(pillars, dtype=np.float64)
    env.START = np.asarray(start, dtype=np.float64)
    try:
        yield
    finally:
        env.WALLS, env.PILLARS, env.START = saved


@contextmanager
def fault_ctx(sigma, speed_factor, seed):
    """Temporary, harness-local injection. Package code on disk never changes."""
    orig_raycast, orig_vmax = env._raycast, env.V_MAX
    rng = np.random.default_rng(seed)

    def noisy_raycast(pos, theta):
        t = orig_raycast(pos, theta)
        if sigma > 0:
            t = np.clip(t + rng.normal(0.0, sigma, t.shape), 0.0, 1.0)
        return t

    env._raycast = noisy_raycast
    env.V_MAX = orig_vmax * speed_factor
    try:
        yield
    finally:
        env._raycast = orig_raycast
        env.V_MAX = orig_vmax


def starts_free(walls, pillars):
    pts = np.array([START] + [list(s) for s in START_SHIFTS])
    with maze_ctx(walls, pillars, START):
        return not bool(env._blocked(pts).any())


def checks(walls, pillars):
    with maze_ctx(walls, pillars, START):
        free = env.free_mask(GRID)
        reach = env.reachable_mask(GRID)
        ratio = float(free.mean())
        reach_ratio = float(reach.sum() / max(free.sum(), 1))
    return ratio, reach_ratio


def place_pillars(rng, n, r_lo, r_hi, min_start, min_sep, extra_keepout=()):
    pillars = []
    for _ in range(n):
        for _try in range(300):
            cx, cy = float(rng.uniform(0.10, 0.90)), float(rng.uniform(0.10, 0.90))
            r = float(rng.uniform(r_lo, r_hi))
            if np.hypot(cx - START[0], cy - START[1]) < min_start + r:
                continue
            if any(np.hypot(cx - px, cy - py) < r + pr + min_sep for px, py, pr in pillars):
                continue
            if any(np.hypot(cx - kx, cy - ky) < r + 0.08 for kx, ky in extra_keepout):
                continue
            pillars.append((cx, cy, r))
            break
        else:
            return None
    return np.array(pillars)


def gen_family(seed, family):
    rng = np.random.default_rng(seed)
    if family == "A":
        pillars = place_pillars(rng, 7, 0.07, 0.10, 0.18, 0.06)
        return np.zeros((0, 4)), pillars
    if family == "C":
        pillars = place_pillars(rng, 12, 0.035, 0.055, 0.16, 0.04)
        return np.zeros((0, 4)), pillars
    if family == "B":
        walls = []
        for i, xlo in enumerate((rng.uniform(0.24, 0.34), rng.uniform(0.50, 0.62), rng.uniform(0.76, 0.86))):
            gap_lo = rng.uniform(0.12, 0.35) if i % 2 == 0 else rng.uniform(0.55, 0.80)
            walls.append([xlo, 0.0, xlo + 0.035, gap_lo])
            walls.append([xlo, gap_lo + 0.28, xlo + 0.035, 1.0])
        walls = np.array(walls)
        pillars = place_pillars(rng, 2, 0.06, 0.09, 0.18, 0.06)
        return walls, pillars
    raise ValueError(family)


def build_mazes():
    mazes, logs = {}, {}
    for family in ("A", "B", "C"):
        got = 0
        flog = []
        for seed in FAMILY_POOL:
            if got == PER_FAMILY:
                break
            walls, pillars = gen_family(seed, family)
            reason = None
            if pillars is None:
                reason = "pillar_placement"
            elif not starts_free(walls, pillars):
                reason = "start_blocked"
            else:
                ratio, reach_ratio = checks(walls, pillars)
                if not (0.75 <= ratio / SOURCE_FREE_RATIO <= 1.15):
                    reason = f"free_area_ratio={ratio:.4f}"
                elif reach_ratio < 0.55:
                    reason = f"reachable_ratio={reach_ratio:.4f}"
            if reason:
                flog.append({"seed": seed, "rejected": reason})
                continue
            ratio, reach_ratio = checks(walls, pillars)
            name = f"{family}{got+1}"
            mazes[name] = {"seed": seed, "family": family, "walls": walls, "pillars": pillars}
            flog.append({"seed": seed, "accepted": name,
                         "free_area_ratio": ratio, "reachable_ratio": reach_ratio})
            got += 1
        if got < PER_FAMILY:
            raise RuntimeError(f"family {family}: only {got} valid mazes")
        logs[family] = flog
    return mazes, logs


SOURCE_WALLS = env.WALLS.copy()
SOURCE_PILLARS = env.PILLARS.copy()


def eval_set(genomes, walls, pillars, start, fault=None):
    fault = fault or {"sigma": 0.0, "speed": 1.0, "seed": 0}
    with maze_ctx(walls, pillars, start), fault_ctx(fault["sigma"], fault["speed"], fault["seed"]):
        f, bd, info = env.evaluate(genomes)
    if not (np.isfinite(f).all() and np.isfinite(bd).all()):
        raise RuntimeError("NaN/Inf -> STOP per safety gate")
    return {
        "mean_fitness": float(f.mean()),
        "mean_collision_rate": float(info["collision_rate"].mean()),
        "mean_path_len": float(info["path_len"].mean()),
        "mean_displacement": float(info["displacement"].mean()),
    }


def load_archive(run):
    a = Archive.load(PKG / "results" / run / "archive.npz")
    return a.genomes[a.filled]


def main():
    if (OUT / "receipts_gen2.jsonl").exists():
        raise SystemExit("ledger exists; refusing to resume/rewrite")
    mazes, maze_logs = build_mazes()
    archives = {run: load_archive(run) for run in PRIMARY + ROBUST}
    random_base = {}
    for name, m in mazes.items():
        rng = np.random.default_rng(2_000_000 + m["seed"])
        random_base[name] = np.clip(rng.normal(0, 1.2, (N_RANDOM, env.GENOME_DIM)), -4, 4)

    rows = []
    ledger = ReceiptLedger(str(OUT / "receipts_gen2.jsonl"))
    ledger.append("study_preregistered", {
        "study_gen2_sha256": hashlib.sha256((OUT / "study_gen2.json").read_bytes()).hexdigest(),
        "mazes": {k: {"seed": v["seed"], "family": v["family"],
                      "walls_sha256": sha(v["walls"]), "pillars_sha256": sha(v["pillars"])}
                  for k, v in mazes.items()},
        "maze_generation_logs": maze_logs,
        "fault_conditions": FAULTS,
        "source_free_area_ratio": SOURCE_FREE_RATIO,
    }, 0)

    def record(run, cond, maze_name, res, genomes_used, walls, pillars):
        rows.append({"archive": run, "condition": cond, "maze": maze_name, **res})
        ledger.append("condition_evaluated", {
            "archive": run, "condition": cond, "maze": maze_name,
            "genomes_sha256": sha(genomes_used),
            "walls_sha256": sha(walls), "pillars_sha256": sha(pillars),
            "n": int(len(genomes_used)),
            "mean_fitness": res["mean_fitness"],
            "mean_collision_rate": res["mean_collision_rate"],
            "mean_path_len": res["mean_path_len"],
            "mean_displacement": res["mean_displacement"],
        }, len(rows))

    for run in PRIMARY:
        g = archives[run]
        clean = eval_set(g, SOURCE_WALLS, SOURCE_PILLARS, START)
        record(run, "CLEAN", "source", clean, g, SOURCE_WALLS, SOURCE_PILLARS)
        for name, m in mazes.items():
            res = eval_set(g, m["walls"], m["pillars"], START)
            record(run, f"H6-{name}", name, res, g, m["walls"], m["pillars"])
            rnd = eval_set(random_base[name], m["walls"], m["pillars"], START)
            record(run, f"H6-{name}-RANDOM", name, rnd, random_base[name], m["walls"], m["pillars"])
        for i, ft in enumerate(FAULTS):
            res = eval_set(g, SOURCE_WALLS, SOURCE_PILLARS, START,
                           fault={"sigma": ft["sigma"], "speed": ft["speed"], "seed": 777_000 + i})
            record(run, f"H7-{ft['id']}", "source", res, g, SOURCE_WALLS, SOURCE_PILLARS)

    for run in ROBUST:
        g = archives[run]
        clean = eval_set(g, SOURCE_WALLS, SOURCE_PILLARS, START)
        record(run, "CLEAN", "source", clean, g, SOURCE_WALLS, SOURCE_PILLARS)
        for name, m in mazes.items():
            res = eval_set(g, m["walls"], m["pillars"], START)
            record(run, f"H6-{name}", name, res, g, m["walls"], m["pillars"])

    ledger.close()
    integ = {"count": ledger.count, "head": ledger.head}
    r = verify_ledger(str(OUT / "receipts_gen2.jsonl"), expected_head=integ["head"], expected_count=integ["count"])
    integ["valid"] = r["valid"]
    (OUT / "integrity_gen2.json").write_text(json.dumps(integ, indent=2), encoding="utf-8")
    (OUT / "rows_gen2.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print("GEN-v2 DONE — rows:", len(rows), "| ledger valid:", integ["valid"],
          "| mazes:", {k: (v["family"], v["seed"]) for k, v in mazes.items()})


if __name__ == "__main__":
    main()
