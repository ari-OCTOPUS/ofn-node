"""Phase M — vendor skeleton adapter (read-only Telegram).

Tests the read-only adapter against a mocked Bot API: the adapter reads
identity/webhook info without ever touching a real network or token, and
publishing is structurally absent (returns RULE_NOT_IMPLEMENTED).
"""

from __future__ import annotations

import unittest
from unittest import mock

from ofn.adapters.platforms.base import (
    PublishRequest, RULE_NOT_IMPLEMENTED,
)
from ofn.adapters.platforms.telegram_readonly import TelegramReadOnlyAdapter


class TestTelegramReadOnly(unittest.TestCase):
    def test_get_me_parses_result(self):
        adapter = TelegramReadOnlyAdapter(token="t:test")
        with mock.patch.object(adapter, "_call",
                               return_value={"ok": True,
                                             "result": {"username": "ari_bot"}}):
            me = adapter.get_me()
        self.assertTrue(me["ok"])
        self.assertEqual(me["result"]["username"], "ari_bot")

    def test_health_uses_get_me(self):
        adapter = TelegramReadOnlyAdapter(token="t:test")
        with mock.patch.object(adapter, "get_me",
                               return_value={"ok": True,
                                             "result": {"username": "ari_bot"}}):
            h = adapter.health()
        self.assertTrue(h["healthy"])
        self.assertEqual(h["bot"], "ari_bot")

    def test_health_reports_unhealthy_without_token(self):
        adapter = TelegramReadOnlyAdapter(token="")
        h = adapter.health()
        self.assertFalse(h["healthy"])

    def test_publish_is_structurally_absent(self):
        """A read-only adapter must NOT publish — rule says not implemented."""
        adapter = TelegramReadOnlyAdapter(token="t:test")
        req = PublishRequest(platform="telegram", idempotency_key="k1",
                             caption="x")
        result = adapter.publish(req)
        self.assertFalse(result.ok)
        self.assertEqual(result.rule, RULE_NOT_IMPLEMENTED)

    def test_no_token_in_health_error(self):
        adapter = TelegramReadOnlyAdapter(token="")
        h = adapter.health()
        # The error must never echo the token (there is none here, but the
        # shape must hold when there is).
        self.assertNotIn("token:", str(h))


if __name__ == "__main__":
    unittest.main()
