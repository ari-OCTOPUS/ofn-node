# -*- coding: utf-8 -*-
"""Beat Ownership Lease — HMAC prototype (NOT the fencing SoT).

Fencing SoT is `_ops/runtime/beat_lease.py`: monotonic clock, safety margin,
vacate-not-delete, freeze file, NATS KV backend. This overlay still uses
HMAC on a JSON file and does **not** increment a fencing token on renew,
so a paused process can write after expiry steal. Do not wire this module.

Keep tests. organism.py / chrono.py are NOT imported.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .exceptions import DualBeatDenied, LedgerClosed

TTL_S = 60.0
RENEW_AFTER_S = 20.0
ENFORCE_ENV = "OCTOPUS_BEAT_LEASE"
HOLDER_ENV = "OCTOPUS_BEAT_HOLDER"
ROLE_ENV = "OCTOPUS_BEAT_ROLE"
HMAC_ENV = "OCTOPUS_BEAT_LEASE_HMAC"
ROLES_THAT_MAY_ACQUIRE = frozenset({"laptop", "arm1"})
SHADOW_ROLE = "shadow"
_LOCK_STALE_S = 5.0
_CORE_KEYS = ("holder_id", "role", "generation", "expires_unix", "nonce")


def enforce_on() -> bool:
    return str(os.environ.get(ENFORCE_ENV, "0")).strip().lower() in ("1", "true", "yes", "on")


def _canonical(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class _Lock:
    def __init__(self, path: Path, stale_s: float = _LOCK_STALE_S) -> None:
        self.path = path
        self.stale = stale_s
        self._fd: int | None = None

    def __enter__(self) -> "_Lock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(80):
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
                time.sleep(0.025)
        raise LedgerClosed(f"beat-lease lock busy: {self.path}")

    def __exit__(self, *exc: object) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        try:
            os.unlink(self.path)
        except OSError:
            pass


@dataclass(frozen=True)
class BeatLease:
    holder_id: str
    role: str
    generation: int
    expires_unix: float
    nonce: str
    hmac: str

    def alive(self, now: float) -> bool:
        return now < self.expires_unix


class BeatOwnership:
    """Single-writer beat permit. Tests inject path + key + clock."""

    def __init__(self, path: Path, hmac_key: bytes) -> None:
        if not hmac_key:
            raise DualBeatDenied("beat-lease HMAC key required")
        self.path = Path(path)
        self.lock_path = Path(str(self.path) + ".lock")
        self._key = hmac_key

    def _mac(self, core: Mapping[str, Any]) -> str:
        body = _canonical({k: core[k] for k in _CORE_KEYS})
        return hmac.new(self._key, body.encode("utf-8"), hashlib.sha256).hexdigest()

    def _make(self, core: Mapping[str, Any]) -> BeatLease:
        return BeatLease(
            holder_id=str(core["holder_id"]),
            role=str(core["role"]),
            generation=int(core["generation"]),
            expires_unix=float(core["expires_unix"]),
            nonce=str(core["nonce"]),
            hmac=self._mac(core),
        )

    def _dump(self, lease: BeatLease) -> None:
        rec = {
            "holder_id": lease.holder_id,
            "role": lease.role,
            "generation": lease.generation,
            "expires_unix": lease.expires_unix,
            "nonce": lease.nonce,
            "hmac": lease.hmac,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            tmp.write_text(_canonical(rec) + "\n", encoding="utf-8")
            with tmp.open("ab") as fh:
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, self.path)
        except OSError as exc:
            raise LedgerClosed(f"beat-lease write failed: {exc}") from exc

    def _load_unlocked(self) -> BeatLease | None:
        if not self.path.exists():
            return None
        try:
            rec = json.loads(self.path.read_text("utf-8"))
        except (OSError, ValueError) as exc:
            raise DualBeatDenied(f"beat-lease unreadable: {exc}") from exc
        try:
            core = {k: rec[k] for k in _CORE_KEYS}
        except KeyError as exc:
            raise DualBeatDenied(f"beat-lease missing field: {exc}") from exc
        expect = self._mac(core)
        if not hmac.compare_digest(expect, str(rec.get("hmac") or "")):
            raise DualBeatDenied("beat-lease hmac mismatch — refuse steal")
        return BeatLease(
            holder_id=str(core["holder_id"]),
            role=str(core["role"]),
            generation=int(core["generation"]),
            expires_unix=float(core["expires_unix"]),
            nonce=str(core["nonce"]),
            hmac=expect,
        )

    def snapshot(self) -> BeatLease | None:
        with _Lock(self.lock_path):
            return self._load_unlocked()

    def _write_new(self, holder_id: str, role: str, generation: int, now: float) -> BeatLease:
        core = {
            "holder_id": holder_id,
            "role": role,
            "generation": generation,
            "expires_unix": now + TTL_S,
            "nonce": uuid.uuid4().hex,
        }
        lease = self._make(core)
        self._dump(lease)
        return lease

    def acquire(self, holder_id: str, role: str, *, now: float | None = None) -> BeatLease:
        if role not in ROLES_THAT_MAY_ACQUIRE:
            raise DualBeatDenied(f"role {role!r} must not acquire the beat")
        if not holder_id.strip():
            raise DualBeatDenied("holder_id empty")
        ts = time.time() if now is None else now
        with _Lock(self.lock_path):
            cur = self._load_unlocked()
            if cur is not None and cur.alive(ts):
                if cur.holder_id == holder_id and cur.role == role:
                    return self._renew_unlocked(cur, ts)
                raise DualBeatDenied(
                    f"beat held by {cur.role}:{cur.holder_id} gen={cur.generation} until {cur.expires_unix}"
                )
            gen = 0 if cur is None else cur.generation + 1
            return self._write_new(holder_id, role, gen, ts)

    def _renew_unlocked(self, cur: BeatLease, now: float) -> BeatLease:
        core = {
            "holder_id": cur.holder_id,
            "role": cur.role,
            "generation": cur.generation,
            "expires_unix": now + TTL_S,
            "nonce": cur.nonce,
        }
        lease = self._make(core)
        self._dump(lease)
        return lease

    def renew(self, holder_id: str, *, now: float | None = None) -> BeatLease:
        ts = time.time() if now is None else now
        with _Lock(self.lock_path):
            cur = self._load_unlocked()
            if cur is None or not cur.alive(ts) or cur.holder_id != holder_id:
                raise DualBeatDenied("renew requires a living lease we hold")
            return self._renew_unlocked(cur, ts)

    def release(self, holder_id: str, *, now: float | None = None) -> None:
        ts = time.time() if now is None else now
        with _Lock(self.lock_path):
            cur = self._load_unlocked()
            if cur is None:
                return
            if cur.holder_id != holder_id:
                raise DualBeatDenied("cannot release another holder's beat")
            # Expire immediately; generation stays so a late packet cannot resurrect.
            core = {
                "holder_id": holder_id,
                "role": cur.role,
                "generation": cur.generation,
                "expires_unix": ts - 1.0,
                "nonce": cur.nonce,
            }
            self._dump(self._make(core))

    def may_beat(self, holder_id: str, *, now: float | None = None) -> bool:
        ts = time.time() if now is None else now
        with _Lock(self.lock_path):
            cur = self._load_unlocked()
        return bool(cur is not None and cur.holder_id == holder_id and cur.alive(ts))


def beat_allowed(
    *,
    path: Path | None = None,
    hmac_key: bytes | None = None,
    holder_id: str | None = None,
    role: str | None = None,
    now: float | None = None,
) -> bool:
    """Hot-path helper. Flag off → True (today's laptop unchanged). Flag on → lease or deny."""
    if not enforce_on():
        return True
    role = (role if role is not None else os.environ.get(ROLE_ENV, "laptop")).strip().lower()
    if role == SHADOW_ROLE:
        return False
    holder = (holder_id if holder_id is not None else os.environ.get(HOLDER_ENV, "")).strip()
    if not holder:
        return False
    key = hmac_key if hmac_key is not None else (os.environ.get(HMAC_ENV) or "").encode("utf-8")
    if not key:
        return False
    lease_path = path or Path(os.environ.get(
        "OCTOPUS_BEAT_LEASE_PATH",
        r"F:\backup\_ops\state\beat-ownership-lease.json",
    ))
    try:
        return BeatOwnership(lease_path, key).may_beat(holder, now=now)
    except (DualBeatDenied, LedgerClosed):
        return False
