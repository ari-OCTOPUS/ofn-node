#!/usr/bin/env python3
"""Exactly one owner-approved, 15-minute controlled local growth canary."""
from __future__ import annotations

import hashlib
import json
import os
import socket
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ofn.organism.cognition.active_inference import EXECUTABLE as AI_EXECUTABLE
from ofn.organism.growth.capabilities import (
    ACTIVE_INFERENCE_CAPABILITY,
    GATE_ID,
    INTERNAL_CAPABILITIES,
    REGISTRY_PATH,
    atomic_write_registry,
    load_registry,
    rollback_capabilities_to_tested,
    transition_capabilities,
    validate_registry,
)
from ofn.organism.growth.controlled import checkpoint_watcher_running
from ofn.organism.identity.ledger import verify_identity_chain
from ofn.organism.runtime.lan_auth import TOKEN_HEADER, load_lan_token
from ofn.organism.science.wbe_allometry import EXECUTABLE as WBE_EXECUTABLE


LAB = Path("/opt/octopus/lab")
DB = LAB / "lab-data/organism.db"
ART = LAB / "artifacts/capability-awakening"
GROWTH_RECEIPTS = ART / "06_growth_receipts.jsonl"
FINAL_RECEIPT = ART / "CONTROLLED_GROWTH_CANARY_RECEIPT.json"
SOAK_STATE = LAB / "evidence/SOAK-RESULTS.json"
DURATION_S = 15 * 60
POLL_S = 15
EXPERIMENTS = (
    "SELF_MODEL_GAP",
    "EPISODIC_CONSOLIDATION",
    "LOCAL_HYPOTHESIS",
)
ACTIVATABLE = tuple(
    item for item in INTERNAL_CAPABILITIES if item != ACTIVE_INFERENCE_CAPABILITY
)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(LAB), *args],
        text=True,
    ).strip()


def unit_show(unit: str) -> dict[str, str]:
    raw = subprocess.check_output(
        [
            "systemctl",
            "show",
            unit,
            "--property=MainPID,ActiveState,SubState,NRestarts,ExecMainStartTimestamp",
            "--no-pager",
        ],
        text=True,
    )
    output: dict[str, str] = {}
    for line in raw.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            output[key] = value
    return output


def ro() -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")
    return con


def db_snapshot(*, integrity: bool = False) -> dict[str, Any]:
    con = ro()
    try:
        identity = con.execute(
            "SELECT sequence,entry_hash FROM identity_ledger ORDER BY sequence DESC LIMIT 1"
        ).fetchone()
        event = con.execute(
            "SELECT node_seq,event_id,hash FROM events ORDER BY node_seq DESC LIMIT 1"
        ).fetchone()
        heartbeat = con.execute(
            """
            SELECT node_seq,event_id
            FROM events
            WHERE event_type='heartbeat'
            ORDER BY node_seq DESC
            LIMIT 1
            """
        ).fetchone()
        schema = con.execute(
            "SELECT v FROM meta WHERE k='schema_migration_version'"
        ).fetchone()
        interval = con.execute(
            "SELECT v FROM meta WHERE k='heartbeat_interval_s'"
        ).fetchone()
        snapshot = {
            "identity_head": {
                "sequence": 0 if not identity else int(identity[0]),
                "hash": None if not identity else identity[1],
            },
            "event_head": {
                "node_seq": 0 if not event else int(event[0]),
                "event_id": None if not event else event[1],
                "hash": None if not event else event[2],
            },
            "heartbeat_count": int(
                con.execute(
                    "SELECT COUNT(*) FROM events WHERE event_type='heartbeat'"
                ).fetchone()[0]
            ),
            "heartbeat_head_node_seq": 0 if not heartbeat else int(heartbeat[0]),
            "heartbeat_head_event_id": None if not heartbeat else heartbeat[1],
            "events": int(con.execute("SELECT COUNT(*) FROM events").fetchone()[0]),
            "episodes": int(con.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]),
            "memory_receipts": int(
                con.execute("SELECT COUNT(*) FROM memory_read_receipts").fetchone()[0]
            ),
            "decision_evidence": int(
                con.execute("SELECT COUNT(*) FROM decision_evidence").fetchone()[0]
            ),
            "self_model_version": int(
                con.execute("SELECT COALESCE(MAX(version),0) FROM self_models").fetchone()[0]
            ),
            "inner_speech": int(
                con.execute("SELECT COUNT(*) FROM inner_speech").fetchone()[0]
            ),
            "wan_fetches": int(
                con.execute("SELECT COUNT(*) FROM wan_fetches").fetchone()[0]
            ),
            "future_use_total": int(
                con.execute(
                    "SELECT COALESCE(SUM(future_use_count),0) "
                    "FROM memory_read_receipts"
                ).fetchone()[0]
            ),
            "evidence_executable_total": int(
                con.execute(
                    "SELECT COALESCE(SUM(executable),0) FROM decision_evidence"
                ).fetchone()[0]
            ),
            "schema": None if not schema else schema[0],
            "heartbeat_interval_s": None if not interval else interval[0],
            "quick_check": con.execute("PRAGMA quick_check").fetchone()[0],
        }
        if integrity:
            snapshot["integrity_check"] = con.execute(
                "PRAGMA integrity_check"
            ).fetchone()[0]
        identity_result = verify_identity_chain(con)
        snapshot["identity_valid"] = bool(identity_result.get("valid"))
        snapshot["identity_error"] = identity_result.get("error")
        return snapshot
    finally:
        con.close()


def heartbeat_ids_after(node_seq: int) -> list[str]:
    con = ro()
    try:
        return [
            str(row[0])
            for row in con.execute(
                """
                SELECT event_id
                FROM events
                WHERE event_type='heartbeat' AND node_seq>?
                ORDER BY node_seq
                """,
                (node_seq,),
            ).fetchall()
        ]
    finally:
        con.close()


def resource_state() -> dict[str, Any]:
    mem_available = -1
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        if line.startswith("MemAvailable:"):
            mem_available = int(line.split()[1])
            break
    stat = os.statvfs("/")
    available = stat.f_bavail * stat.f_frsize
    used_pct = 100.0 * (1.0 - stat.f_bavail / stat.f_blocks)
    temperature = int(
        Path("/sys/class/thermal/thermal_zone0/temp").read_text(encoding="utf-8").strip()
    )
    return {
        "ram_available_kib": mem_available,
        "disk_available_bytes": available,
        "disk_available_gib": round(available / 1024**3, 3),
        "disk_used_pct": round(used_pct, 2),
        "temperature_mC": temperature,
    }


def process_flags(pid: int) -> dict[str, str | None]:
    wanted = {
        "OCTOPUS_GET_PURE",
        "OCTOPUS_REQUIRE_LAN_TOKEN",
        "OCTOPUS_LEARN_EXTERNAL",
    }
    values = {key: None for key in wanted}
    try:
        raw = Path(f"/proc/{pid}/environ").read_bytes().split(bytes([0]))
    except OSError:
        return values
    for item in raw:
        if b"=" not in item:
            continue
        key, value = item.split(b"=", 1)
        name = key.decode("utf-8", errors="replace")
        if name in wanted:
            values[name] = value.decode("utf-8", errors="replace")
    return values


def file_hash(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def http_json(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    authenticated: bool,
    timeout: float = 8.0,
) -> tuple[int, dict[str, Any] | None]:
    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if authenticated:
        headers[TOKEN_HEADER] = load_lan_token()
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers=headers,
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=timeout) as response:
            raw = response.read()
            body = json.loads(raw.decode("utf-8")) if raw else None
            return int(response.status), body if isinstance(body, dict) else None
    except urllib.error.HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8"))
        except Exception:
            body = None
        return int(exc.code), body if isinstance(body, dict) else None
    except Exception:
        return 0, None


def purity_probe(attempts: int = 3) -> dict[str, Any]:
    paths = (
        LAB / "state/ORGANISM-PUBLIC.json",
        LAB / "state/ATTESTATION.json",
    )
    last: dict[str, Any] = {}
    for _ in range(attempts):
        before = db_snapshot()
        hashes_before = [file_hash(path) for path in paths]
        statuses = []
        for endpoint in (
            "/api/v1/organism",
            "/api/v1/episodes?limit=5",
            "/api/v1/capabilities",
        ):
            status, _ = http_json(
                "http://127.0.0.1:8090" + endpoint,
                authenticated=True,
            )
            statuses.append(status)
        after = db_snapshot()
        hashes_after = [file_hash(path) for path in paths]
        keys = (
            "identity_head",
            "event_head",
            "events",
            "episodes",
            "memory_receipts",
            "decision_evidence",
            "self_model_version",
            "inner_speech",
        )
        delta = int(
            any(before[key] != after[key] for key in keys)
            or hashes_before != hashes_after
        )
        last = {"GET_STATE_DELTA": delta, "http_statuses": statuses}
        if delta == 0 and all(status == 200 for status in statuses):
            return last
        time.sleep(1)
    return last


def growth_provenance_audit(execution_id: str) -> dict[str, int]:
    con = ro()
    try:
        rows = con.execute(
            """
            SELECT ev.event_id,ev.payload_json,ep.episode_id
            FROM events AS ev
            LEFT JOIN episodes AS ep
              ON ep.source_event_id=ev.event_id
             AND ep.event_type=ev.event_type
            WHERE ev.event_type='controlled_growth'
            ORDER BY ev.node_seq
            """
        ).fetchall()
        missing = 0
        decision_without_receipt = 0
        unsupported = 0
        counted = 0
        for event_id, payload_json, episode_id in rows:
            try:
                payload = json.loads(payload_json)
            except json.JSONDecodeError:
                continue
            if payload.get("execution_id") != execution_id:
                continue
            counted += 1
            if not episode_id or payload.get("provenance_missing") != 0:
                missing += 1
            receipt_ids = (
                (payload.get("steps") or {})
                .get("3_issue_memory_query", {})
                .get("memory_receipt_ids", [])
            )
            if not receipt_ids:
                decision_without_receipt += 1
            for receipt_id in receipt_ids:
                memory = con.execute(
                    "SELECT ok,future_use_count FROM memory_read_receipts "
                    "WHERE receipt_id=?",
                    (receipt_id,),
                ).fetchone()
                evidence = con.execute(
                    "SELECT COUNT(*) FROM decision_evidence WHERE receipt_id=?",
                    (receipt_id,),
                ).fetchone()[0]
                if not memory or memory[0] != 1 or memory[1] != 0 or evidence < 1:
                    decision_without_receipt += 1
            if (
                payload.get("unsupported_claims") != 0
                or payload.get("executable") is not False
                or payload.get("active_inference_state") != "SHADOW"
            ):
                unsupported += 1
        return {
            "controlled_receipts": counted,
            "provenance_missing": missing,
            "decision_without_memory_receipt_total": decision_without_receipt,
            "unsupported_claims": unsupported,
        }
    finally:
        con.close()


def sample_state(
    *,
    baseline: dict[str, Any],
    expected: dict[str, Any],
    source_hash: str,
    execution_id: str,
    probe_get: bool,
) -> dict[str, Any]:
    organism = unit_show("octopus-organism-lab")
    soak = unit_show("octopus-soak-lab")
    llama = unit_show("octopus-llama-lab")
    gateway = unit_show("octopus-gateway")
    current = db_snapshot()
    resources = resource_state()
    pid = int(organism.get("MainPID") or 0)
    unauth_status, _ = http_json(
        "http://192.168.0.180:8090/api/v1/organism",
        authenticated=False,
    )
    soak_payload = {}
    if SOAK_STATE.is_file():
        try:
            soak_payload = json.loads(SOAK_STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            soak_payload = {"abort": "invalid_soak_json"}
    executable_total = (
        current["evidence_executable_total"]
        + int(AI_EXECUTABLE)
        + int(WBE_EXECUTABLE)
    )
    return {
        "recorded_at": utc_now(),
        "pid": pid,
        "organism_active": organism.get("ActiveState") == "active",
        "organism_nrestarts": int(organism.get("NRestarts") or 0),
        "soak_pid": int(soak.get("MainPID") or 0),
        "llama_pid": int(llama.get("MainPID") or 0),
        "gateway_pid": int(gateway.get("MainPID") or 0),
        "source_hash": git("rev-parse", "HEAD"),
        "process_flags": process_flags(pid) if pid else {},
        "database": current,
        "resources": resources,
        "watcher_running": checkpoint_watcher_running(),
        "unauthenticated_lan_status": unauth_status,
        "unauthenticated_lan_accepted": unauth_status == 200,
        "soak_abort": soak_payload.get("abort"),
        "executable_total": executable_total,
        "provenance": growth_provenance_audit(execution_id),
        "get_purity": purity_probe() if probe_get else None,
        "heartbeat_delta": current["heartbeat_count"] - baseline["heartbeat_count"],
        "expected_pids": expected,
    }


def violations(sample: dict[str, Any], baseline: dict[str, Any]) -> list[str]:
    reasons = []
    db = sample["database"]
    resource = sample["resources"]
    provenance = sample["provenance"]
    expected = sample["expected_pids"]
    if not sample["organism_active"] or sample["pid"] != expected["organism"]:
        reasons.append("service_crash_or_pid_change")
    if sample["organism_nrestarts"] != expected["organism_nrestarts"]:
        reasons.append("organism_restart_count_changed")
    for key, expected_key in (
        ("soak_pid", "soak"),
        ("llama_pid", "llama"),
        ("gateway_pid", "gateway"),
    ):
        if sample[key] != expected[expected_key]:
            reasons.append(f"{key}_changed")
    if not db["identity_valid"]:
        reasons.append("identity_invalid")
    if db["quick_check"] != "ok":
        reasons.append("sqlite_not_ok")
    if db["schema"] != "phase3-skin-1":
        reasons.append("schema_changed")
    if db["future_use_total"] != 0:
        reasons.append("memory_future_use_total")
    if db["wan_fetches"] != baseline["wan_fetches"]:
        reasons.append("wan_fetches")
    if sample["executable_total"] != 0:
        reasons.append("executable_total")
    if provenance["decision_without_memory_receipt_total"] != 0:
        reasons.append("decision_without_memory_receipt_total")
    if provenance["provenance_missing"] != 0:
        reasons.append("provenance_missing")
    if provenance["unsupported_claims"] != 0:
        reasons.append("unsupported_claims")
    if not sample["watcher_running"]:
        reasons.append("checkpoint_watcher_not_running")
    if sample["unauthenticated_lan_accepted"]:
        reasons.append("unauthenticated_lan_accepted")
    if resource["disk_available_bytes"] < 5 * 1024**3:
        reasons.append("disk_below_5gib")
    if resource["disk_used_pct"] >= 92:
        reasons.append("root_at_or_above_92pct")
    if resource["ram_available_kib"] < 350 * 1024:
        reasons.append("ram_below_350mib")
    if 115000 - resource["temperature_mC"] < 10000:
        reasons.append("thermal_threshold")
    if sample["soak_abort"]:
        reasons.append("soak_abort")
    if db["heartbeat_interval_s"] != baseline["heartbeat_interval_s"]:
        reasons.append("heartbeat_interval_changed")
    if sample["source_hash"] != expected["source_hash"]:
        reasons.append("source_hash_changed")
    if sample["process_flags"] != {
        "OCTOPUS_GET_PURE": "1",
        "OCTOPUS_REQUIRE_LAN_TOKEN": "1",
        "OCTOPUS_LEARN_EXTERNAL": "0",
    }:
        reasons.append("security_flags_changed")
    purity = sample.get("get_purity")
    if purity is not None and purity.get("GET_STATE_DELTA") != 0:
        reasons.append("get_state_delta")
    return sorted(set(reasons))


def consume_approval_failure(
    registry: dict[str, Any],
    *,
    reason: str,
    status: str,
) -> dict[str, Any]:
    rolled = rollback_capabilities_to_tested(registry, reason=reason)
    rolled["approval"].update(
        {
            "status": "FAILED",
            "expired": True,
            "completed_at": utc_now(),
            "failure": reason,
        }
    )
    rolled["final_status"] = status
    atomic_write_registry(rolled)
    return rolled


def main() -> int:
    os.environ["OCTOPUS_REQUIRE_LAN_TOKEN"] = "1"
    os.environ["OCTOPUS_LAN_TOKEN_FILE"] = "/etc/octopus/lan-token"
    os.environ["OCTOPUS_GET_PURE"] = "1"
    os.environ["OCTOPUS_LEARN_EXTERNAL"] = "0"
    ART.mkdir(parents=True, exist_ok=True)
    GROWTH_RECEIPTS.write_text("", encoding="utf-8")

    registry = load_registry(REGISTRY_PATH)
    approval = registry["approval"]
    if (
        registry.get("phase") != "CANARY"
        or approval.get("status") != "RUNNING"
        or approval.get("used_once") is not True
        or approval.get("expired") is not False
        or not approval.get("execution_id")
    ):
        print("BLOCKED_PRECONDITION registry_or_approval")
        return 2
    execution_id = str(approval["execution_id"])
    source_hash = git("rev-parse", "HEAD")
    organism = unit_show("octopus-organism-lab")
    soak = unit_show("octopus-soak-lab")
    llama = unit_show("octopus-llama-lab")
    gateway = unit_show("octopus-gateway")
    expected = {
        "organism": int(organism.get("MainPID") or 0),
        "organism_nrestarts": int(organism.get("NRestarts") or 0),
        "soak": int(soak.get("MainPID") or 0),
        "llama": int(llama.get("MainPID") or 0),
        "gateway": int(gateway.get("MainPID") or 0),
        "source_hash": source_hash,
    }
    baseline = db_snapshot(integrity=True)
    pre = sample_state(
        baseline=baseline,
        expected=expected,
        source_hash=source_hash,
        execution_id=execution_id,
        probe_get=True,
    )
    pre_reasons = violations(pre, baseline)
    if baseline.get("integrity_check") != "ok":
        pre_reasons.append("sqlite_integrity_not_ok")
    if pre_reasons:
        reason = ",".join(sorted(set(pre_reasons)))
        consume_approval_failure(
            registry,
            reason=reason,
            status="BLOCKED_PRECONDITION",
        )
        blocked = {
            "GATE_ID": GATE_ID,
            "APPROVAL_USED_ONCE": True,
            "ACTION_EXECUTED": False,
            "FINAL_STATUS": "BLOCKED_PRECONDITION",
            "blocker": reason,
            "preflight": pre,
            "recorded_at": utc_now(),
        }
        write_json(FINAL_RECEIPT, blocked)
        print(json.dumps(blocked, sort_keys=True))
        return 2

    started = time.monotonic()
    started_at = utc_now()
    dispatched_heartbeats: set[str] = set()
    receipts: list[dict[str, Any]] = []
    abort_reasons: list[str] = []
    ram_min = pre["resources"]["ram_available_kib"]
    disk_min = pre["resources"]["disk_available_bytes"]
    root_pct_max = pre["resources"]["disk_used_pct"]
    temp_max = pre["resources"]["temperature_mC"]
    unauth_accepted = False
    get_delta_max = int(pre["get_purity"]["GET_STATE_DELTA"])
    sample_count = 0

    while time.monotonic() - started < DURATION_S:
        elapsed = time.monotonic() - started
        sample = sample_state(
            baseline=baseline,
            expected=expected,
            source_hash=source_hash,
            execution_id=execution_id,
            probe_get=sample_count % 4 == 0,
        )
        sample_count += 1
        resource = sample["resources"]
        ram_min = min(ram_min, resource["ram_available_kib"])
        disk_min = min(disk_min, resource["disk_available_bytes"])
        root_pct_max = max(root_pct_max, resource["disk_used_pct"])
        temp_max = max(temp_max, resource["temperature_mC"])
        unauth_accepted = unauth_accepted or sample["unauthenticated_lan_accepted"]
        if sample.get("get_purity"):
            get_delta_max = max(
                get_delta_max,
                int(sample["get_purity"]["GET_STATE_DELTA"]),
            )
        current_reasons = violations(sample, baseline)
        if current_reasons:
            abort_reasons.extend(current_reasons)
            break

        new_heartbeat_ids = heartbeat_ids_after(baseline["heartbeat_head_node_seq"])
        for heartbeat_id in new_heartbeat_ids:
            if len(receipts) >= len(EXPERIMENTS):
                break
            if heartbeat_id in dispatched_heartbeats:
                continue
            if DURATION_S - (time.monotonic() - started) < 60:
                break
            experiment = EXPERIMENTS[len(receipts)]
            status, body = http_json(
                "http://127.0.0.1:8090/api/v1/controlled-growth",
                method="POST",
                payload={
                    "gate_id": GATE_ID,
                    "execution_id": execution_id,
                    "heartbeat_event_id": heartbeat_id,
                    "experiment": experiment,
                },
                authenticated=True,
                timeout=70,
            )
            dispatched_heartbeats.add(heartbeat_id)
            if status != 200 or not isinstance(body, dict):
                abort_reasons.append(f"experiment_http_{status}:{experiment}")
                break
            receipts.append(body)
            append_jsonl(GROWTH_RECEIPTS, body)
        if abort_reasons:
            break
        remaining = DURATION_S - (time.monotonic() - started)
        if remaining > 0:
            time.sleep(min(POLL_S, remaining))

    elapsed_s = time.monotonic() - started
    end = db_snapshot(integrity=True)
    end_sample = sample_state(
        baseline=baseline,
        expected=expected,
        source_hash=source_hash,
        execution_id=execution_id,
        probe_get=True,
    )
    abort_reasons.extend(violations(end_sample, baseline))
    if end.get("integrity_check") != "ok":
        abort_reasons.append("sqlite_integrity_not_ok")
    get_delta_max = max(
        get_delta_max,
        int((end_sample.get("get_purity") or {}).get("GET_STATE_DELTA", 1)),
    )
    unauth_accepted = (
        unauth_accepted or end_sample["unauthenticated_lan_accepted"]
    )
    provenance = growth_provenance_audit(execution_id)
    external_calls = sum(int(item.get("external_calls") or 0) for item in receipts)
    wan_fetches = end["wan_fetches"] - baseline["wan_fetches"]
    executable_total = (
        end["evidence_executable_total"]
        + int(AI_EXECUTABLE)
        + int(WBE_EXECUTABLE)
    )
    heartbeat_delta = end["heartbeat_count"] - baseline["heartbeat_count"]
    complete_receipts = all(
        item.get("persisted") is True
        and item.get("memory_reads_per_cycle", 0) >= 1
        and item.get("memory_future_use_total") == 0
        and item.get("decision_without_memory_receipt_total") == 0
        and item.get("executable_total") == 0
        and item.get("external_calls") == 0
        and item.get("wan_fetches") == 0
        and item.get("provenance_missing") == 0
        and item.get("resource_violations") == 0
        and item.get("unsupported_claims") == 0
        for item in receipts
    )
    if elapsed_s < DURATION_S:
        abort_reasons.append("duration_below_15_minutes")
    if heartbeat_delta < 3:
        abort_reasons.append("heartbeats_below_3")
    if len(receipts) < 2:
        abort_reasons.append("experiments_below_2")
    if not complete_receipts:
        abort_reasons.append("incomplete_experiment_receipt")
    if provenance["controlled_receipts"] != len(receipts):
        abort_reasons.append("controlled_receipt_count_mismatch")
    if external_calls:
        abort_reasons.append("external_calls")
    if wan_fetches:
        abort_reasons.append("wan_fetches")
    if executable_total:
        abort_reasons.append("executable_total")
    if get_delta_max:
        abort_reasons.append("get_state_delta")
    if unauth_accepted:
        abort_reasons.append("unauthenticated_lan_accepted")
    if provenance["provenance_missing"]:
        abort_reasons.append("provenance_missing")
    if provenance["decision_without_memory_receipt_total"]:
        abort_reasons.append("decision_without_memory_receipt_total")
    if provenance["unsupported_claims"]:
        abort_reasons.append("unsupported_claims")
    abort_reasons = sorted(set(abort_reasons))

    deployment = registry.get("deployment") or {}
    common = {
        "GATE_ID": GATE_ID,
        "APPROVAL_USED_ONCE": True,
        "SOURCE_HASH_BEFORE": deployment.get("source_hash_before"),
        "SOURCE_HASH_AFTER": source_hash,
        "PID_BEFORE": deployment.get("pid_before"),
        "PID_AFTER": expected["organism"],
        "ORGANISM_RESTARTS": 1,
        "SOAK_RESTARTS": 0,
        "HEARTBEATS": heartbeat_delta,
        "EXPERIMENTS": len(receipts),
        "MEMORY_RECEIPTS_ADDED": end["memory_receipts"] - baseline["memory_receipts"],
        "DECISION_EVIDENCE_ADDED": (
            end["decision_evidence"] - baseline["decision_evidence"]
        ),
        "EPISODES_ADDED": end["episodes"] - baseline["episodes"],
        "SELF_MODEL_UPDATES": (
            end["self_model_version"] - baseline["self_model_version"]
        ),
        "EXTERNAL_CALLS": external_calls,
        "WAN_FETCHES": wan_fetches,
        "EXECUTABLE_TOTAL": executable_total,
        "IDENTITY_CHAIN_VALID": end["identity_valid"],
        "SQLITE_INTEGRITY": end.get("integrity_check"),
        "RESOURCE_VIOLATIONS": len(
            [
                item
                for item in abort_reasons
                if item
                in {
                    "disk_below_5gib",
                    "root_at_or_above_92pct",
                    "ram_below_350mib",
                    "thermal_threshold",
                }
            ]
        ),
        "GET_STATE_DELTA": get_delta_max,
        "UNAUTHENTICATED_LAN_ACCEPTED": unauth_accepted,
        "MEMORY_FUTURE_USE_TOTAL": end["future_use_total"],
        "DECISION_WITHOUT_MEMORY_RECEIPT_TOTAL": provenance[
            "decision_without_memory_receipt_total"
        ],
        "PROVENANCE_MISSING": provenance["provenance_missing"],
        "UNSUPPORTED_CLAIMS": provenance["unsupported_claims"],
        "DURATION_SECONDS": round(elapsed_s, 3),
        "DURATION_MINUTES": round(elapsed_s / 60, 3),
        "STARTED_AT": started_at,
        "COMPLETED_AT": utc_now(),
        "RESOURCE_SUMMARY": {
            "minimum_ram_kib": ram_min,
            "minimum_disk_bytes": disk_min,
            "maximum_root_used_pct": root_pct_max,
            "maximum_temperature_mC": temp_max,
        },
        "CAPABILITIES_DISCOVERED": list(INTERNAL_CAPABILITIES),
        "CAPABILITIES_IMPLEMENTED": list(INTERNAL_CAPABILITIES),
        "growth_receipts_path": str(GROWTH_RECEIPTS),
        "registry_path": str(REGISTRY_PATH),
    }

    if abort_reasons:
        reason = ",".join(abort_reasons)
        failed_registry = consume_approval_failure(
            registry,
            reason=reason,
            status="CONTROLLED_GROWTH_CANARY_ABORTED",
        )
        receipt = {
            **common,
            "ACTION_EXECUTED": bool(receipts),
            "CAPABILITIES_ACTIVATED": [],
            "CAPABILITIES_QUARANTINED": list(ACTIVATABLE),
            "ROLLBACK_USED": True,
            "ROLLBACK_RESTART_USED": False,
            "FINAL_STATUS": "CONTROLLED_GROWTH_CANARY_ABORTED",
            "blocker": reason,
            "registry_phase": failed_registry["phase"],
        }
        write_json(FINAL_RECEIPT, receipt)
        print(json.dumps(receipt, sort_keys=True))
        return 2

    active = transition_capabilities(
        registry,
        "ACTIVE_LOCAL",
        evidence=[str(FINAL_RECEIPT), str(GROWTH_RECEIPTS)],
    )
    for capability_id in ACTIVATABLE:
        active["capabilities"][capability_id]["evidence"].append(str(FINAL_RECEIPT))
    active["phase"] = "ACTIVE_LOCAL"
    active["approval"].update(
        {
            "status": "COMPLETED",
            "expired": True,
            "completed_at": utc_now(),
        }
    )
    active["ready_for_next_owner_decision"] = True
    active["final_status"] = "CONTROLLED_GROWTH_CANARY_PASS"
    validate_registry(active)
    atomic_write_registry(active)
    receipt = {
        **common,
        "ACTION_EXECUTED": True,
        "CAPABILITIES_ACTIVATED": list(ACTIVATABLE),
        "CAPABILITIES_QUARANTINED": [],
        "ROLLBACK_USED": False,
        "ROLLBACK_RESTART_USED": False,
        "FINAL_STATUS": "CONTROLLED_GROWTH_CANARY_PASS",
        "MEMORY_CAPABILITY": "ACTIVE_LOCAL",
        "CURIOSITY_CAPABILITY": "ACTIVE_LOCAL",
        "LOCAL_LEARNING_CAPABILITY": "ACTIVE_LOCAL",
        "SELF_MODEL_CAPABILITY": "ACTIVE_LOCAL",
        "CONSOLIDATION_CAPABILITY": "ACTIVE_LOCAL",
        "HYPOTHESIS_CAPABILITY": "ACTIVE_LOCAL",
        "INNER_SPEECH_CAPABILITY": "ACTIVE_LOCAL",
        "ACTIVE_INFERENCE_CAPABILITY": "SHADOW",
        "EXTERNAL_LEARNING_CAPABILITY": "LOCKED",
        "EXTERNAL_ACTION_CAPABILITY": "LOCKED",
        "WAVE1_UNLOCKED": False,
        "READY_FOR_NEXT_OWNER_DECISION": True,
        "registry_sha256": file_hash(REGISTRY_PATH),
    }
    write_json(FINAL_RECEIPT, receipt)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
