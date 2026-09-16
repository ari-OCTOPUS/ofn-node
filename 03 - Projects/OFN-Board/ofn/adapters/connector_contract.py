"""Connector contract: the interface every marketing platform adapter must satisfy.

No real vendor is wired yet. This module defines the shape so that:
  * a fake connector can be built immediately for testing;
  * when the official docs arrive, the real adapter drops in without changing
    the inbox, the ledger, or the rate limiter.

Every method receives a TenantScope and therefore cannot touch another tenant's
state — the same isolation rule the rest of OFN follows.

No method sends anything outbound. A connector *normalises* an inbound payload
and writes it to the inbox; the outbox decides what goes out. The separation is
structural, not a convention.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from ..kernel.tenancy import TenantScope


@dataclass(frozen=True)
class NormalisedEvent:
    """A vendor payload reduced to a vendor-neutral shape.

    The connector fills these fields; the inbox stores them. Anything the
    connector cannot map is left as empty string / zero.

    NO raw vendor payload (O3): the inbox and ledger must never receive the
    original bytes — only the hash and the safe normalised fields below.
    """
    event_type: str            # e.g. "lead", "conversion", "unsubscribe"
    vendor: str                # e.g. "mailchimp", "instagram"
    vendor_event_id: str       # the vendor's own id (for idempotency)
    body_sha256: str           # hash of the raw body (the only trace kept)
    tenant: str                # resolved tenant name
    occurred_at_epoch: int     # when the vendor says it happened
    correlation_id: str        # propagated from X-Correlation-ID
    payload: Mapping[str, str] = ()  # safe normalised key-value pairs


@dataclass(frozen=True)
class ConnectorHealth:
    """Snapshot of a connector's state, for the owner's panel."""
    connector_id: str
    vendor: str
    healthy: bool
    last_inbound_at: str = ""     # ISO timestamp or empty
    last_error: str = ""
    inbox_depth: int = 0
    processed_total: int = 0


class Connector:
    """Base class for marketing platform connectors.

    Subclass this per vendor. Every method has a safe default (return empty /
    False / zero) so an unimplemented connector simply does nothing rather than
    crashing the inbox loop.
    """

    def __init__(self, connector_id: str, vendor: str) -> None:
        self.connector_id = connector_id
        self.vendor = vendor

    def identify(self) -> str:
        return self.connector_id

    def vendor_name(self) -> str:
        return self.vendor

    def verify(self, body: bytes, headers: Mapping[str, str]):
        """Verify a webhook signature. Default: fail closed.

        A connector that does not implement verification must NOT accept
        payloads — an unsigned webhook is a rejected webhook (O3).
        """
        from .webhook_verify import VerifyResult
        return VerifyResult(False, "connector has no verifier")

    def normalise(self, scope: TenantScope, raw_body: bytes,
                  headers: Mapping[str, str],
                  correlation_id: str) -> NormalisedEvent | None:
        """Convert a raw webhook payload into a NormalisedEvent.

        Returns None if the payload is not for this connector or cannot be
        parsed. The caller (inbox loop) silently drops None results.
        """
        return None  # pragma: no cover

    def health(self) -> ConnectorHealth:
        return ConnectorHealth(
            connector_id=self.connector_id,
            vendor=self.vendor,
            healthy=True,
        )


class FakeConnector(Connector):
    """A test connector that accepts any payload and normalises it.

    Vendor is "fake". The vendor_event_id is a hash of the body so repeated
    payloads are idempotent in the inbox. Tests only — never wired in
    production (O3).
    """
    import hashlib as _hl

    def __init__(self) -> None:
        super().__init__("fake", "fake")

    def verify(self, body: bytes, headers: Mapping[str, str]):
        """Fake connector signs nothing; verification is a no-op (tests)."""
        from .webhook_verify import VerifyResult
        return VerifyResult(True)

    def normalise(self, scope: TenantScope, raw_body: bytes,
                  headers: Mapping[str, str],
                  correlation_id: str) -> NormalisedEvent | None:
        import hashlib
        vid = hashlib.sha256(raw_body).hexdigest()[:16]
        return NormalisedEvent(
            event_type="fake",
            vendor="fake",
            vendor_event_id=vid,
            body_sha256=hashlib.sha256(raw_body).hexdigest(),
            tenant=scope.tenant.value,
            occurred_at_epoch=0,
            correlation_id=correlation_id,
            payload={},
        )


def connector_registry(*connectors: Connector) -> Mapping[str, Connector]:
    """Build a lookup map from connector_id to Connector."""
    return {c.identify(): c for c in connectors}
