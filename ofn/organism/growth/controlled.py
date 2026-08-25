"""Owner-gated, bounded, local-only controlled growth experiments.

Every live database write in this module is reached from the organism runtime
and uses the existing event kernel, episodic writer, or mandatory memory gate.
No schema migration, external network call, actuator, shell, or service control
is present.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable

from ofn.organism.cognition.active_inference import EXECUTABLE as AI_EXECUTABLE
from ofn.organism.cognition.backend import LocalCortex
from ofn.organism.contracts.events import make_event
from ofn.organism.growth.capabilities import (
    ACTIVE_INFERENCE_CAPABILITY,
    GATE_ID,
    INTERNAL_CAPABILITIES,
    load_registry,
    validate_registry,
)
from ofn.organism.homeostasis.core import (
    MEM_AVAILABLE_DANGER_KB,
    THERMAL_CRITICAL_MC,
    THERMAL_DANGER_MARGIN_MC,
    measure,
)
from ofn.organism.identity.ledger import verify_identity_chain
from ofn.organism.memory.gate import require_memory_gate
from ofn.organism.persistence.db import DB_LOCK
from ofn.organism.science.wbe_allometry import EXECUTABLE as WBE_EXECUTABLE


ALLOWED_EXPERIMENTS = (
    "SELF_MODEL_GAP",
    "EPISODIC_CONSOLIDATION",
    "LOCAL_HYPOTHESIS",
)
MAX_EXPERIMENTS = 3
WATCHER_HEARTBEAT = Path(
    "/opt/octopus/lab/artifacts/completion-phase3/receipts/watcher.heartbeat.json"
)
_CONTROLLED_GROWTH_LOCK = threading.Lock()


class ControlledGrowthError(RuntimeError):
    """A gate, safety, provenance, or bounded-execution condition failed."""


def _read_meminfo() -> dict[str, int]:
    values: dict[str, int] = {}
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        if ":" not in line:
            continue
        key, rest = line.split(":", 1)
        if key in {"MemAvailable", "MemTotal"}:
            values[key] = int(rest.split()[0])
    return values


def _disk_state() -> dict[str, Any]:
    stat = os.statvfs("/")
    available = stat.f_bavail * stat.f_frsize
    used_pct = 100.0 * (1.0 - stat.f_bavail / stat.f_blocks)
    return {
        "available_bytes": available,
        "available_gib": round(available / 1024**3, 3),
        "used_pct": round(used_pct, 2),
    }


def checkpoint_watcher_running(
    heartbeat_path: Path = WATCHER_HEARTBEAT,
    *,
    max_age_s: float = 45.0,
) -> bool:
    process_found = False
    nul = bytes([0])
    for proc in Path("/proc").glob("[0-9]*"):
        try:
            command = (proc / "cmdline").read_bytes().replace(nul, b" ").decode(
                "utf-8", errors="replace"
            )
        except (OSError, PermissionError):
            continue
        if "/opt/octopus/lab/bin/checkpoint-watcher.py" in command:
            process_found = True
            break
    if not process_found or not heartbeat_path.is_file():
        return False
    try:
        payload = json.loads(heartbeat_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    age = time.time() - heartbeat_path.stat().st_mtime
    return bool(payload.get("running")) and 0 <= age < max_age_s


def engineering_delta_theta(
    *,
    belief_change: float,
    homeostatic_error: float,
    action_relevance: float,
    memory_retention: float,
) -> dict[str, Any]:
    """Pure engineering salience score; not subjective time or consciousness."""

    values = [
        max(0.0, min(1.0, float(value)))
        for value in (
            belief_change,
            homeostatic_error,
            action_relevance,
            memory_retention,
        )
    ]
    belief, homeostatic, action, memory = values
    score = 0.35 * belief + 0.35 * homeostatic + 0.15 * action + 0.15 * memory
    return {
        "delta_theta": round(score, 4),
        "belief_change": round(belief, 4),
        "homeostatic_error": round(homeostatic, 4),
        "action_relevance": round(action, 4),
        "memory_retention": round(memory, 4),
        "cognitive_engineering_threshold_crossed": score >= 0.45,
        "threshold": 0.45,
        "subjective_claim": False,
        "consciousness_claim": False,
        "executable": False,
        "note": "engineering salience only; token/FLOP use is not inner time",
    }


def collect_safety_snapshot(
    con,
    registry: dict[str, Any],
    *,
    watcher_probe: Callable[[], bool] = checkpoint_watcher_running,
) -> dict[str, Any]:
    validate_registry(registry)
    measured = measure()
    signals = {item["name"]: item for item in measured.get("signals") or []}
    mem = _read_meminfo()
    disk = _disk_state()
    temperature = (signals.get("soc_temp_mC") or {}).get("value")
    identity = verify_identity_chain(con)
    with DB_LOCK:
        quick_check = str(con.execute("PRAGMA quick_check").fetchone()[0])
        schema_row = con.execute(
            "SELECT v FROM meta WHERE k='schema_migration_version'"
        ).fetchone()
        future_use_total = int(
            con.execute(
                "SELECT COALESCE(SUM(future_use_count),0) "
                "FROM memory_read_receipts"
            ).fetchone()[0]
        )
        executable_total = int(
            con.execute(
                "SELECT COALESCE(SUM(executable),0) FROM decision_evidence"
            ).fetchone()[0]
        )
        wan_fetches = int(con.execute("SELECT COUNT(*) FROM wan_fetches").fetchone()[0])
    executable_total += int(AI_EXECUTABLE) + int(WBE_EXECUTABLE)
    watcher_ok = bool(watcher_probe())
    violations: list[str] = []
    if os.environ.get("OCTOPUS_GET_PURE") != "1":
        violations.append("GET_PURE_NOT_1")
    if os.environ.get("OCTOPUS_REQUIRE_LAN_TOKEN") != "1":
        violations.append("REQUIRE_LAN_TOKEN_NOT_1")
    if os.environ.get("OCTOPUS_LEARN_EXTERNAL") != "0":
        violations.append("LEARN_EXTERNAL_NOT_0")
    if schema_row is None or schema_row[0] != "phase3-skin-1":
        violations.append("SCHEMA_NOT_PHASE3_SKIN_1")
    if not identity.get("valid"):
        violations.append("IDENTITY_INVALID")
    if quick_check != "ok":
        violations.append("SQLITE_NOT_OK")
    if not watcher_ok:
        violations.append("CHECKPOINT_WATCHER_NOT_RUNNING")
    if disk["available_bytes"] < 5 * 1024**3 or disk["used_pct"] >= 92:
        violations.append("DISK_THRESHOLD")
    if mem.get("MemAvailable", -1) < MEM_AVAILABLE_DANGER_KB:
        violations.append("RAM_THRESHOLD")
    if (
        temperature is None
        or THERMAL_CRITICAL_MC - int(temperature) < THERMAL_DANGER_MARGIN_MC
    ):
        violations.append("THERMAL_THRESHOLD")
    if future_use_total:
        violations.append("MEMORY_FUTURE_USE")
    if executable_total:
        violations.append("EXECUTABLE_TOTAL")
    if wan_fetches:
        violations.append("WAN_FETCHES")
    return {
        "measured_at": measured.get("ts"),
        "health_state": measured.get("health_state"),
        "alerts": list(measured.get("alerts") or []),
        "mem_available_kib": mem.get("MemAvailable"),
        "mem_total_kib": mem.get("MemTotal"),
        "temperature_mC": temperature,
        "disk": disk,
        "identity": {
            "valid": bool(identity.get("valid")),
            "entries": identity.get("entries"),
            "last_hash": identity.get("last_hash"),
            "error": identity.get("error"),
        },
        "sqlite_quick_check": quick_check,
        "schema": None if schema_row is None else schema_row[0],
        "watcher_running": watcher_ok,
        "memory_future_use_total": future_use_total,
        "executable_total": executable_total,
        "wan_fetches": wan_fetches,
        "external_calls": 0,
        "violations": violations,
    }


def _controlled_receipts(con, execution_id: str) -> list[dict[str, Any]]:
    with DB_LOCK:
        rows = con.execute(
            """
            SELECT payload_json
            FROM events
            WHERE event_type='controlled_growth'
            ORDER BY node_seq
            """
        ).fetchall()
    receipts = []
    for row in rows:
        try:
            payload = json.loads(row[0])
        except json.JSONDecodeError:
            continue
        if payload.get("execution_id") == execution_id:
            receipts.append(payload)
    return receipts


def _assert_execution_slot(
    con,
    registry: dict[str, Any],
    *,
    gate_id: str,
    execution_id: str,
    heartbeat_event_id: str,
    experiment: str,
) -> int:
    if gate_id != GATE_ID:
        raise ControlledGrowthError("gate_id_mismatch")
    approval = registry["approval"]
    if approval.get("status") != "RUNNING":
        raise ControlledGrowthError("approval_not_running")
    if approval.get("used_once") is not True or approval.get("expired") is not False:
        raise ControlledGrowthError("approval_not_available")
    if approval.get("execution_id") != execution_id:
        raise ControlledGrowthError("execution_id_mismatch")
    if registry.get("phase") != "CANARY":
        raise ControlledGrowthError("registry_not_canary")
    for capability_id in INTERNAL_CAPABILITIES:
        state = registry["capabilities"][capability_id]["state"]
        expected = (
            "SHADOW"
            if capability_id == ACTIVE_INFERENCE_CAPABILITY
            else "CANARY"
        )
        if state != expected:
            raise ControlledGrowthError(
                f"capability_not_{expected.lower()}:{capability_id}"
            )
    if experiment not in ALLOWED_EXPERIMENTS:
        raise ControlledGrowthError("experiment_not_allowed")
    with DB_LOCK:
        heartbeat = con.execute(
            "SELECT event_id FROM events WHERE event_id=? AND event_type='heartbeat'",
            (heartbeat_event_id,),
        ).fetchone()
    if not heartbeat:
        raise ControlledGrowthError("heartbeat_event_not_found")
    prior = _controlled_receipts(con, execution_id)
    if len(prior) >= MAX_EXPERIMENTS:
        raise ControlledGrowthError("experiment_limit_reached")
    if any(item.get("heartbeat_event_id") == heartbeat_event_id for item in prior):
        raise ControlledGrowthError("heartbeat_already_used")
    if any(item.get("experiment") == experiment for item in prior):
        raise ControlledGrowthError("experiment_already_attempted")
    return len(prior) + 1


def _persist_result_event(
    con,
    kernel,
    *,
    event_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    event = make_event(event_type, payload, priority=18, event_id=event_id)
    committed = kernel.accept(event)
    if committed.get("status") != "committed":
        raise ControlledGrowthError(
            f"result_event_not_committed:{committed.get('status')}"
        )
    kernel.replay_pending(limit=20)
    expected_episode_id = hashlib.sha256(
        f"{event_id}:{event_type}".encode("utf-8")
    ).hexdigest()[:32]
    with DB_LOCK:
        episode = con.execute(
            """
            SELECT ep.episode_id, ev.hash
            FROM episodes AS ep
            JOIN events AS ev ON ev.event_id=ep.source_event_id
            WHERE ep.episode_id=? AND ep.source_event_id=? AND ep.event_type=?
            """,
            (expected_episode_id, event_id, event_type),
        ).fetchone()
    if not episode:
        raise ControlledGrowthError("result_episode_missing_provenance")
    return {
        "event_id": event_id,
        "event_hash": episode[1],
        "episode_id": episode[0],
        "provenance_valid": True,
    }


def _self_model_gap_plan(
    registry: dict[str, Any],
    evidence_ids: list[str],
) -> dict[str, Any]:
    candidates = []
    for capability_id in INTERNAL_CAPABILITIES:
        if capability_id == ACTIVE_INFERENCE_CAPABILITY:
            continue
        entry = registry["capabilities"][capability_id]
        candidates.append((len(entry.get("evidence") or []), capability_id))
    evidence_count, capability_id = sorted(candidates)[0]
    confidence = 0.35 if evidence_count == 0 else min(0.8, 0.4 + evidence_count * 0.1)
    proposal = {
        "proposal_type": "CapabilityProposal",
        "capability_id": capability_id,
        "evidence_ids": evidence_ids,
        "registry_evidence_count": evidence_count,
        "confidence": round(confidence, 2),
        "uncertainty": (
            "Registry evidence count is a coverage signal, not proof of capability "
            "absence or weakness."
        ),
        "proposed_local_test": (
            "Run one bounded synthetic/tempfile test for the selected capability "
            "and require provenance plus executable=false."
        ),
        "executable": False,
    }
    return {
        "gap": f"weakest_registry_evidence:{capability_id}",
        "hypothesis": (
            f"{capability_id} has the smallest direct registry evidence set at "
            "this decision time."
        ),
        "expected_result": "One non-executable CapabilityProposal with evidence IDs.",
        "success_criterion": (
            "Capability ID, evidence IDs, confidence, uncertainty, local test, "
            "and executable=false are all present."
        ),
        "classification": "SUPPORT",
        "measurement": {
            "selected_capability_id": capability_id,
            "registry_evidence_count": evidence_count,
        },
        "event_type": "capability_proposal",
        "event_payload": proposal,
        "external_calls": 0,
        "local_cortex_calls": 0,
        "causal_claim": False,
    }


def _consolidation_plan(con, evidence_ids: list[str]) -> dict[str, Any]:
    used: set[str] = set()
    with DB_LOCK:
        prior_rows = con.execute(
            "SELECT payload_json FROM events WHERE event_type='memory_consolidation'"
        ).fetchall()
        heartbeat_rows = con.execute(
            """
            SELECT event_id, hash, payload_json
            FROM events
            WHERE event_type='heartbeat'
            ORDER BY node_seq DESC
            LIMIT 20
            """
        ).fetchall()
    for row in prior_rows:
        try:
            prior = json.loads(row[0])
        except json.JSONDecodeError:
            continue
        used.update(str(item) for item in prior.get("source_event_ids") or [])
    selected = [row for row in heartbeat_rows if row[0] not in used][:3]
    source_ids = [str(row[0]) for row in selected]
    provenance = [{"event_id": str(row[0]), "event_hash": str(row[1])} for row in selected]
    health_states = []
    for row in selected:
        try:
            body = json.loads(row[2])
        except json.JSONDecodeError:
            body = {}
        health = body.get("health")
        if health is not None and health not in health_states:
            health_states.append(health)
    if len(selected) < 2:
        classification = "INSUFFICIENT_EVIDENCE"
        summary = "Fewer than two unconsolidated heartbeat events were available."
    else:
        classification = "SUPPORT"
        summary = (
            f"Consolidated {len(selected)} heartbeat events; observed health "
            f"values={health_states or ['not_recorded']}."
        )
    payload = {
        "source_event_ids": source_ids,
        "source_provenance": provenance,
        "memory_evidence_ids": evidence_ids,
        "summary": summary,
        "model": "deterministic-local-consolidator",
        "model_version": "1",
        "raw_events_overwritten": False,
        "duplicate_episode_requested": False,
        "executable": False,
    }
    return {
        "gap": "related heartbeat events lack a grouped provenance-preserving episode",
        "hypothesis": (
            "Two or more unconsolidated heartbeat events can be grouped without "
            "altering their raw event rows."
        ),
        "expected_result": (
            "A new deterministic consolidation episode references all source "
            "event IDs and leaves source hashes unchanged."
        ),
        "success_criterion": (
            "At least two source IDs, complete hashes, model/version, one new "
            "episode, no duplicate, and unchanged raw source hashes."
        ),
        "classification": classification,
        "measurement": {
            "source_event_count": len(source_ids),
            "source_event_ids": source_ids,
            "source_hashes_before": {
                item["event_id"]: item["event_hash"] for item in provenance
            },
        },
        "event_type": "memory_consolidation",
        "event_payload": payload,
        "external_calls": 0,
        "local_cortex_calls": 0,
        "causal_claim": False,
    }


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denominator = math.sqrt(
        sum((x - mean_x) ** 2 for x in xs)
        * sum((y - mean_y) ** 2 for y in ys)
    )
    if denominator == 0:
        return None
    return numerator / denominator


def _local_hypothesis_plan(
    evidence_ids: list[str],
    *,
    cortex: LocalCortex | Any | None = None,
    mem_probe: Callable[[], dict[str, int]] = _read_meminfo,
) -> dict[str, Any]:
    local = cortex or LocalCortex(timeout=8)
    observations = []
    for _ in range(5):
        memory = mem_probe()
        response = local.complete(
            "Local telemetry test. Reply exactly OK; do not add facts.",
            max_tokens=4,
        )
        total = int(memory.get("MemTotal") or 0)
        available = int(memory.get("MemAvailable") or 0)
        pressure = None if total <= 0 else 1.0 - available / total
        observations.append(
            {
                "mem_available_kib": available,
                "mem_total_kib": total,
                "memory_pressure_fraction": pressure,
                "latency_ms": response.get("latency_ms"),
                "http_status": response.get("http_status"),
                "status": response.get("status"),
            }
        )
    usable = [
        item
        for item in observations
        if item["memory_pressure_fraction"] is not None
        and isinstance(item.get("latency_ms"), int)
        and item.get("http_status") == 200
    ]
    pressures = [float(item["memory_pressure_fraction"]) for item in usable]
    latencies = [float(item["latency_ms"]) for item in usable]
    correlation = _pearson(pressures, latencies)
    pressure_span = max(pressures) - min(pressures) if pressures else 0.0
    if len(usable) < 5 or correlation is None or pressure_span < 0.005:
        classification = "INSUFFICIENT_EVIDENCE"
    elif correlation >= 0.5:
        classification = "SUPPORT"
    elif correlation <= -0.5:
        classification = "REJECT"
    else:
        classification = "INSUFFICIENT_EVIDENCE"
    payload = {
        "hypothesis_id": "memory-pressure-vs-local-cortex-latency",
        "memory_evidence_ids": evidence_ids,
        "observations": observations,
        "association": {
            "method": "pearson",
            "coefficient": None if correlation is None else round(correlation, 6),
            "usable_points": len(usable),
            "memory_pressure_span": round(pressure_span, 8),
        },
        "classification": classification,
        "causal_claim": False,
        "external_calls": 0,
        "wan_fetches": 0,
        "executable": False,
    }
    return {
        "gap": "local memory-pressure/latency association lacks bounded observations",
        "hypothesis": (
            "Within this bounded local sample, higher measured memory pressure "
            "is associated with higher local cortex latency."
        ),
        "expected_result": (
            "Five local-only observations are classified as SUPPORT, REJECT, or "
            "INSUFFICIENT_EVIDENCE without a causal claim."
        ),
        "success_criterion": (
            "Exactly five bounded local calls, no WAN/external calls, numeric "
            "telemetry only, and epistemically valid classification."
        ),
        "classification": classification,
        "measurement": payload["association"],
        "event_type": "local_hypothesis",
        "event_payload": payload,
        "external_calls": 0,
        "local_cortex_calls": 5,
        "causal_claim": False,
    }


def run_controlled_growth(
    con,
    kernel,
    *,
    gate_id: str,
    execution_id: str,
    heartbeat_event_id: str,
    experiment: str,
    registry_path: Path | None = None,
    registry: dict[str, Any] | None = None,
    watcher_probe: Callable[[], bool] = checkpoint_watcher_running,
    cortex: LocalCortex | Any | None = None,
    mem_probe: Callable[[], dict[str, int]] = _read_meminfo,
) -> dict[str, Any]:
    """Run one allowed experiment for one real heartbeat, at most three total."""

    with _CONTROLLED_GROWTH_LOCK:
        active_registry = (
            validate_registry(registry)
            if registry is not None
            else load_registry(registry_path)
        )
        ordinal = _assert_execution_slot(
            con,
            active_registry,
            gate_id=gate_id,
            execution_id=execution_id,
            heartbeat_event_id=heartbeat_event_id,
            experiment=experiment,
        )
        before = collect_safety_snapshot(
            con, active_registry, watcher_probe=watcher_probe
        )
        if before["violations"]:
            raise ControlledGrowthError(
                "precondition:" + ",".join(before["violations"])
            )

        memory_bundle = require_memory_gate(
            con, f"controlled_growth.{experiment.lower()}"
        )
        memory_receipt_ids = [item.receipt_id for item in memory_bundle.receipts]
        evidence_ids: list[str] = []
        for item in memory_bundle.receipts:
            evidence_ids.extend(item.event_ids)
            evidence_ids.extend(item.episode_ids)
        evidence_ids = list(dict.fromkeys(evidence_ids))

        if experiment == "SELF_MODEL_GAP":
            plan = _self_model_gap_plan(active_registry, evidence_ids)
        elif experiment == "EPISODIC_CONSOLIDATION":
            plan = _consolidation_plan(con, evidence_ids)
        else:
            plan = _local_hypothesis_plan(
                evidence_ids,
                cortex=cortex,
                mem_probe=mem_probe,
            )

        after_experiment = collect_safety_snapshot(
            con, active_registry, watcher_probe=watcher_probe
        )
        if after_experiment["violations"]:
            raise ControlledGrowthError(
                "post_experiment:" + ",".join(after_experiment["violations"])
            )
        if plan["external_calls"] != 0 or plan["causal_claim"] is not False:
            raise ControlledGrowthError("experiment_claim_or_external_violation")

        result_event_id = hashlib.sha256(
            f"{execution_id}:{heartbeat_event_id}:{experiment}:result".encode()
        ).hexdigest()[:32]
        result_payload = {
            **plan["event_payload"],
            "gate_id": gate_id,
            "execution_id": execution_id,
            "heartbeat_event_id": heartbeat_event_id,
            "experiment": experiment,
            "classification": plan["classification"],
            "memory_receipt_ids": memory_receipt_ids,
            "provenance_complete": True,
            "external_calls": 0,
            "wan_fetches": 0,
            "executable": False,
        }
        persisted_result = _persist_result_event(
            con,
            kernel,
            event_id=result_event_id,
            event_type=plan["event_type"],
            payload=result_payload,
        )

        if experiment == "EPISODIC_CONSOLIDATION":
            source_ids = plan["measurement"]["source_event_ids"]
            with DB_LOCK:
                rows = (
                    con.execute(
                        f"SELECT event_id, hash FROM events "
                        f"WHERE event_id IN ({','.join('?' for _ in source_ids)})",
                        source_ids,
                    ).fetchall()
                    if source_ids
                    else []
                )
            hashes_after = {str(row[0]): str(row[1]) for row in rows}
            unchanged = hashes_after == plan["measurement"]["source_hashes_before"]
            plan["measurement"]["source_hashes_after"] = hashes_after
            plan["measurement"]["raw_events_unchanged"] = unchanged
            if not unchanged:
                raise ControlledGrowthError("raw_event_hash_changed")
            if len(source_ids) < 2:
                plan["classification"] = "INSUFFICIENT_EVIDENCE"

        post_persist = collect_safety_snapshot(
            con, active_registry, watcher_probe=watcher_probe
        )
        if post_persist["violations"]:
            raise ControlledGrowthError(
                "post_persist:" + ",".join(post_persist["violations"])
            )
        theta = engineering_delta_theta(
            belief_change=(
                0.4 if plan["classification"] in {"SUPPORT", "REJECT"} else 0.1
            ),
            homeostatic_error=0.0,
            action_relevance=0.0,
            memory_retention=1.0,
        )
        receipt_event_id = hashlib.sha256(
            f"{execution_id}:{heartbeat_event_id}:{experiment}:receipt".encode()
        ).hexdigest()[:32]
        receipt_episode_id = hashlib.sha256(
            f"{receipt_event_id}:controlled_growth".encode()
        ).hexdigest()[:32]
        receipt = {
            "receipt_schema_version": 1,
            "receipt_id": receipt_event_id,
            "receipt_episode_id": receipt_episode_id,
            "gate_id": gate_id,
            "execution_id": execution_id,
            "experiment_ordinal": ordinal,
            "heartbeat_event_id": heartbeat_event_id,
            "experiment": experiment,
            "steps": {
                "1_measure_body_state": before,
                "2_verify_identity": before["identity"],
                "3_issue_memory_query": {
                    "memory_receipt_ids": memory_receipt_ids,
                    "memory_reads_per_cycle": memory_bundle.memory_reads_per_cycle,
                    "memory_future_use_total": memory_bundle.memory_future_use_total,
                },
                "4_retrieve_relevant_evidence": {
                    "evidence_ids": evidence_ids,
                    "evidence_count": len(evidence_ids),
                },
                "5_choose_one_small_gap": plan["gap"],
                "6_form_falsifiable_hypothesis": plan["hypothesis"],
                "7_preregister": {
                    "expected_result": plan["expected_result"],
                    "success_criterion": plan["success_criterion"],
                },
                "8_run_local_sandbox_experiment": {
                    "allowed": True,
                    "external_calls": 0,
                    "local_cortex_calls": plan["local_cortex_calls"],
                    "executable": False,
                },
                "9_measure_result": plan["measurement"],
                "10_classify_belief": plan["classification"],
                "11_update_with_provenance": persisted_result,
                "12_persist_complete_receipt": {
                    "event_id": receipt_event_id,
                    "episode_id": receipt_episode_id,
                    "provenance_required": True,
                },
            },
            "classification": plan["classification"],
            "engineering_theta": theta,
            "memory_reads_per_cycle": memory_bundle.memory_reads_per_cycle,
            "memory_future_use_total": memory_bundle.memory_future_use_total,
            "decision_without_memory_receipt_total": 0,
            "external_calls": 0,
            "wan_fetches": 0,
            "executable_total": 0,
            "provenance_missing": 0,
            "resource_violations": 0,
            "unsupported_claims": 0,
            "active_inference_state": "SHADOW",
            "external_learning_state": "LOCKED",
            "external_action_state": "LOCKED",
            "wave1_unlocked": False,
            "wave0_observe_only": True,
            "propose_only": True,
            "executable": False,
            "recorded_at": time.time(),
        }
        persisted_receipt = _persist_result_event(
            con,
            kernel,
            event_id=receipt_event_id,
            event_type="controlled_growth",
            payload=receipt,
        )
        if persisted_receipt["episode_id"] != receipt_episode_id:
            raise ControlledGrowthError("receipt_episode_id_mismatch")
        return {
            **receipt,
            "persisted": True,
            "receipt_event_hash": persisted_receipt["event_hash"],
            "result_event": persisted_result,
        }
