# -*- coding: utf-8 -*-
"""T65 — organ map from live state + code presence. No file deletion."""
from __future__ import annotations

import json
import time
from pathlib import Path

from .paths import STATE, VAULT

CLASSES = ("LIVE", "SKELETON", "ORPHAN", "DEAD", "DUPLICATE", "UNSAFE_TO_WIRE")


def _read(path: Path) -> dict:
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _exists(*parts: str) -> bool:
    return (VAULT.joinpath(*parts)).exists()


def classify_organ(row: dict) -> str:
    if row.get("unsafe"):
        return "UNSAFE_TO_WIRE"
    if row.get("duplicate_of"):
        return "DUPLICATE"
    if row.get("entrypoint_missing"):
        return "DEAD"
    if not row.get("in_live_import_graph") and not row.get("sidecar_wired"):
        return "ORPHAN" if row.get("code_present") else "DEAD"
    if row.get("in_live_import_graph") and row.get("fresh_data") and row.get("telemetry"):
        return "LIVE"
    if row.get("code_present"):
        return "SKELETON"
    return "DEAD"


def build(*, state: Path | None = None, knowledge_wired: bool = False,
          mapper_lists: bool = False) -> dict:
    state = Path(state) if state is not None else STATE
    org = _read(state / "ORGANISM-STATE.json")
    wiring = org.get("wiring") or {}
    legs = (org.get("business_legs") or {}).get("business_legs") or {}
    cart = org.get("cartographer") or {}
    mining_os = (org.get("mining_os") or {}).get("mining_os") or {}
    chrono = ((org.get("chrono") or {}).get("legs_diag") or {})

    catalog = []

    def add(**kw):
        row = dict(kw)
        row.setdefault("afferent_sources", [])
        row.setdefault("efferent_targets", [])
        row.setdefault("state_files_written", [])
        row.setdefault("state_files_read", [])
        row.setdefault("telemetry_metrics", [])
        row.setdefault("tests_present", False)
        row.setdefault("flag_default", "unset")
        row.setdefault("risk_class", "low")
        row["classification"] = classify_organ(row)
        catalog.append(row)

    kn = legs.get("knowledge") or {}
    add(organ_id="knowledge",
        entrypoint_path="_ops/legs/knowledge_leg.py",
        in_live_import_graph=True,
        code_present=True,
        flag_name="(none — status helper always imported)",
        flag_default="on-as-skeleton",
        afferent_sources=["07 - Knowledge/*.md"] if knowledge_wired else [],
        sidecar_wired=knowledge_wired,
        fresh_data=bool(knowledge_wired),
        telemetry=knowledge_wired,
        last_real_data_at="notes age_days=" + str(kn.get("age_days")),
        tests_present=_exists("_ops", "tests", "test_knowledge_leg.py") or _exists("_ops", "tests", "test_organ_cartographer_20260820.py"),
        owner_value_hypothesis="vault notes as real sensory stream",
        risk_class="low",
        live_status=kn)

    add(organ_id="cartographer",
        entrypoint_path="_ops/legs/cartographer_leg.py",
        in_live_import_graph=bool(wiring.get("wire_cartographer")),
        code_present=True,
        flag_name="OCTOPUS_WIRE_CARTOGRAPHER",
        flag_default="paper-full on",
        afferent_sources=["06 - Architecture Maps/MASTER-ARCHITECTURE-*.md", "_ops/*.py mtime"],
        efferent_targets=["proposal cartography_refresh"],
        telemetry=True,
        fresh_data=mapper_lists,  # count was live; lists make it actionable
        sidecar_wired=mapper_lists,
        last_real_data_at=str(cart.get("map_updated")),
        telemetry_metrics=["drift_files", "map_age_days", "mood"],
        tests_present=True,
        owner_value_hypothesis="actionable orphan/dead/duplicate backlog",
        risk_class="low",
        live_status={"drift_files": cart.get("drift_files"), "map_stale": cart.get("map_stale"),
                     "proposals_total": cart.get("proposals_total")})

    lead = legs.get("lead") or {}
    lead_diag = chrono.get("lead-naghshi") or {}
    add(organ_id="lead",
        entrypoint_path="_ops/legs/lead_leg.py",
        in_live_import_graph=bool(wiring.get("wire_lead")),
        code_present=True,
        flag_name="OCTOPUS_WIRE_LEAD",
        flag_default="paper-full on",
        fresh_data=bool(lead.get("live")),
        telemetry=True,
        last_real_data_at=str(lead_diag),
        tests_present=True,
        owner_value_hypothesis="revenue #1 — diagnose only this session",
        risk_class="medium",
        unsafe=False,
        live_status={"live": lead.get("live"), "phi": lead_diag.get("phi"),
                     "state": lead_diag.get("state")})

    mining = legs.get("mining") or {}
    add(organ_id="mining",
        entrypoint_path="_ops/legs/mining_leg.py",
        in_live_import_graph=bool(wiring.get("wire_mining")),
        code_present=True,
        flag_name="OCTOPUS_WIRE_MINING / OCTOPUS_WIRE_MINING_OS",
        flag_default="off / skeleton",
        fresh_data=False,
        telemetry=True,
        last_real_data_at="decisions.jsonl age_days=" + str(mining.get("age_days")),
        tests_present=True,
        owner_value_hypothesis="162-node plan is research, not a live fleet",
        risk_class="high",
        live_status={"live": mining.get("live"), "os_nodes": (mining_os.get("fleet") or {}).get("nodes_total"),
                     "status_known": (mining_os.get("fleet") or {}).get("status_known")})

    crypto = legs.get("crypto") or {}
    add(organ_id="crypto",
        entrypoint_path="_ops/legs/crypto_leg.py",
        in_live_import_graph=True,
        code_present=True,
        flag_name="OCTOPUS_WIRE_INGEST",
        flag_default="off",
        fresh_data=False,
        telemetry=True,
        last_real_data_at="age_days=" + str(crypto.get("age_days")),
        tests_present=True,
        owner_value_hypothesis="stale snapshots, zero trades — map/RFC only",
        risk_class="high",
        live_status=crypto)

    acct = legs.get("accounting") or {}
    add(organ_id="accounting",
        entrypoint_path="_ops/legs/accounting_leg.py",
        in_live_import_graph=True,
        code_present=True,
        flag_name="OCTOPUS_WIRE_ACCT_BEAT",
        flag_default="off for amounts",
        fresh_data=True,
        telemetry=True,
        unsafe=True,  # PII red line for values
        last_real_data_at="age_days=" + str(acct.get("age_days")),
        tests_present=True,
        owner_value_hypothesis="count/mtime already live; amounts forbidden",
        risk_class="high",
        live_status={"live": acct.get("live"), "signal": acct.get("signal")})

    studio = legs.get("studio_pf") or {}
    add(organ_id="studio_pf",
        entrypoint_path="_ops/legs/studio_pf_leg.py",
        in_live_import_graph=True,
        code_present=True,
        flag_name="GATE-STAMP-GO",
        flag_default="gated",
        fresh_data=False,
        telemetry=True,
        unsafe=True,
        tests_present=True,
        owner_value_hypothesis="Project-F gated; map/RFC only",
        risk_class="high",
        live_status={"live": studio.get("live"), "signal": studio.get("signal")})

    sync = legs.get("sync_agent") or {}
    add(organ_id="sync_agent",
        entrypoint_path="_ops/legs/sync_cartographer.py",
        in_live_import_graph=bool(sync.get("enabled")),
        code_present=True,
        flag_name="OCTOPUS_WIRE_SYNC_AGENT",
        flag_default="inert-until-flag-on",
        fresh_data=False,
        telemetry=False,
        tests_present=False,
        owner_value_hypothesis="contracts listed, body inert",
        risk_class="medium",
        live_status=sync)

    add(organ_id="heart",
        entrypoint_path="_ops/heart",
        in_live_import_graph=bool(wiring.get("wire_heart")),
        code_present=True,
        flag_name="OCTOPUS_WIRE_HEART",
        fresh_data=True,
        telemetry=True,
        tests_present=True,
        owner_value_hypothesis="living beat / arbiter",
        risk_class="none",
        live_status=org.get("arbiter"))

    add(organ_id="cortex",
        entrypoint_path="_ops/cortex/cortex.py",
        in_live_import_graph=True,
        code_present=True,
        flag_name="(process)",
        fresh_data=True,
        telemetry=True,
        tests_present=True,
        owner_value_hypothesis="self-maintenance brain; does not hear organ events yet",
        risk_class="low")

    add(organ_id="business_brain",
        entrypoint_path="_ops/cortex/business_brain.py",
        in_live_import_graph=True,
        code_present=True,
        fresh_data=True,
        telemetry=True,
        tests_present=True,
        owner_value_hypothesis="ops brain; same hearing gap",
        risk_class="low")

    add(organ_id="doctor",
        entrypoint_path="_ops/doctor/doctor.py",
        in_live_import_graph=bool(wiring.get("wire_doctor")),
        code_present=True,
        fresh_data=True,
        telemetry=True,
        tests_present=True,
        owner_value_hypothesis="RFC producer; sentinel -1 on unknown root cause",
        risk_class="low")

    add(organ_id="ziman",
        entrypoint_path="_ops/legs/ziman_leg.py",
        in_live_import_graph=bool(wiring.get("wire_ziman")),
        code_present=True,
        fresh_data=True,
        telemetry=True,
        tests_present=True,
        owner_value_hypothesis="gallery inventory — already reporting",
        risk_class="low",
        live_status=org.get("ziman"))

    add(organ_id="afferent_bus",
        entrypoint_path="_ops/afferent/sensory_bus.py",
        in_live_import_graph=bool(wiring.get("wire_school")),
        code_present=True,
        flag_name="OCTOPUS_WIRE_SCHOOL",
        flag_default="paper-full on",
        fresh_data=False,
        telemetry=True,
        tests_present=True,
        owner_value_hypothesis="ratio metric exists; source is spend-shape not world",
        risk_class="low")

    counts = {c: 0 for c in CLASSES}
    for row in catalog:
        counts[row["classification"]] = counts.get(row["classification"], 0) + 1

    return {
        "schema": "organ-map/1",
        "ts": time.time(),
        "organs_total": len(catalog),
        "counts": counts,
        "organs": catalog,
        "agent": "agent_C",
        "executable": False,
    }
