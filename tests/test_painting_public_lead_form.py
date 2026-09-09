"""Public/local painting lead form — store only (Prompt B2 / A/A2).

Pins the gap closer: a stranger can POST an enquiry on the lead host and a
row appears in the local painting store. Happy path must not enqueue
outbound, must not open a new listener, and must keep baseline_action at 0.
"""

from __future__ import annotations

import ast
import inspect
import json
import os
import threading
import time
import unittest
import urllib.parse
import urllib.request

from ofn import config
from ofn.adapters.facts import FactStore
from ofn.adapters.http_api import ApiApp, HostMap, serve
from ofn.adapters.ledger import Ledger
from ofn.adapters.lead_store import LeadStore
from ofn.adapters.outbox import Outbox
from ofn.adapters.packloader import load_pack
from ofn.kernel.tenancy import TenantRegistry
from ofn.node import Node
from ofn.run import load_web
from tests.tmpdir import temp_dir

NOW_S = 1_800_000_100
NOW_ISO = "2026-09-08T06:00:00Z"
SECRET = "public-lead-form-test-secret"
WEB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "web")
FORM = os.path.join(WEB, "painting-lead-form.html")
HTTP_API = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "ofn", "adapters", "http_api.py")
NODE_PY = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "ofn", "node.py")

FORBIDDEN_PEOPLE = ("ملیحه", "عباس", "اسدی", "سبا", "سبولی", "Sume")
NETWORK_IMPORTS = ("smtplib", "requests", "httpx", "urllib.request")


def registry():
    return TenantRegistry({"lead": load_pack("packs/lead.yaml")})


class _Base(unittest.TestCase):
    def setUp(self):
        d = temp_dir(self)
        self.outbox = Outbox(os.path.join(d, "o.sqlite"))
        self.ledger = Ledger(os.path.join(d, "l.sqlite"))
        self.painting = LeadStore(os.path.join(d, "painting.sqlite"))
        self.node = Node(
            registry=registry(), quota=None,
            ledger=self.ledger, facts=FactStore(os.path.join(d, "f.sqlite")),
            outbox=self.outbox,
            now_epoch_s=lambda: NOW_S, now_iso=lambda: NOW_ISO,
            painting=self.painting)
        self.app = ApiApp(
            registry(), HostMap(tenants={"lead.test": "lead",
                                         "ziman.test": "ziman"},
                                owner_host="panel.test"),
            bot_tokens={"lead": "lead-t", "ziman": "ziman-t",
                        "__owner__": "owner-t"},
            session_secret=SECRET,
            now=lambda: NOW_S,
            capture_public_painting_lead=self.node.capture_public_painting_lead,
        )
        self.addCleanup(self.node.close)

    def post(self, body, *, host="lead.test", as_form=False):
        if as_form:
            payload = urllib.parse.urlencode(body).encode()
            headers = {"host": host,
                       "content-type": "application/x-www-form-urlencoded"}
        else:
            payload = json.dumps(body).encode()
            headers = {"host": host, "content-type": "application/json"}
        return self.app.handle(
            "POST", "/api/v1/public/painting/leads", headers, payload)


class TestPublicLeadStored(_Base):
    def test_submit_writes_row_in_local_store(self):
        before = self.painting.list_leads("lead")
        self.assertEqual(before, [])
        body = {
            "customer_name": "Jordan Lee",
            "phone": "0411000111",
            "email": "jordan.lee@example.test",
            "suburb": "Marrickville",
            "job_type": "interior rooms",
            "message": "two bedrooms and a hallway",
            "source": "evil-external",
            "status": "won",
        }
        resp = self.post(body)
        self.assertEqual(resp.status, 200, resp.body)
        self.assertTrue(resp.body["ok"])
        self.assertTrue(resp.body["stored"])
        self.assertEqual(resp.body["outbound"], 0)
        self.assertEqual(resp.body["baseline_action"], 0)
        self.assertEqual(resp.body["EXTERNAL_ACTIONS"], 0)
        self.assertEqual(resp.body["source"], "web-form")
        self.assertNotIn("phone", resp.body)
        self.assertNotIn("email", resp.body)
        rows = self.painting.list_leads("lead")
        self.assertEqual(len(rows), 1, rows)
        row = rows[0]
        self.assertEqual(row["customer_name"], "Jordan Lee")
        self.assertEqual(row["phone"], "0411000111")
        self.assertEqual(row["suburb"], "Marrickville")
        self.assertEqual(row["source"], "web-form")
        self.assertEqual(row["status"], "new")
        self.assertEqual(row["lead_id"], resp.body["lead_id"])
        counts = self.outbox.counts(self.node.registry.scope("lead"))
        self.assertEqual(sum(counts.values()), 0, counts)


class TestPublicLeadBoundaries(_Base):
    def test_form_urlencoded_is_stored(self):
        resp = self.post({
            "customer_name": "Sam Wright",
            "phone": "0411222333",
            "suburb": "Newtown",
        }, as_form=True)
        self.assertEqual(resp.status, 200, resp.body)
        rows = self.painting.list_leads("lead")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["customer_name"], "Sam Wright")

    def test_name_required(self):
        resp = self.post({"phone": "0411000000"})
        self.assertEqual(resp.status, 400)
        self.assertFalse(resp.body.get("ok"))
        self.assertEqual(self.painting.list_leads("lead"), [])

    def test_phone_or_email_required(self):
        resp = self.post({"customer_name": "No Contact"})
        self.assertEqual(resp.status, 400)
        self.assertEqual(self.painting.list_leads("lead"), [])

    def test_wrong_host_is_not_found(self):
        resp = self.post({"customer_name": "X", "phone": "1"}, host="ziman.test")
        self.assertEqual(resp.status, 404)
        self.assertEqual(self.painting.list_leads("lead"), [])

    def test_owner_host_is_not_found(self):
        resp = self.post({"customer_name": "X", "phone": "1"}, host="panel.test")
        self.assertEqual(resp.status, 404)

    def test_two_people_same_second_are_two_rows(self):
        a = self.post({"customer_name": "A One", "phone": "0400000001"})
        b = self.post({"customer_name": "B Two", "phone": "0400000002"})
        self.assertEqual(a.status, 200)
        self.assertEqual(b.status, 200)
        self.assertNotEqual(a.body["lead_id"], b.body["lead_id"])
        self.assertEqual(len(self.painting.list_leads("lead")), 2)

    def test_rate_limit_after_ten_ok(self):
        for i in range(10):
            r = self.post({"customer_name": f"N{i}", "phone": f"04000000{i:02d}"})
            self.assertEqual(r.status, 200, r.body)
        blocked = self.post({"customer_name": "Overflow", "phone": "0499999999"})
        self.assertEqual(blocked.status, 429)
        self.assertEqual(blocked.body.get("outbound"), 0)
        self.assertEqual(blocked.body.get("baseline_action"), 0)
        self.assertEqual(blocked.body.get("EXTERNAL_ACTIONS"), 0)
        self.assertEqual(len(self.painting.list_leads("lead")), 10)


class TestFormAssetAndBind(unittest.TestCase):
    def test_form_file_is_store_only(self):
        with open(FORM, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn('charset="utf-8"', src)
        self.assertIn("/api/v1/public/painting/leads", src)
        self.assertNotIn("telegram.org", src)
        self.assertNotIn("telegram-web-app.js", src)
        for person in FORBIDDEN_PEOPLE:
            self.assertNotIn(person, src)
        for token in ("stripe", "paypal", "checkout"):
            self.assertNotIn(token, src.lower())

    def test_load_web_serves_enquire_on_lead_port_only(self):
        cfg = config.load()
        web = load_web(cfg)
        lead = web[cfg.ports["lead"]]
        self.assertIn("/enquire", lead)
        self.assertIn("/enquire.html", lead)
        with open(FORM, "rb") as fh:
            self.assertEqual(lead["/enquire"], fh.read())
        for name in ("ziman", "studio", "owner"):
            self.assertNotIn("/enquire", web[cfg.ports[name]])

    def test_serve_default_is_loopback(self):
        params = inspect.signature(serve).parameters
        self.assertEqual(params["host"].default, "127.0.0.1")

    def test_capture_method_has_no_network_imports(self):
        with open(NODE_PY, encoding="utf-8") as fh:
            raw = fh.read()
        tree = ast.parse(raw)
        node_class = next(n for n in ast.walk(tree)
                          if isinstance(n, ast.ClassDef) and n.name == "Node")
        fn = next(n for n in node_class.body
                  if isinstance(n, ast.FunctionDef)
                  and n.name == "capture_public_painting_lead")
        src = ast.get_source_segment(raw, fn)
        for name in NETWORK_IMPORTS:
            self.assertNotIn(name, src)

    def test_route_is_before_principal_and_store_only(self):
        with open(HTTP_API, encoding="utf-8") as fh:
            src = fh.read()
        pre = src.split("principal = self._principal")[0]
        self.assertIn('path == "/api/v1/public/painting/leads"', pre)
        self.assertIn("baseline_action", src)
        self.assertIn("EXTERNAL_ACTIONS", src)
        self.assertNotIn("smtplib", src)


class TestEnquireServedOverLoopback(unittest.TestCase):
    PORT = 8897

    @classmethod
    def setUpClass(cls):
        with open(FORM, "rb") as fh:
            html = fh.read()
        app = ApiApp(
            TenantRegistry({"lead": load_pack("packs/lead.yaml")}),
            HostMap(tenants={"lead.test": "lead"}),
            bot_tokens={"lead": "t"}, session_secret="s",
            now=lambda: NOW_S)
        cls.server = serve(app, cls.PORT, static={
            "/enquire": html, "/enquire.html": html,
        })
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        time.sleep(0.15)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_enquire_is_the_form(self):
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.PORT}/enquire",
            headers={"Host": "lead.test"})
        with urllib.request.urlopen(req, timeout=5) as r:
            body = r.read()
        self.assertIn(b"Painting enquiry", body)
        self.assertIn(b"/api/v1/public/painting/leads", body)
        self.assertNotIn("telegram.org".encode(), body)
