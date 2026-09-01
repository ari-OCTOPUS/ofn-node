"""NSW OCP registry harvester tests — offline, fixture-based."""
from __future__ import annotations

import gzip
import json
import unittest

from ofn.agents.nsw_ocp_harvest import (
    extract_buyer_leads, harvest, is_painting_award, is_supply_side,
)


def release(buyer_name="HealthShare NSW", amount=163836.2,
            desc="Repainting Works on Helicopter Landing Site",
            email="contact@health.nsw.gov.au", person="John Smith",
            phone="02 1234 5678"):
    return {
        "ocid": "ocds-43qwtd-CN-TEST-001",
        "awards": [{
            "buyer": {
                "name": buyer_name,
                "contactPoint": {
                    "name": person, "email": email,
                    "telephone": phone,
                    "address": {"region": "NSW"},
                },
            },
            "items": [{
                "description": f"<p>{desc}</p>",
                "classification": {"id": "72151300", "scheme": "UNSPSC"},
            }],
            "value": {"amount": amount, "currency": "AUD"},
            "title": "NBM51620779",
            "status": "active",
        }],
    }


class TestPaintingDetection(unittest.TestCase):
    def test_painting_award_detected(self):
        self.assertTrue(is_painting_award(release()))

    def test_non_painting_award_rejected(self):
        r = release(desc="IT consultancy and software supply")
        self.assertFalse(is_painting_award(r))

    def test_awards_are_always_demand_side(self):
        self.assertFalse(is_supply_side(release()))


class TestBuyerExtraction(unittest.TestCase):
    def test_buyer_contact_extracted(self):
        leads = extract_buyer_leads([release()])
        self.assertEqual(len(leads), 1)
        lead = leads[0]
        self.assertEqual(lead["name"], "HealthShare NSW")
        self.assertEqual(lead["email"], "contact@health.nsw.gov.au")
        self.assertEqual(lead["contact_person"], "John Smith")
        self.assertEqual(lead["phone"], "02 1234 5678")

    def test_multiple_awards_same_buyer_aggregated(self):
        r1 = release(amount=100000)
        r2 = release(amount=50000)
        leads = extract_buyer_leads([r1, r2])
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]["total_awarded_aud"], 150000)
        self.assertEqual(leads[0]["contract_count"], 2)

    def test_different_buyers_separate_leads(self):
        leads = extract_buyer_leads([
            release(buyer_name="Dept of Education"),
            release(buyer_name="Transport for NSW", amount=900000),
        ])
        self.assertEqual(len(leads), 2)
        self.assertEqual(leads[0]["name"], "Transport for NSW")  # higher total first

    def test_buyer_without_name_skipped(self):
        r = release(buyer_name="")
        leads = extract_buyer_leads([r])
        self.assertEqual(len(leads), 0)

    def test_html_stripped_from_description(self):
        leads = extract_buyer_leads([release(
            desc="<p><b>Repainting</b> of walls</p>")])
        self.assertNotIn("<", leads[0]["last_work_description"])
        self.assertIn("Repainting", leads[0]["last_work_description"])


class TestHarvestFromBytes(unittest.TestCase):
    def test_full_harvest_from_gzipped_jsonl(self):
        releases = [release(), release(buyer_name="Education Dept",
                                       amount=500000)]
        jsonl = "\n".join(json.dumps(r) for r in releases)
        gz = gzip.compress(jsonl.encode())
        leads = harvest(gz)
        self.assertEqual(len(leads), 2)
        self.assertEqual(leads[0]["name"], "Education Dept")  # higher first

    def test_corrupt_lines_skipped(self):
        jsonl = (json.dumps(release()) + "\nNOT-JSON\n" +
                 json.dumps(release(buyer_name="Second Buyer")))
        gz = gzip.compress(jsonl.encode())
        leads = harvest(gz)
        self.assertEqual(len(leads), 2)

    def test_empty_input_returns_empty(self):
        self.assertEqual(harvest(gzip.compress(b"")), [])


class TestLeadShape(unittest.TestCase):
    def test_lead_has_all_required_fields(self):
        leads = extract_buyer_leads([release()])
        lead = leads[0]
        for field in ("lead_id", "channel", "name", "email",
                      "contact_person", "phone", "total_awarded_aud",
                      "contract_count", "status", "source_url", "notes"):
            self.assertIn(field, lead, f"missing field: {field}")
        self.assertEqual(lead["status"], "warm_lead")
        self.assertEqual(lead["channel"], "nsw_ocp_registry")


if __name__ == "__main__":
    unittest.main()
