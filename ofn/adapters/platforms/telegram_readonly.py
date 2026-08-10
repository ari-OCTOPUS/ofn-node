"""Telegram Bot API — read-only skeleton adapter (phase M).

This adapter can READ: getMe, getWebhookInfo, getChatMemberCount, and the
node's own bot identity. It CANNOT publish — publishing stays behind the
OwnerRelease switch and requires Ari's explicit decision, exactly like
every other adapter in this package.

The token is provided by the caller (from config), never read from env
inside this module, never logged. dry_run is always True here.

No real vendor is connected yet — this is the skeleton the real wiring
will hang on once Ari picks the vendor (see
docs/architecture/VENDOR-EVALUATION.md).
"""

from __future__ import annotations

import json
import urllib.request

from .base import (
    PlatformAdapter, PublishRequest, PublishResult,
    RULE_NOT_IMPLEMENTED, RULE_WIRE_CLOSED,
)

__all_platform__ = "telegram_channel"


class TelegramReadOnlyAdapter:
    """Read-only Telegram Bot API surface.

    `platform` matches the existing dry-run telegram_channel adapter, so
    the two are the same vendor with two scopes: read here, publish there
    (publish still dry-run).
    """

    platform = "telegram"

    def __init__(self, token: str = "") -> None:
        # Caller-provided token (config), never read from env here.
        self._token = token

    def _call(self, method: str) -> dict:
        """GET-style Bot API call. Returns the JSON result."""
        if not self._token:
            return {"ok": False, "error": "no token configured"}
        url = f"https://api.telegram.org/bot{self._token}/{method}"
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def get_me(self) -> dict:
        """The bot's own identity: username, id, can_join_groups.

        Pure read — this is the only call that needs no chat context and
        proves the token is alive.
        """
        return self._call("getMe")

    def get_webhook_info(self) -> dict:
        """What URL the bot currently receives updates on (read-only)."""
        return self._call("getWebhookInfo")

    def health(self) -> dict:
        """Adapter-level health for the owner's panel."""
        me = self.get_me()
        if not me.get("ok"):
            return {"ok": False, "healthy": False,
                    "why": "token invalid or network unreachable"}
        return {"ok": True, "healthy": True,
                "bot": (me.get("result") or {}).get("username")}

    # Publishing is structurally absent here — same rule as the rest of
    # this package. A publish() that sends for real would be a bug.
    def publish(self, req: PublishRequest) -> PublishResult:
        return PublishResult(False, self.platform, req.idempotency_key,
                             rule=RULE_NOT_IMPLEMENTED)
