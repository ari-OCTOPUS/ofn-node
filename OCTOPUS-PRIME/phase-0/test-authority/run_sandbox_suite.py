#!/usr/bin/env python3
"""run_sandbox_suite.py — manifest-driven OCTOPUS test authority (F).

Reconciles the existing heterogeneous runner (_ops/tests/run_all.py) into a
machine-driven, per-file, sandboxed runner. It does NOT do a global pytest
collect (that green-lies script-native tests). Each file runs in its own
subprocess with:

  * REAL_VAULT pinned to the CANDIDATE repo (never the live vault) — so harness
    reads candidate data, and test_phase0_safety_net reads candidate source;
  * ORG_ROOT/OPS_DIR/STATE_DIR/... redirected to a per-run sandbox;
  * the sandbox_barrier active via sitecustomize (hard backstop: any write under
    the LIVE vault is refused + recorded, per-process, aggregated here);
  * secrets scrubbed, network + subprocess blocked inside the child.

Usage:
  python -X utf8 run_sandbox_suite.py --limit 12         # bounded proof run
  python -X utf8 run_sandbox_suite.py --full             # full manifest
  python -X utf8 run_sandbox_suite.py --files a.py b.py   # specific files
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TA_DIR = Path(__file__).resolve().parent                 # .../test-authority
REPO = TA_DIR.parents[2]                                  # F:\octopus-phase0-isolated
TESTS_DIR = REPO / "_ops" / "tests"
LIVE_VAULT = Path(os.environ.get("BARRIER_FORBIDDEN_ROOT", r"F:\backup"))

SECURITY_HINTS = ("halt", "stop", "guard", "append", "effector", "approval",
                  "capability", "memory_gate", "consent", "autonomy", "ps_writeback",
                  "security", "token", "binding")


def build_manifest() -> list[dict]:
    sys.path.insert(0, str(TESTS_DIR))
    import run_all as R  # __main__-guarded; importing only defines the lists
    manifest = []
    seen = set()
    for name in R.TESTS:
        if name in seen:
            continue
        seen.add(name)
        low = str(name).lower()
        manifest.append({
            "path": str(TESTS_DIR / name),
            "name": str(name),
            "runner": "pytest" if name in R.PYTEST_TESTS else "python",
            "stage": 2 if any(h in low for h in SECURITY_HINTS) else 1,
            "registered": True,
            "timeout": 300,
        })
    for p in R.EXTRA_TESTS:
        manifest.append({"path": str(p), "name": Path(p).name, "runner": "python",
                         "stage": 1, "registered": True, "timeout": 300})
    return manifest


def make_sandbox(run_id: str) -> tuple[Path, dict]:
    root = Path(tempfile.mkdtemp(prefix=f"octopus-F-{run_id}-"))
    (root / "site").mkdir()
    (root / "barrier-evidence").mkdir()
    (root / "tmp").mkdir()
    # sitecustomize: activate barrier at interpreter startup + dump evidence at exit
    ev = str(root / "barrier-evidence")
    (root / "site" / "sitecustomize.py").write_text(
        "import atexit, json, os, sys\n"
        f"sys.path.insert(0, r'{TA_DIR}')\n"
        "try:\n"
        "    import sandbox_barrier as _B\n"
        "    _B.install()\n"
        "except Exception as _e:\n"
        # barrier MUST be active — never run a test unprotected (would give bogus
        # '0 live-writes' evidence). Abort the child loudly.
        f"    open(os.path.join(r'{ev}', f'{{os.getpid()}}.BARRIER_FAILED'),'w').write(repr(_e))\n"
        "    os._exit(97)\n"
        "def _dump():\n"
        f"    p = os.path.join(r'{ev}', f'{{os.getpid()}}.json')\n"
        "    try:\n"
        "        s = _B.summary(); s['test_file'] = os.environ.get('OCTOPUS_TEST_FILE','?')\n"
        "        open(p,'w',encoding='utf-8').write(json.dumps(s))\n"
        "    except Exception: pass\n"
        "atexit.register(_dump)\n", encoding="utf-8")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root / "site") + os.pathsep + env.get("PYTHONPATH", "")
    # CANDIDATE as REAL_VAULT (never live) — harness reads candidate data/source
    env["REAL_VAULT"] = str(REPO)
    env["ORG_ROOT"] = str(root / "vault")
    env["OPS_DIR"] = str(root / "vault" / "_ops")
    env["STATE_DIR"] = str(root / "vault" / "_ops" / "state")
    env["GENOME_DIR"] = str(root / "vault" / "genome")
    env["TEMP"] = env["TMP"] = str(root / "tmp")
    env["BARRIER_FORBIDDEN_ROOT"] = str(LIVE_VAULT)
    # point the local LLM at a dead loopback port so no real Ollama inference
    # runs during the suite (deterministic; the probe fails-soft).
    env["OLLAMA_BASE_URL"] = "http://127.0.0.1:9"
    # scrub obvious secrets (barrier also does this inside the child)
    for k in list(env):
        if any(t in k.upper() for t in ("TOKEN", "SECRET", "API_KEY", "APIKEY",
                                        "PASSWORD", "POCKETSMITH")) and "WIRE" not in k.upper():
            env[k] = "FAKE-REDACTED"
    # Seed a synthetic baseline config so pytest-style tests that read ORG_ROOT
    # config (e.g. organ_table→budgets.yaml) run ISOLATED instead of silently
    # falling back to the live vault's budgets.yaml. Reuses harness.TEST_BUDGETS.
    budget_dir = root / "vault" / "_ops" / "budget"
    budget_dir.mkdir(parents=True, exist_ok=True)
    (root / "vault" / "_ops" / "state").mkdir(parents=True, exist_ok=True)
    try:
        sys.path.insert(0, str(TESTS_DIR))
        import harness as _h
        (budget_dir / "budgets.yaml").write_text(_h.TEST_BUDGETS, encoding="utf-8")
    except Exception:
        pass
    return root, env


def run_one(entry: dict, env: dict) -> dict:
    p = Path(entry["path"])
    if not p.exists():
        return {**entry, "result": "MISSING_ON_DISK", "returncode": None, "duration_s": 0}
    cmd = ([sys.executable, "-X", "utf8", "-m", "pytest", "-q", str(p)]
           if entry["runner"] == "pytest" else
           [sys.executable, "-X", "utf8", str(p)])
    child_env = dict(env)
    child_env["OCTOPUS_TEST_FILE"] = entry["name"]
    t0 = time.perf_counter()
    try:
        r = subprocess.run(cmd, cwd=str(p.parent), env=child_env, timeout=entry["timeout"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        dt = time.perf_counter() - t0
        tail = "\n".join((r.stdout or "").splitlines()[-6:])
        res = "PASS" if r.returncode == 0 else "FAIL"
        return {**entry, "result": res, "returncode": r.returncode,
                "duration_s": round(dt, 2), "output_tail": tail}
    except subprocess.TimeoutExpired:
        return {**entry, "result": "TIMEOUT", "returncode": None,
                "duration_s": round(time.perf_counter() - t0, 2)}


def aggregate_barrier(root: Path) -> dict:
    total_writes, total_net, files = 0, 0, 0
    samples = []
    for f in (root / "barrier-evidence").glob("*.json"):
        try:
            s = json.loads(f.read_text(encoding="utf-8"))
            files += 1
            total_writes += s.get("attempted_live_writes", 0)
            total_net += s.get("network_attempts", 0)
            samples += s.get("attempted_live_writes_samples", [])[:5]
        except Exception:
            pass
    failed = list((root / "barrier-evidence").glob("*.BARRIER_FAILED"))
    ext_net_by_file = {}
    for f in (root / "barrier-evidence").glob("*.json"):
        try:
            s = json.loads(f.read_text(encoding="utf-8"))
            if s.get("network_attempts", 0) > 0:
                tf = s.get("test_file", "?")
                ext_net_by_file.setdefault(tf, []).extend(s.get("network_attempts_samples", []))
        except Exception:
            pass
    return {"child_processes_with_evidence": files,
            "barrier_install_failures": len(failed),
            "suite_attempted_live_writes": total_writes,
            "suite_external_network_attempts": total_net,
            "external_network_by_file": ext_net_by_file,
            "attempted_live_write_samples": samples[:20]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--files", nargs="*")
    ap.add_argument("--stage", type=int, default=0)
    args = ap.parse_args()

    manifest = build_manifest()
    (TA_DIR / "test_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

    if args.files:
        sel = [e for e in manifest if e["name"] in set(args.files)]
    elif args.stage:
        sel = [e for e in manifest if e["stage"] == args.stage]
    else:
        sel = manifest
    if args.limit:
        sel = sel[:args.limit]

    run_id = str(len(sel))
    root, env = make_sandbox(run_id)
    print(f"sandbox: {root}\nREAL_VAULT(candidate): {env['REAL_VAULT']}\nrunning {len(sel)} files\n")

    results = []
    for i, e in enumerate(sel, 1):
        r = run_one(e, env)
        results.append(r)
        print(f"[{i}/{len(sel)}] {r['result']:6} {e['runner']:6} {e['name']}")

    counts = {}
    for r in results:
        counts[r["result"]] = counts.get(r["result"], 0) + 1
    barrier = aggregate_barrier(root)

    report = {
        "manifest_total": len(manifest),
        "selected": len(sel),
        "counts": counts,
        "barrier_evidence_from_suite": barrier,
        "note": "suite_attempted_live_writes MUST be 0 (distinct from barrier self-test probes)",
        "results": results,
    }
    out = TA_DIR / "FULL-SANDBOX-TEST-REPORT.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\ncounts: {counts}")
    print(f"barrier: {barrier['suite_attempted_live_writes']} attempted live-writes, "
          f"{barrier['suite_external_network_attempts']} external-network attempts, "
          f"{barrier['barrier_install_failures']} barrier-install-failures, "
          f"{barrier['child_processes_with_evidence']} children-with-evidence")
    print(f"report: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
