"""Contract tests for rate limiting and the content router."""

import unittest

from ofn.adapters.rate_limit import may_consume, RateWindow, RULE_LIMIT
from ofn.adapters.content_router import (
    ContentRouter, DraftForRouting, idempotency_key, safe_caption,
)
from ofn.kernel.platform_matrix import PlatformMatrix, PlatformRule


# ── rate limit ────────────────────────────────────────────────────────

class TestRateLimit(unittest.TestCase):
    def _win(self, **kw):
        base = dict(max_count=5, window_seconds=3600, used=0, reset_at=2000)
        base.update(kw)
        return RateWindow(**base)

    def test_within_window_under_limit_ok(self):
        v = may_consume(self._win(used=2), now=1000)
        self.assertTrue(v.ok)

    def test_at_limit_refused_with_retry_after(self):
        v = may_consume(self._win(used=5), now=1000)
        self.assertFalse(v.ok)
        self.assertEqual(v.rule, RULE_LIMIT)
        self.assertEqual(v.retry_after_s, 1000)

    def test_after_reset_ok_again(self):
        v = may_consume(self._win(used=5, reset_at=500), now=1000)
        self.assertTrue(v.ok)

    def test_zero_amount_always_ok(self):
        v = may_consume(self._win(used=5), now=1000, amount=0)
        self.assertTrue(v.ok)

    def test_negative_amount_refused(self):
        v = may_consume(self._win(), now=1000, amount=-1)
        self.assertFalse(v.ok)


# ── content router ────────────────────────────────────────────────────

def _matrix():
    return PlatformMatrix({
        "short": PlatformRule(
            "short", "A", "YELLOW", "wellness_only", False, 10,
            ("beauty",), ("fetish",),
            adult_link_markers=("onlyfans",),
            solicitation_markers=("escort",),
        ),
        "long": PlatformRule(
            "long", "A", "YELLOW", "wellness_only", False, 1000,
            ("beauty",), ("fetish",),
            adult_link_markers=("onlyfans",),
            solicitation_markers=("escort",),
        ),
    })


class TestSafeCaption(unittest.TestCase):
    def test_truncates_to_caption_max(self):
        m = _matrix()
        self.assertEqual(len(safe_caption("x" * 50, "short", m)), 10)

    def test_no_max_leaves_caption_unchanged(self):
        rule = PlatformRule("n", "A", "Y", "wellness_only", False, None)
        m = PlatformMatrix({"n": rule})
        self.assertEqual(safe_caption("hello world", "n", m), "hello world")


class TestIdempotencyKey(unittest.TestCase):
    def test_same_triple_same_key(self):
        k1 = idempotency_key("d1", "p", "caption")
        k2 = idempotency_key("d1", "p", "caption")
        self.assertEqual(k1, k2)

    def test_different_caption_different_key(self):
        k1 = idempotency_key("d1", "p", "caption a")
        k2 = idempotency_key("d1", "p", "caption b")
        self.assertNotEqual(k1, k2)

    def test_different_platform_different_key(self):
        k1 = idempotency_key("d1", "p1", "caption")
        k2 = idempotency_key("d1", "p2", "caption")
        self.assertNotEqual(k1, k2)


class TestContentRouter(unittest.TestCase):
    def test_produces_one_variant_per_platform(self):
        r = ContentRouter(_matrix())
        draft = DraftForRouting("d1", "hello", "general", "educational")
        vs = r.route(draft, ("short", "long"), framing="beauty")
        self.assertEqual(len(vs), 2)
        self.assertEqual({v.platform for v in vs}, {"short", "long"})

    def test_refused_variant_is_returned_not_dropped(self):
        # 'restricted' sensitivity → every platform refuses. The router
        # must still return the variants so the caller sees the refusals.
        r = ContentRouter(_matrix())
        draft = DraftForRouting("d1", "hello", "restricted", "educational")
        vs = r.route(draft, ("short", "long"), framing="beauty")
        self.assertEqual(len(vs), 2)
        self.assertFalse(vs[0].screen.ok)
        self.assertFalse(vs[1].screen.ok)

    def test_truncated_caption_gets_truncated_key(self):
        # A caption truncated to fit short changes the idempotency key
        # vs the long-platform variant, which is correct: they are
        # different posts.
        r = ContentRouter(_matrix())
        draft = DraftForRouting("d1", "x" * 50, "general", "educational")
        vs = r.route(draft, ("short", "long"), framing="beauty")
        keys = {v.platform: v.idempotency_key for v in vs}
        self.assertEqual(len(vs[0].caption), 10)   # short truncated
        self.assertEqual(len(vs[1].caption), 50)   # long intact
        self.assertNotEqual(keys["short"], keys["long"])


if __name__ == "__main__":
    unittest.main()
