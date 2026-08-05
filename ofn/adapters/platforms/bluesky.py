"""Bluesky adapter — Layer A.

Bluesky's atproto is the most permissive major surface in 2026 for labeled
adult content, which makes it a natural Layer-A home for the
general-sensitivity slice of this account. Permissiveness is not a licence:
the adapter still ships dry-run, and the real publish path (a session
created from an app password, then `com.atproto.repo.createRecord` with a
post record) waits for M5 and the OwnerRelease switch.

The app password is a secret and is never held in the adapter. It is read
from the secrets env at the moment of a real publish.
"""

from __future__ import annotations

from ofn.adapters.platforms.base import (
    PublishRequest, PublishResult, RULE_DRY_RUN,
)


class BlueskyAdapter:
    """Dry-run now; real publish wired in M5 behind OwnerRelease."""

    platform = "bsky"

    def __init__(self, handle: str):
        # The handle is public; the app password / session token is not,
        # and is not held here.
        self.handle = handle

    def publish(self, req: PublishRequest) -> PublishResult:
        if req.dry_run:
            return PublishResult(True, self.platform, req.idempotency_key,
                                 rule=RULE_DRY_RUN)
        raise NotImplementedError(
            "real Bluesky publish is wired in M5 behind OwnerRelease; "
            "the WIRE flag is off")
