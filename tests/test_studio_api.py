"""The studio surface, end to end: draft → media → consent → outbox.

The one thing every test here is really checking is that the publish path
stops at the outbox. Nothing in this leg reaches a platform, and the consent
gate is evaluated on the node rather than trusted from the screen — a screen
can be stale, edited or replayed, and the ledger entry that follows has to be
true about the moment it was written.
"""

from __future__ import annotations

import base64
import json
import os
import tempfile
import unittest

from ofn.adapters.consent_store import ConsentStore
from ofn.adapters.facts import FactStore
from ofn.adapters.http_api import ApiApp, HostMap
from ofn.adapters.ledger import Ledger
from ofn.adapters.media import MediaStore
from ofn.adapters.outbox import Outbox
from ofn.adapters.packloader import load_pack
from ofn.adapters.studio_store import StudioStore
from ofn.kernel.auth import issue_session
from ofn.kernel.domain import RiskTier
from ofn.kernel.tenancy import TenantRegistry
from ofn.node import Node

NOW_S = 1_785_000_000
NOW_ISO = "2026-08-05T09:00:00Z"
SECRET = "s"
SABA = "6150431610"
HOST = {"host": "st.test"}
SHA = "d" * 64

# Two renditions, as a canvas would send them.
IMG = base64.b64encode(b"\xff\xd8\xff" + b"x" * 200).decode()
RENDITIONS = {"1600": "data:image/jpeg;base64," + IMG,
              "320": "data:image/jpeg;base64," + IMG}


class Base(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        pack = load_pack("packs/studio.yaml") if os.path.exists(
            "packs/studio.yaml") else load_pack("packs/ziman.yaml")
        self.tenant = pack.tenant.value
        registry = TenantRegistry({self.tenant: pack})
        self.ledger = Ledger(os.path.join(d, "l.sqlite"))
        self.studio = StudioStore(os.path.join(d, "s.sqlite"))
        self.consent = ConsentStore(os.path.join(d, "c.sqlite"))
        self.media = MediaStore(os.path.join(d, "media"))
        self.outbox = Outbox(os.path.join(d, "o.sqlite"))
        for store in (self.ledger, self.studio, self.consent, self.outbox):
            self.addCleanup(store.close)

        self.node = Node(
            registry=registry, quota=None, ledger=self.ledger,
            facts=FactStore(os.path.join(d, "f.sqlite")), outbox=self.outbox,
            now_epoch_s=lambda: NOW_S, now_iso=lambda: NOW_ISO,
            studio=self.studio, consent=self.consent, media=self.media)
        self.app = ApiApp(
            registry, HostMap(tenants={"st.test": self.tenant},
                              owner_host="p.test"),
            bot_tokens={self.tenant: "t", "__owner__": "t"},
            session_secret=SECRET, owner_user_ids=("7",),
            partner_user_ids={self.tenant: [SABA]}, now=lambda: NOW_S,
            studio_board=self.node.studio_board,
            create_draft=self.node.create_draft,
            attach_media=self.node.attach_media,
            publish_draft=self.node.publish_draft,
            record_felt=self.node.record_felt)
        self.session = issue_session(self.tenant, SABA, SECRET,
                                     now_epoch_s=NOW_S)

    def call(self, method, path, body=None):
        headers = dict(HOST, authorization="Bearer " + self.session)
        return self.app.handle(method, path, headers,
                               json.dumps(body or {}).encode())

    def scope(self):
        return self.node.registry.scope(
            self.node.registry.pack(self.tenant).tenant)

    def person(self, sid="saba"):
        self.consent.add_subject(self.tenant, sid, "خودم", now_epoch_s=NOW_S)
        return sid

    def paper(self, sid="saba", scope="instagram", rid="r1"):
        self.consent.record_release(
            rid, sid, scope=scope, signed_at=NOW_S - 86400,
            document_ref="safe/1", document_sha256=SHA,
            recorded_by="operator:ari")

    def draft(self, subjects=("saba",)):
        """The id is minted by the node, not chosen here — a client-chosen id
        becomes a filesystem path once media lands under it."""
        r = self.call("POST", "/api/v1/studio/drafts",
                      {"caption": "متن", "subjects": list(subjects)})
        self.did = r.body.get("draft_id")
        return r

    def attach(self, did=None, position=0):
        did = did or self.did
        return self.call("POST", f"/api/v1/studio/drafts/{did}/media",
                         {"position": position, "renditions": RENDITIONS})


class TestAuth(Base):
    def test_no_session_is_refused(self):
        r = self.app.handle("GET", "/api/v1/studio/board", dict(HOST), b"")
        self.assertEqual(r.status, 401)

    def test_an_unknown_verb_is_not_a_route(self):
        self.person(); self.draft()
        self.assertEqual(self.call(
            "POST", f"/api/v1/studio/drafts/{self.did}/delete").status, 404)

    def test_a_crafted_id_cannot_reach_another_route(self):
        for bad in ("x/publish/extra", "x", "/publish", "x//publish"):
            self.assertEqual(
                self.call("POST", f"/api/v1/studio/drafts/{bad}").status, 404,
                bad)


class TestTheBoard(Base):
    def test_an_empty_board_is_empty_not_invented(self):
        body = self.call("GET", "/api/v1/studio/board").body
        self.assertEqual(body["drafts"], [])

    def test_a_draft_appears_with_its_consent_state(self):
        self.person(); self.paper()
        self.draft()
        row = self.call("GET", "/api/v1/studio/board").body["drafts"][0]
        self.assertEqual(row["draft_id"], self.did)
        self.assertTrue(row["consent_ok"])

    def test_the_board_reports_the_gates_answer_not_its_ingredients(self):
        """A shell that rebuilt this from the parts would be a second
        implementation of the rule, and the two would disagree eventually."""
        self.person()                      # subject, but no release
        self.draft()
        row = self.call("GET", "/api/v1/studio/board").body["drafts"][0]
        self.assertFalse(row["consent_ok"])
        self.assertEqual(row["consent_gaps"], {"saba": "no_release"})

    def test_a_draft_with_nobody_in_it_is_not_consent_ok(self):
        self.draft(subjects=())
        row = self.call("GET", "/api/v1/studio/board").body["drafts"][0]
        self.assertFalse(row["consent_ok"])


class TestMedia(Base):
    def test_both_renditions_land_on_disk(self):
        self.person(); self.draft()
        r = self.attach()
        self.assertEqual(r.status, 200)
        for edge in ("1600", "320"):
            self.assertTrue(self.media.exists(r.body["refs"][edge]))

    def test_no_original_is_written(self):
        """Keeping it proves nothing about what was published, and costs one
        more sensitive file at rest on an unencrypted disk."""
        self.person(); self.draft(); self.attach()
        names = [f for _, _, fs in os.walk(self.media.root) for f in fs]
        self.assertTrue(all("original" not in n for n in names), names)

    def test_an_oversized_payload_is_refused(self):
        self.person(); self.draft()
        huge = "data:image/jpeg;base64," + "A" * (24 * 1024 * 1024)
        r = self.call("POST", f"/api/v1/studio/drafts/{self.did}/media",
                      {"position": 0, "renditions": {"1600": huge, "320": IMG}})
        self.assertEqual(r.status, 400)

    def test_an_svg_is_refused(self):
        self.person(); self.draft()
        r = self.call("POST", f"/api/v1/studio/drafts/{self.did}/media",
                      {"position": 0, "renditions": {
                          "1600": "data:image/svg+xml;base64," + IMG,
                          "320": IMG}})
        self.assertEqual(r.status, 400)

    def test_a_missing_rendition_is_refused_rather_than_half_stored(self):
        self.person(); self.draft()
        r = self.call("POST", f"/api/v1/studio/drafts/{self.did}/media",
                      {"position": 0, "renditions": {"1600": IMG}})
        self.assertEqual(r.status, 400)


class TestPublishStopsAtTheOutbox(Base):
    def ready(self):
        self.person(); self.paper(); self.draft(); self.attach()

    def test_a_cleared_draft_is_queued(self):
        self.ready()
        r = self.call("POST", f"/api/v1/studio/drafts/{self.did}/publish")
        self.assertEqual(r.status, 200)
        self.assertEqual(r.body["status"], "queued")

    def test_it_lands_in_the_outbox_as_red(self):
        """Publishing a picture of a person is irreversible, leaves the
        device, and is a person. No configuration makes it anything else."""
        self.ready()
        self.call("POST", f"/api/v1/studio/drafts/{self.did}/publish")
        items = self.outbox.pending(self.scope())
        self.assertEqual(len(items), 1)
        self.assertIs(items[0].tier, RiskTier.RED)

    def test_nothing_is_sent(self):
        self.ready()
        self.call("POST", f"/api/v1/studio/drafts/{self.did}/publish")
        self.assertEqual(self.outbox.counts(self.scope()).get("sent", 0), 0)

    def test_publishing_twice_does_not_make_two_posts(self):
        """A network timeout that actually succeeded, retried, is the most
        common way an agentic system posts twice."""
        self.ready()
        self.call("POST", f"/api/v1/studio/drafts/{self.did}/publish")
        again = self.call("POST", f"/api/v1/studio/drafts/{self.did}/publish")
        self.assertFalse(again.body["queued"])
        self.assertEqual(len(self.outbox.pending(self.scope())), 1)

    def test_a_draft_without_consent_is_refused(self):
        self.person(); self.draft(); self.attach()      # no release
        r = self.call("POST", f"/api/v1/studio/drafts/{self.did}/publish")
        self.assertEqual(r.status, 400)
        self.assertEqual(r.body["blocked"], ["saba"])
        self.assertEqual(self.outbox.pending(self.scope()), [])

    def test_a_refusal_is_written_down(self):
        """So that "why did nothing publish" is answerable from the ledger
        rather than guessed at."""
        self.person(); self.draft(); self.attach()
        self.call("POST", f"/api/v1/studio/drafts/{self.did}/publish")
        kinds = [e.kind for e in self.ledger.read(self.scope())]
        self.assertIn("PUBLISH_REFUSED", kinds)

    def test_a_withdrawn_release_stops_it(self):
        self.ready()
        self.consent.revoke("r1", now_epoch_s=NOW_S)
        r = self.call("POST", f"/api/v1/studio/drafts/{self.did}/publish")
        self.assertEqual(r.status, 400)

    def test_a_release_for_another_platform_stops_it(self):
        self.person(); self.paper(scope="telegram")
        self.draft(); self.attach()
        r = self.call("POST", f"/api/v1/studio/drafts/{self.did}/publish")
        self.assertEqual(r.status, 400)

    def test_a_draft_with_no_media_is_refused(self):
        self.person(); self.paper(); self.draft()
        r = self.call("POST", f"/api/v1/studio/drafts/{self.did}/publish")
        self.assertEqual(r.status, 400)

    def test_the_gate_is_evaluated_here_not_taken_from_the_caller(self):
        """The shell cannot assert its way past consent."""
        self.person(); self.draft(); self.attach()
        r = self.call("POST", f"/api/v1/studio/drafts/{self.did}/publish",
                      {"consent_ok": True, "force": True})
        self.assertEqual(r.status, 400)


class TestHerReading(Base):
    def test_a_rating_before_any_number_is_trustworthy(self):
        self.person(); self.draft()
        r = self.call("POST", f"/api/v1/studio/drafts/{self.did}/felt", {"rating": 4})
        self.assertTrue(r.body["trustworthy"])

    def test_a_rating_after_a_number_is_kept_but_marked(self):
        self.person(); self.draft()
        self.studio.record_first_metric(self.did, now_epoch_s=NOW_S - 10)
        r = self.call("POST", f"/api/v1/studio/drafts/{self.did}/felt", {"rating": 4})
        self.assertTrue(r.body["ok"])
        self.assertFalse(r.body["trustworthy"])

    def test_an_out_of_range_rating_is_refused(self):
        self.person(); self.draft()
        for bad in (0, 6, "3", True):
            self.assertEqual(
                self.call("POST", f"/api/v1/studio/drafts/{self.did}/felt",
                          {"rating": bad}).status, 400, bad)


if __name__ == "__main__":
    unittest.main()
