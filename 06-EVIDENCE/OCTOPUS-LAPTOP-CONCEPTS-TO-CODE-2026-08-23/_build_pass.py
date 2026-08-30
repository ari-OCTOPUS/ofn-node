# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
import hashlib, json, shutil
from datetime import datetime, timezone

EVROOT = Path(r"F:\backup\06-EVIDENCE\OCTOPUS-LAPTOP-CONCEPTS-TO-CODE-2026-08-23")
LIB = Path(r"F:\backup\agents\octopus_evidence")
OPS_EP = Path(r"F:\backup\_ops\evidence_plane")
BRIEF = Path(r"F:\backup\06-EVIDENCE\OCTOPUS-LAPTOP-AGENT-OWNER-BRIEF-2026-08-22")
OBSIDIAN = Path(r"F:\backup\07 - Knowledge\octopus\94-CONCEPTS-TO-CODE-2026-08-23.md")
WIRING = Path(r"F:\backup\_ops\organs\WIRING.json")
COLLECTED_AT = "2026-08-23T00:34:00+10:00"
COLLECTOR = "laptop-agent-concepts-to-code"

CONNECTOR_EVIDENCE = r'''"""Connector Evidence Record rules (ADR-LAPTOP-AGENT-DECISIONS-2026-08-22).

Extends organism evidence plane with connector-facing fields required for
Similarweb/estimate and CONNECTOR-GAP discipline.

Prefer this module for connector outputs. Existing modules:
- _ops/shadow_homeostasis/evidence_store.py (lab observation JSONL)
- _ops/epistemics/schemas.py EvidenceLink (claim links; no estimate/valid_for)
- _ops/evidence_plane/* (capability registry / events)

Rule: missing evidence_id OR invalid source_type -> unverified=True.
Estimates require confidence + valid_for.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable
import hashlib
import re

SCHEMA = "octopus-connector-evidence.v1"
VALID_SOURCE_TYPES = frozenset({
    "runtime",
    "connector_result",
    "owner_statement",
    "file_line",
    "command_output",
    "test_artifact",
    "derived",
    "manifest",
    "owner-brief",
    "unknown",
})


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def is_valid_source_type(source_type: Any) -> bool:
    if not isinstance(source_type, str):
        return False
    st = source_type.strip()
    return bool(st) and st in VALID_SOURCE_TYPES


def is_valid_evidence_id(evidence_id: Any) -> bool:
    if not isinstance(evidence_id, str):
        return False
    eid = evidence_id.strip()
    if not eid:
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9_.:/-]{8,200}", eid))


def compute_evidence_id(*parts: str) -> str:
    raw = "||".join(str(p) for p in parts).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def normalize_record(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize a connector/evidence datum and apply unverified rule."""
    data = dict(raw or {})
    evidence_id = data.get("evidence_id")
    source_type = data.get("source_type")

    missing_id = not is_valid_evidence_id(evidence_id)
    invalid_st = not is_valid_source_type(source_type)
    unverified = bool(missing_id or invalid_st)

    estimate = data.get("estimate")
    is_estimate = bool(data.get("is_estimate")) or estimate is not None or data.get("label") == "estimate"

    confidence = data.get("confidence")
    valid_for = data.get("valid_for")

    out = {
        "schema": SCHEMA,
        "evidence_id": evidence_id if not missing_id else None,
        "source_type": source_type if not invalid_st else None,
        "captured_at": data.get("captured_at") or _now_iso(),
        "label": data.get("label"),
        "estimate": estimate,
        "is_estimate": is_estimate,
        "confidence": confidence,
        "valid_for": valid_for,
        "value": data.get("value"),
        "scope": data.get("scope"),
        "source_ref": data.get("source_ref"),
        "unverified": unverified,
        "unverified_reasons": [],
    }
    if missing_id:
        out["unverified_reasons"].append("missing_or_invalid_evidence_id")
    if invalid_st:
        out["unverified_reasons"].append("missing_or_invalid_source_type")
    if is_estimate:
        if confidence is None:
            out["unverified"] = True
            out["unverified_reasons"].append("estimate_missing_confidence")
        if not valid_for:
            out["unverified"] = True
            out["unverified_reasons"].append("estimate_missing_valid_for")
    return out


def validate_batch(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    normalized = [normalize_record(r) for r in records]
    return {
        "schema": SCHEMA + ".batch",
        "count": len(normalized),
        "unverified_count": sum(1 for r in normalized if r["unverified"]),
        "records": normalized,
    }
'''

CONNECTOR_GAP = r'''"""CONNECTOR-GAP runtime hook.

Loads CONNECTOR-GAP-REGISTRY.json from the owner-brief / concepts-to-code
evidence package and marks GA4 / GSC / Ads as GAP until OAuth + owner signature.

No secrets. No OAuth automation. Read-only registry load.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_REGISTRY_CANDIDATES = (
    Path(r"F:\backup\06-EVIDENCE\OCTOPUS-LAPTOP-CONCEPTS-TO-CODE-2026-08-23\CONNECTOR-GAP-REGISTRY.json"),
    Path(r"F:\backup\06-EVIDENCE\OCTOPUS-LAPTOP-AGENT-OWNER-BRIEF-2026-08-22\CONNECTOR-GAP-REGISTRY.json"),
)


def resolve_registry_path(explicit: str | Path | None = None) -> Path:
    if explicit:
        p = Path(explicit)
        if not p.exists():
            raise FileNotFoundError(str(p))
        return p
    for c in DEFAULT_REGISTRY_CANDIDATES:
        if c.exists():
            return c
    raise FileNotFoundError("CONNECTOR-GAP-REGISTRY.json not found in known evidence paths")


def load_registry(path: str | Path | None = None) -> dict[str, Any]:
    p = resolve_registry_path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    data["_loaded_from"] = str(p)
    return data


def connector_status(registry: dict[str, Any], connector: str) -> dict[str, Any]:
    name = connector.strip()
    for gap in registry.get("gaps") or []:
        if str(gap.get("connector", "")).strip().lower() == name.lower():
            return {
                "connector": gap.get("connector"),
                "gap_id": gap.get("gap_id"),
                "status": gap.get("status"),
                "is_gap": True,
                "metrics_allowed": False,
                "reason": gap.get("reason"),
                "required_owner_action": gap.get("required_owner_action"),
                "gate": gap.get("gate"),
            }
    for item in registry.get("connector_probe_queue") or []:
        if str(item.get("connector", "")).strip().lower() == name.lower():
            return {
                "connector": item.get("connector"),
                "status": item.get("status"),
                "is_gap": False,
                "metrics_allowed": False,
                "output_policy": item.get("output_policy"),
                "reason": "pending_runtime_probe_no_invent",
            }
    return {
        "connector": name,
        "status": "UNKNOWN_NOT_IN_REGISTRY",
        "is_gap": True,
        "metrics_allowed": False,
        "reason": "unlisted_connector_treated_as_gap",
    }


def mark_oauth_gaps(registry: dict[str, Any] | None = None) -> dict[str, Any]:
    reg = registry or load_registry()
    out = []
    for name in ("GA4", "GSC", "Google Ads"):
        st = connector_status(reg, name)
        st["gap_until_oauth"] = True
        st["metrics_allowed"] = False
        if st.get("status") in (None, "UNKNOWN_NOT_IN_REGISTRY"):
            st["status"] = "WAITING_OWNER_OAUTH"
            st["is_gap"] = True
        out.append(st)
    return {
        "as_of_registry": reg.get("as_of"),
        "loaded_from": reg.get("_loaded_from"),
        "oauth_gaps": out,
        "hard_rules": reg.get("hard_rules") or [],
    }


if __name__ == "__main__":
    print(json.dumps(mark_oauth_gaps(), indent=2))
'''

INIT_PY = '''"""OCTOPUS connector evidence + CONNECTOR-GAP stubs.

Runtime SoT code also mirrored under:
  F:\\\\backup\\\\_ops\\\\evidence_plane\\\\connector_evidence.py
  F:\\\\backup\\\\_ops\\\\evidence_plane\\\\connector_gap_loader.py
"""
from .connector_evidence import (
    SCHEMA,
    VALID_SOURCE_TYPES,
    normalize_record,
    validate_batch,
    compute_evidence_id,
    is_valid_evidence_id,
    is_valid_source_type,
)
from .connector_gap_loader import (
    load_registry,
    connector_status,
    mark_oauth_gaps,
    resolve_registry_path,
)

__all__ = [
    "SCHEMA",
    "VALID_SOURCE_TYPES",
    "normalize_record",
    "validate_batch",
    "compute_evidence_id",
    "is_valid_evidence_id",
    "is_valid_source_type",
    "load_registry",
    "connector_status",
    "mark_oauth_gaps",
    "resolve_registry_path",
]
'''

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def inventory_item(path: Path, classification: str = "internal") -> dict:
    st = path.stat()
    # Windows mtime -> local ISO with +10 approx using timezone aware from timestamp
    mt = datetime.fromtimestamp(st.st_mtime).astimezone().isoformat(timespec='seconds')
    return {
        "path": str(path),
        "size_bytes": int(st.st_size),
        "modified_at": mt,
        "sha256": sha256_file(path),
        "classification": classification,
    }

def inventory_digest(items: list[dict]) -> dict:
    ordered = sorted(items, key=lambda x: x['path'])
    lines = [f"{it['path']}:{it['sha256']}" for it in ordered]
    digest = sha256_text("\n".join(lines) + ("\n" if lines else ""))
    return {"algorithm": "sha256", "ordered_by": "path", "digest_sha256": digest}

def claim(claim_id, statement, status, source_id, locator_kind, locator_value, scope, confidence, value=None, limitations=None):
    return {
        "claim_id": claim_id,
        "statement": statement,
        "value": value,
        "status": status,
        "source_id": source_id,
        "source_locator": {"kind": locator_kind, "value": locator_value},
        "fetched_at": COLLECTED_AT,
        "scope": scope,
        "hash_sha256": sha256_text(statement),
        "confidence": confidence,
        "limitations": limitations or [],
    }

def named(name, status, locator_kind, locator_value, detail=None):
    d = {
        "name": name,
        "status": status,
        "source_locator": {"kind": locator_kind, "value": locator_value},
    }
    if detail is not None:
        d["detail"] = detail
    return d

def service(service, port, protocol, status, locator_kind, locator_value, bind=None):
    d = {
        "service": service,
        "port": port,
        "protocol": protocol,
        "status": status,
        "source_locator": {"kind": locator_kind, "value": locator_value},
    }
    if bind:
        d["bind_address"] = bind
    return d

def handoff(path: Path, status="verified"):
    if not path.exists():
        return {
            "path": str(path),
            "size_bytes": 0,
            "modified_at": COLLECTED_AT,
            "sha256": "0"*64,
            "status": "missing",
        }
    it = inventory_item(path)
    return {
        "path": it["path"],
        "size_bytes": it["size_bytes"],
        "modified_at": it["modified_at"],
        "sha256": it["sha256"],
        "status": status,
    }

def write_lib():
    LIB.mkdir(parents=True, exist_ok=True)
    OPS_EP.mkdir(parents=True, exist_ok=True)
    code_dir = EVROOT / 'code'
    code_dir.mkdir(parents=True, exist_ok=True)

    schema_json = {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "$id": "octopus://schemas/connector-evidence/v1",
      "title": "OCTOPUS Connector Evidence Record v1",
      "type": "object",
      "required": ["evidence_id", "source_type", "captured_at"],
      "properties": {
        "evidence_id": {"type": "string", "minLength": 8},
        "source_type": {"type": "string", "enum": sorted([
            "runtime","connector_result","owner_statement","file_line","command_output",
            "test_artifact","derived","manifest","owner-brief","unknown"])},
        "captured_at": {"type": "string"},
        "label": {"type": ["string", "null"]},
        "estimate": {},
        "is_estimate": {"type": "boolean"},
        "confidence": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
        "valid_for": {"type": ["string", "null"]},
        "value": {},
        "scope": {"type": ["string", "null"]},
        "source_ref": {"type": ["string", "null"]},
        "unverified": {"type": "boolean"}
      }
    }
    wiring_pointer = {
      "schema": "octopus-evidence-wiring-pointer/1",
      "reversible": True,
      "rollback": "set connector_gap_hook=false in F:\\backup\\_ops\\organs\\WIRING.json; remove agents/octopus_evidence/WIRING.json if desired",
      "organism_wiring": str(WIRING),
      "flag": "connector_gap_hook",
      "modules": {
        "agents_stub": str(LIB),
        "runtime_evidence_plane": str(OPS_EP),
        "connector_evidence": str(OPS_EP / "connector_evidence.py"),
        "connector_gap_loader": str(OPS_EP / "connector_gap_loader.py"),
        "registry": str(EVROOT / "CONNECTOR-GAP-REGISTRY.json"),
      },
      "existing_related": [
        r"F:\backup\_ops\shadow_homeostasis\evidence_store.py",
        r"F:\backup\_ops\epistemics\schemas.py",
        r"F:\backup\_ops\evidence_plane\registry.py",
      ],
      "notes": "GA4/GSC/Ads remain GAP until OAuth + owner signature. No invent metrics."
    }

    (LIB / '__init__.py').write_text(INIT_PY, encoding='utf-8')
    (LIB / 'connector_evidence.py').write_text(CONNECTOR_EVIDENCE, encoding='utf-8')
    (LIB / 'connector_gap_loader.py').write_text(CONNECTOR_GAP, encoding='utf-8')
    (LIB / 'connector_evidence.schema.json').write_text(json.dumps(schema_json, indent=2), encoding='utf-8')
    (LIB / 'WIRING.json').write_text(json.dumps(wiring_pointer, indent=2), encoding='utf-8')
    (LIB / 'README.md').write_text(
        "# octopus_evidence\n\nLibrary stub for connector Evidence Store rules + CONNECTOR-GAP loader.\n\n"
        "- Runtime mirrors: `_ops/evidence_plane/connector_*.py`\n"
        "- Related existing: `shadow_homeostasis/evidence_store.py`, `epistemics/schemas.py` EvidenceLink\n"
        "- Rule: missing `evidence_id` OR invalid `source_type` => `unverified=true`\n"
        "- Estimates require `confidence` + `valid_for`\n"
        "- No secrets. No OAuth automation. No WAVE0 unlock. No mining.\n",
        encoding='utf-8')

    (OPS_EP / 'connector_evidence.py').write_text(CONNECTOR_EVIDENCE, encoding='utf-8')
    (OPS_EP / 'connector_gap_loader.py').write_text(CONNECTOR_GAP, encoding='utf-8')
    (code_dir / 'connector_evidence.py').write_text(CONNECTOR_EVIDENCE, encoding='utf-8')
    (code_dir / 'connector_gap_loader.py').write_text(CONNECTOR_GAP, encoding='utf-8')
    (code_dir / 'connector_evidence.schema.json').write_text(json.dumps(schema_json, indent=2), encoding='utf-8')

def patch_wiring():
    data = json.loads(WIRING.read_text(encoding='utf-8'))
    # backup reversible
    bak = WIRING.with_suffix('.json.bak-2026-08-23-concepts-to-code')
    if not bak.exists():
        bak.write_text(json.dumps(data, indent=2) + "\n", encoding='utf-8')
    flags = data.setdefault('flags', {})
    flags['connector_gap_hook'] = True
    # keep rollback note
    data['rollback'] = (
        "set any flag false; sidecar stops emitting; no organism restart required; "
        "connector_gap_hook=false disables CONNECTOR-GAP loader reference"
    )
    hooks = data.setdefault('hooks', {})
    hooks['connector_gap'] = {
        "enabled_flag": "connector_gap_hook",
        "module": r"F:\backup\_ops\evidence_plane\connector_gap_loader.py",
        "registry": str(EVROOT / "CONNECTOR-GAP-REGISTRY.json"),
        "marks_gap_until_oauth": ["GA4", "GSC", "Google Ads"],
        "reversible": True,
    }
    WIRING.write_text(json.dumps(data, indent=2) + "\n", encoding='utf-8')
    return bak

def base_node(node_id, hardware, os_name, hostname, discovery):
    brief = str(BRIEF / 'OWNER-BRIEF.md')
    return {
        "node_id": node_id,
        "hardware": hardware,
        "os": os_name,
        "hostname": hostname,
        "ip_or_discovery_method": discovery,
        "repo_paths": [r"F:\backup"],
        "canonical_repo_candidates": [
            {
                "path": r"F:\backup",
                "rationale": "Owner SoT single-home",
                "status": "canonical",
                "source_locator": {"kind": "owner_statement", "value": brief + "#SoT"},
            }
        ],
        "current_branch_and_commit": [],
        "agent_runtime": "Cursor ExternalShell laptop-agent",
        "services_and_ports": [],
        "message_transport": [],
        "event_schemas": [],
        "data_stores": [],
        "memory_stores": [],
        "secrets_file_names_only": [".env"],
        "feature_flags": [],
        "kill_switches": [],
        "test_commands": [],
        "last_test_results": [],
        "active_projects": [],
        "owner_decisions": [],
        "known_failures": [],
        "open_gates": [],
        "telegram_components": [],
        "webapp_components": [],
        "internet_access_path": [],
        "handoff_files": [],
    }

def build_packs():
    packs_dir = EVROOT / 'node-packs'
    packs_dir.mkdir(parents=True, exist_ok=True)

    # inventory sources shared
    inv_sources = [
        BRIEF / 'OWNER-BRIEF.md',
        BRIEF / 'ADR-LAPTOP-AGENT-DECISIONS-2026-08-22.md',
        BRIEF / 'CONNECTOR-GAP-REGISTRY.json',
        BRIEF / 'NODE-PACK-BUSINESS.schema.json',
        BRIEF / 'NODE-PACK-SENSORIUM.schema.json',
        BRIEF / 'NODE-PACK-LAPTOP.schema.json',
        Path(r'F:\backup\07 - Knowledge\octopus\01-BUSINESS-MAP-CANONICAL.md'),
        Path(r'F:\backup\06-EVIDENCE\OCTOPUS-HANDOFF-MERGE-2026-08-22\merged\CURRENT-TRUTH.md'),
    ]
    inv = [inventory_item(p) for p in inv_sources if p.exists()]
    dig = inventory_digest(inv)

    synthesis_all = {
        "business_pack_received": True,
        "sensorium_pack_received": True,
        "laptop_pack_received": True,
        "can_synthesize": True,
        "pending_reasons": ["PACKS_READY_SYNTHESIS_PENDING"],
    }

    # ---- BUSINESS ----
    bnode = base_node(
        "business-board2",
        "Board2 remote lanes (not local laptop listen)",
        "remote-board2",
        "board2",
        "canonical map + owner-brief live state",
    )
    bnode["services_and_ports"] = [
        service("ziman/GiftMesh", 8791, "https", "unknown", "owner_statement", str(BRIEF/'OWNER-BRIEF.md')+":Ziman LIVE", "ziman.master-painting.com"),
        service("lead/master-painting", 8792, "https", "unknown", "owner_statement", str(BRIEF/'OWNER-BRIEF.md')+":Lead LIVE", "lead.master-painting.com"),
        service("studio", 8793, "https", "unknown", "owner_statement", str(BRIEF/'OWNER-BRIEF.md')+":Studio LIVE", "studio.master-painting.com"),
        service("panel", 8794, "https", "unknown", "owner_statement", r"F:\backup\07 - Knowledge\octopus\01-BUSINESS-MAP-CANONICAL.md#:8794", "panel"),
    ]
    bnode["active_projects"] = [
        named("Master Painting lead campaign", "verified", "owner_statement", str(BRIEF/'OWNER-BRIEF.md')+":Lead", "existing 8 CRM leads running; no money invent"),
        named("Ziman public catalog", "verified", "owner_statement", str(BRIEF/'OWNER-BRIEF.md')+":Ziman", "activated=true"),
        named("Studio library-only posts", "verified", "owner_statement", str(BRIEF/'OWNER-BRIEF.md')+":Studio", "consent + shot-0001 publish PASS"),
        named("Mining", "missing", "owner_statement", str(BRIEF/'OWNER-BRIEF.md')+":Mining", "SEPARATE DEFERRED — do not work"),
    ]
    bnode["owner_decisions"] = [
        named("GA4/GSC/Ads CONNECTOR-GAP", "verified", "file_line", str(BRIEF/'CONNECTOR-GAP-REGISTRY.json'), "WAITING_OWNER_OAUTH"),
        named("Similarweb Premium ADOPT estimate-only", "verified", "file_line", str(BRIEF/'ADR-LAPTOP-AGENT-DECISIONS-2026-08-22.md'), "estimate+evidence_id+confidence+valid_for"),
        named("Mining deferred", "verified", "owner_statement", str(BRIEF/'OWNER-BRIEF.md')+":non-actions", "no mining work"),
    ]
    bnode["open_gates"] = [
        named("D1/D7 owner gates", "verified", "owner_statement", str(BRIEF/'ADR-LAPTOP-AGENT-DECISIONS-2026-08-22.md'), "binding for irreversible"),
        named("OAuth GA4/GSC/Ads", "unverified", "file_line", str(BRIEF/'CONNECTOR-GAP-REGISTRY.json'), "gap until OAuth"),
    ]
    bnode["webapp_components"] = [
        named("lead.master-painting.com", "verified", "owner_statement", str(BRIEF/'OWNER-BRIEF.md'), "LIVE"),
        named("ziman.master-painting.com", "verified", "owner_statement", str(BRIEF/'OWNER-BRIEF.md'), "LIVE"),
        named("studio.master-painting.com", "verified", "owner_statement", str(BRIEF/'OWNER-BRIEF.md'), "LIVE library-only"),
    ]
    bnode["telegram_components"] = [
        named("Studio shot-0001 Telegram publish", "verified", "owner_statement", "BOARD2-STUDIO-PUBLISH-DRAIN-2026-08-22", "PASS"),
    ]
    bnode["known_failures"] = [
        named("Money metrics invent forbidden", "verified", "owner_statement", "BOARD2-MONEY-NA-2026-08-22", "no invent money"),
    ]
    bnode["handoff_files"] = [
        handoff(BRIEF / 'OWNER-BRIEF.md'),
        handoff(Path(r'F:\backup\07 - Knowledge\octopus\01-BUSINESS-MAP-CANONICAL.md')),
    ]
    bnode["test_commands"] = [
        {"command": "Get-NetTCPConnection -State Listen | ? LocalPort -in 8791,8792,8793", "purpose": "local listen probe (Board2 may be remote)"},
    ]
    bnode["last_test_results"] = [
        {
            "command": "Get-NetTCPConnection ... 8791,8792,8793",
            "executed_at": COLLECTED_AT,
            "status": "pass",
            "summary": "No local listen on laptop for 8791/8792/8793; Board2 LIVE remains owner-brief claim (remote).",
            "evidence_ref": str(EVROOT / 'RESULT.json'),
            "source_locator": {"kind": "command_output", "value": "ExternalShell listen probe 2026-08-23"},
        }
    ]
    business = {
        "pack_version": "1.0",
        "node_role": "business",
        "collected_at": COLLECTED_AT,
        "collector": COLLECTOR,
        "collection_method": "mixed",
        "node": bnode,
        "inventory": inv,
        "inventory_digest": dig,
        "claims": [
            claim("B-001", "Three live brands only: Master Painting, Ziman, Studio; Mining deferred", "verified", "OWNER-BRIEF", "owner_statement", str(BRIEF/'OWNER-BRIEF.md')+":canonical businesses", "business", 0.99, value=["master-painting","ziman","studio"]),
            claim("B-002", "Ziman public catalog activated=true", "verified", "OWNER-BRIEF", "owner_statement", str(BRIEF/'OWNER-BRIEF.md')+":Ziman", "ziman", 0.9),
            claim("B-003", "Studio consent + shot-0001 Telegram publish PASS (library-only)", "verified", "OWNER-BRIEF", "owner_statement", str(BRIEF/'OWNER-BRIEF.md')+":Studio", "studio", 0.9),
            claim("B-004", "Lead/Painting campaign running on existing 8 CRM leads", "verified", "OWNER-BRIEF", "owner_statement", str(BRIEF/'OWNER-BRIEF.md')+":Lead", "master-painting", 0.9),
            claim("B-005", "No money figures invented in this pack", "verified", "ADR", "owner_statement", str(BRIEF/'ADR-LAPTOP-AGENT-DECISIONS-2026-08-22.md')+":connector-first", "business", 1.0, limitations=["BOARD2-MONEY-NA"]),
            claim("B-006", "GA4/GSC/Ads are CONNECTOR-GAP until OAuth", "verified", "CONNECTOR-GAP", "file_line", str(BRIEF/'CONNECTOR-GAP-REGISTRY.json'), "connectors", 1.0),
        ],
        "contradictions": [],
        "open_questions": [
            "Board2 ports 8791/8792/8793 not listening on laptop; remote liveness beyond owner-brief not re-probed this pass",
            "OAuth timing for GA4/GSC/Ads unknown",
        ],
        "synthesis_lock": synthesis_all,
        "business_scope": ["master-painting", "ziman", "studio", "mining"],
    }

    # ---- SENSORIUM ----
    snode = base_node(
        "sensorium-orangepi",
        "Orange Pi + ESP32 Phase A (inet feeds); Phase B hardware deferred",
        "linux-orangepi",
        "orangepi",
        "Pi evidence folders + CURRENT-TRUTH + owner-brief",
    )
    snode["services_and_ports"] = [
        service("MQTT", 1883, "tcp", "closed", "owner_statement", str(Path(r'F:\backup\06-EVIDENCE\OCTOPUS-HANDOFF-MERGE-2026-08-22\merged\CURRENT-TRUTH.md'))+":MQTT CLOSED"),
        service("LAN metrics", 9101, "http", "open", "owner_statement", str(Path(r'F:\backup\06-EVIDENCE\OCTOPUS-HANDOFF-MERGE-2026-08-22\merged\CURRENT-TRUTH.md'))+":lan_9101", "192.168.0.182"),
    ]
    snode["feature_flags"] = [
        named("WAVE0 hardware", "verified", "owner_statement", "CURRENT-TRUTH WAVE0 KEEP_LOCKED", "KEEP_LOCKED / BLOCKED_NEED_ESTOP"),
        named("software_only_a0", "verified", "owner_statement", "CURRENT-TRUTH SOFTWARE_ONLY_A0", "overlay enabled; no actuator authority"),
        named("actuator_authority", "verified", "owner_statement", "CURRENT-TRUTH actuator_authority=NONE", "NONE"),
    ]
    snode["kill_switches"] = [
        named("WAVE0 hardware lock", "verified", "owner_statement", "ADR/OWNER-BRIEF KEEP_LOCKED", "do not unlock"),
        named("MQTT CLOSED", "verified", "owner_statement", "CURRENT-TRUTH MQTT CLOSED", "no invent PASS"),
    ]
    snode["active_projects"] = [
        named("Inet feeds Phase A", "verified", "owner_statement", str(BRIEF/'OWNER-BRIEF.md')+":Inet feeds Phase A PASS", "7/7 expand; timer 15m; ABC skipped 500"),
        named("ESP32 Phase B", "missing", "owner_statement", str(BRIEF/'OWNER-BRIEF.md')+":ESP32 Phase B DEFERRED", "wait hardware"),
    ]
    snode["internet_access_path"] = [
        named("OPENMETEO", "verified", "owner_statement", "OWNER-BRIEF Phase A", "PASS"),
        named("AQI", "verified", "owner_statement", "OWNER-BRIEF Phase A", "PASS"),
        named("TIME", "verified", "owner_statement", "OWNER-BRIEF Phase A", "PASS"),
        named("FX-AUD", "verified", "owner_statement", "OWNER-BRIEF Phase A", "PASS"),
        named("BOM-SYD", "verified", "owner_statement", "OWNER-BRIEF Phase A", "PASS"),
        named("NEWS-AU Guardian", "verified", "owner_statement", "OWNER-BRIEF Phase A", "PASS"),
        named("USGS-QUAKE", "verified", "owner_statement", "OWNER-BRIEF Phase A", "PASS"),
        named("ABC", "verified", "owner_statement", "OWNER-BRIEF Phase A", "skipped 500"),
    ]
    snode["owner_decisions"] = [
        named("Sensorium shared policy ADOPT", "verified", "file_line", str(BRIEF/'ADR-LAPTOP-AGENT-DECISIONS-2026-08-22.md'), "shared allowlist; separate namespaces"),
        named("No WAVE0 unlock this pass", "verified", "owner_statement", str(BRIEF/'OWNER-BRIEF.md')+":non-actions", "KEEP_LOCKED"),
    ]
    snode["open_gates"] = [
        named("Physical e-stop", "verified", "owner_statement", "Path H BLOCKED_NEED_ESTOP", "LATER"),
        named("MQTT enable", "verified", "owner_statement", "MQTT PARKED/CLOSED", "Enable ABD may exist; listener not open"),
    ]
    snode["known_failures"] = [
        named("ABC feed 500", "verified", "owner_statement", "OWNER-BRIEF Phase A", "skipped"),
    ]
    snode["handoff_files"] = [
        handoff(Path(r'F:\backup\06-EVIDENCE\OCTOPUS-HANDOFF-MERGE-2026-08-22\merged\CURRENT-TRUTH.md')),
        handoff(BRIEF / 'OWNER-BRIEF.md'),
    ]
    sensorium = {
        "pack_version": "1.0",
        "node_role": "sensorium",
        "collected_at": COLLECTED_AT,
        "collector": COLLECTOR,
        "collection_method": "mixed",
        "node": snode,
        "inventory": inv,
        "inventory_digest": dig,
        "claims": [
            claim("S-001", "Inet feeds Phase A PASS 7/7 (ABC skipped 500); timer 15m", "verified", "OWNER-BRIEF", "owner_statement", str(BRIEF/'OWNER-BRIEF.md')+":Inet feeds", "sensorium", 0.95),
            claim("S-002", "WAVE0 hardware KEEP_LOCKED / BLOCKED_NEED_ESTOP", "verified", "CURRENT-TRUTH", "file_line", r"F:\backup\06-EVIDENCE\OCTOPUS-HANDOFF-MERGE-2026-08-22\merged\CURRENT-TRUTH.md", "wave0", 1.0),
            claim("S-003", "MQTT 1883 CLOSED", "verified", "CURRENT-TRUTH", "file_line", r"F:\backup\06-EVIDENCE\OCTOPUS-HANDOFF-MERGE-2026-08-22\merged\CURRENT-TRUTH.md", "mqtt", 1.0),
            claim("S-004", "ESP32 Phase B DEFERRED (no invent UART/pins)", "verified", "OWNER-BRIEF", "owner_statement", str(BRIEF/'OWNER-BRIEF.md')+":ESP32", "esp32", 0.95),
            claim("S-005", "LAN :9101 OPEN on 192.168.0.182 (metrics HTTP 200 claimed)", "verified", "CURRENT-TRUTH", "file_line", r"F:\backup\06-EVIDENCE\OCTOPUS-HANDOFF-MERGE-2026-08-22\merged\CURRENT-TRUTH.md", "lan9101", 0.9, limitations=["laptop firewall verify may still be pending"]),
        ],
        "contradictions": [],
        "open_questions": [
            "Laptop firewall verify for LAN:9101 may still be pending",
            "When physical e-stop arrives, WAVE0 unlock remains owner-gated (not this pass)",
        ],
        "synthesis_lock": synthesis_all,
        "sensorium_scope": ["senses", "laboratory", "connector-gateway", "evidence-store", "verifier"],
    }

    # ---- LAPTOP ----
    lnode = base_node(
        "laptop-center",
        "Windows laptop Center / SoT host",
        "Microsoft Windows 11 Pro N (10.0.26200)",
        "DESKTOP-KA9RFN5",
        "hostname + ExternalShell live probe",
    )
    lnode["services_and_ports"] = [
        service("Board2 lead", 8792, "https", "closed", "command_output", "local listen probe: not listening on laptop"),
        service("Board2 ziman", 8791, "https", "closed", "command_output", "local listen probe: not listening on laptop"),
        service("Board2 studio", 8793, "https", "closed", "command_output", "local listen probe: not listening on laptop"),
        service("MQTT", 1883, "tcp", "closed", "command_output", "local listen probe: not listening on laptop"),
    ]
    lnode["active_projects"] = [
        named("Center process", "verified", "owner_statement", "OCTOPUS-CENTER-RESTART-AFTER-PHASE3 RESULT PASS", "PID 35916 observed among python processes"),
        named("Laptop agent owner brief", "verified", "file_line", str(BRIEF/'OWNER-BRIEF.md'), "OWNER_BRIEF_ACTIVE"),
        named("Concepts→Code parallel pass", "verified", "owner_statement", str(EVROOT), "this evidence package"),
    ]
    lnode["owner_decisions"] = [
        named("SoT F:\\backup", "verified", "owner_statement", str(BRIEF/'OWNER-BRIEF.md'), "single-home"),
        named("JetStream TRIAL Inbox/Outbox first", "verified", "file_line", str(BRIEF/'ADR-LAPTOP-AGENT-DECISIONS-2026-08-22.md'), "pass criteria required"),
        named("Telegram Mini App RO-first", "verified", "file_line", str(BRIEF/'ADR-LAPTOP-AGENT-DECISIONS-2026-08-22.md'), "parallel path forbidden"),
    ]
    lnode["feature_flags"] = [
        named("connector_gap_hook", "verified", "file_line", str(WIRING), "wired true reversible"),
        named("OCTOPUS_DOCTOR_MAY_MERGE", "verified", "owner_statement", "CURRENT-TRUTH", "live flags-loaded"),
    ]
    lnode["message_transport"] = [
        named("Inbox/Outbox default", "verified", "owner_statement", "ADR JetStream TRIAL", "JetStream not promoted"),
    ]
    lnode["data_stores"] = [
        named("F:\\backup SoT", "verified", "owner_statement", "OWNER-BRIEF", "canonical"),
        named("_ops/organs/WIRING.json", "verified", "file_line", str(WIRING), "organism wiring"),
    ]
    lnode["memory_stores"] = [
        named("_ops/state", "unverified", "owner_statement", r"F:\backup\_ops\state", "present; not fully inventoried this pass"),
    ]
    lnode["telegram_components"] = [
        named("Telegram Mini App", "verified", "owner_statement", "ADR ADOPT RO-first", "parallel path forbidden"),
        named("Telegram Payment", "verified", "owner_statement", "ADR TRIAL limited", "one business + auditable receipt only"),
    ]
    lnode["webapp_components"] = [
        named("cp.master-painting.com Phase-3", "verified", "owner_statement", "CURRENT-TRUTH Phase-3 PASS", "CONTROL_URL"),
    ]
    lnode["open_gates"] = [
        named("gap002_registry", "verified", "owner_statement", "CURRENT-TRUTH doctor", "still blocking"),
        named("GitHub DietPi PAT", "verified", "owner_statement", "CURRENT-TRUTH deferred", "pending owner"),
    ]
    lnode["known_failures"] = [
        named("germline index.lock money thematic commit", "verified", "owner_statement", "CURRENT-TRUTH", "do not force / do not remove lock"),
    ]
    lnode["kill_switches"] = [
        named("No external write without owner gate", "verified", "owner_statement", "ADR", "D1/D7"),
    ]
    lnode["test_commands"] = [
        {"command": "hostname; Get-NetTCPConnection listen 8791/8792/8793/1883", "purpose": "laptop live facts"},
        {"command": "python -c import jsonschema; validate node packs", "purpose": "schema validate packs"},
    ]
    lnode["last_test_results"] = [
        {
            "command": "hostname",
            "executed_at": COLLECTED_AT,
            "status": "pass",
            "summary": "DESKTOP-KA9RFN5",
            "evidence_ref": str(EVROOT / 'RESULT.json'),
            "source_locator": {"kind": "command_output", "value": "ExternalShell hostname"},
        },
        {
            "command": "Get-Process python",
            "executed_at": COLLECTED_AT,
            "status": "pass",
            "summary": "PID 35916 present (center AFTER PID from CURRENT-TRUTH)",
            "evidence_ref": "OCTOPUS-CENTER-RESTART-AFTER-PHASE3-2026-08-22",
            "source_locator": {"kind": "command_output", "value": "Get-Process python"},
        },
    ]
    lnode["handoff_files"] = [
        handoff(BRIEF / 'OWNER-BRIEF.md'),
        handoff(BRIEF / 'ADR-LAPTOP-AGENT-DECISIONS-2026-08-22.md'),
        handoff(WIRING),
    ]
    lnode["internet_access_path"] = [
        named("connector-first research", "verified", "owner_statement", "ADR", "Similarweb/Statista/etc; no invent"),
    ]
    laptop = {
        "pack_version": "1.0",
        "node_role": "laptop",
        "collected_at": COLLECTED_AT,
        "collector": COLLECTOR,
        "collection_method": "mixed",
        "node": lnode,
        "inventory": inv,
        "inventory_digest": dig,
        "claims": [
            claim("L-001", "Laptop hostname DESKTOP-KA9RFN5 running Windows 11 Pro N", "verified", "runtime", "command_output", "hostname / OSVersion", "laptop", 1.0, value={"hostname":"DESKTOP-KA9RFN5"}),
            claim("L-002", "Center restart after Phase-3 PASS; PID 35916 still observed", "verified", "CURRENT-TRUTH+runtime", "command_output", "Get-Process python includes 35916", "center", 0.9),
            claim("L-003", "Local ports 8791/8792/8793/1883 not listening on laptop", "verified", "runtime", "command_output", "Get-NetTCPConnection listen probe", "ports", 1.0),
            claim("L-004", "WIRING.json connector_gap_hook wired reversible", "verified", "runtime", "file_line", str(WIRING), "wiring", 1.0),
            claim("L-005", "SoT remains F:\\backup", "verified", "OWNER-BRIEF", "owner_statement", str(BRIEF/'OWNER-BRIEF.md'), "sot", 1.0),
        ],
        "contradictions": [],
        "open_questions": [
            "Full git commit SHA for F:\\backup not captured in this pack (left empty array)",
            "Unsigned ckpt / sign paths remain laptop responsibility (no key export)",
        ],
        "synthesis_lock": synthesis_all,
        "laptop_scope": ["control-plane", "telegram-bot", "miniapp", "self-coding-loop", "policy-gate"],
    }

    paths = {
        "business": packs_dir / "NODE-PACK-BUSINESS.json",
        "sensorium": packs_dir / "NODE-PACK-SENSORIUM.json",
        "laptop": packs_dir / "NODE-PACK-LAPTOP.json",
    }
    paths["business"].write_text(json.dumps(business, indent=2) + "\n", encoding="utf-8")
    paths["sensorium"].write_text(json.dumps(sensorium, indent=2) + "\n", encoding="utf-8")
    paths["laptop"].write_text(json.dumps(laptop, indent=2) + "\n", encoding="utf-8")
    return paths, business, sensorium, laptop

def validate_packs(paths):
    import jsonschema
    mapping = {
        "business": EVROOT / "schemas" / "NODE-PACK-BUSINESS.schema.json",
        "sensorium": EVROOT / "schemas" / "NODE-PACK-SENSORIUM.schema.json",
        "laptop": EVROOT / "schemas" / "NODE-PACK-LAPTOP.schema.json",
    }
    results = {}
    for key, path in paths.items():
        schema = json.loads(mapping[key].read_text(encoding="utf-8"))
        inst = json.loads(path.read_text(encoding="utf-8"))
        jsonschema.validate(inst, schema)
        results[key] = {"path": str(path), "valid": True, "sha256": sha256_file(path)}
    return results

def write_hashes(validate_results):
    lines = []
    for key in ("business", "sensorium", "laptop"):
        p = Path(validate_results[key]["path"])
        lines.append(f"{validate_results[key]['sha256']}  {p.name}")
    # also hash registry + code
    for extra in [
        EVROOT / "CONNECTOR-GAP-REGISTRY.json",
        EVROOT / "code" / "connector_evidence.py",
        EVROOT / "code" / "connector_gap_loader.py",
        LIB / "connector_evidence.py",
        OPS_EP / "connector_evidence.py",
    ]:
        if extra.exists():
            lines.append(f"{sha256_file(extra)}  {extra}")
    text = "\n".join(lines) + "\n"
    (EVROOT / "HASHES.sha256").write_text(text, encoding="utf-8")
    (EVROOT / "node-packs" / "HASHES.sha256").write_text("\n".join(lines[:3]) + "\n", encoding="utf-8")
    return text

def write_gap_map():
    md = f"""---
tags: [octopus, connector-gap, concepts-to-code, 2026-08-23]
date: 2026-08-23
timezone: Australia/Sydney
status: GAP_MAP_ACTIVE
SoT: F:\\backup
---

# GAP-MAP — Concepts→Code (2026-08-23)

## OAuth connector gaps (no invent metrics)

| gap_id | connector | status | until |
|---|---|---|---|
| CG-001 | GA4 | WAITING_OWNER_OAUTH | OAuth + property-mapping signoff (D1/D7) |
| CG-002 | GSC | WAITING_OWNER_OAUTH | OAuth + verified-property binding (D1/D7) |
| CG-003 | Google Ads | WAITING_OWNER_OAUTH | OAuth + account-approval signoff (D1/D7) |

Registry: `{EVROOT / 'CONNECTOR-GAP-REGISTRY.json'}`  
Runtime hook: `_ops/evidence_plane/connector_gap_loader.py` (flag `connector_gap_hook` in `_ops/organs/WIRING.json`)

## Evidence Store gaps addressed this pass

| rule | implementation |
|---|---|
| evidence_id / source_type / estimate / confidence / valid_for | `agents/octopus_evidence/connector_evidence.py` + `_ops/evidence_plane/connector_evidence.py` |
| missing evidence_id OR invalid source_type → unverified | `normalize_record()` |
| estimate requires confidence + valid_for | enforced in `normalize_record()` |

## Explicit non-gaps / non-actions

- WAVE0 hardware remains KEEP_LOCKED (not unlocked)
- MQTT remains CLOSED
- Mining remains deferred
- No secrets written
- No money invent

## Probe queue (not OAuth gaps; still no invent)

Similarweb Premium, Statista, CB Insights, Realtime Finance Data, GitHub, Hugging Face — PENDING_RUNTIME_PROBE per registry.
"""
    (EVROOT / "GAP-MAP.md").write_text(md, encoding="utf-8")

def write_obsidian():
    OBSIDIAN.parent.mkdir(parents=True, exist_ok=True)
    md = f"""---
tags: [octopus, concepts-to-code, node-pack, connector-gap, evidence-store, 2026-08-23]
date: 2026-08-23
timezone: Australia/Sydney
status: PACKS_READY_SYNTHESIS_PENDING
SoT: F:\\backup
---

# 94 — CONCEPTS→CODE (2026-08-23)

Parallel pass converting OWNER-BRIEF / ADR / NODE-PACK schemas / CONNECTOR-GAP into loadable code + filled pack instances.

## Evidence root

`{EVROOT}`

## What landed

### A) Evidence Store rules (CODE)

- Runtime: `F:\\backup\\_ops\\evidence_plane\\connector_evidence.py`
- Stub package: `F:\\backup\\agents\\octopus_evidence\\`
- Fields: `evidence_id`, `source_type`, `estimate`, `confidence`, `valid_for`
- Rule: missing/invalid `evidence_id` OR `source_type` → `unverified=true`
- Existing related (not replaced): `_ops/shadow_homeostasis/evidence_store.py`, `_ops/epistemics/schemas.py` EvidenceLink

### B) NODE-PACK instances (CODE+DATA)

- `node-packs/NODE-PACK-BUSINESS.json`
- `node-packs/NODE-PACK-SENSORIUM.json`
- `node-packs/NODE-PACK-LAPTOP.json`
- Validated against schemas; `HASHES.sha256` written
- `synthesis_status`: **PACKS_READY_SYNTHESIS_PENDING** (all three received+hashed; final synthesis not executed)

### C) CONNECTOR-GAP hook (CODE + reversible WIRING)

- Loader: `_ops/evidence_plane/connector_gap_loader.py`
- Flag: `connector_gap_hook=true` in `_ops/organs/WIRING.json` (backup `.bak-2026-08-23-concepts-to-code`)
- GA4/GSC/Ads marked GAP until OAuth

## Cross-links

- [[93-LAPTOP-AGENT-OWNER-BRIEF]]
- [[01-BUSINESS-MAP-CANONICAL]]
- Evidence: `06-EVIDENCE/OCTOPUS-LAPTOP-CONCEPTS-TO-CODE-2026-08-23/`
"""
    OBSIDIAN.write_text(md, encoding="utf-8")

def write_result(validate_results, bak_path, gap_probe):
    result = {
        "pass": "OCTOPUS-LAPTOP-CONCEPTS-TO-CODE-2026-08-23",
        "collected_at": COLLECTED_AT,
        "timezone": "Australia/Sydney",
        "auth_owner": "Evidence + NODE-PACKs + CONNECTOR-GAP",
        "synthesis_status": "PACKS_READY_SYNTHESIS_PENDING",
        "evidence_root": str(EVROOT),
        "code_vs_docs": {
            "code": [
                str(LIB / "connector_evidence.py"),
                str(LIB / "connector_gap_loader.py"),
                str(OPS_EP / "connector_evidence.py"),
                str(OPS_EP / "connector_gap_loader.py"),
                str(EVROOT / "code" / "connector_evidence.py"),
                str(EVROOT / "code" / "connector_gap_loader.py"),
                str(WIRING) + "#flags.connector_gap_hook + hooks.connector_gap",
            ],
            "docs_data": [
                str(EVROOT / "node-packs" / "NODE-PACK-BUSINESS.json"),
                str(EVROOT / "node-packs" / "NODE-PACK-SENSORIUM.json"),
                str(EVROOT / "node-packs" / "NODE-PACK-LAPTOP.json"),
                str(EVROOT / "HASHES.sha256"),
                str(EVROOT / "GAP-MAP.md"),
                str(EVROOT / "RESULT.json"),
                str(OBSIDIAN),
                str(LIB / "README.md"),
                str(LIB / "WIRING.json"),
                str(LIB / "connector_evidence.schema.json"),
            ],
        },
        "evidence_store": {
            "preferred_existing": [
                r"F:\backup\_ops\shadow_homeostasis\evidence_store.py",
                r"F:\backup\_ops\epistemics\schemas.py",
                r"F:\backup\_ops\evidence_plane\\",
            ],
            "new_runtime_module": str(OPS_EP / "connector_evidence.py"),
            "agents_stub": str(LIB),
            "rule": "missing evidence_id OR invalid source_type -> unverified=true; estimates require confidence+valid_for",
        },
        "node_packs": validate_results,
        "connector_gap": gap_probe,
        "wiring": {
            "path": str(WIRING),
            "backup": str(bak_path),
            "flag": "connector_gap_hook",
            "reversible": True,
        },
        "non_actions_honored": [
            "no secrets",
            "no WAVE0 unlock",
            "no mining",
            "no invent money",
            "no invent MQTT/WAVE0 PASS",
        ],
        "laptop_live": {
            "hostname": "DESKTOP-KA9RFN5",
            "os": "Microsoft Windows 11 Pro N 10.0.26200",
            "local_listen_8791_8792_8793_1883": False,
            "center_pid_observed": 35916,
        },
    }
    (EVROOT / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result

def main():
    write_lib()
    bak = patch_wiring()
    paths, *_ = build_packs()
    validate_results = validate_packs(paths)
    write_hashes(validate_results)
    write_gap_map()
    write_obsidian()
    # smoke gap loader
    import sys
    sys.path.insert(0, str(LIB))
    from connector_gap_loader import mark_oauth_gaps
    from connector_evidence import normalize_record
    gap_probe = mark_oauth_gaps()
    # smoke unverified rule
    bad = normalize_record({"value": 1})
    good = normalize_record({
        "evidence_id": "ev-test-12345678",
        "source_type": "owner-brief",
        "label": "estimate",
        "estimate": {"visits": "unknown"},
        "confidence": 0.4,
        "valid_for": "P7D",
    })
    assert bad["unverified"] is True
    assert good["unverified"] is False
    result = write_result(validate_results, bak, gap_probe)
    print(json.dumps({
        "ok": True,
        "evidence_root": str(EVROOT),
        "synthesis_status": result["synthesis_status"],
        "packs_valid": {k: v["valid"] for k,v in validate_results.items()},
        "pack_hashes": {k: v["sha256"] for k,v in validate_results.items()},
        "wiring_backup": str(bak),
        "obsidian": str(OBSIDIAN),
        "smoke_unverified_missing_id": bad["unverified"],
        "smoke_estimate_ok": (not good["unverified"]),
    }, indent=2))

if __name__ == "__main__":
    main()
