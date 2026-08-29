"""Change records. Written by the change executor, never by Doctor."""

from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path
from typing import Any

from octopus_cognition.doctor.chain import GENESIS, chain_hash

CHAIN_ID = "octopus-audit-change"
STATE_DIR = Path("/var/lib/octopus/state/change")
HEAD_SCHEMA = "octopus.change-ledger.head.v1"


class ChangeLedger:
    def __init__(self, directory: Path = STATE_DIR) -> None:
        self.directory = directory
        self.ledger = directory / "ledger.jsonl"
        self.head = directory / "HEAD.json"

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
                record = dict(body)
                record["schema"] = "octopus.change-record.v1"
                record["chain_id"] = CHAIN_ID
                record["seq"] = seq
                if "before_digest" not in record or "rollback_tested" not in record or "outcome" not in record:
                    raise ValueError("change record requires before_digest, rollback_tested, outcome")
                digest = chain_hash(prev, record)
                entry = {"seq": seq, "prev_hash": prev, "hash": digest, "body": record}
                with self.ledger.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                tmp = self.head.with_suffix(".tmp")
                tmp.write_text(
                    json.dumps({"seq": seq, "hash": digest, "schema": HEAD_SCHEMA, "chain_id": CHAIN_ID}) + "\n",
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
            expect = chain_hash(prev, entry.get("body") or {})
            if expect != entry.get("hash"):
                return False, seq, "digest"
            prev = entry["hash"]
        head_seq, head_hash = self.read_head()
        if seq and (head_seq != seq or head_hash != prev):
            return False, seq, "head_mismatch"
        return True, None, f"seq={seq}"
