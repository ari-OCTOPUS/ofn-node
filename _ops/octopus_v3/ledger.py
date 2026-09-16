# -*- coding: utf-8 -*-
"""Hash-chained INTENT ledger (INV-5 overlay).

stdlib-only. Fail-closed on I/O. O_APPEND + fsync. HMAC optional.
Does not replace the genome ledger or NBB-CP events.py.

Process-boundary (separate UID / O_APPEND writer) is documented, not faked:
this module never imports an executor. On Win32 we cannot fork a second UID;
the testable contract is: no execute() in this file, and write failure aborts.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from pathlib import Path
from typing import Any, Mapping

from .exceptions import LedgerClosed, LedgerIntegrityError

GENESIS_HASH = "0" * 64
_LOCK_STALE_S = 30.0


def _canonical(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_hash(seq: int, ts: str, kind: str, payload: Mapping[str, Any], prev_hash: str) -> str:
    body = f"{seq}|{ts}|{kind}|{_canonical(payload)}|{prev_hash}"
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def compute_hmac(digest: str, key: bytes) -> str:
    return hmac.new(key, digest.encode("utf-8"), hashlib.sha256).hexdigest()


class _Lock:
    def __init__(self, path: Path, stale_s: float = _LOCK_STALE_S) -> None:
        self.path = path
        self.stale = stale_s
        self._fd: int | None = None

    def __enter__(self) -> "_Lock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(50):
            try:
                self._fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                return self
            except FileExistsError:
                try:
                    if time.time() - os.path.getmtime(self.path) > self.stale:
                        os.unlink(self.path)
                        continue
                except OSError:
                    pass
                time.sleep(0.05)
        raise LedgerClosed(f"lock busy: {self.path}")

    def __exit__(self, *exc: object) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        try:
            os.unlink(self.path)
        except OSError:
            pass


class IntentLedger:
    """Append-only INTENT/RESULT/KILL events. Callers must record INTENT first."""

    def __init__(self, path: Path, hmac_key: bytes | None = None) -> None:
        self.path = Path(path)
        self.tip_path = self.path.with_suffix(self.path.suffix + ".tip.json")
        self.lock_path = Path(str(self.path) + ".lock")
        self.hmac_key = hmac_key

    def _append_line(self, line: str) -> None:
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        if hasattr(os, "O_BINARY"):
            flags |= os.O_BINARY
        try:
            fd = os.open(str(self.path), flags)
        except OSError as exc:
            raise LedgerClosed(f"open failed: {exc}") from exc
        try:
            os.write(fd, (line + "\n").encode("utf-8"))
            os.fsync(fd)
        except OSError as exc:
            raise LedgerClosed(f"write/fsync failed: {exc}") from exc
        finally:
            os.close(fd)

    def _read_tip(self) -> tuple[int, str]:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return -1, GENESIS_HASH
        last: dict[str, Any] | None = None
        try:
            with self.path.open("r", encoding="utf-8") as fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    last = json.loads(raw)
        except (OSError, ValueError) as exc:
            raise LedgerClosed(f"ledger unreadable: {exc}") from exc
        if last is None:
            return -1, GENESIS_HASH
        return int(last["seq"]), str(last["hash"])

    def _write_tip(self, seq: int, digest: str) -> None:
        payload = json.dumps({"seq": seq, "hash": digest}, separators=(",", ":"))
        tmp = self.tip_path.with_suffix(self.tip_path.suffix + ".tmp")
        try:
            tmp.write_text(payload, encoding="utf-8")
            os.replace(tmp, self.tip_path)
        except OSError as exc:
            raise LedgerClosed(f"tip write failed: {exc}") from exc

    def append(self, kind: str, payload: Mapping[str, Any], ts: str | None = None) -> dict[str, Any]:
        """Record one event. Raises LedgerClosed on any disk failure — caller must not execute."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record_ts = ts or time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        with _Lock(self.lock_path):
            prev_seq, prev_hash = self._read_tip()
            seq = prev_seq + 1
            digest = compute_hash(seq, record_ts, kind, payload, prev_hash)
            mac = compute_hmac(digest, self.hmac_key) if self.hmac_key else ""
            rec = {
                "seq": seq,
                "ts": record_ts,
                "kind": kind,
                "payload": dict(payload),
                "prev_hash": prev_hash,
                "hash": digest,
                "hmac": mac,
            }
            try:
                self._append_line(_canonical(rec))
                self._write_tip(seq, digest)
            except LedgerClosed:
                raise
            except OSError as exc:
                raise LedgerClosed(str(exc)) from exc
            return rec

    def verify_integrity(self) -> int:
        """Return event count. Raise LedgerIntegrityError on the first break."""
        if not self.path.exists():
            return 0
        prev: dict[str, Any] | None = None
        n = 0
        try:
            lines = self.path.read_text("utf-8").splitlines()
        except OSError as exc:
            raise LedgerClosed(str(exc)) from exc
        for i, raw in enumerate(lines):
            if not raw.strip():
                continue
            try:
                rec = json.loads(raw)
            except ValueError as exc:
                raise LedgerIntegrityError(f"torn/json at line {i + 1}: {exc}") from exc
            expected_seq = 0 if prev is None else int(prev["seq"]) + 1
            if int(rec["seq"]) != expected_seq:
                raise LedgerIntegrityError(f"seq gap at {rec.get('seq')}, expected {expected_seq}")
            expected_prev = GENESIS_HASH if prev is None else prev["hash"]
            if rec["prev_hash"] != expected_prev:
                raise LedgerIntegrityError(f"prev_hash mismatch at seq {rec['seq']}")
            recomputed = compute_hash(
                int(rec["seq"]), rec["ts"], rec["kind"], rec["payload"], rec["prev_hash"]
            )
            if recomputed != rec["hash"]:
                raise LedgerIntegrityError(f"hash forged at seq {rec['seq']}")
            if self.hmac_key:
                expect_mac = compute_hmac(recomputed, self.hmac_key)
                if not hmac.compare_digest(expect_mac, rec.get("hmac") or ""):
                    raise LedgerIntegrityError(f"hmac mismatch at seq {rec['seq']}")
            prev = rec
            n += 1
        return n
