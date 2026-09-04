"""Kernel-pure approval class — complementary to the review-gate workflow.

UNKNOWN is not FALSE. Author/bot/unlisted are not independent.
Ready is not authorized. This module is not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.approval_class import (
    APPROVAL_STATES,
    APPROVAL_VERDICTS,
    ApprovalDecision,
    author_self_is_independent,
    bot_is_independent,
    claims_immutable,
    classify_approval,
    grants_send,
    halt_blocks_approval,
    listed_author_is_independent,
    listed_bot_is_independent,
    proposal_is_execution,
    ready_is_authorized,
    unknown_is_false,
    unknown_is_independent,
    unlisted_is_independent,
)
from ofn.kernel.errors import FailClosedError

_VALID = frozenset({"rev-a", "rev-b"})


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_approval(self):
        self.assertFalse(halt_blocks_approval())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_unknown_is_not_independent(self):
        self.assertFalse(unknown_is_independent())

    def test_author_self_is_not_independent(self):
        self.assertFalse(author_self_is_independent())

    def test_bot_is_not_independent(self):
        self.assertFalse(bot_is_independent())

    def test_unlisted_is_not_independent(self):
        self.assertFalse(unlisted_is_independent())

    def test_listed_bot_is_not_independent(self):
        self.assertFalse(listed_bot_is_independent())

    def test_listed_author_is_not_independent(self):
        self.assertFalse(listed_author_is_independent())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_closed_vocabularies(self):
        self.assertEqual(
            APPROVAL_VERDICTS,
            {"independent", "author_self", "bot", "unlisted", "unknown"})
        self.assertEqual(
            APPROVAL_STATES,
            {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"})

    def test_classify_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(classify_approval).parameters
        self.assertEqual(
            list(params),
            ["author", "approver", "state", "valid_reviewers"])
        for forbidden in ("resend", "send_authorized", "quote_sent",
                          "campaign_envelope_ready", "halt", "halt_raw",
                          "required"):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            ApprovalDecision(
                verdict="unknown", author="a", approver=None,
                grants_send=True)

    def test_constructor_refuses_independent_without_approver(self):
        with self.assertRaises(FailClosedError):
            ApprovalDecision(
                verdict="independent", author="a", approver=None)

    def test_constructor_refuses_independent_author_as_approver(self):
        with self.assertRaises(FailClosedError):
            ApprovalDecision(
                verdict="independent", author="a", approver="a")

    def test_constructor_refuses_author_self_mismatch(self):
        with self.assertRaises(FailClosedError):
            ApprovalDecision(
                verdict="author_self", author="a", approver="b")

    def test_constructor_refuses_bot_without_marker(self):
        with self.assertRaises(FailClosedError):
            ApprovalDecision(
                verdict="bot", author="a", approver="rev-a")

    def test_constructor_refuses_foreign_verdict(self):
        with self.assertRaises(FailClosedError):
            ApprovalDecision(
                verdict="ok", author="a", approver="rev-a")

    def test_constructor_refuses_sealed_author(self):
        with self.assertRaises(FailClosedError):
            ApprovalDecision(
                verdict="unknown", author="send_authorized", approver=None)


class ClassifyIndependent(unittest.TestCase):
    def test_listed_human_non_author_is_independent(self):
        d = classify_approval(
            author="cursor[bot]", approver="rev-a",
            state="APPROVED", valid_reviewers=_VALID)
        self.assertEqual(d.verdict, "independent")
        self.assertEqual(d.approver, "rev-a")
        self.assertFalse(d.grants_send)

    def test_second_listed_reviewer_is_also_independent(self):
        d = classify_approval(
            author="writer", approver="rev-b",
            state="APPROVED", valid_reviewers=_VALID)
        self.assertEqual(d.verdict, "independent")
        self.assertFalse(d.grants_send)

    def test_gov_v6_names_work_when_supplied_not_hardcoded(self):
        d = classify_approval(
            author="cursor[bot]", approver="Elahe-z",
            state="APPROVED",
            valid_reviewers=("Elahe-z", "aram-ui"))
        self.assertEqual(d.verdict, "independent")
        d2 = classify_approval(
            author="cursor[bot]", approver="aram-ui",
            state="APPROVED",
            valid_reviewers=("Elahe-z", "aram-ui"))
        self.assertEqual(d2.verdict, "independent")


class ClassifyAuthorSelf(unittest.TestCase):
    def test_author_approving_own_change_is_author_self(self):
        d = classify_approval(
            author="writer", approver="writer",
            state="APPROVED", valid_reviewers=_VALID)
        self.assertEqual(d.verdict, "author_self")
        self.assertFalse(author_self_is_independent())
        self.assertFalse(d.grants_send)

    def test_author_listed_in_valid_set_is_still_author_self(self):
        d = classify_approval(
            author="rev-a", approver="rev-a",
            state="APPROVED", valid_reviewers=_VALID)
        self.assertEqual(d.verdict, "author_self")
        self.assertFalse(listed_author_is_independent())


class ClassifyBot(unittest.TestCase):
    def test_bot_suffix_is_bot(self):
        d = classify_approval(
            author="writer", approver="cursor[bot]",
            state="APPROVED", valid_reviewers=_VALID)
        self.assertEqual(d.verdict, "bot")
        self.assertFalse(bot_is_independent())
        self.assertFalse(d.grants_send)

    def test_bot_suffix_is_case_insensitive(self):
        d = classify_approval(
            author="writer", approver="App[BOT]",
            state="APPROVED", valid_reviewers=_VALID)
        self.assertEqual(d.verdict, "bot")

    def test_bot_listed_in_valid_set_is_still_bot(self):
        d = classify_approval(
            author="writer", approver="helper[bot]",
            state="APPROVED",
            valid_reviewers=("rev-a", "helper[bot]"))
        self.assertEqual(d.verdict, "bot")
        self.assertFalse(listed_bot_is_independent())


class ClassifyUnlisted(unittest.TestCase):
    def test_human_outside_valid_set_is_unlisted(self):
        d = classify_approval(
            author="writer", approver="stranger",
            state="APPROVED", valid_reviewers=_VALID)
        self.assertEqual(d.verdict, "unlisted")
        self.assertFalse(unlisted_is_independent())
        self.assertFalse(d.grants_send)

    def test_login_match_is_case_sensitive(self):
        d = classify_approval(
            author="writer", approver="Rev-A",
            state="APPROVED", valid_reviewers=_VALID)
        self.assertEqual(d.verdict, "unlisted")


class ClassifyUnknown(unittest.TestCase):
    def test_missing_approver_is_unknown_not_false(self):
        d = classify_approval(
            author="writer", approver=None,
            state="APPROVED", valid_reviewers=_VALID)
        self.assertEqual(d.verdict, "unknown")
        self.assertIsNone(d.approver)
        self.assertFalse(unknown_is_false())
        self.assertFalse(unknown_is_independent())

    def test_missing_state_is_unknown_not_independent(self):
        d = classify_approval(
            author="writer", approver="rev-a",
            state=None, valid_reviewers=_VALID)
        self.assertEqual(d.verdict, "unknown")
        self.assertEqual(d.approver, "rev-a")
        self.assertFalse(unknown_is_independent())

    def test_changes_requested_is_unknown_not_independent(self):
        d = classify_approval(
            author="writer", approver="rev-a",
            state="CHANGES_REQUESTED", valid_reviewers=_VALID)
        self.assertEqual(d.verdict, "unknown")
        self.assertFalse(d.grants_send)

    def test_dismissed_is_unknown_not_independent(self):
        d = classify_approval(
            author="writer", approver="rev-a",
            state="DISMISSED", valid_reviewers=_VALID)
        self.assertEqual(d.verdict, "unknown")


class FailClosedInputs(unittest.TestCase):
    def test_missing_author_refuses(self):
        with self.assertRaises(FailClosedError):
            classify_approval(
                author=None, approver="rev-a",
                state="APPROVED", valid_reviewers=_VALID)

    def test_bool_author_refuses(self):
        with self.assertRaises(FailClosedError):
            classify_approval(
                author=True, approver="rev-a",
                state="APPROVED", valid_reviewers=_VALID)

    def test_blank_author_refuses(self):
        with self.assertRaises(FailClosedError):
            classify_approval(
                author="  ", approver="rev-a",
                state="APPROVED", valid_reviewers=_VALID)

    def test_missing_valid_reviewers_is_unknown_not_empty(self):
        with self.assertRaises(FailClosedError):
            classify_approval(
                author="writer", approver="rev-a",
                state="APPROVED", valid_reviewers=None)

    def test_string_valid_reviewers_is_not_a_set(self):
        with self.assertRaises(FailClosedError):
            classify_approval(
                author="writer", approver="r",
                state="APPROVED", valid_reviewers="rev-a")

    def test_empty_valid_reviewers_does_not_satisfy(self):
        with self.assertRaises(FailClosedError):
            classify_approval(
                author="writer", approver="rev-a",
                state="APPROVED", valid_reviewers=())

    def test_commented_is_not_an_approval_state(self):
        with self.assertRaises(FailClosedError):
            classify_approval(
                author="writer", approver="rev-a",
                state="COMMENTED", valid_reviewers=_VALID)

    def test_bool_state_refuses(self):
        with self.assertRaises(FailClosedError):
            classify_approval(
                author="writer", approver="rev-a",
                state=True, valid_reviewers=_VALID)

    def test_sealed_author_refuses(self):
        with self.assertRaises(FailClosedError):
            classify_approval(
                author="send_authorized", approver="rev-a",
                state="APPROVED", valid_reviewers=_VALID)

    def test_sealed_approver_refuses(self):
        with self.assertRaises(FailClosedError):
            classify_approval(
                author="writer", approver="quote_sent",
                state="APPROVED", valid_reviewers=_VALID)

    def test_sealed_valid_reviewer_refuses(self):
        with self.assertRaises(FailClosedError):
            classify_approval(
                author="writer", approver="rev-a",
                state="APPROVED",
                valid_reviewers=("campaign_envelope_ready",))

    def test_sealed_state_refuses(self):
        with self.assertRaises(FailClosedError):
            classify_approval(
                author="writer", approver="rev-a",
                state="send_authorized", valid_reviewers=_VALID)


if __name__ == "__main__":
    unittest.main()
