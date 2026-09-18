#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only doctor path/schema inventory. Lane D-S0-HUNT.

Prints present / absent / schema class for known vault and ofn-node paths.
Does not import ofn.doctor, does not run a doctor round, does not touch
the network, and does not set flags.

Every path below is a real filesystem location this probe will Test-Path.
Absence here is this_host_only, not system-wide missing.
"""
from __future__ import annotations

import argparse
import json
import socket
from pathlib import Path

VAULT = Path(r"F:\backup")
OFN = Path(r"F:\ofn-node")

SCHEMA_DOCTOR_REPORT = "octopus.doctor-report.v1"
SCHEMA_FINDINGS_KEYS = frozenset(
    {"vault_root", "findings", "stats", "changed_sources", "read_only_proven"}
)

OFN_DOCTOR_PY = (
    "__init__.py",
    "cli.py",
    "round.py",
    "backlog.py",
    "destiny.py",
    "contract_map.py",
    "prescription.py",
    "receipts.py",
    "miniyaml.py",
)

DOCTOR_LANE_TESTS = (
    "test_doctor_lane_backlog.py",
    "test_doctor_lane_cli.py",
    "test_doctor_lane_contract_map.py",
    "test_doctor_lane_destiny.py",
    "test_doctor_lane_round.py",
)

FIXED_JSON = (
    VAULT / "state" / "doctor" / "report.json",
    OFN / "data" / "state" / "doctor" / "report.json",
    VAULT / "06-EVIDENCE" / "OCTOPUS-DOCTOR-REFRESH-2026-08-23" / "doctor-report.json",
    VAULT / "OCTOPUS-DOCTOR" / "90-_meta" / "state" / "doctor-vitals.json",
)


def _sniff_json(path: Path) -> dict:
    """Load a small JSON object, or the first jsonl object. Never rewrite the file."""
    raw = path.read_bytes()[: 1 << 16]
    text = raw.decode("utf-8", errors="replace").lstrip()
    if not text:
        return {"_empty": True}
    first = text.splitlines()[0] if path.suffix == ".jsonl" or text[:1] != "{" else text
    try:
        obj = json.loads(first if path.suffix == ".jsonl" else text)
    except json.JSONDecodeError:
        return {"_not_json": True}
    return obj if isinstance(obj, dict) else {"_json_type": type(obj).__name__}


def classify(path: Path) -> tuple[str, str]:
    """Return (presence_or_schema, detail)."""
    if not path.exists():
        return "ABSENT", ""
    if not path.is_file():
        return "PRESENT_NOT_FILE", "dir" if path.is_dir() else path.stat().st_mode
    suffix = path.suffix.lower()
    if suffix in {".db", ".db-shm", ".db-wal"}:
        return "PRESENT_SQLITE_OR_WAL", f"bytes={path.stat().st_size}"
    if suffix not in {".json", ".jsonl"}:
        return "PRESENT_NOT_JSON", f"bytes={path.stat().st_size}"
    try:
        obj = _sniff_json(path)
    except OSError as exc:
        return "UNREADABLE", type(exc).__name__
    if obj.get("_empty"):
        return "PRESENT_EMPTY", f"bytes={path.stat().st_size}"
    if obj.get("_not_json") or obj.get("_json_type"):
        return "PRESENT_NOT_OBJECT", f"bytes={path.stat().st_size}"
    named = obj.get("schema")
    if named == SCHEMA_DOCTOR_REPORT:
        status = obj.get("status", "unverified")
        repairs = obj.get("repairs_attempted", "unverified")
        host_hint = "other_host" if "/var/lib/octopus" in json.dumps(obj, ensure_ascii=False) else "host_unverified"
        return "DOCTOR_REPORT_V1", f"status={status} repairs_attempted={repairs} {host_hint}"
    if SCHEMA_FINDINGS_KEYS <= set(obj):
        return "OFN_DOCTOR_FINDINGS", f"read_only_proven={obj.get('read_only_proven')}"
    if isinstance(named, str) and named:
        return "OTHER_NAMED_SCHEMA", named
    keys = ",".join(list(obj)[:6])
    return "OTHER_JSON", f"keys={keys}"


def row(kind: str, path: Path, verdict: str, detail: str) -> str:
    exists = path.exists()
    return f"{kind}\t{verdict}\t{exists}\t{path}\t{detail}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Read-only doctor schema probe (D-S0-HUNT)")
    ap.parse_args(argv)

    host = socket.gethostname()
    print(f"probe=doctor_schema_probe")
    print(f"lane=D-S0-HUNT")
    print(f"host={host}")
    print(f"scope=this_host_only")
    print(f"network=none")
    print(f"cwd={Path.cwd()}")
    print("kind\tverdict\texists\tpath\tdetail")

    for path in FIXED_JSON:
        verdict, detail = classify(path)
        print(row("fixed", path, verdict, detail))

    ops = VAULT / "_ops" / "state" / "doctor"
    if ops.is_dir():
        for path in sorted(ops.iterdir()):
            if path.is_file() and not path.name.endswith("-shm"):
                verdict, detail = classify(path)
                print(row("ops_state_doctor", path, verdict, detail))
    else:
        print(row("ops_state_doctor", ops, "ABSENT", "dir"))

    doctor_pkg = OFN / "ofn" / "doctor"
    for name in OFN_DOCTOR_PY:
        path = doctor_pkg / name
        verdict = "PRESENT" if path.is_file() else "ABSENT"
        detail = f"bytes={path.stat().st_size}" if path.is_file() else ""
        print(row("ofn_doctor_module", path, verdict, detail))
    contract = doctor_pkg / "contract" / "LAB-DOCTOR-CONTRACT.yaml"
    print(row("ofn_doctor_contract", contract, "PRESENT" if contract.is_file() else "ABSENT",
              f"bytes={contract.stat().st_size}" if contract.is_file() else ""))

    tests = OFN / "tests"
    for name in DOCTOR_LANE_TESTS:
        path = tests / name
        verdict = "PRESENT" if path.is_file() else "ABSENT"
        detail = f"bytes={path.stat().st_size}" if path.is_file() else ""
        print(row("doctor_lane_test", path, verdict, detail))
    repair = tests / "test_repair_api.py"
    print(row("repair_api_test", repair, "ABSENT" if not repair.exists() else "PRESENT_UNEXPECTED", ""))

    # Summary: canonical report on this vault
    canonical = VAULT / "state" / "doctor" / "report.json"
    print(f"canonical_report={classify(canonical)[0]}")
    print(f"repair_api_test={('ABSENT' if not repair.exists() else 'PRESENT')}")
    print("note=ABSENT on this laptop is body_not_on_this_host, not system-wide missing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
