"""Machine-written self-model producer — the organ that was specced, never coded.

Implements the population half of ``docs/octopus-surgery/04-SELF-MODEL-SPEC.md``
(schema ``octopus.self-model.v2``): every value in the output is observed at
runtime from this host and this checkout, or is explicitly absent/unknown with
its measurement source recorded. Nothing in the artifact is hand-written —
running this module is the artifact's only birth mechanism.

Real producers wired here:

* code identity + recent events — this checkout's git (``git:HEAD``, ``git:log``)
* member process liveness — loopback TCP connects to the Day-7 board ports;
  on a dev host these are measured ABSENT (they live on the board, not here),
  which is a verified negative, not a fault
* capabilities — an AST scan of the registry below (file + symbol present)
* brain-probe run evidence — dated receipt files; absent here means the
  verdict fails closed to unknown, never healthy

Every producer is injectable so tests can drive the honest paths (absent,
inconclusive, malformed) without faking reality.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from ofn.kernel import self_model
from ofn.kernel.self_model import Reading

SCHEMA_ID = "octopus.self-model.v3"

# GOV ruling V2 (2026-09-03): probe the REAL always-on board services instead
# of the dead 877x loopback ports of the previous architecture (those sockets
# never existed on board138 — the old map read permanently absent).
# The timer-driven oneshots (heartbeat/imap/quote) are deliberately not listed:
# "inactive" is their normal between-runs state, so is-active would misreport;
# their health surfaces via the heartbeat pulse and imap events.
MEMBER_UNITS: dict[str, str] = {
    "bridge": "octopus-bridge.service",
    "control_router": "octopus-control-router.service",
    "cycle_settler": "octopus-cycle-settler.service",
    "router": "octopus-router.service",
    "supervisor": "octopus-supervisor.service",
    "verify_dispatcher": "octopus-verify-dispatcher.service",
}

# kept for hosts/colour checks that still want a raw loopback probe
PORT_TIMEOUT_SECONDS = 0.25
GIT_TIMEOUT_SECONDS = 10.0
EVENT_LIMIT = 5

FRESHNESS_SECONDS = {
    "sensor": 300,
    "process": 180,
    "event": 900,
    "probe": 3600,
}

# name -> (module path inside the repo, symbol that must be defined in it).
# A capability is present only if the code that provides it is in this
# checkout; a doc that mentions it is not a capability.
CAPABILITIES: tuple[tuple[str, str, str | None], ...] = (
    ("task_envelope", "ofn/kernel/envelope.py", "create_envelope"),
    ("halt_layer3", "ofn/kernel/halt.py", None),
    ("token_ceiling", "ofn/kernel/token_ceiling.py", None),
    ("source_health", "ofn/kernel/source_health.py", None),
    ("run_store", "ofn/adapters/run_store.py", None),
    ("run_gate", "ofn/adapters/run_gate.py", None),
    ("halt_flag_adapter", "ofn/adapters/halt_flag.py", None),
    ("remote_brain", "ofn/adapters/remote_brain.py", "RemoteBrain"),
    ("local_brain", "ofn/adapters/remote_brain.py", "LocalBrain"),
    ("known_answer_probe", "ofn/kernel/probe.py", "QUESTIONS"),
    ("cockpit_read_model", "ofn/adapters/cockpit_v2_read_model.py",
     "CockpitV2ReadModel"),
    ("sender_dryrun", "ofn/adapters/sender_dryrun.py", None),
    ("self_model", "ofn/kernel/self_model.py", "build_model"),
)

AUTHORITY = {
    "may_propose": True,
    "may_approve": False,
    "may_execute": False,
    "direct_handles": [],
}

BUDGETS = {
    "network_write": 0,
    "external_effects": 0,
    "new_runtime_dependencies": 0,
}

# Where dated brain-probe run evidence would live if any existed on this
# host. Receipts elsewhere (the board) are not visible from here and are
# therefore not claimed.
PROBE_EVIDENCE_GLOBS = (
    "docs/octopus-surgery/receipts/BRAIN-PROBE-*.json",
    "state/self-model/brain-probe-receipt.json",
)

GitRunner = Callable[..., "str | None"]
PortProber = Callable[[str, int, float], "tuple[bool | None, str]"]
UnitProber = Callable[[str], "tuple[bool | None, str]"]


def rfc3339(epoch: float) -> str:
    return (
        datetime.fromtimestamp(float(epoch), tz=timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def default_clock() -> float:
    return time.time()


def run_git(repo_root: Path, *args: str) -> str | None:
    """One git invocation. Any failure returns None — the reading that
    depends on it becomes unknown, never a guess."""
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout


def probe_unit(unit: str) -> tuple[bool | None, str]:
    """systemd is-active measurement with the three-way honest split.

    active -> (True, ...) measured alive. inactive/failed -> (False, ...)
    measured absent. No systemctl (dev hosts) or any error -> (None, ...)
    inconclusive: an unanswered question, never a guessed colour.
    """
    if shutil.which("systemctl") is None:
        return None, "systemctl unavailable"
    try:
        quiet = subprocess.run(
            ["systemctl", "is-active", "--quiet", unit],
            capture_output=True, text=True, timeout=5)
        if quiet.returncode == 0:
            return True, "active"
        state = subprocess.run(
            ["systemctl", "is-active", unit],
            capture_output=True, text=True, timeout=5)
        return False, (state.stdout.strip() or "inactive")
    except (OSError, subprocess.SubprocessError) as error:
        return None, f"probe error: {type(error).__name__}"


def probe_port(host: str, port: int, timeout: float) -> tuple[bool | None, str]:
    """Loopback liveness measurement with the three-way honest split.

    Connected -> (True, ...) measured alive. Refused -> (False, ...)
    measured absent. Timeout / other error -> (None, ...) inconclusive:
    an unanswered question, not a negative.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, "connected"
    except (ConnectionRefusedError, ConnectionResetError) as error:
        # On loopback both mean nothing is listening: a measured negative.
        # (Windows raises ConnectionResetError where Unix refuses.)
        reason = ("refused" if isinstance(error, ConnectionRefusedError)
                  else "reset")
        return False, f"connection {reason}"
    except (socket.timeout, TimeoutError):
        return None, "probe timeout"
    except OSError as error:
        return None, f"probe error: {type(error).__name__}"


def _symbol_present(source: str, symbol: str) -> bool:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)) and node.name == symbol:
            return True
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target] if node.target else []
        if any(isinstance(target, ast.Name) and target.id == symbol
               for target in targets):
            return True
    return False


def check_capability(repo_root: Path, module_path: str,
                     symbol: str | None) -> bool | None:
    """File-and-symbol presence check. A module that is not in this
    checkout is a verified absence (False). A module that exists but
    cannot be read is unknown (None) — the check failed, the capability
    was not measured absent."""
    candidate = repo_root / Path(module_path)
    try:
        if not candidate.exists():
            return False
        source = candidate.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    if symbol is None:
        return True
    return _symbol_present(source, symbol)


def _collect_code_identity(repo_root: Path, git_runner: GitRunner,
                           now_epoch: float) -> tuple[dict[str, Any], Reading]:
    head = git_runner(repo_root, "rev-parse", "HEAD")
    branch = git_runner(repo_root, "branch", "--show-current")
    identity: dict[str, Any] = {
        "commit_sha": head.strip() if head else None,
        "branch": branch.strip() if branch and branch.strip() else None,
    }
    if head:
        reading = Reading(
            sensor_id="code_identity",
            implementation="git rev-parse HEAD",
            status=self_model.HEALTHY,
            value=identity["commit_sha"],
            source="git:HEAD",
            observed_epoch=now_epoch,
        )
    else:
        reading = Reading(
            sensor_id="code_identity",
            implementation="git rev-parse HEAD",
            status=self_model.UNKNOWN,
            value=None,
            source="git:HEAD",
            observed_epoch=None,
            detail="git identity unavailable",
        )
    return identity, reading


def _collect_processes(
    units: Mapping[str, str],
    now_epoch: float,
    prober: UnitProber,
) -> list[Reading]:
    readings = []
    for member, unit in sorted(units.items()):
        alive, detail = prober(unit)
        readings.append(
            self_model.process_reading(
                sensor_id=f"process_{member}",
                implementation=f"systemctl is-active {unit}",
                alive=alive,
                observed_epoch=now_epoch,
                source=f"unit:{unit}",
                detail=detail,
            )
        )
    return readings


def _collect_capabilities(repo_root: Path) -> list[Reading]:
    readings = []
    for name, module_path, symbol in CAPABILITIES:
        present = check_capability(repo_root, module_path, symbol)
        readings.append(
            self_model.capability_reading(
                sensor_id=f"capability_{name}",
                implementation=module_path + (
                    f"::{symbol}" if symbol else ""),
                present=present,
                source=f"ast:{module_path}",
            )
        )
    return readings


def _collect_events(repo_root: Path, git_runner: GitRunner,
                    limit: int) -> list[dict[str, Any]]:
    output = git_runner(
        repo_root, "log", f"-{limit}", "--format=%H%x1f%ct%x1f%s")
    events: list[dict[str, Any]] = []
    if not output:
        return events
    for line in output.strip().splitlines():
        parts = line.split("\x1f")
        if len(parts) != 3:
            continue
        sha, stamp, subject = parts
        try:
            epoch = float(stamp)
        except ValueError:
            continue
        events.append({
            "sha": sha,
            "at_epoch": epoch,
            "at": rfc3339(epoch),
            "subject": subject,
            "source": "git:log",
        })
    return events


def _collect_brain_probe(repo_root: Path,
                         now_epoch: float) -> dict[str, Any]:
    """Dated run evidence only. No evidence -> fail-closed unknown."""
    evidence_epoch: float | None = None
    evidence_source: str | None = None
    for pattern in PROBE_EVIDENCE_GLOBS:
        candidates = sorted(repo_root.glob(pattern))
        if not candidates:
            continue
        newest = candidates[-1]
        try:
            evidence_epoch = newest.stat().st_mtime
        except OSError:
            continue
        evidence_source = f"fs:{newest.relative_to(repo_root).as_posix()}"
        break
    return self_model.brain_probe_verdict(
        evidence_epoch, evidence_source, now_epoch,
        FRESHNESS_SECONDS["probe"],
    )


def produce(
    *,
    clock: Callable[[], float] | None = None,
    repo_root: Path | str | None = None,
    units: Mapping[str, str] | None = None,
    git_runner: GitRunner | None = None,
    unit_prober: UnitProber | None = None,
) -> dict[str, Any]:
    """Generate the self-model envelope from real (or injected) producers."""
    now_epoch = (clock or default_clock)()
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[2]
    repo_root = Path(repo_root)
    if git_runner is None:
        git_runner = run_git
    if unit_prober is None:
        unit_prober = probe_unit
    if units is None:
        units = MEMBER_UNITS

    identity, identity_reading = _collect_code_identity(
        repo_root, git_runner, now_epoch)
    processes = _collect_processes(units, now_epoch, unit_prober)
    capabilities = _collect_capabilities(repo_root)
    events = _collect_events(repo_root, git_runner, EVENT_LIMIT)
    brain_probe = _collect_brain_probe(repo_root, now_epoch)

    model = self_model.build_model(
        code_identity=identity,
        sensors=[identity_reading],
        processes=processes,
        capabilities=capabilities,
        events=events,
        brain_probe=brain_probe,
        authority=dict(AUTHORITY),
        budgets=dict(BUDGETS),
        unknowns=[
            "member service liveness is read via systemctl on this host; "
            "without systemd (dev machines) it stays unknown, never green",
            "no dated brain-probe run evidence exists on this host; the "
            "probe verdict fails closed until one does",
        ],
    )
    warnings = [
        f"{reading['sensor_id']}_{reading['status']}"
        for group in ("sensors", "processes", "capabilities")
        for reading in model[group]
        if reading["status"] != self_model.HEALTHY
    ]
    if model["brain_probe"]["status"] != self_model.HEALTHY:
        warnings.append("brain_probe_" + model["brain_probe"]["status"])
    stale_after = rfc3339(
        now_epoch + min(FRESHNESS_SECONDS.values()))
    return {
        "schema": SCHEMA_ID,
        "generated_at": rfc3339(now_epoch),
        "generated_epoch": now_epoch,
        "status": model["status"],
        "data": model,
        "sources": sorted({
            reading["source"]
            for group in ("sensors", "processes", "capabilities")
            for reading in model[group]
            if reading["source"]
        }),
        "warnings": sorted(warnings),
        "stale_after": stale_after,
    }


def semantic_digest(envelope: Mapping[str, Any]) -> str:
    """sha256 over the model with generation time excluded — the same
    system state must digest identically no matter when it was read."""
    payload = {
        key: value
        for key, value in envelope.items()
        if key not in {"generated_at", "generated_epoch"}
    }
    body = json.dumps(
        payload, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def write_artifact(envelope: Mapping[str, Any], path: Path | str) -> tuple[str, str]:
    """Write the artifact atomically. Returns (posix path, sha256)."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(
        envelope, ensure_ascii=False, sort_keys=True, indent=2,
        allow_nan=False).encode("utf-8") + b"\n"
    digest = hashlib.sha256(body).hexdigest()
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_bytes(body)
    os.replace(temporary, target)
    return target.as_posix(), digest


def summary_line(envelope: Mapping[str, Any]) -> str:
    counts = envelope["data"]["counts"]
    identity = envelope["data"]["code_identity"]
    return (
        f"self-model status={envelope['status']} "
        f"commit={identity.get('commit_sha') or 'unknown'} "
        f"sensors={counts['sensors']} processes={counts['processes']} "
        f"capabilities={counts['capabilities']} "
        f"healthy={counts['healthy']} absent={counts['absent']} "
        f"stale={counts['stale']} failed={counts['failed']} "
        f"unknown={counts['unknown']}"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate the machine-written system self-model.")
    parser.add_argument("--repo", default=".")
    parser.add_argument(
        "--output",
        default=None,
        help="artifact path (default <repo>/state/self-model/SYSTEM-SELF-MODEL.json)",
    )
    args = parser.parse_args(argv)
    repo_root = Path(args.repo).resolve()
    output = Path(args.output) if args.output else (
        repo_root / "state" / "self-model" / "SYSTEM-SELF-MODEL.json")

    envelope = produce(repo_root=repo_root)
    path, digest = write_artifact(envelope, output)
    print(summary_line(envelope))
    print(f"artifact={path}")
    print(f"sha256={digest}")
    print(f"semantic_digest={semantic_digest(envelope)}")
    print(f"generated_at={envelope['generated_at']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
