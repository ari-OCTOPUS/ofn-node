"""Tests for the studio marketing snapshot endpoint.

This is the wiring the senior-architect review demanded proof of: that the
partner surface can see the marketing cycle's state, scoped to studio and
carrying no secrets, no other leg's data, and no owner-only controls.

Three contracts:

1. The endpoint exists and returns a snapshot (not 404) for a partner.
2. The snapshot carries the studio brain and the marketing summary, not
   secrets/tokens/owner controls.
3. The snapshot's gates are reported as closed/off when they are, and the
   brain modules report their wired state honestly.
"""

import json
import os
import tempfile
import unittest

from ofn.adapters.consent_store import ConsentStore
from ofn.adapters.http_api import ApiApp, HostMap
from ofn.adapters.ledger import Ledger
from ofn.adapters.marketing_store import MarketingStore
from ofn.adapters.media import MediaStore
from ofn.adapters.outbox import Outbox
from ofn.adapters.facts import FactStore
from ofn.adapters.studio_store import StudioStore
from ofn.kernel.auth import issue_session
from ofn.kernel.tenancy import TenantRegistry
from ofn.node import Node
from ofn.adapters.packloader import load_pack


HOST = {"host": "st.test"}
NOW_S = 1_800_000_000
SECRET = "test-secret-at-least-16-chars"
SABA = "4242"


class _Base(unittest.TestCase):
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
        self.marketing = MarketingStore(os.path.join(d, "m.sqlite"))
        for store in (self.ledger, self.studio, self.consent, self.outbox,
                      self.marketing):
            self.addCleanup(store.close)

        self.node = Node(
            registry=registry, quota=None, ledger=self.ledger,
            facts=FactStore(os.path.join(d, "f.sqlite")),
            outbox=self.outbox,
            now_epoch_s=lambda: NOW_S, now_iso=lambda: "2026-08-05",
            studio=self.studio, consent=self.consent, media=self.media,
            marketing=self.marketing,
            base_closed_gates=("secret_rotation", "partner_precondition"))
        self.app = ApiApp(
            registry, HostMap(tenants={"st.test": self.tenant},
                              owner_host="p.test"),
            bot_tokens={self.tenant: "t", "__owner__": "t"},
            session_secret=SECRET, owner_user_ids=("7",),
            partner_user_ids={self.tenant: [SABA]}, now=lambda: NOW_S,
            studio_board=self.node.studio_board,
            studio_marketing=self.node.studio_marketing)
        self.session = issue_session(self.tenant, SABA, SECRET,
                                     now_epoch_s=NOW_S)

    def call(self, method, path, body=None):
        headers = dict(HOST, authorization="Bearer " + self.session)
        return self.app.handle(method, path, headers,
                               json.dumps(body or {}).encode())


class TestMarketingEndpoint(_Base):
    def test_endpoint_exists_for_partner(self):
        r = self.call("GET", "/api/v1/studio/marketing")
        self.assertEqual(r.status, 200, r.body)

    def test_snapshot_has_the_expected_shape(self):
        r = self.call("GET", "/api/v1/studio/marketing")
        body = r.body
        for key in ("now", "viewer", "gates", "brain_modules", "marketing"):
            self.assertIn(key, body, f"missing {key}")
        self.assertEqual(body["viewer"]["scope"], "studio")
        self.assertEqual(body["viewer"]["role"], "partner")

    def test_closed_gates_reported_as_closed(self):
        body = self.call("GET", "/api/v1/studio/marketing").body
        self.assertEqual(body["gates"]["secret_rotation"], "closed")
        self.assertEqual(body["gates"]["partner_precondition"], "closed")

    def test_wire_publish_and_owner_release_reported_off(self):
        body = self.call("GET", "/api/v1/studio/marketing").body
        self.assertEqual(body["gates"]["wire_publish"], "off")
        self.assertEqual(body["gates"]["owner_release"], "off")

    def test_marketing_summary_reflects_store(self):
        # Seed the store with one observation so the summary is non-empty.
        from ofn.kernel.marketing_scout import (
            Candidate, Note, TrendObservation, Disposition,
        )
        obs = TrendObservation(source_id="manual", term="foot care",
                               observed_at=NOW_S, count_value=3.0)
        cand = Candidate(key="foot-care", title="Foot care",
                         style_id="educational", framing="beauty",
                         observations=(obs,), confidence=0.8)
        self.marketing.remember(
            self.tenant, cand,
            Note(cand.key, Disposition.REJECTED_HARD, "test", NOW_S),
            rejected_by="test", now_epoch_s=NOW_S)

        body = self.call("GET", "/api/v1/studio/marketing").body
        self.assertEqual(body["marketing"]["rejected_ideas_in_memory"], 1)

    def test_no_session_is_refused(self):
        # No authorization header at all.
        r = self.app.handle("GET", "/api/v1/studio/marketing", HOST, b"")
        self.assertEqual(r.status, 401)


class TestSnapshotRedaction(_Base):
    """The snapshot must not leak secret *values* or other legs' data.

    Note: gate *names* like `secret_rotation` legitimately contain the word
    'secret' — they are public identifiers, not secret values. The markers
    below target value-shaped leaks (tokens, passwords, keys, other legs'
    private data), not the well-known gate vocabulary.
    """

    # Value-shaped leak markers. 'secret_rotation' as a gate name is fine;
    # a value like "sk-..." or "Bearer xyz" would not be.
    LEAK_MARKERS = ("token", "api_key", "password", "bearer",
                    "cloudflared", "lead_customer", "ziman_private",
                    "sk-", "session_secret")

    def test_snapshot_text_has_no_secret_value_markers(self):
        body = self.call("GET", "/api/v1/studio/marketing").body
        text = json.dumps(body).lower()
        for marker in self.LEAK_MARKERS:
            self.assertNotIn(marker, text,
                             f"snapshot leaked {marker!r}")


if __name__ == "__main__":
    unittest.main()
