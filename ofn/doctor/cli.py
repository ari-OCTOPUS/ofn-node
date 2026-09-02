#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI for the self-completing doctor (thin; logic lives in the modules).

    python -m ofn.doctor.cli contract-map
    python -m ofn.doctor.cli round --vault <root> --out <dir>
    python -m ofn.doctor.cli backlog --state <self-backlog.json>
    python -m ofn.doctor.cli destiny --journal <journal.jsonl> \
        --proposals <proposals.json> --out <outcomes.json> [--pr-url URL]

The round command writes ONLY inside --out (a lane artifact directory); it
never writes to the vault.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import (DestinyEngine, DoctorRound, Proposal, ReceiptLog, REQUIREMENTS,
               requirement_stats)
from .backlog import SelfBacklog
from .contract_map import extract_gaps, load_contract


def cmd_contract_map(_args) -> int:
    stats = requirement_stats()
    print(f"contract: LAB-DOCTOR-CONTRACT.yaml (bundled, source sha256 recorded)")
    for key in ("total", "IMPLEMENTED", "DELEGATED_LANE_C", "BACKLOG_ITEM"):
        print(f"  {key:<18} {stats.get(key, 0)}")
    print()
    for r in REQUIREMENTS:
        print(f"{r.req_id}  [{r.status}]\n    contract : {r.contract_path}"
              f"\n    symbol   : {r.code_symbol}\n    test     : {r.test_symbol}"
              f"\n    failure  : {r.failure_mode}\n    receipt  : {r.receipt}")
    return 0


def cmd_round(args) -> int:
    vault = Path(args.vault)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    receipt = ReceiptLog(out / "receipt.jsonl")
    receipt.write("round_start", vault_root=str(vault), mode="read-only-dry-run-only")
    try:
        result = DoctorRound().run(vault)
    except Exception as e:                                  # noqa: BLE001
        receipt.write("round_aborted", error=f"{type(e).__name__}: {e}")
        print(f"ROUND ABORTED: {e}", file=sys.stderr)
        return 2
    receipt.write_manifest("integrity_before", result.manifest_before)
    for f in result.findings:
        receipt.write("finding", finding_id=f.id, severity=f.severity,
                      category=f.category, evidence_path=f.evidence_path,
                      evidence_sha256=f.evidence_sha256)
    receipt.write_manifest("integrity_after", result.manifest_after)
    receipt.write("round_end", **result.stats)
    (out / "findings.json").write_text(
        json.dumps(result.to_machine_json(), ensure_ascii=False, indent=2),
        encoding="utf-8")
    ok = result.stats["read_only_proven"] and receipt.verify()["valid"]
    print(json.dumps(result.stats, ensure_ascii=False, indent=2))
    print(f"receipt: {out / 'receipt.jsonl'} (verify={receipt.verify()})")
    print(f"read_only_proven={result.stats['read_only_proven']}")
    return 0 if ok else 1


def cmd_backlog(args) -> int:
    backlog = SelfBacklog(args.state)
    gaps = extract_gaps(load_contract())
    counts = backlog.upsert_from_gaps(gaps)
    print(json.dumps({**counts, "total_items": len(backlog.items()),
                      "open": len(backlog.open_items())}, ensure_ascii=False))
    return 0


def cmd_destiny(args) -> int:
    proposals = [Proposal(**p) for p in json.loads(Path(args.proposals).read_text(encoding="utf-8"))]
    engine = DestinyEngine(args.journal)
    pr_url = args.pr_url or ""

    def executor(prop: Proposal) -> str:
        if not pr_url:
            raise RuntimeError("PR URL missing — refusing to claim PR_CREATED without a real PR")
        return pr_url

    outcomes = {}
    for p in proposals:
        d = engine.assign(p, executor=executor if pr_url else None)
        outcomes[p.id] = {"outcome": d.outcome, "reason": d.reason,
                          "rule_trace": d.rule_trace}
    orphans = engine.orphan_count()
    Path(args.out).write_text(
        json.dumps({"outcomes": outcomes, "orphans": orphans,
                    "all_destined": orphans == 0}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(json.dumps({"outcomes": {k: v["outcome"] for k, v in outcomes.items()},
                      "orphans": orphans}, ensure_ascii=False, indent=2))
    return 0 if orphans == 0 else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ofn.doctor")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("contract-map").set_defaults(func=cmd_contract_map)

    p_round = sub.add_parser("round")
    p_round.add_argument("--vault", required=True)
    p_round.add_argument("--out", required=True)
    p_round.set_defaults(func=cmd_round)

    p_backlog = sub.add_parser("backlog")
    p_backlog.add_argument("--state", required=True)
    p_backlog.set_defaults(func=cmd_backlog)

    p_dest = sub.add_parser("destiny")
    p_dest.add_argument("--journal", required=True)
    p_dest.add_argument("--proposals", required=True)
    p_dest.add_argument("--out", required=True)
    p_dest.add_argument("--pr-url", default="")
    p_dest.set_defaults(func=cmd_destiny)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
