"""Owner Command Center read models: truthful, bounded, and owner-only.

The owner surface crosses all three tenant boundaries.  That makes its shape a
security contract, not just a dashboard contract: every field is an explicit
projection, unknown is never dressed up as healthy, and no raw outbox or ledger
payload is returned.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from ofn.adapters.facts import FactStore
from ofn.adapters.http_api import ApiApp, HostMap
from ofn.adapters.ledger import Ledger
from ofn.adapters.outbox import Outbox
from ofn.kernel.auth import issue_session
from ofn.kernel.domain import PackSpec, RiskTier, TenantId
from ofn.kernel.quota import NodeQuota
from ofn.kernel.tenancy import TenantRegistry
from ofn.node import Node


NOW = 1_800_000_000
NOW_ISO = "2027-01-15T08:00:00Z"
SECRET = "owner-api-test-secret"
OWNER_ID = "5001"
PARTNER_ID = "7001"
OWNER_HOST = "panel.test"
PARTNER_HOST = "studio.test"
OWNER_PATHS = (
    "/api/v1/owner/snapshot",
    "/api/v1/owner/businesses",
    "/api/v1/owner/businesses/studio/snapshot",
    "/api/v1/owner/partners",
    "/api/v1/owner/mini-apps",
    "/api/v1/owner/core/snapshot",
    "/api/v1/owner/risks",
    "/api/v1/owner/ledger/summary",
)


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


class OwnerApiBase(unittest.TestCase):
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
        quota = NodeQuota(
            estimated_capacity_tokens=100_000,
            utilisation=0.4,
            shares={"lead": 0.30, "studio": 0.30, "ziman": 0.40},
        )
        self.node = Node(
            registry=registry,
            quota=quota,
            ledger=self.ledger,
            facts=self.facts,
            outbox=self.outbox,
            now_epoch_s=lambda: NOW,
            now_iso=lambda: NOW_ISO,
            base_closed_gates=("secret_rotation",),
        )

        # Seed sensitive values deliberately.  The new projections may count
        # these rows but must never serialize their payload or note.
        ziman = registry.scope("ziman")
        self.outbox.enqueue(
            ziman,
            "red-1",
            "publish",
            {"text": "PRIVATE-CUSTOMER-TEXT", "token": "sk-never-return"},
            RiskTier.RED,
            NOW_ISO,
        )
        self.ledger.append(
            ziman,
            "PRIVATE_EVENT",
            {"password": "never-return", "customer": "private-person"},
            NOW_ISO,
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
            partner_user_ids={
                "lead": (),
                "studio": (PARTNER_ID,),
                # ziman deliberately absent: missing differs from empty.
            },
            now=lambda: NOW,
            owner_queue=self.node.owner_queue,
            owner_decide=self.node.owner_decide,
            owner_status=self.node.owner_status,
            owner_events=self.node.recent_events,
            owner_snapshot=self.node.owner_snapshot,
            owner_businesses=self.node.owner_businesses,
            owner_business_snapshot=self.node.owner_business_snapshot,
            owner_core_snapshot=self.node.owner_core_snapshot,
            owner_risks=self.node.owner_risks,
            owner_ledger_summary=self.node.owner_ledger_summary,
            mini_apps=(
                {"id": "lead", "business_id": "lead", "role": "partner",
                 "listen_port": 8792, "paths": ("/", "/index.html")},
                {"id": "studio", "business_id": "studio", "role": "partner",
                 "listen_port": 8793,
                 "paths": ("/", "/index.html", "/sabaapp")},
                {"id": "ziman", "business_id": "ziman", "role": "partner",
                 "listen_port": 8791, "paths": ("/", "/index.html")},
                {"id": "owner", "business_id": None, "role": "owner",
                 "listen_port": 8794, "paths": ("/", "/index.html")},
            ),
        )
        self.owner_session = issue_session(
            "owner", OWNER_ID, SECRET, now_epoch_s=NOW)
        self.partner_session = issue_session(
            "studio", PARTNER_ID, SECRET, now_epoch_s=NOW)

    def owner_get(self, path: str):
        return self.app.handle(
            "GET", path,
            {"host": OWNER_HOST,
             "authorization": "Bearer " + self.owner_session},
            b"",
        )


class TestOwnerReadRoutes(OwnerApiBase):
    def test_all_phase_two_reads_exist_and_are_no_store(self):
        for path in OWNER_PATHS:
            with self.subTest(path=path):
                response = self.owner_get(path)
                self.assertEqual(response.status, 200, response.body)
                self.assertEqual(
                    response.headers.get("Cache-Control"),
                    "private, no-store",
                )

    def test_all_reads_require_an_owner_session(self):
        for path in OWNER_PATHS:
            with self.subTest(path=path):
                anonymous = self.app.handle(
                    "GET", path, {"host": OWNER_HOST}, b"")
                self.assertEqual(anonymous.status, 401)
                cross_role = self.app.handle(
                    "GET", path,
                    {"host": OWNER_HOST,
                     "authorization": "Bearer " + self.partner_session},
                    b"",
                )
                self.assertEqual(cross_role.status, 401)

    def test_business_id_is_one_known_path_segment(self):
        for path in (
            "/api/v1/owner/businesses/nope/snapshot",
            "/api/v1/owner/businesses/studio/extra/snapshot",
            "/api/v1/owner/businesses//snapshot",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.owner_get(path).status, 404)

    def test_gets_have_no_ledger_or_outbox_side_effect(self):
        before_ledger = {
            t.value: self.ledger.count(self.node.registry.scope(t))
            for t in self.node.registry
        }
        before_outbox = {
            t.value: dict(self.outbox.counts(self.node.registry.scope(t)))
            for t in self.node.registry
        }
        for path in OWNER_PATHS:
            self.assertEqual(self.owner_get(path).status, 200)
        after_ledger = {
            t.value: self.ledger.count(self.node.registry.scope(t))
            for t in self.node.registry
        }
        after_outbox = {
            t.value: dict(self.outbox.counts(self.node.registry.scope(t)))
            for t in self.node.registry
        }
        self.assertEqual(after_ledger, before_ledger)
        self.assertEqual(after_outbox, before_outbox)


class TestTruthfulOwnerProjection(OwnerApiBase):
    def test_businesses_are_deterministic_and_do_not_invent_identity(self):
        body = self.owner_get("/api/v1/owner/businesses").body
        rows = body["businesses"]
        self.assertEqual([r["id"] for r in rows], ["lead", "studio", "ziman"])
        for row in rows:
            self.assertIsNone(row["identity"]["display_name"])
            self.assertEqual(row["identity"]["status"], "not_canonical")
            self.assertEqual(row["operational_status"]["status"], "not_modeled")
            self.assertEqual(
                set(row["decision_counts"]),
                {"pending", "in_flight", "held", "sent", "failed"},
            )
            self.assertEqual(row["quota"]["persistence"], "process_memory")
            self.assertTrue(row["quota"]["resets_on_restart"])

    def test_business_detail_has_only_safe_ledger_head_metadata(self):
        body = self.owner_get(
            "/api/v1/owner/businesses/ziman/snapshot").body
        self.assertEqual(body["business"]["id"], "ziman")
        self.assertEqual(body["ledger_head"]["seq"], 1)
        self.assertNotIn("payload", body["ledger_head"])
        self.assertLessEqual(len(body["ledger_head"]["hash_prefix"]), 16)

    def test_partner_counts_are_safe_and_activity_is_unknown(self):
        body = self.owner_get("/api/v1/owner/partners").body
        rows = {r["business_id"]: r for r in body["businesses"]}
        self.assertEqual(rows["studio"]["configured_account_count"], 1)
        self.assertEqual(rows["lead"]["configured_account_count"], 0)
        self.assertEqual(rows["lead"]["configuration_status"], "locked_empty")
        self.assertEqual(rows["ziman"]["configuration_status"], "missing")
        for row in rows.values():
            self.assertEqual(row["identifiers"], "omitted")
            self.assertEqual(row["activity"], {
                "status": "unknown", "reason": "not_measured"})
        serial = json.dumps(body)
        self.assertNotIn(PARTNER_ID, serial)
        self.assertNotIn(OWNER_ID, serial)

    def test_configured_mini_app_is_not_reported_healthy(self):
        body = self.owner_get("/api/v1/owner/mini-apps").body
        self.assertEqual(len(body["mini_apps"]), 4)
        for app in body["mini_apps"]:
            self.assertIn(app["configuration_status"], {"configured", "partial"})
            self.assertEqual(app["health"], {
                "status": "unknown", "reason": "not_measured"})
            self.assertNotIn("host", app)

    def test_core_labels_process_local_and_unmeasured_state(self):
        core = self.owner_get("/api/v1/owner/core/snapshot").body
        self.assertEqual(core["liveness"]["source"], "live_ledger_read")
        self.assertEqual(core["quota"]["persistence"], "process_memory")
        self.assertTrue(core["quota"]["resets_on_restart"])
        self.assertEqual(core["watchdog"], {
            "status": "unknown", "reason": "not_exposed"})
        self.assertEqual(core["worker"]["persistence"], "process_memory")
        self.assertEqual(core["brain"]["provider_reachability"], "unknown")

    def test_risk_endpoint_is_bounded_partial_and_payload_free(self):
        body = self.owner_get("/api/v1/owner/risks").body
        self.assertEqual(body["coverage"], "actionable_queue")
        self.assertEqual(body["completeness"], "partial")
        self.assertEqual(body["counts"]["pending"], 1)
        self.assertEqual(len(body["items"]), 1)
        item = body["items"][0]
        self.assertEqual(
            set(item),
            {"id", "business_id", "kind", "tier", "state",
             "created_at", "needs_second_confirmation"},
        )
        serial = json.dumps(body)
        self.assertNotIn("PRIVATE-CUSTOMER-TEXT", serial)
        self.assertNotIn("sk-never-return", serial)
        self.assertNotIn("note", serial)
        self.assertNotIn("payload", serial)

    def test_ledger_is_named_as_audit_and_payload_is_omitted(self):
        body = self.owner_get("/api/v1/owner/ledger/summary").body
        self.assertEqual(body["kind"], "audit_event_ledger")
        self.assertTrue(body["verification"]["ok"])
        self.assertEqual(body["verification"]["reason_code"], "verified")
        serial = json.dumps(body)
        self.assertNotIn("never-return", serial)
        self.assertNotIn("private-person", serial)
        self.assertNotIn("payload", serial)
        self.assertNotIn("balance", serial)
        self.assertNotIn("revenue", serial)

    def test_snapshot_marks_unavailable_calibration_and_automation(self):
        body = self.owner_get("/api/v1/owner/snapshot").body
        self.assertEqual(body["snapshot_version"], "phase2-owner-v1")
        self.assertEqual(body["availability"]["status"], "partial")
        self.assertIsNone(body["calibration"]["action_score"])
        self.assertFalse(body["calibration"]["persisted"])
        self.assertEqual(body["automation"]["thinking"]["persistence"],
                         "process_memory")
        self.assertEqual(body["automation"]["state_machine"],
                         "not_implemented")


class TestOwnerDecisionBodyIsStrict(OwnerApiBase):
    def post(self, payload: bytes):
        return self.app.handle(
            "POST", "/api/v1/decide",
            {"host": OWNER_HOST,
             "authorization": "Bearer " + self.owner_session},
            payload,
        )

    def test_non_object_body_is_400_not_an_exception(self):
        for payload in (b"[]", b"null", b'"text"'):
            with self.subTest(payload=payload):
                self.assertEqual(self.post(payload).status, 400)

    def test_boolean_strings_are_refused(self):
        for body in (
            {"id": "ziman:red-1", "approve": "false"},
            {"id": "ziman:red-1", "approve": True,
             "confirmed_twice": "true"},
        ):
            with self.subTest(body=body):
                response = self.post(json.dumps(body).encode())
                self.assertEqual(response.status, 400)


if __name__ == "__main__":
    unittest.main()
