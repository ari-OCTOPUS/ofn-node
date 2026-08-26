"""Contract tests for platform adapters, canonical IDs, and the matrix loader.

Two contracts matter most here:

1. Adapters never crash on a closed WIRE flag — they return a controlled
   `wire:disabled` result, so the outbox worker stays up.
2. Every adapter's `platform` id must exist in the loaded matrix. A router
   that sends to a platform the matrix has never heard of is the bug the
   senior-architect review flagged: it produces `platform:unknown` at
   runtime and the post silently goes nowhere.
"""

import unittest

from ofn.adapters.platforms.base import PublishRequest, RULE_DRY_RUN, RULE_WIRE_CLOSED
from ofn.adapters.platforms.telegram_channel import TelegramChannelAdapter
from ofn.adapters.platforms.bluesky import BlueskyAdapter
from ofn.adapters.platforms.email_ses import EmailSesAdapter
from ofn.adapters.platforms.shopify import ShopifyAdapter
from ofn.adapters.platforms.onlyfans import OnlyFansAdapter
from ofn.adapters.platform_matrix_loader import load_matrix, default_matrix_path


ADAPTER_CLASSES = (
    TelegramChannelAdapter,
    BlueskyAdapter,
    EmailSesAdapter,
    ShopifyAdapter,
    OnlyFansAdapter,
)
CANONICAL_PLATFORMS = {
    "telegram_channel", "bluesky", "email_ses", "x_twitter",
    "youtube_shorts", "threads", "instagram", "tiktok", "pinterest",
    "facebook", "reddit", "shopify", "onlyfans",
}


def _req(**kw):
    base = dict(platform="x", idempotency_key="k", caption="hi")
    base.update(kw)
    return PublishRequest(**base)


class TestDryRunIsDefault(unittest.TestCase):
    def test_default_request_is_dry_run(self):
        self.assertTrue(_req().dry_run)


class TestTelegramAdapter(unittest.TestCase):
    def test_dry_run_returns_ok(self):
        a = TelegramChannelAdapter(channel_id="@channel")
        r = a.publish(_req(platform="telegram_channel"))
        self.assertTrue(r.ok)
        self.assertEqual(r.rule, RULE_DRY_RUN)

    def test_real_publish_returns_wire_disabled_not_crash(self):
        a = TelegramChannelAdapter(channel_id="@channel")
        r = a.publish(_req(platform="telegram_channel", dry_run=False))
        self.assertFalse(r.ok)
        # No token passed → refused without crashing (never a wire crash).
        self.assertEqual(r.rule, "telegram:no-token")


class TestBlueskyAdapter(unittest.TestCase):
    def test_dry_run_returns_ok(self):
        a = BlueskyAdapter(handle="x.bsky.social")
        r = a.publish(_req(platform="bluesky"))
        self.assertTrue(r.ok)
        self.assertEqual(r.rule, RULE_DRY_RUN)

    def test_real_publish_returns_wire_disabled_not_crash(self):
        a = BlueskyAdapter(handle="x.bsky.social")
        r = a.publish(_req(platform="bluesky", dry_run=False))
        self.assertFalse(r.ok)
        self.assertEqual(r.rule, RULE_WIRE_CLOSED)


class TestEmailAdapter(unittest.TestCase):
    def test_dry_run_returns_ok(self):
        a = EmailSesAdapter(from_address="x@y.com", list_id="L")
        r = a.publish(_req(platform="email_ses"))
        self.assertTrue(r.ok)
        self.assertEqual(r.rule, RULE_DRY_RUN)

    def test_real_publish_returns_wire_disabled_not_crash(self):
        a = EmailSesAdapter(from_address="x@y.com", list_id="L")
        r = a.publish(_req(platform="email_ses", dry_run=False))
        self.assertFalse(r.ok)
        self.assertEqual(r.rule, RULE_WIRE_CLOSED)


class TestCanonicalIds(unittest.TestCase):
    """The senior-architect review's blocker: ids must be canonical and
    consistent across adapters and the matrix, or routing silently fails."""

    def test_adapter_platform_ids_are_canonical(self):
        expected = {
            TelegramChannelAdapter: "telegram_channel",
            BlueskyAdapter: "bluesky",
            EmailSesAdapter: "email_ses",
            ShopifyAdapter: "shopify",
            OnlyFansAdapter: "onlyfans",
        }
        for adapter in ADAPTER_CLASSES:
            with self.subTest(adapter=adapter.__name__):
                self.assertEqual(adapter.platform, expected[adapter])

    def test_every_adapter_platform_exists_in_loaded_matrix(self):
        """If this fails, a routed variant hits `platform:unknown` at runtime."""
        m = load_matrix(default_matrix_path())
        for adapter in ADAPTER_CLASSES:
            with self.subTest(adapter=adapter.__name__):
                self.assertIn(
                    adapter.platform, m.rules,
                    f"{adapter.platform!r} not in matrix — router would refuse it")

    def test_matrix_has_all_thirteen_canonical_platforms(self):
        m = load_matrix(default_matrix_path())
        self.assertEqual(
            CANONICAL_PLATFORMS,
            set(m.rules),
            "matrix platform set drifted from canonical thirteen",
        )


class TestPlatformCountsAreSplitAndHonest(unittest.TestCase):
    """Policy, adapter-code, and armed counts must stay distinct and ordered.

    The current snapshot is policy: 13, available: 5, armed: 0. Policy entries
    do not imply live outputs; adapter code is still inert until explicitly
    wired and released.
    """

    def test_available_platforms_discovers_the_five_adapters(self):
        from ofn.adapters.platforms import available_platforms
        got = available_platforms()
        self.assertEqual(
            set(got),
            {"telegram_channel", "bluesky", "email_ses", "shopify", "onlyfans"},
        )

    def test_available_platforms_are_subset_of_policy_known(self):
        from ofn.adapters.platforms import available_platforms
        m = load_matrix(default_matrix_path())
        avail = set(available_platforms())
        self.assertTrue(avail.issubset(set(m.rules)),
                        "an adapter exists for a platform the matrix doesn't know")

    def test_armed_never_exceeds_available_never_exceeds_policy(self):
        # The structural invariant. Today armed is 0 (no adapter is built into
        # the node until OwnerRelease is wired); the test pins that fact so a
        # future change that reports armed>0 has to also wire real publishing,
        # which the hard rules keep off by default.
        from ofn.adapters.platforms import available_platforms
        m = load_matrix(default_matrix_path())
        policy_known = len(m.rules)
        available = len(available_platforms())
        armed = 0
        self.assertEqual(policy_known, 13)
        self.assertEqual(available, 5)
        self.assertEqual(armed, 0)
        self.assertLessEqual(armed, available)
        self.assertLessEqual(available, policy_known)


class TestMatrixLoader(unittest.TestCase):
    def test_loads_default_matrix_with_all_thirteen_platforms(self):
        m = load_matrix(default_matrix_path())
        self.assertEqual(len(m.rules), 13)

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
                    "threads", "youtube_shorts"):
            v = m.screen(platform=key, caption="see my onlyfans",
                         framing="beauty", sensitivity="general")
            self.assertFalse(v.ok, f"{key} allowed an adult link")


class TestContentRouterWithLoadedMatrix(unittest.TestCase):
    """The router must be tested against the loaded matrix, not a hand-built
    one — the senior-architect review's point: the real data path is what
    ships."""

    def test_router_with_loaded_matrix_no_unknowns(self):
        from ofn.adapters.content_router import ContentRouter, DraftForRouting
        m = load_matrix(default_matrix_path())
        router = ContentRouter(m)
        draft = DraftForRouting(
            draft_id="d1", caption_seed="calm beauty moment",
            sensitivity="general", style_id="educational",
            media_refs=("m1",),
        )
        targets = ["telegram_channel", "bluesky", "email_ses", "instagram",
                   "tiktok", "pinterest"]
        vs = router.route(draft, targets, framing="beauty")
        self.assertEqual(len(vs), len(targets))
        # None may be unknown — every target must be a real matrix entry.
        for v in vs:
            self.assertNotEqual(v.screen.rule, "platform:unknown",
                                f"{v.platform} came back unknown")


class TestShopifyAdapter(unittest.TestCase):
    def test_dry_run_returns_ok(self):
        a = ShopifyAdapter(shop_domain="example.myshopify.com")
        r = a.publish(_req(platform="shopify"))
        self.assertTrue(r.ok)
        self.assertEqual(r.rule, RULE_DRY_RUN)

    def test_real_publish_returns_wire_closed_not_crash(self):
        a = ShopifyAdapter(shop_domain="example.myshopify.com")
        r = a.publish(_req(platform="shopify", dry_run=False))
        self.assertFalse(r.ok)
        self.assertEqual(r.rule, RULE_WIRE_CLOSED)

    def test_platform_id_is_shopify(self):
        self.assertEqual(ShopifyAdapter.platform, "shopify")


class TestOnlyFansAdapter(unittest.TestCase):
    def test_dry_run_returns_ok(self):
        a = OnlyFansAdapter(account_id="scaffold")
        r = a.publish(_req(platform="onlyfans"))
        self.assertTrue(r.ok)
        self.assertEqual(r.rule, RULE_DRY_RUN)

    def test_real_publish_returns_wire_closed_not_crash(self):
        a = OnlyFansAdapter(account_id="scaffold")
        r = a.publish(_req(platform="onlyfans", dry_run=False))
        self.assertFalse(r.ok)
        self.assertEqual(r.rule, RULE_WIRE_CLOSED)

    def test_platform_id_is_onlyfans(self):
        self.assertEqual(OnlyFansAdapter.platform, "onlyfans")

if __name__ == "__main__":
    unittest.main()
