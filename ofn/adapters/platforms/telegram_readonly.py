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
import urllib.parse
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

    def __init__(self, token: str = "", channel_id: str = "") -> None:
        # Caller-provided token (config), never read from env here.
        # channel_id: the broadcast channel the node publishes to; the pilot
        # may read its member count with the same bot that publishes.
        self._token = token
        self._channel_id = channel_id

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

    def get_chat_member_count(self, chat_id: str) -> dict:
        """How many members the bot can see in a chat/channel (read-only).

        Needs a chat context; the bot must be a member (or admin) of the
        channel. Fail-closed: any error is reported, never guessed.
        """
        return self._call(
            "getChatMemberCount?" + urllib.parse.urlencode(
                {"chat_id": chat_id}))

    def read_page(self, cursor: str = "", limit: int = 20) -> dict:
        """One bounded read-only page, for the O10 pilot harness.

        Reads the bot's identity, its webhook state, and — when a channel
        id is configured on the adapter — the channel's member count. Each
        is a separate Bot API call; the page is the collection of their
        results. `cursor` is accepted for pilot compatibility; these reads
        have no pagination, so the next cursor is always empty.

        Pure read, no state mutation, no publish. A page that fails reads
        what it can and says so per-item — the pilot records receipts from
        the items that answered, exactly like a real vendor page.
        """
        items: list[dict] = []
        me = self.get_me()
        if me.get("ok"):
            r = me.get("result") or {}
            items.append({"id": "me", "type": "bot_identity",
                          "username": r.get("username", ""),
                          "can_join_groups": r.get("can_join_groups")})
        hook = self.get_webhook_info()
        if hook.get("ok"):
            r = hook.get("result") or {}
            items.append({"id": "webhook", "type": "webhook_info",
                          "url": r.get("url", ""),
                          "pending": r.get("pending_update_count", 0)})
        if self._channel_id:
            count = self.get_chat_member_count(self._channel_id)
            if count.get("ok"):
                # getChatMemberCount returns the count directly in
                # `result` (an int), not nested in an object.
                n = count.get("result")
                items.append({"id": "channel", "type": "member_count",
                              "chat": self._channel_id,
                              "count": n if isinstance(n, int) else 0})
        return {"items": items[:limit], "next_cursor": ""}

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
