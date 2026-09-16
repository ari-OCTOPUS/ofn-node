#!/usr/bin/env python3
"""Re-derive the Octopus verification verdict from produced artifacts.

This script is a *different reader* than the suite runners: it imports no
patch-internal test helpers and executes no fixtures. It checks receipts,
summary, side-effect measurements, baseline, preregistry, and reality map,
then writes a verdict JSON into the kit directory.

Independence is never inferred: default is independent=false. A genuinely
separate verifier session attests independence explicitly:

    python verdict.py --identity "<session-id>" \
        --statement <file-with-INDEPENDENT_SESSION_ATTESTATION-line> \
        --head <evidence-head> --preflight <false>

The implementing session must always use --preflight, which records
independent=false regardless of other flags.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent
DEFAULT_HEAD = "d3013390d52aab2e61bd2578613aff7077f68742"
IMPLEMENTATION_HEAD = "fa38d16cca944a80396ae1e1a16c547ab3122f78"


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _read_lines(path: Path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--head", default=DEFAULT_HEAD)
    ap.add_argument("--preflight", action="store_true",
                    help="implementing-session mode: independence is always false")
    ap.add_argument("--identity", default=None)
    ap.add_argument("--statement", default=None,
                    help="path to independence statement (required for non-preflight)")
    ap.add_argument("--lab", default=str(KIT.parent / "OCTOPUS-SECURITY-LAB-2026-08-21"),
                    help="security lab artifact dir")
    args = ap.parse_args()

    lab = Path(args.lab)
    checks: dict[str, bool] = {}
    try:
        receipts = _read_lines(KIT / "PREFLIGHT-RECEIPTS.jsonl")
        summary = _read(KIT / "PREFLIGHT-SUMMARY.json")
        side = _read(KIT / "PREFLIGHT-SIDE-EFFECTS.json")
        baseline = _read(lab / "SECURITY-FAILING-TEST-BASELINE.json")
        prereg = _read_lines(lab / "SECURITY-EXPERIMENT-PREREGISTRY.jsonl")
        reality = _read(lab / "SECURITY-REALITY-MAP.json")
        manifest = _read(lab / "LAB-ARTIFACT-MANIFEST.json")
    except FileNotFoundError as e:
        print(f"FATAL: missing artifact {e}", file=sys.stderr)
        return 2

    checks["all_receipts_pass"] = bool(receipts) and all(r.get("verdict") == "PASS" for r in receipts)
    checks["receipts_nonempty"] = all(r.get("output_sha256") for r in receipts)
    checks["receipts_match_head"] = all(r.get("code_head") == args.head for r in receipts)
    checks["registered_equals_executed"] = summary.get("registered") == summary.get("executed")
    checks["executed_equals_163"] = summary.get("executed") == 163
    checks["failed_zero"] = summary.get("failed") == 0
    checks["baseline_was_red"] = baseline.get("expected_red_before_patch") is True and baseline.get("failed", 0) > 0
    checks["preregistered_experiments"] = len(prereg) >= 6
    checks["memory_unchanged_during_run"] = side.get("memory_unchanged") is True
    checks["miniapp_hits_unchanged_during_run"] = side.get("miniapp_hits_unchanged") is True
    checks["send_log_unchanged_during_run"] = side.get("send_log_unchanged") is True
    checks["send_log_zero_delta_during_run"] = (
        side.get("send_log_delta", {}).get("delta_rows") in (0, None))
    checks["provenance_distinct"] = len({reality.get("initial_document_commit"),
                                         reality.get("security_correction_commit"),
                                         reality.get("provenance_commit")}) == 3
    checks["manifest_hashes_match"] = True
    for a in manifest.get("artifacts", []):
        f = lab / a["file"]
        if not f.is_file():
            checks["manifest_hashes_match"] = False
            continue
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        if h != a.get("sha256"):
            checks["manifest_hashes_match"] = False

    failed = [name for name, ok in checks.items() if not ok]

    independent = False
    identity = args.identity or "implementing-session-preflight"
    independence_statement = None
    if not args.preflight:
        if not args.identity or not args.statement:
            print("FATAL: non-preflight mode requires --identity and --statement", file=sys.stderr)
            return 2
        stmt = Path(args.statement)
        if not stmt.is_file():
            print(f"FATAL: statement file missing: {stmt}", file=sys.stderr)
            return 2
        text = stmt.read_text(encoding="utf-8")
        if "INDEPENDENT_SESSION_ATTESTATION" not in text:
            print("FATAL: statement lacks INDEPENDENT_SESSION_ATTESTATION line", file=sys.stderr)
            return 2
        if args.identity not in text:
            print("FATAL: statement does not name the same identity", file=sys.stderr)
            return 2
        independent = True
        independence_statement = str(stmt)

    confirmed = not failed
    terminal = ("SECURITY_SHADOW_PASS" if (confirmed and independent)
                else ("IMPLEMENTATION_COMPLETE_VERIFICATION_PENDING" if confirmed
                      else "FAILED_SAFE"))
    result = {
        "schema": "kit-independent-verdict/1",
        "generated_at": None,  # filled below
        "exact_verified_head": args.head,
        "implementation_head": IMPLEMENTATION_HEAD,
        "verifier_identity": identity,
        "verifier_independent": independent,
        "independence_statement": independence_statement,
        "mode": "preflight" if args.preflight else "independent",
        "confirmed": confirmed,
        "failed_checks": failed,
        "checks": checks,
        "terminal_state": terminal,
        "note": ("Preflight by the implementing session — independent=false."
                 if args.preflight else
                 "Attested independent session; identity recorded verbatim. "
                 "This JSON alone is not proof of separation; the statement and "
                 "session record must back it."),
    }
    import datetime
    result["generated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    out_name = "PREFLIGHT-VERDICT.json" if args.preflight else "INDEPENDENT-VERDICT.json"
    out = KIT / out_name
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"confirmed": confirmed, "failed_checks": failed,
                      "verifier_independent": independent,
                      "terminal_state": terminal}, ensure_ascii=False))
    return 0 if confirmed else 1


if __name__ == "__main__":
    raise SystemExit(main())
