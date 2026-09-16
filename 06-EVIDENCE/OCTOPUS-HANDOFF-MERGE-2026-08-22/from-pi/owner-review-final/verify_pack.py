#!/usr/bin/env python3
"""Read-only integrity check for owner-review-final. Not a signature."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

EXPECTED_CHAIN = "octopus-audit-ledger"
EXPECTED_HASH = "sha256:ec98f51753c6565d845acd6734c052e2c929383469c8a2755d88dcfbb24b7fc2"


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def digest_of(entry) -> str | None:
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        return entry.get("sha256")
    return None


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()
    manifest_path = root / "MANIFEST.json"
    claimed = (root / "MANIFEST.json.sha256").read_text(encoding="utf-8").strip()
    actual = sha256(manifest_path)
    errors = []
    if claimed != actual and claimed != actual.removeprefix("sha256:"):
        errors.append(f"MANIFEST.json.sha256 mismatch {claimed} vs {actual}")
    man = json.loads(manifest_path.read_text(encoding="utf-8"))
    ck = man.get("audit_checkpoint") or man.get("seq_266") or {}
    if ck.get("chain_id") != EXPECTED_CHAIN:
        errors.append(f"chain_id {ck.get('chain_id')}")
    rec = ck.get("record_hash_full") or ck.get("anchored_head_hash")
    if rec != EXPECTED_HASH:
        errors.append(f"seq266 hash {rec}")
    listed = man.get("files") or {}
    listed_paths = set()
    for rel, entry in listed.items():
        rel_s = str(rel).replace("\\", "/")
        if rel_s.startswith("/") or ".." in Path(rel_s).parts:
            errors.append(f"illegal path {rel_s}")
            continue
        listed_paths.add(rel_s)
        path = (root / rel_s).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            errors.append(f"escapes root {rel_s}")
            continue
        if not path.is_file():
            errors.append(f"missing {rel_s}")
            continue
        got = sha256(path)
        want = digest_of(entry)
        if got != want:
            errors.append(f"digest mismatch {rel_s}")
    extras = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = str(path.relative_to(root)).replace("\\", "/")
        if rel in {"MANIFEST.json", "MANIFEST.json.sha256"}:
            continue
        if rel not in listed_paths:
            extras.append(rel)
    if extras:
        errors.append("unlisted: " + ", ".join(extras))
    print("manifest_digest", actual)
    print("digest_is_signature", False)
    print("read_only_is_not_integrity", True)
    print("chain_id_ok", ck.get("chain_id") == EXPECTED_CHAIN)
    print("seq266_full_hash_ok", rec == EXPECTED_HASH)
    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("PASS pack digests match (not a signature)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
