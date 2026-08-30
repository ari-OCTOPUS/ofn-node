# -*- coding: utf-8 -*-
"""Capability lease — BRAIN issues a signed permit; executor stays inside it.

Implements the DA-4 lease subset: params hash binding, expiry, one-shot nonce,
cost/call caps. HMAC is the signature for P0 (Ed25519 owner-signing is TIER-2
and stays in `_ops/owner-signing/` — this module does not touch private keys).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Mapping

from .exceptions import LeaseError


def params_hash(params: Mapping[str, Any]) -> str:
    body = json.dumps(params, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


@dataclass
class CapabilityLease:
    lease_id: str
    capability: str
    cost_cap_cents: int
    max_calls: int
    network_allow: tuple[str, ...]
    expires_unix: float
    bound_params_hash: str
    nonce: str
    hmac: str
    used_calls: int = 0
    used_cents: int = 0
    burned: bool = False

    def remaining_cents(self) -> int:
        return self.cost_cap_cents - self.used_cents


class LeaseStore:
    def __init__(self, hmac_key: bytes) -> None:
        if not hmac_key:
            raise LeaseError("lease HMAC key required")
        self._key = hmac_key
        self._leases: dict[str, CapabilityLease] = {}
        self._nonces: set[str] = set()

    def _mac(self, fields: Mapping[str, Any]) -> str:
        body = json.dumps(fields, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hmac.new(self._key, body.encode("utf-8"), hashlib.sha256).hexdigest()

    def issue(
        self,
        *,
        capability: str,
        cost_cap_cents: int,
        max_calls: int,
        network_allow: tuple[str, ...],
        ttl_s: float,
        bound_params: Mapping[str, Any],
        now: float | None = None,
    ) -> CapabilityLease:
        if cost_cap_cents < 0 or max_calls < 1:
            raise LeaseError("invalid lease caps")
        nonce = uuid.uuid4().hex
        if nonce in self._nonces:
            raise LeaseError("nonce collision")
        ts = now if now is not None else time.time()
        lease_id = uuid.uuid4().hex
        bound = params_hash(bound_params)
        expires = ts + float(ttl_s)
        core = {
            "lease_id": lease_id,
            "capability": capability,
            "cost_cap_cents": int(cost_cap_cents),
            "max_calls": int(max_calls),
            "network_allow": list(network_allow),
            "expires_unix": expires,
            "bound_params_hash": bound,
            "nonce": nonce,
        }
        lease = CapabilityLease(
            lease_id=lease_id,
            capability=capability,
            cost_cap_cents=int(cost_cap_cents),
            max_calls=int(max_calls),
            network_allow=tuple(network_allow),
            expires_unix=expires,
            bound_params_hash=bound,
            nonce=nonce,
            hmac=self._mac(core),
        )
        self._leases[lease.lease_id] = lease
        self._nonces.add(nonce)
        return lease

    def _verify_mac(self, lease: CapabilityLease) -> None:
        core = {
            "lease_id": lease.lease_id,
            "capability": lease.capability,
            "cost_cap_cents": lease.cost_cap_cents,
            "max_calls": lease.max_calls,
            "network_allow": list(lease.network_allow),
            "expires_unix": lease.expires_unix,
            "bound_params_hash": lease.bound_params_hash,
            "nonce": lease.nonce,
        }
        expect = self._mac(core)
        if not hmac.compare_digest(expect, lease.hmac):
            raise LeaseError("lease hmac invalid")

    def consume(
        self,
        lease: CapabilityLease,
        *,
        params: Mapping[str, Any],
        cost_cents: int,
        now: float | None = None,
    ) -> CapabilityLease:
        stored = self._leases.get(lease.lease_id)
        if stored is None:
            raise LeaseError("unknown lease")
        self._verify_mac(stored)
        ts = now if now is not None else time.time()
        if stored.burned:
            raise LeaseError("lease nonce already burned")
        if ts > stored.expires_unix:
            stored.burned = True
            raise LeaseError("lease expired")
        if params_hash(params) != stored.bound_params_hash:
            raise LeaseError("params hash mismatch — client tamper")
        if stored.used_calls + 1 > stored.max_calls:
            stored.burned = True
            raise LeaseError("lease call cap exhausted")
        if cost_cents < 0:
            raise LeaseError("negative cost")
        if stored.used_cents + cost_cents > stored.cost_cap_cents:
            raise LeaseError("lease cost cap exhausted")
        stored.used_calls += 1
        stored.used_cents += int(cost_cents)
        if stored.used_calls >= stored.max_calls:
            stored.burned = True
        return stored
