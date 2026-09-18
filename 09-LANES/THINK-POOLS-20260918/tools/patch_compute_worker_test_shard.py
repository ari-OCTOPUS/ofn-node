#!/usr/bin/env python3
"""RUN-TO-COMPLETION item 5 — add the `test_shard` profile to compute_worker.py.

Run ON 138 against the repo source of truth:
    python3 patch_compute_worker_test_shard.py \
        /home/ari/ofn/state/fleet-compute/compute_worker.py

Replacements (each uniqueness-checked):
  R1  helpers _shard_ids + _work_test_shard inserted before PROFILES.
      The workload collects the suite with pytest --collect-only, takes every
      Nth id (disjoint, covering), and runs exactly that slice. root/pylib are
      confined to the task's allowed roots; both subprocesses are bounded by
      the envelope deadline.
  R2  PROFILES registry entry (allowlist — the only way new work becomes
      executable on a node).
  R3  AGENT_VERSION bump for two-way deploy verification.

Aborts without writing if the preimage sha or any anchor mismatches.
"""
import hashlib
import sys
from pathlib import Path

EXPECTED_PRE = "feaaf8d882f170a0957a468941e44a7825a597ed5266696c9fb08f59c0279bf3"

R1_OLD = '''PROFILES = {
    # name -> spec. Adding a profile is the ONLY way to make new work executable.
'''
R1_NEW = '''def _shard_ids(ids: list, index: int, count: int) -> list:
    """Deterministic disjoint slice: every count-th id starting at index.

    Shards of one collection are pairwise disjoint and their union is the
    whole list, so a fleet can split a suite without overlaps or gaps."""
    if not (0 <= index < count):
        raise ValueError(f"shard {index}/{count} out of range")
    return ids[index::count]


def _work_test_shard(params: dict, ctx: dict) -> dict:
    """Run one deterministic slice of the ofn pytest suite — real CI work.

    root (suite checkout) and pylib (vendored pytest) are confined to the
    profile's allowed prefixes, so a task cannot aim pytest at arbitrary
    trees. Collection order comes from pytest and is stable, so shards are
    comparable and recombinable across nodes."""
    import subprocess
    import sys
    root = Path(str(params["root"])).resolve()
    allowed = tuple(ctx["allowed_roots"])
    if not any(str(root).startswith(p) for p in allowed):
        raise PermissionError(f"root outside allowed prefixes: {root}")
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    pylib = str(params.get("pylib", "") or "").strip()
    if pylib:
        plib = Path(pylib).resolve()
        if not any(str(plib).startswith(p) for p in allowed):
            raise PermissionError(f"pylib outside allowed prefixes: {plib}")
        env["PYTHONPATH"] = str(plib)
    shard_index = int(params["shard_index"])
    shard_count = int(params["shard_count"])

    def remaining() -> float:
        return max(5.0, ctx["deadline_mono"] - time.monotonic())

    started = time.monotonic()
    collect = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=str(root), env=env, capture_output=True, text=True,
        timeout=min(remaining(), 90.0))
    ids = [line.strip() for line in collect.stdout.splitlines() if "::" in line]
    if not ids:
        raise RuntimeError(
            f"collection_empty rc={collect.returncode} {collect.stderr.strip()[:120]}")
    selected = _shard_ids(ids, shard_index, shard_count)
    run = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header",
         "-p", "no:cacheprovider", *selected],
        cwd=str(root), env=env, capture_output=True, text=True,
        timeout=remaining())
    lines = [l for l in run.stdout.strip().splitlines() if l.strip()]
    summary = (lines[-1] if lines else "")[:200]
    return {
        "root": str(root),
        "shard": f"{shard_index}/{shard_count}",
        "collected": len(ids),
        "selected": len(selected),
        "pytest_rc": run.returncode,
        "summary": summary,
        "collect_rc": collect.returncode,
        "elapsed_s": round(time.monotonic() - started, 2),
    }


PROFILES = {
    # name -> spec. Adding a profile is the ONLY way to make new work executable.
'''

R2_OLD = '''            "max_bytes": {"type": "int", "min": 1, "max": 2 * 1024 * 1024 * 1024},
        },
    },
}
'''
R2_NEW = '''            "max_bytes": {"type": "int", "min": 1, "max": 2 * 1024 * 1024 * 1024},
        },
    },
    "test_shard": {
        "version": "1",
        "resource_class": "cpu_batch",
        "max_seconds": 240,
        "default_seconds": 100,
        "workload": _work_test_shard,
        "params": {
            "root": {"type": "str", "max_len": 300},
            "shard_index": {"type": "int", "min": 0, "max": 63},
            "shard_count": {"type": "int", "min": 1, "max": 64},
            "pylib": {"type": "str", "max_len": 300},
        },
    },
}
'''

R3_OLD = 'AGENT_VERSION = "1.1.0"'
R3_NEW = 'AGENT_VERSION = "1.2.0-testshard"'

REPLACEMENTS = [("R1 helpers+workload", R1_OLD, R1_NEW),
                ("R2 registry entry", R2_OLD, R2_NEW),
                ("R3 version", R3_OLD, R3_NEW)]


def main() -> int:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else
                  "/home/ari/ofn/state/fleet-compute/compute_worker.py")
    pre = hashlib.sha256(target.read_bytes()).hexdigest()
    if pre != EXPECTED_PRE:
        print("PREIMAGE_MISMATCH", pre)
        return 2
    src = target.read_text(encoding="utf-8")
    for name, old, new in REPLACEMENTS:
        n = src.count(old)
        if n != 1:
            print(f"ABORT anchor {name} count={n}")
            return 3
        src = src.replace(old, new)
    with target.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(src)
    print("PREIMAGE ", pre)
    print("POSTIMAGE", hashlib.sha256(target.read_bytes()).hexdigest())
    print("PATCHED", len(REPLACEMENTS), "replacements ->", target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
