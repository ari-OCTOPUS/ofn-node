from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
from typing import Any

GENESIS = "0" * 64


def canon(obj: dict[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def state_hash(obj: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canon(obj)).hexdigest()


class ChainedLedger:
    """Append-only hash-chained JSONL. Records are never rewritten."""

    def __init__(self, directory: Path, head_schema: str) -> None:
        self.directory = directory
        self.ledger = directory / "ledger.jsonl"
        self.head = directory / "HEAD.json"
        self.head_schema = head_schema

    def read_head(self) -> tuple[int, str]:
        try:
            doc = json.loads(self.head.read_text(encoding="utf-8"))
            return int(doc["seq"]), str(doc["hash"])
        except (OSError, ValueError, KeyError):
            return 0, GENESIS

    def append(self, body: dict[str, Any]) -> dict[str, Any]:
        self.directory.mkdir(parents=True, exist_ok=True)
        lock_path = self.directory / "ledger.lock"
        with lock_path.open("a+", encoding="utf-8") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                seq, prev = self.read_head()
                seq += 1
                digest = hashlib.sha256(
                    prev.encode("utf-8") + str(seq).encode("ascii") + canon(body)
                ).hexdigest()
                entry = {"seq": seq, "prev_hash": prev, "hash": digest, "body": body}
                with self.ledger.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                tmp = self.head.with_suffix(".tmp")
                tmp.write_text(
                    json.dumps({"seq": seq, "hash": digest, "schema": self.head_schema}) + "\n",
                    encoding="utf-8",
                )
                os.replace(tmp, self.head)
                return entry
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def verify(self) -> tuple[bool, int | None, str]:
        prev = GENESIS
        seq = 0
        if not self.ledger.exists():
            return True, None, "empty"
        for line in self.ledger.read_text(encoding="utf-8").splitlines():
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
                prev.encode("utf-8") + str(seq).encode("ascii") + canon(entry.get("body") or {})
            ).hexdigest()
            if expect != entry.get("hash"):
                return False, seq, "digest"
            prev = entry["hash"]
        head_seq, head_hash = self.read_head()
        if seq and (head_seq != seq or head_hash != prev):
            return False, seq, "head_mismatch"
        return True, None, f"seq={seq}"

    def bodies(self) -> list[dict[str, Any]]:
        if not self.ledger.exists():
            return []
        out: list[dict[str, Any]] = []
        for line in self.ledger.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            body = dict(entry.get("body") or {})
            body["_seq"] = entry.get("seq")
            out.append(body)
        return out
