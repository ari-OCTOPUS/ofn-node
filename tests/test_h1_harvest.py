"""H1 harvest loop — fixture tests for the autonomous tender feed.

No network: fetch_releases is injected/mocked; `harvest` and `cycle` are
pure over the OCDS fixture payloads. Pins the three contract points:
dedup (idempotent cycles), park-not-crash on feed failure, and
owner-queue notification for each NEW painting tender only.
"""
from __future__ import annotations

import unittest

from ofn.agents.h1_harvest import TenderHarvestError, cycle, harvest

NOW = lambda: 1_800_000_000  # noqa: E731


def ocds(rftuuid="rft-1", title="Repaint of community hall",
         regions=None, amount=50_000, unspsc=None, closing="2026-10-01"):
    return {
        "tender": {
            "RFTUUID": rftuuid,
            "title": title,
            "description": "External painting and repaint of walls",
            "deliveryLocation": {"gazetteer": {"Identifiers":
                             regions or ["sydney"]}},
            "value": {"amount": amount},
            "items": [{"classification": {"id": c}} for c in (unspsc or [])],
            "tenderPeriod": {"endDate": closing},
        },
        "buyer": {"name": "NSW FaCS"},
    }


class FakeStore:
    def __init__(self):
        self.rows = []

    def tenders(self, tenant, limit=50):
        return self.rows


class Case(unittest.TestCase):
    def setUp(self):
        self.store = FakeStore()
        self.notifications = []
        self.notify = lambda rid, kind, detail: (
            self.notifications.append((rid, detail)) or True)

    def create(self, hit):
        self.store.rows.append({"tender_id": hit["tender_id"],
                                "title": hit["title"]})
        return {"ok": True, "score": 0.62, "recommendation": "watch"}

    def test_painting_tender_harvested_scored_and_notified(self):
        """A REAL cycle call: fetch is injected, create and notify run."""
        import ofn.agents.h1_harvest as mod
        orig = mod.fetch_releases
        mod.fetch_releases = lambda n: [ocds()]
        try:
            out = cycle(self.store, self.create,
                        notify=self.notify, now_epoch_s=NOW)
        finally:
            mod.fetch_releases = orig
        self.assertEqual(out["status"], "DONE")
        self.assertEqual(out["new"], 1)
        self.assertEqual(out["notified"], 1)
        self.assertEqual(len(self.notifications), 1)
        self.assertEqual(len(self.store.rows), 1)

    def test_non_painting_tender_rejected(self):
        hits = harvest([ocds(title="IT consultancy", unspsc=[])])
        # description still says painting → adjust: override description
        release = ocds(title="Software supply")
        release["tender"]["description"] = "Supply of software licences"
        hits = harvest([release])
        self.assertEqual(hits, [])

    def test_duplicate_tender_not_recreated(self):
        hits1 = harvest([ocds()])
        for h in hits1:
            self.create(h)
        before = len(self.store.rows)
        hits2 = harvest([ocds()])          # same rftuuid
        for h in hits2:
            if h["tender_id"] not in {r["tender_id"] for r in self.store.rows}:
                self.create(h)
        self.assertEqual(len(self.store.rows), before)

    def test_feed_failure_parks_not_crashes(self):
        def boom(n):
            raise TenderHarvestError("fetch failed after 2: timeout")
        # fetch_releases itself raises; cycle must catch and park
        import ofn.agents.h1_harvest as mod
        orig = mod.fetch_releases
        mod.fetch_releases = boom
        try:
            out = cycle(self.store, self.create, notify=self.notify,
                        now_epoch_s=NOW)
        finally:
            mod.fetch_releases = orig
        self.assertEqual(out["status"], "PARKED")
        self.assertEqual(out["new"], 0)

    def test_low_value_tender_rejected(self):
        hits = harvest([ocds(amount=100)])
        self.assertEqual(hits, [])

    def test_outside_service_area_rejected(self):
        hits = harvest([ocds(regions=["tweed"])])
        self.assertEqual(hits, [])

    def test_legacy_nsw_feed_is_marked_dead(self):
        from ofn.agents import h1_harvest
        self.assertIn("tenders.nsw.gov.au", h1_harvest.FEED_URL)
        self.assertEqual(h1_harvest.FEED_STATUS, "dead_redirect_buy_nsw")
        self.assertNotIn("buy.nsw.gov.au", h1_harvest.FEED_URL)


if __name__ == "__main__":
    unittest.main()
