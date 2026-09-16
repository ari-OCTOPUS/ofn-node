"""Local numerical replay of every retained controller in the primary archive."""
import argparse
from pathlib import Path
import numpy as np
from environment import evaluate
from map_elites import Archive
from experiment import dump_json, digest_file


def validate(archive_path, out):
    archive = Archive.load(archive_path)
    genomes, fitness, bd = archive.elites()
    error_f = error_bd = 0.0
    for start in range(0, len(genomes), 256):
        stop = start + 256
        ff, bb, _ = evaluate(genomes[start:stop])
        error_f = max(error_f, float(np.max(np.abs(ff - fitness[start:stop]))))
        error_bd = max(error_bd, float(np.max(np.abs(bb - bd[start:stop]))))
    record = {"archive_sha256": digest_file(archive_path), "elites_checked": len(genomes),
              "max_fitness_abs_error": error_f, "max_descriptor_abs_error": error_bd,
              "tolerance": 1e-12, "valid": error_f <= 1e-12 and error_bd <= 1e-12,
              "scope": "all primary-run elites, same environment; no held-out or independent audit"}
    dump_json(out, record)
    if not record["valid"]:
        raise RuntimeError(record)
    print(record)


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive", type=Path, default=root / "results/full_seed7/archive.npz")
    p.add_argument("--out", type=Path, default=root / "results/full_archive_replay.json")
    args = p.parse_args()
    validate(args.archive, args.out)
