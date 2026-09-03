"""Tests for H3 Strata Hub adapter.

Fixtures are real records pulled from the live NSW Strata Hub FeatureServer
on 2026-09-02 (Sydney LGA sample). Fully offline: fetch is injected.
"""
from datetime import datetime, timezone
import inspect
import unittest

from ofn.agents import h3_strata


# --- Real feature samples (from live FeatureServer, 2026-09-02) ---------------
FEATURE_SYDNEY = {
    "attributes": {
        "plannumber": 245,
        "registrationdate": -217641600000,  # ~1963
        "address": "8-10 BILLYARD AVENUE ELIZABETH BAY",
        "suburb": "ELIZABETH BAY",
        "lga": "SYDNEY",
        "lottotal": 53,
    }
}

FEATURE_NO_LOTS = {
    "attributes": {
        "plannumber": 999001,
        "registrationdate": None,
        "address": "1 TEST STREET",
        "suburb": "TESTVILLE",
        "lga": "WOLLONGONG",
        "lottotal": None,  # absent — must stay None, not 0
    }
}

FEATURE_OUT_OF_AREA = {
    "attributes": {
        "plannumber": 999002,
        "registrationdate": 1000000000000,  # ~2001
        "address": "5 FAR ROAD",
        "suburb": "TWEED HEADS",
        "lga": "TWEED",
        "lottotal": 12,
    }
}

FEATURE_NO_PLAN = {
    "attributes": {
        "registrationdate": 0,
        "address": "NO PLAN HERE",
        "lga": "SYDNEY",
    }
}

FEATURE_UNKNOWN_LGA = {
    "attributes": {
        "plannumber": 999003,
        "registrationdate": 0,
        "address": "7 MYSTERY LANE",
        "suburb": "",
        "lga": None,
        "lottotal": 4,
    }
}


class TestParseFeature(unittest.TestCase):
    def test_parses_real_sydney_record(self):
        rec = h3_strata.parse_feature(FEATURE_SYDNEY)
        self.assertIsNotNone(rec)
        self.assertEqual(rec["plan_number"], 245)
        self.assertEqual(rec["plan_label"], "SP245")
        self.assertEqual(rec["address"], "8-10 BILLYARD AVENUE ELIZABETH BAY")
        self.assertEqual(rec["suburb"], "ELIZABETH BAY")
        self.assertEqual(rec["lga"], "SYDNEY")
        self.assertEqual(rec["lots"], 53)
        self.assertEqual(rec["segment"], "strata")
        self.assertEqual(rec["tenant_id"], "lead")

    def test_deterministic_id_from_plan(self):
        rec = h3_strata.parse_feature(FEATURE_SYDNEY)
        self.assertEqual(rec["tender_id"], "lead:strata:245")

    def test_registration_year_from_epoch(self):
        rec = h3_strata.parse_feature(FEATURE_SYDNEY)
        self.assertEqual(rec["registration_year"], 1963)

    def test_pre1970_year_survives_windows_fromtimestamp_gap(self):
        # CI job 100305711881 (windows-latest, 2026-09-02T15:20:54Z):
        # datetime.fromtimestamp(-217641600) raises OSError on Windows.
        # The helper must still return 1963. POSIX hosts accept the same
        # instant; the contract is the year, not the OSError.
        ms = FEATURE_SYDNEY["attributes"]["registrationdate"]
        self.assertEqual(h3_strata._epoch_ms_to_year(ms), 1963)
        try:
            datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
        except OSError:
            pass  # expected on Windows; helper already returned 1963
        rec = h3_strata.parse_feature(FEATURE_SYDNEY)
        self.assertEqual(rec["registration_year"], 1963)

    def test_post1970_epoch_year(self):
        rec = h3_strata.parse_feature(FEATURE_OUT_OF_AREA)
        self.assertEqual(rec["registration_year"], 2001)

    def test_epoch_zero_is_1970(self):
        rec = h3_strata.parse_feature(FEATURE_UNKNOWN_LGA)
        self.assertEqual(rec["registration_year"], 1970)

    def test_missing_plan_returns_none(self):
        self.assertIsNone(h3_strata.parse_feature(FEATURE_NO_PLAN))

    def test_absent_lots_stays_none_not_zero(self):
        rec = h3_strata.parse_feature(FEATURE_NO_LOTS)
        self.assertIsNone(rec["lots"])  # never guessed to 0

    def test_absent_registration_stays_none(self):
        rec = h3_strata.parse_feature(FEATURE_NO_LOTS)
        self.assertIsNone(rec["registration_year"])

    def test_tenant_id_everywhere(self):
        for feat in (FEATURE_SYDNEY, FEATURE_NO_LOTS, FEATURE_OUT_OF_AREA):
            rec = h3_strata.parse_feature(feat)
            self.assertEqual(rec["tenant_id"], "lead")
            self.assertTrue(rec["tender_id"].startswith("lead:"))


class TestEpochMsToYear(unittest.TestCase):
    """Negative and boundary cases for the portable year helper."""

    def test_bool_is_not_a_timestamp(self):
        # bool is a subclass of int; must not be treated as epoch-ms.
        self.assertIsNone(h3_strata._epoch_ms_to_year(True))
        self.assertIsNone(h3_strata._epoch_ms_to_year(False))

    def test_non_numeric_returns_none(self):
        self.assertIsNone(h3_strata._epoch_ms_to_year(None))
        self.assertIsNone(h3_strata._epoch_ms_to_year("1963"))
        self.assertIsNone(h3_strata._epoch_ms_to_year({}))

    def test_overflow_returns_none_not_guess(self):
        self.assertIsNone(h3_strata._epoch_ms_to_year(10**20))
        self.assertIsNone(h3_strata._epoch_ms_to_year(-(10**20)))

    def test_unix_epoch_zero_is_1970(self):
        self.assertEqual(h3_strata._epoch_ms_to_year(0), 1970)

    def test_float_milliseconds_accepted(self):
        self.assertEqual(h3_strata._epoch_ms_to_year(-217641600000.0), 1963)

    def test_helper_source_does_not_call_fromtimestamp(self):
        # Structural lock: Windows OSError on negative POSIX times.
        # Docstring may name the forbidden API; the body must not call it.
        src = inspect.getsource(h3_strata._epoch_ms_to_year)
        body = src.split('"""', 2)[-1]
        self.assertIn("timedelta(", body)
        self.assertNotIn("fromtimestamp(", body)


class TestClassifyArea(unittest.TestCase):
    def test_sydney_is_tier1(self):
        self.assertEqual(h3_strata.classify_area("SYDNEY"), "tier1_metro")

    def test_wollongong_is_tier2(self):
        self.assertEqual(h3_strata.classify_area("WOLLONGONG"), "tier2_greater")

    def test_tweed_is_out_of_area(self):
        self.assertEqual(h3_strata.classify_area("TWEED"), "out_of_area")

    def test_none_lga_is_unknown(self):
        self.assertEqual(h3_strata.classify_area(None), "unknown")

    def test_empty_lga_is_unknown(self):
        self.assertEqual(h3_strata.classify_area(""), "unknown")

    def test_case_insensitive(self):
        self.assertEqual(h3_strata.classify_area("sydney"), "tier1_metro")

    def test_out_of_area_is_kept_not_rejected(self):
        # build_records must KEEP an out-of-area feature (referral/resale).
        recs = h3_strata.build_records([FEATURE_OUT_OF_AREA])
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["area_tier"], "out_of_area")


class TestBuildRecords(unittest.TestCase):
    def test_builds_all_valid(self):
        feats = [FEATURE_SYDNEY, FEATURE_NO_LOTS, FEATURE_OUT_OF_AREA]
        recs = h3_strata.build_records(feats)
        self.assertEqual(len(recs), 3)

    def test_drops_only_no_plan(self):
        feats = [FEATURE_SYDNEY, FEATURE_NO_PLAN, FEATURE_UNKNOWN_LGA]
        recs = h3_strata.build_records(feats)
        self.assertEqual(len(recs), 2)  # NO_PLAN dropped, unknown-lga kept

    def test_unknown_lga_kept_and_flagged(self):
        recs = h3_strata.build_records([FEATURE_UNKNOWN_LGA])
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["area_tier"], "unknown")


class TestHarvestPagination(unittest.TestCase):
    def test_paginates_until_short_page(self):
        # Fake fetch: page 0 full (2 features w/ page_size=2), page 1 short (1).
        calls = {"n": 0}

        def fake_fetch(where, result_offset, result_record_count):
            calls["n"] += 1
            if result_offset == 0:
                return {"features": [FEATURE_SYDNEY, FEATURE_OUT_OF_AREA]}
            return {"features": [FEATURE_NO_LOTS]}  # short -> stop

        recs = h3_strata.harvest(fetch=fake_fetch, page_size=2)
        self.assertEqual(len(recs), 3)
        self.assertEqual(calls["n"], 2)

    def test_single_short_page_stops_immediately(self):
        def fake_fetch(where, result_offset, result_record_count):
            return {"features": [FEATURE_SYDNEY]}

        recs = h3_strata.harvest(fetch=fake_fetch, page_size=2000)
        self.assertEqual(len(recs), 1)

    def test_empty_result_is_safe(self):
        def fake_fetch(where, result_offset, result_record_count):
            return {"features": []}

        recs = h3_strata.harvest(fetch=fake_fetch, page_size=2000)
        self.assertEqual(recs, [])

    def test_max_pages_cap_respected(self):
        # Always returns a full page -> must stop at max_pages, not loop forever.
        def fake_fetch(where, result_offset, result_record_count):
            return {"features": [FEATURE_SYDNEY, FEATURE_OUT_OF_AREA]}

        recs = h3_strata.harvest(fetch=fake_fetch, page_size=2, max_pages=3)
        self.assertEqual(len(recs), 6)  # 3 pages * 2


class TestReplayIdempotent(unittest.TestCase):
    def test_same_feature_yields_same_id(self):
        # Deterministic id => downstream store dedup (ON CONFLICT) collapses.
        r1 = h3_strata.parse_feature(FEATURE_SYDNEY)
        r2 = h3_strata.parse_feature(FEATURE_SYDNEY)
        self.assertEqual(r1["tender_id"], r2["tender_id"])


if __name__ == "__main__":
    unittest.main()
