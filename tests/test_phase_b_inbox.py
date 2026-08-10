"""Phase B — inbox state machine + dry-run processor (findings 28, 39, 27).

The inbox gains a claim state machine:
  pending → processing (atomic claim) → processed | failed | held

And a dry-run processor that claims + validates shape, doing NO outbound
work. Reconciliation gaps (inbox stored but ledger failed) are counted and
exposed in observability.
"""

from __future__ import annotations

import os
import unittest

from ofn.adapters.inbox_processor import ProcessStats, process_inbox_once
from ofn.adapters.marketing_inbox import (
    FAILED, HELD, PENDING, PROCESSED, PROCESSING, InboxItem, MarketingInbox,
)

from tests.tmpdir import temp_dir

NOW_ISO = "2026-08-10T12:00:00"


def _store(inbox, i: int, *, vendor_event_id: str | None = None):
    """Helper: store item i with default values."""
    vid = f"v{i}" if vendor_event_id is None else vendor_event_id
    return inbox.store(
        tenant="ziman", connector_id="fake", vendor="fake",
        vendor_event_id=vid,
        correlation_id=f"c{i}", body=b"{}", inbox_id=f"id{i}",
        now_iso=NOW_ISO)


class TestClaimNext(unittest.TestCase):
    """claim_next is atomic: pending → processing, race-free."""

    def setUp(self):
        self.dir = temp_dir(self)
        self.inbox = MarketingInbox(os.path.join(self.dir, "inbox.sqlite"))
        self.addCleanup(self.inbox.close)

    def test_claims_oldest_pending(self):
        _store(self.inbox, 1)
        _store(self.inbox, 2)
        item = self.inbox.claim_next(tenant="ziman", now_iso=NOW_ISO)
        self.assertIsNotNone(item)
        assert item is not None
        self.assertEqual(item.inbox_id, "id1")
        self.assertEqual(item.status, PENDING)  # returned snapshot is pre-claim
        # The row in DB is now processing
        rows = self.inbox.pending("ziman")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].inbox_id, "id2")

    def test_claim_next_returns_none_when_empty(self):
        self.assertIsNone(self.inbox.claim_next(tenant="ziman",
                                                now_iso=NOW_ISO))

    def test_two_claims_never_get_same_item(self):
        _store(self.inbox, 1)
        _store(self.inbox, 2)
        a = self.inbox.claim_next(tenant="ziman", now_iso=NOW_ISO)
        b = self.inbox.claim_next(tenant="ziman", now_iso=NOW_ISO)
        assert a is not None and b is not None
        self.assertNotEqual(a.inbox_id, b.inbox_id)

    def test_mark_processed_only_from_processing(self):
        _store(self.inbox, 1)
        # Without claiming, mark_processed must fail
        self.assertFalse(self.inbox.mark_processed("id1", "ziman", NOW_ISO))
        item = self.inbox.claim_next(tenant="ziman", now_iso=NOW_ISO)
        assert item is not None
        self.assertTrue(self.inbox.mark_processed("id1", "ziman", NOW_ISO))
        # Double mark fails
        self.assertFalse(self.inbox.mark_processed("id1", "ziman", NOW_ISO))

    def test_mark_failed_from_processing(self):
        _store(self.inbox, 1)
        item = self.inbox.claim_next(tenant="ziman", now_iso=NOW_ISO)
        assert item is not None
        self.assertTrue(self.inbox.mark_failed("id1", "ziman", NOW_ISO,
                                               note="bad shape"))
        recent = self.inbox.recent("ziman")
        self.assertEqual(recent[0].status, FAILED)


class TestRecoverStale(unittest.TestCase):
    """PROCESSING rows older than timeout become HELD, fresh ones don't."""

    def setUp(self):
        self.dir = temp_dir(self)
        self.inbox = MarketingInbox(os.path.join(self.dir, "inbox.sqlite"))
        self.addCleanup(self.inbox.close)

    def test_old_processing_row_becomes_held(self):
        _store(self.inbox, 1)
        old_claim = "2026-08-10T10:00:00"   # 2 hours before NOW_ISO
        item = self.inbox.claim_next(tenant="ziman", now_iso=old_claim)
        assert item is not None
        # Simulate a crash: item stays PROCESSING
        n = self.inbox.recover_stale(timeout_s=300, now_iso=NOW_ISO)
        self.assertEqual(n, 1)
        recent = self.inbox.recent("ziman")
        self.assertEqual(recent[0].status, HELD)

    def test_fresh_processing_row_not_touched(self):
        _store(self.inbox, 1)
        item = self.inbox.claim_next(tenant="ziman", now_iso=NOW_ISO)
        assert item is not None
        n = self.inbox.recover_stale(timeout_s=300, now_iso=NOW_ISO)
        self.assertEqual(n, 0)


class TestDryRunProcessor(unittest.TestCase):
    """process_inbox_once claims and validates; does nothing else."""

    def setUp(self):
        self.dir = temp_dir(self)
        self.inbox = MarketingInbox(os.path.join(self.dir, "inbox.sqlite"))
        self.addCleanup(self.inbox.close)

    def test_valid_items_are_processed(self):
        _store(self.inbox, 1)
        _store(self.inbox, 2)
        stats = process_inbox_once(self.inbox, tenant="ziman",
                                   now_iso=NOW_ISO, limit=10)
        self.assertEqual(stats.claimed, 2)
        self.assertEqual(stats.processed, 2)
        self.assertEqual(stats.held, 0)
        self.assertEqual(stats.errors, 0)
        self.assertEqual(self.inbox.depth("ziman"), 0)
        self.assertEqual(self.inbox.counts("ziman").get(PROCESSED), 2)

    def test_item_without_vendor_event_id_is_held(self):
        _store(self.inbox, 1, vendor_event_id="")
        stats = process_inbox_once(self.inbox, tenant="ziman",
                                   now_iso=NOW_ISO, limit=10)
        self.assertEqual(stats.held, 1)
        self.assertEqual(stats.processed, 0)
        recent = self.inbox.recent("ziman")
        self.assertEqual(recent[0].status, FAILED)
        self.assertIn("missing vendor event id", recent[0].error_note)

    def test_limit_respected(self):
        for i in range(5):
            _store(self.inbox, i)
        stats = process_inbox_once(self.inbox, tenant="ziman",
                                   now_iso=NOW_ISO, limit=3)
        self.assertEqual(stats.claimed, 3)
        self.assertEqual(self.inbox.depth("ziman"), 2)

    def test_stats_shape(self):
        s = ProcessStats()
        self.assertEqual(s.as_dict(),
                         {"claimed": 0, "processed": 0, "held": 0,
                          "errors": 0})


class TestReconciliationCounter(unittest.TestCase):
    """inbox stored but ledger failed must be countable, not silent."""

    def setUp(self):
        self.dir = temp_dir(self)
        from ofn.adapters.ledger import Ledger
        from ofn.adapters.outbox import Outbox
        from ofn.adapters.facts import FactStore
        from ofn.adapters.packloader import load_dir
        from ofn.kernel.quota import NodeQuota
        from ofn.kernel.tenancy import TenantRegistry
        from ofn.node import Node

        packs_dir = os.path.join(self.dir, "packs")
        os.makedirs(packs_dir)
        with open(os.path.join(packs_dir, "ziman.yaml"), "w") as f:
            f.write(
                "tenant: ziman\n"
                "capacity_units_per_week: 6\n"
                "required_facts:\n"
                "  dummy_fact: owner_confirmed\n"
                "gates: []\n"
                "risk_overrides:\n"
                "  dummy_action: green\n"
                "quota_share: 0.5\n"
            )

        self.inbox = MarketingInbox(os.path.join(self.dir, "inbox.sqlite"))
        registry = TenantRegistry(load_dir(packs_dir))
        self.node = Node(
            registry=registry,
            quota=NodeQuota(estimated_capacity_tokens=1_000_000,
                            utilisation=1.0, shares={"ziman": 0.5}),
            ledger=Ledger(os.path.join(self.dir, "ledger.sqlite")),
            facts=FactStore(os.path.join(self.dir, "facts.sqlite")),
            outbox=Outbox(os.path.join(self.dir, "outbox.sqlite")),
            now_epoch_s=lambda: 1_785_000_000,
            now_iso=lambda: NOW_ISO,
            inbox=self.inbox,
        )
        self.addCleanup(self.node.close)

    def test_gap_counter_starts_zero(self):
        obs = self.node.owner_observability()
        self.assertEqual(obs.get("inbox_ledger_gaps"), 0)

    def test_gap_counter_exposed_in_observability(self):
        # Break the ledger by closing it, then store a webhook
        self.node.ledger.close()
        result = self.node.handle_webhook("ziman", {}, b"{}")
        self.assertTrue(result["ok"])   # inbox accepted despite ledger fail
        obs = self.node.owner_observability()
        self.assertEqual(obs.get("inbox_ledger_gaps"), 1)


if __name__ == "__main__":
    unittest.main()


class TestConnectorMetricsWired(unittest.TestCase):
    """ConnectorMetrics is wired: handle_webhook records, observability reads."""

    def setUp(self):
        self.dir = temp_dir(self)
        from ofn.adapters.ledger import Ledger
        from ofn.adapters.outbox import Outbox
        from ofn.adapters.facts import FactStore
        from ofn.adapters.packloader import load_dir
        from ofn.adapters.connector_metrics import ConnectorMetrics
        from ofn.adapters.inbound_rate import InboundRateLimiter
        from ofn.kernel.quota import NodeQuota
        from ofn.kernel.tenancy import TenantRegistry
        from ofn.node import Node

        packs_dir = os.path.join(self.dir, "packs")
        os.makedirs(packs_dir)
        with open(os.path.join(packs_dir, "ziman.yaml"), "w") as f:
            f.write(
                "tenant: ziman\n"
                "capacity_units_per_week: 6\n"
                "required_facts:\n"
                "  dummy_fact: owner_confirmed\n"
                "gates: []\n"
                "risk_overrides:\n"
                "  dummy_action: green\n"
                "quota_share: 0.5\n"
            )

        inbox = MarketingInbox(os.path.join(self.dir, "inbox.sqlite"))
        registry = TenantRegistry(load_dir(packs_dir))
        self.node = Node(
            registry=registry,
            quota=NodeQuota(estimated_capacity_tokens=1_000_000,
                            utilisation=1.0, shares={"ziman": 0.5}),
            ledger=Ledger(os.path.join(self.dir, "ledger.sqlite")),
            facts=FactStore(os.path.join(self.dir, "facts.sqlite")),
            outbox=Outbox(os.path.join(self.dir, "outbox.sqlite")),
            now_epoch_s=lambda: 1_785_000_000,
            now_iso=lambda: NOW_ISO,
            inbox=inbox,
            rate_limiter=InboundRateLimiter(max_requests=100,
                                            window_seconds=60),
            connector_metrics=ConnectorMetrics(),
        )
        self.addCleanup(self.node.close)

    def test_webhook_records_inbound_and_processed(self):
        result = self.node.handle_webhook("ziman", {}, b"{}")
        self.assertTrue(result["ok"])
        obs = self.node.owner_observability()
        snap = obs.get("connectors", {}).get("default", {})
        self.assertEqual(snap.get("inbound"), 1)
        self.assertEqual(snap.get("processed"), 1)

    def test_rejected_webhook_records_rejected(self):
        self.node.handle_webhook("nonexistent", {}, b"{}")
        obs = self.node.owner_observability()
        snap = obs.get("connectors", {}).get("default", {})
        self.assertEqual(snap.get("rejected"), 1)

    def test_rate_limited_records_rejected(self):
        node = self.node
        # Override limiter with tiny cap
        from ofn.adapters.inbound_rate import InboundRateLimiter
        node.rate_limiter = InboundRateLimiter(max_requests=1,
                                               window_seconds=60)
        node.handle_webhook("ziman", {}, b"{}")
        node.handle_webhook("ziman", {}, b"{}")  # second → 429
        obs = node.owner_observability()
        snap = obs.get("connectors", {}).get("default", {})
        self.assertEqual(snap.get("inbound"), 1)
        self.assertGreaterEqual(snap.get("rejected", 0), 1)
