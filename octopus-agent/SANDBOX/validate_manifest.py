#!/usr/bin/env python3
"""Deterministic experiment-manifest validator (P3). Dependency-free by design:
no network, no third-party libraries, no clock-dependent logic. Any violated rule
from manifest-schema.json hard_rejections (R01..R20) causes exit code 1 with the
rule ids printed. Acceptance is all-or-nothing.

Usage: validate_manifest.py <manifest.json>
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

AGENT_ROOT = Path("/opt/octopus-agent")
CODE_ROOT = Path("/opt/octopus")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
EXP_ID = re.compile(r"^exp-[0-9a-z][0-9a-z-]*$")
UTC_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
CRIT_FLAGS = ("index_content_equal", "event_count_equal", "event_order_equal", "schema_equal", "errors_zero")
LIMIT_FLOORS = {"cpu_s": 1, "as_mb": 64, "fsize_mb": 16, "wall_s": 1}


def _rejects() -> list[str]:
    return []


def validate(path: str) -> tuple[bool, list[str]]:
    errors: list[str] = []
    p = Path(path)
    try:
        manifest = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False, ["R20 file not parseable as JSON"]
    if not isinstance(manifest, dict):
        return False, ["R20 file not parseable as JSON"]

    # R01-R04 identity block
    if not isinstance(manifest.get("experiment_id"), str) or not EXP_ID.match(manifest.get("experiment_id", "")):
        errors.append("R01 experiment_id missing or malformed")
    if not isinstance(manifest.get("created_at"), str) or not UTC_Z.match(manifest.get("created_at", "")):
        errors.append("R02 created_at missing or not UTC-Z ISO-8601")
    if not str(manifest.get("authorization_ref") or "").strip():
        errors.append("R03 authorization_ref missing/empty")
    if not str(manifest.get("hypothesis") or "").strip():
        errors.append("R04 hypothesis missing/empty")

    # R05-R08 fixture block
    fixture = manifest.get("fixture") or {}
    f_file = str(fixture.get("file") or "")
    if not f_file.startswith(("FIXTURES/", "/opt/octopus-agent/FIXTURES/")) or not (AGENT_ROOT / f_file).is_file():
        errors.append("R05 fixture.file missing or not under agent FIXTURES")
    else:
        actual = hashlib.sha256((AGENT_ROOT / f_file).read_bytes()).hexdigest()
        sha = fixture.get("sha256")
        if not isinstance(sha, str) or not HEX64.match(sha):
            errors.append("R06 fixture.sha256 missing or not 64-hex")
        elif sha != actual:
            errors.append("R06 fixture.sha256 != actual file hash")
        sidecar = (AGENT_ROOT / f_file).parent / ((AGENT_ROOT / f_file).name.rsplit(".", 1)[0] + ".manifest.json")
        if not sidecar.is_file():
            errors.append("R08 fixture manifest sidecar missing")
    if not isinstance(fixture.get("records"), int) or fixture.get("records", 0) < 1:
        errors.append("R07 fixture.records missing or < 1")

    # R09-R10 code block
    code = manifest.get("code_under_test") or {}
    src = str(code.get("source_path") or "")
    if not src.startswith("/opt/octopus/") or not Path(src).is_file():
        errors.append("R09 code_under_test.source_path outside /opt/octopus or missing")
    else:
        actual = hashlib.sha256(Path(src).read_bytes()).hexdigest()
        sha = code.get("sha256")
        if not isinstance(sha, str) or not HEX64.match(sha) or sha != actual:
            errors.append("R10 code_under_test.sha256 mismatch vs live file")

    # R11 modes block
    modes = manifest.get("modes") or {}
    for side in ("baseline", "candidate"):
        block = modes.get(side) or {}
        env = block.get("env") or {}
        if not isinstance(env.get("OCTOPUS_INDEX_FLUSH_EVERY"), int) or env.get("OCTOPUS_INDEX_FLUSH_EVERY", 0) < 1:
            errors.append(f"R11 modes.{side} missing/incomplete (OCTOPUS_INDEX_FLUSH_EVERY)")

    # R12-R14 frozen criteria
    crit = manifest.get("frozen_criteria") or {}
    for flag in CRIT_FLAGS:
        if flag not in crit:
            errors.append(f"R12 frozen criteria incomplete: {flag}")
        elif crit[flag] is not True:
            errors.append(f"R13 frozen criteria flag not true: {flag}")
    wr = crit.get("write_reduction_min_percent")
    if not isinstance(wr, (int, float)) or not (0 <= wr <= 100):
        errors.append("R14 write_reduction_min_percent missing or out of [0,100]")

    # R15 runs_required
    if not isinstance(manifest.get("runs_required"), int) or manifest.get("runs_required", 0) < 3:
        errors.append("R15 runs_required missing or < 3")

    # R16 limits
    limits = manifest.get("limits") or {}
    for key, floor in LIMIT_FLOORS.items():
        if not isinstance(limits.get(key), int) or limits.get(key, 0) < floor:
            errors.append(f"R16 limits.{key} missing or below floor {floor}")

    # R17 network
    if "network" in manifest and manifest.get("network") != "denied":
        errors.append("R17 network present and != 'denied'")

    # R18 rollback
    if not str(manifest.get("rollback") or "").strip():
        errors.append("R18 rollback missing/empty")

    # R19 may_authorize
    if "may_authorize" in manifest and manifest.get("may_authorize") is not False:
        errors.append("R19 may_authorize present and != false")

    return (not errors), errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_manifest.py <manifest.json>", file=sys.stderr)
        return 2
    ok, errors = validate(sys.argv[1])
    if ok:
        manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        print(f"ACCEPT {manifest.get('experiment_id')}")
        return 0
    for e in errors:
        print(f"REJECT {e}")
    print(f"REJECTED {len(errors)} rule(s) — no partial acceptance")
    return 1


if __name__ == "__main__":
    sys.exit(main())
