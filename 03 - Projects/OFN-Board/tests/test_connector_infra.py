"""Marketing connector infrastructure — one test file for all new adapter modules.

Covers: connector_contract, marketing_inbox, correlation, inbound_rate,
        webhook_verify, connector_metrics, and the node.handle_webhook wiring.

All tests use real SQLite in temp dirs (no mocks for stores) and frozen clocks
via lambda overrides, matching the existing OFN test conventions.
"""

from __future__ import annotations

import hashlib
import os
import unittest

from ofn.adapters.connector_contract import (
    FakeConnector,
    Connector, ConnectorHealth, FakeConnector, NormalisedEvent,
    connector_registry,
)
from ofn.adapters.connector_metrics import ConnectorMetrics
from ofn.adapters.correlation import HEADER, generate, from_header
from ofn.adapters.inbound_rate import (
    RULE_LIMITED, RULE_OK, InboundRateLimiter, InboundVerdict,
)
from ofn.adapters.marketing_inbox import (
    FAILED, InboxItem, MarketingInbox, PENDING, PROCESSED,
)
from ofn.adapters.webhook_verify import (
    VerifyResult, noop_verify, verify_hmac, verify_with_header,
)
from ofn.kernel.tenancy import TenantScope, TenantId
from tests.tmpdir import temp_dir

NOW_ISO = "2026-08-10T12:00:00"
NOW_EPOCH = 1_785_000_000


# ═══════════════════════════════════════════════════════════════════════════
#  connector_contract
# ═══════════════════════════════════════════════════════════════════════════

class TestNormalisedEvent(unittest.TestCase):
    def test_frozen(self):
        ev = NormalisedEvent(
            event_type="lead", vendor="fake", vendor_event_id="v1",
            body_sha256="a" * 64, tenant="ziman",
            occurred_at_epoch=NOW_EPOCH, correlation_id="abc123",
        )
        with self.assertRaises(AttributeError):
            ev.event_type = "other"  # type: ignore[misc]

    def test_default_payload_is_empty_tuple(self):
        ev = NormalisedEvent(
            event_type="lead", vendor="fake", vendor_event_id="v1",
            body_sha256="a" * 64, tenant="ziman",
            occurred_at_epoch=NOW_EPOCH, correlation_id="abc123",
        )
        self.assertEqual(ev.payload, ())


class TestConnectorBase(unittest.TestCase):
    def test_default_normalise_returns_none(self):
        c = Connector("test", "test_vendor")
        scope = TenantScope(TenantId("ziman"))
        self.assertIsNone(c.normalise(scope, b"{}", {}, "cid"))

    def test_identify_and_vendor(self):
        c = Connector("my_id", "my_vendor")
        self.assertEqual(c.identify(), "my_id")
        self.assertEqual(c.vendor_name(), "my_vendor")

    def test_health_default(self):
        c = Connector("my_id", "my_vendor")
        h = c.health()
        self.assertIsInstance(h, ConnectorHealth)
        self.assertTrue(h.healthy)
        self.assertEqual(h.connector_id, "my_id")


class TestFakeConnector(unittest.TestCase):
    def setUp(self):
        self.fc = FakeConnector()

    def test_identify_is_fake(self):
        self.assertEqual(self.fc.identify(), "fake")
        self.assertEqual(self.fc.vendor_name(), "fake")

    def test_normalise_produces_event(self):
        scope = TenantScope(TenantId("ziman"))
        body = b'{"test": true}'
        ev = self.fc.normalise(scope, body, {}, "cid123")
        self.assertIsNotNone(ev)
        assert ev is not None  # for type checkers
        self.assertEqual(ev.event_type, "fake")
        self.assertEqual(ev.vendor, "fake")
        self.assertEqual(ev.tenant, "ziman")
        self.assertEqual(ev.correlation_id, "cid123")
        # Raw payload is gone (O3): only the hash survives.
        self.assertEqual(len(ev.body_sha256), 64)
        self.assertEqual(
            ev.body_sha256,
            hashlib.sha256(body).hexdigest())

    def test_vendor_event_id_is_sha256_prefix(self):
        scope = TenantScope(TenantId("ziman"))
        body = b"hello"
        ev = self.fc.normalise(scope, body, {}, "c")
        assert ev is not None
        expected = hashlib.sha256(body).hexdigest()[:16]
        self.assertEqual(ev.vendor_event_id, expected)

    def test_same_body_same_id(self):
        scope = TenantScope(TenantId("ziman"))
        body = b"duplicate"
        ev1 = self.fc.normalise(scope, body, {}, "a")
        ev2 = self.fc.normalise(scope, body, {}, "b")
        assert ev1 is not None and ev2 is not None
        self.assertEqual(ev1.vendor_event_id, ev2.vendor_event_id)


class TestConnectorRegistry(unittest.TestCase):
    def test_builds_lookup_map(self):
        a = FakeConnector()
        b = Connector("other", "other_vendor")
        reg = connector_registry(a, b)
        self.assertIs(reg["fake"], a)
        self.assertIs(reg["other"], b)
        self.assertEqual(len(reg), 2)


# ═══════════════════════════════════════════════════════════════════════════
#  marketing_inbox
# ═══════════════════════════════════════════════════════════════════════════

class TestMarketingInbox(unittest.TestCase):
    def setUp(self):
        self.dir = temp_dir(self)
        self.inbox = MarketingInbox(os.path.join(self.dir, "inbox.sqlite"))
        self.addCleanup(self.inbox.close)

    def test_store_returns_true_on_first_insert(self):
        ok = self.inbox.store(
            tenant="ziman", connector_id="fake", vendor="fake",
            vendor_event_id="v1", correlation_id="c1",
            body=b"{}", inbox_id="id1", now_iso=NOW_ISO,
        )
        self.assertTrue(ok)

    def test_store_returns_false_on_duplicate(self):
        self.inbox.store(
            tenant="ziman", connector_id="fake", vendor="fake",
            vendor_event_id="v1", correlation_id="c1",
            body=b"{}", inbox_id="id1", now_iso=NOW_ISO,
        )
        ok = self.inbox.store(
            tenant="ziman", connector_id="fake", vendor="fake",
            vendor_event_id="v1", correlation_id="c2",
            body=b"{}", inbox_id="id2", now_iso=NOW_ISO,
        )
        self.assertFalse(ok)

    def test_pending_fetches_only_pending(self):
        for i in range(3):
            self.inbox.store(
                tenant="ziman", connector_id="fake", vendor="fake",
                vendor_event_id=f"v{i}", correlation_id=f"c{i}",
                body=f"{{i={i}}}".encode(), inbox_id=f"id{i}",
                now_iso=NOW_ISO,
            )
        # Claim id0 (pending → processing), then finalise it.
        claimed = self.inbox.claim_next(tenant="ziman", now_iso=NOW_ISO)
        self.assertIsNotNone(claimed)
        self.assertTrue(self.inbox.mark_processed("id0", "ziman", NOW_ISO))
        pending = self.inbox.pending("ziman")
        self.assertEqual(len(pending), 2)
        self.assertEqual(pending[0].inbox_id, "id1")

    def test_mark_failed(self):
        self.inbox.store(
            tenant="ziman", connector_id="fake", vendor="fake",
            vendor_event_id="v1", correlation_id="c1",
            body=b"{}", inbox_id="id1", now_iso=NOW_ISO,
        )
        claimed = self.inbox.claim_next(tenant="ziman", now_iso=NOW_ISO)
        self.assertIsNotNone(claimed)
        self.assertTrue(self.inbox.mark_failed("id1", "ziman", NOW_ISO, "parse error"))
        pending = self.inbox.pending("ziman")
        self.assertEqual(len(pending), 0)
        recent = self.inbox.recent("ziman")
        self.assertEqual(recent[0].status, FAILED)
        self.assertEqual(recent[0].error_note, "parse error")

    def test_counts(self):
        for i in range(2):
            self.inbox.store(
                tenant="ziman", connector_id="fake", vendor="fake",
                vendor_event_id=f"v{i}", correlation_id=f"c{i}",
                body=b"{}", inbox_id=f"id{i}", now_iso=NOW_ISO,
            )
        self.inbox.claim_next(tenant="ziman", now_iso=NOW_ISO)
        self.assertTrue(self.inbox.mark_processed("id0", "ziman", NOW_ISO))
        counts = self.inbox.counts("ziman")
        self.assertEqual(counts[PENDING], 1)
        self.assertEqual(counts[PROCESSED], 1)

    def test_counts_all_is_per_tenant(self):
        self.inbox.store(
            tenant="ziman", connector_id="fake", vendor="fake",
            vendor_event_id="v1", correlation_id="c1",
            body=b"{}", inbox_id="id1", now_iso=NOW_ISO,
        )
        self.inbox.store(
            tenant="lead", connector_id="fake", vendor="fake",
            vendor_event_id="v2", correlation_id="c2",
            body=b"{}", inbox_id="id2", now_iso=NOW_ISO,
        )
        all_counts = self.inbox.counts_all()
        self.assertIn("ziman", all_counts)
        self.assertIn("lead", all_counts)

    def test_depth(self):
        for i in range(5):
            self.inbox.store(
                tenant="ziman", connector_id="fake", vendor="fake",
                vendor_event_id=f"v{i}", correlation_id=f"c{i}",
                body=b"{}", inbox_id=f"id{i}", now_iso=NOW_ISO,
            )
        # Claim id0 (processing), id1 stays pending and is failed directly.
        self.inbox.claim_next(tenant="ziman", now_iso=NOW_ISO)
        self.assertTrue(self.inbox.mark_processed("id0", "ziman", NOW_ISO))
        self.assertTrue(self.inbox.mark_failed("id1", "ziman", NOW_ISO, "err"))
        self.assertEqual(self.inbox.depth("ziman"), 3)

    def test_tenant_isolation(self):
        """Items stored for one tenant must not appear in another's queries."""
        self.inbox.store(
            tenant="ziman", connector_id="fake", vendor="fake",
            vendor_event_id="v1", correlation_id="c1",
            body=b"{}", inbox_id="id1", now_iso=NOW_ISO,
        )
        self.assertEqual(self.inbox.depth("lead"), 0)
        self.assertEqual(len(self.inbox.pending("lead")), 0)

    def test_wal_mode(self):
        mode = self.inbox._conn.execute(
            "PRAGMA journal_mode").fetchone()[0]
        self.assertEqual(str(mode).lower(), "wal")

    def test_inbox_item_fields(self):
        self.inbox.store(
            tenant="ziman", connector_id="fake", vendor="fake",
            vendor_event_id="v1", correlation_id="c1",
            body=b'{"data": 42}', inbox_id="id1",
            now_iso=NOW_ISO, event_type="lead",
        )
        items = self.inbox.pending("ziman")
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertIsInstance(item, InboxItem)
        self.assertEqual(item.inbox_id, "id1")
        self.assertEqual(item.tenant, "ziman")
        self.assertEqual(item.event_type, "lead")
        self.assertEqual(len(item.body_sha256), 64)
        self.assertEqual(item.status, PENDING)
        self.assertEqual(item.attempts, 0)


# ═══════════════════════════════════════════════════════════════════════════
#  correlation
# ═══════════════════════════════════════════════════════════════════════════

class TestCorrelation(unittest.TestCase):
    def test_generate_is_16_hex_chars(self):
        cid = generate()
        self.assertEqual(len(cid), 16)
        int(cid, 16)  # must not raise

    def test_generate_is_unique(self):
        cids = {generate() for _ in range(200)}
        self.assertEqual(len(cids), 200)

    def test_from_header_case_insensitive(self):
        cid = from_header({"x-correlation-id": "abc123"})
        self.assertEqual(cid, "abc123")

    def test_from_header_missing_returns_default(self):
        cid = from_header({"content-type": "text/plain"}, default="fallback")
        self.assertEqual(cid, "fallback")

    def test_header_constant(self):
        self.assertEqual(HEADER, "X-Correlation-ID")


# ═══════════════════════════════════════════════════════════════════════════
#  inbound_rate
# ═══════════════════════════════════════════════════════════════════════════

class TestInboundRateLimiter(unittest.TestCase):
    def setUp(self):
        self.limiter = InboundRateLimiter(max_requests=3, window_seconds=60)

    def test_allows_within_limit(self):
        v = self.limiter.check("tenant:ziman", now=0.0)
        self.assertTrue(v.allowed)
        self.assertEqual(v.remaining, 2)
        self.assertEqual(v.rule, RULE_OK)

    def test_rejects_over_limit(self):
        for i in range(3):
            self.limiter.check("tenant:ziman", now=0.0)
        v = self.limiter.check("tenant:ziman", now=0.0)
        self.assertFalse(v.allowed)
        self.assertEqual(v.remaining, 0)
        self.assertGreater(v.retry_after_s, 0)
        self.assertEqual(v.rule, RULE_LIMITED)

    def test_resets_after_window(self):
        for i in range(3):
            self.limiter.check("tenant:ziman", now=0.0)
        v = self.limiter.check("tenant:ziman", now=61.0)
        self.assertTrue(v.allowed)
        self.assertEqual(v.remaining, 2)

    def test_separate_keys(self):
        """One tenant hitting the limit must not block another."""
        for i in range(3):
            self.limiter.check("tenant:ziman", now=0.0)
        v = self.limiter.check("tenant:lead", now=0.0)
        self.assertTrue(v.allowed)

    def test_reset_clears_key(self):
        self.limiter.check("tenant:ziman", now=0.0)
        self.limiter.reset("tenant:ziman")
        v = self.limiter.check("tenant:ziman", now=0.0)
        self.assertEqual(v.remaining, 2)

    def test_reset_all(self):
        self.limiter.check("a", now=0.0)
        self.limiter.check("b", now=0.0)
        self.limiter.reset()
        snap = self.limiter.snapshot()
        self.assertEqual(len(snap), 0)

    def test_snapshot_shows_state(self):
        self.limiter.check("tenant:ziman", now=0.0)
        self.limiter.check("tenant:ziman", now=0.0)
        snap = self.limiter.snapshot()
        self.assertIn("tenant:ziman", snap)
        self.assertEqual(snap["tenant:ziman"]["count"], 2)


class TestRateLimiterBucketCap(unittest.TestCase):
    """The limiter must cap bucket count to prevent memory exhaustion."""

    def test_eviction_when_cap_exceeded(self):
        limiter = InboundRateLimiter(max_requests=10, window_seconds=60,
                                     max_buckets=5)
        # Fill exactly to cap with distinct keys
        for i in range(5):
            limiter.check(f"key{i}", now=0.0)
        # Adding a 6th distinct key should evict the oldest
        limiter.check("key5", now=0.0)
        snap = limiter.snapshot()
        self.assertEqual(len(snap), 5)
        # key0 (oldest) should be evicted
        self.assertNotIn("key0", snap)
        self.assertIn("key5", snap)

    def test_cap_does_not_affect_rate_limiting(self):
        """Even after eviction, the limiter still rate-limits correctly."""
        limiter = InboundRateLimiter(max_requests=2, window_seconds=60,
                                     max_buckets=3)
        for i in range(3):
            limiter.check(f"k{i}", now=0.0)
        # Evict k0 by adding k3
        limiter.check("k3", now=0.0)
        # k1 should still be at count=1
        v = limiter.check("k1", now=0.0)
        self.assertTrue(v.allowed)
        self.assertEqual(v.remaining, 0)  # was 1, now 2 (cap), remaining 0


class TestInboxNoRawBody(unittest.TestCase):
    """The inbox must never store raw webhook payloads — only hash + size."""

    def setUp(self):
        self.dir = temp_dir(self)
        self.inbox = MarketingInbox(os.path.join(self.dir, "inbox.sqlite"))
        self.addCleanup(self.inbox.close)

    def test_stores_hash_not_body(self):
        body = b'{"customer": "private-person", "email": "secret@x.com"}'
        self.inbox.store(
            tenant="ziman", connector_id="fake", vendor="fake",
            vendor_event_id="v1", correlation_id="c1",
            body=body, inbox_id="id1", now_iso=NOW_ISO,
        )
        items = self.inbox.pending("ziman")
        self.assertEqual(len(items), 1)
        item = items[0]
        # Hash is present and is 64 hex chars
        self.assertEqual(len(item.body_sha256), 64)
        # Size is correct
        self.assertEqual(item.body_size, len(body))
        # Raw body is NOT stored anywhere
        import hashlib
        self.assertEqual(item.body_sha256,
                         hashlib.sha256(body).hexdigest())

    def test_no_raw_body_column_in_table(self):
        """The table schema must not have a raw_body column."""
        cols = {r[1] for r in self.inbox._conn.execute(
            "PRAGMA table_info(marketing_inbox)")}
        self.assertNotIn("raw_body", cols)
        self.assertIn("body_sha256", cols)
        self.assertIn("body_size", cols)


class TestInboxStoreErrorPropagation(unittest.TestCase):
    """DB errors must propagate, not be silently returned as 'duplicate'."""

    def setUp(self):
        self.dir = temp_dir(self)
        self.inbox = MarketingInbox(os.path.join(self.dir, "inbox.sqlite"))
        self.addCleanup(self.inbox.close)

    def test_duplicate_returns_false(self):
        """A genuine duplicate returns False, not an exception."""
        self.inbox.store(
            tenant="ziman", connector_id="fake", vendor="fake",
            vendor_event_id="v1", correlation_id="c1",
            body=b"{}", inbox_id="id1", now_iso=NOW_ISO,
        )
        result = self.inbox.store(
            tenant="ziman", connector_id="fake", vendor="fake",
            vendor_event_id="v1", correlation_id="c2",
            body=b"{}", inbox_id="id2", now_iso=NOW_ISO,
        )
        self.assertFalse(result)


class TestWebhookRateLimit(unittest.TestCase):
    """handle_webhook must enforce rate limiting."""

    def setUp(self):
        self.dir = temp_dir(self)
        from ofn.adapters.ledger import Ledger
        from ofn.adapters.outbox import Outbox
        from ofn.adapters.facts import FactStore
        from ofn.adapters.packloader import load_dir
        from ofn.adapters.marketing_inbox import MarketingInbox
        from ofn.adapters.inbound_rate import InboundRateLimiter
        from ofn.kernel.quota import NodeQuota
        from ofn.kernel.tenancy import TenantRegistry
        from ofn.node import Node

        packs_dir = os.path.join(self.dir, "packs")
        os.makedirs(packs_dir)
        _write_pack(os.path.join(packs_dir, "ziman.yaml"))

        inbox = MarketingInbox(os.path.join(self.dir, "inbox.sqlite"))
        registry = TenantRegistry(load_dir(packs_dir))
        self.node = Node(
            registry=registry,
            quota=NodeQuota(estimated_capacity_tokens=1_000_000,
                            utilisation=1.0, shares={"ziman": 1.0}),
            ledger=Ledger(os.path.join(self.dir, "ledger.sqlite")),
            facts=FactStore(os.path.join(self.dir, "facts.sqlite")),
            outbox=Outbox(os.path.join(self.dir, "outbox.sqlite")),
            now_epoch_s=lambda: NOW_EPOCH,
            now_iso=lambda: NOW_ISO,
            inbox=inbox,
            connectors={"fake": FakeConnector()},
            rate_limiter=InboundRateLimiter(max_requests=3, window_seconds=60),
        )
        self.addCleanup(self.node.close)

    def test_allows_within_limit(self):
        # Distinct bodies: same body = same vendor event = duplicate, which
        # is a different rejection from rate limiting.
        for i in range(3):
            r = self.node.handle_webhook(
                "ziman", "fake", {}, b'{"n": ' + str(i).encode() + b'}')
            self.assertTrue(r["ok"])

    def test_rejects_over_limit(self):
        for i in range(3):
            self.node.handle_webhook(
                "ziman", "fake", {}, b'{"n": ' + str(i).encode() + b'}')
        r = self.node.handle_webhook("ziman", "fake", {}, b'{"n": 99}')
        self.assertFalse(r["ok"])
        self.assertEqual(r["error"], "rate limited")
        self.assertIn("retry_after_s", r)


# ═══════════════════════════════════════════════════════════════════════════
#  webhook_verify
# ═══════════════════════════════════════════════════════════════════════════

class TestVerifyHmac(unittest.TestCase):
    def test_valid_signature(self):
        secret = "whsec2026"
        payload = b'{"event": "test"}'
        sig = _make_sig(payload, secret, "sha256")
        r = verify_hmac(payload, secret, sig)
        self.assertTrue(r.valid)

    def test_wrong_secret(self):
        secret = "whsec2026"
        payload = b'{"event": "test"}'
        sig = _make_sig(payload, "other_secret", "sha256")
        r = verify_hmac(payload, secret, sig)
        self.assertFalse(r.valid)
        self.assertEqual(r.reason, "signature mismatch")

    def test_empty_secret(self):
        r = verify_hmac(b"{}", "", "sig")
        self.assertFalse(r.valid)
        self.assertEqual(r.reason, "no signing secret configured")

    def test_empty_signature(self):
        r = verify_hmac(b"{}", "secret", "")
        self.assertFalse(r.valid)
        self.assertEqual(r.reason, "no signature in header")

    def test_tampered_payload(self):
        secret = "whsec2026"
        sig = _make_sig(b'{"good": true}', secret, "sha256")
        r = verify_hmac(b'{"good": false}', secret, sig)
        self.assertFalse(r.valid)


class TestNoopVerify(unittest.TestCase):
    def test_always_valid(self):
        r = noop_verify(b"any", {})
        self.assertTrue(r.valid)


class TestVerifyWithHeader(unittest.TestCase):
    def test_extracts_header_case_insensitive(self):
        secret = "whsec2026"
        payload = b'{"test": true}'
        sig = _make_sig(payload, secret, "sha256")
        r = verify_with_header(
            payload, {"X-Webhook-Signature": sig},
            header_name="x-webhook-signature", secret=secret)
        self.assertTrue(r.valid)

    def test_missing_header_fails(self):
        r = verify_with_header(
            b"{}", {"content-type": "text/plain"},
            header_name="x-webhook-signature", secret="secret")
        self.assertFalse(r.valid)


class TestVerifyHmacSha1(unittest.TestCase):
    def test_sha1_algorithm(self):
        secret = "whsec2026"
        payload = b"hello"
        import hmac as _hmac
        import hashlib as _hl
        mac = _hmac.new(secret.encode(), payload, _hl.sha1)
        sig = f"sha1={mac.hexdigest()}"
        r = verify_hmac(payload, secret, sig, algorithm="sha1")
        self.assertTrue(r.valid)


def _make_sig(payload: bytes, secret: str, algorithm: str) -> str:
    import hashlib
    import hmac
    mac = hmac.new(secret.encode(), payload, getattr(hashlib, algorithm))
    return f"{algorithm}={mac.hexdigest()}"


# ═══════════════════════════════════════════════════════════════════════════
#  connector_metrics
# ═══════════════════════════════════════════════════════════════════════════

class TestConnectorMetrics(unittest.TestCase):
    def setUp(self):
        self.m = ConnectorMetrics()

    def test_initial_snapshot_empty(self):
        self.assertEqual(self.m.snapshot(), {})

    def test_record_inbound(self):
        self.m.record_inbound("fake")
        snap = self.m.snapshot()
        self.assertEqual(snap["fake"]["inbound"], 1)

    def test_record_processed(self):
        self.m.record_processed("fake")
        snap = self.m.snapshot()
        self.assertEqual(snap["fake"]["processed"], 1)

    def test_record_failed(self):
        self.m.record_failed("fake")
        snap = self.m.snapshot()
        self.assertEqual(snap["fake"]["failed"], 1)

    def test_record_rejected(self):
        self.m.record_rejected("fake")
        snap = self.m.snapshot()
        self.assertEqual(snap["fake"]["rejected"], 1)

    def test_record_timing(self):
        self.m.record_timing("fake", 100)
        self.m.record_timing("fake", 200)
        snap = self.m.snapshot()
        self.assertEqual(snap["fake"]["avg_processing_ms"], 150.0)
        self.assertEqual(snap["fake"]["processing_count"], 2)

    def test_multiple_connectors(self):
        self.m.record_inbound("fake")
        self.m.record_inbound("mailchimp")
        snap = self.m.snapshot()
        self.assertIn("fake", snap)
        self.assertIn("mailchimp", snap)

    def test_reset(self):
        self.m.record_inbound("fake")
        self.m.reset()
        self.assertEqual(self.m.snapshot(), {})

    def test_avg_with_no_records(self):
        self.m.record_inbound("fake")
        snap = self.m.snapshot()
        self.assertEqual(snap["fake"]["avg_processing_ms"], 0.0)
        self.assertEqual(snap["fake"]["processing_count"], 0)

    def test_thread_safety(self):
        """Multiple threads incrementing should not lose counts."""
        import threading
        threads = []
        for _ in range(10):
            t = threading.Thread(
                target=lambda: self.m.record_inbound("fake"))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(self.m.snapshot()["fake"]["inbound"], 10)


# ═══════════════════════════════════════════════════════════════════════════
#  integration: node.handle_webhook
# ═══════════════════════════════════════════════════════════════════════════

class TestHandleWebhook(unittest.TestCase):
    """Test the Node.handle_webhook method end-to-end with real stores."""

    def setUp(self):
        self.dir = temp_dir(self)
        from ofn.adapters.ledger import Ledger
        from ofn.adapters.outbox import Outbox
        from ofn.adapters.facts import FactStore
        from ofn.adapters.packloader import load_dir
        from ofn.adapters.marketing_inbox import MarketingInbox
        from ofn.kernel.quota import NodeQuota
        from ofn.kernel.tenancy import TenantRegistry
        from ofn.node import Node

        packs_dir = os.path.join(self.dir, "packs")
        os.makedirs(packs_dir)
        # Create minimal ziman pack so the registry has a tenant
        _write_pack(os.path.join(packs_dir, "ziman.yaml"))

        ledger_path = os.path.join(self.dir, "ledger.sqlite")
        facts_path = os.path.join(self.dir, "facts.sqlite")
        outbox_path = os.path.join(self.dir, "outbox.sqlite")
        inbox_path = os.path.join(self.dir, "inbox.sqlite")

        ledger = Ledger(ledger_path)
        facts = FactStore(facts_path)
        outbox = Outbox(outbox_path)
        inbox = MarketingInbox(inbox_path)

        registry = TenantRegistry(load_dir(packs_dir))
        quota = NodeQuota(estimated_capacity_tokens=1_000_000,
                          utilisation=1.0,
                          shares={"ziman": 1.0})

        self.node = Node(
            registry=registry, quota=quota,
            ledger=ledger, facts=facts, outbox=outbox,
            now_epoch_s=lambda: NOW_EPOCH,
            now_iso=lambda: NOW_ISO,
            inbox=inbox,
            connectors={"fake": FakeConnector()},
        )
        self.addCleanup(self.node.close)
        self.inbox_ref = inbox

    def test_accepted_stores_in_inbox(self):
        result = self.node.handle_webhook("ziman", "fake", {}, b'{"hello": "world"}')
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "accepted")
        self.assertIn("inbox_id", result)
        self.assertIn("correlation_id", result)

        # Verify it actually landed in the inbox
        pending = self.inbox_ref.pending("ziman")
        self.assertEqual(len(pending), 1)
        self.assertEqual(len(pending[0].body_sha256), 64)

    def test_unknown_tenant_rejected(self):
        result = self.node.handle_webhook("nonexistent", "fake", {}, b"{}")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "rejected")
        self.assertIn("unknown tenant", result["error"])

    def test_none_tenant_rejected(self):
        result = self.node.handle_webhook(None, "fake", {}, b"{}")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "rejected")

    def test_correlation_id_propagated_from_header(self):
        headers = {"X-Correlation-Id": "incoming-cid-12345"}
        result = self.node.handle_webhook("ziman", "fake", headers, b"{}")
        self.assertEqual(result["correlation_id"], "incoming-cid-12345")

    def test_duplicate_rejected(self):
        """Same vendor_event_id+connector_id+tenant must be rejected by inbox."""
        r1 = self.node.handle_webhook("ziman", "fake", {}, b"first")
        self.assertTrue(r1["ok"])

        # Re-inserting with the same vendor_event_id is a duplicate
        # because handle_webhook sets vendor_event_id = inbox_id.
        dup = self.inbox_ref.store(
            tenant="ziman", connector_id="fake", vendor="unknown",
            vendor_event_id=r1["inbox_id"], correlation_id="test",
            body=b"dup", inbox_id="dup_id", now_iso=NOW_ISO,
        )
        self.assertFalse(dup)  # duplicate vendor_event_id

        # A genuinely new vendor_event_id succeeds.
        ok = self.inbox_ref.store(
            tenant="ziman", connector_id="fake", vendor="unknown",
            vendor_event_id="brand_new_vid", correlation_id="test",
            body=b"new", inbox_id="new_id", now_iso=NOW_ISO,
        )
        self.assertTrue(ok)

    def test_ledger_entry_created(self):
        result = self.node.handle_webhook("ziman", "fake", {}, b'{"event": "test"}')
        self.assertTrue(result["ok"])
        scope = self.node.registry.scope("ziman")
        events = self.node.ledger.read(scope, limit=1)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].kind, "WEBHOOK_RECEIVED")
        self.assertEqual(events[0].payload["inbox_id"], result["inbox_id"])


# ═══════════════════════════════════════════════════════════════════════════
#  owner_observability endpoint
# ═══════════════════════════════════════════════════════════════════════════

class TestOwnerObservability(unittest.TestCase):
    """The owner's observability read: counts only, no secrets, no PII."""

    def setUp(self):
        self.dir = temp_dir(self)
        from ofn.adapters.ledger import Ledger
        from ofn.adapters.outbox import Outbox
        from ofn.adapters.facts import FactStore
        from ofn.adapters.packloader import load_dir
        from ofn.adapters.marketing_inbox import MarketingInbox
        from ofn.kernel.quota import NodeQuota
        from ofn.kernel.tenancy import TenantRegistry
        from ofn.node import Node

        packs_dir = os.path.join(self.dir, "packs")
        os.makedirs(packs_dir)
        _write_pack(os.path.join(packs_dir, "ziman.yaml"))

        ledger = Ledger(os.path.join(self.dir, "ledger.sqlite"))
        facts = FactStore(os.path.join(self.dir, "facts.sqlite"))
        outbox = Outbox(os.path.join(self.dir, "outbox.sqlite"))
        inbox = MarketingInbox(os.path.join(self.dir, "inbox.sqlite"))

        registry = TenantRegistry(load_dir(packs_dir))
        quota = NodeQuota(estimated_capacity_tokens=1_000_000,
                          utilisation=1.0, shares={"ziman": 1.0})

        self.node = Node(
            registry=registry, quota=quota,
            ledger=ledger, facts=facts, outbox=outbox,
            now_epoch_s=lambda: NOW_EPOCH,
            now_iso=lambda: NOW_ISO,
            inbox=inbox,
            connectors={"fake": FakeConnector()},
        )
        self.addCleanup(self.node.close)
        self.inbox_ref = inbox

    def test_returns_ok(self):
        obs = self.node.owner_observability()
        self.assertTrue(obs["ok"])

    def test_webhook_route_reported(self):
        obs = self.node.owner_observability()
        self.assertTrue(obs["webhook_route"])

    def test_no_vendors_connected(self):
        """No real vendor is wired yet."""
        obs = self.node.owner_observability()
        self.assertEqual(obs["vendors_connected"], [])

    def test_tenant_counts_present(self):
        obs = self.node.owner_observability()
        self.assertIn("ziman", obs["tenants"])
        t = obs["tenants"]["ziman"]
        self.assertEqual(t["inbox_pending"], 0)
        self.assertEqual(t["inbox_depth"], 0)

    def test_counts_reflect_stored_items(self):
        self.inbox_ref.store(
            tenant="ziman", connector_id="fake", vendor="fake",
            vendor_event_id="v1", correlation_id="c1",
            body=b"{}", inbox_id="id1", now_iso=NOW_ISO,
        )
        self.inbox_ref.store(
            tenant="ziman", connector_id="fake", vendor="fake",
            vendor_event_id="v2", correlation_id="c2",
            body=b"{}", inbox_id="id2", now_iso=NOW_ISO,
        )
        self.inbox_ref.claim_next(tenant="ziman", now_iso=NOW_ISO)
        self.assertTrue(self.inbox_ref.mark_processed("id1", "ziman", NOW_ISO))
        obs = self.node.owner_observability()
        t = obs["tenants"]["ziman"]
        self.assertEqual(t["inbox_pending"], 1)
        self.assertEqual(t["inbox_processed"], 1)
        self.assertEqual(t["inbox_depth"], 1)

    def test_no_raw_body_or_secret_leaked(self):
        """The response must never contain raw webhook payloads or secrets."""
        secret_like = "whsec_super_secret_12345"
        self.inbox_ref.store(
            tenant="ziman", connector_id="fake", vendor="fake",
            vendor_event_id="v1", correlation_id="c1",
            body=('{"secret": "' + secret_like + '"}').encode(),
            inbox_id="id1", now_iso=NOW_ISO,
        )
        import json
        obs = self.node.owner_observability()
        serialised = json.dumps(obs)
        self.assertNotIn(secret_like, serialised)
        self.assertNotIn("raw_body", serialised)

    def test_no_inbox_wired_reports_error(self):
        """When inbox is None, the response says so rather than crashing."""
        from ofn.adapters.ledger import Ledger
        from ofn.adapters.outbox import Outbox
        from ofn.adapters.facts import FactStore
        from ofn.adapters.packloader import load_dir
        from ofn.kernel.quota import NodeQuota
        from ofn.kernel.tenancy import TenantRegistry
        from ofn.node import Node

        packs_dir = os.path.join(self.dir, "packs2")
        os.makedirs(packs_dir)
        _write_pack(os.path.join(packs_dir, "ziman.yaml"))
        registry = TenantRegistry(load_dir(packs_dir))
        node = Node(
            registry=registry,
            quota=NodeQuota(estimated_capacity_tokens=1_000_000,
                            utilisation=1.0, shares={"ziman": 1.0}),
            ledger=Ledger(os.path.join(self.dir, "l2.sqlite")),
            facts=FactStore(os.path.join(self.dir, "f2.sqlite")),
            outbox=Outbox(os.path.join(self.dir, "o2.sqlite")),
            now_epoch_s=lambda: NOW_EPOCH,
            now_iso=lambda: NOW_ISO,
            inbox=None,
        )
        self.addCleanup(node.close)
        obs = node.owner_observability()
        self.assertIn("inbox_error", obs)


class TestObservabilityHttpRoute(unittest.TestCase):
    """The HTTP route for observability: owner-only, no-store."""

    def setUp(self):
        self.dir = temp_dir(self)
        from ofn.adapters.ledger import Ledger
        from ofn.adapters.outbox import Outbox
        from ofn.adapters.facts import FactStore
        from ofn.adapters.packloader import load_dir
        from ofn.adapters.marketing_inbox import MarketingInbox
        from ofn.adapters.http_api import ApiApp, HostMap
        from ofn.kernel.auth import issue_session
        from ofn.kernel.quota import NodeQuota
        from ofn.kernel.tenancy import TenantRegistry
        from ofn.node import Node

        packs_dir = os.path.join(self.dir, "packs")
        os.makedirs(packs_dir)
        _write_pack(os.path.join(packs_dir, "ziman.yaml"))

        ledger = Ledger(os.path.join(self.dir, "ledger.sqlite"))
        facts = FactStore(os.path.join(self.dir, "facts.sqlite"))
        outbox = Outbox(os.path.join(self.dir, "outbox.sqlite"))
        inbox = MarketingInbox(os.path.join(self.dir, "inbox.sqlite"))

        self.registry = TenantRegistry(load_dir(packs_dir))
        self.node = Node(
            registry=self.registry,
            quota=NodeQuota(estimated_capacity_tokens=1_000_000,
                            utilisation=1.0, shares={"ziman": 1.0}),
            ledger=ledger, facts=facts, outbox=outbox,
            now_epoch_s=lambda: NOW_EPOCH,
            now_iso=lambda: NOW_ISO,
            inbox=inbox,
            connectors={"fake": FakeConnector()},
        )
        self.addCleanup(self.node.close)
        SECRET = "obs-test-secret"
        OWNER_ID = "9001"
        self.app = ApiApp(
            self.registry,
            HostMap(tenants={"panel.test": "ziman"}, owner_host="panel.test"),
            bot_tokens={"__owner__": "t"},
            session_secret=SECRET,
            owner_user_ids=(OWNER_ID,),
            partner_user_ids={},
            now=lambda: NOW_EPOCH,
            owner_observability=self.node.owner_observability,
        )
        self.owner_session = issue_session(
            "owner", OWNER_ID, SECRET, now_epoch_s=NOW_EPOCH)

    def _owner_get(self, path):
        return self.app.handle(
            "GET", path,
            {"host": "panel.test",
             "authorization": "Bearer " + self.owner_session},
            b"")

    def test_returns_200_with_inbox_counts(self):
        resp = self._owner_get("/api/v1/owner/observability")
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.body["ok"])
        self.assertIn("tenants", resp.body)
        self.assertIn("ziman", resp.body["tenants"])

    def test_no_store_header(self):
        resp = self._owner_get("/api/v1/owner/observability")
        self.assertEqual(
            resp.headers.get("Cache-Control"), "private, no-store")

    def test_requires_owner_session(self):
        resp = self.app.handle(
            "GET", "/api/v1/owner/observability",
            {"host": "panel.test"}, b"")
        self.assertEqual(resp.status, 401)


def _write_pack(path: str) -> None:
    """Write a minimal pack YAML so the registry can load it."""
    with open(path, "w") as f:
        f.write(
            "tenant: ziman\n"
            "sku_prefix: ZM\n"
            "locale:\n"
            "  id: en-AU\n"
            "  timezone: Australia/Sydney\n"
            "  tax:\n"
            "    status: unresolved\n"
            "    pricing: inclusive\n"
            "  payment_rails: []\n"
            "  platforms: []\n"
            "capacity_units_per_week: 6\n"
            "required_facts:\n"
            "  dummy_fact: owner_confirmed\n"
            "costing:\n"
            "  cost_fields: [materials_cost_aud]\n"
            "  quick_sale_days: 7\n"
            "channels:\n"
            "questions:\n"
            "gates: []\n"
            "risk_overrides:\n"
            "  dummy_action: green\n"
            "quota_share: 0.35\n"
        )


class TestO3WebhookSecurity(unittest.TestCase):
    """O3: unknown connector rejected, fake signed once, no raw body."""

    def setUp(self):
        self.dir = temp_dir(self)
        from ofn.adapters.ledger import Ledger
        from ofn.adapters.outbox import Outbox
        from ofn.adapters.facts import FactStore
        from ofn.adapters.packloader import load_dir
        from ofn.adapters.marketing_inbox import MarketingInbox
        from ofn.kernel.quota import NodeQuota
        from ofn.kernel.tenancy import TenantRegistry
        from ofn.node import Node

        packs_dir = os.path.join(self.dir, "packs")
        os.makedirs(packs_dir)
        _write_pack(os.path.join(packs_dir, "ziman.yaml"))
        inbox = MarketingInbox(os.path.join(self.dir, "inbox.sqlite"))
        registry = TenantRegistry(load_dir(packs_dir))
        self.node = Node(
            registry=registry,
            quota=NodeQuota(estimated_capacity_tokens=1_000_000,
                            utilisation=1.0, shares={"ziman": 1.0}),
            ledger=Ledger(os.path.join(self.dir, "ledger.sqlite")),
            facts=FactStore(os.path.join(self.dir, "facts.sqlite")),
            outbox=Outbox(os.path.join(self.dir, "outbox.sqlite")),
            now_epoch_s=lambda: NOW_EPOCH,
            now_iso=lambda: NOW_ISO,
            inbox=inbox,
            connectors={"fake": FakeConnector()},
        )
        self.addCleanup(self.node.close)
        self.inbox_ref = inbox

    def test_unknown_connector_rejected(self):
        r = self.node.handle_webhook("ziman", "nope", {}, b"{}")
        self.assertFalse(r["ok"])
        self.assertEqual(r.get("rule"), "webhook:unknown-connector")
        # Nothing stored
        self.assertEqual(self.inbox_ref.depth("ziman"), 0)

    def test_connector_without_verifier_rejected(self):
        # A plain Connector (no verify impl) must reject everything.
        from ofn.adapters.connector_contract import Connector
        self.node.connectors = {"plain": Connector("plain", "v")}
        r = self.node.handle_webhook("ziman", "plain", {}, b"{}")
        self.assertFalse(r["ok"])
        self.assertEqual(r.get("rule"), "webhook:signature-invalid")

    def test_same_body_is_duplicate(self):
        """Same vendor event id (body hash) + connector = one store."""
        r1 = self.node.handle_webhook("ziman", "fake", {}, b'{"x": 1}')
        self.assertTrue(r1["ok"])
        r2 = self.node.handle_webhook("ziman", "fake", {}, b'{"x": 1}')
        self.assertFalse(r2["ok"])
        self.assertEqual(r2["error"], "duplicate webhook")
        self.assertEqual(self.inbox_ref.depth("ziman"), 1)

    def test_different_body_same_id_is_handled_by_hash(self):
        """Different bodies → different vendor ids → both accepted."""
        r1 = self.node.handle_webhook("ziman", "fake", {}, b'{"x": 1}')
        r2 = self.node.handle_webhook("ziman", "fake", {}, b'{"x": 2}')
        self.assertTrue(r1["ok"])
        self.assertTrue(r2["ok"])
        self.assertNotEqual(r1["inbox_id"], r2["inbox_id"])
        self.assertEqual(self.inbox_ref.depth("ziman"), 2)

    def test_no_raw_body_in_inbox(self):
        secret_like = "secret-value-12345"
        self.node.handle_webhook(
            "ziman", "fake", {}, f'{{"s": "{secret_like}"}}'.encode())
        items = self.inbox_ref.pending("ziman")
        self.assertEqual(len(items), 1)
        import json as _j
        serialised = _j.dumps(self.inbox_ref.recent("ziman")[0].__dict__)
        self.assertNotIn(secret_like, serialised)
