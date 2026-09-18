#!/usr/bin/env python3
"""FLEET COMPUTE — control-plane scheduler cycle.

One cycle:
  1. probe telemetry from every configured node (read-only, nonce-verified)
  2. reclaim leases that expired (reboot / partition safety)
  3. evaluate admission for each node and pick a placement
  4. shadow mode: record the decision and dispatch nothing
     canary mode: lease, push a validated task envelope, run it under cgroup
     limits, verify the receipt, settle exactly once
  5. refresh the cockpit read model

Modes are deliberately explicit. Shadow is the default and refuses to execute
anything, because the scan's Phase 1 requires placement decisions to be
comparable against observed headroom before any real load exists.

python3 standard library only.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import compute_core as cc  # noqa: E402
import fleet_probe as fp  # noqa: E402

CONTROL_STATE = Path("/home/ari/ofn/state/fleet-compute")
CONFIG_PATH = HERE / "compute_config.json"
AGENT_PATH = "/usr/local/bin/compute_worker.py"
REMOTE_WORK_ROOT = "/var/lib/octopus-compute"

DEFAULT_CONFIG = {
    "schema": "compute_config.v1",
    "mode": "shadow",
    "ssh_key": "octopus_mesh_ed25519",
    "agent_path": AGENT_PATH,
    "work_root": REMOTE_WORK_ROOT,
    "nodes": [],
    "policy": dict(cc.DEFAULT_POLICY),
    "cgroup": {
        "CPUQuota": "50%",
        "CPUWeight": "50",
        "MemoryMax": "512M",
        "MemoryHigh": "384M",
        "IOWeight": "50",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def load_config(path: Path) -> dict:
    if not path.exists():
        return dict(DEFAULT_CONFIG)
    cfg = json.loads(path.read_text(encoding="utf-8"))
    merged = dict(DEFAULT_CONFIG)
    merged.update(cfg)
    merged["policy"] = {**DEFAULT_CONFIG["policy"], **cfg.get("policy", {})}
    return merged


def ssh(host: str, key: str, cmd: str, timeout: int = 60, stdin_data: str | None = None):
    key_path = Path.home() / ".ssh" / key
    full = [
        "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
        "-o", f"ConnectTimeout=8", "-i", str(key_path), host, cmd,
    ]
    try:
        proc = subprocess.run(
            full, capture_output=True, text=True, timeout=timeout,
            input=stdin_data, stdin=None if stdin_data is not None else subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return 124, "", "ssh_timeout"
    return proc.returncode, proc.stdout or "", proc.stderr or ""


# --------------------------------------------------------------------------
# Phase 1: telemetry + capability
# --------------------------------------------------------------------------

def collect_telemetry(cfg: dict) -> dict:
    """Nonce-verified read-only telemetry for every configured node."""
    import secrets
    nonce = secrets.token_hex(8)
    round_id = secrets.token_hex(6)
    key_path = str(Path.home() / ".ssh" / cfg["ssh_key"])
    out = {}
    for node in cfg["nodes"]:
        rec = fp.probe_node(node, nonce, round_id, key_path=key_path)
        out[node["id"]] = rec
    return out


def collect_capability(cfg: dict, node: dict) -> dict | None:
    """Read the worker's own capability record. None if the agent is absent."""
    rc, out, _ = ssh(node["ssh"], cfg["ssh_key"],
                     f"python3 {cfg['agent_path']} --capability", timeout=25)
    if rc != 0 or not out.strip():
        return None
    try:
        return json.loads(out[out.index("{"):])
    except (ValueError, json.JSONDecodeError):
        return None


# --------------------------------------------------------------------------
# Phase 2: dispatch (canary and beyond)
# --------------------------------------------------------------------------

def push_task(cfg: dict, node: dict, envelope: dict) -> tuple[bool, str, str]:
    """Write a task envelope to the worker, verifying the digest on arrival.

    The envelope is data. The only thing that ever reaches a shell from the
    control plane is a path derived from the task id.
    """
    payload = json.dumps(envelope, sort_keys=True, separators=(",", ":"))
    digest = cc.sha(envelope)
    remote_path = f"{cfg['work_root']}/tasks/{envelope['task_id']}.json"
    cmd = (
        f"mkdir -p {cfg['work_root']}/tasks && "
        f"cat > {remote_path} && sha256sum {remote_path} | cut -d' ' -f1"
    )
    rc, out, err = ssh(node["ssh"], cfg["ssh_key"], cmd, timeout=30, stdin_data=payload)
    if rc != 0:
        return False, "", f"push_failed rc={rc} {err[:200]}"
    arrived = out.strip().splitlines()[-1].strip() if out.strip() else ""
    if arrived != digest:
        return False, remote_path, f"digest_mismatch local={digest[:12]} remote={arrived[:12]}"
    return True, remote_path, ""


def unit_name(task_id: str, attempt: int) -> str:
    """Deterministic per-attempt scope name.

    Per-attempt on purpose: a retry of the same task must not collide with a
    scope that is still loaded from the previous attempt. Observed live on
    2026-09-18 — a retry failed with "Unit ... was already loaded or has a
    fragment file" because the unit name was derived from the task id alone.
    Deterministic on purpose: the reclaim path can recompute it to stop a scope
    left behind by a task whose lease expired.
    """
    return f"octopus-compute-{task_id.split('-')[-1][:12]}-a{attempt}"


def stop_scope(cfg: dict, node: dict, unit: str) -> None:
    """Best-effort teardown of a scope. Never raises into the caller.

    A scope that outlives its lease is exactly the runaway the scan says must
    not happen, so every failure path calls this before giving up on a task.
    """
    try:
        ssh(node["ssh"], cfg["ssh_key"], f"systemctl stop {unit} --no-block 2>/dev/null || true",
            timeout=20)
    except Exception:  # noqa: BLE001
        pass


def run_under_cgroup(cfg: dict, node: dict, unit: str, remote_path: str, timeout: int):
    """Execute the agent inside a transient scope with real resource limits."""
    props = " ".join(f"-p {k}={v}" for k, v in cfg["cgroup"].items())
    cmd = (
        f"systemd-run --scope --collect --unit={unit} {props} -- "
        f"python3 {cfg['agent_path']} --run-task {remote_path}"
    )
    return ssh(node["ssh"], cfg["ssh_key"], cmd, timeout=timeout)


def parse_receipt(stdout: str) -> dict | None:
    """The receipt is the last JSON object the agent printed."""
    for line in reversed(stdout.strip().splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return None


def _parse_size(text: str) -> int | None:
    """systemd size property -> bytes (512M, 384M, 1G, plain bytes)."""
    text = text.strip()
    if not text:
        return None
    mult = 1
    if text[-1] in "KMGTP":
        mult = {"K": 1024, "M": 1024 ** 2, "G": 1024 ** 3, "T": 1024 ** 4, "P": 1024 ** 5}[text[-1]]
        text = text[:-1]
    try:
        return int(float(text) * mult)
    except ValueError:
        return None


def expected_cgroup_limits(cfg: dict) -> dict:
    """Translate the requested systemd properties into cgroup v2 file values."""
    want = {}
    quota = cfg["cgroup"].get("CPUQuota", "").strip()
    if quota.endswith("%"):
        try:
            # CPUQuota is a share of ONE cpu; cgroup v2 expresses it over a 100ms period.
            want["cpu_max"] = f"{int(float(quota[:-1]) * 1000)} 100000"
        except ValueError:
            pass
    weight = cfg["cgroup"].get("CPUWeight")
    if weight is not None:
        want["cpu_weight"] = str(weight)
    for prop, key in (("MemoryMax", "memory_max"), ("MemoryHigh", "memory_high")):
        if cfg["cgroup"].get(prop):
            size = _parse_size(cfg["cgroup"][prop])
            if size is not None:
                want[key] = str(size)
    return want


def verify_cgroup(observed: dict, cfg: dict) -> dict:
    """Did the envelope actually get applied to the process that ran?

    Without this the receipt proves only that a scope existed. A run whose
    limits cannot be confirmed is treated as unbounded, which is exactly the
    case the scan says must never be trusted on a shared board.
    """
    want = expected_cgroup_limits(cfg)
    checks, mismatches, unknown = {}, [], []
    for key, expected in sorted(want.items()):
        got = observed.get(key)
        if got is None:
            unknown.append(key)
        elif str(got).strip() == expected:
            checks[key] = expected
        else:
            mismatches.append(f"{key}: want={expected} got={str(got).strip()}")
    if mismatches:
        verdict = "MISMATCH"
    elif unknown:
        verdict = "UNVERIFIED"
    else:
        verdict = "VERIFIED" if checks else "UNVERIFIED"
    return {"verdict": verdict, "expected": want, "observed": observed,
            "mismatches": mismatches, "unknown": unknown}


def dispatch(store: cc.Store, cfg: dict, task: dict, node: dict, decisions_path: Path) -> dict:
    lease_seconds = int(cfg["policy"]["lease_seconds"])
    claimed = store.claim(task["task_id"], node["id"], lease_seconds=lease_seconds)
    if not claimed["ok"]:
        return {"ok": False, "error": claimed["error"]}

    envelope = {
        "schema": "compute_task.v1",
        "task_id": task["task_id"],
        "profile": task["profile"],
        "params": json.loads(task["params_json"]),
        "input_digest": task["input_digest"],
        "resource_class": task["resource_class"],
        "max_seconds": min(lease_seconds - 10, 120) if lease_seconds > 20 else 20,
        "external_effects": 0,
        "customer_send": False,
        "commander_node_id": cfg.get("commander_node_id", "138"),
    }

    attempt_next = int(task["attempt"]) + 1
    unit = unit_name(task["task_id"], attempt_next)

    # Insurance against a scope left loaded by a previous attempt.
    stop_scope(cfg, node, unit)

    ok, remote_path, err = push_task(cfg, node, envelope)
    if not ok:
        store.fail(task["task_id"], error=f"push:{err}", retryable=True)
        return {"ok": False, "error": err}

    store.start(task["task_id"])
    # Patience must exceed the envelope, not the other way round: the earlier
    # 45 s margin was shorter than the workload's own overrun.
    patience = int(envelope["max_seconds"]) + 60
    rc, out, errout = run_under_cgroup(cfg, node, unit, remote_path, timeout=patience)
    receipt = parse_receipt(out)
    cgroup_check = verify_cgroup((receipt or {}).get("cgroup", {}) if receipt else {}, cfg)
    log_jsonl(decisions_path.parent / "receipts.jsonl", {
        "schema": "compute_dispatch.v1", "at_utc": utc_now(),
        "task_id": task["task_id"], "node_id": node["id"], "unit": unit, "rc": rc,
        "receipt": receipt, "cgroup_envelope": cgroup_check,
        "stderr_head": errout[:300],
    })
    if receipt is None:
        # Whatever the cause, nothing may keep running once we stop listening.
        stop_scope(cfg, node, unit)
        store.fail(task["task_id"], error=f"no_receipt rc={rc} {errout[:200]}", retryable=True)
        return {"ok": False, "error": "no_receipt", "rc": rc, "unit": unit}

    # Fail closed on an unproven envelope: work that was not actually capped
    # must not be allowed to continue on a shared board.
    if cgroup_check["verdict"] == "MISMATCH":
        stop_scope(cfg, node, unit)
        store.fail(task["task_id"],
                   error=f"cgroup_envelope_mismatch: {'; '.join(cgroup_check['mismatches'])[:200]}",
                   retryable=False)
        return {"ok": False, "error": "cgroup_envelope_mismatch",
                "detail": cgroup_check["mismatches"]}

    if receipt.get("status") != "SUCCEEDED":
        # A refusal is a contract problem, not a transient fault: do not retry it.
        retryable = receipt.get("status") not in ("REFUSED",)
        store.fail(task["task_id"], error=f"{receipt.get('status')}:{receipt.get('error')}",
                   retryable=retryable)
        return {"ok": False, "error": receipt.get("error"), "status": receipt.get("status")}

    if receipt.get("input_digest") != task["input_digest"]:
        store.fail(task["task_id"], error="input_digest_mismatch", retryable=False)
        return {"ok": False, "error": "input_digest_mismatch"}

    settled = store.succeed(
        task["task_id"],
        output_digest=receipt.get("output_digest", ""),
        result=receipt.get("result", {}),
    )
    return {"ok": True, "status": "SUCCEEDED", "duplicate": settled.get("duplicate", False),
            "output_digest": receipt.get("output_digest", "")[:16],
            "cgroup_envelope": cgroup_check["verdict"],
            "duration_s": receipt.get("duration_s")}


# --------------------------------------------------------------------------
# Cycle
# --------------------------------------------------------------------------

def cycle(store: cc.Store, cfg: dict, state_dir: Path, *, arrival: dict | None = None) -> dict:
    """One control-plane cycle.

    `arrival` describes a would-be task. In shadow mode it is never written to
    the durable queue: Phase 1 exists to record placement decisions, and a
    queue that silently accumulated hundreds of never-dispatched tasks would
    all fire at once the moment the mode flips to canary.
    """
    decisions_path = state_dir / "decisions.jsonl"
    paused = (state_dir / "OWNER_PAUSE").exists()

    reclaimed = store.reclaim_expired()
    # A reclaimed lease means the worker is gone, hung, or partitioned. Stop its
    # scope so a task whose lease expired cannot keep burning CPU on the board.
    for row in reclaimed:
        node_cfg = next((n for n in cfg["nodes"] if n["id"] == row.get("node_id")), None)
        if node_cfg and row.get("task_id"):
            stop_scope(cfg, node_cfg, unit_name(row["task_id"], int(row.get("attempt") or 1)))

    shadow = cfg["mode"] == "shadow"
    if arrival and not shadow:
        store.enqueue(
            profile=arrival["profile"], params=arrival["params"],
            input_digest=arrival["input_digest"],
            idempotency_key=arrival["idempotency_key"],
            resource_class=arrival.get("resource_class", "cpu_batch"),
            max_attempts=arrival.get("max_attempts", 2),
        )

    telemetry = collect_telemetry(cfg)
    failures = {}
    for row in store.db.execute(
        "SELECT worker_node_id, COUNT(*) c FROM tasks WHERE state='FAILED_FINAL' "
        "AND worker_node_id IS NOT NULL GROUP BY worker_node_id"
    ).fetchall():
        failures[row["worker_node_id"]] = row["c"]

    # Capability records are read on every cycle: placement must be driven by
    # what a node reports it can run, not by its hostname.
    capabilities = {n["id"]: collect_capability(cfg, n) for n in cfg["nodes"]}

    candidates = [
        {
            "node_id": n["id"],
            "telemetry": telemetry.get(n["id"]),
            "failure_count": failures.get(n["id"], 0),
            "capability": capabilities.get(n["id"]),
        }
        for n in cfg["nodes"]
    ]

    policy = dict(cfg["policy"])
    if paused:
        policy["allowed_nodes"] = []
    require_capability = cfg["mode"] in ("canary", "active")
    placement = cc.select_placement(candidates, policy, require_capability=require_capability)

    queued = store.by_state("QUEUED", limit=1)
    task = queued[0] if queued else None

    decision = {
        "schema": "compute_decision.v1",
        "at_utc": utc_now(),
        "mode": cfg["mode"],
        "owner_pause": paused,
        "reclaimed_leases": reclaimed,
        "queued_task": task["task_id"] if task else None,
        "profile": task["profile"] if task else (arrival["profile"] if arrival else None),
        "synthetic_arrival": (
            {"profile": arrival["profile"], "params": arrival["params"],
             "input_digest": arrival["input_digest"], "idempotency_key": arrival["idempotency_key"],
             "enqueued": not shadow}
            if arrival else None
        ),
        "chosen_node": placement["chosen"]["node_id"] if placement["chosen"] else None,
        "chosen_score": placement["chosen"]["score"] if placement["chosen"] else None,
        "reason": placement["reason"],
        "evaluated": [
            {"node_id": e["node_id"], "admit": e["admit"], "verdict": e["verdict"],
             "reasons": e["reasons"], "score": e["score"], "capable": e.get("capable"),
             "headroom": e.get("headroom")}
            for e in placement["evaluated"]
        ],
    }

    result = {"decision": decision, "dispatched": None}
    if not shadow and cfg["mode"] in ("canary", "active") and task and placement["chosen"]:
        node_cfg = next(n for n in cfg["nodes"] if n["id"] == placement["chosen"]["node_id"])
        result["dispatched"] = dispatch(store, cfg, task, node_cfg, decisions_path)
    elif not shadow and task and not placement["chosen"]:
        store.park(task["task_id"], reason=placement["reason"] or "no_placement")

    log_jsonl(decisions_path, decision)
    write_cockpit(store, cfg, telemetry, decision, state_dir)
    return result


def write_cockpit(store: cc.Store, cfg: dict, telemetry: dict, decision: dict, state_dir: Path) -> None:
    nodes = []
    by_id = {e["node_id"]: e for e in decision["evaluated"]}
    for n in cfg["nodes"]:
        t = telemetry.get(n["id"], {}) or {}
        verdict = by_id.get(n["id"], {})
        nodes.append({
            "node_id": n["id"],
            "admit": verdict.get("admit"),
            "verdict": verdict.get("verdict"),
            "reasons": verdict.get("reasons", []),
            "score": verdict.get("score"),
            "cpu_pct": t.get("cpu_pct"),
            "load1": t.get("load1"),
            "hottest_c": round((t.get("hottest_millic") or 0) / 1000.0, 1) if t.get("hottest_millic") else None,
            "mem_used_pct": t.get("mem_used_pct"),
            "disk_used_pct": t.get("disk_root_used_pct"),
            "telemetry_age_s": _age(t.get("node_utc")),
            "ssh_rtt_s": t.get("ssh_rtt_s"),
            "liveness_proven": t.get("liveness_proven"),
            "boot_id": (t.get("boot_id") or "")[:8],
        })
    cockpit = {
        "schema": "compute_cockpit.v1",
        "at_utc": utc_now(),
        "mode": cfg["mode"],
        "owner_pause": decision["owner_pause"],
        "queue": store.stats(),
        "nodes": nodes,
        "last_decision": {
            "chosen_node": decision["chosen_node"],
            "reason": decision["reason"],
            "at_utc": decision["at_utc"],
        },
    }
    (state_dir / "cockpit.json").write_text(
        json.dumps(cockpit, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )


def _age(stamp: str | None) -> float | None:
    if not stamp:
        return None
    try:
        return round((datetime.now(timezone.utc) - cc.parse_utc(stamp)).total_seconds(), 1)
    except ValueError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(CONFIG_PATH))
    ap.add_argument("--state", default=str(CONTROL_STATE))
    ap.add_argument("--enqueue-profile")
    ap.add_argument("--enqueue-params", default="{}")
    ap.add_argument("--enqueue-key")
    ap.add_argument("--auto-enqueue", action="store_true",
                    help="enqueue one synthetic task per cycle (shadow workload arrival)")
    ap.add_argument("--auto-profile", default="cpu_bench")
    ap.add_argument("--auto-params", default="{}")
    ap.add_argument("--auto-seconds", type=int, help="shorthand for auto params seconds=N")
    ap.add_argument("--cgroup-quota", help="override CPUQuota for this run (e.g. 200%%)")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--interval", type=float, default=60.0)
    ap.add_argument("--duration", type=float, default=0.0, help="minutes; 0 = forever")
    ap.add_argument("--dry-run", action="store_true", help="force shadow mode for this run")
    args = ap.parse_args()

    cfg = load_config(Path(args.config))
    if args.dry_run:
        cfg["mode"] = "shadow"
    if args.cgroup_quota:
        cfg["cgroup"]["CPUQuota"] = args.cgroup_quota
    state_dir = Path(args.state)
    state_dir.mkdir(parents=True, exist_ok=True)
    store = cc.Store(state_dir / "compute_tasks.db")

    def build_arrival() -> dict | None:
        """A would-be task for this cycle: explicit CLI request, or the auto arrival."""
        if args.enqueue_profile and args.enqueue_key:
            params = json.loads(args.enqueue_params)
            return {
                "profile": args.enqueue_profile,
                "params": params,
                "input_digest": cc.sha({"profile": args.enqueue_profile, "params": params}),
                "idempotency_key": args.enqueue_key,
            }
        if not args.auto_enqueue:
            return None
        params = json.loads(args.auto_params)
        if args.auto_seconds:
            params["seconds"] = args.auto_seconds
        stamp = utc_now()
        return {
            "profile": args.auto_profile,
            "params": params,
            "input_digest": cc.sha({"profile": args.auto_profile, "params": params}),
            # An explicit --enqueue-key wins; otherwise the arrival is keyed by
            # its UTC second so a retry of the same cycle dedupes.
            "idempotency_key": args.enqueue_key or f"auto-{args.auto_profile}-{stamp}",
        }

    if args.loop:
        deadline = time.time() + args.duration * 60 if args.duration else None
        n = 0
        while True:
            n += 1
            res = cycle(store, cfg, state_dir, arrival=build_arrival())
            d = res["decision"]
            print(f"[{d['at_utc']}] mode={d['mode']} chosen={d['chosen_node']} "
                  f"reason={d['reason']} dispatched={res['dispatched']}", flush=True)
            if deadline and time.time() + args.interval > deadline:
                break
            time.sleep(args.interval)
    else:
        res = cycle(store, cfg, state_dir, arrival=build_arrival())
        print(json.dumps(res, indent=1, ensure_ascii=False))
    store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
