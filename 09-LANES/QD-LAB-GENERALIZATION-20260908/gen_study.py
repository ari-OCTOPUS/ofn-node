"""OCTOPUS-QD-LAB-GEN-v1 — held-out generalization study for the delivered QD lab.

Preregistration: results_gen/study_gen.json (written and hashed BEFORE any
held-out evaluation; see ledger event 0). Local simulation only, propose-only,
production_authorized=false. Package code is imported, never modified.
"""
import hashlib
import json
import os
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

OUT = HERE / "results_gen"
GRID = 64
N_RANDOM = 256
INIT_SIGMA = 1.2
CLIP = 4.0

PRIMARY = ["full_seed7", "full_seed11", "full_seed23"]
ROBUST_H4 = ["mutation_seed7", "mutation_seed11", "mutation_seed23"]

START = np.array([0.06, 0.06])
START_SHIFTS = [(0.04, 0.06), (0.08, 0.06), (0.06, 0.04), (0.06, 0.08)]
DESC_START = (0.08, 0.08)
MAZE_SEED_POOL = [101, 102, 103, 104, 105, 106, 107, 108]
N_MAZES = 6


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


def free_area_ratio(walls, pillars):
    with maze_ctx(walls, pillars, START):
        return float(env.free_mask(GRID).mean())


def reachable_ratio(walls, pillars):
    with maze_ctx(walls, pillars, START):
        free = env.free_mask(GRID)
        reach = env.reachable_mask(GRID)
    return float(reach.sum() / max(free.sum(), 1))


def starts_free(walls, pillars):
    pts = np.array([START] + [list(s) for s in START_SHIFTS] + [list(DESC_START)])
    with maze_ctx(walls, pillars, START):
        return not bool(env._blocked(pts).any())


def generate_maze(seed):
    """Source-maze grammar, deterministic per seed. Returns (walls, pillars, log)."""
    rng = np.random.default_rng(seed)
    log = {"seed": seed, "candidates": []}
    for attempt in range(1, 201):
        lower_y = float(rng.uniform(0.26, 0.38))
        upper_y = float(rng.uniform(0.58, 0.70))
        th = 0.035
        gap_w = 0.28
        lower_gap_right = bool(rng.integers(0, 2))
        if lower_gap_right:
            lower = [0.0, lower_y, 1.0 - gap_w, lower_y + th]
        else:
            lower = [gap_w, lower_y, 1.0, lower_y + th]
        upper_gap_right = not lower_gap_right
        if upper_gap_right:
            upper = [0.0, upper_y, 1.0 - gap_w, upper_y + th]
        else:
            upper = [gap_w, upper_y, 1.0, upper_y + th]
        blade_x = float(rng.uniform(0.30, 0.62))
        blade = [blade_x, upper_y + th, blade_x + 0.035, 0.86]
        walls = np.array([lower, upper, blade])

        pillars = []
        ok = True
        gap_centers = [
            (1.0 - gap_w / 2 if lower_gap_right else gap_w / 2, lower_y + th / 2),
            (1.0 - gap_w / 2 if upper_gap_right else gap_w / 2, upper_y + th / 2),
        ]
        for _ in range(4):
            placed = False
            for _try in range(200):
                cx, cy = float(rng.uniform(0.08, 0.92)), float(rng.uniform(0.08, 0.92))
                r = float(rng.uniform(0.06, 0.09))
                if np.hypot(cx - START[0], cy - START[1]) < 0.16 + r:
                    continue
                if any(np.hypot(cx - px, cy - py) < r + pr + 0.05 for px, py, pr in pillars):
                    continue
                if any(np.hypot(cx - gx, cy - gy) < r + 0.10 for gx, gy in gap_centers):
                    continue
                if cy > 0.80 and abs(cx - (blade_x + 0.0175)) < r + 0.10:
                    continue
                pillars.append((cx, cy, r))
                placed = True
                break
            if not placed:
                ok = False
                break
        if not ok:
            log["candidates"].append({"attempt": attempt, "rejected": "pillar_placement"})
            continue
        pillars_arr = np.array(pillars)
        checks = {
            "starts_free": starts_free(walls, pillars_arr),
            "free_area_ratio": free_area_ratio(walls, pillars_arr),
            "reachable_ratio": reachable_ratio(walls, pillars_arr),
        }
        if not checks["starts_free"]:
            log["candidates"].append({"attempt": attempt, "rejected": "start_blocked"})
            continue
        if not (0.75 <= checks["free_area_ratio"] / SOURCE_FREE_RATIO <= 1.15):
            log["candidates"].append({"attempt": attempt, "rejected": "free_area_ratio",
                                      "value": checks["free_area_ratio"]})
            continue
        if checks["reachable_ratio"] < 0.55:
            log["candidates"].append({"attempt": attempt, "rejected": "reachable_ratio",
                                      "value": checks["reachable_ratio"]})
            continue
        log["candidates"].append({"attempt": attempt, "accepted": True, **checks})
        return walls, pillars_arr, log
    raise RuntimeError(f"no valid maze for seed {seed}")


SOURCE_WALLS = env.WALLS.copy()
SOURCE_PILLARS = env.PILLARS.copy()
SOURCE_FREE_RATIO = free_area_ratio(SOURCE_WALLS, SOURCE_PILLARS)


def eval_set(genomes, walls, pillars, start):
    with maze_ctx(walls, pillars, start):
        f, bd, info = env.evaluate(genomes)
    if not (np.isfinite(f).all() and np.isfinite(bd).all()):
        raise RuntimeError("NaN/Inf in evaluation -> STOP per megaprompt safety gate")
    return {
        "mean_fitness": float(f.mean()),
        "qd_sum": float(f.sum()),
        "mean_collision_rate": float(info["collision_rate"].mean()),
        "mean_path_len": float(info["path_len"].mean()),
        "mean_displacement": float(info["displacement"].mean()),
        "_f": f, "_bd": bd,
    }


def load_archive(run):
    a = Archive.load(PKG / "results" / run / "archive.npz")
    return a.genomes[a.filled], a.fitness[a.filled], a.bd[a.filled], a.ids[a.filled]


def main():
    OUT.mkdir(exist_ok=True)
    ledger_path = OUT / "receipts_gen.jsonl"
    if ledger_path.exists():
        raise SystemExit("ledger exists; refusing to resume/rewrite — new folder required")

    # ---- held-out mazes (preregistered pool + rules) ----
    mazes, maze_logs = {}, {}
    for s in MAZE_SEED_POOL:
        if len(mazes) == N_MAZES:
            break
        walls, pillars, log = generate_maze(s)
        name = f"m{len(mazes)+1}"
        mazes[name] = {"seed": s, "walls": walls, "pillars": pillars}
        maze_logs[name] = log

    archives = {run: load_archive(run) for run in PRIMARY + ROBUST_H4}
    random_base = {}  # per maze + source
    rng_src = np.random.default_rng(1_000_000)
    random_base["SOURCE"] = np.clip(rng_src.normal(0, INIT_SIGMA, (N_RANDOM, env.GENOME_DIM)), -CLIP, CLIP)
    for name, m in mazes.items():
        rng_m = np.random.default_rng(1_000_000 + m["seed"])
        random_base[name] = np.clip(rng_m.normal(0, INIT_SIGMA, (N_RANDOM, env.GENOME_DIM)), -CLIP, CLIP)

    rows = []
    ledger = ReceiptLedger(str(ledger_path))
    ledger.append("study_preregistered", {
        "study_gen_sha256": hashlib.sha256((OUT / "study_gen.json").read_bytes()).hexdigest(),
        "mazes": {k: {"seed": v["seed"], "walls_sha256": sha(v["walls"]),
                      "pillars_sha256": sha(v["pillars"])} for k, v in mazes.items()},
        "maze_generation_logs": maze_logs,
        "primary_archives": PRIMARY, "robustness_archives_h4": ROBUST_H4,
        "source_free_area_ratio": SOURCE_FREE_RATIO,
    }, 0)

    def record(run, cond, maze_name, start, walls, pillars, res, tag):
        row = {"archive": run, "condition": cond, "maze": maze_name,
               "start": [float(start[0]), float(start[1])], **{k: v for k, v in res.items() if not k.startswith("_")}}
        rows.append(row)
        ledger.append("condition_evaluated", {
            "archive": run, "condition": cond, "maze": maze_name,
            "start": [float(start[0]), float(start[1])], "tag": tag,
            "genomes_sha256": sha(archives[run][0] if tag == "elites"
                                  else random_base["SOURCE" if maze_name == "source" else maze_name]),
            "walls_sha256": sha(walls), "pillars_sha256": sha(pillars),
            "n": int(len(res["_f"])),
            "mean_fitness": row["mean_fitness"], "qd_sum": row["qd_sum"],
            "mean_collision_rate": row["mean_collision_rate"],
            "mean_path_len": row["mean_path_len"],
            "mean_displacement": row["mean_displacement"],
        }, len(rows))

    for run in PRIMARY:
        genomes, f_stored, bd_stored, ids = archives[run]
        src = eval_set(genomes, SOURCE_WALLS, SOURCE_PILLARS, START)
        src_cells = np.minimum((src["_bd"] * GRID).astype(int), GRID - 1)
        record(run, "SOURCE", "source", START, SOURCE_WALLS, SOURCE_PILLARS, src, "elites")
        rrng = np.random.default_rng(1_000_000)
        rb = eval_set(random_base["SOURCE"], SOURCE_WALLS, SOURCE_PILLARS, START)
        record(run, "SOURCE_RANDOM", "source", START, SOURCE_WALLS, SOURCE_PILLARS, rb, "random")
        for name, m in mazes.items():
            res = eval_set(genomes, m["walls"], m["pillars"], START)
            cells = np.minimum((res["_bd"] * GRID).astype(int), GRID - 1)
            res["cell_transfer_fraction"] = float((cells == src_cells).all(axis=1).mean())
            record(run, f"H4-{name}", name, START, m["walls"], m["pillars"], res, "elites")
            rres = eval_set(random_base[name], m["walls"], m["pillars"], START)
            record(run, f"H4-{name}-RANDOM", name, START, m["walls"], m["pillars"], rres, "random")
        for sx, sy in START_SHIFTS:
            res = eval_set(genomes, SOURCE_WALLS, SOURCE_PILLARS, (sx, sy))
            record(run, f"H5-s({sx},{sy})", "source", (sx, sy), SOURCE_WALLS, SOURCE_PILLARS, res, "elites")
        for name, m in mazes.items():
            res = eval_set(genomes, m["walls"], m["pillars"], DESC_START)
            record(run, f"DESC-{name}-comb", name, DESC_START, m["walls"], m["pillars"], res, "elites")

    for run in ROBUST_H4:
        genomes, f_stored, bd_stored, ids = archives[run]
        src = eval_set(genomes, SOURCE_WALLS, SOURCE_PILLARS, START)
        record(run, "SOURCE", "source", START, SOURCE_WALLS, SOURCE_PILLARS, src, "elites")
        for name, m in mazes.items():
            res = eval_set(genomes, m["walls"], m["pillars"], START)
            record(run, f"H4-{name}", name, START, m["walls"], m["pillars"], res, "elites")

    ledger.close()
    integ = {"count": ledger.count, "head": ledger.head}
    r = verify_ledger(str(ledger_path), expected_head=integ["head"], expected_count=integ["count"])
    integ["valid"] = r["valid"]
    (OUT / "integrity_gen.json").write_text(json.dumps(integ, indent=2), encoding="utf-8")

    for row in rows:
        row.pop("_f", None); row.pop("_bd", None)
    (OUT / "rows_gen.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    (OUT / "maze_generation_log.json").write_text(json.dumps(maze_logs, indent=1), encoding="utf-8")
    print("EVALUATION DONE — rows:", len(rows), "| ledger valid:", integ["valid"],
          "| mazes:", {k: v["seed"] for k, v in mazes.items()})


if __name__ == "__main__":
    main()
