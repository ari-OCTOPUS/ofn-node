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
from ofn.adapters.lead_store import LeadStore
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


if __name__ == "__main__":
    unittest.main()
