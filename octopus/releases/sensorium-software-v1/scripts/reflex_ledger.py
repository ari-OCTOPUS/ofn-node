#!/usr/bin/env python3
"""Tamper-evident Reflex advisory ledger. Observe-only; never executes host commands."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

GENESIS = "0" * 64
DIR = Path("/var/lib/octopus/state/reflex")
LEDGER = DIR / "ledger.jsonl"
HEAD = DIR / "HEAD.json"
LOCK = DIR / "ARMED.json"


def _canon(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def read_head() -> tuple[int, str]:
    try:
        doc = json.loads(HEAD.read_text(encoding="utf-8"))
        return int(doc["seq"]), str(doc["hash"])
    except (OSError, ValueError, KeyError):
        return 0, GENESIS


def append(body: dict) -> dict:
    DIR.mkdir(parents=True, exist_ok=True)
    seq, prev = read_head()
    seq += 1
    digest = hashlib.sha256(prev.encode("utf-8") + str(seq).encode("ascii") + _canon(body)).hexdigest()
    entry = {"seq": seq, "prev_hash": prev, "hash": digest, "body": body}
    with LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    tmp = HEAD.with_suffix(".tmp")
    tmp.write_text(json.dumps({"seq": seq, "hash": digest, "schema": "octopus.reflex-ledger.head.v1"}) + "\n", encoding="utf-8")
    os.replace(tmp, HEAD)
    return entry


def verify() -> tuple[bool, int | None, str]:
    prev = GENESIS
    seq = 0
    if not LEDGER.exists():
        return True, None, "empty"
    try:
        lines = LEDGER.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return False, None, f"unreadable:{exc}"
    for line in lines:
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            return False, seq + 1, "json"
        seq += 1
        if entry.get("seq") != seq or entry.get("prev_hash") != prev:
            return False, seq, "link"
        expect = hashlib.sha256(
            prev.encode("utf-8") + str(seq).encode("ascii") + _canon(entry.get("body") or {})
        ).hexdigest()
        if expect != entry.get("hash"):
            return False, seq, "digest"
        prev = entry["hash"]
    head_seq, head_hash = read_head()
    if seq and (head_seq != seq or head_hash != prev):
        return False, seq, "head_mismatch"
    return True, None, f"seq={seq}"


def lock_advisory_forever(reason: str) -> None:
    DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "armed": False,
        "locked": True,
        "lock_reason": reason,
        "owner_approval": "required",
        "note": "ledger break locks Reflex in advisory; do not auto-arm",
    }
    LOCK.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def is_armed() -> bool:
    try:
        doc = json.loads(LOCK.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return bool(doc.get("armed")) and not doc.get("locked")


def seal_prechain_archive(archive: Path) -> dict:
    """First chained entry: hash the archived advisory-spam file, do not ingest its lines."""
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    lines = [ln for ln in archive.read_text(encoding="utf-8").splitlines() if ln.strip()]
    body = {
        "schema": "octopus.reflex-ledger.genesis.v1",
        "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text(encoding="utf-8").strip(),
        "pre_chain_path": str(archive),
        "pre_chain_sha256": digest,
        "pre_chain_lines": len(lines),
        "pre_chain_note": (
            "archived unchained advisory_clear spam; not arming evidence; "
            "chain starts here"
        ),
        "actuator_authority": "NONE",
        "decision": "genesis_seal",
    }
    return append(body)


if __name__ == "__main__":
    import sys

    ok, seq, detail = verify()
    print(json.dumps({"ok": ok, "break_seq": seq, "detail": detail}))
    raise SystemExit(0 if ok else 2)
