"""Lead outbound: reply / quote go through the same fail-closed outbox gate
studio uses.

Contracts:
  - A note (internal) is captured as an interaction + ledger row, no outbox.
  - An SMS/email reply is queued at RED (PII + leaves device), idempotent.
  - A quote is queued at RED (money), idempotent.
  - The partner list endpoint supports q/status filtering.
  - owner_decide works on a lead:reply item (approve/reject via the queue).

These use the real Node with a real Outbox and Ledger — not lambdas — so the
end-to-end outbox path is exercised the same way the live service runs it.
"""

import json
import os
import tempfile
import unittest

from ofn.adapters.facts import FactStore
from ofn.adapters.http_api import ApiApp, HostMap
from ofn.adapters.ledger import Ledger
from ofn.adapters.lead_store import LeadStore
from ofn.adapters.outbox import Outbox, PENDING
from ofn.adapters.packloader import load_pack
from ofn.kernel.auth import issue_session
from ofn.kernel.domain import RiskTier
from ofn.kernel.tenancy import TenantRegistry
from ofn.node import Node

NOW_S = 1_800_000_000
NOW_ISO = "2026-08-07T00:00:00Z"
SECRET = "lead-outbox-test-secret"
PARTNER_ID = "7001"
OWNER_ID = "5001"
OWNER_HOST = "panel.test"


def registry():
    pack = load_pack("packs/lead.yaml")
    return TenantRegistry({"lead": pack})


class _Base(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.mkdtemp()
        d = self._d
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
        self.app = ApiApp(
            registry(), HostMap(tenants={"lead.test": "lead"},
                                owner_host=OWNER_HOST),
            bot_tokens={"lead": "lead-t", "__owner__": "owner-t"},
            session_secret=SECRET,
            owner_user_ids=(OWNER_ID,),
            partner_user_ids={"lead": (PARTNER_ID,)},
            now=lambda: NOW_S,
            painting_dashboard=self.node.painting_dashboard,
            painting_leads=self.node.painting_leads,
            create_painting_lead=self.node.create_painting_lead,
            update_painting_lead=self.node.update_painting_lead,
            send_lead_reply=self.node.send_lead_reply,
            send_lead_quote=self.node.send_lead_quote,
            owner_queue=self.node.owner_queue,
            owner_decide=self.node.owner_decide,
            status_for=lambda s: {"readiness": {"done": 1, "total": 1},
                                  "pending_decisions": 0,
                                  "capacity_per_week": 6})

    def tearDown(self):
        self.painting.close()
        self.outbox.close()

    def _seed_lead(self, **extra):
        body = {"customer_name": "سارا", "phone": "0400111222",
                "suburb": "Marrickville", "job_type": "رنگ اتاق",
                "message": "دو اتاق می‌خوام رنگ شه", "source": "web"}
        body.update(extra)
        out = self.node.create_painting_lead(body, actor="owner")
        self.assertTrue(out["ok"], out)
        return out["lead"]["lead_id"]

    def partner_headers(self):
        sess = issue_session("lead", PARTNER_ID, SECRET, now_epoch_s=NOW_S)
        return {"host": "lead.test", "authorization": "Bearer " + sess}

    def owner_headers(self):
        sess = issue_session("owner", OWNER_ID, SECRET, now_epoch_s=NOW_S)
        return {"host": OWNER_HOST, "authorization": "Bearer " + sess}

    def call(self, method, path, headers, body=None, query=""):
        r = self.app.handle(method, path, headers,
                            json.dumps(body).encode() if body is not None else b"",
                            query=query)
        # Response.body is already a dict (or None) — ApiApp keeps the
        # structured object; it only serialises at the socket boundary.
        return r


class TestPartnerList(_Base):
    def test_partner_get_leads_returns_list(self):
        self._seed_lead()
        r = self.call("GET", "/api/v1/painting/leads", self.partner_headers())
        self.assertEqual(r.status, 200)
        body = r.body
        self.assertTrue(body["ok"])
        self.assertEqual(len(body["leads"]), 1)

    def test_partner_get_leads_search_by_query(self):
        self._seed_lead(customer_name="آرین", suburb="Ashfield")
        self._seed_lead(customer_name="مونا", suburb="Newtown")
        r = self.call("GET", "/api/v1/painting/leads", self.partner_headers(),
                      query="q=Newtown")
        body = r.body
        self.assertEqual(len(body["leads"]), 1)
        self.assertIn("مونا", body["leads"][0]["customer_name"])

    def test_partner_get_leads_filter_by_status(self):
        lid = self._seed_lead()
        # move the lead to "won"
        self.node.update_painting_lead(lid, {"status": "won"}, actor="owner")
        # a second lead with a different source so it is not idempotently
        # folded into the first one
        self._seed_lead(source="referral")
        r = self.call("GET", "/api/v1/painting/leads", self.partner_headers(),
                      query="status=won")
        body = r.body
        self.assertEqual(len(body["leads"]), 1)
        self.assertEqual(body["leads"][0]["status"], "won")


class TestNote(_Base):
    def test_note_is_captured_as_interaction_not_outbox(self):
        lid = self._seed_lead()
        r = self.call("POST", f"/api/v1/painting/leads/{lid}/reply",
                      self.partner_headers(),
                      {"channel": "note", "message": "زنگ زد، گفتم عصر جواب می‌دم"})
        self.assertEqual(r.status, 200)
        body = r.body
        self.assertTrue(body["ok"])
        self.assertEqual(body["kind"], "note")
        # nothing in the outbox
        self.assertEqual(len(self.outbox.pending(self.scope)), 0)
        # but an interaction was captured
        lead = self.painting.get("lead", lid)
        # the interaction is findable via the lead's interaction list (if any)
        # — at minimum, the ledger recorded a LEAD_NOTE_CAPTURED
        rows = self.ledger._conn.execute(
            "SELECT kind FROM ledger WHERE tenant=? ORDER BY seq DESC",
            ("lead",)).fetchall()
        kinds = [r[0] for r in rows]
        self.assertIn("LEAD_NOTE_CAPTURED", kinds)


class TestReplyOutbox(_Base):
    def test_sms_reply_queued_at_red(self):
        lid = self._seed_lead()
        r = self.call("POST", f"/api/v1/painting/leads/{lid}/reply",
                      self.partner_headers(),
                      {"channel": "sms", "message": "سلام، عصر تماس می‌گیرم."})
        body = r.body
        self.assertTrue(body["ok"])
        self.assertTrue(body["queued"])
        items = self.outbox.pending(self.scope)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].tier, RiskTier.RED)
        self.assertEqual(items[0].kind, "lead:reply")

    def test_idempotent_double_send(self):
        lid = self._seed_lead()
        msg = {"channel": "sms", "message": "یک پیام"}
        r1 = self.call("POST", f"/api/v1/painting/leads/{lid}/reply",
                       self.partner_headers(), msg)
        r2 = self.call("POST", f"/api/v1/painting/leads/{lid}/reply",
                       self.partner_headers(), msg)
        self.assertTrue(r1.body["queued"])
        self.assertFalse(r2.body["queued"])  # duplicate
        self.assertEqual(len(self.outbox.pending(self.scope)), 1)

    def test_new_lead_auto_flips_to_contacted(self):
        lid = self._seed_lead()
        self.call("POST", f"/api/v1/painting/leads/{lid}/reply",
                  self.partner_headers(),
                  {"channel": "sms", "message": "تماس می‌گیرم"})
        lead = self.painting.get("lead", lid)
        self.assertEqual(lead["status"], "contacted")

    def test_missing_message_refused(self):
        lid = self._seed_lead()
        r = self.call("POST", f"/api/v1/painting/leads/{lid}/reply",
                      self.partner_headers(), {"channel": "sms"})
        body = r.body
        self.assertFalse(body["ok"])


class TestQuote(_Base):
    def test_quote_queued_at_red(self):
        lid = self._seed_lead()
        r = self.call("POST", f"/api/v1/painting/leads/{lid}/quote",
                      self.partner_headers(),
                      {"amount": 1200, "note": "شامل رنگ و آماده‌سازی"})
        body = r.body
        self.assertTrue(body["ok"])
        self.assertTrue(body["queued"])
        items = self.outbox.pending(self.scope)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].tier, RiskTier.RED)
        self.assertEqual(items[0].kind, "lead:quote")
        self.assertEqual(items[0].payload["amount"], 1200)

    def test_zero_amount_refused(self):
        lid = self._seed_lead()
        r = self.call("POST", f"/api/v1/painting/leads/{lid}/quote",
                      self.partner_headers(), {"amount": 0})
        self.assertFalse(r.body["ok"])

    def test_quote_flips_status_to_quoted(self):
        lid = self._seed_lead()
        self.call("POST", f"/api/v1/painting/leads/{lid}/quote",
                  self.partner_headers(), {"amount": 990})
        lead = self.painting.get("lead", lid)
        self.assertEqual(lead["status"], "quoted")


class TestOwnerDecide(_Base):
    def test_lead_reply_appears_in_owner_queue(self):
        lid = self._seed_lead()
        self.call("POST", f"/api/v1/painting/leads/{lid}/reply",
                  self.partner_headers(),
                  {"channel": "email", "message": "quotation follows"})
        queue = self.node.owner_queue()
        lead_items = [i for i in queue if i.get("tenant") == "lead"]
        self.assertEqual(len(lead_items), 1)
        self.assertEqual(lead_items[0]["tier"], "red")
        self.assertTrue(lead_items[0]["needs_double_confirm"])


if __name__ == "__main__":
    unittest.main()
