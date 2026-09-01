#!/usr/bin/env python3
"""Read-only lineage gap scan for STAGE-01.

The concept registry states expected_status. This tool walks the tree and
derives a status from path existence. Agreement is a measurement. Disagreement
is a failed scan.

It does not read secret files, does not write production state, does not
open gates, and does not open a network socket.

Usage:
    python3 tools/gap_scan.py
    python3 tools/gap_scan.py --json
    python3 tools/gap_scan.py --tests
    python3 tools/gap_scan.py --write-receipt PATH
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_REL = os.path.join(
    "docs",
    "octopus-surgery",
    "stage-01-lineage-scan",
    "2026-09-01",
    "CONCEPT-REGISTRY.json",
)
INTAKE_REL = os.path.join(
    "docs",
    "octopus-surgery",
    "stage-01-lineage-scan",
    "2026-09-01",
    "receipts",
    "INTAKE-SHA256.json",
)
# Text sources are hashed after CRLF → LF. Windows checkouts with
# core.autocrlf must not look like a different document.
SOURCE_FILES = {
    "repo_stage00": {
        "rel": os.path.join(
            "docs", "octopus-surgery", "stage-01-lineage-scan",
            "2026-09-01", "sources", "STAGE-00-SCAN-REPORT.md",
        ),
        "normalize_newlines": True,
    },
    "repo_cbhf": {
        "rel": os.path.join(
            "docs", "octopus-surgery", "stage-01-lineage-scan",
            "2026-09-01", "sources", "CB-INSIGHTS-HUGGING-FACE.md",
        ),
        "normalize_newlines": True,
    },
    "repo_ten_aspect": {
        "rel": os.path.join(
            "docs", "octopus-surgery", "stage-01-lineage-scan",
            "2026-09-01", "sources", "octopus-deep-scan-10-aspects.md",
        ),
        "normalize_newlines": True,
    },
    "repo_image_1": {
        "rel": os.path.join(
            "docs", "octopus-surgery", "stage-01-lineage-scan",
            "2026-09-01", "sources", "images", "image_1.png",
        ),
        "normalize_newlines": False,
    },
    "repo_image_2": {
        "rel": os.path.join(
            "docs", "octopus-surgery", "stage-01-lineage-scan",
            "2026-09-01", "sources", "images", "image_2.png",
        ),
        "normalize_newlines": False,
    },
}

FORBIDDEN_READ_PREFIXES = (
    os.path.expanduser("~/.config/ofn"),
    "/etc/cloudflared",
)

STATUSES = frozenset(
    {
        "present_in_this_lineage",
        "partial_in_this_lineage",
        "documented_only",
        "body_not_on_this_host",
        "absent",
        "contradicted",
        "owner_gated",
        "historical_stale",
        "incomplete_enumeration",
    }
)

DERIVE = frozenset(
    {
        "present_if_all_exist",
        "partial_if_exist_and_absent",
        "body_not_on_this_host_if_all_absent",
        "absent_if_none_exist",
        "documented_only_if_docs",
        "fixed",
    }
)


class GapScanError(ValueError):
    """Fail-closed registry or path error."""


def _sha256_file(path: str, *, normalize_newlines: bool = False) -> str:
    """Hash file bytes. Text sources strip CR so Windows CRLF == Linux LF."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        data = fh.read()
    if normalize_newlines:
        data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    digest.update(data)
    return digest.hexdigest()


def _exists(root: str, rel: str) -> bool:
    if not rel or rel.startswith("/") or ".." in rel.split("/"):
        raise GapScanError(f"refusing unsafe path {rel!r}")
    return os.path.exists(os.path.join(root, rel))


def _classify(concept: dict[str, Any], root: str) -> dict[str, Any]:
    cid = concept.get("id")
    if not cid:
        raise GapScanError("concept missing id")
    expected = concept.get("expected_status")
    derive = concept.get("derive")
    if expected not in STATUSES:
        raise GapScanError(f"{cid}: unknown expected_status {expected!r}")
    if derive not in DERIVE:
        raise GapScanError(f"{cid}: unknown derive {derive!r}")

    must_exist = list(concept.get("must_exist") or [])
    must_not_exist = list(concept.get("must_not_exist") or [])
    present = [p for p in must_exist if _exists(root, p)]
    missing = [p for p in must_exist if p not in present]
    absent_ok = [p for p in must_not_exist if not _exists(root, p)]
    unexpectedly_present = [p for p in must_not_exist if p not in absent_ok]

    if derive == "present_if_all_exist":
        derived = (
            "present_in_this_lineage"
            if present and not missing and not unexpectedly_present
            else "contradicted"
        )
    elif derive == "partial_if_exist_and_absent":
        derived = (
            "partial_in_this_lineage"
            if present and not missing and not unexpectedly_present
            else "contradicted"
        )
    elif derive == "body_not_on_this_host_if_all_absent":
        derived = (
            "body_not_on_this_host"
            if must_not_exist and not unexpectedly_present and not present
            else "contradicted"
        )
    elif derive == "absent_if_none_exist":
        derived = (
            "absent"
            if must_exist and not present and not unexpectedly_present
            else "contradicted"
        )
    elif derive == "documented_only_if_docs":
        docs_ok = present and all(p.startswith("docs/") for p in present)
        derived = (
            "documented_only"
            if docs_ok and not missing and not unexpectedly_present
            else "contradicted"
        )
    else:
        paths_ok = not missing and not unexpectedly_present
        derived = expected if paths_ok else "contradicted"

    return {
        "id": cid,
        "name": concept.get("name"),
        "tier": concept.get("tier"),
        "sources": concept.get("sources") or [],
        "expected_status": expected,
        "derived_status": derived,
        "match": derived == expected,
        "present": present,
        "missing": missing,
        "absent_ok": absent_ok,
        "unexpectedly_present": unexpectedly_present,
        "notes": concept.get("notes"),
    }


def load_registry(root: str = ROOT) -> dict[str, Any]:
    path = os.path.join(root, REGISTRY_REL)
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if data.get("schema") != "octopus.gap_scan.registry.v1":
        raise GapScanError("registry schema mismatch")
    concepts = data.get("concepts")
    if not isinstance(concepts, list) or not concepts:
        raise GapScanError("registry has no concepts")
    ids = [c.get("id") for c in concepts]
    if len(ids) != len(set(ids)):
        raise GapScanError("duplicate concept id")
    return data


def scan_sources(root: str = ROOT) -> dict[str, Any]:
    intake_path = os.path.join(root, INTAKE_REL)
    with open(intake_path, encoding="utf-8") as fh:
        intake = json.load(fh)
    measured = {
        key: _sha256_file(
            os.path.join(root, spec["rel"]),
            normalize_newlines=bool(spec["normalize_newlines"]),
        )
        for key, spec in SOURCE_FILES.items()
    }
    expected = intake.get("files") or {}
    mismatches = {
        key: {"expected": expected.get(key), "measured": digest}
        for key, digest in measured.items()
        if expected.get(key) != digest
    }
    return {
        "cbhf_uploads_identical": bool(intake.get("cbhf_uploads_identical")),
        "measured": measured,
        "mismatches": mismatches,
        "match": not mismatches,
    }


def scan_concepts(registry: dict[str, Any], root: str = ROOT) -> list[dict[str, Any]]:
    return [_classify(concept, root) for concept in registry["concepts"]]


def _git_head(root: str) -> str | None:
    head_path = os.path.join(root, ".git", "HEAD")
    if not os.path.isfile(head_path):
        return None
    with open(head_path, encoding="utf-8") as fh:
        ref = fh.read().strip()
    if ref.startswith("ref:"):
        ref_path = os.path.join(root, ".git", ref.split(" ", 1)[1].strip())
        if not os.path.isfile(ref_path):
            return None
        with open(ref_path, encoding="utf-8") as fh:
            return fh.read().strip() or None
    return ref or None


def _working_tree_dirty(root: str) -> bool | None:
    """True when git reports any staged, unstaged, or untracked path.

    None means git could not be asked. A historical receipt that used
    `git_head` is left alone; new receipts use this plus base_git_head.
    """
    try:
        import subprocess
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    return bool(proc.stdout.strip())


def _scanner_sha256(root: str) -> str:
    return _sha256_file(
        os.path.join(root, "tools", "gap_scan.py"),
        normalize_newlines=True,
    )


def scan(*, root: str = ROOT, with_tests: bool = False) -> dict[str, Any]:
    for prefix in FORBIDDEN_READ_PREFIXES:
        if root.startswith(prefix):
            raise GapScanError("refusing to scan a secrets path")

    registry = load_registry(root)
    concepts = scan_concepts(registry, root)
    sources = scan_sources(root)
    sys.path.insert(0, root)
    from tools.repo_baseline import baseline

    out: dict[str, Any] = {
        "schema": "octopus.gap_scan.receipt.v1",
        "scanned_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root": "." if os.path.abspath(root) == os.path.abspath(ROOT) else root,
        "base_git_head": _git_head(root),
        "working_tree_dirty": _working_tree_dirty(root),
        "scanner_sha256": _scanner_sha256(root),
        "scope": "this_host_only",
        "vantage": "cursor-cloud-agent",
        "propose_only": True,
        "baseline": baseline(with_tests=with_tests),
        "sources": sources,
        "concepts": concepts,
        "numeric_claims": registry.get("numeric_claims") or [],
        "counts": {
            "concepts": len(concepts),
            "matched": sum(1 for row in concepts if row["match"]),
            "mismatched": sum(1 for row in concepts if not row["match"]),
            "by_derived_status": {},
        },
        "ok": sources["match"] and all(row["match"] for row in concepts),
    }
    by_status: dict[str, int] = {}
    for row in concepts:
        status = row["derived_status"]
        by_status[status] = by_status.get(status, 0) + 1
    out["counts"]["by_derived_status"] = dict(sorted(by_status.items()))
    return out


def render_text(receipt: dict[str, Any]) -> str:
    lines = [
        f"gap_scan ok={receipt['ok']} "
        f"matched={receipt['counts']['matched']}/"
        f"{receipt['counts']['concepts']}",
        f"head={receipt.get('base_git_head')}",
        f"tenants={', '.join(receipt['baseline']['tenants'])}",
    ]
    if "collected_tests" in receipt["baseline"]:
        lines.append(
            "collected_tests="
            f"{receipt['baseline']['collected_tests']} "
            "(receipt only; not a document constant)"
        )
    mismatches = [row for row in receipt["concepts"] if not row["match"]]
    if mismatches:
        lines.append("mismatches:")
        for row in mismatches:
            lines.append(
                f"  {row['id']}: expected {row['expected_status']} "
                f"derived {row['derived_status']} "
                f"missing={row['missing']} unexpected={row['unexpectedly_present']}"
            )
    if not receipt["sources"]["match"]:
        lines.append(f"source hash mismatches: {receipt['sources']['mismatches']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only STAGE-01 gap scan")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--tests", action="store_true",
                        help="also collect pytest count via repo_baseline")
    parser.add_argument("--write-receipt", metavar="PATH")
    args = parser.parse_args(argv)

    receipt = scan(with_tests=args.tests)
    if args.write_receipt:
        dest = args.write_receipt
        if os.path.isabs(dest):
            path = dest
        else:
            path = os.path.join(ROOT, dest)
        parent = os.path.dirname(path)
        os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(receipt, fh, ensure_ascii=False, indent=2)
            fh.write("\n")

    if args.json:
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
    else:
        print(render_text(receipt))
    return 0 if receipt["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
