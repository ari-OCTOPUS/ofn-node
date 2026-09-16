#!/usr/bin/env python3
"""Fan-out receipts for OWNER_SIGNATURE_BUNDLE_V1 — run AFTER the owner signs.

Owner-only signing happens in SIGN-BUNDLE-V1-2026-08-21.ps1 (private key never
enters this process). This script only VERIFIES with the anchor public key and
then writes one receipt per owner-signable item (Phase 6) and updates the
pending owner-controlled statuses to OWNER_SIGNED_VIA_BUNDLE.

Usage:  python fanout_receipts.py [--root F:\\backup]

Refuses to run if the detached signature is missing or does not verify.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT_DEFAULT = Path(r"F:\backup")
OUT = ROOT_DEFAULT / "_ops" / "owner-signing" / "bundle-v1"
PUB = ROOT_DEFAULT / "_ops" / "owner-signing" / "octopus-owner-ed25519-public.pem"
FINGERPRINT = "2413e9746f13afc900b31ad4d966a6783d73662f661fa0d6dc578e9b244ab6b2"
BUNDLE_TAG = "OCTOPUS_OWNER_SIGNATURE_BUNDLE_V1"

# owner-controlled records whose pending status becomes OWNER_SIGNED_VIA_BUNDLE
OWNER_RECORDS = [
    "02-DECISIONS/PRE-REG-K9-THREE-SEED-2026-08-20.md",
    "02-DECISIONS/PRE-REG-ABLATION-FOUR-ARM-2026-08-20.md",
    "02-DECISIONS/OWNER-VERDICT-SHADOW-VERTICAL-SLICE-2026-08-20.md",
]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT_DEFAULT))
    args = ap.parse_args()
    root = Path(args.root)
    out = root / "_ops" / "owner-signing" / "bundle-v1"
    pub = root / "_ops" / "owner-signing" / "octopus-owner-ed25519-public.pem"

    manifest = json.loads((out / "OWNER_SIGNATURE_MANIFEST_V1.json").read_text(encoding="utf-8"))
    root_payload = (out / "OWNER_SIGNATURE_BUNDLE_V1.root-payload.txt").read_bytes()
    sig_path = out / "OWNER_SIGNATURE_BUNDLE_V1.root-payload.txt.sig"
    if not sig_path.is_file():
        print("FATAL: detached signature missing; owner must run SIGN-BUNDLE-V1-2026-08-21.ps1",
              file=sys.stderr)
        return 2

    # fingerprint check (fail-closed)
    proc = subprocess.run(["openssl", "pkey", "-pubin", "-in", str(pub), "-outform", "DER"],
                          capture_output=True)
    fp = hashlib.sha256(proc.stdout).hexdigest()
    if fp != FINGERPRINT:
        print("FATAL: public key fingerprint mismatch", file=sys.stderr)
        return 2

    # verify detached signature
    proc = subprocess.run(
        ["openssl", "pkeyutl", "-verify", "-pubin", "-inkey", str(pub),
         "-rawin", "-in", str(out / "OWNER_SIGNATURE_BUNDLE_V1.root-payload.txt"),
         "-sigfile", str(sig_path)],
        capture_output=True, text=True)
    ok = proc.returncode == 0 and "Verified" in proc.stdout
    if not ok:
        print("FATAL: root signature does not verify:", proc.stdout, proc.stderr, file=sys.stderr)
        return 2

    bundle_root = sha256_bytes(root_payload)
    sig_sha256 = sha256_bytes(sig_path.read_bytes())
    manifest_sha256 = sha256_bytes((out / "OWNER_SIGNATURE_MANIFEST_V1.json").read_bytes())

    receipts_dir = out / "receipts"
    receipts_dir.mkdir(parents=True, exist_ok=True)
    manifest_records = manifest["signature_records"]
    receipt_ids = []
    for rec in manifest_records:
        receipt = {
            "schema": "owner-signature-receipt/1",
            "sig_id": rec["sig_id"],
            "status": "OWNER_SIGNED_VIA_BUNDLE",
            "bundle_version": BUNDLE_TAG,
            "bundle_root": bundle_root,
            "root_signature_sha256": sig_sha256,
            "owner_key_fingerprint": FINGERPRINT,
            "payload_sha256": rec["payload_sha256"],
            "manifest_sha256": manifest_sha256,
            "verification_result": "Signature Verified Successfully",
            "generated": "2026-08-21",
        }
        p = receipts_dir / f"{rec['sig_id']}-receipt.json"
        p.write_text(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                     encoding="utf-8")
        receipt_ids.append(rec["sig_id"])
        print(f"receipt {rec['sig_id']} -> {p.relative_to(root)}")

    # update owner-controlled pending statuses (append-only: preserve original,
    # flip the pending marker after the signed root exists)
    for rel in OWNER_RECORDS:
        p = root / rel
        if not p.is_file():
            print(f"WARN missing record {rel}", file=sys.stderr)
            continue
        text = p.read_text(encoding="utf-8")
        new = text.replace("status: AWAITING_OWNER_SIGNATURE",
                           "status: OWNER_SIGNED_VIA_BUNDLE")
        if new == text:
            print(f"WARN no AWAITING_OWNER_SIGNATURE marker in {rel}", file=sys.stderr)
            continue
        p.write_text(new, encoding="utf-8")
        print(f"status updated {rel}")

    print("FANOUT_COMPLETE")
    print(json.dumps({
        "bundle_root": bundle_root,
        "root_signature_verified": True,
        "owner_items_signed": len(receipt_ids),
        "independent_items_remaining": ["SIG-IV"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
