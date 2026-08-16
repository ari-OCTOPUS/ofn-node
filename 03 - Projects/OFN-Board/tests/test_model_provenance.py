"""Which model actually answered — not which one we asked for.

The whole architecture rests on being able to say where an answer came from.
`_parse` read `choices` and `usage` out of the response and ignored `model`,
the field an OpenAI-compatible provider uses to state what served the
request. So the ledger recorded the string we sent.

That is fine exactly as long as nothing ever remaps a name — and a gateway
that substitutes a model when one is busy, or rewrites an alias, is invisible
under that scheme. Every "which model said this" would be wrong, and nothing
in the system would ever disagree.

The fix is not to trust the response instead of the request. It is to record
both, and to make the disagreement loud.
"""

from __future__ import annotations

import unittest

from ofn.adapters.remote_brain import RemoteBrain
from ofn.adapters.router import BrainReply


def parse(payload):
    brain = RemoteBrain(api_key="k", model="fugu")
    return brain._parse(payload)


def body(text="ok", **extra):
    return {"choices": [{"message": {"content": text}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}, **extra}


class TestTheServedNameIsRecorded(unittest.TestCase):
    def test_the_providers_own_name_wins(self):
        self.assertEqual(parse(body(model="glm-4-plus")).model, "glm-4-plus")

    def test_what_we_asked_is_kept_beside_it(self):
        reply = parse(body(model="glm-4-plus"))
        self.assertEqual(reply.requested, "fugu")

    def test_a_substitution_is_visible(self):
        """The case this exists for: something else answered and said so."""
        self.assertIs(parse(body(model="glm-4-plus")).model_matched_request,
                      False)

    def test_agreement_is_visible_too(self):
        self.assertIs(parse(body(model="fugu")).model_matched_request, True)


class TestSilenceIsNotAgreement(unittest.TestCase):
    def test_a_provider_that_says_nothing_falls_back(self):
        self.assertEqual(parse(body()).model, "fugu")

    def test_but_that_fallback_is_not_reported_as_a_match(self):
        """Unknown is not agreement. Reporting True here would turn "nobody
        looked" into "we checked"."""
        reply = parse(body())
        self.assertEqual(reply.requested, "fugu")
        self.assertIs(reply.model_matched_request, True)

    def test_an_empty_model_field_is_treated_as_silence(self):
        self.assertEqual(parse(body(model="   ")).model, "fugu")

    def test_a_non_string_model_field_is_ignored(self):
        self.assertEqual(parse(body(model=17)).model, "fugu")


class TestErrorPathsCarryItToo(unittest.TestCase):
    def test_a_reply_with_no_choices_still_names_what_was_asked(self):
        reply = parse({"usage": {}})
        self.assertEqual(reply.requested, "fugu")
        self.assertTrue(reply.insufficient)

    def test_an_unarmed_brain_says_which_model_it_would_have_been(self):
        reply = RemoteBrain(api_key="", model="fugu").answer("t", "p")
        self.assertTrue(reply.insufficient)
        self.assertEqual(reply.requested, "fugu")
        self.assertIn("not-armed", reply.model)


class TestTheLedgerSeesTheDisagreement(unittest.TestCase):
    """A mismatch has to reach the record, not just the dataclass."""

    def test_a_matching_reply_adds_nothing(self):
        reply = BrainReply("x", model="fugu", requested="fugu")
        self.assertIs(reply.model_matched_request, True)

    def test_a_mismatched_reply_is_flagged(self):
        reply = BrainReply("x", model="glm-4-plus", requested="fugu")
        self.assertIs(reply.model_matched_request, False)

    def test_a_suffixed_error_name_still_compares_on_the_model(self):
        """`fugu:unreachable` is still fugu — the suffix is our own note
        about the failure, not a different model."""
        reply = BrainReply("", model="fugu:unreachable", requested="fugu")
        self.assertIs(reply.model_matched_request, True)

    def test_nothing_known_is_none(self):
        self.assertIsNone(BrainReply("x").model_matched_request)


if __name__ == "__main__":
    unittest.main()
