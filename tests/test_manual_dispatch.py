"""Manual dispatch state machine (operations launch O1).

Pins the outbox transitions for manual delivery:
  pending → approved_manual → manual_completed
  pending/approved_manual → rejected
approval NEVER claims (in_flight is for a real sender, which does not
exist yet). Completion is idempotent. Migration adds the new columns.
"""

from __future__ import annotations

import os
import unittest

from ofn.adapters.manual_dispatch import CompletionReceipt, ManualPacket
from ofn.adapters.outbox import (
    APPROVED_MANUAL, COMPLETED, IN_FLIGHT, PENDING, REJECTED, SENT, Outbox,
)
from ofn.kernel.domain import RiskTier, TenantId
from ofn.kernel.tenancy import TenantScope

from tests.tmpdir import temp_dir

A = TenantScope(TenantId("alpha"))
T0 = "2026-08-10T10:00:00Z"
T1 = "2026-08-10T11:00:00Z"


def _outbox(case) -> Outbox:
    d = temp_dir(case)
    ob = Outbox(os.path.join(d, "o.sqlite"))
    case.addCleanup(ob.close)
    return ob


class TestManualStateMachine(unittest.TestCase):
    def setUp(self):
        self.ob = _outbox(self)

    def test_approve_manual_moves_pending_to_approved_manual(self):
        self.ob.enqueue(A, "k1", "email", {"text": "hi"}, RiskTier.YELLOW, T0)
        ok = self.ob.approve_manual(A, "k1", T1, approved_by="owner")
        self.assertTrue(ok)
        item = self.ob.get(A, "k1")
        self.assertEqual(item.status, APPROVED_MANUAL)
        self.assertEqual(item.approved_at, T1)
        self.assertEqual(item.delivery_mode, "manual")

    def test_approval_never_claims(self):
        """The bug being fixed: approval must NOT move to in_flight."""
        self.ob.enqueue(A, "k1", "email", {"text": "hi"}, RiskTier.YELLOW, T0)
        self.ob.approve_manual(A, "k1", T1)
        item = self.ob.get(A, "k1")
        self.assertNotEqual(item.status, IN_FLIGHT)
        self.assertEqual(item.status, APPROVED_MANUAL)
        self.assertEqual(item.attempts, 0)   # no claim → no attempt bump

    def test_approve_on_non_pending_fails(self):
        self.ob.enqueue(A, "k1", "email", {}, RiskTier.YELLOW, T0)
        self.ob.claim(A, "k1", T1)
        ok = self.ob.approve_manual(A, "k1", T1)
        self.assertFalse(ok)

    def test_reject_from_pending(self):
        self.ob.enqueue(A, "k1", "email", {}, RiskTier.YELLOW, T0)
        ok = self.ob.reject(A, "k1", T1, note="no")
        self.assertTrue(ok)
        self.assertEqual(self.ob.get(A, "k1").status, REJECTED)

    def test_reject_from_approved_manual(self):
        self.ob.enqueue(A, "k1", "email", {}, RiskTier.YELLOW, T0)
        self.ob.approve_manual(A, "k1", T1)
        ok = self.ob.reject(A, "k1", T1, note="changed mind")
        self.assertTrue(ok)
        self.assertEqual(self.ob.get(A, "k1").status, REJECTED)

    def test_reject_from_sent_is_fail_closed(self):
        """Terminal states are immutable."""
        self.ob.enqueue(A, "k1", "email", {}, RiskTier.YELLOW, T0)
        self.ob.claim(A, "k1", T1)
        self.ob.mark_sent(A, "k1", T1)
        ok = self.ob.reject(A, "k1", T1)
        self.assertFalse(ok)
        self.assertEqual(self.ob.get(A, "k1").status, SENT)

    def test_complete_manual_from_approved(self):
        self.ob.enqueue(A, "k1", "email", {"text": "hi"}, RiskTier.YELLOW, T0)
        self.ob.approve_manual(A, "k1", T1)
        ok = self.ob.complete_manual(
            A, "k1", T1, completed_by="ari", channel="email",
            packet_sha256="a" * 64)
        self.assertTrue(ok)
        item = self.ob.get(A, "k1")
        self.assertEqual(item.status, COMPLETED)
        self.assertEqual(item.completed_by, "ari")
        self.assertEqual(item.packet_sha256, "a" * 64)

    def test_complete_is_idempotent(self):
        self.ob.enqueue(A, "k1", "email", {}, RiskTier.YELLOW, T0)
        self.ob.approve_manual(A, "k1", T1)
        self.ob.complete_manual(A, "k1", T1, completed_by="ari")
        # Second completion: no-op, no duplicate effect.
        ok = self.ob.complete_manual(A, "k1", T1, completed_by="ari")
        self.assertFalse(ok)
        self.assertEqual(self.ob.get(A, "k1").status, COMPLETED)

    def test_complete_without_approval_fails(self):
        self.ob.enqueue(A, "k1", "email", {}, RiskTier.YELLOW, T0)
        ok = self.ob.complete_manual(A, "k1", T1)
        self.assertFalse(ok)
        self.assertEqual(self.ob.get(A, "k1").status, PENDING)

    def test_approved_manual_query(self):
        self.ob.enqueue(A, "k1", "email", {}, RiskTier.YELLOW, T0)
        self.ob.enqueue(A, "k2", "sms", {}, RiskTier.RED, T0)
        self.ob.approve_manual(A, "k1", T1)
        approved = self.ob.approved_manual(A)
        self.assertEqual([i.idem_key for i in approved], ["alpha:k1"])


class TestManualPacket(unittest.TestCase):
    def test_packet_hash_is_deterministic(self):
        p1 = ManualPacket("k1", "alpha", "email", text="hi", target="x@y.z")
        p2 = ManualPacket("k1", "alpha", "email", text="hi", target="x@y.z")
        self.assertEqual(p1.sha256(), p2.sha256())
        self.assertEqual(len(p1.sha256()), 64)

    def test_packet_hash_changes_with_content(self):
        p1 = ManualPacket("k1", "alpha", "email", text="hi")
        p2 = ManualPacket("k1", "alpha", "email", text="bye")
        self.assertNotEqual(p1.sha256(), p2.sha256())

    def test_receipt_shape(self):
        r = CompletionReceipt("k1", "alpha", T1, "ari", "email",
                              packet_sha256="a" * 64)
        self.assertEqual(r.idem_key, "k1")
        self.assertEqual(r.external_ref_digest, "")


class TestMigrationAddsColumns(unittest.TestCase):
    def test_old_schema_file_gets_new_columns(self):
        d = temp_dir(self)
        path = os.path.join(d, "o.sqlite")
        # Build a file with the OLD schema, then open with the new class.
        import sqlite3
        conn = sqlite3.connect(path)
        conn.execute(
            "CREATE TABLE outbox (idem_key TEXT PRIMARY KEY, tenant TEXT,"
            " kind TEXT, payload TEXT, tier TEXT, status TEXT,"
            " attempts INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT,"
            " note TEXT DEFAULT '')")
        conn.commit()
        conn.close()
        ob = Outbox(path)
        self.addCleanup(ob.close)
        cols = {r[1] for r in ob._conn.execute("PRAGMA table_info(outbox)")}
        for col in ("delivery_mode", "approved_at", "completed_at",
                    "packet_sha256", "external_ref_digest"):
            self.assertIn(col, cols)


if __name__ == "__main__":
    unittest.main()


class TestOwnerApproveManualHttp(unittest.TestCase):
    """O2 end-to-end: approve → approved_manual, packet, complete via HTTP."""

    def setUp(self):
        self.dir = temp_dir(self)
        from ofn.adapters.facts import FactStore
        from ofn.adapters.http_api import ApiApp, HostMap
        from ofn.adapters.lead_store import LeadStore
        from ofn.adapters.ledger import Ledger
        from ofn.kernel.auth import issue_session
        from ofn.kernel.domain import PackSpec, TenantId
        from ofn.kernel.quota import NodeQuota
        from ofn.kernel.tenancy import TenantRegistry
        from ofn.node import Node

        registry = TenantRegistry({
            "lead": PackSpec(tenant=TenantId("lead"),
                             capacity_units_per_week=6, quota_share=1.0),
        })
        self.node = Node(
            registry=registry,
            quota=NodeQuota(estimated_capacity_tokens=1_000_000,
                            utilisation=1.0, shares={"lead": 1.0}),
            ledger=Ledger(os.path.join(self.dir, "ledger.sqlite")),
            facts=FactStore(os.path.join(self.dir, "facts.sqlite")),
            outbox=Outbox(os.path.join(self.dir, "outbox.sqlite")),
            painting=LeadStore(os.path.join(self.dir, "painting.sqlite")),
            now_epoch_s=lambda: 1_785_000_000,
            now_iso=lambda: "2026-08-10T12:00:00Z",
        )
        self.addCleanup(self.node.close)
        self.app = ApiApp(
            registry,
            HostMap(tenants={"l.test": "lead"}, owner_host="panel.test"),
            bot_tokens={"__owner__": "t", "lead": "h"},
            session_secret="sec",
            owner_user_ids=("1",),
            partner_user_ids={"lead": ("2",)},
            now=lambda: 1_785_000_000,
            owner_decide=self.node.owner_decide,
            owner_outbox_packet=self.node.owner_outbox_packet,
            owner_outbox_complete=self.node.owner_outbox_complete,
            owner_approved_manual=self.node.owner_approved_manual,
        )
        self.session = issue_session("owner", "1", "sec",
                                     now_epoch_s=1_785_000_000)

    def _owner(self, method, path, body=None):
        import json as _j
        return self.app.handle(
            method, path,
            {"host": "panel.test", "authorization": "Bearer " + self.session},
            _j.dumps(body or {}).encode() if body is not None else b"")

    def test_full_manual_cycle(self):
        # Enqueue a lead reply (RED) via the node path
        lead = self.node.create_painting_lead(
            {"customer_name": "تست", "phone": "123", "message": "hi",
             "source": "test", "source_ref": "s1"}, actor="test")
        lid = lead["lead"]["lead_id"]
        self.node.send_lead_reply(
            lid, {"channel": "sms", "message": "سلام"}, actor="test")
        # Find the queued item id
        scope = self.node.registry.scope("lead")
        item = self.node.outbox.pending(scope)[0]
        key = item.idem_key.split(":", 1)[1]

        # Approve (RED needs confirmed_twice)
        resp = self._owner("POST", "/api/v1/decide",
                           {"id": f"lead:{key}", "approve": True,
                            "confirmed_twice": True})
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.body.get("status"), "approved_manual")
        # NOT in_flight — the bug is fixed
        item = self.node.outbox.get(scope, key)
        self.assertEqual(item.status, APPROVED_MANUAL)
        self.assertNotEqual(item.status, IN_FLIGHT)

        # Packet endpoint
        resp = self._owner("GET", f"/api/v1/owner/outbox/{key}/packet")
        self.assertEqual(resp.status, 200)
        packet = resp.body.get("packet", {})
        self.assertEqual(packet.get("text"), "سلام")
        self.assertEqual(len(packet.get("sha256", "")), 64)

        # Approved-manual queue shows it
        resp = self._owner("GET", "/api/v1/owner/approved-manual")
        self.assertEqual(len(resp.body.get("items", [])), 1)

        # Complete
        resp = self._owner(
            "POST", f"/api/v1/owner/outbox/{key}/complete",
            {"channel": "sms", "packet_sha256": packet["sha256"],
             "confirmed_twice": True, "completed_by": "ari"})
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.body.get("status"), "manual_completed")
        item = self.node.outbox.get(scope, key)
        self.assertEqual(item.status, COMPLETED)
        self.assertEqual(item.packet_sha256, packet["sha256"])

        # Queue is now empty
        resp = self._owner("GET", "/api/v1/owner/approved-manual")
        self.assertEqual(len(resp.body.get("items", [])), 0)

    def test_complete_without_second_confirm_red_is_refused(self):
        lead = self.node.create_painting_lead(
            {"customer_name": "تست", "phone": "123", "message": "hi",
             "source": "test", "source_ref": "s2"}, actor="test")
        self.node.send_lead_reply(
            lead["lead"]["lead_id"], {"channel": "sms", "message": "x"},
            actor="test")
        scope = self.node.registry.scope("lead")
        key = self.node.outbox.pending(scope)[0].idem_key.split(":", 1)[1]
        self._owner("POST", "/api/v1/decide",
                    {"id": f"lead:{key}", "approve": True,
                     "confirmed_twice": True})
        resp = self._owner("POST", f"/api/v1/owner/outbox/{key}/complete",
                           {"channel": "sms", "confirmed_twice": False})
        self.assertEqual(resp.status, 400)
        self.assertIn("second confirmation", resp.body.get("error", ""))
