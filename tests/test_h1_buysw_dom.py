"""H1 buy.nsw DOM-batch ingest — fixture tests for the extension bridge.

No network. The batch fixtures mirror EXACTLY what the Chrome extension's
mapping.js emits (schema "buynsw-harvest-batch/1", canonical record keys,
absent fields absent — not filled with placeholders), so a drift on either
side of the bridge fails here first.

Pins the contract points:
  - valid painting record → accepted, scored, stored once (idempotent)
  - same gates as the dead API path: non-painting / low-value /
    outside-region records are rejected by the same h1_buysw filter
  - dedup within the batch and against the store
  - malformed batches fail closed: REJECTED before any write
  - honest accounting: records == accepted + all rejection counters
"""
from __future__ import annotations

import os
import shutil
import tempfile
import unittest

from ofn.adapters.lead_store import LeadStore
from ofn.agents.h1_buysw_dom import BATCH_SCHEMA, dom_to_parsed, ingest_batch


def ext_record(**over):
    """One record exactly as mapping.js normalizeRecord() emits it."""
    rec = {
        "notice_uuid": "1f0e3dad-9946-4c2b-8f7e-9a1b2c3d4e5f",
        "title": "Repaint of community hall - external walls",
        "buyer_name": "NSW FaCS",
        "location_text": "Sydney",
        "closing_at": "02 Oct 2026 2:00 pm",
        "amount_aud": 50000.0,
        "detail_url": "https://www.buy.nsw.gov.au/notices/1f0e3dad-9946-4c2b-8f7e-9a1b2c3d4e5f",
        "raw_text": "External painting and repaint of walls. Estimated value: $50,000. Closing 02 Oct 2026.",
        "captured_at": "2026-09-02T06:18:00.000Z",
    }
    rec.update(over)
    return rec


def ext_batch(records):
    """Wrapper exactly as background.js buildBatch() emits it."""
    return {
        "schema": BATCH_SCHEMA,
        "captured_at": "2026-09-02T06:18:00.000Z",
        "capture_url": "https://www.buy.nsw.gov.au/opportunity/search?event=public.RFT.list",
        "records": records,
    }


class Case(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp(prefix="ofn-buysw-dom-")
        self.store = LeadStore(os.path.join(self.directory, "painting.sqlite"))

    def tearDown(self):
        self.store.close()
        shutil.rmtree(self.directory, ignore_errors=True)

    def stored_ids(self):
        return {t["tender_id"] for t in self.store.tenders("lead", limit=500)}

    def test_painting_record_accepted_scored_stored(self):
        out = ingest_batch(ext_batch([ext_record()]), self.store)
        self.assertEqual(out["status"], "DONE")
        self.assertEqual(out["accepted"], 1)
        self.assertEqual(out["records"], 1)
        self.assertEqual(
            out["created"], ["buy_nsw_dom:1f0e3dad-9946-4c2b-8f7e-9a1b2c3d4e5f"])
        self.assertEqual(len(self.stored_ids()), 1)

    def test_reingest_same_batch_is_idempotent(self):
        batch = ext_batch([ext_record()])
        first = ingest_batch(batch, self.store)
        second = ingest_batch(batch, self.store)
        self.assertEqual(first["accepted"], 1)
        self.assertEqual(second["accepted"], 0)
        self.assertEqual(second["rejected_dup"], 1)
        self.assertEqual(len(self.stored_ids()), 1)

    def test_stored_record_carries_owner_upload_and_unverified(self):
        ingest_batch(ext_batch([ext_record()]), self.store)
        row = self.store.tenders("lead", limit=10)[0]
        self.assertEqual(row["access_mode"], "owner_upload")
        self.assertEqual(row["evidence_status"], "unverified")
        self.assertEqual(row["source"], "buy_nsw_dom")
        self.assertIn("score", row)

    def test_non_painting_rejected_by_shared_filter(self):
        out = ingest_batch(ext_batch(
            [ext_record(title="Supply of software licences",
                        raw_text="Supply of software licences and support.")]),
            self.store)
        self.assertEqual(out["status"], "DONE")
        self.assertEqual(out["accepted"], 0)
        self.assertEqual(out["rejected_filter"], 1)
        self.assertEqual(self.stored_ids(), set())

    def test_low_value_rejected_by_shared_filter(self):
        out = ingest_batch(
            ext_batch([ext_record(amount_aud=100.0)]), self.store)
        self.assertEqual(out["accepted"], 0)
        self.assertEqual(out["rejected_filter"], 1)

    def test_outside_region_rejected_by_shared_filter(self):
        out = ingest_batch(
            ext_batch([ext_record(location_text="Tweed Heads")]), self.store)
        self.assertEqual(out["accepted"], 0)
        self.assertEqual(out["rejected_filter"], 1)

    def test_paint_product_rejected_by_shared_filter(self):
        out = ingest_batch(ext_batch(
            [ext_record(title="Bulk paint supply",
                        raw_text="Supply of paints and primers in bulk.")]),
            self.store)
        self.assertEqual(out["accepted"], 0)
        self.assertEqual(out["rejected_filter"], 1)

    def test_duplicate_within_batch_counted_not_recreated(self):
        dup = ext_record()
        out = ingest_batch(ext_batch([dup, dict(dup)]), self.store)
        self.assertEqual(out["accepted"], 1)
        self.assertEqual(out["rejected_dup"], 1)
        self.assertEqual(len(self.stored_ids()), 1)

    def test_record_without_title_is_invalid_not_accepted(self):
        rec = ext_record()
        rec["title"] = ""
        out = ingest_batch(ext_batch([rec]), self.store)
        self.assertEqual(out["accepted"], 0)
        self.assertEqual(out["rejected_invalid"], 1)

    def test_record_without_uuid_but_with_url_derives_identity(self):
        rec = ext_record()
        rec.pop("notice_uuid")
        parsed = dom_to_parsed(rec)
        self.assertIsNotNone(parsed)
        self.assertIn("1f0e3dad", parsed["tender_id"])

    def test_accounting_sums_to_records(self):
        out = ingest_batch(ext_batch([
            ext_record(),                                          # accept
            ext_record(notice_uuid="aaaa1111-2222-3333-4444-555566667777",
                       title="IT consultancy",
                       raw_text="Software services procurement."),   # filter
            ext_record(),                                          # dup
            {"no_title": True},                                    # invalid
        ]), self.store)
        self.assertEqual(out["records"], 4)
        self.assertEqual(
            out["records"],
            out["accepted"] + out["rejected_filter"]
            + out["rejected_dup"] + out["rejected_invalid"])
        self.assertEqual(out["accepted"], 1)
        self.assertEqual(out["rejected_filter"], 1)
        self.assertEqual(out["rejected_dup"], 1)
        self.assertEqual(out["rejected_invalid"], 1)

    # --- fail-closed on malformed batches: nothing is ever written ---

    def test_wrong_schema_rejected_before_writes(self):
        bad = ext_batch([ext_record()])
        bad["schema"] = "buynsw-harvest-batch/2"
        out = ingest_batch(bad, self.store)
        self.assertEqual(out["status"], "REJECTED")
        self.assertEqual(self.stored_ids(), set())

    def test_non_object_payload_rejected(self):
        for bad in (None, [], "x", 42):
            out = ingest_batch(bad, self.store)
            self.assertEqual(out["status"], "REJECTED")

    def test_records_not_a_list_rejected(self):
        out = ingest_batch({"schema": BATCH_SCHEMA, "records": "nope"},
                           self.store)
        self.assertEqual(out["status"], "REJECTED")

    def test_empty_records_rejected(self):
        out = ingest_batch({"schema": BATCH_SCHEMA, "records": []}, self.store)
        self.assertEqual(out["status"], "REJECTED")

    def test_oversized_batch_rejected(self):
        out = ingest_batch({"schema": BATCH_SCHEMA,
                            "records": [ext_record()] * 5001}, self.store)
        self.assertEqual(out["status"], "REJECTED")


if __name__ == "__main__":
    unittest.main()
