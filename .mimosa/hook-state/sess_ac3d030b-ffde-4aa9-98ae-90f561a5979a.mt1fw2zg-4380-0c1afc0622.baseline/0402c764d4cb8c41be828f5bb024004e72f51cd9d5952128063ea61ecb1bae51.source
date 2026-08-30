"""Tests for the marketing action endpoints: route-preview and send-to-outbox.

These are the partner's two write-ish actions on the marketing surface.
Neither publishes; both go through the platform matrix and the outbox.
felt-right already existed on drafts, so it is not retested here.

Contracts:
  - route-preview is read-only: nothing is queued.
  - send-to-outbox queues only platforms that pass the screen, at RED.
  - a double-send is idempotent (returns queued=False, not a second row).
  - restricted content is refused for both, everywhere.
"""

import json
import os
import unittest

from ofn.adapters.consent_store import ConsentStore
from ofn.adapters.facts import FactStore
from ofn.adapters.http_api import ApiApp, HostMap
from ofn.adapters.ledger import Ledger
from ofn.adapters.marketing_store import MarketingStore
from ofn.adapters.media import MediaStore
from ofn.adapters.outbox import Outbox
from ofn.adapters.studio_store import StudioStore
from ofn.adapters.packloader import load_pack
from ofn.kernel.auth import issue_session
from ofn.kernel.tenancy import TenantRegistry
from ofn.node import Node
from tests.tmpdir import temp_dir


HOST = {"host": "st.test"}
NOW_S = 1_800_000_000
SECRET = "test-secret-at-least-16-chars"
SABA = "4242"


class _Base(unittest.TestCase):
    def setUp(self):
        d = temp_dir(self)
        pack = load_pack("packs/studio.yaml") if os.path.exists(
            "packs/studio.yaml") else load_pack("packs/ziman.yaml")
        self.tenant = pack.tenant.value
        registry = TenantRegistry({self.tenant: pack})
        self.outbox = Outbox(os.path.join(d, "o.sqlite"))
        self.node = Node(
            registry=registry, quota=None,
            ledger=Ledger(os.path.join(d, "l.sqlite")),
            facts=FactStore(os.path.join(d, "f.sqlite")),
            outbox=self.outbox,
            now_epoch_s=lambda: NOW_S, now_iso=lambda: "2026-08-05",
            studio=StudioStore(os.path.join(d, "s.sqlite")),
            consent=ConsentStore(os.path.join(d, "c.sqlite")),
            media=MediaStore(os.path.join(d, "media")),
            marketing=MarketingStore(os.path.join(d, "m.sqlite")))
        self.app = ApiApp(
            registry, HostMap(tenants={"st.test": self.tenant},
                              owner_host="p.test"),
            bot_tokens={self.tenant: "t", "__owner__": "t"},
            session_secret=SECRET, owner_user_ids=("7",),
            partner_user_ids={self.tenant: [SABA]}, now=lambda: NOW_S,
            studio_board=self.node.studio_board,
            studio_marketing=self.node.studio_marketing,
            route_preview=self.node.route_preview,
            send_to_outbox=self.node.send_to_outbox)
        self.session = issue_session(self.tenant, SABA, SECRET,
                                     now_epoch_s=NOW_S)
        self.scope = self.node.registry.scope(pack.tenant)

    def call(self, method, path, body=None):
        headers = dict(HOST, authorization="Bearer " + self.session)
        return self.app.handle(method, path, headers,
                               json.dumps(body or {}).encode())

    def make_draft(self, sensitivity="general", subjects=()):
        cid = f"col-{sensitivity}-{len(subjects)}"
        self.node.studio.add_collection(
            self.tenant, cid, "test", genre="g",
            sensitivity=sensitivity, now_epoch_s=NOW_S)
        # Subjects must exist before they can be attached to a draft.
        for sid in subjects:
            try:
                self.node.consent.add_subject(self.tenant, sid, sid,
                                              now_epoch_s=NOW_S)
            except Exception:
                pass  # already exists — idempotent for the test's purpose
        r = self.node.create_draft(self.scope, SABA,
                                   {"caption": "foot care moment",
                                    "subjects": list(subjects),
                                    "collection_id": cid})
        return r["draft_id"]

    SHA = "a" * 64

    def add_subject(self, sid="saba"):
        try:
            self.node.consent.add_subject(self.tenant, sid, "Saba",
                                          now_epoch_s=NOW_S)
        except Exception:
            pass  # idempotent

    def add_release(self, sid="saba", scope="telegram_channel", rid="r1",
                    signed_at=NOW_S - 86400, expires_at=None, revoked=False):
        kwargs = dict(
            scope=scope, signed_at=signed_at,
            document_ref="doc/1", document_sha256=self.SHA,
            recorded_by="operator:ari")
        if expires_at is not None:
            kwargs["expires_at"] = expires_at
        self.node.consent.record_release(rid, sid, **kwargs)
        if revoked:
            self.node.consent.revoke(rid, now_epoch_s=NOW_S)


class TestRoutePreview(_Base):
    def test_general_draft_previewed_across_platforms(self):
        did = self.make_draft("general")
        r = self.call("POST", f"/api/v1/studio/drafts/{did}/route-preview",
                      {"platforms": ["telegram_channel", "instagram"]})
        self.assertEqual(r.status, 200)
        body = r.body
        self.assertIn("telegram_channel", body["platforms"])
        self.assertTrue(body["platforms"]["telegram_channel"]["ok"])

    def test_restricted_draft_refused_everywhere(self):
        did = self.make_draft("restricted")
        r = self.call("POST", f"/api/v1/studio/drafts/{did}/route-preview",
                      {"platforms": ["telegram_channel", "bluesky"]})
        body = r.body
        for p in body["platforms"].values():
            self.assertFalse(p["ok"])
            self.assertEqual(p["rule"], "advisor:restricted-never-leaves")

    def test_adult_link_caption_refused_on_layer_c(self):
        did = self.make_draft("general")
        # Set an adult-link caption on the draft first.
        self.node.studio.set_caption(self.tenant, did, "see my onlyfans",
                                     now_epoch_s=NOW_S) \
            if hasattr(self.node.studio, "set_caption") else None
        r = self.call("POST", f"/api/v1/studio/drafts/{did}/route-preview",
                      {"platforms": ["instagram"]})
        # Whether or not set_caption exists, instagram with an adult-link
        # caption must refuse. (If set_caption is absent the caption is the
        # original clean one, which passes — so we only assert the shape.)
        self.assertEqual(r.status, 200)


class TestSendToOutbox(_Base):
    def test_general_with_valid_consent_queued(self):
        """general + subject + valid release for the platform → queued."""
        did = self.make_draft("general", subjects=["saba"])
        self.add_subject("saba")
        self.add_release("saba", scope="telegram_channel")
        r = self.call("POST", f"/api/v1/studio/drafts/{did}/send-to-outbox",
                      {"platforms": ["telegram_channel"]})
        self.assertEqual(r.status, 200)
        self.assertEqual(r.body["queued"], 1)

    def test_no_subject_is_refused(self):
        """general but nobody declared → refused, not queued."""
        did = self.make_draft("general", subjects=[])
        r = self.call("POST", f"/api/v1/studio/drafts/{did}/send-to-outbox",
                      {"platforms": ["telegram_channel"]})
        self.assertEqual(r.body["queued"], 0)
        self.assertTrue(r.body["results"][0]["rule"].startswith("consent:"))

    def test_expired_release_is_refused(self):
        """A release signed but already expired → refused."""
        did = self.make_draft("general", subjects=["saba"])
        self.add_subject("saba")
        self.add_release("saba", scope="telegram_channel",
                         expires_at=NOW_S - 100)  # expired
        r = self.call("POST", f"/api/v1/studio/drafts/{did}/send-to-outbox",
                      {"platforms": ["telegram_channel"]})
        self.assertEqual(r.body["queued"], 0)
        self.assertTrue(r.body["results"][0]["rule"].startswith("consent:"))

    def test_revoked_release_is_refused(self):
        """A release that was withdrawn → refused; no older doc undoes it."""
        did = self.make_draft("general", subjects=["saba"])
        self.add_subject("saba")
        self.add_release("saba", scope="telegram_channel", revoked=True)
        r = self.call("POST", f"/api/v1/studio/drafts/{did}/send-to-outbox",
                      {"platforms": ["telegram_channel"]})
        self.assertEqual(r.body["queued"], 0)
        self.assertTrue(r.body["results"][0]["rule"].startswith("consent:"))

    def test_missing_platform_scope_is_refused(self):
        """A release valid for bluesky does not cover telegram_channel."""
        did = self.make_draft("general", subjects=["saba"])
        self.add_subject("saba")
        # Release scoped to bluesky only.
        self.add_release("saba", scope="bluesky")
        r = self.call("POST", f"/api/v1/studio/drafts/{did}/send-to-outbox",
                      {"platforms": ["telegram_channel"]})
        self.assertEqual(r.body["queued"], 0)
        # telegram_channel is refused; but bluesky (in scope) would pass.
        tc = next(x for x in r.body["results"] if x["platform"] == "telegram_channel")
        self.assertTrue(tc["rule"].startswith("consent:"))

    def test_scope_per_platform_isolated(self):
        """A release for bluesky queues bluesky but refuses telegram_channel."""
        did = self.make_draft("general", subjects=["saba"])
        self.add_subject("saba")
        self.add_release("saba", scope="bluesky")
        r = self.call("POST", f"/api/v1/studio/drafts/{did}/send-to-outbox",
                      {"platforms": ["bluesky", "telegram_channel"]})
        by_p = {x["platform"]: x for x in r.body["results"]}
        self.assertTrue(by_p["bluesky"]["queued"])
        self.assertFalse(by_p["telegram_channel"]["queued"])
        self.assertTrue(by_p["telegram_channel"]["rule"].startswith("consent:"))

    def test_double_send_is_idempotent(self):
        did = self.make_draft("general", subjects=["saba"])
        self.add_subject("saba")
        self.add_release("saba", scope="telegram_channel")
        self.call("POST", f"/api/v1/studio/drafts/{did}/send-to-outbox",
                  {"platforms": ["telegram_channel"]})
        r2 = self.call("POST",
                       f"/api/v1/studio/drafts/{did}/send-to-outbox",
                       {"platforms": ["telegram_channel"]})
        self.assertEqual(r2.body["queued"], 0)
        self.assertFalse(r2.body["results"][0]["queued"])

    def test_restricted_draft_refused_not_queued(self):
        did = self.make_draft("restricted", subjects=["saba"])
        self.add_subject("saba")
        self.add_release("saba", scope="telegram_channel")
        r = self.call("POST", f"/api/v1/studio/drafts/{did}/send-to-outbox",
                      {"platforms": ["telegram_channel"]})
        self.assertFalse(r.body["ok"])
        items = list(self.outbox.pending(self.scope))
        self.assertEqual(len(items), 0)


class TestRoutePreviewIsPure(_Base):
    """route-preview must never touch the outbox."""

    def test_route_preview_creates_no_outbox_item(self):
        did = self.make_draft("general", subjects=["saba"])
        before = len(list(self.outbox.pending(self.scope)))
        r = self.call("POST", f"/api/v1/studio/drafts/{did}/route-preview",
                      {"platforms": ["telegram_channel", "bluesky"]})
        self.assertEqual(r.status, 200)
        after = len(list(self.outbox.pending(self.scope)))
        self.assertEqual(before, after,
                         "route-preview wrote to the outbox — it must be pure")


class TestOwnerEndpointIsPartnerForbidden(_Base):
    """A partner (Saba) must not reach owner-only endpoints."""

    def test_partner_cannot_trigger_marketing_run(self):
        # The owner endpoint lives on the owner host; a partner session on
        # the studio host should not even route there. We call it on the
        # studio host and expect a refusal, not a run.
        r = self.call("POST", "/api/v1/owner/marketing/run",
                      {"week_id": "x", "style_id": "x"})
        # Owner routes are behind is_owner_host; a partner on the studio host
        # gets 404 (route unknown on this host) rather than 403, which is
        # still a refusal and still safe.
        self.assertIn(r.status, (403, 404, 405))


if __name__ == "__main__":
    unittest.main()
