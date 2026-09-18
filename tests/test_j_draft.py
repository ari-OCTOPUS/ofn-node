"""J1/J2 — strata email DRAFT generator. Tests first, per §5 of the task.

What this module is allowed to be, stated as tests rather than as a promise:

  * `draft_email_from_offer(lead, offer)` is PURE. It returns a payload and
    touches nothing — no DB, no outbox, no clock. Elaheh's correction to §6:
    the original signature let a draft reach the queue directly, which meant a
    killed node could still fill its own outbox. Generation and admission are
    now two different functions with two different blast radii.

  * `enqueue_draft(...)` takes an *enqueue callable* with the signature of
    `node._gate_enqueue` — the existing choke point at node.py:3036 that
    checks the kill switch. It never imports Outbox and never calls
    `outbox.enqueue` itself. `test_kill_switch_blocks_enqueue` is the test
    that would fail if someone "simplified" that back to a direct write.

  * Every claim in the body traces to an item in Offer v0.3, and the two
    numbers the Offer deliberately withholds from customer-facing prose
    ($400 minimum, 8 before/after photos) stay in config for qualification
    and never appear in an email. The Offer's own §8 gives the reason: Ari
    sets prices, and the photo count may grow — an email that names either
    becomes a lie later without anyone editing it.

Nothing here sends. The end state of a successful draft is `status=pending`
in the outbox, waiting for a human.

One deviation from §3 of the task, which named `ofn/config/offer.py`: a module
`ofn/config.py` already exists and is imported in nineteen places, so a
`ofn/config/` package would shadow it and take the suite down. The offer lives
at `ofn/offer_v0_3.py` instead — same intent, no collision. It is a Python
dict rather than YAML because PyYAML is not installed and §4.8 forbids adding
it; `packs/` parses its own YAML subset by hand for the same reason.
"""

from __future__ import annotations

import os
import re
import unittest

from ofn.adapters.facts import FactStore
from ofn.adapters.ledger import Ledger
from ofn.adapters.lead_store import LeadStore
from ofn.adapters.outbox import Outbox, PENDING
from ofn.adapters.packloader import load_pack
from ofn.agents import j_draft
from ofn.agents.lead_email_writer import FORBIDDEN
from ofn import offer_v0_3 as offer_config
from ofn.kernel.domain import RiskTier
from ofn.kernel.tenancy import TenantRegistry
from ofn.node import Node
from tests.tmpdir import temp_dir

NOW_S = 1_800_000_000
NOW_ISO = "2026-09-16T00:00:00Z"

# The first real use of this code path (§1 of the task): Tim at Sara Strata,
# who is waiting on an email. A lead row with no price, no ABN, no licence —
# which is the normal case, and the case that tempts a generator to invent.
SARA_STRATA = {
    "lead_id": "lead-sara-strata-001",
    "tenant_id": "lead",
    "source": "phone",
    "customer_name": "Tim",
    "email": "tim@sarastrata.example.com.au",
    "phone": "",
    "suburb": "Chatswood",
    "job_type": "strata exterior repaint",
    "message": "Asked for something in writing about the free assessment.",
    "status": "new",
}


def registry():
    return TenantRegistry({"lead": load_pack("packs/lead.yaml")})


class _Base(unittest.TestCase):
    """A real Node with a real Outbox — the same wiring test_painting_outbox
    uses. Nothing is stubbed on the admission path, because the admission
    path is the thing under test."""

    def setUp(self):
        d = temp_dir(self)
        self.outbox = Outbox(os.path.join(d, "o.sqlite"))
        self.ledger = Ledger(os.path.join(d, "l.sqlite"))
        self.painting = LeadStore(os.path.join(d, "p.sqlite"))
        self.node = Node(
            registry=registry(), quota=None,
            ledger=self.ledger, facts=FactStore(os.path.join(d, "f.sqlite")),
            outbox=self.outbox,
            now_epoch_s=lambda: NOW_S, now_iso=lambda: NOW_ISO,
            painting=self.painting)
        self.scope = self.node.registry.scope("lead")
        self.offer = offer_config.load_offer()

    def tearDown(self):
        self.painting.close()
        self.outbox.close()
        self.ledger.close()

    def draft(self, lead=None, offer=None):
        return j_draft.draft_email_from_offer(lead or SARA_STRATA,
                                              offer or self.offer)

    def enqueue(self, lead=None, offer=None):
        return j_draft.enqueue_draft(
            self.node._gate_enqueue, self.scope,
            lead or SARA_STRATA, offer or self.offer, NOW_ISO)


# ── §5.1 — fact-only ────────────────────────────────────────────────────────

class TestFactOnly(_Base):
    """A lead carrying no price, no ABN, no licence and no insurance figure
    must not receive an email that contains any of them."""

    # Patterns that only ever appear in a *fabricated* claim, given a lead and
    # an Offer that contain none of these facts.
    FABRICATION = (
        (r"\$\s*\d", "a dollar figure"),
        (r"\b\d+\s*(?:%|per\s?cent)", "a percentage"),
        (r"\bABN\b", "an ABN claim"),
        (r"\b\d{2}\s?\d{3}\s?\d{3}\s?\d{3}\b", "an ABN-shaped number"),
        (r"\blicen[cs]e\b", "a licence claim"),
        (r"\bwarrant(?:y|ies)\b", "a warranty claim"),
        (r"\b\d+\s*(?:year|yr)s?\b", "a duration claim"),
        (r"\b\d+\s*(?:building|propert)", "a building count"),
    )

    def test_no_fabricated_facts_in_subject_or_body(self):
        d = self.draft()
        text = (d["subject"] + "\n" + d["body"])
        for pattern, what in self.FABRICATION:
            self.assertIsNone(
                re.search(pattern, text, re.IGNORECASE),
                f"draft fabricated {what}; Offer v0.3 does not supply it:\n{text}")

    def test_insurance_is_claimed_without_a_figure(self):
        """Offer item 7 permits the words 'fully insured' and forbids the
        coverage amount. Both halves are asserted — dropping the claim is as
        wrong as inventing the number."""
        body = self.draft()["body"].lower()
        self.assertIn("insured", body)
        self.assertIsNone(re.search(r"\$\s*\d|\bmillion\b|\bm\b\s*cover", body))

    def test_no_robot_cliches(self):
        """The guard list is reused from lead_email_writer (R2) rather than
        rewritten — that module stays untouched; only its FORBIDDEN travels."""
        text = (self.draft()["subject"] + "\n" + self.draft()["body"]).lower()
        for bad in FORBIDDEN:
            self.assertNotIn(bad, text)


# ── the numbers the Offer withholds on purpose ──────────────────────────────

class TestWithheldNumbersStayInConfig(_Base):
    """Elaheh's answer to Q1: $400 and '8 photos' are facts we hold, not
    claims we make. They belong to qualification (I3), never to prose."""

    def test_config_actually_carries_them(self):
        self.assertEqual(self.offer["min_project_value_aud"], 400)
        self.assertEqual(self.offer["proof_photo_count"], 8)

    def test_minimum_value_never_reaches_the_body(self):
        text = (self.draft()["subject"] + self.draft()["body"])
        self.assertNotIn("400", text)
        self.assertIsNone(re.search(r"minimum|hard floor", text, re.IGNORECASE))

    def test_photo_count_never_reaches_the_body(self):
        """'documented before-and-after results' is the honest form: it stays
        true when the count changes."""
        d = self.draft()
        text = d["subject"] + d["body"]
        self.assertIsNone(re.search(r"\b8\b|\beight\b", text, re.IGNORECASE))
        self.assertIn("before", d["body"].lower())


# ── §5.2 — unknown is explicit ──────────────────────────────────────────────

class TestUnknownIsExplicit(_Base):
    def test_missing_offer_field_becomes_a_visible_placeholder(self):
        """A stripped Offer must not silently drop the sentence, and must not
        guess. It must hand the owner something they can see and fill."""
        thin = dict(self.offer)
        del thin["insurance_status"]
        d = self.draft(offer=thin)
        self.assertIn("[OWNER INPUT REQUIRED: insurance_status]", d["body"])
        self.assertIn("insurance_status", d["placeholders"])

    def test_missing_lead_name_becomes_a_placeholder_not_a_guess(self):
        nameless = dict(SARA_STRATA, customer_name="")
        d = self.draft(lead=nameless)
        self.assertIn("[OWNER INPUT REQUIRED: contact_name]", d["body"])
        self.assertNotIn("Dear Sir", d["body"])
        self.assertNotIn("To whom", d["body"])

    def test_a_complete_offer_leaves_no_placeholders(self):
        d = self.draft()
        self.assertEqual(d["placeholders"], [])
        self.assertNotIn("OWNER INPUT REQUIRED", d["body"])


# ── §5.4 — offer-bound ──────────────────────────────────────────────────────

class TestOfferBound(_Base):
    def test_every_claim_traces_to_an_offer_item(self):
        d = self.draft()
        self.assertTrue(d["offer_refs"], "draft cited no offer items")
        for ref in d["offer_refs"]:
            self.assertIn(ref, self.offer,
                          f"draft cited {ref!r}, which is not in Offer v0.3")

    def test_the_cta_is_the_offer_cta(self):
        """Offer item 2 — one action, the no-obligation condition assessment."""
        body = self.draft()["body"].lower()
        self.assertIn("no-obligation", body)
        self.assertIn("assessment", body)
        self.assertIn("primary_cta", self.draft()["offer_refs"])

    def test_a_claim_absent_from_the_offer_is_not_generated(self):
        """Offer v0.3 has no award, no certification, no client testimonial."""
        body = self.draft()["body"].lower()
        for absent in ("award", "certified", "accredited", "guarantee",
                       "testimonial", "five star", "5 star", "abn"):
            self.assertNotIn(absent, body)

    def test_generator_refuses_an_offer_of_the_wrong_version(self):
        """Content is bound to v0.3 specifically. A future v0.4 with different
        permissions must not be silently rendered by v0.3 logic."""
        with self.assertRaises(ValueError):
            self.draft(offer=dict(self.offer, version="0.4"))


# ── §5.3 / §5.5 / §5.6 — admission ──────────────────────────────────────────

class TestEnqueue(_Base):
    def test_enqueue_creates_exactly_one_pending_item(self):
        res = self.enqueue()
        self.assertTrue(res["ok"])
        self.assertTrue(res["queued"])
        pending = self.outbox.pending(self.scope)
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].status, PENDING)

    def test_second_enqueue_for_the_same_lead_is_a_no_op(self):
        """§5.3 — the idem_key is stable across calls, so a retry cannot
        produce a second draft of the same email."""
        first = self.enqueue()
        second = self.enqueue()
        self.assertTrue(first["queued"])
        self.assertFalse(second["queued"])
        self.assertEqual(first["idem_key"], second["idem_key"])
        self.assertEqual(len(self.outbox.pending(self.scope)), 1)

    def test_status_is_pending_and_nothing_else(self):
        """§5.6 — not approved, not sent, not in flight. The draft's entire
        journey ends at the queue; a human moves it or it does not move."""
        self.enqueue()
        item = self.outbox.get(self.scope, self.enqueue()["idem_key"])
        self.assertEqual(item.status, PENDING)
        self.assertEqual(item.attempts, 0)
        self.assertEqual(self.outbox.counts(self.scope).get("sent", 0), 0)

    def test_queued_at_red(self):
        """Email leaves the device and carries a customer's name — RED, the
        same tier send_lead_reply uses for the same reason."""
        self.enqueue()
        self.assertEqual(self.outbox.pending(self.scope)[0].tier, RiskTier.RED)

    def test_tenant_is_carried_by_key_and_payload(self):
        """§5.5 — tenant travels in the scope, in the payload, and in the key,
        so no read path can lose it."""
        res = self.enqueue()
        item = self.outbox.pending(self.scope)[0]
        self.assertEqual(item.tenant, "lead")
        self.assertEqual(item.payload["tenant"], "lead")
        self.assertIn("lead", res["idem_key"])

    def test_kind_matches_the_existing_lead_namespace(self):
        """node.py already queues 'lead:reply' and 'lead:quote'. A draft is a
        third member of that family, not a new vocabulary."""
        self.enqueue()
        self.assertEqual(self.outbox.pending(self.scope)[0].kind, "lead:draft")


# ── the architectural decision, as a test ───────────────────────────────────

class TestKillSwitchIsNotBypassed(_Base):
    def test_a_killed_node_queues_nothing(self):
        """This is the whole reason draft and enqueue were split. If a future
        edit makes j_draft call `outbox.enqueue` directly, this goes red."""
        self.node.killed = True
        res = self.enqueue()
        self.assertFalse(res["ok"])
        self.assertEqual(res.get("rule"), "gate:kill-switch")
        self.assertEqual(self.outbox.pending(self.scope), [])
        self.assertEqual(len(self.outbox.pending(self.scope)), 0)

    def test_j_draft_does_not_import_the_outbox(self):
        """Structural, not behavioural: the module has no way to reach the
        queue except through the callable it is handed."""
        import inspect
        src = inspect.getsource(j_draft)
        self.assertNotIn("from ..adapters.outbox", src)
        self.assertNotIn("import outbox", src)
        self.assertNotIn(".enqueue(", src)


class TestDraftIsPure(_Base):
    def test_drafting_writes_nothing(self):
        before = self.outbox.counts(self.scope)
        self.draft()
        self.draft()
        self.assertEqual(self.outbox.counts(self.scope), before)
        self.assertEqual(self.outbox.pending(self.scope), [])

    def test_same_input_same_output(self):
        self.assertEqual(self.draft(), self.draft())

    def test_different_leads_get_different_keys(self):
        other = dict(SARA_STRATA, lead_id="lead-other-002")
        self.assertNotEqual(j_draft.draft_idem_key(SARA_STRATA, self.offer),
                            j_draft.draft_idem_key(other, self.offer))


# ── §4.6 — no raw PII ───────────────────────────────────────────────────────

class TestNoRawRecipientPII(_Base):
    def test_recipient_address_is_hashed_in_the_payload(self):
        """The queue row is durable and is read by the digest and the owner
        panel. The address itself stays in LeadStore, addressable by lead_id
        when a human is actually ready to send."""
        self.enqueue()
        payload = self.outbox.pending(self.scope)[0].payload
        blob = str(payload)
        self.assertNotIn("tim@sarastrata.example.com.au", blob)
        self.assertIn("to_digest", payload)
        self.assertEqual(len(payload["to_digest"]), 16)
        self.assertEqual(payload["lead_id"], SARA_STRATA["lead_id"])

    def test_the_digest_is_stable_and_specific(self):
        a = j_draft.contact_digest("tim@sarastrata.example.com.au")
        b = j_draft.contact_digest("tim@sarastrata.example.com.au")
        c = j_draft.contact_digest("someone@else.example.com")
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)


if __name__ == "__main__":
    unittest.main()
