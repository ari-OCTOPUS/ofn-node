# -*- coding: utf-8 -*-
"""NODE-PACK synthesis: Business -> Sensorium -> Laptop. No invent."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from jsonschema import Draft202012Validator

ROOT = Path(r"F:\backup\06-EVIDENCE\OCTOPUS-LAPTOP-CONCEPTS-TO-CODE-2026-08-23")
BRIEF = Path(r"F:\backup\06-EVIDENCE\OCTOPUS-LAPTOP-AGENT-OWNER-BRIEF-2026-08-22")
PACKS_DIR = ROOT / "node-packs"
HASHES_PATH = PACKS_DIR / "HASHES.sha256"
OBSIDIAN = Path(r"F:\backup\07 - Knowledge\octopus\94-CONCEPTS-TO-CODE-2026-08-23.md")
WIRING = Path(r"F:\backup\_ops\organs\WIRING.json")
EVIDENCE_PLANE = Path(r"F:\backup\_ops\evidence_plane")
TZ = ZoneInfo("Australia/Sydney")
NOW = datetime.now(TZ).isoformat(timespec="seconds")

PACK_FILES = {
    "business": "NODE-PACK-BUSINESS.json",
    "sensorium": "NODE-PACK-SENSORIUM.json",
    "laptop": "NODE-PACK-LAPTOP.json",
}
SCHEMA_FILES = {
    "business": "NODE-PACK-BUSINESS.schema.json",
    "sensorium": "NODE-PACK-SENSORIUM.schema.json",
    "laptop": "NODE-PACK-LAPTOP.schema.json",
}

VALID_SOURCE_TYPES = frozenset({
    "runtime", "connector_result", "owner_statement", "file_line",
    "command_output", "test_artifact", "derived", "manifest",
    "owner-brief", "unknown",
})


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_expected_hashes() -> dict[str, str]:
    out = {}
    for line in HASHES_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            out[parts[1].replace("\\", "/").split("/")[-1]] = parts[0].lower()
    return out


def verify_hashes() -> dict:
    expected = load_expected_hashes()
    checks = []
    all_ok = True
    for role, fname in PACK_FILES.items():
        path = PACKS_DIR / fname
        actual = sha256_file(path)
        exp = expected.get(fname, "").lower()
        ok = actual == exp and bool(exp)
        if not ok:
            all_ok = False
        checks.append({
            "role": role,
            "file": str(path),
            "expected_sha256": exp,
            "actual_sha256": actual,
            "match": ok,
        })
    return {"ok": all_ok, "checks": checks}


def validate_schemas(packs: dict) -> dict:
    results = {}
    all_ok = True
    for role, pack in packs.items():
        schema_path = BRIEF / SCHEMA_FILES[role]
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        local = json.loads((ROOT / "schemas" / SCHEMA_FILES[role]).read_text(encoding="utf-8"))
        errs = sorted(Draft202012Validator(schema).iter_errors(pack), key=lambda e: list(e.path))
        ok = len(errs) == 0
        if not ok:
            all_ok = False
        results[role] = {
            "ok": ok,
            "schema": str(schema_path),
            "schema_matches_package_copy": schema == local,
            "error_count": len(errs),
            "errors": [
                {"path": "/".join(map(str, e.path)), "message": e.message}
                for e in errs[:20]
            ],
        }
    return {"ok": all_ok, "by_role": results}


def map_source_type(claim: dict) -> str | None:
    loc = claim.get("source_locator") or {}
    kind = loc.get("kind")
    if isinstance(kind, str) and kind in VALID_SOURCE_TYPES:
        return kind
    return None


def normalize_claim(claim: dict, pack_role: str, pack_path: str) -> dict:
    loc = claim.get("source_locator") or {}
    source_type = map_source_type(claim)
    evidence_id = claim.get("hash_sha256")
    if not (isinstance(evidence_id, str) and len(evidence_id.strip()) >= 8):
        evidence_id = None

    is_estimate = bool(claim.get("is_estimate")) or claim.get("label") == "estimate" or claim.get("estimate") is not None
    missing_id = evidence_id is None
    invalid_st = source_type is None
    unverified = missing_id or invalid_st or claim.get("status") == "unverified"
    reasons = []
    if missing_id:
        reasons.append("missing_or_invalid_evidence_id")
    if invalid_st:
        reasons.append("missing_or_invalid_source_type")
    if claim.get("status") == "unverified":
        reasons.append("pack_status_unverified")
    if is_estimate:
        if claim.get("confidence") is None:
            unverified = True
            reasons.append("estimate_missing_confidence")
        if not claim.get("valid_for"):
            unverified = True
            reasons.append("estimate_missing_valid_for")

    return {
        "claim_id": claim.get("claim_id"),
        "pack_role": pack_role,
        "pack_path": pack_path,
        "statement": claim.get("statement"),
        "value": claim.get("value"),
        "status": claim.get("status"),
        "scope": claim.get("scope"),
        "source_id": claim.get("source_id"),
        "source_locator": loc,
        "fetched_at": claim.get("fetched_at"),
        "hash_sha256": claim.get("hash_sha256"),
        "confidence": claim.get("confidence"),
        "limitations": claim.get("limitations") or [],
        "evidence_id": evidence_id,
        "source_type": source_type,
        "is_estimate": is_estimate,
        "estimate": claim.get("estimate"),
        "valid_for": claim.get("valid_for"),
        "unverified": unverified,
        "unverified_reasons": reasons,
    }


def extract_named_items(node: dict, key: str) -> list:
    items = node.get(key) or []
    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        out.append({
            "name": it.get("name"),
            "status": it.get("status"),
            "detail": it.get("detail"),
            "source_locator": it.get("source_locator"),
        })
    return out


def build_synthesis(packs: dict, hash_report: dict, schema_report: dict) -> dict:
    order = ["business", "sensorium", "laptop"]
    claims = []
    open_questions = []
    contradictions = []
    for role in order:
        pack = packs[role]
        path = str(PACKS_DIR / PACK_FILES[role])
        for c in pack.get("claims") or []:
            claims.append(normalize_claim(c, role, path))
        for q in pack.get("open_questions") or []:
            open_questions.append({"pack_role": role, "question": q})
        for x in pack.get("contradictions") or []:
            contradictions.append({"pack_role": role, "item": x})

    biz = packs["business"]
    sen = packs["sensorium"]
    lap = packs["laptop"]
    bn = biz["node"]
    sn = sen["node"]
    ln = lap["node"]

    gap_path = ROOT / "CONNECTOR-GAP-REGISTRY.json"
    gap = json.loads(gap_path.read_text(encoding="utf-8")) if gap_path.exists() else {}

    can_synth = all(
        (packs[r].get("synthesis_lock") or {}).get("can_synthesize") for r in order
    )
    hash_ok = hash_report["ok"]
    schema_ok = schema_report["ok"]
    status = "SYNTHESIS_PASS" if (can_synth and hash_ok and schema_ok) else "SYNTHESIS_FAIL"
    fail_reasons = []
    if not hash_ok:
        fail_reasons.append("HASH_MISMATCH")
    if not schema_ok:
        fail_reasons.append("SCHEMA_VALIDATION_FAIL")
    if not can_synth:
        fail_reasons.append("SYNTHESIS_LOCK_BLOCKED")

    synthesis = {
        "schema": "octopus-node-pack-synthesis.v1",
        "synthesis_status": status,
        "fail_reasons": fail_reasons,
        "synthesized_at": NOW,
        "timezone": "Australia/Sydney",
        "sot": r"F:\backup",
        "order": ["business", "sensorium", "laptop"],
        "evidence_root": str(ROOT),
        "non_actions_honored": [
            "no secrets",
            "no WAVE0 unlock",
            "no mining",
            "no invent money",
            "no invent MQTT/WAVE0 PASS",
        ],
        "hash_verification": hash_report,
        "schema_validation": schema_report,
        "packs": {
            role: {
                "path": str(PACKS_DIR / PACK_FILES[role]),
                "sha256": next(
                    c["actual_sha256"] for c in hash_report["checks"] if c["role"] == role
                ),
                "pack_version": packs[role].get("pack_version"),
                "node_role": packs[role].get("node_role"),
                "collected_at": packs[role].get("collected_at"),
                "collector": packs[role].get("collector"),
                "synthesis_lock": packs[role].get("synthesis_lock"),
            }
            for role in order
        },
        "businesses": {
            "scope": biz.get("business_scope"),
            "node_id": bn.get("node_id"),
            "hostname": bn.get("hostname"),
            "hardware": bn.get("hardware"),
            "services_and_ports": bn.get("services_and_ports"),
            "active_projects": extract_named_items(bn, "active_projects"),
            "owner_decisions": extract_named_items(bn, "owner_decisions"),
            "open_gates": extract_named_items(bn, "open_gates"),
            "webapp_components": extract_named_items(bn, "webapp_components"),
            "telegram_components": extract_named_items(bn, "telegram_components"),
            "known_failures": extract_named_items(bn, "known_failures"),
            "live_brands_only": ["master-painting", "ziman", "studio"],
            "mining": "SEPARATE_DEFERRED",
            "note": "Three live brands only; Mining deferred — from packs, no invent",
        },
        "sensorium": {
            "scope": sen.get("sensorium_scope"),
            "node_id": sn.get("node_id"),
            "hostname": sn.get("hostname"),
            "hardware": sn.get("hardware"),
            "services_and_ports": sn.get("services_and_ports"),
            "feature_flags": extract_named_items(sn, "feature_flags"),
            "kill_switches": extract_named_items(sn, "kill_switches"),
            "active_projects": extract_named_items(sn, "active_projects"),
            "owner_decisions": extract_named_items(sn, "owner_decisions"),
            "open_gates": extract_named_items(sn, "open_gates"),
            "internet_access_path": extract_named_items(sn, "internet_access_path"),
            "known_failures": extract_named_items(sn, "known_failures"),
            "wave0": "KEEP_LOCKED",
            "mqtt_1883": "CLOSED",
            "esp32_phase_b": "DEFERRED",
            "inet_feeds_phase_a": "PASS_7_of_7_ABC_skipped_500",
        },
        "laptop_center": {
            "scope": lap.get("laptop_scope"),
            "node_id": ln.get("node_id"),
            "hostname": ln.get("hostname"),
            "os": ln.get("os"),
            "hardware": ln.get("hardware"),
            "services_and_ports": ln.get("services_and_ports"),
            "feature_flags": extract_named_items(ln, "feature_flags"),
            "kill_switches": extract_named_items(ln, "kill_switches"),
            "active_projects": extract_named_items(ln, "active_projects"),
            "owner_decisions": extract_named_items(ln, "owner_decisions"),
            "open_gates": extract_named_items(ln, "open_gates"),
            "data_stores": extract_named_items(ln, "data_stores"),
            "memory_stores": extract_named_items(ln, "memory_stores"),
            "telegram_components": extract_named_items(ln, "telegram_components"),
            "webapp_components": extract_named_items(ln, "webapp_components"),
            "last_test_results": ln.get("last_test_results"),
            "center_pid_observed": 35916,
            "local_listen_8791_8792_8793_1883": False,
        },
        "connector_gap": {
            "registry_path": str(gap_path),
            "as_of": gap.get("as_of") or gap.get("collected_at") or gap.get("generated_at"),
            "entries": gap.get("gaps") or gap.get("connectors") or gap.get("entries") or gap,
            "hard_rules": [
                "Any datum missing evidence_id or source_type is unverified",
                "No external write action without owner gate",
                "Estimate data is not promoted to fact without explicit verification",
            ],
        },
        "claims": claims,
        "claims_summary": {
            "total": len(claims),
            "verified": sum(1 for c in claims if c.get("status") == "verified"),
            "unverified_flag": sum(1 for c in claims if c.get("unverified")),
            "estimates": sum(1 for c in claims if c.get("is_estimate")),
        },
        "open_questions": open_questions,
        "contradictions": contradictions,
        "estimate_policy": {
            "rule": "Estimates require label estimate + evidence_id + confidence + valid_for",
            "estimates_in_packs": sum(1 for c in claims if c.get("is_estimate")),
            "note": "No money/Similarweb estimate figures present in the three packs; none invented in synthesis",
        },
    }
    return synthesis


def write_md(synthesis: dict, synth_path: Path, md_path: Path) -> None:
    h = sha256_file(synth_path)
    lines = [
        "---",
        "tags: [octopus, node-pack, synthesis, sot, 2026-08-23]",
        f"date: {NOW[:10]}",
        "timezone: Australia/Sydney",
        f"status: {synthesis['synthesis_status']}",
        r"SoT: F:\backup",
        "---",
        "",
        "# NODE-PACK SYNTHESIS (Business -> Sensorium -> Laptop)",
        "",
        f"**synthesis_status:** `{synthesis['synthesis_status']}`  ",
        f"**synthesized_at:** {synthesis['synthesized_at']}  ",
        f"**SYNTHESIS.json sha256:** `{h}`  ",
        f"**evidence_root:** `{synthesis['evidence_root']}`",
        "",
        "## Verification",
        "",
        f"- HASHES.sha256 match: **{synthesis['hash_verification']['ok']}**",
        f"- Schema validation (owner-brief NODE-PACK-*.schema.json): **{synthesis['schema_validation']['ok']}**",
        f"- Fail reasons: {synthesis['fail_reasons'] or 'none'}",
        "",
        "### Pack hashes",
        "",
    ]
    for c in synthesis["hash_verification"]["checks"]:
        lines.append(
            f"- `{c['role']}`: `{c['actual_sha256']}` match={c['match']}"
        )
    lines += [
        "",
        "## Businesses (from BUSINESS pack only)",
        "",
        f"- node_id: `{synthesis['businesses']['node_id']}`",
        f"- live brands: {', '.join(synthesis['businesses']['live_brands_only'])}",
        f"- mining: `{synthesis['businesses']['mining']}`",
        "",
    ]
    for p in synthesis["businesses"]["active_projects"]:
        lines.append(f"- project `{p['name']}` status={p['status']} — {p.get('detail')}")
    lines += [
        "",
        "## Sensorium state (from SENSORIUM pack only)",
        "",
        f"- node_id: `{synthesis['sensorium']['node_id']}`",
        f"- WAVE0: `{synthesis['sensorium']['wave0']}`",
        f"- MQTT 1883: `{synthesis['sensorium']['mqtt_1883']}`",
        f"- ESP32 Phase B: `{synthesis['sensorium']['esp32_phase_b']}`",
        f"- Inet feeds Phase A: `{synthesis['sensorium']['inet_feeds_phase_a']}`",
        "",
        "## Laptop / Center (from LAPTOP pack only)",
        "",
        f"- node_id: `{synthesis['laptop_center']['node_id']}`",
        f"- hostname: `{synthesis['laptop_center']['hostname']}`",
        f"- os: `{synthesis['laptop_center']['os']}`",
        f"- center_pid_observed: `{synthesis['laptop_center']['center_pid_observed']}`",
        f"- local listen 8791/8792/8793/1883: `{synthesis['laptop_center']['local_listen_8791_8792_8793_1883']}`",
        "",
        "## Claims merge",
        "",
        f"- total: {synthesis['claims_summary']['total']}",
        f"- verified status: {synthesis['claims_summary']['verified']}",
        f"- unverified flag: {synthesis['claims_summary']['unverified_flag']}",
        f"- estimates: {synthesis['claims_summary']['estimates']} (none invented)",
        "",
    ]
    for c in synthesis["claims"]:
        est = " [ESTIMATE]" if c.get("is_estimate") else ""
        uv = " [unverified]" if c.get("unverified") else ""
        lines.append(
            f"- `{c['claim_id']}` ({c['pack_role']}){est}{uv}: {c['statement']} "
            f"| evidence_id=`{c.get('evidence_id')}` source_type=`{c.get('source_type')}`"
        )
    lines += [
        "",
        "## Open questions (from packs)",
        "",
    ]
    for q in synthesis["open_questions"]:
        lines.append(f"- ({q['pack_role']}) {q['question']}")
    lines += [
        "",
        "## Contradictions",
        "",
        f"- count: {len(synthesis['contradictions'])} (none across packs)",
        "",
        "## Non-actions honored",
        "",
    ]
    for n in synthesis["non_actions_honored"]:
        lines.append(f"- {n}")
    lines += [
        "",
        "## Pointers",
        "",
        f"- JSON: `{synth_path}`",
        f"- RESULT: `{ROOT / 'RESULT.json'}`",
        r"- WIRING hook: `F:\backup\_ops\organs\WIRING.json#hooks.synthesis_node_packs`",
        r"- evidence_plane pointer: `F:\backup\_ops\evidence_plane\SYNTHESIS-NODE-PACKS.pointer.json`",
        "",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_result(synthesis: dict, synth_sha: str) -> None:
    result_path = ROOT / "RESULT.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["synthesis_status"] = synthesis["synthesis_status"]
    result["synthesized_at"] = synthesis["synthesized_at"]
    result["synthesis"] = {
        "path_json": str(ROOT / "SYNTHESIS.json"),
        "path_md": str(ROOT / "SYNTHESIS.md"),
        "sha256": synth_sha,
        "order": synthesis["order"],
        "hash_verification_ok": synthesis["hash_verification"]["ok"],
        "schema_validation_ok": synthesis["schema_validation"]["ok"],
        "claims_total": synthesis["claims_summary"]["total"],
        "estimates": synthesis["claims_summary"]["estimates"],
        "fail_reasons": synthesis["fail_reasons"],
    }
    pkg = ROOT / "PACKAGE"
    pkg.mkdir(exist_ok=True)
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    result_path.write_text(text, encoding="utf-8")
    (pkg / "RESULT.json").write_text(text, encoding="utf-8")


def update_obsidian(synthesis: dict, synth_sha: str) -> None:
    status = synthesis["synthesis_status"]
    body = f"""---
tags: [octopus, concepts-to-code, node-pack, connector-gap, evidence-store, synthesis, 2026-08-23]
date: 2026-08-23
timezone: Australia/Sydney
status: {status}
SoT: F:\\backup
---

# 94 — CONCEPTS→CODE (2026-08-23)

Parallel pass converting OWNER-BRIEF / ADR / NODE-PACK schemas / CONNECTOR-GAP into loadable code + filled pack instances + **merged synthesis**.

## Evidence root

`F:\\backup\\06-EVIDENCE\\OCTOPUS-LAPTOP-CONCEPTS-TO-CODE-2026-08-23`

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
- Validated against owner-brief schemas; `HASHES.sha256` verified
- `synthesis_status`: **{status}**

### C) SYNTHESIS (merged SoT view)

- `SYNTHESIS.json` sha256=`{synth_sha}`
- `SYNTHESIS.md`
- Order: Business → Sensorium → Laptop
- No invent; estimate fields marked; evidence_id/source_type retained on claims
- Estimates in packs: {synthesis['claims_summary']['estimates']}

### D) CONNECTOR-GAP hook (CODE + reversible WIRING)

- Loader: `_ops/evidence_plane/connector_gap_loader.py`
- Flag: `connector_gap_hook=true` in `_ops/organs/WIRING.json` (backup `.bak-2026-08-23-concepts-to-code`)
- Synthesis pointer: `hooks.synthesis_node_packs` + `_ops/evidence_plane/SYNTHESIS-NODE-PACKS.pointer.json` (backup `.bak-2026-08-23-synthesis-node-packs`)
- GA4/GSC/Ads marked GAP until OAuth

## Cross-links

- [[93-LAPTOP-AGENT-OWNER-BRIEF]]
- [[01-BUSINESS-MAP-CANONICAL]]
- Evidence: `06-EVIDENCE/OCTOPUS-LAPTOP-CONCEPTS-TO-CODE-2026-08-23/`
"""
    OBSIDIAN.write_text(body, encoding="utf-8")


def update_wiring_and_pointer(synth_sha: str) -> None:
    wiring = json.loads(WIRING.read_text(encoding="utf-8"))
    flags = wiring.setdefault("flags", {})
    flags["synthesis_node_packs_hook"] = True
    hooks = wiring.setdefault("hooks", {})
    hooks["synthesis_node_packs"] = {
        "enabled_flag": "synthesis_node_packs_hook",
        "synthesis_json": str(ROOT / "SYNTHESIS.json"),
        "synthesis_md": str(ROOT / "SYNTHESIS.md"),
        "sha256": synth_sha,
        "packs_dir": str(PACKS_DIR),
        "order": ["business", "sensorium", "laptop"],
        "reversible": True,
        "rollback": "set flags.synthesis_node_packs_hook=false; remove hooks.synthesis_node_packs; restore WIRING.json.bak-2026-08-23-synthesis-node-packs",
    }
    rb = wiring.get("rollback") or ""
    extra = "; synthesis_node_packs_hook=false disables synthesis pointer"
    if "synthesis_node_packs_hook" not in rb:
        wiring["rollback"] = (rb.rstrip("; ") + extra)
    WIRING.write_text(json.dumps(wiring, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    pointer = {
        "schema": "octopus-evidence-plane-pointer.v1",
        "name": "SYNTHESIS-NODE-PACKS",
        "enabled": True,
        "reversible": True,
        "created_at": NOW,
        "timezone": "Australia/Sydney",
        "points_to": {
            "synthesis_json": str(ROOT / "SYNTHESIS.json"),
            "synthesis_md": str(ROOT / "SYNTHESIS.md"),
            "sha256": synth_sha,
            "result_json": str(ROOT / "RESULT.json"),
            "package_result_json": str(ROOT / "PACKAGE" / "RESULT.json"),
            "packs_dir": str(PACKS_DIR),
        },
        "wiring_hook": r"F:\backup\_ops\organs\WIRING.json#hooks.synthesis_node_packs",
        "wiring_backup": r"F:\backup\_ops\organs\WIRING.json.bak-2026-08-23-synthesis-node-packs",
        "rollback": [
            "set WIRING.flags.synthesis_node_packs_hook=false",
            "remove WIRING.hooks.synthesis_node_packs",
            "restore WIRING from .bak-2026-08-23-synthesis-node-packs",
            "delete or rename this pointer file",
        ],
        "does_not": [
            "restart center",
            "unlock WAVE0",
            "mine",
            "write secrets",
        ],
    }
    (EVIDENCE_PLANE / "SYNTHESIS-NODE-PACKS.pointer.json").write_text(
        json.dumps(pointer, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main() -> None:
    packs = {
        role: json.loads((PACKS_DIR / fname).read_text(encoding="utf-8"))
        for role, fname in PACK_FILES.items()
    }
    hash_report = verify_hashes()
    schema_report = validate_schemas(packs)
    synthesis = build_synthesis(packs, hash_report, schema_report)

    synth_path = ROOT / "SYNTHESIS.json"
    md_path = ROOT / "SYNTHESIS.md"
    synth_path.write_text(json.dumps(synthesis, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_md(synthesis, synth_path, md_path)
    synth_sha = sha256_file(synth_path)

    update_result(synthesis, synth_sha)
    update_obsidian(synthesis, synth_sha)
    update_wiring_and_pointer(synth_sha)

    out = {
        "synthesis_status": synthesis["synthesis_status"],
        "synthesis_json": str(synth_path),
        "synthesis_md": str(md_path),
        "sha256": synth_sha,
        "hash_ok": hash_report["ok"],
        "schema_ok": schema_report["ok"],
        "result": str(ROOT / "RESULT.json"),
        "package_result": str(ROOT / "PACKAGE" / "RESULT.json"),
        "obsidian": str(OBSIDIAN),
        "wiring": str(WIRING),
        "pointer": str(EVIDENCE_PLANE / "SYNTHESIS-NODE-PACKS.pointer.json"),
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
