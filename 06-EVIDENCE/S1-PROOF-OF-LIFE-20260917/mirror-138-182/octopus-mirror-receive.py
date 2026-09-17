#!/usr/bin/env python3
"""OCTOPUS mirror-138 receiver on node 182 (witness). Push-based, append-only.

Receipt policy (owner verdict 2026-09-17): this receiver may claim RECEIVED and
HASH-MATCH only. It must NOT claim REPLAY-VALID while S1-GAP-02C (G13 replay
divergence) is open.

Design:
- stdin: tar stream {payload/, manifest.sha256, manifest.sha256.sig}
- manifest signed on 138 with ed25519 (ssh-keygen -Y, namespace octopus-mirror-manifest)
- path allowlist enforced; sizes capped; symlinks rejected
- publishes atomically (rename) into incoming/<UTC-stamp>/ — never rewrites old data
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HOME = Path("/var/lib/mirror-138")
ALLOWED_SIGNERS = HOME / "trusted" / "allowed_signers"
NAMESPACE = "octopus-mirror-manifest"
PRINCIPAL = "mirror-138"
MAX_FILE = 50 * 1024 * 1024
MAX_TOTAL = 200 * 1024 * 1024
ALLOW_PATTERNS = [
    re.compile(r"^api-budget/budget-ledger\.jsonl$"),
    re.compile(r"^api-budget/config/[^/]+\.jsonl?$"),
    re.compile(r"^revenue-drive/season-meter\.json$"),
]


_STAGE = None


def fail(reason: str) -> None:
    if _STAGE is not None:
        import shutil
        shutil.rmtree(str(_STAGE), ignore_errors=True)
    print(json.dumps({"status": "REJECTED", "reason": reason, "received_at_utc": _now()}))
    sys.exit(1)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def main() -> None:
    stage_root = HOME / "staging"
    global _STAGE
    stage = Path(tempfile.mkdtemp(prefix="stage-", dir=str(stage_root)))
    _STAGE = stage
    bundle = stage / "bundle"
    bundle.mkdir()
    rc = subprocess.call(["tar", "--no-same-owner", "--no-same-permissions", "-xf", "-", "-C", str(bundle)],
                         stdin=sys.stdin.buffer)
    if rc != 0:
        fail("tar_extract_failed")

    manifest = bundle / "manifest.sha256"
    sig = bundle / "manifest.sha256.sig"
    payload = bundle / "payload"
    if not (manifest.is_file() and sig.is_file() and payload.is_dir()):
        fail("bundle_shape_invalid")

    for p in bundle.rglob("*"):
        if p.is_symlink():
            fail(f"symlink_rejected:{p.name}")

    # OpenSSH 10 contract: -Y verify reads the signed message from STDIN (no positional file).
    v = subprocess.run(
        ["ssh-keygen", "-Y", "verify", "-f", str(ALLOWED_SIGNERS), "-I", PRINCIPAL,
         "-n", NAMESPACE, "-s", str(sig)],
        input=manifest.read_bytes(),
        capture_output=True,
    )
    if v.returncode != 0:
        fail("manifest_signature_invalid:" + v.stderr.decode(errors="replace")[:200].strip())

    entries = []
    total = 0
    for line in manifest.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            fail(f"manifest_line_malformed:{line[:60]}")
        digest, rel = parts[0], parts[1].lstrip("*").strip()
        if not any(p.match(rel) for p in ALLOW_PATTERNS):
            fail(f"path_not_allowlisted:{rel}")
        f = payload / rel
        if not f.is_file() or f.stat().st_size > MAX_FILE:
            fail(f"file_missing_or_too_big:{rel}")
        total += f.stat().st_size
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        if h != digest:
            fail(f"hash_mismatch:{rel}")
        entries.append({"path": rel, "sha256": h, "bytes": f.stat().st_size})
    if not entries or total > MAX_TOTAL:
        fail("payload_empty_or_total_too_big")

    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    target = HOME / "incoming" / stamp
    if target.exists():
        fail("target_exists_push_duplicate")
    os.rename(str(bundle), str(target))
    fd = os.open(str(target.parent), os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)

    receipt = {
        "status": "RECEIVED+HASH-MATCH",
        "witness_claim": "HASH-MATCH ONLY; REPLAY-VALID NOT CLAIMED (S1-GAP-02C open: G13 replay divergence)",
        "received_at_utc": _now(),
        "mirror_version": "v1",
        "files": entries,
    }
    rpath = target / "RECEIPT.json"
    with open(rpath, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(receipt, indent=2) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    # drop the signature+manifest alongside payload for independent re-verification
    print(json.dumps(receipt))
    try:
        import shutil
        shutil.rmtree(str(stage), ignore_errors=True)
    except Exception:
        pass


if __name__ == "__main__":
    main()
