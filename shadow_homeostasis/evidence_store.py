"""Bounded, locked, hash-chained local journal. Hashes are not authentication."""
from contextlib import contextmanager
from datetime import datetime
import hashlib
import os
from pathlib import Path

from .canonical import canonical, digest, strict_json
from .observation import parse_dt

ZERO = "0" * 64


class LedgerError(ValueError):
    pass


class TornTail(LedgerError):
    pass


class EvidenceStore:
    def __init__(self, path, *, max_bytes=8 * 1024 * 1024, max_records=4096, max_line=512 * 1024):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.max_bytes, self.max_records, self.max_line = max_bytes, max_records, max_line
        self.unusable = False
        self._signature = None
        with self._locked():
            self._scan()

    @contextmanager
    def _locked(self):
        lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        with lock_path.open("a+b") as handle:
            if handle.seek(0, 2) == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                yield
            finally:
                handle.seek(0)
                if os.name == "nt":
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle, fcntl.LOCK_UN)

    def _stat(self):
        if not self.path.exists():
            return None
        stat = self.path.stat()
        return stat.st_size, stat.st_mtime_ns, stat.st_ino

    def _scan(self):
        self._records, self._index = [], {}
        self.head, self.offset = ZERO, 0
        if self.path.exists():
            if self.path.stat().st_size > self.max_bytes:
                raise LedgerError("ledger byte budget exceeded")
            with self.path.open("rb") as handle:
                while True:
                    line = handle.readline(self.max_line + 1)
                    if not line:
                        break
                    prefix = f"offset={self.offset} prefix_head={self.head}"
                    if len(line) > self.max_line:
                        raise LedgerError("record byte budget exceeded " + prefix)
                    if not line.endswith(b"\n"):
                        raise TornTail("torn tail " + prefix)
                    try:
                        rec = strict_json(line)
                        if not isinstance(rec, dict):
                            raise ValueError("not object")
                        expected = dict(rec)
                        stored_hash = expected.pop("record_hash")
                        event = {"kind": rec["kind"], "payload": rec["payload"]}
                        if (rec["schema"] != "octopus-journal.v2"
                                or type(rec["seq"]) is not int
                                or rec["seq"] != len(self._records) + 1
                                or rec["prev_hash"] != self.head
                                or stored_hash != digest(expected)
                                or rec["event_hash"] != digest(event)
                                or not isinstance(rec["event_id"], str) or not rec["event_id"]
                                or rec["event_id"] in self._index):
                            raise ValueError("invalid chain/identity")
                    except (ValueError, KeyError, TypeError, UnicodeError) as exc:
                        raise LedgerError("corrupt record " + prefix) from exc
                    self._records.append(rec)
                    self._index[rec["event_id"]] = rec
                    self.head = stored_hash
                    self.offset += len(line)
                    if len(self._records) > self.max_records:
                        raise LedgerError("record count budget exceeded")
        self._signature = self._stat()

    def _refresh(self):
        if self.unusable:
            raise LedgerError("durability uncertain: reopen store before retry")
        if self._signature != self._stat():
            self._scan()

    @property
    def records(self):
        # Return a detached snapshot; consumers cannot mutate the journal cache.
        with self._locked():
            self._refresh()
            return strict_json(canonical(self._records))

    def append_record(self, kind, event_id, payload):
        if not isinstance(event_id, str) or not event_id or not isinstance(kind, str) or not kind:
            raise ValueError("kind and event_id required")
        event_hash = digest({"kind": kind, "payload": payload})
        # Freeze caller-owned mutable content.
        payload = strict_json(canonical(payload))
        with self._locked():
            self._refresh()
            existing = self._index.get(event_id)
            if existing:
                if existing["event_hash"] != event_hash:
                    raise LedgerError("event ID collision: " + event_id + " old=" +
                                      existing["event_hash"] + " new=" + event_hash)
                return self._receipt(existing, True)
            rec = {"schema": "octopus-journal.v2", "seq": len(self._records) + 1,
                   "kind": kind, "event_id": event_id, "event_hash": event_hash,
                   "prev_hash": self.head, "payload": payload}
            rec["record_hash"] = digest(rec)
            line = (canonical(rec) + "\n").encode("utf-8")
            if (len(line) > self.max_line or self.offset + len(line) > self.max_bytes
                    or len(self._records) >= self.max_records):
                raise LedgerError("ledger budget exhausted; no append")
            try:
                with self.path.open("ab", buffering=0) as handle:
                    remaining = memoryview(line)
                    while remaining:
                        count = handle.write(remaining)
                        if count is None or count <= 0:
                            raise OSError("short write without progress")
                        remaining = remaining[count:]
                    handle.flush()
                    os.fsync(handle.fileno())
            except BaseException:
                self.unusable = True
                raise
            self._records.append(rec)
            self._index[event_id] = rec
            self.head, self.offset = rec["record_hash"], self.offset + len(line)
            self._signature = self._stat()
            return self._receipt(rec, False)

    @staticmethod
    def _receipt(rec, duplicate):
        return {"ok": True, "duplicate": duplicate, "event_id": rec["event_id"],
                "seq": rec["seq"], "record_hash": rec["record_hash"],
                "event_hash": rec["event_hash"],
                "durability": "validated_existing_record" if duplicate else "fsync_returned"}

    def append(self, obs):
        receipt = self.append_record("observation", obs.observation_id, obs.to_dict())
        return dict(receipt, observation_id=obs.observation_id)

    def record_gap(self, beat, reason, decision_time):
        payload = {"kind": "GAP", "beat": beat, "reason": reason,
                   "decision_time": parse_dt(decision_time).isoformat(),
                   "note": "missing beat is not synthesized"}
        return self.append_record("gap", "gap-" + digest(payload), payload)

    def snapshot_latest(self, latest_path, *, beat_claim, historical):
        source = Path(latest_path)
        with source.open("rb") as handle:
            raw_bytes = handle.read(self.max_line + 1)
        if len(raw_bytes) > self.max_line:
            raise LedgerError("snapshot byte budget exceeded")
        raw = strict_json(raw_bytes)
        if not isinstance(raw, dict):
            raise LedgerError("snapshot object required")
        return {"source": str(source), "source_hash": digest(raw),
                "source_bytes_hash": hashlib.sha256(raw_bytes).hexdigest(),
                "beat_in_file": raw.get("beat"), "historical_claim": historical,
                "beat_claim": beat_claim, "can_prove_historical": False,
                "claim": "latest snapshot alone cannot prove an historical beat"}

    @staticmethod
    def rotation_policy():
        return {"auto_delete": False, "cap_mb": 8,
                "overflow": "explicit failure; archive/rotation requires owner decision"}
