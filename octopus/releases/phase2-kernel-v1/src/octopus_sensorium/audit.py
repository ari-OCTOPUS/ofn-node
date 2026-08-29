"""Append-only JSONL audit with a hash chain. No truncate API. Credentials never written."""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any

DEFAULT_AUDIT_PATH = Path("/var/lib/octopus/audit/sensorium.jsonl")
DEFAULT_HEAD_PATH = Path("/var/lib/octopus/audit/head.hash")
GENESIS = "sha256:" + hashlib.sha256(b"").hexdigest()
_SECRET = re.compile(r"(password|secret|token|credential|private_key|passwd)", re.I)


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            ("***" if _SECRET.search(str(k)) else k): ("***" if _SECRET.search(str(k)) else _scrub(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_scrub(v) for v in value]
    return value


def canonical_json(record: dict[str, Any]) -> bytes:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def chain_hash(previous_hash: str, payload_hash: str) -> str:
    return sha256_bytes((previous_hash + payload_hash).encode("utf-8"))


def verify_chain(path: Path = DEFAULT_AUDIT_PATH, head_path: Path = DEFAULT_HEAD_PATH) -> tuple[bool, str]:
    if not path.exists() or path.stat().st_size == 0:
        return False, "empty"
    prev = GENESIS
    seen = {GENESIS}
    seq = 0
    last_record_hash = prev
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            seq += 1
            if "record_hash" not in rec:
                last_record_hash = sha256_bytes(line.encode("utf-8"))
                prev = last_record_hash
                seen.add(last_record_hash)
                continue
            body = {k: v for k, v in rec.items() if k not in {"record_hash", "signature", "previous_hash", "payload_hash"}}
            payload_hash = sha256_bytes(canonical_json(body))
            if rec.get("payload_hash") != payload_hash:
                return False, f"break at seq {seq}: payload_hash mismatch"
            parent = rec.get("previous_hash")
            self_ok = rec.get("record_hash") == chain_hash(parent, payload_hash)
            if parent == prev:
                if not self_ok:
                    return False, f"break at seq {seq}: record_hash mismatch"
            elif parent in seen and self_ok:
                # Concurrent or delayed append forked from an earlier record.
                # Keep both lines; the walk continues on this later record.
                pass
            else:
                return False, f"break at seq {seq}: previous_hash mismatch"
            prev = rec["record_hash"]
            seen.add(prev)
            last_record_hash = prev
    if head_path.exists():
        stored = head_path.read_text(encoding="utf-8").strip()
        if stored != last_record_hash:
            return False, "head.hash does not match chain tip"
    return True, f"seq={seq} head={last_record_hash}"


class AuditLog:
    def __init__(self, path: Path = DEFAULT_AUDIT_PATH, head_path: Path = DEFAULT_HEAD_PATH) -> None:
        self.path = path
        self.head_path = head_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch(mode=0o640)
        self._seq = 0
        self._prev = GENESIS
        self._restore_tip()

    def _restore_tip(self) -> None:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return
        last = None
        count = 0
        with self.path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    last = line.strip()
                    count += 1
        self._seq = count
        if not last:
            return
        rec = json.loads(last)
        self._prev = rec.get("record_hash") or sha256_bytes(last.encode("utf-8"))

    def append(self, event_type: str, **fields: Any) -> str:
        self._seq += 1
        audit_id = str(uuid.uuid4())
        body = {
            "audit_id": audit_id,
            "event_id": audit_id,
            "event_type": event_type,
            "sequence": self._seq,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
            **_scrub(fields),
        }
        payload_hash = sha256_bytes(canonical_json(body))
        record = {
            **body,
            "previous_hash": self._prev,
            "payload_hash": payload_hash,
            "signature": None,
        }
        record_hash = chain_hash(self._prev, payload_hash)
        record["record_hash"] = record_hash
        line = json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n"
        fd = os.open(self.path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o640)
        try:
            os.write(fd, line.encode("utf-8"))
            os.fsync(fd)
        finally:
            os.close(fd)
        self._prev = record_hash
        self.head_path.write_text(record_hash + "\n", encoding="utf-8")
        os.chmod(self.head_path, 0o640)
        return audit_id
