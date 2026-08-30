#!/usr/bin/env python3
"""Read-only integrity check for the owner-review pack. Not a signature. Not provenance."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

EXPECTED_CHAIN_ID = "octopus-audit-ledger"
EXPECTED_SEQ = 266
EXPECTED_RECORD_HASH = "sha256:ec98f51753c6565d845acd6734c052e2c929383469c8a2755d88dcfbb24b7fc2"
FORBIDDEN_PHRASE = "ledger head = 266"


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    manifest_path = root / "MANIFEST.json"
    digest_path = root / "MANIFEST.json.sha256"
    errors: list[str] = []
    if not manifest_path.is_file():
        print("FAIL missing MANIFEST.json")
        return 2
    if not digest_path.is_file():
        errors.append("missing MANIFEST.json.sha256")
        claimed = ""
    else:
        claimed = digest_path.read_text(encoding="utf-8").strip()
        actual = sha256(manifest_path)
        if claimed != actual and claimed != actual.removeprefix("sha256:"):
            errors.append(f"MANIFEST.json.sha256 mismatch claimed={claimed} actual={actual}")
        print("manifest_digest", actual)
        print("manifest_digest_is_signature", False)
        print("manifest_digest_is_provenance", False)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    listed = manifest.get("files") or {}
    seq = manifest.get("seq_266") or manifest.get("audit_checkpoint") or {}
    chain_id = seq.get("chain_id") or (manifest.get("audit_checkpoint") or {}).get("chain_id")
    if chain_id != EXPECTED_CHAIN_ID:
        errors.append(f"chain_id {chain_id!r} != {EXPECTED_CHAIN_ID!r}")
    record_hash = seq.get("record_hash_full") or seq.get("anchored_head_hash")
    if record_hash != EXPECTED_RECORD_HASH:
        errors.append(f"seq 266 record hash {record_hash!r} != {EXPECTED_RECORD_HASH!r}")
    if seq.get("anchored_seq") not in {EXPECTED_SEQ, None} and seq.get("anchored_through_seq") not in {EXPECTED_SEQ, None}:
        if seq.get("anchored_seq") != EXPECTED_SEQ and seq.get("anchored_through_seq") != EXPECTED_SEQ:
            errors.append(f"anchored seq {seq.get('anchored_seq')}/{seq.get('anchored_through_seq')} != {EXPECTED_SEQ}")
    listed_paths = set()
    for rel, digest in listed.items():
        rel_s = str(rel).replace("\\", "/")
        if rel_s.startswith("/") or ".." in Path(rel_s).parts:
            errors.append(f"illegal path {rel_s}")
            continue
        listed_paths.add(rel_s)
        path = (root / rel_s).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            errors.append(f"path escapes pack root: {rel_s}")
            continue
        if not path.is_file():
            errors.append(f"missing artifact {rel_s}")
            continue
        got = sha256(path)
        if got != digest:
            errors.append(f"digest mismatch {rel_s} claimed={digest} actual={got}")
    extras = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = str(path.relative_to(root)).replace("\\", "/")
        if rel in {"MANIFEST.json", "MANIFEST.json.sha256"}:
            continue
        if rel not in listed_paths:
            extras.append(rel)
    if extras:
        errors.append("unlisted files: " + ", ".join(extras))
    print("read_only_is_not_integrity", True)
    print("chain_id_ok", chain_id == EXPECTED_CHAIN_ID)
    print("seq266_full_hash_ok", record_hash == EXPECTED_RECORD_HASH)
    print("forbidden_phrase", FORBIDDEN_PHRASE)
    if errors:
        print("FAIL")
        for err in errors:
            print(" -", err)
        return 1
    print("PASS pack digests match MANIFEST.json (still not a signature)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
