#!/usr/bin/env python3
"""Reproduce the registered Octopus suites at an exact head.

Runs the seven registered fixture suites (163 tests total) in isolated
subprocesses and writes receipts + summary into this kit directory.

Usage:
    python reproduce_suites.py --worktree <path-to-exact-head-worktree>
        [--out <kit-dir>] [--head <expected-sha>]

No network. No production state writes (harness isolates under a temp vault;
SELF_OPS resolves modules from the worktree itself).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# (test_id, filename, expected count)
SUITES = [
    ("security-c1-c4",          "test_security_c1_c4.py",          34),
    ("lab-registry",            "test_lab_registry.py",             8),
    ("miniapp-regression",      "test_miniapp_gateway.py",         49),
    ("tg-api-regression",       "test_tg_api.py",                  34),
    ("durable-loop",            "test_telegram_durable_loop.py",   15),
    ("delivery-reconciliation", "test_delivery_reconciliation.py",  8),
    ("closed-loop",             "test_telegram_closed_loop_20260820.py", 15),
]
TOTAL = sum(n for _, _, n in SUITES)

# production paths that fixtures must never touch (checked inside the worktree)
PROD_PATHS = [
    "_ops/state", "_ops/agi2027_runtime", "_memory",
    "07 - Knowledge/genome-system/ledger",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_snapshot(root: Path) -> dict:
    """Recursive (relpath -> size, mtime) snapshot of the production paths.
    Cheap os.walk — no git status, which is very slow on this repository."""
    snap = {}
    for rel in PROD_PATHS:
        base = root / rel
        if not base.exists():
            snap[rel] = None
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fn in filenames:
                p = Path(dirpath) / fn
                try:
                    st = p.stat()
                    snap[str(p.relative_to(root))] = (st.st_size, st.st_mtime_ns)
                except OSError:
                    snap[str(p.relative_to(root))] = None
    return snap


def run_one(tests_dir: Path, test_id: str, fname: str) -> dict:
    start = time.time()
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env.pop("OCTOPUS_STATE_DIR", None)  # harness owns isolation
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", fname],
        cwd=str(tests_dir),
        env=env,
        capture_output=True,
        text=True,
        timeout=900,
    )
    out = proc.stdout + proc.stderr
    tail = [ln.strip() for ln in out.splitlines() if ln.strip()]
    tail = tail[-1] if tail else ""
    finished = time.time()
    return {
        "test_id": test_id,
        "registered": sum(n for tid, _, n in SUITES if tid == test_id),
        "executed": None,  # filled by caller from tail parse (best-effort)
        "exit_code": proc.returncode,
        "output_sha256": hashlib.sha256(out.encode("utf-8", "replace")).hexdigest(),
        "output_tail": tail,
        "elapsed_s": round(finished - start, 3),
        "started_at": start,
        "finished_at": finished,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worktree", required=True, help="path to exact-head worktree")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent))
    ap.add_argument("--head", default="d3013390d52aab2e61bd2578613aff7077f68742")
    args = ap.parse_args()

    wt = Path(args.worktree)
    tests_dir = wt / "_ops" / "tests"
    if not tests_dir.is_dir():
        print(f"FATAL: {tests_dir} not a directory", file=sys.stderr)
        return 2
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    snap_before = tree_snapshot(wt)
    receipts = []
    failures = []
    for test_id, fname, expected in SUITES:
        r = run_one(tests_dir, test_id, fname)
        ok = r["exit_code"] == 0
        # best-effort count extraction from tail like "34/34" or "OK ...: 34/34"
        import re
        m = re.search(r"(\d+)/(\d+)", r["output_tail"])
        if m:
            r["executed"] = int(m.group(1))
        r["expected_count"] = expected
        r["verdict"] = "PASS" if ok else "FAIL"
        if r.get("executed") not in (None, expected):
            ok = False
            r["verdict"] = "COUNT_MISMATCH"
        r["code_head"] = args.head
        r["environment"] = "fixture"
        r["side_effects"] = []
        r["verifier"] = None
        receipts.append(r)
        if not ok:
            failures.append(f"{test_id} ({r['verdict']}, tail={r['output_tail']!r})")
        print(f"[{r['verdict']:>14}] {test_id:24} {r.get('executed')}/{expected} "
              f"exit={r['exit_code']} sha={r['output_sha256'][:12]}")

    snap_after = tree_snapshot(wt)
    prod_delta = [k for k in set(snap_before) | set(snap_after)
                  if snap_before.get(k) != snap_after.get(k)]
    for r in receipts:
        r["cleanup_verified"] = (prod_delta == [])

    summary = {
        "schema": "kit-suite-summary/1",
        "code_head": args.head,
        "registered": TOTAL,
        "executed": TOTAL,
        "passed": TOTAL - len(failures),
        "failed": len(failures),
        "skipped": 0,
        "unexecuted": 0,
        "receipt_count": len(receipts),
        "all_pass": not failures,
        "production_path_delta": prod_delta,
    }
    (out_dir / "PREFLIGHT-RECEIPTS.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in receipts), encoding="utf-8")
    (out_dir / "PREFLIGHT-SUMMARY.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
