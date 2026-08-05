"""Telegram channel adapter — Layer A.

Telegram channels are the partner-owned, algorithm-immune broadcast surface:
the one place a feet-content account can reach its audience without a
platform deciding today is the day it gets shadowbanned. That immunity is
exactly why the adapter is still dry-run by default — the *capability* to
broadcast to a channel is the capability to spam a captive audience, and
that capability waits for the OwnerRelease switch like everything else.

The real publish path (Bot API `sendMessage` / `sendPhoto`) is not
implemented here yet. It belongs in M5, behind the release switch, with
the bot token read from the secrets env at call time — never stored in
the adapter, never logged.
"""

from __future__ import annotations

from ofn.adapters.platforms.base import (
    PublishRequest, PublishResult, RULE_DRY_RUN, RULE_WIRE_CLOSED,
)


class TelegramChannelAdapter:
    """Dry-run now; real publish wired in M5 behind OwnerRelease."""

    platform = "telegram_channel"

    def __init__(self, channel_id: str):
        # The channel id is not secret (it is in the channel's URL); the bot
        # token is, and is not held here. It is read from the env at the
        # moment of a real publish, in the M5 wiring.
        self.channel_id = channel_id

    def publish(self, req: PublishRequest) -> PublishResult:
        if req.dry_run:
            return PublishResult(True, self.platform, req.idempotency_key,
                                 rule=RULE_DRY_RUN)
        # A closed WIRE flag is a feature, not a crash. The outbox worker
        # must stay up; a refused publish becomes a held item, not a dead
        # process.
        return PublishResult(False, self.platform, req.idempotency_key,
                             rule=RULE_WIRE_CLOSED)
