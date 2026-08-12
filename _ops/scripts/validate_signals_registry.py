#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate architecture/signals-registry.yaml — JSON Schema + semantic rules (Stage 2–3).

Emits a JSON report with registry digest, git SHA, errors, warnings, signal count, timestamp.
Does NOT register WORKLOCK suites.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "architecture" / "signals-registry.schema.json"
DATA = ROOT / "architecture" / "signals-registry.yaml"
OPS = ROOT / "_ops"
TESTS = OPS / "tests"
CAPABILITY_RECORD = OPS / "capabilities" / "neural-learned-apply.json"
DEFAULT_REPORT = OPS / "state" / "adr-033" / "reports" / "signals-registry-validate.json"

LADDER = [
    "SPEC_NOT_BUILT",
    "STRUCTURAL",
    "TESTED",
    "SHADOW",
    "ARMED",
    "LOCKED",
    "RETIRED",
]
LADDER_IDX = {name: i for i, name in enumerate(LADDER)}
BUILT_STATUSES = {"TESTED", "SHADOW", "ARMED", "LOCKED"}
NON_NONE_EFFECTS = {"trace_only", "bounded_ranking_bias", "gate_internal"}


def _git_sha() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(ROOT),
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip() or None
    except Exception:
        return None


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _resolve_impl(path: str | None) -> Path | None:
    if not path:
        return None
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / path
    return p


def _resolve_test(name: str) -> Path:
    # accept bare filename or relative under _ops/tests
    if name.endswith(".py") and "/" not in name and "\\" not in name:
        return TESTS / name
    p = Path(name)
    if not p.is_absolute():
        p = ROOT / name
    return p


def _resolve_trace(path: str) -> Path:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / path
    return p


def validate_registry(
    data: dict[str, Any] | None = None,
    *,
    raw_yaml: bytes | None = None,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Return validation report dict. ok=True iff errors empty."""
    try:
        import yaml
        import jsonschema
    except ImportError as exc:
        return {
            "ok": False,
            "errors": [f"missing_dependency:{exc}"],
            "warnings": [],
            "signal_count": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    schema_path = root / "architecture" / "signals-registry.schema.json"
    data_path = root / "architecture" / "signals-registry.yaml"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if raw_yaml is None:
        raw_yaml = data_path.read_bytes()
    if data is None:
        data = yaml.safe_load(raw_yaml.decode("utf-8"))

    errors: list[str] = []
    warnings: list[str] = []
    signals = list(data.get("signals") or [])

    # 1) JSON Schema
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        errors.append(f"json_schema:{e.message}|path={list(e.path)}")

    # 2) duplicate IDs
    seen: set[str] = set()
    for s in signals:
        sid = s.get("id")
        if sid in seen:
            errors.append(f"duplicate_id:{sid}")
        seen.add(sid)

    ops = root / "_ops"
    tests_dir = ops / "tests"
    cap_path = ops / "capabilities" / "neural-learned-apply.json"

    for s in signals:
        sid = s.get("id", "?")
        role = s.get("role")
        truth = s.get("truth_status")
        evid = s.get("evidence_level")
        auth = s.get("authority") or {}
        eq = s.get("equation") or {}
        sg = s.get("safeguards") or {}
        ev = s.get("evidence") or {}
        impl = eq.get("implementation_path")
        effect = auth.get("allowed_effect", "none")

        # ladder: claimed truth must not exceed evidence_level
        if truth in LADDER_IDX and evid in LADDER_IDX:
            if LADDER_IDX[truth] > LADDER_IDX[evid]:
                errors.append(
                    f"{sid}:truth_status_exceeds_evidence_level:{truth}>{evid}"
                )

        # diagnostic/detector => may_gate false (also in schema; re-check)
        if role in ("diagnostic", "detector") and auth.get("may_gate") is True:
            errors.append(f"{sid}:diagnostic_or_detector_may_gate")

        # every signal: ledger/tool false
        if auth.get("may_mutate_ledger") is not False:
            errors.append(f"{sid}:may_mutate_ledger_must_be_false")
        if auth.get("may_trigger_tool") is not False:
            errors.append(f"{sid}:may_trigger_tool_must_be_false")

        # SPEC_NOT_BUILT => null path
        if truth == "SPEC_NOT_BUILT" or evid == "SPEC_NOT_BUILT":
            if impl is not None:
                errors.append(f"{sid}:SPEC_NOT_BUILT_requires_null_implementation_path")

        # built statuses require existing implementation path
        if truth in BUILT_STATUSES or evid in BUILT_STATUSES:
            if not impl:
                errors.append(f"{sid}:built_status_requires_implementation_path")
            else:
                p = _resolve_impl(impl)
                if p is None or not p.exists():
                    errors.append(f"{sid}:missing_implementation_path:{impl}")

        # non-none effect => SHADOW+ and rollback_flag
        if effect in NON_NONE_EFFECTS:
            if evid not in ("SHADOW", "ARMED", "LOCKED"):
                errors.append(f"{sid}:non_none_effect_requires_SHADOW_or_higher")
            rb = sg.get("rollback_flag")
            if not rb:
                errors.append(f"{sid}:non_none_effect_requires_rollback_flag")

        # ARMED/LOCKED => test + shadow_window_days>=7
        if evid in ("ARMED", "LOCKED") or truth in ("ARMED", "LOCKED"):
            tests = ev.get("tests") or []
            if not tests:
                errors.append(f"{sid}:ARMED_LOCKED_requires_tests")
            sw = ev.get("shadow_window_days")
            if not isinstance(sw, int) or sw < 7:
                errors.append(f"{sid}:ARMED_LOCKED_requires_shadow_window_days>=7")

        # existing test / trace paths
        for tname in ev.get("tests") or []:
            tp = tests_dir / tname if "/" not in tname and "\\" not in tname else (
                root / tname if not Path(tname).is_absolute() else Path(tname)
            )
            if not tp.exists():
                errors.append(f"{sid}:missing_test_path:{tname}")

        for tr in ev.get("traces") or []:
            # traces may be files that appear after first run — require parent dir OR file
            tp = root / tr if not Path(tr).is_absolute() else Path(tr)
            if not tp.exists() and not tp.parent.exists():
                errors.append(f"{sid}:missing_trace_path:{tr}")
            elif not tp.exists():
                warnings.append(f"{sid}:trace_file_absent_parent_ok:{tr}")

        # neural-learned-apply hard pin (ADR-035 ACCEPTED — owner «هردو» 2026-08-12).
        # APPLY=1 زنده (runtime + flags.cmd + owner-verdicts.yaml fallback).
        # may_gate=true, gate_internal, ARMED, production_apply_enabled=true.
        # مرز سخت: payment/email/CRM/external = همیشه may_mutate_ledger/tool=false.
        if sid == "neural-learned-apply":
            if truth != "TESTED":
                errors.append("neural-learned-apply:truth_status_must_be_TESTED")
            if evid != "ARMED":
                errors.append("neural-learned-apply:evidence_level_must_be_ARMED")
            if effect != "gate_internal":
                errors.append("neural-learned-apply:allowed_effect_must_be_gate_internal")
            if auth.get("may_gate") is not True:
                errors.append("neural-learned-apply:may_gate_must_be_true")
            if sg.get("production_apply_enabled") is not True:
                errors.append(
                    "neural-learned-apply:production_apply_enabled_must_be_true"
                )
            if auth.get("may_mutate_ledger") is not False:
                errors.append("neural-learned-apply:may_mutate_ledger_must_be_false")
            if auth.get("may_trigger_tool") is not False:
                errors.append("neural-learned-apply:may_trigger_tool_must_be_false")
            # capability record must agree
            if cap_path.exists():
                try:
                    cap = json.loads(cap_path.read_text(encoding="utf-8"))
                    if cap.get("evidence_level") != "ARMED":
                        errors.append(
                            "neural-learned-apply:capability_record_evidence_mismatch"
                        )
                    if (cap.get("runtime") or {}).get("production_apply_enabled") is not True:
                        errors.append(
                            "neural-learned-apply:capability_record_apply_disabled"
                        )
                    if (cap.get("authority") or {}).get("may_gate") is not True:
                        errors.append(
                            "neural-learned-apply:capability_record_may_gate"
                        )
                    if (cap.get("authority") or {}).get("allowed_effect") != "gate_internal":
                        errors.append(
                            "neural-learned-apply:capability_record_effect"
                        )
                except Exception as exc:
                    errors.append(f"neural-learned-apply:capability_record_unreadable:{exc}")
            else:
                errors.append("neural-learned-apply:capability_record_missing")

    report = {
        "ok": not errors,
        "registry_id": data.get("registry_id"),
        "registry_digest_sha256": _digest(raw_yaml),
        "git_sha": _git_sha(),
        "signal_count": len(signals),
        "errors": errors,
        "warnings": warnings,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "schema": str(schema_path.relative_to(root)).replace("\\", "/"),
        "data": str(data_path.relative_to(root)).replace("\\", "/"),
    }
    return report


def main(argv: list[str] | None = None) -> int:
    argv = list(argv or sys.argv[1:])
    root = ROOT
    schema_path = SCHEMA
    data_path = DATA
    out = DEFAULT_REPORT

    def _take(flag: str) -> Path | None:
        if flag not in argv:
            return None
        i = argv.index(flag)
        if i + 1 >= len(argv):
            raise SystemExit(f"missing value for {flag}")
        return Path(argv[i + 1])

    reg = _take("--registry")
    sch = _take("--schema")
    rep = _take("--report") or _take("--out")
    if reg is not None:
        data_path = reg if reg.is_absolute() else (ROOT / reg)
    if sch is not None:
        schema_path = sch if sch.is_absolute() else (ROOT / sch)
    if rep is not None:
        out = rep if rep.is_absolute() else (ROOT / rep)

    try:
        import yaml
    except ImportError:
        print("FAIL: need pyyaml")
        return 2

    raw = data_path.read_bytes()
    data = yaml.safe_load(raw.decode("utf-8"))
    # validate_registry uses ROOT-relative defaults; pass explicit via root + override paths
    report = validate_registry(data, raw_yaml=raw, root=root)
    # pin paths actually used
    report["schema"] = str(schema_path.relative_to(root)).replace("\\", "/") if schema_path.is_relative_to(root) else str(schema_path)
    report["data"] = str(data_path.relative_to(root)).replace("\\", "/") if data_path.is_relative_to(root) else str(data_path)

    # Explicit neural-learned-apply confirmation block for WORKLOCK preflight
    nla = next((s for s in (data.get("signals") or []) if s.get("id") == "neural-learned-apply"), None)
    report["neural_learned_apply"] = None
    if nla:
        report["neural_learned_apply"] = {
            "truth_status": nla.get("truth_status"),
            "evidence_level": nla.get("evidence_level"),
            "allowed_effect": (nla.get("authority") or {}).get("allowed_effect"),
            "may_gate": (nla.get("authority") or {}).get("may_gate"),
            "production_apply_enabled": (nla.get("safeguards") or {}).get(
                "production_apply_enabled"
            ),
        }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"ok": report["ok"], "errors": len(report["errors"]),
                      "warnings": len(report["warnings"]),
                      "signals": report["signal_count"],
                      "neural_learned_apply": report.get("neural_learned_apply"),
                      "report": str(out)}, ensure_ascii=False))
    if report["errors"]:
        for e in report["errors"]:
            print("ERROR:", e)
    for w in report["warnings"]:
        print("WARN:", w)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
