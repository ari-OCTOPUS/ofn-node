"""collection → draft → media, and three ordering decisions.

Each of the three is cheap right now and impossible later. They are the
reason this file exists before anything uses it.

    sensitivity NOT NULL     added later it leaves NULL rows, and NULL is
                             neither value — fail-closed then depends on how
                             somebody reads NULL

    two timestamps           intent is not verifiable; order is. Without
                             both, a column of ratings has no way to say
                             which are contaminated — and the contaminated
                             ones are exactly those that correlate with the
                             numbers, because they are reflections of them

    no archived originals    keeping one proves nothing about what was sent,
                             and costs a sensitive file at rest
"""

from __future__ import annotations

import os
import tempfile
import unittest

from ofn.adapters.studio_store import StudioError, StudioStore
from ofn.kernel.advisor_gate import (
    RULE_NO_COLLECTION, RULE_RESTRICTED, Collection, Sensitivity,
    assert_no_pixels, may_send_image,
)
from ofn.kernel.errors import FailClosedError

NOW = 1_785_000_000
HOUR = 3600
SHA = "b" * 64


class Store(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "studio.sqlite")
        self.s = StudioStore(self.path)
        self.addCleanup(self.s.close)

    def coll(self, cid="c1", sensitivity="restricted"):
        return self.s.add_collection("studio", cid, "مجموعه", genre="پرتره",
                                     sensitivity=sensitivity, now_epoch_s=NOW)

    def draft(self, did="d1", cid=None):
        return self.s.add_draft("studio", did, collection_id=cid,
                                caption="متن", now_epoch_s=NOW)


class TestSensitivityIsNotNullFromTheStart(Store):
    def test_the_column_is_not_null(self):
        cols = {r[1]: r for r in self.s._conn.execute(
            "PRAGMA table_info(collections)")}
        self.assertEqual(cols["sensitivity"][3], 1, "sensitivity is nullable")

    def test_the_default_is_restricted(self):
        cols = {r[1]: r for r in self.s._conn.execute(
            "PRAGMA table_info(collections)")}
        self.assertIn("restricted", str(cols["sensitivity"][4]))

    def test_a_collection_made_without_saying_is_restricted(self):
        self.s._conn.execute("BEGIN IMMEDIATE")
        self.s._conn.execute(
            "INSERT INTO collections (collection_id, tenant_id, label, "
            "created_at) VALUES ('c9', 'studio', 'x', 1)")
        self.s._conn.execute("COMMIT")
        self.assertIs(self.s.collection("c9").sensitivity,
                      Sensitivity.RESTRICTED)

    def test_a_third_value_is_refused_by_the_database(self):
        """Not only by Python. A CHECK constraint is the half that survives
        somebody writing SQL by hand."""
        with self.assertRaises(Exception):
            self.s._conn.execute(
                "INSERT INTO collections (collection_id, tenant_id, label, "
                "sensitivity, created_at) VALUES ('c8','studio','x','maybe',1)")

    def test_python_refuses_it_too(self):
        with self.assertRaises(StudioError):
            self.coll(cid="c7", sensitivity="public")

    def test_an_unknown_stored_value_reads_as_restricted(self):
        """A typo, a migration gap, or a future third value all fail towards
        not sending."""
        for raw in (None, "", "General", "public", 1, "restricted"):
            self.assertIs(Sensitivity.of(raw), Sensitivity.RESTRICTED, raw)
        self.assertIs(Sensitivity.of("general"), Sensitivity.GENERAL)


class TestTheAdvisorGateIsStructural(unittest.TestCase):
    def general(self):
        return Collection("c1", "x", "g", Sensitivity.GENERAL)

    def restricted(self):
        return Collection("c1", "x", "g", Sensitivity.RESTRICTED)

    def test_restricted_never_leaves(self):
        v = may_send_image(self.restricted())
        self.assertFalse(v)
        self.assertEqual(v.rule, RULE_RESTRICTED)

    def test_no_collection_is_not_a_safe_collection(self):
        v = may_send_image(None)
        self.assertFalse(v)
        self.assertEqual(v.rule, RULE_NO_COLLECTION)

    def test_general_is_allowed(self):
        self.assertTrue(may_send_image(self.general()))

    def test_the_gate_takes_no_consent_argument(self):
        """Consent is people agreeing to be published. It says nothing about
        handing bytes to a third party, and accepting it here would let a
        caller believe one had bought the other."""
        import inspect as py
        params = set(py.signature(may_send_image).parameters)
        self.assertEqual(params, {"collection"})

    def test_there_is_no_override(self):
        import ofn.kernel.advisor_gate as g
        for name in dir(g):
            self.assertNotIn("force", name.lower())
            self.assertNotIn("override", name.lower())
            self.assertNotIn("allow_restricted", name.lower())


class TestTierZeroCannotCarryPixels(unittest.TestCase):
    """The structural half of "no pixel leaves the board": the extraction
    layer refuses the shapes an image arrives in, rather than the code
    happening not to put one there today."""

    def test_bytes_are_refused(self):
        for payload in (b"\x89PNG", bytearray(b"x"), memoryview(b"x")):
            with self.assertRaises(FailClosedError):
                assert_no_pixels(payload)

    def test_a_data_url_is_refused(self):
        with self.assertRaises(FailClosedError):
            assert_no_pixels("data:image/jpeg;base64,AAAA")

    def test_it_looks_inside_containers(self):
        """A payload is a dict of measurements. One bad value three levels
        down is exactly how a pixel gets out."""
        with self.assertRaises(FailClosedError):
            assert_no_pixels({"stats": [{"thumb": b"\x89PNG"}]})
        with self.assertRaises(FailClosedError):
            assert_no_pixels({"a": {"b": ["data:image/png;base64,AA"]}})

    def test_ordinary_measurements_pass(self):
        assert_no_pixels({"posts": 38, "window_days": 90,
                          "labels": ["single-subject", "soft-light"],
                          "retention": 0.42})


class TestTheTwoTimestamps(Store):
    def test_a_rating_given_before_any_number_is_trustworthy(self):
        self.draft()
        d = self.s.record_felt_right("d1", 4, now_epoch_s=NOW)
        self.assertTrue(d.rating_is_trustworthy)

    def test_a_rating_given_after_a_number_is_not(self):
        """The whole point. At that moment the answer is a reflection of the
        figure rather than an independent signal."""
        self.draft()
        self.s.record_first_metric("d1", now_epoch_s=NOW)
        d = self.s.record_felt_right("d1", 5, now_epoch_s=NOW + HOUR)
        self.assertFalse(d.rating_is_trustworthy)

    def test_the_contaminated_rating_is_kept_not_discarded(self):
        """Labelling it beats dropping it: discarding contaminated rows is
        how you end up unable to measure how often contamination happens."""
        self.draft()
        self.s.record_first_metric("d1", now_epoch_s=NOW)
        d = self.s.record_felt_right("d1", 5, now_epoch_s=NOW + HOUR)
        self.assertEqual(d.felt_right, 5)
        self.assertIsNotNone(d.felt_right_at)

    def test_a_tie_is_not_trusted(self):
        """Same second, no order. The safe reading is the one that claims
        less."""
        self.draft()
        self.s.record_first_metric("d1", now_epoch_s=NOW)
        d = self.s.record_felt_right("d1", 3, now_epoch_s=NOW)
        self.assertFalse(d.rating_is_trustworthy)

    def test_no_rating_is_not_trustworthy(self):
        self.assertFalse(self.draft().rating_is_trustworthy)

    def test_the_first_metric_stamp_never_moves(self):
        """A second call would quietly reclassify contaminated ratings as
        clean, because the stamp is what every trust decision compares
        against."""
        self.draft()
        self.s.record_first_metric("d1", now_epoch_s=NOW)
        self.s.record_first_metric("d1", now_epoch_s=NOW + 10 * HOUR)
        self.assertEqual(self.s.draft("d1").first_metric_at, NOW)

    def test_a_rating_is_written_once(self):
        self.draft()
        self.s.record_felt_right("d1", 4, now_epoch_s=NOW)
        with self.assertRaises(StudioError):
            self.s.record_felt_right("d1", 1, now_epoch_s=NOW + HOUR)

    def test_the_scale_is_one_to_five_and_a_bool_is_not_a_rating(self):
        self.draft()
        for bad in (0, 6, -1, True, False, "3", 3.5):
            with self.assertRaises(StudioError):
                self.s.record_felt_right("d1", bad, now_epoch_s=NOW)

    def test_only_trustworthy_rows_are_offered_to_an_analysis(self):
        self.draft("clean")
        self.s.record_felt_right("clean", 5, now_epoch_s=NOW)
        self.draft("dirty")
        self.s.record_first_metric("dirty", now_epoch_s=NOW)
        self.s.record_felt_right("dirty", 5, now_epoch_s=NOW + HOUR)
        self.draft("unrated")
        self.assertEqual([d.draft_id for d in self.s.trustworthy_ratings("studio")],
                         ["clean"])


class TestTheShape(Store):
    def test_a_draft_may_have_no_collection(self):
        """Forcing one would make her invent a category before she is ready
        to have one."""
        self.assertIsNone(self.draft().collection_id)

    def test_a_draft_in_an_unknown_collection_is_refused(self):
        with self.assertRaises(StudioError):
            self.draft(cid="ghost")

    def test_media_are_ordered_inside_a_post(self):
        self.draft()
        for pos in (2, 0, 1):
            self.s.attach_media("d1", pos, f"studio/d1/{pos}-1600.jpg")
        self.assertEqual([p for p, _ in self.s.media_of("d1")], [0, 1, 2])

    def test_a_bool_is_not_a_position(self):
        """`True == 1`, so it would silently become position 1."""
        self.draft()
        for bad in (True, False, "0", 1.0, None):
            with self.assertRaises(StudioError):
                self.s.attach_media("d1", bad, "x")

    def test_a_position_out_of_range_is_refused(self):
        self.draft()
        for bad in (-1, 10, 9999):
            with self.assertRaises(StudioError):
                self.s.attach_media("d1", bad, "x")

    def test_replacing_a_position_does_not_duplicate_it(self):
        self.draft()
        self.s.attach_media("d1", 0, "first")
        self.s.attach_media("d1", 0, "second")
        self.assertEqual(self.s.media_of("d1"), [(0, "second")])

    def test_the_consent_unit_is_the_draft_not_the_media(self):
        """A three-photo post asks the question once. If media were the unit
        it would ask three times, which is the decision-multiplication the
        design directive exists against."""
        self.draft()
        for pos in range(3):
            self.s.attach_media("d1", pos, f"m{pos}")
        self.assertEqual(len(self.s.media_of("d1")), 3)
        # One draft id — one row in `draft_subjects`, one decision.
        self.assertEqual(self.s.draft("d1").draft_id, "d1")


class TestWhatActuallyWentOverTheWire(Store):
    def test_the_hash_is_of_what_was_sent(self):
        self.draft()
        self.s.record_sent("d1", 0, platform="instagram", sha256=SHA,
                           byte_size=1234, sent_at=NOW)
        self.assertEqual(self.s.sent_for("d1"),
                         [(0, "instagram", SHA, NOW)])

    def test_a_missing_hash_is_refused(self):
        self.draft()
        with self.assertRaises(StudioError):
            self.s.record_sent("d1", 0, platform="instagram", sha256="",
                               byte_size=1, sent_at=NOW)

    def test_the_same_media_on_two_platforms_is_two_rows(self):
        """Each carries its own hash: the rendition sent to one may not be
        the rendition sent to another."""
        self.draft()
        self.s.record_sent("d1", 0, platform="instagram", sha256=SHA,
                           byte_size=1, sent_at=NOW)
        self.s.record_sent("d1", 0, platform="telegram", sha256="c" * 64,
                           byte_size=1, sent_at=NOW)
        self.assertEqual(len(self.s.sent_for("d1")), 2)

    def test_recording_the_same_send_twice_is_refused(self):
        self.draft()
        self.s.record_sent("d1", 0, platform="instagram", sha256=SHA,
                           byte_size=1, sent_at=NOW)
        with self.assertRaises(StudioError):
            self.s.record_sent("d1", 0, platform="instagram", sha256=SHA,
                               byte_size=1, sent_at=NOW + 1)


class TestDurability(Store):
    def test_wal_and_full_sync(self):
        mode = self.s._conn.execute("PRAGMA journal_mode").fetchone()[0]
        self.assertEqual(str(mode).lower(), "wal")
        self.assertEqual(
            self.s._conn.execute("PRAGMA synchronous").fetchone()[0], 2)

    def test_it_survives_reopening(self):
        self.coll()
        self.draft(cid="c1")
        self.s.record_felt_right("d1", 4, now_epoch_s=NOW)
        self.s.close()
        again = StudioStore(self.path)
        self.addCleanup(again.close)
        self.assertTrue(again.draft("d1").rating_is_trustworthy)
        self.assertIs(again.collection("c1").sensitivity,
                      Sensitivity.RESTRICTED)


if __name__ == "__main__":
    unittest.main()
