"""Revenue-stage wiring: thresholds, lead follow-up/booked, gate expiry."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

from ofn.adapters.facts import FactStore
from ofn.adapters.http_api import ApiApp, HostMap
from ofn.adapters.lead_store import LeadStore
from ofn.adapters.ledger import Ledger
from ofn.adapters.outbox import Outbox
from ofn.adapters import pilot_thresholds as pt
from ofn.kernel.auth import issue_session
from ofn.kernel.domain import PackSpec, TenantId
from ofn.kernel.quota import NodeQuota
from ofn.kernel.tenancy import TenantRegistry
from ofn.node import Node
from ofn import config as config_module

from tests.tmpdir import temp_dir

NOW = 1_785_000_000
NOW_ISO = "2026-08-11T02:00:00Z"
SECRET = "revenue-stage-secret"


class TestPilotThresholds(unittest.TestCase):
    def test_defaults_match_pilot_doc(self):
        d = temp_dir(self)
        cfg = pt.load(d)
        self.assertEqual(cfg.source, "defaults")
        self.assertEqual(cfg.thresholds["min_production_listings"], 3)
        self.assertEqual(cfg.payment_methods["lead"], "unset")

    def test_save_payment_methods(self):
        d = temp_dir(self)
        out = pt.save(d, {"payment_methods": {
            "lead": "payid", "ziman": "cash", "studio": "unset"}})
        self.assertEqual(out.payment_methods["lead"], "payid")
        self.assertEqual(out.source, "owner")
        again = pt.load(d)
        self.assertEqual(again.payment_methods["ziman"], "cash")
        if os.name != "nt":   # 0600 bits are POSIX-only; the roundtrip above
            mode = os.stat(os.path.join(d, "pilot_config.json")).st_mode & 0o777
            self.assertEqual(mode, 0o600)


class TestLeadBookedAndFollowUp(unittest.TestCase):
    def setUp(self):
        self.dir = temp_dir(self)
        self.store = LeadStore(os.path.join(self.dir, "lead.sqlite"))
        self.addCleanup(self.store.close)
        self.store.create_lead("lead", {
            "customer_name": "Test", "phone": "0411111111",
            "source": "test", "source_ref": "r1",
        }, now_iso=NOW_ISO)
        self.lid = self.store.list_leads("lead")[0]["lead_id"]

    def test_booked_marks_won(self):
        out = self.store.record_booked_revenue(
            "lead", self.lid, amount_cents=45000,
            booked_at=NOW_ISO, payment_ref_digest="abcd1234")
        self.assertTrue(out["ok"])
        lead = self.store.get("lead", self.lid)
        self.assertEqual(lead["status"], "won")
        self.assertEqual(lead["booked_amount_cents"], 45000)

    def test_node_api_follow_up_and_booked(self):
        registry = TenantRegistry({
            "lead": PackSpec(tenant=TenantId("lead"),
                             capacity_units_per_week=6, quota_share=1.0),
        })
        node = Node(
            registry=registry,
            quota=NodeQuota(estimated_capacity_tokens=1_000_000,
                            utilisation=1.0, shares={"lead": 1.0}),
            ledger=Ledger(os.path.join(self.dir, "l.sqlite")),
            facts=FactStore(os.path.join(self.dir, "f.sqlite")),
            outbox=Outbox(os.path.join(self.dir, "o.sqlite")),
            painting=self.store,
            now_epoch_s=lambda: NOW,
            now_iso=lambda: NOW_ISO,
            state_dir=self.dir,
        )
        self.addCleanup(node.close)
        app = ApiApp(
            registry,
            HostMap(tenants={"l.test": "lead"}, owner_host="panel.test"),
            bot_tokens={"__owner__": "t", "lead": "h"},
            session_secret=SECRET,
            owner_user_ids=("1",),
            partner_user_ids={"lead": ("2",)},
            now=lambda: NOW,
            set_lead_follow_up=node.set_lead_follow_up,
            touch_lead_contact=node.touch_lead_contact,
            lead_duplicate_candidates=node.lead_duplicate_candidates,
            record_lead_booked=node.record_lead_booked,
            owner_pilot_config=node.owner_pilot_config,
            set_owner_pilot_config=node.set_owner_pilot_config,
            owner_workboard=node.owner_workboard,
        )
        partner = issue_session("lead", "2", SECRET, now_epoch_s=NOW)
        owner = issue_session("owner", "1", SECRET, now_epoch_s=NOW)

        def partner_post(path, body):
            return app.handle(
                "POST", path,
                {"host": "l.test", "authorization": "Bearer " + partner},
                json.dumps(body).encode())

        r = partner_post(
            f"/api/v1/painting/leads/{self.lid}/follow-up",
            {"due_at": "2026-08-12T10:00:00Z", "action": "تماس"})
        self.assertEqual(r.status, 200, r.body)
        self.assertTrue(r.body["ok"])

        r = partner_post(
            f"/api/v1/painting/leads/{self.lid}/touch", {})
        self.assertTrue(r.body["ok"])

        r = partner_post(
            f"/api/v1/painting/leads/{self.lid}/booked",
            {"amount_aud": 450, "payment_ref_digest": "paydigest1"})
        self.assertTrue(r.body["ok"], r.body)

        wb = app.handle(
            "GET", "/api/v1/owner/workboard",
            {"host": "panel.test", "authorization": "Bearer " + owner}, b"")
        self.assertEqual(wb.status, 200)
        self.assertGreaterEqual(wb.body["lead"]["booked_revenue_cents"], 45000)

        cfg = app.handle(
            "POST", "/api/v1/owner/pilot/config",
            {"host": "panel.test", "authorization": "Bearer " + owner},
            json.dumps({"payment_methods": {"lead": "payid",
                                            "ziman": "cash",
                                            "studio": "payid"}}).encode())
        self.assertTrue(cfg.body["ok"])
        self.assertTrue(cfg.body["ready_for_measured_pilot"])


class TestGateExpiry(unittest.TestCase):
    def test_open_before_deadline(self):
        env = {
            "OFN_EXTRA_CLOSED_GATES": "",
            "OFN_KEEP_GATES_OPEN": "0",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            with mock.patch("ofn.config.datetime") as dt:
                dt.strptime = datetime.strptime
                dt.now.return_value = datetime(
                    2026, 8, 11, tzinfo=timezone.utc)
                dt.side_effect = lambda *a, **k: datetime(*a, **k)
                # datetime.strptime is used from the real class via patch object
                # Re-load carefully: patch only now().
        with mock.patch.dict(os.environ, env, clear=False):
            with mock.patch("ofn.config.datetime") as fake_dt:
                real = datetime
                fake_dt.strptime = real.strptime
                fake_dt.timezone = timezone
                fake_dt.now.return_value = real(
                    2026, 8, 11, 12, 0, 0, tzinfo=timezone.utc)
                cfg = config_module.load()
                self.assertNotIn("secret_rotation", cfg.base_closed_gates)
                self.assertNotIn("partner_precondition", cfg.base_closed_gates)

    def test_closed_after_deadline(self):
        env = {
            "OFN_EXTRA_CLOSED_GATES": "",
            "OFN_KEEP_GATES_OPEN": "0",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            with mock.patch("ofn.config.datetime") as fake_dt:
                real = datetime
                fake_dt.strptime = real.strptime
                fake_dt.timezone = timezone
                fake_dt.now.return_value = real(
                    2026, 8, 17, 0, 0, 1, tzinfo=timezone.utc)
                cfg = config_module.load()
                self.assertIn("secret_rotation", cfg.base_closed_gates)
                self.assertIn("partner_precondition", cfg.base_closed_gates)

    def test_keep_open_flag(self):
        env = {
            "OFN_EXTRA_CLOSED_GATES": "",
            "OFN_KEEP_GATES_OPEN": "1",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            with mock.patch("ofn.config.datetime") as fake_dt:
                real = datetime
                fake_dt.strptime = real.strptime
                fake_dt.timezone = timezone
                fake_dt.now.return_value = real(
                    2026, 8, 20, tzinfo=timezone.utc)
                cfg = config_module.load()
                self.assertNotIn("secret_rotation", cfg.base_closed_gates)


class TestPanelRevenueWords(unittest.TestCase):
    def test_panel_calls_pilot_and_consent(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        panel = open(os.path.join(root, "web", "panel.html"),
                     encoding="utf-8").read()
        self.assertIn("/api/v1/owner/pilot/config", panel)
        self.assertIn("/api/v1/owner/consent/subjects", panel)
        self.assertIn("/api/v1/owner/consent/gaps", panel)
        self.assertIn("publish-telegram", panel)
        lead = open(os.path.join(root, "web", "lead.html"),
                    encoding="utf-8").read()
        self.assertIn("/follow-up", lead)
        self.assertIn("/booked", lead)
        self.assertIn("/duplicates/", lead)


if __name__ == "__main__":
    unittest.main()
