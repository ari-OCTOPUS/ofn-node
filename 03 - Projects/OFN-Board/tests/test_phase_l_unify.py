"""Phase L — UNIFY: hypno edge model inside OFN.

The pure edge math (ofn/kernel/edge.py) serves three endpoints through the
partner route: decision (12 scores), daily (B/C/X → verdict stored as a
fact), and history. This is the first step of bringing hypno inside OFN —
the endpoints work while the standalone hypno service still runs; switching
the service off is a separate, owner-approved step.
"""

from __future__ import annotations

import json
import os
import unittest

from ofn.adapters.facts import FactStore
from ofn.adapters.http_api import ApiApp, HostMap
from ofn.adapters.ledger import Ledger
from ofn.adapters.outbox import Outbox
from ofn.kernel.auth import issue_session
from ofn.kernel.domain import PackSpec, TenantId
from ofn.kernel.quota import NodeQuota
from ofn.kernel.tenancy import TenantRegistry
from ofn.node import Node

from tests.tmpdir import temp_dir

NOW = 1_785_000_000
NOW_ISO = "2026-08-10T12:00:00"
SECRET = "unify-test-secret"


def _packs():
    return {
        "hypno": PackSpec(tenant=TenantId("hypno"),
                          capacity_units_per_week=10, quota_share=1.0),
    }


class HypnoEdgeBase(unittest.TestCase):
    def setUp(self):
        self.dir = temp_dir(self)
        registry = TenantRegistry(_packs())
        ledger = Ledger(os.path.join(self.dir, "ledger.sqlite"))
        facts = FactStore(os.path.join(self.dir, "facts.sqlite"))
        outbox = Outbox(os.path.join(self.dir, "outbox.sqlite"))
        self.node = Node(
            registry=registry,
            quota=NodeQuota(estimated_capacity_tokens=1_000_000,
                            utilisation=1.0, shares={"hypno": 1.0}),
            ledger=ledger, facts=facts, outbox=outbox,
            now_epoch_s=lambda: NOW,
            now_iso=lambda: NOW_ISO,
        )
        self.addCleanup(self.node.close)
        self.app = ApiApp(
            registry,
            HostMap(tenants={"h.test": "hypno"}, owner_host="panel.test"),
            bot_tokens={"__owner__": "t", "hypno": "h"},
            session_secret=SECRET,
            owner_user_ids=("1",),
            partner_user_ids={"hypno": ("2",)},
            now=lambda: NOW,
            hypno_edge_decision=self.node.hypno_edge_decision,
            hypno_edge_daily=self.node.hypno_edge_daily,
            hypno_edge_history=self.node.hypno_edge_history,
        )
        self.session = issue_session("hypno", "2", SECRET,
                                     now_epoch_s=NOW)

    def _post(self, path, data):
        return self.app.handle(
            "POST", path,
            {"host": "h.test", "authorization": "Bearer " + self.session},
            json.dumps(data).encode())

    def _get(self, path):
        return self.app.handle(
            "GET", path,
            {"host": "h.test", "authorization": "Bearer " + self.session},
            b"")


class TestEdgeDecisionEndpoint(HypnoEdgeBase):
    def test_twelve_scores_return_decomposition(self):
        body = {k: 5 for k in
                ("V", "P", "K", "D", "H", "E", "F", "M", "U", "C")}
        body["sleep_debt"] = 5
        body["stress"] = 5
        resp = self._post("/api/v1/hypno/edge/decision", body)
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.body.get("ok"))
        # decomposition keys present
        self.assertIn("dominant", resp.body)

    def test_missing_scores_default(self):
        resp = self._post("/api/v1/hypno/edge/decision", {})
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.body.get("ok"))

    def test_requires_auth(self):
        resp = self.app.handle(
            "POST", "/api/v1/hypno/edge/decision",
            {"host": "h.test"}, b"{}")
        self.assertEqual(resp.status, 401)


class TestEdgeDailyEndpoint(HypnoEdgeBase):
    def test_daily_verdict_stored_as_fact(self):
        resp = self._post("/api/v1/hypno/edge/daily",
                          {"B": 8, "C": 2, "X": 3})
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.body.get("ok"))
        self.assertIn("verdict", resp.body)
        # Stored as a day-keyed fact for hypno tenant
        scope = self.node.registry.scope("hypno")
        daily = [f for f in self.node.facts.all_active(scope)
                 if f.predicate.startswith("edge_daily:")]
        self.assertEqual(len(daily), 1)

    def test_three_red_days_flag(self):
        # Three distinct days, all red → flag on the fourth.
        days = ["2026-08-08T12:00:00", "2026-08-09T12:00:00",
                "2026-08-10T12:00:00"]
        for d in days:
            self.node.now_iso = lambda d=d: d
            self._post("/api/v1/hypno/edge/daily", {"B": 1, "C": 9, "X": 9})
        self.node.now_iso = lambda: "2026-08-11T12:00:00"
        resp = self._post("/api/v1/hypno/edge/daily", {"B": 1, "C": 9, "X": 9})
        self.assertTrue(resp.body.get("three_red_days"))


class TestEdgeHistoryEndpoint(HypnoEdgeBase):
    def test_history_after_daily(self):
        self._post("/api/v1/hypno/edge/daily", {"B": 8, "C": 2, "X": 3})
        resp = self._get("/api/v1/hypno/edge/history")
        self.assertEqual(resp.status, 200)
        self.assertEqual(len(resp.body.get("entries", [])), 1)
        self.assertIn("day", resp.body["entries"][0])


if __name__ == "__main__":
    unittest.main()
