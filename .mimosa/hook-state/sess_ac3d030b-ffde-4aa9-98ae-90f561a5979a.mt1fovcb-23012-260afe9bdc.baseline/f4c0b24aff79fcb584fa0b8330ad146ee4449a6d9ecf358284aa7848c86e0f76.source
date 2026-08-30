"""Platform adapter contract — the shape every publisher implements.

A platform adapter is the *only* place that knows how to talk to one
specific outside service. Everything upstream of it (consent, the release
switch, the platform matrix, the outbox) is brand-agnostic; everything
downstream of this interface is brand-specific.

All adapters ship as dry-run by default. `PublishRequest.dry_run` is True
unless the caller explicitly sets it False, and no caller in the current
codebase ever does — real publishing is behind the OwnerRelease switch
(M5) and is not wired until then. An adapter that publishes when
`dry_run=True` is not a feature, it is a bug, and a dangerous one.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PublishRequest:
    platform: str
    idempotency_key: str
    caption: str
    media_refs: tuple[str, ...] = ()
    hashtags: tuple[str, ...] = ()
    dry_run: bool = True          # the default that keeps us safe
    adult_label: bool = False


@dataclass(frozen=True)
class PublishResult:
    ok: bool
    platform: str
    idempotency_key: str
    external_id: str | None = None    # the remote post id, on a real publish
    rule: str = "adapter:ok"


RULE_DRY_RUN = "adapter:dry-run"
RULE_WIRE_CLOSED = "wire:disabled"               # a closed gate, not a crash
RULE_NOT_IMPLEMENTED = "adapter:real-publish-not-implemented"


class PlatformAdapter(Protocol):
    """The contract. Adapters may carry their own config; this is the shape."""

    platform: str

    def publish(self, req: PublishRequest) -> PublishResult: ...
