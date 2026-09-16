"""Reproducible study runner. Writes only to a new local output folder per run."""
import argparse
from contextlib import redirect_stderr
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import unittest
import numpy as np
import matplotlib
from map_elites import Config, run
from octopus_bridge import ReceiptLedger, verify_ledger

ROOT = Path(__file__).resolve().parent
SCIENTIFIC_FILES = ("environment.py", "map_elites.py", "octopus_bridge.py", "experiment.py")
HYPOTHESES = [
    {
        "id": "OQD-H1", "claim": "Archive reuse beats fresh random sampling on diversity and quality.",
        "status": "PREREGISTERED_LOCAL", "test_plan": "Paired seeds 7,11,23; same initial genomes and evaluation budget.",
        "primary_metrics": ["coverage", "qd_score"],
        "threshold": {"mean_coverage_delta": .10, "mean_qd_relative_delta": .10},
        "kill_condition": "Reject if mean coverage gain <0.10 or relative QD gain <0.10; missing pairs => UNKNOWN.",
    },
    {
        "id": "OQD-H2", "claim": "The fixed mixed operator policy adds value over mutation-only.",
        "status": "PREREGISTERED_LOCAL", "test_plan": "Paired seeds 7,11,23 under identical environment and budgets.",
        "threshold": {"mean_qd_relative_delta": .02, "minimum_mean_coverage_delta": -.01},
        "kill_condition": "Reject if mixed policy improves QD by <2% or loses >1 percentage point coverage.",
    },
    {
        "id": "OQD-H3", "claim": "The local evidence gate fails closed under the covered fault cases.",
        "status": "PREREGISTERED_LOCAL", "test_plan": "Run test_bridge and anchor every run's ledger head and length.",
        "threshold": {"all_tests_pass": True, "all_chains_valid": True, "production_authorized": False},
        "kill_condition": "Any covered corrupt/missing evidence is accepted, any chain fails, or any production authorization appears.",
    },
]


def dump_json(path, value):
    with Path(path).open("w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)


def digest_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_hashes():
    return {name: digest_file(ROOT / name) for name in SCIENTIFIC_FILES}


def test_evidence(out):
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(ROOT), pattern="test_*.py")
    with redirect_stderr(stream):
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    (out / "tests.txt").write_text(stream.getvalue(), encoding="utf-8")
    record = {
        "tests_run": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors), "skipped": len(result.skipped),
        "successful": result.wasSuccessful() and not result.skipped,
        "scope": "local tests, not independent audit",
        "test_hashes": {p.name: digest_file(p) for p in ROOT.glob("test_*.py")},
    }
    dump_json(out / "tests.json", record)
    if not record["successful"]:
        raise RuntimeError("Tests failed; study halted")
    return record


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=ROOT / "results")
    p.add_argument("--generations", type=int, default=500)
    p.add_argument("--grid", type=int, default=64)
    p.add_argument("--batch", type=int, default=96)
    p.add_argument("--initial", type=int, default=256)
    p.add_argument("--seeds", type=int, nargs="+", default=[7, 11, 23])
    p.add_argument("--modes", nargs="+", choices=["full", "mutation", "random", "crossover"],
                   default=["full", "mutation", "random"])
    args = p.parse_args()
    config = Config(grid=args.grid, batch=args.batch, generations=args.generations, initial=args.initial)
    args.out.mkdir(parents=True, exist_ok=True)
    protocol_path = args.out / "study.json"
    now = datetime.now(timezone.utc).isoformat()
    if protocol_path.exists():
        protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
        if protocol["config"] != asdict(config) or protocol["scientific_code_sha256"] != source_hashes():
            raise RuntimeError("Frozen study/config mismatch: use a NEW --out folder")
    else:
        protocol = {
            "study_id": "OCTOPUS-QD-LAB-v2", "created_at": now,
            "status": "LOCAL_SIMULATION_ONLY", "production_authorized": False,
            "config": asdict(config), "planned_seeds": [7, 11, 23],
            "planned_modes": ["full", "mutation", "random"],
            "scientific_code_sha256": source_hashes(), "hypotheses": HYPOTHESES,
            "preregistration_note": "Frozen before this v2 study, after earlier exploratory v1 runs. No external timestamp anchor.",
            "versions": {"python": platform.python_version(), "numpy": np.__version__,
                         "matplotlib": matplotlib.__version__, "platform": platform.platform()},
        }
        with protocol_path.open("x", encoding="utf-8") as f:
            json.dump(protocol, f, ensure_ascii=False, indent=2, allow_nan=False)
    test_record = test_evidence(args.out)
    for seed in args.seeds:
        for mode in args.modes:
            if source_hashes() != protocol["scientific_code_sha256"]:
                raise RuntimeError("Harness changed during study")
            out = args.out / f"{mode}_seed{seed}"
            out.mkdir()  # Fail rather than overwrite existing or partial experiment.
            ledger_path = out / "receipts.jsonl"
            ledger = ReceiptLedger(ledger_path)
            ledger.append("protocol_bound", {"study_sha256": digest_file(protocol_path),
                                           "scientific_code_sha256": source_hashes()}, 0)
            archive, history, stats = run(seed, config, mode, ledger)
            archive.save(out / "archive.npz")
            dump_json(out / "history.json", history)
            dump_json(out / "operators.json", stats)
            final_payload = {
                "archive_sha256": digest_file(out / "archive.npz"),
                "history_sha256": digest_file(out / "history.json"),
                "operators_sha256": digest_file(out / "operators.json"),
                "metrics": history[-1], "tests_ok": test_record["successful"],
            }
            last = ledger.append("run_completed", final_payload, config.generations)
            ledger.close()
            check = verify_ledger(ledger_path, expected_head=last["hash"], expected_count=config.generations + 4)
            dump_json(out / "integrity.json", check)
            if not check["valid"]:
                raise RuntimeError(f"Integrity failure: {check}")
            dump_json(out / "run_summary.json", {
                "mode": mode, "seed": seed, "config": asdict(config), "final": history[-1],
                "receipt_anchor": {"head": last["hash"], "count": config.generations + 4},
                "file_hashes": {n: digest_file(out / n) for n in
                               ("archive.npz", "history.json", "operators.json", "receipts.jsonl")},
                "note": "Anchor is local and unsigned; preserve elsewhere for later comparison.",
            })


if __name__ == "__main__":
    main()
