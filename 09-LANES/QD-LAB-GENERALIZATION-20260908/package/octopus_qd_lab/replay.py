"""Replay an archived neural controller, locally, with no mutation or external action."""
import argparse
import json
from pathlib import Path
import numpy as np
from environment import evaluate
from map_elites import Archive


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive", type=Path,
                   default=Path(__file__).resolve().parent / "results/full_seed7/archive.npz")
    p.add_argument("--elite-id", type=int)
    p.add_argument("--trajectory", type=Path, help="Optional new CSV path for x,y trajectory")
    args = p.parse_args()
    a = Archive.load(args.archive)
    g, f, bd = a.elites()
    ids = a.ids[a.filled]
    if args.elite_id is None:
        k = int(np.argmax(f))
    else:
        match = np.flatnonzero(ids == args.elite_id)
        if len(match) != 1:
            p.error("Elite ID not retained in this archive")
        k = int(match[0])
    ff, bb, info = evaluate(g[k], record_traj=True)
    np.testing.assert_allclose(ff[0], f[k], atol=1e-12, rtol=0)
    np.testing.assert_allclose(bb[0], bd[k], atol=1e-12, rtol=0)
    if args.trajectory:
        with args.trajectory.open("x", encoding="utf-8") as fp:
            np.savetxt(fp, info["traj"][:, 0], delimiter=",", header="x,y", comments="")
    print(json.dumps({"elite_id": int(ids[k]), "fitness": float(ff[0]), "descriptor": bb[0].tolist(),
                      "replay_match": True, "production_authorized": False,
                      "episode": {key: float(v[0]) for key, v in info.items() if key != "traj"}},
                     indent=2))


if __name__ == "__main__":
    main()
