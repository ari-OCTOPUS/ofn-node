"""H1 buy.nsw DOM-batch ingest — fixture tests for the extension bridge.

No network. Fixtures mirror EXACTLY what the producers emit:
  - v1: mapping.js v1 canonical records under {"schema": ...} wrappers
  - v2: the recovered pack's mapping.normalize() records under the
    background worker's {"source": "buysw_web", "count": N} export wrapper
(absent fields absent — not filled with placeholders), so drift on either
side of the bridge fails here first.

Pins the contract points:
  - valid painting record → accepted, scored, stored once (idempotent)
  - same gates as the dead API path: non-painting / low-value /
    outside-region records are rejected by the same h1_buysw rules
  - dedup within the batch and against the store
  - award (CAN) records also mint a warm buyer lead; opportunities never do
  - malformed batches/exports fail closed: REJECTED before any write
  - honest accounting: records == accepted + all rejection counters
"""
from __future__ import annotations

import os
import shutil
import tempfile
import unittest

from ofn.adapters.lead_store import LeadStore
from ofn.agents.h1_buysw_dom import (
    BATCH_SCHEMA, _normalize, ingest_batch,
)


def v1_record(**over):
    """One record exactly as the v1 mapping.js normalizeRecord() emitted."""
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


def v1_batch(records):
    return {
        "schema": BATCH_SCHEMA,
        "captured_at": "2026-09-02T06:18:00.000Z",
        "capture_url": "https://www.buy.nsw.gov.au/opportunity/search?event=public.RFT.list",
        "records": records,
    }


def v2_record(**over):
    """One record exactly as the pack's mapping.js normalize() emits it
    (keys, ordering and absences mirrored from the recovered source)."""
    rec = {
        "tender_id": "lead:tender:buysw:AAAA111122223333444455556666",
        "channel": "buysw_web",
        "kind": "opportunity",
        "title": "External Painting Services - Bankstown Public School",
        "buyer_name": "NSW Department of Education",
        "description": "Repainting of classroom blocks, external painting.",
        "location": "South West Sydney",
        "category": "",
        "closing_at": "2026-10-01T00:00:00Z",
        "published_at": "2026-09-01T00:00:00Z",
        "amount_text": "$180,000",
        "supplier_name": "",
        "contact_email": "",
        "contact_phone": "",
        "abn": "",
        "uuid": "AAAA111122223333444455556666",
        "source": "buy.nsw.gov.au",
        "source_url": "https://buy.nsw.gov.au/notices/AAAA1111-2222-3333-4444-55556666",
        "access_mode": "browser_session",
        "evidence_status": "unverified",
        "status": "received",
        "_painting_hint": True,
        "_in_service_area": True,
        "_scraped_at": "2026-09-02T09:00:00.000Z",
        "raw": {},
    }
    rec.update(over)
    return rec


def v2_export(records):
    """Wrapper exactly as the pack's background.js download() emits it."""
    return {
        "source": "buysw_web",
        "count": len(records),
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

    # ---------------- v1 wrapper (versioned batch) ----------------

    def test_painting_record_accepted_scored_stored(self):
        out = ingest_batch(v1_batch([v1_record()]), self.store)
        self.assertEqual(out["status"], "DONE")
        self.assertEqual(out["accepted"], 1)
        self.assertEqual(out["records"], 1)
        self.assertEqual(
            out["created"], ["buy_nsw_dom:1f0e3dad-9946-4c2b-8f7e-9a1b2c3d4e5f"])
        self.assertEqual(len(self.stored_ids()), 1)

    def test_reingest_same_batch_is_idempotent(self):
        batch = v1_batch([v1_record()])
        first = ingest_batch(batch, self.store)
        second = ingest_batch(batch, self.store)
        self.assertEqual(first["accepted"], 1)
        self.assertEqual(second["accepted"], 0)
        self.assertEqual(second["rejected_dup"], 1)
        self.assertEqual(len(self.stored_ids()), 1)

    def test_stored_record_carries_owner_upload_and_unverified(self):
        ingest_batch(v1_batch([v1_record()]), self.store)
        row = self.store.tenders("lead", limit=10)[0]
        self.assertEqual(row["access_mode"], "owner_upload")
        self.assertEqual(row["evidence_status"], "unverified")
        self.assertEqual(row["source"], "buysw_web")
        self.assertIn("score", row)

    def test_record_without_uuid_but_with_url_derives_identity(self):
        rec = v1_record()
        rec.pop("notice_uuid")
        norm = _normalize(rec)
        self.assertIsNotNone(norm)
        self.assertIn("1f0e3dad", norm["tender_id"])

    # ---------------- v2 wrapper (extension export) ----------------

    def test_v2_export_accepted(self):
        out = ingest_batch(v2_export([v2_record()]), self.store)
        self.assertEqual(out["status"], "DONE")
        self.assertEqual(out["accepted"], 1)
        self.assertEqual(out["records"], 1)
        self.assertEqual(
            out["created"], ["lead:tender:buysw:AAAA111122223333444455556666"])
        row = self.store.tenders("lead", limit=10)[0]
        self.assertEqual(row["source"], "buysw_web")
        self.assertEqual(row["access_mode"], "owner_upload")
        self.assertIn("score", row)

    def test_v2_export_count_mismatch_rejected_before_writes(self):
        bad = v2_export([v2_record(), v2_record(notice_uuid=None,
                                                 uuid="BBBB1")])
        bad["count"] = 5
        out = ingest_batch(bad, self.store)
        self.assertEqual(out["status"], "REJECTED")
        self.assertEqual(self.stored_ids(), set())

    def test_v2_amount_text_parsed_and_low_value_rejected(self):
        out = ingest_batch(v2_export([v2_record(amount_text="$50")]),
                           self.store)
        self.assertEqual(out["accepted"], 0)
        self.assertEqual(out["rejected_filter"], 1)

    def test_v2_out_of_area_rejected(self):
        out = ingest_batch(v2_export([v2_record(location="Broken Hill")]),
                           self.store)
        self.assertEqual(out["accepted"], 0)
        self.assertEqual(out["rejected_filter"], 1)

    def test_v2_no_location_passes_like_ocds_path(self):
        out = ingest_batch(v2_export([v2_record(location="")]), self.store)
        self.assertEqual(out["accepted"], 1)

    def test_v2_real_card_closing_normalized_to_iso(self):
        # Exact field as scraped from the real All-opportunities page:
        # "Closes: 21-Sep-2026 15:00" -> matchClosing keeps "21-Sep-2026 15:00".
        out = ingest_batch(
            v2_export([v2_record(closing_at="21-Sep-2026 15:00")]), self.store)
        self.assertEqual(out["accepted"], 1)
        row = self.store.tenders("lead", limit=10)[0]
        self.assertEqual(row["closing_at"], "2026-09-21T15:00+00:00")

    def test_v2_unparseable_closing_passed_through_untouched(self):
        out = ingest_batch(
            v2_export([v2_record(closing_at="see documents")]), self.store)
        self.assertEqual(out["accepted"], 1)
        row = self.store.tenders("lead", limit=10)[0]
        self.assertEqual(row["closing_at"], "see documents")

    # ---------------- award (CAN) → warm lead ----------------

    def test_v2_award_creates_tender_and_lead(self):
        rec = v2_record(
            kind="award", contact_email="procurement@det.nsw.gov.au",
            supplier_name="Acme Painting Pty Ltd", abn="12 345 678 901")
        out = ingest_batch(v2_export([rec]), self.store)
        self.assertEqual(out["accepted"], 1)
        self.assertEqual(out["leads_minted"], 1)
        leads = self.store.list_leads("lead")
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]["customer_name"], "NSW Department of Education")
        self.assertEqual(leads[0]["email"], "procurement@det.nsw.gov.au")

    def test_v2_opportunity_makes_no_lead(self):
        out = ingest_batch(v2_export([v2_record()]), self.store)
        self.assertEqual(out["leads_minted"], 0)
        self.assertEqual(self.store.list_leads("lead"), [])

    def test_v2_award_without_buyer_no_lead_but_tender_kept(self):
        out = ingest_batch(
            v2_export([v2_record(kind="award", buyer_name="")]), self.store)
        self.assertEqual(out["accepted"], 1)
        self.assertEqual(out["leads_minted"], 0)

    def test_pii_findings_surfaced(self):
        rec = v2_record(
            kind="award",
            description="Contact procurement@det.nsw.gov.au for documents.")
        out = ingest_batch(v2_export([rec]), self.store)
        self.assertEqual(out["accepted"], 1)
        self.assertGreaterEqual(out["pii_findings"], 1)

    # ---------------- shared filter rules ----------------

    def test_non_painting_rejected_by_shared_filter(self):
        out = ingest_batch(v2_export(
            [v2_record(title="Supply of software licences",
                       description="Supply of software licences and support.",
                       _painting_hint=False)]), self.store)
        self.assertEqual(out["status"], "DONE")
        self.assertEqual(out["accepted"], 0)
        self.assertEqual(out["rejected_filter"], 1)
        self.assertEqual(self.stored_ids(), set())

    def test_paint_product_rejected_by_shared_filter(self):
        out = ingest_batch(v2_export(
            [v2_record(title="Bulk paint supply",
                        description="Supply of paints and primers in bulk.")]),
            self.store)
        self.assertEqual(out["accepted"], 0)
        self.assertEqual(out["rejected_filter"], 1)

    def test_low_value_rejected_by_shared_filter(self):
        out = ingest_batch(v1_batch([v1_record(amount_aud=100.0)]), self.store)
        self.assertEqual(out["accepted"], 0)
        self.assertEqual(out["rejected_filter"], 1)

    def test_outside_region_rejected_by_shared_filter(self):
        out = ingest_batch(
            v1_batch([v1_record(location_text="Tweed Heads")]), self.store)
        self.assertEqual(out["accepted"], 0)
        self.assertEqual(out["rejected_filter"], 1)

    def test_duplicate_within_batch_counted_not_recreated(self):
        dup = v2_record()
        out = ingest_batch(v2_export([dup, dict(dup)]), self.store)
        self.assertEqual(out["accepted"], 1)
        self.assertEqual(out["rejected_dup"], 1)
        self.assertEqual(len(self.stored_ids()), 1)

    def test_record_without_title_is_invalid_not_accepted(self):
        rec = v2_record()
        rec["title"] = ""
        out = ingest_batch(v2_export([rec]), self.store)
        self.assertEqual(out["accepted"], 0)
        self.assertEqual(out["rejected_invalid"], 1)

    def test_accounting_sums_to_records(self):
        out = ingest_batch(v2_export([
            v2_record(),                                          # accept
            v2_record(tender_id="lead:tender:buysw:BBBB1", uuid="BBBB1",
                      title="IT consultancy",
                      description="Software services procurement.",
                      _painting_hint=False),                      # filter
            v2_record(),                                          # dup
            {"no_title": True},                                   # invalid
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

    # --- fail-closed on malformed wrappers: nothing is ever written ---

    def test_wrong_schema_rejected_before_writes(self):
        bad = v1_batch([v1_record()])
        bad["schema"] = "buynsw-harvest-batch/2"
        out = ingest_batch(bad, self.store)
        self.assertEqual(out["status"], "REJECTED")
        self.assertEqual(self.stored_ids(), set())

    def test_unknown_source_wrapper_rejected(self):
        out = ingest_batch({"source": "scrapeme", "records": [v1_record()]},
                           self.store)
        self.assertEqual(out["status"], "REJECTED")

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
                            "records": [v1_record()] * 5001}, self.store)
        self.assertEqual(out["status"], "REJECTED")


if __name__ == "__main__":
    unittest.main()
