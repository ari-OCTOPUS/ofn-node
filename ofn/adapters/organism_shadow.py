"""Advisory bridge from observed self-model readings to EXEC-001 libraries.

No actuation, network, env lookup, inferred inter-node links or invented sensor
values. assess_snapshot is pure. Only the existing producer CLI opts into the
bounded journal writer; cockpit reads remain write-free.
"""
from __future__ import annotations

from datetime import datetime, timezone
import math
import os
from pathlib import Path
import re

from shadow_homeostasis.canonical import assert_shadow, digest, canonical, finite_number
from shadow_homeostasis.evidence_store import EvidenceStore
from shadow_homeostasis.pipeline import run_shadow_pipeline
from shadow_homeostasis.registry import default_registry, MetricSpec
from octopus_exec.contracts import observation_from_dict, envelope
from octopus_exec.topology import analyze_topology
from octopus_exec.resource_budget import ArtifactBudget, assess_resources, account_legs
from octopus_exec.experience import Experience, calibration_report
from octopus_exec.checkpoint import save_checkpoint, verify_checkpoint
from octopus_exec.handoff import request_owner, owner_states, write_inbox
from octopus_exec.snapshot_reader import no_reparse

SOURCE = "ofn.self_model"
SCHEMA = "octopus.organism-shadow.v1"
STATUSES = {"healthy", "absent", "stale", "failed", "unknown"}
RESEARCH_IDS = tuple("R%02d" % n for n in range(1, 16))


def _epoch(value):
    if type(value) not in (int, float):
        return None
    try:
        if not math.isfinite(value):
            return None
        return datetime.fromtimestamp(value, timezone.utc).isoformat()
    except (ValueError, OverflowError, OSError):
        return None


def assess_snapshot(model, *, now_epoch, process_max_age=180, node_id=None, boot_id=None):
    """Preserve actual status evidence; physiology without sensors stays unknown."""
    now = _epoch(now_epoch)
    if now is None or not isinstance(model, dict):
        raise ValueError("model and explicit finite observation clock required")
    if not finite_number(process_max_age) or process_max_age < 0:
        raise ValueError("invalid existing freshness window")
    for identity in (node_id, boot_id):
        if identity is not None and (not isinstance(identity, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", identity)):
            raise ValueError("invalid explicit node/boot identity")
    projection = []
    seen = set()
    for group in ("sensors", "processes", "capabilities"):
        rows = model.get(group, [])
        if not isinstance(rows, list) or len(rows) > 64:
            raise ValueError("bounded reading list required")
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("reading object required")
            name, status, source = row.get("sensor_id"), row.get("status"), row.get("source")
            if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", name) or name in seen:
                raise ValueError("invalid or duplicate reading identity")
            seen.add(name)
            if not isinstance(status, str) or status not in STATUSES:
                status = "unknown"
            # Only source metadata emitted by this existing producer is admitted.
            if not isinstance(source, str) or not re.fullmatch(r"(?:git:HEAD|unit:[A-Za-z0-9_.@-]+\.service|ast:ofn/[A-Za-z0-9_./-]+\.py)", source):
                source, status = None, "unknown"
            value = row.get("value")
            if group in {"processes", "capabilities"}:
                if type(value) is not bool or (status == "healthy" and value is not True) or (status == "absent" and value is not False):
                    status = "unknown"
            observed = _epoch(row.get("observed_epoch"))
            projection.append({"group": group, "sensor_id": name, "status": status,
                               "source": source, "observed_at": observed})
    if len(projection) > 128:
        raise ValueError("observation budget exceeded")
    projection.sort(key=lambda row: row["sensor_id"])
    source_hash = digest(projection)
    registry = default_registry()
    registry.register_source(SOURCE, "observed_self_model", "ofn/adapters/self_model_producer.py")
    observations = []
    for row in projection:
        metric = "self_model." + row["sensor_id"] + ".status"
        registry.register_metric(MetricSpec(metric, "enum", (SOURCE,), process_max_age,
                                            process_max_age, 0, False, "last"))
        quality = "STALE" if row["status"] == "stale" else "MISSING" if row["status"] in {"unknown", "failed"} else "VALID"
        observations.append(observation_from_dict({
            "observation_id": digest({"row": row, "source_hash": source_hash,
                                       "node_id": node_id, "boot_id": boot_id}),
            "source_id": SOURCE, "metric": metric,
            "value": row["status"] if row["status"] != "unknown" else None,
            "unit": "enum", "occurred_at": row["observed_at"],
            "recorded_at": now, "decision_time": now, "beat": None,
            "boot_id": boot_id, "node_id": node_id, "process_id": None,
            "provenance_path": row["source"] or "unknown:self_model",
            "source_hash": source_hash, "quality": quality,
            "quality_reasons": ["STATUS_OBSERVATION_NOT_PHYSIOLOGY_MEASUREMENT"],
            "latest_only": True, "historical_claim": False}))
    case = {"case_id": source_hash, "label": "REDACTED_SNAPSHOT", "sent_at": now,
            "ttl_s": process_max_age, "observations": [o.to_dict() for o in observations]}
    signal = envelope(case, now)
    pipeline = run_shadow_pipeline(observations, decision_time=now, boot_id=boot_id, registry=registry)
    organs = [{"id": r["sensor_id"], "observed_status": r["status"], "source": r["source"]}
              for r in projection if r["group"] == "processes"]
    declared_graph = analyze_topology({"organs": organs, "links": [], "required_organs": []})
    topology = {"connectivity_state": "UNKNOWN", "measured_isolation": None,
                "measured_degradation": None, "declared_graph_analysis": declared_graph,
                "scope": "incomplete declared graph, not measured runtime connectivity",
                "executable": False}
    resources = assess_resources(pipeline["observations"])
    result = {"schema": SCHEMA, "evaluated_at": now, "node_id": node_id, "boot_id": boot_id,
              "source_snapshot_hash": source_hash, "source_observations": projection,
              "source_hash_scope": "canonical redacted status projection, not original artifact bytes",
              "signal": signal, "pipeline": pipeline, "topology": topology,
              "resources": resources, "business_legs": account_legs([]),
              "calibration": calibration_report([]), "research_ids": list(RESEARCH_IDS),
              "body_state": pipeline["homeostatic_assessment"]["global_state"],
              "evidence_scope": "ACTUAL_SELF_MODEL_STATUS_ROWS_ONLY; no invented physiology, cost, trials or neural links",
              "unknown_inputs": ["physiology metrics", "inter-organ links/deadlines", "business cost attribution", "prediction outcomes"],
              "node_identity_scope": "explicit caller identity or unknown; never inferred from checkout",
              "action_authority": "NONE", "executable": False}
    assert_shadow(result)
    result["assessment_hash"] = digest(result)
    return result


def record_assessment(assessment, state_root, *, code_provenance=None):
    """Append bounded source-bearing advisory evidence; never truncate or repair."""
    assert_shadow(assessment)
    expected = dict(assessment)
    stored_hash = expected.pop("assessment_hash")
    if digest(expected) != stored_hash:
        raise ValueError("assessment integrity mismatch")
    root = no_reparse(state_root).resolve()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if root.stat().st_mode & 0o077 and os.name != "nt":
        raise ValueError("advisory state directory must be owner-private")
    # The imported ledger predates path hardening. Guard all fixed writer paths
    # here, including its lock files and atomic derived-file staging paths.
    for name in ("WRITER.jsonl", "WRITER.jsonl.lock", "journal.jsonl", "journal.jsonl.lock",
                 "checkpoint.json", "checkpoint.json.pending", "OWNER-INBOX.md", "OWNER-INBOX.md.pending"):
        no_reparse(root / name)
    budget = ArtifactBudget(root)
    guard = EvidenceStore(root / "WRITER.jsonl")
    with guard._locked():
        store = EvidenceStore(root / "journal.jsonl")
        verify_checkpoint(root / "checkpoint.json", "organism-shadow.v1", store.records)
        payload = {"assessment": assessment, "code_provenance": code_provenance,
                   "executable": False}
        assert_shadow(payload)
        event_digest = digest(payload)
        event = "assessment:" + event_digest
        budget.require(4096)
        if not any(r["event_id"] == event for r in store.records):
            budget.require(len(canonical(payload).encode("utf-8")) + 4096)
        store.append_record("decision", event, payload)
        memory = Experience(store)
        memory.remember({"id": event_digest, "occurred_at": assessment["evaluated_at"],
                         "recorded_at": assessment["evaluated_at"],
                         "payload": {"assessment_hash": stored_hash, "body_state": assessment["body_state"],
                                     "node_id": assessment["node_id"], "boot_id": assessment["boot_id"]},
                         "supersedes": None})
        if assessment["unknown_inputs"]:
            request_owner(store, "SHADOW-SENSOR-COVERAGE: declare real physiology/link/cost/outcome sources before interpreting organism readiness",
                          {"missing": assessment["unknown_inputs"], "executable": False})
        write_inbox(store, root / "OWNER-INBOX.md", budget)
        save_checkpoint(root / "checkpoint.json", "organism-shadow.v1",
                        sum(r["kind"] == "decision" for r in store.records), store, budget)
        return {"state": "COMMITTED_ADVISORY", "assessment_hash": stored_hash,
                "journal_head": store.head, "logical_records": len(store.records),
                "recall": memory.query(valid_at=assessment["evaluated_at"], known_at=assessment["evaluated_at"]),
                "owner_requests": owner_states(store), "budget_cap_bytes": budget.cap_bytes,
                "journal_cap_bytes": store.max_bytes, "executable": False}
