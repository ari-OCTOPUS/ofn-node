"""Kill switch: the panic button that must always work.

The kill switch is the one control the owner must be able to reach under
duress. These tests pin the contract from three angles, because a panic
button that works at one layer and silently no-ops at another is worse than
no button at all:

  - kernel: `admit()` refuses everything at gate:kill-switch when killed
  - node:   engage/release flip state and write the audit trail
  - HTTP:   owner-only, release needs two-step, partner/anonymous refused

The fail-safe direction matters and is asserted: a restart disengages
(killed defaults False), because an owner who reboots to fix a stuck state
must not find the organism still frozen. The audit row persists.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from ofn.adapters.facts import FactStore
from ofn.adapters.http_api import ApiApp, HostMap
from ofn.adapters.ledger import Ledger
from ofn.adapters.marketing_store import MarketingStore
from ofn.adapters.outbox import Outbox
from ofn.kernel.auth import issue_session
from ofn.kernel.domain import Action, PackSpec, RiskTier, TenantId
from ofn.kernel.gates import admit
from ofn.kernel.quota import NodeQuota
from ofn.kernel.tenancy import TenantRegistry
from ofn.node import Node


NOW = 1_800_000_000
NOW_ISO = "2027-01-15T08:00:00Z"
SECRET = "kill-switch-test-secret"
OWNER_ID = "5001"
PARTNER_ID = "7001"
OWNER_HOST = "panel.test"


def _packs() -> dict[str, PackSpec]:
    return {
        name: PackSpec(
            tenant=TenantId(name),
            capacity_units_per_week=capacity,
            quota_share=share,
        )
        for name, capacity, share in (
            ("lead", 8, 0.30),
            ("studio", 5, 0.30),
            ("ziman", 6, 0.40),
        )
    }


def _quota() -> NodeQuota:
    return NodeQuota(
        estimated_capacity_tokens=100_000,
        utilisation=0.4,
        shares={"lead": 0.30, "studio": 0.30, "ziman": 0.40},
    )


def _green_action(tenant: str = "ziman") -> Action:
    """A trivially-green action: it would be allowed if not killed."""
    return Action(
        tenant=TenantId(tenant), name="classify_inbound",
        estimated_tokens=0, touches_money=False, leaves_node=False,
    )


# ── kernel ────────────────────────────────────────────────────────────────

class TestKillSwitchAtTheGate(unittest.TestCase):
    """The choke point honours the kill switch before anything else."""

    def test_killed_refuses_even_a_green_action(self):
        d = admit(_green_action(), _packs()["ziman"], _quota(),
                  now_epoch_s=NOW, killed=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.rule, "gate:kill-switch")

    def test_not_killed_lets_the_green_action_through(self):
        d = admit(_green_action(), _packs()["ziman"], _quota(),
                  now_epoch_s=NOW, killed=False)
        self.assertTrue(d.allowed)

    def test_kill_beats_quota(self):
        """A killed node refuses even when budget would allow it."""
        d = admit(_green_action(), _packs()["ziman"], _quota(),
                  now_epoch_s=NOW, killed=True)
        self.assertFalse(d.allowed)
        # The reason must be the kill switch, not a quota message.
        self.assertIn("kill", d.reason)


# ── node ──────────────────────────────────────────────────────────────────

class KillSwitchNodeBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        registry = TenantRegistry(_packs())
        self.ledger = Ledger(os.path.join(self.tmp.name, "ledger.sqlite"))
        self.facts = FactStore(os.path.join(self.tmp.name, "facts.sqlite"))
        self.outbox = Outbox(os.path.join(self.tmp.name, "outbox.sqlite"))
        self.marketing = MarketingStore(
            os.path.join(self.tmp.name, "marketing.sqlite"))
        self.addCleanup(self.ledger.close)
        self.addCleanup(self.facts.close)
        self.addCleanup(self.outbox.close)
        self.addCleanup(self.marketing.close)
        self.node = Node(
            registry=registry,
            quota=_quota(),
            ledger=self.ledger,
            facts=self.facts,
            outbox=self.outbox,
            now_epoch_s=lambda: NOW,
            now_iso=lambda: NOW_ISO,
            marketing=self.marketing,
        )


class TestEngageRelease(KillSwitchNodeBase):
    def test_engage_flips_killed_true(self):
        self.assertFalse(self.node.killed)
        out = self.node.engage_kill(
            reason="test panic", owner_id=OWNER_ID, session_id="abc")
        self.assertTrue(out["ok"])
        self.assertEqual(out["status"], "engaged")
        self.assertTrue(self.node.killed)

    def test_release_requires_two_step(self):
        self.node.engage_kill(reason="x", owner_id=OWNER_ID,
                               session_id="abc")
        out = self.node.release_kill(
            reason="resume", owner_id=OWNER_ID, session_id="abc",
            confirmed_twice=False)
        self.assertFalse(out["ok"])
        self.assertIn("two-step", out["error"])
        # Still killed — the refusal did not flip state.
        self.assertTrue(self.node.killed)

    def test_release_with_confirmation_flips_killed_false(self):
        self.node.engage_kill(reason="x", owner_id=OWNER_ID,
                               session_id="abc")
        out = self.node.release_kill(
            reason="resume", owner_id=OWNER_ID, session_id="abc",
            confirmed_twice=True)
        self.assertTrue(out["ok"])
        self.assertEqual(out["status"], "released")
        self.assertFalse(self.node.killed)

    def test_engage_is_idempotent(self):
        first = self.node.engage_kill(reason="x", owner_id=OWNER_ID,
                                      session_id="abc")
        second = self.node.engage_kill(reason="x", owner_id=OWNER_ID,
                                       session_id="abc")
        self.assertTrue(first["ok"])
        self.assertTrue(second["ok"])
        self.assertEqual(second["status"], "already-engaged")

    def test_release_when_not_killed_is_idempotent(self):
        out = self.node.release_kill(
            reason="resume", owner_id=OWNER_ID, session_id="abc",
            confirmed_twice=True)
        self.assertTrue(out["ok"])
        self.assertEqual(out["status"], "already-released")

    def test_owner_status_reports_killed(self):
        """§8-ب: the claim `killed` must have an independent read. The
        panel trusts this field, so it is verified against node.killed."""
        self.assertFalse(self.node.owner_status()["get"] if False else
                         self.node.owner_status()["killed"])
        self.node.engage_kill(reason="x", owner_id=OWNER_ID,
                              session_id="abc")
        self.assertTrue(self.node.owner_status()["killed"])


class TestKillSwitchAuditTrail(KillSwitchNodeBase):
    def test_engage_writes_release_event(self):
        self.node.engage_kill(reason="incident", owner_id=OWNER_ID,
                              session_id="sess-1")
        first_tenant = next(iter(self.node.registry)).value
        events = self.marketing.release_events(first_tenant)
        self.assertTrue(any(e["event_type"] == "kill_switch_on"
                            for e in events))
        self.assertTrue(any(e["reason"] == "incident"
                            for e in events))

    def test_release_writes_release_event(self):
        self.node.engage_kill(reason="x", owner_id=OWNER_ID,
                              session_id="sess-1")
        self.node.release_kill(reason="all clear", owner_id=OWNER_ID,
                               session_id="sess-1", confirmed_twice=True)
        first_tenant = next(iter(self.node.registry)).value
        events = self.marketing.release_events(first_tenant)
        self.assertTrue(any(e["event_type"] == "kill_switch_off"
                            for e in events))

    def test_kill_switch_logged_to_every_leg_ledger(self):
        """A node-wide halt affects every leg, so every leg's ledger must
        show it — a partner reviewing their own history sees the halt."""
        self.node.engage_kill(reason="x", owner_id=OWNER_ID,
                              session_id="sess-1")
        for tenant in self.node.registry:
            scope = self.node.registry.scope(tenant)
            events = self.ledger.read(scope, limit=5)
            kinds = [e.kind for e in events]
            self.assertIn("KILL_SWITCH", kinds,
                          f"tenant {tenant} ledger missing KILL_SWITCH")


class TestKillSwitchSurvivesMissingMarketing(unittest.TestCase):
    """If the marketing store is not wired, the kill still takes effect —
    the audit table is best-effort, the in-memory flag is the source."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        registry = TenantRegistry(_packs())
        self.ledger = Ledger(os.path.join(self.tmp.name, "ledger.sqlite"))
        self.facts = FactStore(os.path.join(self.tmp.name, "facts.sqlite"))
        self.outbox = Outbox(os.path.join(self.tmp.name, "outbox.sqlite"))
        self.addCleanup(self.ledger.close)
        self.addCleanup(self.facts.close)
        self.addCleanup(self.outbox.close)
        self.node = Node(
            registry=registry,
            quota=_quota(),
            ledger=self.ledger,
            facts=self.facts,
            outbox=self.outbox,
            now_epoch_s=lambda: NOW,
            now_iso=lambda: NOW_ISO,
            # marketing deliberately None
        )

    def test_engage_works_without_marketing_store(self):
        out = self.node.engage_kill(reason="x", owner_id=OWNER_ID,
                                    session_id="abc")
        self.assertTrue(out["ok"])
        self.assertTrue(self.node.killed)


# ── HTTP ──────────────────────────────────────────────────────────────────

class KillSwitchHttpBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        registry = TenantRegistry(_packs())
        self.ledger = Ledger(os.path.join(self.tmp.name, "ledger.sqlite"))
        self.facts = FactStore(os.path.join(self.tmp.name, "facts.sqlite"))
        self.outbox = Outbox(os.path.join(self.tmp.name, "outbox.sqlite"))
        self.marketing = MarketingStore(
            os.path.join(self.tmp.name, "marketing.sqlite"))
        self.addCleanup(self.ledger.close)
        self.addCleanup(self.facts.close)
        self.addCleanup(self.outbox.close)
        self.addCleanup(self.marketing.close)
        self.node = Node(
            registry=registry,
            quota=_quota(),
            ledger=self.ledger,
            facts=self.facts,
            outbox=self.outbox,
            now_epoch_s=lambda: NOW,
            now_iso=lambda: NOW_ISO,
            marketing=self.marketing,
        )
        self.app = ApiApp(
            registry,
            HostMap(
                tenants={
                    "lead.test": "lead",
                    "studio.test": "studio",
                    "ziman.test": "ziman",
                },
                owner_host=OWNER_HOST,
            ),
            bot_tokens={
                "lead": "lead-token",
                "studio": "studio-token",
                "ziman": "ziman-token",
                "__owner__": "owner-token",
            },
            session_secret=SECRET,
            owner_user_ids=(OWNER_ID,),
            partner_user_ids={"studio": (PARTNER_ID,)},
            now=lambda: NOW,
            engage_kill=self.node.engage_kill,
            release_kill=self.node.release_kill,
            owner_status=self.node.owner_status,
        )
        self.owner_session = issue_session(
            "owner", OWNER_ID, SECRET, now_epoch_s=NOW)
        self.partner_session = issue_session(
            "studio", PARTNER_ID, SECRET, now_epoch_s=NOW)

    def owner_post(self, path: str, body: dict):
        return self.app.handle(
            "POST", path,
            {"host": OWNER_HOST,
             "authorization": "Bearer " + self.owner_session},
            json.dumps(body).encode(),
        )

    def partner_post(self, path: str, body: dict):
        """Partner session against the *owner* host — a partner trying to
        reach an owner-only endpoint. The host is the owner's because that
        is the only host that routes to _owner_route."""
        return self.app.handle(
            "POST", path,
            {"host": OWNER_HOST,
             "authorization": "Bearer " + self.partner_session},
            json.dumps(body).encode(),
        )

    def anon_post(self, path: str, body: dict):
        return self.app.handle(
            "POST", path,
            {"host": OWNER_HOST},
            json.dumps(body).encode(),
        )


class TestKillSwitchHttpAuth(KillSwitchHttpBase):
    def test_engage_requires_owner_session(self):
        """Anonymous must not reach the panic button — that would let
        anyone halt the business."""
        r = self.anon_post("/api/v1/owner/kill", {"reason": "x"})
        self.assertEqual(r.status, 401)

    def test_engage_refuses_partner_session(self):
        """A partner session presented to the owner host is not an owner."""
        r = self.partner_post("/api/v1/owner/kill", {"reason": "x"})
        # partner token against owner host → not admitted
        self.assertEqual(r.status, 401)

    def test_release_requires_owner_session(self):
        r = self.anon_post("/api/v1/owner/kill/release",
                           {"reason": "x", "confirmed_twice": True})
        self.assertEqual(r.status, 401)


class TestKillSwitchHttpEngage(KillSwitchHttpBase):
    def test_owner_engage_returns_200_and_flips_state(self):
        r = self.owner_post("/api/v1/owner/kill", {"reason": "incident"})
        self.assertEqual(r.status, 200)
        self.assertTrue(r.body["ok"])
        self.assertEqual(r.body["status"], "engaged")
        self.assertTrue(self.node.killed)

    def test_engage_without_reason_body_still_works(self):
        """Reason is optional — in a real panic the owner may not type one."""
        r = self.owner_post("/api/v1/owner/kill", {})
        self.assertEqual(r.status, 200)
        self.assertTrue(r.body["ok"])

    def test_status_reflects_engage(self):
        """The panel polls /owner/status; after engage it must see killed."""
        self.owner_post("/api/v1/owner/kill", {"reason": "x"})
        r = self.app.handle(
            "GET", "/api/v1/owner/status",
            {"host": OWNER_HOST,
             "authorization": "Bearer " + self.owner_session},
            b"",
        )
        self.assertEqual(r.status, 200)
        self.assertTrue(r.body["killed"])


class TestKillSwitchHttpRelease(KillSwitchHttpBase):
    def test_release_without_confirmation_is_refused(self):
        self.owner_post("/api/v1/owner/kill", {"reason": "x"})
        r = self.owner_post("/api/v1/owner/kill/release",
                            {"reason": "resume", "confirmed_twice": False})
        self.assertEqual(r.status, 200)
        self.assertFalse(r.body["ok"])
        self.assertIn("two-step", r.body["error"])
        # Still killed.
        self.assertTrue(self.node.killed)

    def test_release_with_confirmation_works(self):
        self.owner_post("/api/v1/owner/kill", {"reason": "x"})
        r = self.owner_post("/api/v1/owner/kill/release",
                            {"reason": "all clear",
                             "confirmed_twice": True})
        self.assertEqual(r.status, 200)
        self.assertTrue(r.body["ok"])
        self.assertFalse(self.node.killed)

    def test_release_string_confirmation_refused(self):
        """Same strictness as /decide: 'true' is not True."""
        self.owner_post("/api/v1/owner/kill", {"reason": "x"})
        r = self.owner_post("/api/v1/owner/kill/release",
                            {"reason": "x", "confirmed_twice": "true"})
        self.assertEqual(r.status, 400)

    def test_release_non_object_body_is_400(self):
        for payload in (b"[]", b"null", b'"text"'):
            with self.subTest(payload=payload):
                r = self.app.handle(
                    "POST", "/api/v1/owner/kill/release",
                    {"host": OWNER_HOST,
                     "authorization": "Bearer " + self.owner_session},
                    payload,
                )
                self.assertEqual(r.status, 400)


if __name__ == "__main__":
    unittest.main()
