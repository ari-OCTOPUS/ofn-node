"""Demand-harvester tests — offline, no network, 16 cases.

Pins the three hard gates: supply-side rejection (with a permanent
negative control), 403-never-retries, and non-compensatory scoring.
"""
from __future__ import annotations

import unittest

from ofn.agents.demand_harvest import (
    HarvestError, cycle, fetch_json, is_supply_side, parse_ocds_release,
    score_demand, strip_leading_space,
)


def ocds(rftuuid="rft-1", title="External repaint of community hall",
         desc="External painting and repaint of walls", amount=50_000,
         buyer="NSW FaCS", regions=("sydney",), unspsc=("72151300",),
         closing="2026-10-01T23:59:59Z", employment_type=None):
    t = {
        "RFTUUID": rftuuid,
        "title": title,
        "description": desc,
        "deliveryLocation": {"gazetteer": {"Identifiers": list(regions)}},
        "value": {"amount": amount},
        "items": [{"classification": {"id": c}} for c in unspsc],
        "tenderPeriod": {"endDate": closing},
    }
    if employment_type:
        t["employmentType"] = employment_type
    return {"tender": t, "buyer": {"name": buyer}}


class TestT1SupplySideGate(unittest.TestCase):
    def test_job_ad_rejected_via_salary(self):
        r = ocds(title="Painter wanted - great salary", amount=None,
                 buyer=None)
        self.assertTrue(is_supply_side(parse_ocds_release(r)))

    def test_job_ad_rejected_via_employment_type(self):
        r = ocds(employment_type="full_time")
        self.assertTrue(is_supply_side(parse_ocds_release(r)))

    def test_job_ad_rejected_via_hiring_verb(self):
        r = ocds(desc="We are hiring experienced painters ASAP")
        self.assertTrue(is_supply_side(parse_ocds_release(r)))

    def test_pure_demand_record_passes(self):
        self.assertFalse(is_supply_side(parse_ocds_release(ocds())))

    def test_negative_control_spray_painter_hiring(self):
        """PERMANENT NEGATIVE CONTROL: if this ever returns False the
        direction gate has drifted and every lead is suspect."""
        r = ocds(title="Spray Painter",
                 desc="We are hiring spray painters for our workshop",
                 amount=None, buyer=None)
        parsed = parse_ocds_release(r)
        self.assertTrue(is_supply_side(parsed),
                        "DIRECTION GATE DRIFT: supply-side ad accepted")


class TestT2FetchPolicy(unittest.TestCase):
    def test_403_raises_immediately(self):
        import urllib.error
        import urllib.request
        from unittest import mock

        def urlopen_403(req, timeout):
            raise urllib.error.HTTPError(
                req.full_url, 403, "Forbidden", {}, None)

        with mock.patch.object(urllib.request, "urlopen", urlopen_403):
            with self.assertRaises(HarvestError) as ctx:
                fetch_json("https://example.gov/api")
        self.assertIn("authorised access", str(ctx.exception))

    def test_304_returns_none_with_etag(self):
        import urllib.error
        import urllib.request
        from unittest import mock

        def urlopen_304(req, timeout):
            raise urllib.error.HTTPError(
                req.full_url, 304, "Not Modified", {}, None)

        with mock.patch.object(urllib.request, "urlopen", urlopen_304):
            body, etag = fetch_json("https://example.gov/api",
                                    etag='"abc123"')
        self.assertIsNone(body)
        self.assertEqual(etag, '"abc123"')


class TestT3Parser(unittest.TestCase):
    def test_missing_rftuuid_returns_none(self):
        self.assertIsNone(parse_ocds_release({"tender": {"title": "x"}}))

    def test_missing_title_returns_none(self):
        self.assertIsNone(
            parse_ocds_release({"tender": {"RFTUUID": "r"}}))

    def test_empty_fields_are_none_not_error(self):
        r = {"tender": {"RFTUUID": "r1", "title": "t"},
             "buyer": {}}
        parsed = parse_ocds_release(r)
        self.assertIsNone(parsed["buyer_name"])
        self.assertEqual(parsed["regions"], [])
        self.assertIsNone(parsed["amount"])

    def test_leading_space_stripped_once(self):
        self.assertEqual(strip_leading_space(" rft-123"), "rft-123")
        self.assertEqual(strip_leading_space("rft-123"), "rft-123")

    def test_non_string_buyer_name_to_none(self):
        r = ocds()
        r["buyer"]["name"] = 12345
        parsed = parse_ocds_release(r)
        self.assertIsNone(parsed["buyer_name"])


class TestT4NonCompensatoryScore(unittest.TestCase):
    def test_no_buyer_disclosure_is_hard_zero(self):
        r = ocds(amount=None, buyer=None)
        score = score_demand(parse_ocds_release(r))
        self.assertEqual(score["score"], 0.0)
        self.assertFalse(score["consent_ok"])

    def test_below_min_value_is_hard_zero(self):
        r = ocds(amount=100)
        score = score_demand(parse_ocds_release(r))
        self.assertEqual(score["score"], 0.0)
        self.assertFalse(score["capacity_ok"])

    def test_outside_service_area_is_hard_zero(self):
        r = ocds(regions=("tweed",))
        score = score_demand(parse_ocds_release(r))
        self.assertEqual(score["score"], 0.0)

    def test_valid_demand_scores_positive(self):
        score = score_demand(parse_ocds_release(ocds()))
        self.assertGreater(score["score"], 0.0)
        self.assertTrue(score["consent_ok"])
        self.assertTrue(score["capacity_ok"])

    def test_score_ceiling_1_5(self):
        r = ocds(amount=500_000, buyer="Big Dept",
                 regions=("sydney", "sydney"), unspsc=("72151300",) * 5,
                 closing="2027-06-01T00:00:00Z")
        score = score_demand(parse_ocds_release(r))
        self.assertLessEqual(score["score"], 1.5)


class TestT5Cycle(unittest.TestCase):
    def test_full_cycle_rejects_supply_creates_demand(self):
        import json
        feed = json.dumps({
            "releases": [
                ocds(title="Painter wanted - great pay", amount=None,
                     buyer=None),          # supply → rejected
                ocds(rftuuid="rft-2"),                            # demand
                ocds(rftuuid="rft-1"),                            # pre-existing
            ]
        })
        store = {"nsw_tender:rft-1"}                     # already known
        notified = []

        out = cycle(
            lambda url, etag="": (feed, '"e1"'),
            lambda: set(store),
            lambda lead: (store.add(lead["lead_id"]) or {"ok": True}),
            lambda rid, kind, d: notified.append(rid) or True)
        self.assertEqual(out["status"], "DONE")
        self.assertEqual(out["rejected_supply"], 1)
        self.assertEqual(out["new"], 1)
        self.assertEqual(len(notified), 1)

    def test_cycle_parks_on_403(self):
        def boom(url, etag=""):
            raise HarvestError("403 forbidden: get authorised")

        out = cycle(boom, lambda: set(), lambda l: {"ok": True})
        self.assertEqual(out["status"], "PARKED")

    def test_cycle_no_change_on_304(self):
        out = cycle(lambda url, etag="": (None, etag),
                    lambda: set(), lambda l: {"ok": True}, etag='"e"')
        self.assertEqual(out["status"], "NO_CHANGE")


if __name__ == "__main__":
    unittest.main()
