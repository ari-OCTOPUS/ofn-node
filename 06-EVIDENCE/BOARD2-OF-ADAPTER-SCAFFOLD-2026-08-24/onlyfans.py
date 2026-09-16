"""OnlyFans adapter — SCAFFOLD only (2026-08-24).

Board2 / marketing scaffold. Live publish is forbidden until a second
explicit owner GO. Credentials are never stored on this class; env keys
are documented only (OFN_ONLYFANS_*).

Defaults:
- PublishRequest.dry_run is True (base contract)
- Even if dry_run=False, live path requires OFN_ONLYFANS_LIVE=1 AND
  credentials; the real HTTP client is not wired yet (scaffold returns
  RULE_NOT_IMPLEMENTED).

Do not invent captions. Do not auto-enqueue. telegram_channel remains
the live caption-gated path.
"""

from __future__ import annotations

import os

from ofn.adapters.platforms.base import (
    PublishRequest,
    PublishResult,
    RULE_DRY_RUN,
    RULE_NOT_IMPLEMENTED,
    RULE_WIRE_CLOSED,
)

# Documented env placeholders (do not invent values; leave unset until GO):
#   OFN_ONLYFANS_LIVE=1          — second owner GO required to even attempt live
#   OFN_ONLYFANS_SESSION_COOKIE  — vault/secrets only, never in chat / node.env
#   OFN_ONLYFANS_USER_AGENT      — optional
#   OFN_ONLYFANS_ACCOUNT_ID      — optional account selector

__all_platform__ = "onlyfans"


class OnlyFansAdapter:
    """Scaffold publisher for OnlyFans. Dry-run by default; live not implemented."""

    platform = "onlyfans"

    def __init__(self, account_id: str = ""):
        self.account_id = (
            account_id or os.environ.get("OFN_ONLYFANS_ACCOUNT_ID") or ""
        ).strip()

    def publish(self, req: PublishRequest) -> PublishResult:
        if req.dry_run:
            return PublishResult(
                True,
                self.platform,
                req.idempotency_key,
                rule=RULE_DRY_RUN,
            )

        live = (os.environ.get("OFN_ONLYFANS_LIVE") or "").strip() == "1"
        if not live:
            # Closed gate is a feature, not a crash (same shape as bluesky/shopify).
            return PublishResult(
                False,
                self.platform,
                req.idempotency_key,
                rule=RULE_WIRE_CLOSED,
            )

        cookie = (os.environ.get("OFN_ONLYFANS_SESSION_COOKIE") or "").strip()
        if not cookie:
            return PublishResult(
                False,
                self.platform,
                req.idempotency_key,
                rule="onlyfans:no-credentials",
            )

        # Scaffold: no HTTP client. Second owner GO still required to wire real post.
        return PublishResult(
            False,
            self.platform,
            req.idempotency_key,
            rule=RULE_NOT_IMPLEMENTED,
        )
