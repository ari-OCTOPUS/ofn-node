"""Deterministic, offline MAP-Elites evolution island. No external executor."""
from dataclasses import asdict, dataclass
import hashlib
import numpy as np
from environment import GENOME_DIM, evaluate, free_mask


@dataclass(frozen=True)
class Config:
    grid: int = 64
    batch: int = 96
    generations: int = 500
    initial: int = 256
    init_sigma: float = 1.2
    clip: float = 4.0
    sigma_iso: float = .10
    sigma_line: float = .25
    sigma_mut: float = .18
    mut_rate: float = .30

    def __post_init__(self):
        for name in ("grid", "batch", "initial"):
            if type(getattr(self, name)) is not int or getattr(self, name) <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if type(self.generations) is not int or self.generations < 0:
            raise ValueError("generations must be a nonnegative integer")
        for name in ("init_sigma", "clip", "sigma_iso", "sigma_line", "sigma_mut"):
            if not np.isfinite(getattr(self, name)) or getattr(self, name) <= 0:
                raise ValueError(f"Invalid {name}")
        if not 0 <= self.mut_rate <= 1:
            raise ValueError("Invalid mut_rate")


class Archive:
    def __init__(self, grid=64):
        self.grid = grid
        self.fitness = np.full((grid, grid), np.nan)
        self.genomes = np.zeros((grid, grid, GENOME_DIM))
        self.bd = np.zeros((grid, grid, 2))
        self.first_generation = np.full((grid, grid), -1, dtype=int)
        self.last_generation = np.full((grid, grid), -1, dtype=int)
        self.ids = np.full((grid, grid), -1, dtype=np.int64)
        self.parents = np.full((grid, grid, 2), -1, dtype=np.int64)
        self.operators = np.full((grid, grid), "none", dtype="<U8")
        self.center_free = free_mask(grid)
        self.meta = {key: np.zeros((grid, grid)) for key in
                     ("path_len", "collision_rate", "turn_effort", "displacement", "max_y")}

    @property
    def filled(self):
        return np.isfinite(self.fitness)

    def cell(self, bd):
        a = np.asarray(bd)
        if a.shape[-1] != 2 or not np.isfinite(a).all() or (a < 0).any() or (a > 1).any():
            raise ValueError("Descriptors must be finite [0,1]^2")
        idx = np.minimum((a * self.grid).astype(int), self.grid - 1)
        return idx[..., 0], idx[..., 1]

    def add_batch(self, genomes, fitness, bd, generation, ids, parents, ops, info):
        if not np.isfinite(genomes).all() or not np.isfinite(fitness).all():
            raise ValueError("Invalid candidate")
        ii, jj = self.cell(bd)
        admitted = np.zeros(len(fitness), dtype=bool)
        new_cell = np.zeros(len(fitness), dtype=bool)
        for k, (i, j) in enumerate(zip(ii, jj)):
            current = self.fitness[i, j]
            if np.isfinite(current) and fitness[k] <= current:
                continue
            new_cell[k] = not np.isfinite(current)
            if new_cell[k]:
                self.first_generation[i, j] = generation
            admitted[k] = True
            self.fitness[i, j] = fitness[k]
            self.genomes[i, j] = genomes[k]
            self.bd[i, j] = bd[k]
            self.ids[i, j] = ids[k]
            self.parents[i, j] = parents[k]
            self.operators[i, j] = ops[k]
            self.last_generation[i, j] = generation
            for key in self.meta:
                self.meta[key][i, j] = info[key][k]
        # Accepted sequentially is not the same as surviving the whole batch.
        survives = self.ids[ii, jj] == ids
        return admitted, new_cell, survives

    def elites(self):
        m = self.filled
        return self.genomes[m], self.fitness[m], self.bd[m]

    def metrics(self, seed=2026):
        _, f, bd = self.elites()
        hist, _, _ = np.histogram2d(bd[:, 0], bd[:, 1], bins=8, range=[[0, 1], [0, 1]])
        p = hist.ravel()
        p = p[p > 0] / len(f)
        # Private diagnostic RNG: never consumes evolution RNG, no global state.
        rng = np.random.default_rng(seed)
        if len(bd) < 2:
            spread = 0.0
        else:
            a = rng.integers(0, len(bd), 4096)
            b = (a + rng.integers(1, len(bd), 4096)) % len(bd)
            spread = float(np.linalg.norm(bd[a] - bd[b], axis=1).mean())
        return {
            "n_elites": len(f),
            "coverage": len(f) / self.grid**2,
            "center_free_coverage": float((self.filled & self.center_free).sum() / self.center_free.sum()),
            "n_center_free": int(self.center_free.sum()),
            "n_boundary_elites": int((self.filled & ~self.center_free).sum()),
            "qd_score": float(f.sum()),
            "normalized_qd": float(f.sum() / self.grid**2),
            "mean_fitness": float(f.mean()),
            "max_fitness": float(f.max()),
            "bd_entropy": float(-(p * np.log2(p)).sum()),
            "bd_spread": spread,
        }

    def save(self, path):
        np.savez_compressed(path, fitness=self.fitness, genomes=self.genomes, bd=self.bd,
                            first_generation=self.first_generation, last_generation=self.last_generation,
                            ids=self.ids, parents=self.parents, operators=self.operators,
                            center_free=self.center_free, **self.meta)

    @classmethod
    def load(cls, path):
        with np.load(path, allow_pickle=False) as data:
            a = cls(data["fitness"].shape[0])
            for key in ("fitness", "genomes", "bd", "first_generation", "last_generation",
                        "ids", "parents", "operators", "center_free"):
                setattr(a, key, data[key].copy())
            for key in a.meta:
                a.meta[key] = data[key].copy()
        return a


def uniform_crossover(x, y, rng):
    return np.where(rng.random(x.shape) < .5, x, y)


def gaussian_mutation(x, rng, sigma=.18, rate=.30):
    mask = rng.random(x.shape) < rate
    return x + mask * rng.normal(0, sigma, x.shape)


def variation(archive, rng, config, mode):
    genomes, _, _ = archive.elites()
    ids = archive.ids[archive.filled]
    first = rng.integers(0, len(ids), config.batch)
    second = rng.integers(0, len(ids), config.batch)
    p1, p2 = genomes[first], genomes[second]
    parents = np.stack((ids[first], ids[second]), axis=1)
    probs = {"full": [.4, .4, .2], "mutation": [0, 0, 1], "crossover": [0, 1, 0]}[mode]
    ops = rng.choice(["line", "xover", "mut"], size=config.batch, p=probs)
    kids = np.empty_like(p1)
    for k, op in enumerate(ops):
        if op == "line":
            kids[k] = p1[k] + rng.normal(0, config.sigma_iso, GENOME_DIM) + rng.normal(0, config.sigma_line) * (p2[k] - p1[k])
        elif op == "xover":
            kids[k] = gaussian_mutation(uniform_crossover(p1[k], p2[k], rng), rng,
                                        config.sigma_mut, config.mut_rate)
        else:
            kids[k] = gaussian_mutation(p1[k], rng, config.sigma_mut * 1.5, .5)
            parents[k, 1] = -1
    return np.clip(kids, -config.clip, config.clip), parents, ops


def run(seed=7, config=None, mode="full", ledger=None, verbose=True):
    config = config or Config()
    if mode not in ("full", "mutation", "crossover", "random"):
        raise ValueError("Unknown mode")
    rng = np.random.default_rng(seed)
    archive = Archive(config.grid)
    history = []
    stats = {op: {"attempts": 0, "admitted": 0, "new_cells": 0, "survived_batch": 0}
             for op in ("line", "xover", "mut", "random")}
    if ledger:
        ledger.append("run_started", {"seed": seed, "mode": mode, "config": asdict(config)}, 0)
    evaluations = 0
    for generation in range(config.generations + 1):
        count = config.initial if generation == 0 else config.batch
        if generation == 0 or mode == "random":
            kids = np.clip(rng.normal(0, config.init_sigma, (count, GENOME_DIM)), -config.clip, config.clip)
            parents = np.full((count, 2), -1, dtype=np.int64)
            ops = np.full(count, "random")
        else:
            kids, parents, ops = variation(archive, rng, config, mode)
        ids = np.arange(evaluations, evaluations + count)
        fitness, bd, info = evaluate(kids)
        admitted, new, survives = archive.add_batch(kids, fitness, bd, generation, ids, parents, ops, info)
        evaluations += count
        if generation > 0:
            for op in stats:
                m = ops == op
                stats[op]["attempts"] += int(m.sum())
                stats[op]["admitted"] += int((m & admitted).sum())
                stats[op]["new_cells"] += int((m & new).sum())
                stats[op]["survived_batch"] += int((m & survives).sum())
        row = dict(gen=generation, evals=evaluations, new_cells=int(new.sum()),
                   admissions=int(admitted.sum()), surviving_offspring=int(survives.sum()),
                   reused_parent_ids=int(len(np.unique(parents[parents >= 0]))),
                   **archive.metrics(seed=2026 + generation))
        history.append(row)
        if ledger:
            ledger.append("generation_evaluated", {
                "metrics": row,
                "candidate_weights_sha256": hashlib.sha256(kids.astype("<f8").tobytes()).hexdigest(),
                "selected_parent_ids": np.unique(parents[parents >= 0]).tolist(),
                "admitted_ids": ids[admitted].tolist(),
                "surviving_ids": ids[survives].tolist(),
            }, generation)
        if verbose and (generation % 100 == 0 or generation == config.generations):
            print(f"{mode} seed={seed} gen={generation} evals={evaluations} "
                  f"coverage={row['coverage']:.3f} QD={row['qd_score']:.1f}", flush=True)
    return archive, history, stats
