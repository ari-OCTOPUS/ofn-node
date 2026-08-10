"""O7 — studio draft workflow + owner consent administration.

- draft creation via the partner route (POST /studio/drafts)
- consent admin endpoints are owner-only and only digest/scope (no bytes)
- revoke is a mutation recorded by the owner
"""

from __future__ import annotations

import json
import os
import unittest

from ofn.adapters.consent_store import ConsentStore
from ofn.adapters.facts import FactStore
from ofn.adapters.http_api import ApiApp, HostMap
from ofn.adapters.ledger import Ledger
from ofn.adapters.media import MediaStore
from ofn.adapters.outbox import Outbox
from ofn.adapters.studio_store import StudioStore
from ofn.kernel.auth import issue_session
from ofn.kernel.domain import PackSpec, TenantId
from ofn.kernel.quota import NodeQuota
from ofn.kernel.tenancy import TenantRegistry
from ofn.node import Node

from tests.tmpdir import temp_dir

NOW = 1_785_000_000
NOW_ISO = "2026-08-10T12:00:00Z"
SECRET = "o7-test-secret"


class StudioO7Base(unittest.TestCase):
    def setUp(self):
        self.dir = temp_dir(self)
        registry = TenantRegistry({
            "studio": PackSpec(tenant=TenantId("studio"),
                               capacity_units_per_week=5, quota_share=1.0),
        })
        self.node = Node(
            registry=registry,
            quota=NodeQuota(estimated_capacity_tokens=1_000_000,
                            utilisation=1.0, shares={"studio": 1.0}),
            ledger=Ledger(os.path.join(self.dir, "ledger.sqlite")),
            facts=FactStore(os.path.join(self.dir, "facts.sqlite")),
            outbox=Outbox(os.path.join(self.dir, "outbox.sqlite")),
            studio=StudioStore(os.path.join(self.dir, "studio.sqlite")),
            consent=ConsentStore(os.path.join(self.dir, "consent.sqlite")),
            media=MediaStore(os.path.join(self.dir, "photos")),
            now_epoch_s=lambda: NOW,
            now_iso=lambda: NOW_ISO,
        )
        self.addCleanup(self.node.close)
        self.app = ApiApp(
            registry,
            HostMap(tenants={"s.test": "studio"}, owner_host="panel.test"),
            bot_tokens={"__owner__": "t", "studio": "h"},
            session_secret=SECRET,
            owner_user_ids=("1",),
            partner_user_ids={"studio": ("2",)},
            now=lambda: NOW,
            create_draft=self.node.create_draft,
            attach_media=self.node.attach_media,
            record_felt=self.node.record_felt,
            owner_consent_subjects=self.node.owner_consent_subjects,
            owner_consent_gaps=self.node.owner_consent_gaps,
            owner_consent_add_subject=self.node.owner_consent_add_subject,
            owner_consent_add_release=self.node.owner_consent_add_release,
            owner_consent_revoke=self.node.owner_consent_revoke,
        )
        self.owner = issue_session("owner", "1", SECRET, now_epoch_s=NOW)
        self.partner = issue_session("studio", "2", SECRET, now_epoch_s=NOW)

    def _owner(self, method, path, body=None):
        return self.app.handle(
            method, path,
            {"host": "panel.test",
             "authorization": "Bearer " + self.owner},
            json.dumps(body or {}).encode() if body is not None else b"")

    def _partner(self, method, path, body=None):
        return self.app.handle(
            method, path,
            {"host": "s.test",
             "authorization": "Bearer " + self.partner},
            json.dumps(body or {}).encode() if body is not None else b"")


class TestDraftCreationFromUI(StudioO7Base):
    def test_partner_creates_draft(self):
        resp = self._partner("POST", "/api/v1/studio/drafts",
                             {"caption": "پست جدید"})
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.body.get("ok"))
        draft_id = resp.body.get("draft_id")
        self.assertTrue(draft_id)
        # Read back on the board — API saying ok is not enough (O7).
        drafts = self.node.studio.drafts("studio") or []
        ids = [d.draft_id for d in drafts]
        self.assertIn(draft_id, ids)

    def test_draft_creation_requires_auth(self):
        resp = self.app.handle("POST", "/api/v1/studio/drafts",
                               {"host": "s.test"}, b"{}")
        self.assertEqual(resp.status, 401)


class TestConsentAdmin(StudioO7Base):
    def test_subjects_list_owner_only(self):
        resp = self._owner("GET", "/api/v1/owner/consent/subjects")
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.body.get("ok"))
        # Partner cannot reach the owner consent surface.
        resp = self.app.handle(
            "GET", "/api/v1/owner/consent/subjects",
            {"host": "s.test",
             "authorization": "Bearer " + self.partner}, b"")
        self.assertNotEqual(resp.status, 200)

    def test_add_subject_and_release(self):
        out = self._owner("POST", "/api/v1/owner/consent/subjects",
                          {"subject_id": "s1", "label": "خودم"})
        self.assertTrue(out.body.get("ok"))
        out = self._owner("POST", "/api/v1/owner/consent/releases",
                          {"release_id": "r1", "subject_id": "s1",
                           "scope": "instagram",
                           "document_ref": "safe/box/1"})
        self.assertTrue(out.body.get("ok"), out.body)
        # Revoke
        out = self._owner(
            "POST", "/api/v1/owner/consent/releases/r1/revoke")
        self.assertTrue(out.body.get("ok"))

    def test_gaps_reported(self):
        # A draft exists with a subject that has no release → gap.
        self._owner("POST", "/api/v1/owner/consent/subjects",
                    {"subject_id": "nobody", "label": "بدون رضایت"})
        out = self._partner("POST", "/api/v1/studio/drafts",
                            {"caption": "x"})
        draft_id = out.body["draft_id"]
        self.node.consent.add_to_draft(
            draft_id, "nobody", added_by="partner:2",
            now_epoch_s=NOW)
        gaps = self._owner("GET", "/api/v1/owner/consent/gaps")
        self.assertTrue(gaps.body.get("ok"))
        found = any(g["draft_id"] == draft_id
                    for g in gaps.body.get("gaps", []))
        self.assertTrue(found)


if __name__ == "__main__":
    unittest.main()
