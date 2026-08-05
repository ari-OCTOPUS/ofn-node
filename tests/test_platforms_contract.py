"""Contract tests for platform adapters and the matrix loader.

The adapters' core contract: dry-run is the default, and real publishing
is not implemented (it is wired later, behind OwnerRelease). Anything
that publishes when dry_run=True is a dangerous bug, so we assert it
explicitly.
"""

import unittest

from ofn.adapters.platforms.base import PublishRequest, RULE_DRY_RUN
from ofn.adapters.platforms.telegram_channel import TelegramChannelAdapter
from ofn.adapters.platforms.bluesky import BlueskyAdapter
from ofn.adapters.platforms.email_ses import EmailSesAdapter
from ofn.adapters.platform_matrix_loader import load_matrix, default_matrix_path


def _req(**kw):
    base = dict(platform="x", idempotency_key="k", caption="hi")
    base.update(kw)
    return PublishRequest(**base)


class TestDryRunIsDefault(unittest.TestCase):
    """PublishRequest.dry_run is True unless explicitly set False."""

    def test_default_request_is_dry_run(self):
        self.assertTrue(_req().dry_run)


class TestTelegramAdapter(unittest.TestCase):
    def test_dry_run_returns_ok(self):
        a = TelegramChannelAdapter(channel_id="@channel")
        r = a.publish(_req(platform="tg_channel"))
        self.assertTrue(r.ok)
        self.assertEqual(r.rule, RULE_DRY_RUN)

    def test_real_publish_raises_not_implemented(self):
        a = TelegramChannelAdapter(channel_id="@channel")
        with self.assertRaises(NotImplementedError):
            a.publish(_req(platform="tg_channel", dry_run=False))


class TestBlueskyAdapter(unittest.TestCase):
    def test_dry_run_returns_ok(self):
        a = BlueskyAdapter(handle="x.bsky.social")
        r = a.publish(_req(platform="bsky"))
        self.assertTrue(r.ok)
        self.assertEqual(r.rule, RULE_DRY_RUN)

    def test_real_publish_raises(self):
        a = BlueskyAdapter(handle="x.bsky.social")
        with self.assertRaises(NotImplementedError):
            a.publish(_req(platform="bsky", dry_run=False))


class TestEmailAdapter(unittest.TestCase):
    def test_dry_run_returns_ok(self):
        a = EmailSesAdapter(from_address="x@y.com", list_id="L")
        r = a.publish(_req(platform="email"))
        self.assertTrue(r.ok)
        self.assertEqual(r.rule, RULE_DRY_RUN)

    def test_real_publish_raises(self):
        a = EmailSesAdapter(from_address="x@y.com", list_id="L")
        with self.assertRaises(NotImplementedError):
            a.publish(_req(platform="email", dry_run=False))


class TestMatrixLoader(unittest.TestCase):
    def test_loads_default_matrix_with_real_platforms(self):
        m = load_matrix(default_matrix_path())
        # The shipped file defines the eleven platforms the plan covers.
        keys = set(m.rules)
        self.assertIn("tg_channel", keys)
        self.assertIn("bsky", keys)
        self.assertIn("email", keys)
        self.assertIn("instagram", keys)
        self.assertIn("tiktok", keys)
        self.assertGreaterEqual(len(m.rules), 10)

    def test_shipped_matrix_refuses_restricted_everywhere(self):
        m = load_matrix(default_matrix_path())
        for key in m.rules:
            v = m.screen(platform=key, caption="hi", framing="beauty",
                         sensitivity="restricted")
            self.assertFalse(v.ok, f"{key} allowed restricted out")
            self.assertEqual(v.rule, "advisor:restricted-never-leaves")

    def test_shipped_matrix_refuses_unknown(self):
        m = load_matrix(default_matrix_path())
        v = m.screen(platform="does_not_exist", caption="hi",
                     framing="beauty", sensitivity="general")
        self.assertFalse(v.ok)
        self.assertEqual(v.rule, "platform:unknown")

    def test_shipped_layer_c_refuses_adult_link(self):
        m = load_matrix(default_matrix_path())
        for key in ("instagram", "tiktok", "facebook", "pinterest",
                    "threads", "yt_shorts"):
            v = m.screen(platform=key, caption="see my onlyfans",
                         framing="beauty", sensitivity="general")
            self.assertFalse(v.ok, f"{key} allowed an adult link")


if __name__ == "__main__":
    unittest.main()
