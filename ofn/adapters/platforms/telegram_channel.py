"""Telegram channel adapter — Layer A, real publish behind the release switch.

A channel is the partner-owned broadcast surface. The capability to
broadcast is the capability to spam a captive audience, so the real
publish path is gated by `require_release_context()` at the CALL SITE
(node wiring), never inside this adapter. The adapter itself only knows
how to talk to the Bot API.

The bot token is read from config at call time (secrets env) — never
stored in the adapter, never logged. `dry_run=True` in the request means
this returns the dry-run result without touching the network.

Safety envelope (O11): one tenant, one platform, one item cap, second
confirmation, dry-run diff — all enforced by the caller before publish().
"""

from __future__ import annotations

import json
import urllib.request

from ofn.adapters.platforms.base import (
    PublishRequest, PublishResult, RULE_DRY_RUN, RULE_NOT_IMPLEMENTED,
)


class TelegramChannelAdapter:
    """Publish caption + optional photo to a Telegram channel."""

    platform = "telegram_channel"

    def __init__(self, channel_id: str):
        # The channel id is not secret (it is in the channel's URL); the bot
        # token is, and is passed per-call from config, never held here.
        self.channel_id = channel_id

    def publish(self, req: PublishRequest,
                token: str = "") -> PublishResult:
        if req.dry_run:
            return PublishResult(True, self.platform, req.idempotency_key,
                                 rule=RULE_DRY_RUN)
        if not token:
            return PublishResult(False, self.platform, req.idempotency_key,
                                 rule="telegram:no-token")
        # sendMessage needs a chat id: a numeric id (-100...) or a public
        # @username. An invite link (t.me/+...) is NOT usable by the Bot
        # API — refuse loudly instead of sending it as chat_id.
        cid = str(self.channel_id or "").strip()
        if not cid or cid.startswith("t.me/") or "/" in cid:
            return PublishResult(False, self.platform, req.idempotency_key,
                                 rule="telegram:invite-link-not-usable")
        # sendMessage for text; media_refs are local paths and are NOT sent
        # over the wire here (photo upload needs the bytes; the caller sends
        # them explicitly). Text-only broadcast is the minimal real send.
        # Telegram Bot API accepts form-encoded data (more reliable than JSON
        # for simple text sends).
        import urllib.parse
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = urllib.parse.urlencode({
            "chat_id": cid,
            "text": req.caption,
            "disable_web_page_preview": "true",
        }).encode("utf-8")
        try:
            with urllib.request.urlopen(url, data=payload, timeout=15) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            return PublishResult(False, self.platform, req.idempotency_key,
                                 rule=f"telegram:send-failed:{exc}")
        if not body.get("ok"):
            return PublishResult(False, self.platform, req.idempotency_key,
                                 rule="telegram:api-refused")
        external_id = str((body.get("result") or {}).get("message_id", ""))
        return PublishResult(True, self.platform, req.idempotency_key,
                             external_id=external_id or None)
