"""O5 — lead operationalisation: follow-ups, duplicates, hashes.

- follow-up due/overdue via next_action_at
- last_contacted_at recorded on contact
- duplicate warning via contact hashes (never raw contact in the hash)
- phone/email update re-hashes
"""

from __future__ import annotations

import os
import unittest

from ofn.adapters.lead_store import LeadStore

from tests.tmpdir import temp_dir

NOW = "2026-08-10T12:00:00Z"
LATER = "2026-08-15T12:00:00Z"


class TestLeadFollowUps(unittest.TestCase):
    def setUp(self):
        self.dir = temp_dir(self)
        self.store = LeadStore(os.path.join(self.dir, "lead.sqlite"))
        self.addCleanup(self.store.close)
        self.store.create_lead("lead", {
            "customer_name": "علی", "phone": "0412345678",
            "source": "test", "source_ref": "a1",
        }, now_iso=NOW)

    def _lead_id(self):
        return self.store.list_leads("lead")[0]["lead_id"]

    def test_set_follow_up(self):
        lid = self._lead_id()
        ok = self.store.set_follow_up("lead", lid, due_at=LATER,
                                      action="تماس دوباره", now_iso=NOW)
        self.assertTrue(ok)
        lead = self.store.get("lead", lid)
        self.assertEqual(lead["next_action_at"], LATER)
        self.assertEqual(lead["next_action"], "تماس دوباره")

    def test_follow_ups_due_filters(self):
        lid = self._lead_id()
        self.store.set_follow_up("lead", lid, due_at=NOW, now_iso=NOW)
        due = self.store.follow_ups_due("lead", before_iso=NOW)
        self.assertEqual(len(due), 1)
        future = self.store.follow_ups_due("lead", before_iso="2026-08-01")
        self.assertEqual(len(future), 0)

    def test_touch_contact_records_time(self):
        lid = self._lead_id()
        self.store.touch_contact("lead", lid, at_iso=NOW)
        lead = self.store.get("lead", lid)
        self.assertEqual(lead["last_contacted_at"], NOW)


class TestLeadDuplicates(unittest.TestCase):
    def setUp(self):
        self.dir = temp_dir(self)
        self.store = LeadStore(os.path.join(self.dir, "lead.sqlite"))
        self.addCleanup(self.store.close)
        self.store.create_lead("lead", {
            "customer_name": "علی", "phone": "0412345678",
            "source": "test", "source_ref": "a1",
        }, now_iso=NOW)

    def test_duplicate_detected_by_phone(self):
        # Same phone with different formatting → same hash → duplicate.
        self.store.create_lead("lead", {
            "customer_name": "علی دیگر", "phone": "+61 412 345 678",
            "source": "test", "source_ref": "a2",
        }, now_iso=NOW)
        leads = self.store.list_leads("lead")
        dupes = self.store.duplicate_candidates("lead", leads[0]["lead_id"])
        self.assertEqual(len(dupes), 1)

    def test_no_duplicate_for_different_phone(self):
        self.store.create_lead("lead", {
            "customer_name": "مریم", "phone": "0999999999",
            "source": "test", "source_ref": "a3",
        }, now_iso=NOW)
        leads = self.store.list_leads("lead")
        dupes = self.store.duplicate_candidates("lead", leads[0]["lead_id"])
        self.assertEqual(len(dupes), 0)

    def test_hash_never_contains_raw_contact(self):
        lid = self.store.list_leads("lead")[0]["lead_id"]
        lead = self.store.get("lead", lid)
        h = lead["contact_phone_hash"]
        self.assertEqual(len(h), 16)
        self.assertNotIn("0412345678", h)

    def test_update_rehashes(self):
        self.store.create_lead("lead", {
            "customer_name": "دیگر", "phone": "0111111111",
            "source": "test", "source_ref": "a4",
        }, now_iso=NOW)
        lid = self.store.list_leads("lead")[0]["lead_id"]
        self.store.update_lead("lead", lid, {"phone": "0222222222"},
                               now_iso=NOW)
        lead = self.store.get("lead", lid)
        self.assertEqual(lead["phone"], "0222222222")
        self.assertEqual(len(lead["contact_phone_hash"]), 16)


class TestOpsColumnsMigration(TestLeadFollowUps):
    def test_new_columns_exist(self):
        cols = {r[1] for r in self.store._conn.execute(
            "PRAGMA table_info(painting_leads)")}
        for col in ("next_action_at", "last_contacted_at", "outcome_reason",
                    "contact_phone_hash", "contact_email_hash"):
            self.assertIn(col, cols)


if __name__ == "__main__":
    unittest.main()
