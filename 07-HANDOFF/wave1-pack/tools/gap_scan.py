#!/usr/bin/env python3
"""Regenerate CONCEPT-CODE-GAP.csv by scanning the repo for concept terms.

The register shipped with this pack was built by reading documents. That makes it
a level-2 claim. This script turns it into a level-1 claim by checking, for each
concept, whether an implementation path and a test actually exist.

    python tools/gap_scan.py --repo F:\backup            # print
    python tools/gap_scan.py --repo F:\backup --out CONCEPT-CODE-GAP.csv

Read-only. Writes at most one CSV. Never enables a flag, never deletes.
"""
import argparse
import csv
import io
import os
import re
import subprocess
import sys

# concept id -> (search terms in docs, candidate code paths, candidate test paths)
PROBES = {
    "G-01": (["Envelope", "may_authorize", "redaction_applied"],
             ["_ops/events/envelope.py", "src/events/envelope.py"],
             ["tests/events/test_envelope.py"]),
    "G-02": (["run_id", "proposal_hash", "policy_version"],
             ["_ops/events/run_id.py"], ["tests/events/test_run_id.py"]),
    "G-03": (["Run Store", "run_store", "append-only"],
             ["_ops/events/run_store.py"], ["tests/events/test_run_store.py"]),
    "G-04": (["RUN_CREATED", "RUN_COMPLETED"],
             ["_ops/events/lifecycle.py"], ["tests/events/test_lifecycle.py"]),
    "G-05": (["idempotency", "payload fingerprint", "POST /proposals"],
             ["src/nbb_cp/api/proposals.py"], ["tests/nbb_cp/api/test_idempotency.py"]),
    "G-06": (["Truth Layer", "UNVERIFIED", "REPORTED", "CONFLICT"],
             ["_ops/truth/states.py"], ["tests/truth/test_states.py"]),
    "G-07": (["EXECUTION_RECEIPT", "execution receipt"],
             ["_ops/truth/receipt.py"], ["tests/truth/test_receipt.py"]),
    "G-08": (["Context Bundle"], ["src/nbb_cp/context_bundle.py"],
             ["tests/contract/test_context_bundle.py"]),
    "G-14": (["INV-1", "integer cents"], ["src/nbb_cp/invariants/"],
             ["tests/contract/test_invariants.py"]),
    "M-01": (["held-out", "heldout"], ["eval/heldout/"], ["eval/heldout/manifest.json"]),
    "M-03": (["scaffold-variation", "scaffold variation"], ["eval/scaffold/"],
             ["eval/scaffold/results.json"]),
    "M-05": (["external judge", "judge"], ["eval/judge/"], ["eval/judge/criteria.hash"]),
    "M-06": (["P3", "metric_version"], ["metrics/"], ["tests/metrics/test_blinded.py"]),
    "M-09": (["fault injection", "kill Redis"], ["eval/fault/"], ["eval/fault/results.json"]),
    "B-01": (["L-OBSERVE", "edge profile", "edge envelope"], ["_ops/edge/profile.py"],
             ["tests/edge/test_profile.py"]),
    "B-02": (["board_id", "firmware_hash"], ["_ops/edge/identity.py"],
             ["tests/edge/test_identity.py"]),
    "B-05": (["propose-only", "edge propose"], ["_ops/edge/"],
             ["tests/edge/test_structural.py"]),
    "B-06": (["edge budget", "per-board cap"], ["_ops/edge/budget.py"],
             ["tests/edge/test_budget.py"]),
    "V-01": (["VBAA", "ArgumentProvenanceGuard"], ["_ops/vbaa/"], ["tests/vbaa/"]),
    "S-01": (["honeypot", "prompt injection"], ["_ops/security/honeypot"],
             ["tests/security/test_honeypot.py"]),
}

DOC_EXT = (".md", ".yaml", ".yml", ".txt")
SKIP = {".git", "__pycache__", ".pytest_cache", "node_modules", "99-ARCHIVE"}


def doc_hits(repo, terms):
    hits = []
    for dirpath, dirnames, filenames in os.walk(repo):
        dirnames[:] = [d for d in dirnames if d not in SKIP]
        for fn in filenames:
            if not fn.endswith(DOC_EXT):
                continue
            fp = os.path.join(dirpath, fn)
            try:
                txt = io.open(fp, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            if any(t.lower() in txt.lower() for t in terms):
                hits.append(os.path.relpath(fp, repo))
                if len(hits) >= 4:
                    return hits
    return hits


def first_existing(repo, paths):
    for p in paths:
        if os.path.exists(os.path.join(repo, p)):
            return p
    return None


def classify(doc, code, test):
    """The whole point: written but not built is a distinct, nameable state."""
    if code and test:
        return "implemented"
    if code and not test:
        return "code-without-test"
    if doc and not code:
        return "concept-only"          # the 'written but no code' band
    if not doc and not code:
        return "absent"                # not even written down
    return "unknown"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.getcwd())
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    repo = os.path.abspath(args.repo)

    rows = [["id", "doc_sources", "code_path", "test_path", "state"]]
    tally = {}
    for cid, (terms, codes, tests) in sorted(PROBES.items()):
        docs = doc_hits(repo, terms)
        code = first_existing(repo, codes)
        test = first_existing(repo, tests)
        state = classify(docs, code, test)
        tally[state] = tally.get(state, 0) + 1
        rows.append([cid, "; ".join(docs) or "none", code or "none",
                     test or "none", state])

    if args.out:
        with open(args.out, "w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerows(rows)
        print("wrote", args.out)
    else:
        for r in rows:
            print(" | ".join(str(x)[:48].ljust(48) for x in r))

    total = len(PROBES)
    concept_only = tally.get("concept-only", 0) + tally.get("absent", 0)
    print("\nprobed: %d" % total, file=sys.stderr)
    for k in sorted(tally):
        print("  %-20s %d" % (k, tally[k]), file=sys.stderr)
    print("\nwritten-but-unbuilt share: %.0f%% (%d/%d)"
          % (100.0 * concept_only / total, concept_only, total), file=sys.stderr)
    print("NOTE: this is a share of the probe set, not of the whole system. "
          "Do not quote it as a system-wide figure.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
