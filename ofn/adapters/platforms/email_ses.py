"""Email adapter (Amazon SES) — Layer A, and the only owned channel.

Email is the one surface no platform algorithm can take away: the list is
owned, the relationship is direct, and a shadowban elsewhere does not
silence it. That makes it the most important *strategic* channel, and the
adapter treats it accordingly — dry-run by default, real send wired in M5.

Deliverability is a real concern the adapter does not solve here: SPF,
DKIM, and DMARC are configured at the domain (not in code), and a cold
list will land in spam regardless of how correct the send is. The adapter
assumes a warmed, opted-in list; a cold list is a configuration error the
first bounce will surface, not something to silently absorb.
"""

from __future__ import annotations

from ofn.adapters.platforms.base import (
    PublishRequest, PublishResult, RULE_DRY_RUN, RULE_WIRE_CLOSED,
)


class EmailSesAdapter:
    """Dry-run now; real send wired in M5 behind OwnerRelease."""

    platform = "email_ses"

    def __init__(self, from_address: str, list_id: str):
        # The from-address and list id are operational config; the SES
        # access key / secret are not held here.
        self.from_address = from_address
        self.list_id = list_id

    def publish(self, req: PublishRequest) -> PublishResult:
        if req.dry_run:
            return PublishResult(True, self.platform, req.idempotency_key,
                             rule=RULE_DRY_RUN)
        # A closed WIRE flag is a feature, not a crash.
        return PublishResult(False, self.platform, req.idempotency_key,
                             rule=RULE_WIRE_CLOSED)
