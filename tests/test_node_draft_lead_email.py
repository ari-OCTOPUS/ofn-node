"""J1 wiring: `Node.draft_lead_email` puts a fact-only draft in the queue.

`j_draft` has been on main and tested since #262, but nothing in the product
called it — the generator was a library with no caller. This is the contract
for the one method that connects it, and the contract is deliberately narrow:

  - the draft reaches `outbox` at `pending` and stops there — no send, ever
  - the enqueue goes through `Node._gate_enqueue`, so a killed node queues
    nothing from this path either
  - the failure shape matches `send_lead_reply`: no store / no pack / no lead
    all return a Persian error rather than raising
  - a fabricated claim is refused cleanly, not as a traceback

These use the real Node with a real Outbox, Ledger and LeadStore — same as
`test_painting_outbox` — so the path exercised here is the one the live
service runs, not a lambda standing in for the gate.
"""

import os
import unittest
from unittest import mock

from ofn.adapters.facts import FactStore
from ofn.adapters.ledger import Ledger
from ofn.adapters.lead_store import TERMINAL_LEAD_STATUSES, LeadStore
from ofn.adapters.outbox import PENDING, Outbox
from ofn.adapters.packloader import load_pack
from ofn.agents import j_draft
from ofn.kernel.domain import RiskTier
from ofn.kernel.tenancy import TenantRegistry
from ofn.node import Node
from ofn.offer_v0_3 import FORBIDDEN_CLAIMS, QUALIFICATION_ONLY, load_offer
from tests.tmpdir import temp_dir

NOW_S = 1_800_000_000
NOW_ISO = "2026-08-07T00:00:00Z"
LEAD_EMAIL = "sara@example.com"


def registry():
    pack = load_pack("packs/lead.yaml")
    return TenantRegistry({"lead": pack})


class _Base(unittest.TestCase):
    def setUp(self):
        d = temp_dir(self)
        self.outbox = Outbox(os.path.join(d, "o.sqlite"))
        self.addCleanup(self.outbox.close)
        self.ledger = Ledger(os.path.join(d, "l.sqlite"))
        self.painting = LeadStore(os.path.join(d, "p.sqlite"))
        self.addCleanup(self.painting.close)
        self.node = Node(
            registry=registry(), quota=None,
            ledger=self.ledger, facts=FactStore(os.path.join(d, "f.sqlite")),
            outbox=self.outbox,
            now_epoch_s=lambda: NOW_S, now_iso=lambda: NOW_ISO,
            painting=self.painting)
        self.scope = self.node.registry.scope("lead")

    def seed_lead(self, **extra):
        """A strata lead as intake actually stores one: a name, a way to
        reach them, and no money. Nothing here supplies a price, and that is
        the point — every figure in the queue would have to be invented."""
        body = {"customer_name": "سارا", "email": LEAD_EMAIL,
                "phone": "0400111222", "suburb": "Marrickville",
                "job_type": "رنگ ساختمان", "source": "web"}
        body.update(extra)
        out = self.node.create_painting_lead(body, actor="owner")
        self.assertTrue(out["ok"], out)
        return out["lead"]["lead_id"]

    def pending_items(self):
        return list(self.outbox.pending(self.scope, limit=50))


class TestDraftLeadEmailHappyPath(_Base):
    def test_draft_is_queued_pending_at_red(self):
        lead_id = self.seed_lead()

        out = self.node.draft_lead_email(lead_id)

        self.assertTrue(out["ok"], out)
        self.assertTrue(out["queued"])
        items = self.pending_items()
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item.kind, "lead:draft")
        self.assertEqual(item.kind, j_draft.KIND)
        self.assertEqual(item.tier, RiskTier.RED)
        self.assertEqual(item.status, PENDING)
        self.assertEqual(item.payload["lead_id"], lead_id)
        self.assertEqual(item.payload["channel"], "email")

    def test_queue_row_carries_the_digest_not_the_address(self):
        # The address stays in LeadStore and is resolved by lead_id at send
        # time; the durable queue row the owner panel reads holds a handle.
        lead_id = self.seed_lead()

        self.node.draft_lead_email(lead_id)

        payload = self.pending_items()[0].payload
        self.assertEqual(payload["to_digest"],
                         j_draft.contact_digest(LEAD_EMAIL))
        self.assertNotIn(LEAD_EMAIL, repr(payload))


class TestDraftLeadEmailKillSwitch(_Base):
    """The one that matters most: a killed node is a closed door on every
    path, and this is a new path."""

    def test_killed_node_queues_nothing(self):
        lead_id = self.seed_lead()
        self.node.killed = True

        out = self.node.draft_lead_email(lead_id)

        self.assertFalse(out["ok"])
        self.assertEqual(out["rule"], "gate:kill-switch")
        self.assertEqual(self.pending_items(), [])

    def test_killed_node_does_not_leak_the_address_in_the_refusal(self):
        # `enqueue_draft` builds the draft before offering it to the gate, so
        # the refusal dict carries a `draft` the caller never asked for. That
        # object must be as address-free as the queue row would have been: a
        # killed node must not become a second way for PII to get out.
        lead_id = self.seed_lead()
        self.node.killed = True

        out = self.node.draft_lead_email(lead_id)

        self.assertFalse(out["ok"])
        self.assertNotIn(LEAD_EMAIL, repr(out))
        self.assertNotIn(LEAD_EMAIL.split("@")[0], repr(out))
        draft = out.get("draft")
        if draft is not None:
            self.assertEqual(draft["to_digest"],
                             j_draft.contact_digest(LEAD_EMAIL))
            self.assertNotIn(LEAD_EMAIL, list(draft.values()))


class TestDraftLeadEmailFailClosed(_Base):
    def test_unknown_lead_is_refused_in_persian(self):
        out = self.node.draft_lead_email("lead:does-not-exist")

        self.assertFalse(out["ok"])
        self.assertEqual(out["error"], "لید پیدا نشد")
        self.assertEqual(self.pending_items(), [])

    def test_node_without_the_lead_pack_is_refused_in_persian(self):
        # A LeadStore is wired but this node does not carry the lead pack, so
        # `_lead_scope()` has no tenant to mint. Refuse rather than reach for
        # a scope that does not exist on this node.
        d = temp_dir(self)
        outbox = Outbox(os.path.join(d, "o3.sqlite"))
        self.addCleanup(outbox.close)
        packless = Node(
            registry=TenantRegistry({"studio": load_pack("packs/studio.yaml")}),
            quota=None,
            ledger=Ledger(os.path.join(d, "l3.sqlite")),
            facts=FactStore(os.path.join(d, "f3.sqlite")),
            outbox=outbox,
            now_epoch_s=lambda: NOW_S, now_iso=lambda: NOW_ISO,
            painting=self.painting)

        out = packless.draft_lead_email("lead:anything")

        self.assertFalse(out["ok"])
        self.assertEqual(out["error"], "پک لید نقاشی روی این نود نیست")
        self.assertEqual(self.pending_items(), [])

    def test_node_without_lead_store_is_refused_in_persian(self):
        d = temp_dir(self)
        outbox = Outbox(os.path.join(d, "o2.sqlite"))
        self.addCleanup(outbox.close)
        bare = Node(
            registry=registry(), quota=None,
            ledger=Ledger(os.path.join(d, "l2.sqlite")),
            facts=FactStore(os.path.join(d, "f2.sqlite")),
            outbox=outbox,
            now_epoch_s=lambda: NOW_S, now_iso=lambda: NOW_ISO)

        out = bare.draft_lead_email("lead:anything")

        self.assertFalse(out["ok"])
        self.assertEqual(out["error"], "ذخیره‌ساز لید وصل نیست")
        self.assertEqual(list(outbox.pending(self.scope, limit=50)), [])


class TestDraftLeadEmailIdempotent(_Base):
    def test_drafting_twice_leaves_one_item(self):
        # Same lead, same offer, same draft — the second call must recognise
        # its own earlier work rather than give the owner a duplicate to read.
        lead_id = self.seed_lead()

        first = self.node.draft_lead_email(lead_id)
        second = self.node.draft_lead_email(lead_id)

        self.assertTrue(first["ok"], first)
        self.assertTrue(first["queued"])
        self.assertTrue(second["ok"], second)
        self.assertFalse(second["queued"])
        self.assertEqual(second["idem_key"], first["idem_key"])
        self.assertEqual(len(self.pending_items()), 1)


class TestDraftLeadEmailFactOnly(_Base):
    def test_queued_draft_invents_no_figure(self):
        # End to end: the lead arrives with no price and no ABN, the offer
        # holds figures it may qualify on but never state, and what lands in
        # the queue must contain neither.
        lead_id = self.seed_lead(budget_text="", message="ساختمان ما نیاز به رنگ دارد")

        out = self.node.draft_lead_email(lead_id)
        self.assertTrue(out["ok"], out)

        payload = self.pending_items()[0].payload
        text = str(payload["subject"]) + "\n" + str(payload["body"])
        self.assertFalse(any(ch.isdigit() for ch in text),
                         f"draft states a figure nobody supplied: {text!r}")
        lowered = text.lower()
        for claim in FORBIDDEN_CLAIMS:
            self.assertNotIn(claim, lowered)
        offer = load_offer()
        for field in QUALIFICATION_ONLY:
            value = offer.get(field)
            if isinstance(value, (int, float)):
                self.assertNotIn(str(value), text)
        # Every sentence that made a claim cites the offer key it came from,
        # and nothing was left as an owner-input placeholder.
        self.assertEqual(payload["placeholders"], [])
        self.assertTrue(payload["offer_refs"])
        for key in payload["offer_refs"]:
            self.assertIn(key, offer)


class TestDraftLeadEmailFabricatedOffer(_Base):
    def test_tampered_offer_is_refused_without_crashing(self):
        lead_id = self.seed_lead()
        tampered = load_offer()
        tampered["insurance_status"] = "fully insured and ABN certified"

        with mock.patch("ofn.offer_v0_3.load_offer", return_value=tampered):
            out = self.node.draft_lead_email(lead_id)

        self.assertFalse(out["ok"])
        self.assertIn("error", out)
        self.assertEqual(self.pending_items(), [])


class TestDraftLeadEmailSuppression(_Base):
    """A terminal lead must not receive a new draft.

    `draft_lead_email` used to check only that the row existed, so a lead
    marked spam, archived, lost or won was as draftable as a live one — the
    generator would happily write to someone who had asked to be left alone,
    or to a job that closed months ago. The refusal is per-status rather than
    one blanket message because the owner has to be able to read *why* a
    draft was withheld, so each carries its own `rule` code.

    Every case asserts the queue as well as the return value: the check sits
    before `_gate_enqueue`, and a refusal that still queued something would
    be the only failure that matters.
    """

    def suppressed_lead(self, status, **extra):
        """Seed a live lead and drive it to `status` through the real path.

        `spam`, `archived` and `lost` are ordinary owner classifications from
        `new`. `won` is not: it is delivery-derived, so `update_lead` refuses
        it and only `record_booked_revenue` can mint it. Seeding it the long
        way keeps the fixture honest about how a lead actually reaches won.
        """
        lead_id = self.seed_lead(**extra)
        if status == "won":
            out = self.painting.record_booked_revenue(
                self.scope.tenant.value, lead_id, amount_cents=250_000,
                booked_at=NOW_ISO, authority="owner")
        else:
            out = self.node.update_painting_lead(
                lead_id, {"status": status}, actor="owner")
        self.assertTrue(out["ok"], out)
        self.assertEqual(
            self.painting.get(self.scope.tenant.value, lead_id)["status"],
            status)
        return lead_id

    def test_spam_lead_is_refused_and_queues_nothing(self):
        lead_id = self.suppressed_lead("spam")

        out = self.node.draft_lead_email(lead_id)

        self.assertFalse(out["ok"])
        self.assertEqual(out["error"], "لید مسدود است")
        self.assertEqual(out["rule"], "suppression:spam-or-archived")
        self.assertEqual(self.pending_items(), [])

    def test_archived_lead_is_refused_and_queues_nothing(self):
        lead_id = self.suppressed_lead("archived")

        out = self.node.draft_lead_email(lead_id)

        self.assertFalse(out["ok"])
        self.assertEqual(out["error"], "لید مسدود است")
        self.assertEqual(out["rule"], "suppression:spam-or-archived")
        self.assertEqual(self.pending_items(), [])

    def test_lost_lead_is_refused_and_queues_nothing(self):
        lead_id = self.suppressed_lead("lost")

        out = self.node.draft_lead_email(lead_id)

        self.assertFalse(out["ok"])
        self.assertEqual(out["error"], "لید از دست رفته است")
        self.assertEqual(out["rule"], "suppression:lost")
        self.assertEqual(self.pending_items(), [])

    def test_won_lead_is_refused_and_queues_nothing(self):
        # `won` is terminal too, and blocked by default: a closed job is not
        # an outreach target. If quote follow-up ever wants this path, it is
        # one branch to delete — but it has to be a decision, not a gap.
        lead_id = self.suppressed_lead("won")

        out = self.node.draft_lead_email(lead_id)

        self.assertFalse(out["ok"])
        self.assertEqual(out["error"], "لید بسته شده است")
        self.assertEqual(out["rule"], "suppression:won")
        self.assertEqual(self.pending_items(), [])

    def test_every_suppression_refusal_is_persian(self):
        # The method's other refusals are Persian; a suppression that answered
        # in English would be the one error the owner cannot read. Distinct
        # `source_ref` values keep the four leads apart — `lead_id` is derived
        # from source, source_ref and the (frozen) clock.
        statuses = ("spam", "archived", "lost", "won")
        # If this fails, a terminal status was added and the branches above
        # never grew one — the catch-all is carrying it with a generic
        # message. Give it its own message, or accept the generic one here.
        self.assertEqual(set(statuses), set(TERMINAL_LEAD_STATUSES))
        seen = set()
        for i, status in enumerate(statuses):
            lead_id = self.suppressed_lead(status, source_ref=f"ref-{i}")

            out = self.node.draft_lead_email(lead_id)

            self.assertFalse(out["ok"], (status, out))
            self.assertTrue(out["rule"].startswith("suppression:"), out)
            message = out["error"]
            self.assertTrue(message.strip(), status)
            self.assertFalse(
                any(ch.isascii() and ch.isalpha() for ch in message),
                f"{status} refuses in English: {message!r}")
            seen.add(out["rule"])
        self.assertEqual(len(seen), 3)  # spam and archived share one rule
        self.assertEqual(self.pending_items(), [])

    def test_a_future_terminal_status_is_refused_by_the_catch_all(self):
        # The four branches above are literals; TERMINAL_LEAD_STATUSES is the
        # source of truth. Add a fifth terminal status there — "blocked", say
        # — and without this catch-all the method would quietly go back to
        # drafting for it. The status cannot be stored (the column's CHECK
        # knows only today's eight), so the future is staged rather than
        # written: the set gains a member and the store hands back a row
        # carrying it.
        future = frozenset(TERMINAL_LEAD_STATUSES | {"blocked"})
        lead_id = self.seed_lead()
        blocked = dict(self.painting.get(self.scope.tenant.value, lead_id))
        blocked["status"] = "blocked"

        with mock.patch("ofn.node.TERMINAL_LEAD_STATUSES", future), \
                mock.patch.object(self.painting, "get", return_value=blocked):
            out = self.node.draft_lead_email(lead_id)

        self.assertFalse(out["ok"])
        self.assertEqual(out["error"], "لید نهایی است")
        self.assertEqual(out["rule"], "suppression:blocked")
        self.assertEqual(self.pending_items(), [])

    def test_a_live_lead_still_drafts(self):
        # The regression guard: suppression must not cost the happy path.
        lead_id = self.seed_lead()
        self.assertEqual(
            self.painting.get(self.scope.tenant.value, lead_id)["status"],
            "new")

        out = self.node.draft_lead_email(lead_id)

        self.assertTrue(out["ok"], out)
        self.assertTrue(out["queued"])
        self.assertEqual(len(self.pending_items()), 1)


if __name__ == "__main__":
    unittest.main()
