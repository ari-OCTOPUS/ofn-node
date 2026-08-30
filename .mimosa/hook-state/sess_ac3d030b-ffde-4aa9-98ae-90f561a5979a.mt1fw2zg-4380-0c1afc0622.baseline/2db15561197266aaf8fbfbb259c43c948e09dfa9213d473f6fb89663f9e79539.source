#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only mirror verifier (A2-001). stdlib-only. No network. No writes into --tree.

Exit: 0 PASS · 1 MISMATCH · 2 MALFORMED_INPUT
Hash-chain on receipts is integrity_hint only — not a signature.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_MANIFEST = "manifest.v1"
SCHEMA_RECEIPT = "receipt.v1"
SCHEMA_REPORT = "mirror_verify_report.v1"
ALG = "sha256"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
INTEGRITY_HINT = "hash-chain-unkeyed"
DEFAULT_DENYLIST = (
    ".git/",
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    "*.env",
    "*.pem",
    "*private*",
)

EXIT_PASS = 0
EXIT_MISMATCH = 1
EXIT_MALFORMED = 2


def canonical_dumps(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def posix_rel(path: str) -> str:
    return path.replace("\\", "/").lstrip("/")


def is_denied(rel: str, patterns: list[str]) -> bool:
    rel = posix_rel(rel)
    parts = rel.split("/")
    for raw in patterns:
        pat = posix_rel(str(raw))
        if not pat:
            continue
        prefix = pat.rstrip("/")
        if rel == prefix or rel.startswith(prefix + "/"):
            return True
        if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(Path(rel).name, pat):
            return True
        if any(fnmatch.fnmatch(part, prefix) for part in parts):
            return True
    return False


def load_json(path: Path) -> tuple[Any, str | None]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return None, f"read-failed:{path}:{exc}"
    if len(raw) == 0:
        return None, f"zero-byte:{path}"
    try:
        return json.loads(raw.decode("utf-8")), None
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, f"json:{path}:{exc}"


def validate_manifest(obj: Any) -> list[str]:
    errs: list[str] = []
    if not isinstance(obj, dict):
        return ["manifest-not-object"]
    if obj.get("schema") != SCHEMA_MANIFEST:
        errs.append("bad-manifest-schema")
    algo = obj.get("algorithm", ALG)
    if algo != ALG:
        errs.append("algorithm-must-be-sha256")
    denylist = obj.get("denylist", [])
    if denylist is not None and (
        not isinstance(denylist, list) or not all(isinstance(x, str) and x for x in denylist)
    ):
        errs.append("denylist-malformed")
    entries = obj.get("entries")
    if not isinstance(entries, list):
        errs.append("entries-not-array")
        return errs
    seen: set[str] = set()
    for i, row in enumerate(entries):
        if not isinstance(row, dict):
            errs.append(f"entry-{i}-not-object")
            continue
        rel = posix_rel(str(row.get("relative_path") or ""))
        if not rel or rel in (".", "..") or ".." in rel.split("/"):
            errs.append(f"entry-{i}-bad-path")
        if rel in seen:
            errs.append(f"entry-{i}-duplicate-path")
        seen.add(rel)
        if row.get("algorithm") != ALG:
            errs.append(f"entry-{i}-algorithm")
        digest = row.get("sha256")
        if not isinstance(digest, str) or not HEX64.match(digest):
            errs.append(f"entry-{i}-sha256")
        size = row.get("size_bytes")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            errs.append(f"entry-{i}-size")
    return errs


def validate_receipt(obj: Any) -> list[str]:
    errs: list[str] = []
    if not isinstance(obj, dict):
        return ["receipt-not-object"]
    if obj.get("schema_version") != SCHEMA_RECEIPT:
        errs.append("bad-receipt-schema")
    if not str(obj.get("receipt_id") or "").strip():
        errs.append("receipt-id-missing")
    if not str(obj.get("snapshot_id") or "").strip():
        errs.append("snapshot-id-missing")
    for field in ("manifest_hash", "report_hash"):
        val = obj.get(field)
        if not isinstance(val, str) or not HEX64.match(val):
            errs.append(f"{field}-malformed")
    prev = obj.get("previous_receipt_hash")
    if prev is not None and (not isinstance(prev, str) or not HEX64.match(prev)):
        errs.append("previous_receipt_hash-malformed")
    if not str(obj.get("observed_at") or "").strip():
        errs.append("observed_at-missing")
    if not str(obj.get("observer_node") or "").strip():
        errs.append("observer_node-missing")
    if obj.get("result") not in ("PASS", "MISMATCH", "MALFORMED"):
        errs.append("result-not-allowed")
    if obj.get("integrity_hint") != INTEGRITY_HINT:
        errs.append("integrity_hint-must-be-hash-chain-unkeyed")
    return errs


def walk_tree(root: Path, denylist: list[str]) -> dict[str, Path]:
    found: dict[str, Path] = {}
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        rel_dir = posix_rel(os.path.relpath(dirpath, root))
        if rel_dir == ".":
            rel_dir = ""
        # prune denied directories in-place
        keep = []
        for name in dirnames:
            rel = posix_rel(f"{rel_dir}/{name}" if rel_dir else name)
            if is_denied(rel, denylist) or is_denied(rel + "/", denylist):
                continue
            keep.append(name)
        dirnames[:] = sorted(keep)
        for name in filenames:
            rel = posix_rel(f"{rel_dir}/{name}" if rel_dir else name)
            if is_denied(rel, denylist):
                continue
            found[rel] = Path(dirpath) / name
    return found


def receipt_content_hash(obj: dict) -> str:
    return sha256_bytes(canonical_dumps(obj))


def check_receipts(current: dict | None, prior: list[dict]) -> list[str]:
    """integrity_hint only: detect replay and broken order in the supplied set."""
    issues: list[str] = []
    if current is None:
        return issues
    seen_ids: set[str] = set()
    last_hash: str | None = None
    for rec in prior:
        rid = str(rec.get("receipt_id") or "")
        if rid in seen_ids:
            issues.append(f"replayed-receipt:{rid}")
        seen_ids.add(rid)
        prev = rec.get("previous_receipt_hash")
        if last_hash is None:
            if prev is not None:
                issues.append(f"out-of-order-receipt:{rid}")
        elif prev != last_hash:
            issues.append(f"out-of-order-receipt:{rid}")
        last_hash = receipt_content_hash(rec)
    rid = str(current.get("receipt_id") or "")
    if rid in seen_ids:
        issues.append(f"replayed-receipt:{rid}")
    prev = current.get("previous_receipt_hash")
    if last_hash is None:
        if prev is not None:
            issues.append(f"out-of-order-receipt:{rid}")
    elif prev != last_hash:
        issues.append(f"out-of-order-receipt:{rid}")
    return issues


def verify(tree: Path, manifest: dict, receipts: tuple[dict | None, list[dict]] | None = None) -> dict:
    denylist = list(manifest.get("denylist") or DEFAULT_DENYLIST)
    expected: dict[str, dict] = {}
    for row in manifest["entries"]:
        rel = posix_rel(row["relative_path"])
        if is_denied(rel, denylist):
            continue
        expected[rel] = row

    actual = walk_tree(tree, denylist)
    missing = sorted(set(expected) - set(actual))
    unexpected = sorted(set(actual) - set(expected))
    mismatches: list[dict] = []
    for rel in sorted(set(expected) & set(actual)):
        path = actual[rel]
        want = expected[rel]
        try:
            size = path.stat().st_size
            digest = sha256_file(path)
        except OSError as exc:
            mismatches.append({"path": rel, "reason": f"stat-failed:{exc}"})
            continue
        if size != want["size_bytes"] or digest != want["sha256"]:
            mismatches.append({
                "path": rel,
                "reason": "content-or-size",
                "got_size": size,
                "want_size": want["size_bytes"],
                "got_sha256": digest,
                "want_sha256": want["sha256"],
            })

    receipt_issues: list[str] = []
    if receipts is not None:
        receipt_issues = check_receipts(receipts[0], receipts[1])

    if missing or unexpected or mismatches or receipt_issues:
        result = "MISMATCH"
        exit_code = EXIT_MISMATCH
    else:
        result = "PASS"
        exit_code = EXIT_PASS

    body = {
        "schema": SCHEMA_REPORT,
        "result": result,
        "exit_code": exit_code,
        "manifest_hash": sha256_bytes(canonical_dumps(manifest)),
        "entry_count": len(expected),
        "actual_count": len(actual),
        "missing": missing,
        "unexpected": unexpected,
        "mismatches": mismatches,
        "denylist": sorted(denylist),
        "receipt_issues": receipt_issues,
        "integrity_hint": INTEGRITY_HINT,
    }
    report_hash = sha256_bytes(canonical_dumps(body))
    body["report_hash"] = report_hash
    return body


def emit(obj: dict, dest: Path | None) -> None:
    blob = (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if dest is None:
        sys.stdout.buffer.write(blob)
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_bytes(blob)
    os.replace(tmp, dest)
    got = dest.read_bytes()
    if got != blob or len(got) == 0:
        raise RuntimeError(f"report-write-verify-failed:{dest}")


def load_receipts(receipt_path: Path | None, receipts_dir: Path | None) -> tuple[dict | None, list[dict], list[str]]:
    errs: list[str] = []
    prior: list[dict] = []
    current = None
    if receipts_dir is not None:
        if not receipts_dir.is_dir():
            return None, [], [f"receipts-dir-missing:{receipts_dir}"]
        for p in sorted(receipts_dir.glob("*.json")):
            obj, err = load_json(p)
            if err:
                errs.append(err)
                continue
            ve = validate_receipt(obj)
            if ve:
                errs.extend(f"{p.name}:{e}" for e in ve)
                continue
            prior.append(obj)
    if receipt_path is not None:
        obj, err = load_json(receipt_path)
        if err:
            errs.append(err)
        else:
            ve = validate_receipt(obj)
            if ve:
                errs.extend(ve)
            else:
                current = obj
    return current, prior, errs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mirror_verify")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("verify", help="read-only verify tree against manifest")
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--tree", required=True, type=Path)
    p.add_argument("--receipt", type=Path, default=None)
    p.add_argument("--receipts-dir", type=Path, default=None)
    p.add_argument("--out", type=Path, default=None, help="write report JSON here; never into --tree")
    args = parser.parse_args(argv)

    if args.cmd != "verify":
        return EXIT_MALFORMED

    tree: Path = args.tree
    if not tree.is_dir():
        malformed = {
            "schema": SCHEMA_REPORT,
            "result": "MALFORMED",
            "exit_code": EXIT_MALFORMED,
            "errors": [f"tree-not-dir:{tree}"],
            "integrity_hint": INTEGRITY_HINT,
        }
        malformed["report_hash"] = sha256_bytes(canonical_dumps({k: v for k, v in malformed.items() if k != "report_hash"}))
        try:
            emit(malformed, args.out)
        except RuntimeError:
            return EXIT_MALFORMED
        return EXIT_MALFORMED

    if args.out is not None:
        try:
            out_resolved = args.out.resolve()
            tree_resolved = tree.resolve()
            if out_resolved.is_relative_to(tree_resolved):
                print("refusing to write report inside --tree", file=sys.stderr)
                return EXIT_MALFORMED
        except AttributeError:
            # py<3.9; 3.13 has is_relative_to
            pass

    manifest, err = load_json(args.manifest)
    errors = [err] if err else validate_manifest(manifest)
    current, prior, rec_errs = load_receipts(args.receipt, args.receipts_dir)
    errors.extend(rec_errs)
    if errors:
        malformed = {
            "schema": SCHEMA_REPORT,
            "result": "MALFORMED",
            "exit_code": EXIT_MALFORMED,
            "errors": errors,
            "integrity_hint": INTEGRITY_HINT,
        }
        body = {k: v for k, v in malformed.items() if k != "report_hash"}
        malformed["report_hash"] = sha256_bytes(canonical_dumps(body))
        emit(malformed, args.out)
        return EXIT_MALFORMED

    report = verify(tree, manifest, (current, prior) if (current is not None or prior) else None)
    emit(report, args.out)
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
