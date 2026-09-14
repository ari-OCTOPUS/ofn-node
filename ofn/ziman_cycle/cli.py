"""CLI for ofn.ziman_cycle: validate-fields, dry-run-cycle4, verify-artifact."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

from .atomic_io import read_json
from .runner import run_dry_run_cycle4
from .sales_fields import FieldRecord, apply_validation, validate_field
from .verify import VerifyError, verify_artifact


def _cmd_validate_fields(args: argparse.Namespace) -> int:
    raw = read_json(args.input) if args.input else json.loads(args.json or "{}")
    if isinstance(raw, list):
        rows = raw
    elif isinstance(raw, dict) and "sell_fields_table" in raw:
        rows = raw["sell_fields_table"]
    elif isinstance(raw, dict) and "fields" in raw:
        rows = [{"field_name": k, **v} for k, v in raw["fields"].items()]
    else:
        rows = [raw]
    results = []
    ok = True
    for row in rows:
        rec = FieldRecord.from_dict(row if "field_name" in row or "field" in row else row)
        if "field" in row and not rec.field_name:
            rec.field_name = row["field"]
        apply_validation(rec)
        results.append(rec.to_dict())
        if rec.validation_errors:
            ok = False
    print(json.dumps({"ok": ok, "fields": results}, indent=2, ensure_ascii=False))
    return 0 if ok else 2


def _cmd_dry_run_cycle4(args: argparse.Namespace) -> int:
    result = run_dry_run_cycle4(
        prior_path=args.prior,
        catalog_path=args.catalog,
        out_dir=args.out_dir,
        expected_prior_sha=args.expected_prior_sha,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _cmd_verify_artifact(args: argparse.Namespace) -> int:
    try:
        result = verify_artifact(
            args.artifact,
            expected_previous_sha=args.previous_sha,
            receipt_path=args.receipt,
            expected_cycle=args.cycle,
        )
    except VerifyError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m ofn.ziman_cycle")
    sub = p.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate-fields", help="Validate sales field records")
    v.add_argument("--input", help="Path to JSON file")
    v.add_argument("--json", help="Inline JSON string")
    v.set_defaults(func=_cmd_validate_fields)

    d = sub.add_parser("dry-run-cycle4", help="CYCLE-4 dry-run readiness")
    d.add_argument("--prior", required=True, help="Prior cycle artifact (C3b)")
    d.add_argument("--catalog", required=True, help="ziman-catalog.json path")
    d.add_argument("--out-dir", required=True, help="Output directory for CYCLE-4")
    d.add_argument("--expected-prior-sha", default=None)
    d.set_defaults(func=_cmd_dry_run_cycle4)

    z = sub.add_parser("verify-artifact", help="Verify outcome artifact / receipt")
    z.add_argument("--artifact", required=True)
    z.add_argument("--receipt", default=None)
    z.add_argument("--previous-sha", default=None)
    z.add_argument("--cycle", default="4")
    z.set_defaults(func=_cmd_verify_artifact)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
