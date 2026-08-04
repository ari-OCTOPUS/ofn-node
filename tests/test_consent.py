"""ST-1 — consent, built before anything that would use it.

The content of this leg is pictures of a real person. That changes the risk
model, and it changes what "done" means: a boolean called `consent_confirmed`
has the shape of a control without being one.

The test that matters most in this file is the last class. Everything else
here could be added in a month with a migration. `draft_subjects` could not:
the only moment "who is in this draft" exists is the moment somebody puts
them there, and if it is not written then it is not recoverable from the
image, the caption, or the ledger.

    the day somebody withdraws consent, the question is
    "everything published that this person is in — which ones?"

That question either has an answer or it never will.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from ofn.adapters.consent_store import ConsentError, ConsentStore
from ofn.kernel.consent import (
    FUTURE_TOLERANCE_S, Refusal, Release, Subject, may_publish, parse_scope,
    subjects_needing_attention,
)
from ofn.kernel.errors import FailClosedError

NOW = 1_785_000_000
DAY = 86_400
SHA = "a" * 64


def rel(rid="r1", sid="s1", scope="instagram", signed=NOW - DAY,
        expires=None, revoked=None) -> Release:
    return Release(rid, sid, parse_scope(scope), signed, expires, revoked)


SABA = Subject("s1", "خودم")
OTHER = Subject("s2", "دوست")


class TestNobodyDeclared(unittest.TestCase):
    """The rule this module exists for.

    Same shape as `fleet.judge`: no baseline → UNKNOWN, never healthy. Here,
    "nobody said there is a person in this" is the same bytes as "nobody
    looked", and an empty list is the most common way for a check to pass by
    accident.
    """

    def test_no_subjects_is_refused_not_allowed(self):
        v = may_publish([], [], platform="instagram", now_epoch_s=NOW)
        self.assertFalse(v.allowed)
        self.assertFalse(v)                    # __bool__ agrees

    def test_the_reason_says_it_is_not_the_same_as_nobody_being_in_it(self):
        v = may_publish([], [], platform="instagram", now_epoch_s=NOW)
        self.assertIn("not the same", v.why)

    def test_releases_without_subjects_do_not_rescue_it(self):
        """A pile of valid paperwork attached to nobody is still nobody."""
        v = may_publish([], [rel()], platform="instagram", now_epoch_s=NOW)
        self.assertFalse(v.allowed)


class TestOneSubjectOneRelease(unittest.TestCase):
    def test_a_live_release_for_this_platform_allows_it(self):
        v = may_publish([SABA], [rel()], platform="instagram", now_epoch_s=NOW)
        self.assertTrue(v.allowed)
        self.assertEqual(v.blocks, ())

    def test_a_subject_with_no_release_blocks(self):
        v = may_publish([SABA], [], platform="instagram", now_epoch_s=NOW)
        self.assertFalse(v.allowed)
        self.assertEqual(v.blocks[0].reason, Refusal.NO_RELEASE)

    def test_an_expired_release_blocks(self):
        v = may_publish([SABA], [rel(expires=NOW - 1)],
                        platform="instagram", now_epoch_s=NOW)
        self.assertEqual(v.blocks[0].reason, Refusal.EXPIRED)

    def test_expiry_is_exclusive_at_the_stroke(self):
        """A document that expires at exactly now is expired. The alternative
        is a one-second window in which it is both."""
        v = may_publish([SABA], [rel(expires=NOW)],
                        platform="instagram", now_epoch_s=NOW)
        self.assertEqual(v.blocks[0].reason, Refusal.EXPIRED)

    def test_no_expiry_means_no_expiry(self):
        v = may_publish([SABA], [rel(expires=None)],
                        platform="instagram", now_epoch_s=NOW + 40 * 365 * DAY)
        self.assertTrue(v.allowed)

    def test_a_platform_outside_the_scope_blocks(self):
        v = may_publish([SABA], [rel(scope="instagram")],
                        platform="telegram", now_epoch_s=NOW)
        self.assertEqual(v.blocks[0].reason, Refusal.OUT_OF_SCOPE)

    def test_a_release_signed_in_the_future_is_not_yet_in_force(self):
        """This board has no battery-backed clock, so a date ahead of now is
        as likely to be our fault as theirs. Either way it cannot authorise
        anything yet, and accepting it would let a mistyped year outlive
        every later withdrawal."""
        v = may_publish([SABA], [rel(signed=NOW + 10 * DAY)],
                        platform="instagram", now_epoch_s=NOW)
        self.assertEqual(v.blocks[0].reason, Refusal.NOT_YET_IN_FORCE)

    def test_a_small_clock_skew_is_tolerated(self):
        v = may_publish([SABA], [rel(signed=NOW + FUTURE_TOLERANCE_S - 1)],
                        platform="instagram", now_epoch_s=NOW)
        self.assertTrue(v.allowed)


class TestWithdrawalDoesNotComeBack(unittest.TestCase):
    def test_a_revoked_release_blocks(self):
        v = may_publish([SABA], [rel(revoked=NOW - 60)],
                        platform="instagram", now_epoch_s=NOW)
        self.assertEqual(v.blocks[0].reason, Refusal.REVOKED)

    def test_an_older_document_cannot_undo_a_withdrawal(self):
        """The failure this rule exists for. Somebody withdraws; an earlier
        signature is still sitting in the table; a naive "is there any live
        release" check finds it and publishes."""
        withdrawn = rel("r2", signed=NOW - 10 * DAY, revoked=NOW - DAY)
        older = rel("r1", signed=NOW - 20 * DAY)      # never revoked itself
        v = may_publish([SABA], [older, withdrawn],
                        platform="instagram", now_epoch_s=NOW)
        self.assertFalse(v.allowed)
        self.assertEqual(v.blocks[0].reason, Refusal.REVOKED)

    def test_order_in_the_list_does_not_change_the_answer(self):
        withdrawn = rel("r2", signed=NOW - 10 * DAY, revoked=NOW - DAY)
        older = rel("r1", signed=NOW - 20 * DAY)
        a = may_publish([SABA], [older, withdrawn],
                        platform="instagram", now_epoch_s=NOW)
        b = may_publish([SABA], [withdrawn, older],
                        platform="instagram", now_epoch_s=NOW)
        self.assertEqual(a.allowed, b.allowed)
        self.assertEqual(a.blocks, b.blocks)

    def test_signing_again_afterwards_does_count(self):
        """Irreversible must not mean "banned for life". A person who changes
        their mind and signs a new document is not locked out — what is
        irreversible is that no *older* paper can be produced to undo it."""
        withdrawn = rel("r1", signed=NOW - 20 * DAY, revoked=NOW - 10 * DAY)
        fresh = rel("r2", signed=NOW - DAY)
        v = may_publish([SABA], [withdrawn, fresh],
                        platform="instagram", now_epoch_s=NOW)
        self.assertTrue(v.allowed)

    def test_a_document_signed_at_the_exact_moment_of_withdrawal_does_not(self):
        """Ties go to the withdrawal."""
        withdrawn = rel("r1", signed=NOW - 20 * DAY, revoked=NOW - 10 * DAY)
        same_instant = rel("r2", signed=NOW - 10 * DAY)
        v = may_publish([SABA], [withdrawn, same_instant],
                        platform="instagram", now_epoch_s=NOW)
        self.assertFalse(v.allowed)


class TestEverybodyIsNamed(unittest.TestCase):
    def test_every_blocking_person_is_reported_not_just_the_first(self):
        """Fixing consent one refusal at a time, with a publish attempt
        between each, is how somebody gets missed."""
        v = may_publish([SABA, OTHER], [], platform="instagram",
                        now_epoch_s=NOW)
        self.assertEqual(len(v.blocks), 2)
        self.assertEqual({b.subject_id for b in v.blocks}, {"s1", "s2"})

    def test_one_cleared_and_one_not_is_still_refused(self):
        v = may_publish([SABA, OTHER], [rel(sid="s1")],
                        platform="instagram", now_epoch_s=NOW)
        self.assertFalse(v.allowed)
        self.assertEqual([b.subject_id for b in v.blocks], ["s2"])

    def test_the_map_view_agrees_with_the_verdict(self):
        gaps = subjects_needing_attention(
            [SABA, OTHER], [rel(sid="s1")], platform="instagram",
            now_epoch_s=NOW)
        self.assertEqual(gaps, {"s2": Refusal.NO_RELEASE})

    def test_no_real_name_travels_in_a_verdict(self):
        """Blocks carry the subject id. The label somebody chose stays in the
        store — a refusal ends up in logs and on screens."""
        v = may_publish([Subject("s1", "نام واقعی")], [],
                        platform="instagram", now_epoch_s=NOW)
        self.assertNotIn("نام واقعی", repr(v))


class TestScope(unittest.TestCase):
    def test_several_platforms_in_one_document(self):
        v = may_publish([SABA], [rel(scope="instagram, telegram")],
                        platform="telegram", now_epoch_s=NOW)
        self.assertTrue(v.allowed)

    def test_whitespace_and_case_are_not_a_grant(self):
        self.assertEqual(parse_scope("  Instagram\tTELEGRAM "),
                         frozenset({"instagram", "telegram"}))

    def test_there_is_no_wildcard(self):
        """A document that says "everywhere" is a document whose author could
        not have known where everywhere would be a year later."""
        for text in ("*", "all", "any"):
            v = may_publish([SABA], [rel(scope=text)],
                            platform="instagram", now_epoch_s=NOW)
            self.assertFalse(v.allowed, f"{text!r} granted a platform")

    def test_an_empty_scope_grants_nothing(self):
        v = may_publish([SABA], [rel(scope="   ")],
                        platform="instagram", now_epoch_s=NOW)
        self.assertFalse(v.allowed)

    def test_a_malformed_platform_argument_is_refused_loudly(self):
        """Not "refused quietly" — a caller passing rubbish here has a bug,
        and a False return would look like an ordinary consent gap."""
        with self.assertRaises(FailClosedError):
            may_publish([SABA], [rel()], platform="", now_epoch_s=NOW)
        with self.assertRaises(FailClosedError):
            may_publish([SABA], [rel()], platform="Insta gram",
                        now_epoch_s=NOW)

    def test_a_malformed_subject_id_is_refused_at_construction(self):
        with self.assertRaises(FailClosedError):
            Subject("../etc/passwd", "x")


class Store(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.s = ConsentStore(os.path.join(self.dir, "consent.sqlite"))
        self.addCleanup(self.s.close)

    def person(self, sid="s1", label="خودم"):
        return self.s.add_subject("studio", sid, label, now_epoch_s=NOW)

    def paper(self, rid="r1", sid="s1", scope="instagram", signed=NOW - DAY,
              expires=None):
        return self.s.record_release(
            rid, sid, scope=scope, signed_at=signed, expires_at=expires,
            document_ref="safe/box/1", document_sha256=SHA,
            recorded_by="operator:ari")


class TestDurability(Store):
    """The ST-1 checklist names this explicitly, so it gets an assertion
    rather than a claim. This board has no battery: under WAL with
    `synchronous=NORMAL`, SQLite's own documentation says transactions may
    roll back after a power failure — and a consent record that silently
    rolls back is the worst row in this database to lose."""

    def test_wal_and_full_sync(self):
        mode = self.s._conn.execute("PRAGMA journal_mode").fetchone()[0]
        self.assertEqual(str(mode).lower(), "wal")
        # 2 == FULL. NORMAL (1) would trade away exactly what is needed here.
        self.assertEqual(self.s._conn.execute("PRAGMA synchronous").fetchone()[0], 2)

    def test_foreign_keys_are_on(self):
        """`releases.subject_id` and `draft_subjects.subject_id` both point at
        `subjects`. Without enforcement those are documentation."""
        self.assertEqual(
            self.s._conn.execute("PRAGMA foreign_keys").fetchone()[0], 1)


class TestTheStoreRefusesHalfRecords(Store):
    def test_a_release_without_a_hash_is_refused(self):
        """A row saying somebody signed something, with no way to check which
        something, reads exactly like a row that can be checked."""
        self.person()
        with self.assertRaises(ConsentError):
            self.s.record_release("r1", "s1", scope="instagram",
                                  signed_at=NOW, document_ref="box",
                                  document_sha256="", recorded_by="ari")

    def test_a_release_without_a_location_is_refused(self):
        self.person()
        with self.assertRaises(ConsentError):
            self.s.record_release("r1", "s1", scope="instagram",
                                  signed_at=NOW, document_ref="  ",
                                  document_sha256=SHA, recorded_by="ari")

    def test_a_release_for_an_unknown_person_is_refused(self):
        with self.assertRaises(ConsentError):
            self.paper()

    def test_a_scope_naming_no_real_platform_is_refused_at_write_time(self):
        """Better here than at publish time: a row that can never authorise
        anything looks, in a list, exactly like one that can."""
        self.person()
        with self.assertRaises(ConsentError):
            self.paper(scope="everywhere!!")

    def test_the_document_is_not_in_the_database(self):
        """Only a reference and a hash. A database that holds the evidence of
        consent is one whose corruption destroys the evidence."""
        self.person()
        self.paper()
        cols = {r[1] for r in self.s._conn.execute(
            "PRAGMA table_info(releases)")}
        self.assertIn("document_ref", cols)
        self.assertIn("document_sha256", cols)
        for blobbish in ("document", "document_body", "pdf", "content"):
            self.assertNotIn(blobbish, cols)

    def test_the_hash_is_kept_out_of_the_kernels_reach(self):
        self.person()
        r = self.paper()
        self.assertFalse(hasattr(r, "document_sha256"))
        self.assertEqual(self.s.document_digest("r1"), SHA)


class TestRevokingThroughTheStore(Store):
    def test_revoking_blocks_publication(self):
        self.person()
        self.paper()
        self.s.revoke("r1", now_epoch_s=NOW)
        v = may_publish(self.s.subjects("studio"),
                        self.s.releases_for(["s1"]),
                        platform="instagram", now_epoch_s=NOW + 10)
        self.assertFalse(v.allowed)

    def test_revoking_twice_is_refused(self):
        """The second call would move the date forward, and the date is what
        every judgement compares against — it would quietly widen the range
        of documents the withdrawal invalidates."""
        self.person()
        self.paper()
        self.s.revoke("r1", now_epoch_s=NOW)
        with self.assertRaises(ConsentError):
            self.s.revoke("r1", now_epoch_s=NOW + DAY)

    def test_there_is_no_unrevoke(self):
        self.assertFalse(hasattr(self.s, "unrevoke"))
        self.assertFalse(hasattr(self.s, "restore"))

    def test_it_survives_reopening_the_file(self):
        self.person()
        self.paper()
        self.s.revoke("r1", now_epoch_s=NOW)
        path = self.s._pool._path if hasattr(self.s._pool, "_path") else None
        self.s.close()
        again = ConsentStore(os.path.join(self.dir, "consent.sqlite"))
        self.addCleanup(again.close)
        self.assertIsNotNone(again.release("r1").revoked_at)
        del path


class TestTheTableThatCannotBeAddedLater(Store):
    """`draft_subjects`, and the question it exists to answer."""

    def publish(self, draft, post_id, platform="instagram", at=NOW):
        return self.s.record_post("studio", post_id, draft,
                                  platform=platform, published_at=at)

    def test_the_withdrawal_question_has_an_answer(self):
        self.person("s1")
        self.person("s2", "دوست")
        self.s.add_to_draft("d1", "s1", added_by="saba", now_epoch_s=NOW)
        self.s.add_to_draft("d2", "s1", added_by="saba", now_epoch_s=NOW)
        self.s.add_to_draft("d2", "s2", added_by="saba", now_epoch_s=NOW)
        self.s.add_to_draft("d3", "s2", added_by="saba", now_epoch_s=NOW)
        self.publish("d1", "p1")
        self.publish("d2", "p2", at=NOW + 10)
        self.publish("d3", "p3", at=NOW + 20)

        mine = self.s.published_containing("s1")
        self.assertEqual([p.post_id for p in mine], ["p1", "p2"])

    def test_an_unpublished_draft_is_not_in_the_answer(self):
        self.person()
        self.s.add_to_draft("d1", "s1", added_by="saba", now_epoch_s=NOW)
        self.assertEqual(self.s.published_containing("s1"), [])

    def test_the_answer_is_ordered_by_when_it_went_out(self):
        self.person()
        for i, at in ((1, NOW + 300), (2, NOW + 100), (3, NOW + 200)):
            self.s.add_to_draft(f"d{i}", "s1", added_by="saba",
                                now_epoch_s=NOW)
            self.publish(f"d{i}", f"p{i}", at=at)
        self.assertEqual([p.post_id for p in self.s.published_containing("s1")],
                         ["p2", "p3", "p1"])

    def test_it_spans_platforms(self):
        self.person()
        self.s.add_to_draft("d1", "s1", added_by="saba", now_epoch_s=NOW)
        self.publish("d1", "p1", platform="instagram")
        self.s.add_to_draft("d2", "s1", added_by="saba", now_epoch_s=NOW)
        self.publish("d2", "p2", platform="telegram", at=NOW + 5)
        self.assertEqual({p.platform for p in self.s.published_containing("s1")},
                         {"instagram", "telegram"})

    def test_somebody_can_be_taken_out_of_a_draft_before_it_goes_out(self):
        self.person()
        self.s.add_to_draft("d1", "s1", added_by="saba", now_epoch_s=NOW)
        self.s.remove_from_draft("d1", "s1")
        self.assertEqual(self.s.subjects_in_draft("d1"), [])

    def test_a_published_draft_cannot_have_its_people_edited(self):
        """The hole this closes was found by writing the test first and not
        liking the answer. `published_containing` joins posts to
        `draft_subjects`, so deleting a row here after publication does not
        undo the publication — it deletes the evidence of it, and the
        withdrawal question starts returning a shorter, comfortable, wrong
        answer.

        Editing the plan is fine. Editing what already happened is not on
        offer."""
        self.person()
        self.s.add_to_draft("d1", "s1", added_by="saba", now_epoch_s=NOW)
        self.publish("d1", "p1")
        with self.assertRaises(ConsentError):
            self.s.remove_from_draft("d1", "s1")
        self.assertEqual([p.post_id for p in self.s.published_containing("s1")],
                         ["p1"])

    def test_withdrawal_is_done_by_revoking_not_by_deleting(self):
        """The refusal above has to leave a real route, or it is just an
        obstacle. Revoking blocks everything future without touching what
        already went out."""
        self.person()
        self.paper()
        self.s.add_to_draft("d1", "s1", added_by="saba", now_epoch_s=NOW)
        self.publish("d1", "p1")
        self.s.revoke("r1", now_epoch_s=NOW + DAY)

        # History intact — that is what answers "which posts am I in".
        self.assertEqual(len(self.s.published_containing("s1")), 1)
        # And nothing else may go out.
        people = self.s.subjects_in_draft("d1")
        v = may_publish(people, self.s.releases_for(["s1"]),
                        platform="instagram", now_epoch_s=NOW + 2 * DAY)
        self.assertFalse(v.allowed)
        self.assertEqual(v.blocks[0].reason, Refusal.REVOKED)

    def test_adding_the_same_person_twice_is_not_an_error(self):
        self.person()
        self.s.add_to_draft("d1", "s1", added_by="saba", now_epoch_s=NOW)
        self.s.add_to_draft("d1", "s1", added_by="saba", now_epoch_s=NOW + 5)
        self.assertEqual(len(self.s.subjects_in_draft("d1")), 1)

    def test_an_unknown_person_cannot_be_added_to_a_draft(self):
        with self.assertRaises(ConsentError):
            self.s.add_to_draft("d1", "ghost", added_by="saba",
                                now_epoch_s=NOW)

    def test_a_post_carries_a_slot_for_the_platforms_own_id(self):
        """Empty today — no wire is connected. It exists now because a column
        that starts being written later leaves a gap in the history."""
        self.person()
        self.s.add_to_draft("d1", "s1", added_by="saba", now_epoch_s=NOW)
        p = self.publish("d1", "p1")
        self.assertIsNone(p.external_id)
        cols = {r[1] for r in self.s._conn.execute("PRAGMA table_info(posts)")}
        self.assertIn("external_id", cols)


class TestTheGateAndTheStoreAgree(Store):
    def test_a_full_pass_end_to_end(self):
        self.person()
        self.paper(scope="instagram telegram")
        self.s.add_to_draft("d1", "s1", added_by="saba", now_epoch_s=NOW)
        people = self.s.subjects_in_draft("d1")
        docs = self.s.releases_for([p.subject_id for p in people])
        self.assertTrue(may_publish(people, docs, platform="telegram",
                                    now_epoch_s=NOW).allowed)

    def test_a_draft_with_nobody_in_it_is_refused(self):
        """Not "allowed because there is nobody to object"."""
        people = self.s.subjects_in_draft("d-empty")
        self.assertEqual(people, [])
        self.assertFalse(may_publish(people, [], platform="instagram",
                                     now_epoch_s=NOW).allowed)


if __name__ == "__main__":
    unittest.main()
