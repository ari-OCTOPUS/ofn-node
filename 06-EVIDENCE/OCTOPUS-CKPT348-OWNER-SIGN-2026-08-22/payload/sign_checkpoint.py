#!/usr/bin/env python3
"""Sign audit checkpoint with existing root-v2. Windows only."""
from __future__ import annotations
import hashlib, json, os, sys
from datetime import datetime, timezone
from pathlib import Path
from nacl.signing import SigningKey
HERE = Path(__file__).resolve().parent
SRC = HERE / "checkpoint.unsigned.json"
EXPECTED_V2 = "sha256:a20d836d1f461482c76c4d3ed6c6de301d38b3e8e0ef4707e87d7b45e2223a40"
BUNDLE = HERE / "SIGNED-CHECKPOINT-BUNDLE"

def find_key():
    for path in [
        HERE / "private" / "root-v2.ed25519.private",
        Path.home() / "Desktop" / "OCTOPUS-ROOT-V2" / "private" / "root-v2.ed25519.private",
    ]:
        if path.is_file():
            return path
    print("existing root-v2 private key not found", file=sys.stderr)
    raise SystemExit(2)

def main():
    payload = SRC.read_bytes()
    key = SigningKey(find_key().read_bytes())
    fp = "sha256:" + hashlib.sha256(bytes(key.verify_key)).hexdigest()
    if fp != EXPECTED_V2:
        print("refusing unknown key", file=sys.stderr)
        return 5
    BUNDLE.mkdir(exist_ok=True)
    (BUNDLE / "checkpoint.json").write_bytes(payload)
    (BUNDLE / "checkpoint.json.sig").write_bytes(key.sign(payload).signature)
    (BUNDLE / "root-v2.ed25519.public").write_bytes(bytes(key.verify_key))
    (BUNDLE / "manifest.json").write_text(json.dumps({
        "bundle_type": "AUDIT_CHECKPOINT",
        "public_key_fingerprint": fp,
        "signed_at": datetime.now(timezone.utc).isoformat(),
        "private_key_included": False,
    }, indent=2))
    print("signed checkpoint with root-v2", fp)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
