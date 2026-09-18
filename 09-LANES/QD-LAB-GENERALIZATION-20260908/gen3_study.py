"""OCTOPUS-QD-LAB-GEN-v3 — controlled archive-consumption intervention (H8).

Arms T (transfer-seed) / R (random-seed) / F (frozen parents) on maze B1.
Preregistration: results_gen3/study_gen3.json hashed into ledger event 0 BEFORE
any run. Package files imported, never modified. Local simulation, propose-only.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PKG = HERE / "package" / "octopus_qd_lab"
sys.path.insert(0, str(PKG))
sys.path.insert(0, str(HERE))

import environment as env  # noqa: E402
import map_elites as me  # noqa: E402
from gen2_study import build_mazes, maze_ctx  # noqa: E402
from octopus_bridge import ReceiptLedger, verify_ledger  # noqa: E402

OUT = HERE / "results_gen3"
SEEDS = [7, 11, 23]
ARMS = ["T", "R", "F"]
CONFIG = me.Config(generations=150)  # package defaults otherwise (batch 96, initial 256, grid 64)
CHECKPOINTS = (50, 150)


def sha_bytes(arr):
    return hashlib.sha256(np.ascontiguousarray(arr, dtype="<f8").tobytes()).hexdigest()


def prechecks():
    sums = {}
    for line in (PKG / "SHA256SUMS.txt").read_text().splitlines():
        h, name = line.split(None, 1)
        sums[name.strip()] = h
    bad = [n for n, h in sums.items() if hashlib.sha256((PKG / n).read_bytes()).hexdigest() != h]
    assert not bad, f"package files changed: {bad}"
    for res, tag in (("results_gen", "gen"), ("results_gen2", "gen2")):
        integ = json.load(open(HERE / res / f"integrity_{tag}.json", encoding="utf-8"))
        r = verify_ledger(str(HERE / res / f"receipts_{tag}.jsonl"),
                          expected_head=integ["head"], expected_count=integ["count"])
        assert r["valid"], f"prior ledger {tag} broken"
    mazes, _ = build_mazes()
    b1 = mazes["B1"]
    ev0 = json.loads((HERE / "results_gen2" / "receipts_gen2.jsonl")
                     .read_text(encoding="utf-8").splitlines()[0])
    ref = ev0["payload"]["mazes"]["B1"]
    assert sha_bytes(b1["walls"]) == ref["walls_sha256"], "B1 walls mismatch"
    assert sha_bytes(b1["pillars"]) == ref["pillars_sha256"], "B1 pillars mismatch"
    return b1


def load_frozen(seed):
    a = me.Archive.load(PKG / "results" / f"full_seed{seed}" / "archive.npz")
    m = a.filled
    return a.genomes[m], a.ids[m]


def mutate_from(pool_genomes, pool_ids, rng, config):
    """Replicates map_elites.variation(mode='mutation') rng call order exactly:
    two integers draws + one choice draw + gaussian_mutation(p1, .27, .5)."""
    first = rng.integers(0, len(pool_ids), config.batch)
    second = rng.integers(0, len(pool_ids), config.batch)
    p1 = pool_genomes[first]
    parents = np.stack((pool_ids[first], pool_ids[second]), axis=1)
    ops = rng.choice(["line", "xover", "mut"], size=config.batch, p=[0, 0, 1])
    kids = np.empty_like(p1)
    for k in range(config.batch):
        kids[k] = me.gaussian_mutation(p1[k], rng, config.sigma_mut * 1.5, .5)
        parents[k, 1] = -1
    return np.clip(kids, -config.clip, config.clip), parents, ops


def run_arm(arm, seed, maze, ledger, rows, counter):
    rng = np.random.default_rng(seed)
    frozen_g, frozen_ids = load_frozen(seed)
    config = CONFIG
    with maze_ctx(maze["walls"], maze["pillars"], env.START):
        archive = me.Archive(config.grid)
        evaluations = 0
        for gen in range(config.generations + 1):
            count = config.initial if gen == 0 else config.batch
            if gen == 0:
                if arm == "T":
                    idx = rng.choice(len(frozen_g), count, replace=False)
                    kids = frozen_g[idx]
                    parents = np.stack((frozen_ids[idx], np.full(count, -1, dtype=np.int64)), axis=1)
                    ops = np.full(count, "migrant")
                else:  # R and F share the identical gen-0 draw
                    kids = np.clip(rng.normal(0, config.init_sigma, (count, env.GENOME_DIM)),
                                   -config.clip, config.clip)
                    parents = np.full((count, 2), -1, dtype=np.int64)
                    ops = np.full(count, "random")
            elif arm == "F":
                kids, parents, ops = mutate_from(frozen_g, frozen_ids, rng, config)
            else:  # T and R: parents from the local growing archive
                lg, _, _ = archive.elites()
                lids = archive.ids[archive.filled]
                kids, parents, ops = mutate_from(lg, lids, rng, config)

            ids = np.arange(evaluations, evaluations + count)
            fitness, bd, info = env.evaluate(kids)
            if not (np.isfinite(fitness).all() and np.isfinite(bd).all()):
                raise RuntimeError(f"NaN/Inf in {arm} seed {seed} gen {gen} -> STOP")
            admitted, new, survives = archive.add_batch(
                kids, fitness, bd, gen, ids, parents, ops, info)
            evaluations += count

            filled = archive.filled
            row = {
                "arm": arm, "seed": seed, "gen": gen, "evals": evaluations,
                "coverage": float(filled.sum() / config.grid ** 2),
                "qd_score": float(archive.fitness[filled].sum()),
                "n_elites": int(filled.sum()),
                "admitted": int(admitted.sum()), "new_cells": int(new.sum()),
                "surviving": int(survives.sum()),
            }
            if arm == "T" and gen > 0:
                p0 = parents[:, 0]
                row["migrant_parent_count"] = int((p0[p0 >= 0] < config.initial).sum())
                row["migrant_parent_share"] = row["migrant_parent_count"] / config.batch
            rows.append(row)
            counter[0] += 1
            ledger.append("generation_evaluated", {
                "arm": arm, "seed": seed, "gen": gen, "evals": evaluations,
                "coverage": row["coverage"], "qd_score": row["qd_score"],
                "n_elites": row["n_elites"], "admitted": row["admitted"],
                "new_cells": row["new_cells"], "surviving": row["surviving"],
                "migrant_parent_count": row.get("migrant_parent_count"),
                "candidate_weights_sha256": sha_bytes(kids),
                "selected_parent_ids": np.unique(parents[parents >= 0]).tolist(),
            }, counter[0])
            if gen % 25 == 0 or gen == config.generations:
                print(f"{arm} seed={seed} gen={gen} cov={row['coverage']:.3f} "
                      f"QD={row['qd_score']:.1f}", flush=True)


def main():
    if (OUT / "receipts_gen3.jsonl").exists():
        raise SystemExit("ledger exists; refusing to resume/rewrite")
    b1 = prechecks()
    rows = []
    counter = [0]
    ledger = ReceiptLedger(str(OUT / "receipts_gen3.jsonl"))
    ledger.append("study_preregistered", {
        "study_gen3_sha256": hashlib.sha256((OUT / "study_gen3.json").read_bytes()).hexdigest(),
        "maze": "B1", "walls_sha256": sha_bytes(b1["walls"]),
        "pillars_sha256": sha_bytes(b1["pillars"]),
        "arms": ["T_transfer_seed", "R_random_seed", "F_frozen_parents"],
        "seeds": SEEDS, "config": {"generations": CONFIG.generations, "batch": CONFIG.batch,
                                   "initial": CONFIG.initial, "grid": CONFIG.grid},
        "variation_mode": "mutation-only, rng call order replicated from map_elites.variation",
    }, 0)
    for seed in SEEDS:
        for arm in ARMS:
            run_arm(arm, seed, b1, ledger, rows, counter)
    ledger.close()
    integ = {"count": ledger.count, "head": ledger.head}
    r = verify_ledger(str(OUT / "receipts_gen3.jsonl"),
                      expected_head=integ["head"], expected_count=integ["count"])
    integ["valid"] = r["valid"]
    (OUT / "integrity_gen3.json").write_text(json.dumps(integ, indent=2), encoding="utf-8")
    (OUT / "rows_gen3.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print("GEN-v3 DONE — rows:", len(rows), "| ledger events:", integ["count"],
          "| valid:", integ["valid"])


if __name__ == "__main__":
    main()
