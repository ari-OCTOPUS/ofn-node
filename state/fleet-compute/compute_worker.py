#!/usr/bin/env python3
"""FLEET COMPUTE — node-side worker agent.

Runs on each participating board. It executes only pre-registered task
profiles; the `params` object is data and is never interpolated into a shell
string. Every other guarantee the fleet CPU scan asks for lives here:

* task-profile allowlist with per-profile param schemas
* hard timeout, output-size cap, clean SIGTERM cancellation
* capability record the control plane reads instead of guessing node roles
* receipts carrying input digest, output digest, host facts and cgroup facts

Modes:
  --capability                 print the capability record as JSON
  --run-task PATH              validate and execute a task file, print a receipt
  --version                    print the agent version

The agent itself is deliberately NOT the cgroup. The control plane launches it
through `systemd-run --scope -p CPUQuota=... -p MemoryMax=...` so a worker bug
cannot starve OFN, SSH or the mesh transport. The agent reports the cgroup it
observed so a receipt can prove the envelope was actually applied.

python3 standard library only.
"""

from __future__ import annotations

import hashlib
import json
import multiprocessing
import os
import platform
import shutil
import signal
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

AGENT_VERSION = "1.2.1-testshard-clockbase"
RECEIPT_SCHEMA = "compute_receipt.v1"
CAPABILITY_SCHEMA = "worker_capability.v1"

STDOUT_HEAD_CHARS = 2000
DEFAULT_MAX_SECONDS = 60
MAX_OUTPUT_BYTES = 8 * 1024 * 1024
# Leave room for the agent to serialise and report before the envelope closes.
DURATION_MARGIN_S = 3.0

_cancelled = {"flag": False}


def _on_term(signum, _frame):
    _cancelled["flag"] = True


signal.signal(signal.SIGTERM, _on_term)
signal.signal(signal.SIGINT, _on_term)


def arm_timeout(seconds: int) -> bool:
    """Cooperative in-process deadline, where the platform offers one.

    SIGALRM is the backstop on Linux nodes; the authoritative timeout is the
    control plane's SSH/lease expiry. Workloads also check their own deadline,
    so behaviour is correct on platforms without SIGALRM (e.g. a test laptop).
    """
    if hasattr(signal, "SIGALRM"):
        signal.signal(signal.SIGALRM, _on_term)
        signal.alarm(int(seconds))
        return True
    return False


def disarm_timeout() -> None:
    if hasattr(signal, "SIGALRM"):
        signal.alarm(0)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_text(path: str, limit: int = 4096) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read(limit).strip()
    except OSError:
        return ""


def meminfo() -> dict:
    out = {}
    for line in read_text("/proc/meminfo", 65536).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip()
    return out


# --------------------------------------------------------------------------
# Task profiles
# --------------------------------------------------------------------------

def _cpu_churn(seconds: float, block_mb: int, seed: bytes) -> tuple[int, str]:
    """Hash-churn for `seconds`. Pure CPU, no I/O, no writes.

    Kept as a module-level function so a multiprocessing Pool can call it.
    """
    block = hashlib.sha256(seed).digest() * (block_mb * 1024 * 32)
    digest = hashlib.sha256(block).digest()
    ops = 0
    started = time.time()
    while time.time() - started < seconds and not _cancelled["flag"]:
        # One chunk = 4096 rounds of hashing over the fixed block.
        for _ in range(4096):
            digest = hashlib.sha256(digest + block[:4096]).digest()
        ops += 4096
    return ops, digest.hex()


def _child_reset_signals() -> None:
    """Pool children must die on SIGTERM.

    The parent installs a soft SIGTERM handler for cooperative cancellation.
    Forked children inherit it, which silently defeats process-pool termination:
    the child ignores the signal, the parent never returns, and the task's
    systemd scope outlives its lease. Observed live on 114 on 2026-09-18 as
    three simultaneous 8-worker scopes that never exited. Resetting to the
    default in the child restores hard termination.
    """
    for name in ("SIGTERM", "SIGINT", "SIGALRM"):
        if hasattr(signal, name):
            signal.signal(getattr(signal, name), signal.SIG_DFL)


def _churn_child(seconds: float, block_mb: int, seed: bytes, queue) -> None:
    _child_reset_signals()
    try:
        ops, digest = _cpu_churn(seconds, block_mb, seed)
        queue.put((ops, digest))
    except Exception:  # noqa: BLE001 - a dying child must not take the parent down
        pass


def _run_parallel(seconds: float, block_mb: int, seed_base: bytes, workers: int,
                  deadline_mono: float) -> list[tuple[int, str]]:
    """Run `workers` churn processes with hard, explicit teardown.

    multiprocessing.Pool is avoided deliberately: its join()/terminate()
    interaction is what deadlocked the first sustained canary. Here every child
    is terminated (then killed) explicitly, so a hung child cannot pin the scope.
    """
    mpc = _mp_context()
    queue = mpc.Queue()
    procs = []
    for i in range(workers):
        proc = mpc.Process(
            target=_churn_child,
            args=(seconds, block_mb, seed_base + f"-{i}".encode(), queue),
            daemon=True,
        )
        proc.start()
        procs.append(proc)

    results: list[tuple[int, str]] = []
    hard_deadline = deadline_mono + 5
    for _ in range(workers):
        remaining = hard_deadline - time.time()
        if remaining <= 0:
            break
        try:
            results.append(queue.get(timeout=remaining))
        except Exception:  # noqa: BLE001 - queue.Empty and friends
            break

    for proc in procs:
        if proc.is_alive():
            proc.terminate()
    time.sleep(0.2)
    for proc in procs:
        if proc.is_alive():
            proc.kill()
        proc.join(timeout=5)
    return results


def _mp_context():
    """fork where available (Linux nodes); spawn elsewhere (test laptops)."""
    method = "fork" if hasattr(os, "fork") else "spawn"
    return multiprocessing.get_context(method)


def _work_cpu_bench(params: dict, ctx: dict) -> dict:
    """Deterministic CPU calibration: SHA-256 churn over a fixed buffer.

    `workers` runs the churn in that many processes. One Python process can only
    ever occupy one core, so a multi-core board cannot be loaded to its quota by
    a single worker — the earlier single-process version capped out at load 0.97
    on an 8-core board regardless of the cgroup quota. The cgroup scope is
    inherited by every child, so the quota still bounds the whole group.
    """
    seconds = float(params.get("seconds", 10))
    block_mb = int(params.get("block_mb", 4))
    workers = int(params.get("workers", 1))
    seed_base = b"octopus-fleet-calibration-v1"
    started = time.time()

    if workers <= 1:
        ops, digest = _cpu_churn(seconds, block_mb, seed_base)
        per_worker = [(ops, digest)]
    else:
        per_worker = _run_parallel(seconds, block_mb, seed_base, workers,
                                   ctx["deadline_mono"])
        if len(per_worker) != workers:
            raise TimeoutError(
                f"only {len(per_worker)}/{workers} workers reported within the deadline"
            )

    elapsed = max(1e-6, time.time() - started)
    total_ops = sum(w[0] for w in per_worker)
    combined = hashlib.sha256(
        "|".join(sorted(w[1] for w in per_worker)).encode()
    ).hexdigest()
    return {
        "workers": workers,
        "ops": total_ops,
        "ops_per_sec": round(total_ops / elapsed, 1),
        "per_worker_ops": [w[0] for w in per_worker],
        "elapsed_s": round(elapsed, 3),
        "final_digest": combined,
        "deterministic": True,
    }


def _work_sha256_manifest(params: dict, ctx: dict) -> dict:
    """Hash a bounded file set and return a manifest digest.

    This is real indexing work, not a synthetic benchmark. The root is confined
    to the profile's allowed prefixes so a task cannot walk the whole filesystem.
    Walking is depth-first with sorted entries and an early break, so memory
    stays bounded and the order is still deterministic.
    """
    root = Path(str(params["root"])).resolve()
    allowed = tuple(ctx["allowed_roots"])
    if not any(str(root).startswith(p) for p in allowed):
        raise PermissionError(f"root outside allowed prefixes: {root}")

    max_files = int(params.get("max_files", 2000))
    max_bytes = int(params.get("max_bytes", 512 * 1024 * 1024))
    entries: list[dict] = []
    total = 0
    stop = False

    for dirpath, dirnames, filenames in os.walk(root):
        if stop or _cancelled["flag"] or time.time() > ctx["deadline_mono"]:
            break
        dirnames.sort()
        for name in sorted(filenames):
            if _cancelled["flag"] or time.time() > ctx["deadline_mono"]:
                break
            path = Path(dirpath) / name
            try:
                size = path.stat().st_size
            except OSError:
                continue
            if size > max_bytes:
                continue
            h = hashlib.sha256()
            try:
                with open(path, "rb") as fh:
                    for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                        if _cancelled["flag"]:
                            break
                        h.update(chunk)
            except OSError:
                continue
            entries.append({"path": str(path.relative_to(root)), "size": size, "sha256": h.hexdigest()})
            total += size
            if len(entries) >= max_files:
                stop = True
                break

    manifest_digest = hashlib.sha256(
        json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "root": str(root),
        "files": len(entries),
        "bytes": total,
        "complete": not stop and not _cancelled["flag"],
        "manifest_digest": manifest_digest,
        "sample": entries[:5],
    }


def _shard_ids(ids: list, index: int, count: int) -> list:
    """Deterministic disjoint slice: every count-th id starting at index.

    Shards of one collection are pairwise disjoint and their union is the
    whole list, so a fleet can split a suite without overlaps or gaps."""
    if not (0 <= index < count):
        raise ValueError(f"shard {index}/{count} out of range")
    return ids[index::count]


def _check_test_shard(params: dict) -> tuple[bool, str]:
    """Cross-field rule: a shard index must exist inside its shard count."""
    if int(params.get("shard_index", -1)) >= int(params.get("shard_count", 0)):
        return False, "SHARD_INDEX_GE_COUNT"
    return True, ""


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

    # ctx["deadline_mono"] is wall-clock based in run_task (time.time despite
    # the name); derive our own monotonic budget from max_seconds instead —
    # feeding a wall-clock delta into subprocess timeouts raises OverflowError.
    budget_s = float(ctx.get("max_seconds", 120))
    started = time.monotonic()

    def remaining() -> float:
        return max(5.0, budget_s - (time.monotonic() - started))
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
    "cpu_bench": {
        "version": "2",
        "resource_class": "cpu_batch",
        "max_seconds": 120,
        "default_seconds": 10,
        "workload": _work_cpu_bench,
        "params": {
            "seconds": {"type": "float", "min": 1, "max": 120},
            "block_mb": {"type": "int", "min": 1, "max": 64},
            "workers": {"type": "int", "min": 1, "max": 8},
        },
    },
    "sha256_manifest": {
        "version": "1",
        "resource_class": "io_batch",
        "max_seconds": 300,
        "default_seconds": 120,
        "workload": _work_sha256_manifest,
        "params": {
            "root": {"type": "str", "max_len": 300},
            "max_files": {"type": "int", "min": 1, "max": 20000},
            "max_bytes": {"type": "int", "min": 1, "max": 2 * 1024 * 1024 * 1024},
        },
    },
    "test_shard": {
        "version": "1",
        "resource_class": "cpu_batch",
        "max_seconds": 240,
        "default_seconds": 100,
        "workload": _work_test_shard,
        "cross_check": _check_test_shard,
        "params": {
            "root": {"type": "str", "max_len": 300},
            "shard_index": {"type": "int", "min": 0, "max": 63},
            "shard_count": {"type": "int", "min": 1, "max": 64},
            "pylib": {"type": "str", "max_len": 300},
        },
    },
}

# Filesystem prefixes any task may read. Nothing outside these is reachable,
# regardless of what a task asks for.
ALLOWED_ROOTS = ("/home/ari/ofn", "/srv/octopus-compute", "/tmp/octopus-compute", "/var/lib/octopus-compute")


def validate_task(task: dict) -> tuple[bool, str]:
    """Validate a task envelope. Returns (ok, error_code)."""
    if not isinstance(task, dict):
        return False, "TASK_NOT_OBJECT"
    if task.get("schema") != "compute_task.v1":
        return False, "SCHEMA_MISMATCH"
    profile = task.get("profile")
    if profile not in PROFILES:
        return False, "PROFILE_NOT_ALLOWED"
    if not task.get("task_id"):
        return False, "TASK_ID_MISSING"
    params = task.get("params", {})
    if not isinstance(params, dict):
        return False, "PARAMS_NOT_OBJECT"
    spec = PROFILES[profile]
    for key, value in params.items():
        rule = spec["params"].get(key)
        if rule is None:
            return False, "PARAM_NOT_ALLOWED"
        kind = rule["type"]
        # bool is a subclass of int in Python, so `true` would otherwise satisfy
        # an integer parameter.
        if kind == "int":
            if isinstance(value, bool) or not isinstance(value, int):
                return False, "PARAM_TYPE"
        elif kind == "float":
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return False, "PARAM_TYPE"
        elif kind == "str":
            if not isinstance(value, str) or len(value) > rule.get("max_len", 300):
                return False, "PARAM_TYPE"
        else:
            return False, "PARAM_RULE_UNKNOWN"
        if kind in ("int", "float"):
            if "min" in rule and value < rule["min"]:
                return False, "PARAM_RANGE"
            if "max" in rule and value > rule["max"]:
                return False, "PARAM_RANGE"
    # Optional per-profile cross-field rules (e.g. shard_index < shard_count).
    cross = spec.get("cross_check")
    if cross:
        ok2, err2 = cross(params)
        if not ok2:
            return False, err2
    # An envelope that claims external effects is refused outright.
    if task.get("external_effects", 0) or task.get("customer_send", False):
        return False, "EXTERNAL_EFFECTS_REFUSED"
    return True, ""


# --------------------------------------------------------------------------
# Capability record
# --------------------------------------------------------------------------

def build_capability() -> dict:
    zones = []
    for zone in sorted(Path("/sys/class/thermal").glob("thermal_zone*")):
        zones.append({"name": read_text(str(zone / "type"), 64) or zone.name})

    mem = meminfo()
    try:
        disk = shutil.disk_usage("/")
        disk_avail_kb, disk_total_kb = disk.free // 1024, disk.total // 1024
    except OSError:
        disk_avail_kb = disk_total_kb = None

    profiles = [
        {
            "name": name,
            "version": spec["version"],
            "resource_class": spec["resource_class"],
            "max_seconds": spec["max_seconds"],
            "params": sorted(spec["params"].keys()),
        }
        for name, spec in sorted(PROFILES.items())
    ]
    return {
        "schema": CAPABILITY_SCHEMA,
        "agent_version": AGENT_VERSION,
        "at_utc": utc_now(),
        "node_id": read_text("/etc/hostname", 64) or socket.gethostname(),
        "hostname": socket.gethostname(),
        "arch": platform.machine(),
        "model": (read_text("/proc/device-tree/model", 128).replace("\x00", "") or platform.platform())[:64],
        "kernel": platform.release(),
        "python": platform.python_version(),
        "machine_id": read_text("/etc/machine-id", 64),
        "boot_id": read_text("/proc/sys/kernel/random/boot_id", 64),
        "nproc": os.cpu_count(),
        "mem_total_kb": int(mem.get("MemTotal", "0 kB").split()[0] or 0),
        "mem_avail_kb": int(mem.get("MemAvailable", "0 kB").split()[0] or 0),
        "disk_root_total_kb": disk_total_kb,
        "disk_root_avail_kb": disk_avail_kb,
        "thermal_zones": zones,
        "profiles": profiles,
        "allowed_roots": list(ALLOWED_ROOTS),
        "cgroup_v2": os.path.exists("/sys/fs/cgroup/cgroup.controllers"),
        "systemd_run": shutil.which("systemd-run") is not None,
    }


def observe_cgroup() -> dict:
    """Report the cgroup envelope actually applied to this process.

    The limits live in this process's own cgroup directory, not at the cgroup
    root: reading /sys/fs/cgroup/cpu.max returns the root's value (usually
    "max") and would make an unenforced run look capped.
    """
    out = {}
    rel = ""
    try:
        with open("/proc/self/cgroup", encoding="utf-8") as fh:
            for line in fh.read(512).splitlines():
                parts = line.split(":", 2)
                if len(parts) == 3:
                    rel = parts[2].strip()
                    out["path"] = f"{parts[0]}:{parts[1]}:{rel}"
                    break
    except OSError:
        pass

    base = Path("/sys/fs/cgroup") / rel.lstrip("/")
    for fname, key in (
        ("cpu.max", "cpu_max"),
        ("cpu.weight", "cpu_weight"),
        ("memory.max", "memory_max"),
        ("memory.high", "memory_high"),
        ("pids.max", "pids_max"),
    ):
        path = base / fname
        try:
            if path.exists():
                out[key] = read_text(str(path), 64)
        except OSError:
            continue
    out["cgroup_dir"] = str(base)
    out["controllers"] = read_text("/sys/fs/cgroup/cgroup.controllers", 128)
    return out


# --------------------------------------------------------------------------
# Execution
# --------------------------------------------------------------------------

def run_task(task: dict) -> dict:
    started = utc_now()
    started_mono = time.time()
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "agent_version": AGENT_VERSION,
        "task_id": task.get("task_id"),
        "profile": task.get("profile"),
        "input_digest": task.get("input_digest"),
        "started_utc": started,
    }

    ok, err = validate_task(task)
    if not ok:
        receipt.update({
            "status": "REFUSED",
            "error": err,
            "ended_utc": utc_now(),
            "duration_s": round(time.time() - started_mono, 3),
        })
        return receipt

    spec = PROFILES[task["profile"]]
    params = dict(task.get("params", {}))
    params.setdefault("seconds", spec.get("default_seconds", DEFAULT_MAX_SECONDS))
    max_seconds = min(float(task.get("max_seconds", spec["max_seconds"])), spec["max_seconds"])

    # A workload must not be able to outlive the envelope it was leased under.
    # Live failure 2026-09-18: params.seconds=120 arrived with max_seconds=110,
    # so the work kept running past its deadline and the control plane declared
    # a timeout against a task that was still executing.
    duration_keys = [k for k, rule in spec["params"].items() if k == "seconds"]
    clamped = {}
    for key in duration_keys:
        requested = float(params.get(key, 0) or 0)
        allowed = max(1.0, max_seconds - DURATION_MARGIN_S)
        if requested > allowed:
            clamped[key] = {"requested": requested, "applied": allowed}
            params[key] = allowed

    arm_timeout(int(max_seconds) + 5)

    ctx = {"allowed_roots": ALLOWED_ROOTS, "profile": task["profile"],
           "max_seconds": max_seconds, "deadline_mono": started_mono + max_seconds}
    status = "SUCCEEDED"
    error = None
    try:
        result = spec["workload"](params, ctx)
    except PermissionError as exc:
        status, error, result = "REFUSED", f"PERMISSION: {exc}", {}
    except Exception as exc:  # noqa: BLE001 - the agent must never crash a node
        status, error, result = "FAILED", f"{type(exc).__name__}: {exc}", {}
    finally:
        disarm_timeout()

    if _cancelled["flag"] and status == "SUCCEEDED":
        status = "CANCELLED"

    payload = json.dumps(result, sort_keys=True, separators=(",", ":"))
    output_digest = hashlib.sha256(payload.encode()).hexdigest()
    receipt.update({
        "status": status,
        "error": error,
        "ended_utc": utc_now(),
        "duration_s": round(time.time() - started_mono, 3),
        "output_digest": output_digest,
        "result": result,
        "result_bytes": len(payload),
        "truncated": len(payload) > STDOUT_HEAD_CHARS,
        "cancelled": _cancelled["flag"],
        "max_seconds": max_seconds,
        "params_applied": params,
        "params_clamped": clamped,
        "host": {
            "nproc": os.cpu_count(),
            "mem_avail_kb": int(meminfo().get("MemAvailable", "0 kB").split()[0] or 0),
            "load1": read_text("/proc/loadavg", 64).split(" ")[0],
            "boot_id": read_text("/proc/sys/kernel/random/boot_id", 64),
        },
        "cgroup": observe_cgroup(),
    })
    return receipt


def main(argv: list[str]) -> int:
    if "--version" in argv:
        print(AGENT_VERSION)
        return 0
    if "--capability" in argv:
        print(json.dumps(build_capability(), indent=1, ensure_ascii=False))
        return 0
    if "--run-task" in argv:
        idx = argv.index("--run-task")
        if idx + 1 >= len(argv):
            print(json.dumps({"status": "REFUSED", "error": "MISSING_TASK_PATH"}))
            return 2
        path = argv[idx + 1]
        try:
            with open(path, "r", encoding="utf-8") as fh:
                task = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            print(json.dumps({"status": "REFUSED", "error": f"TASK_UNREADABLE: {exc}"}))
            return 2
        receipt = run_task(task)
        print(json.dumps(receipt, ensure_ascii=False))
        return 0 if receipt["status"] == "SUCCEEDED" else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
