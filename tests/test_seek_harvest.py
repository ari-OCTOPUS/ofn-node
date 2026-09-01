"""Seek harvester tests — pure over fixture HTML (no network)."""
from __future__ import annotations

import unittest

from ofn.agents.seek_harvest import HarvestError, cycle, harvest, parse_jobs

FIXTURE = """
<div data-automation="jobTitle">Painter</div>
<div data-automation="jobLocation">Sydney NSW</div>
<div data-automation="jobTitle">Professional Painter, Above Award Pay</div>
<div data-automation="jobLocation">Wahroonga, Sydney NSW</div>
<div data-automation="jobTitle">Accountant</div>
<div data-automation="jobLocation">Sydney NSW</div>
<div data-automation="jobTitle">Painter and Decorator</div>
<div data-automation="jobLocation">Sydney NSW</div>
<div data-automation="jobTitle">IT Consultant</div>
<div data-automation="jobLocation">Sydney NSW</div>
"""


class TestSeekHarvest(unittest.TestCase):
    def test_parsing_extracts_titles_and_locations(self):
        jobs = parse_jobs(FIXTURE)
        self.assertEqual(len(jobs), 5)
        self.assertEqual(jobs[0]["title"], "Painter")
        self.assertEqual(jobs[1]["location"], "Wahroonga, Sydney NSW")

    def test_painting_filter_keeps_only_relevant(self):
        leads = harvest(FIXTURE)
        titles = [l["name"] for l in leads]
        self.assertIn("Painter", titles)
        self.assertIn("Professional Painter, Above Award Pay", titles)
        self.assertIn("Painter and Decorator", titles)
        self.assertNotIn("Accountant", titles)
        self.assertNotIn("IT Consultant", titles)

    def test_cycle_dedup_and_notify(self):
        store, notifications = set(), []

        def create(hit):
            store.add(hit["lead_id"])
            return {"ok": True}

        def notify(rid, kind, detail):
            notifications.append(rid)
            return True

        out1 = cycle(lambda: set(store), create, notify,
                     fetch=lambda: FIXTURE)
        self.assertEqual(out1["status"], "DONE")
        self.assertEqual(out1["new"], 3)
        self.assertEqual(len(notifications), 3)

        out2 = cycle(lambda: set(store), create, notify,
                     fetch=lambda: FIXTURE)   # same feed: all deduped
        self.assertEqual(out2["new"], 0)
        self.assertEqual(len(notifications), 3)

    def test_feed_failure_parks(self):
        def boom():
            raise HarvestError("seek fetch failed after 2: timeout")

        out = cycle(lambda: set(), lambda h: {"ok": True}, None,
                    fetch=boom)
        self.assertEqual(out["status"], "PARKED")
        self.assertEqual(out["new"], 0)

    def test_lead_id_deterministic(self):
        leads = harvest(FIXTURE)
        ids = [l["lead_id"] for l in leads]
        self.assertEqual(len(ids), len(set(ids)), "ids must be unique")


if __name__ == "__main__":
    unittest.main()
