#!/usr/bin/env python3
"""Verify a signed audit checkpoint. Does not close GAP-002 unless signature and hashes match."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from octopus_sensorium.audit import export_checkpoint, verify_chain
from octopus_sensorium.verify import SignatureError, load_root_public_key, load_signed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", type=Path)
    args = parser.parse_args()
    live = export_checkpoint()
    payload = json.loads(args.checkpoint.read_text(encoding="utf-8"))
    sig = args.checkpoint.with_suffix(args.checkpoint.suffix + ".sig")
    if not sig.exists():
        print(json.dumps({"ok": False, "reason": "unsigned", "gap": "GAP-002", "audit_integrity": "HASH_CHAIN_ONLY"}))
        return 2
    try:
        load_signed(args.checkpoint, load_root_public_key())
    except SignatureError as exc:
        print(json.dumps({"ok": False, "reason": str(exc), "gap": "GAP-002"}))
        return 2
    ok_chain, detail = verify_chain()
    match = payload.get("head_hash") == live.get("head_hash") and payload.get("sequence") == live.get("sequence")
    closed = bool(ok_chain and match)
    print(
        json.dumps(
            {
                "ok": closed,
                "chain": detail,
                "head_match": match,
                "gap": "GAP-002" if not closed else "GAP-002-CLOSED",
                "audit_integrity": "EXTERNALLY_CHECKPOINTED" if closed else "HASH_CHAIN_ONLY",
            }
        )
    )
    return 0 if closed else 2


if __name__ == "__main__":
    raise SystemExit(main())
