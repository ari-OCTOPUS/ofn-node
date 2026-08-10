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


class TestTelegramReadPage(unittest.TestCase):
    """P0-4: the pilot adapter can actually READ a page now.

    Before the fix, TelegramReadOnlyAdapter had no read_page at all, so
    ReadOnlyPilot.run() crashed with AttributeError on every pass and the
    pilot could never run. These tests pin the read surface: identity +
    webhook + channel member count, bounded, read-only, fail-per-item.
    """

    def test_read_page_collects_identity_and_webhook(self):
        adapter = TelegramReadOnlyAdapter(token="t:test")
        with mock.patch.object(adapter, "get_me",
                               return_value={"ok": True, "result": {
                                   "username": "ari_bot",
                                   "can_join_groups": True}}), \
             mock.patch.object(adapter, "get_webhook_info",
                               return_value={"ok": True, "result": {
                                   "url": "https://x/h",
                                   "pending_update_count": 2}}):
            page = adapter.read_page()
        items = {i["type"]: i for i in page["items"]}
        self.assertEqual(items["bot_identity"]["username"], "ari_bot")
        self.assertEqual(items["webhook_info"]["pending"], 2)
        self.assertEqual(page["next_cursor"], "")

    def test_read_page_includes_channel_member_count_when_configured(self):
        adapter = TelegramReadOnlyAdapter(token="t:test",
                                          channel_id="@testchan")
        with mock.patch.object(adapter, "get_me",
                               return_value={"ok": True, "result": {
                                   "username": "ari_bot"}}), \
             mock.patch.object(adapter, "get_webhook_info",
                               return_value={"ok": True, "result": {}}), \
             mock.patch.object(adapter, "get_chat_member_count",
                               return_value={"ok": True, "result": 12}):
            page = adapter.read_page()
        types = [i["type"] for i in page["items"]]
        self.assertIn("member_count", types)
        by_type = {i["type"]: i for i in page["items"]}
        self.assertEqual(by_type["member_count"]["count"], 12)
        self.assertEqual(by_type["member_count"]["chat"], "@testchan")

    def test_read_page_is_bounded_by_limit(self):
        adapter = TelegramReadOnlyAdapter(token="t:test")
        with mock.patch.object(adapter, "get_me",
                               return_value={"ok": True, "result": {}}), \
             mock.patch.object(adapter, "get_webhook_info",
                               return_value={"ok": True, "result": {}}):
            page = adapter.read_page(limit=1)
        self.assertLessEqual(len(page["items"]), 1)

    def test_read_page_never_mutates_and_never_publishes(self):
        """The pilot's page is a read; publishing is structurally absent."""
        adapter = TelegramReadOnlyAdapter(token="t:test")
        with mock.patch.object(adapter, "get_me",
                               return_value={"ok": True, "result": {}}), \
             mock.patch.object(adapter, "get_webhook_info",
                               return_value={"ok": True, "result": {}}):
            page = adapter.read_page()
        req = PublishRequest(platform="telegram", idempotency_key="k1",
                             caption="x")
        result = adapter.publish(req)
        self.assertFalse(result.ok)
        self.assertEqual(result.rule, RULE_NOT_IMPLEMENTED)
        self.assertEqual(page["next_cursor"], "")

    def test_read_page_works_inside_the_pilot_harness(self):
        """The end-to-end shape that was broken: ReadOnlyPilot.run() must
        be able to call the real adapter's read_page."""
        from ofn.adapters.pilot import PilotState, ReadOnlyPilot
        adapter = TelegramReadOnlyAdapter(token="t:test",
                                          channel_id="@testchan")
        with mock.patch.object(adapter, "get_me",
                               return_value={"ok": True, "result": {
                                   "username": "ari_bot"}}), \
             mock.patch.object(adapter, "get_webhook_info",
                               return_value={"ok": True, "result": {}}), \
             mock.patch.object(adapter, "get_chat_member_count",
                               return_value={"ok": True, "result": {
                                   "count": 7}}):
            state = PilotState(connector_id="telegram", tenant="studio")
            pilot = ReadOnlyPilot(adapter, state, page_limit=20)
            out = pilot.run()
        self.assertTrue(out["ok"])
        self.assertEqual(out["read"], 3)   # identity + webhook + members
        self.assertEqual(len(state.receipts), 3)


if __name__ == "__main__":
    unittest.main()
