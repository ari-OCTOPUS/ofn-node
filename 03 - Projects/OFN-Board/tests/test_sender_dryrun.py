"""O11 — dry-run sender tests.

The sender must be structurally unable to publish: only dry_run_diff
exists, it mutates nothing, and without a green release context it
refuses even to propose.
"""

from __future__ import annotations

import ast
import os
import unittest

from ofn.adapters.sender_dryrun import PublishIntent, dry_run_diff
from ofn.kernel.domain import RiskTier
from ofn.kernel.release_switch import (
    ReleaseContext, require_release_context,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SENDER = os.path.join(ROOT, "ofn", "adapters", "sender_dryrun.py")


def _green_release() -> dict:
    ctx = ReleaseContext(
        owner_confirmed_step1=True, owner_confirmed_step2=True,
        secret_rotation_open=True, partner_precondition_open=True,
        kill_switch_active=False, sensitivity="general",
        consent_ok=True, platform_ok=True, rate_limit_ok=True,
        idempotency_unused=True, ledger_ready=True)
    verdict = require_release_context(ctx)
    return {"ok": verdict.ok, "rule": verdict.rule,
            "risk": verdict.risk, "reason": verdict.rule}


class TestDryRunDiff(unittest.TestCase):
    def test_diff_builds_with_green_release(self):
        intent = PublishIntent("ziman", "bluesky", "k1", "کپشن تست")
        out = dry_run_diff(intent, _green_release())
        self.assertTrue(out["ok"])
        self.assertEqual(out["mode"], "dry-run")
        self.assertEqual(out["diff"]["caption"], "کپشن تست")
        self.assertEqual(out["diff"]["platform"], "bluesky")

    def test_refuses_without_release_context(self):
        intent = PublishIntent("ziman", "bluesky", "k1", "x")
        out = dry_run_diff(intent, None)
        self.assertFalse(out["ok"])
        self.assertEqual(out["rule"], "release:context-missing")

    def test_refuses_when_release_blocked(self):
        intent = PublishIntent("ziman", "bluesky", "k1", "x")
        blocked = {"ok": False, "rule": "release:kill-switch-active",
                   "risk": "RED", "reason": "kill"}
        out = dry_run_diff(intent, blocked)
        self.assertFalse(out["ok"])
        self.assertEqual(out["rule"], "release:kill-switch-active")

    def test_diff_is_deterministic(self):
        intent = PublishIntent("ziman", "bluesky", "k1", "کپشن")
        rel = _green_release()
        a = dry_run_diff(intent, rel)
        b = dry_run_diff(intent, rel)
        self.assertEqual(a["diff"]["payload_json"],
                         b["diff"]["payload_json"])


class TestNoRealSender(unittest.TestCase):
    def test_module_has_no_send_function(self):
        with open(SENDER, encoding="utf-8") as fh:
            src = fh.read()
        tree = ast.parse(src)
        funcs = [n.name for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        for name in funcs:
            self.assertNotIn("send", name.lower(),
                             f"module must not define {name}")

    def test_no_transport_imports(self):
        with open(SENDER, encoding="utf-8") as fh:
            src = fh.read()
        for token in ("urllib.request", "requests", "http.client",
                      "smtplib", "telebot"):
            self.assertNotIn(token, src)


if __name__ == "__main__":
    unittest.main()


class TestPublishToTelegram(unittest.TestCase):
    """O11 real-publish path: outbox-mediated (P0-2), real release checks
    (P0-3). A send is the completion of an approved outbox item — there is
    no free-standing send anymore."""

    NOW = 1_785_000_000

    def _node(self, *, killed=False, wire_consent=True, wire_budget=True,
              wire_studio=True):
        import os
        from ofn.adapters.consent_store import ConsentStore
        from ofn.adapters.facts import FactStore
        from ofn.adapters.ledger import Ledger
        from ofn.adapters.outbox import Outbox
        from ofn.adapters.studio_store import StudioStore
        from ofn.kernel.callbudget import CallBudget
        from ofn.kernel.domain import PackSpec, TenantId
        from ofn.kernel.quota import NodeQuota
        from ofn.kernel.tenancy import TenantRegistry
        from ofn.node import Node
        from tests.tmpdir import temp_dir
        d = temp_dir(self)
        registry = TenantRegistry({
            "studio": PackSpec(tenant=TenantId("studio"),
                               capacity_units_per_week=5, quota_share=1.0)})
        node = Node(
            registry=registry,
            quota=NodeQuota(estimated_capacity_tokens=1_000_000,
                            utilisation=1.0, shares={"studio": 1.0}),
            ledger=Ledger(os.path.join(d, "l.sqlite")),
            facts=FactStore(os.path.join(d, "f.sqlite")),
            outbox=Outbox(os.path.join(d, "o.sqlite")),
            studio=(StudioStore(os.path.join(d, "s.sqlite"))
                    if wire_studio else None),
            consent=(ConsentStore(os.path.join(d, "c.sqlite"))
                     if wire_consent else None),
            now_epoch_s=lambda: self.NOW,
            now_iso=lambda: "2026-08-10T12:00:00Z",
            killed=killed,
            _telegram_channel_id="@testchannel",
            _telegram_token="t:test",
        )
        if wire_budget:
            node.call_budget = CallBudget()
        self.addCleanup(node.close)
        return node, d, registry

    def _green_item(self, node, registry, *, idem="k1", caption="متن تست",
                    draft_id="d1"):
        """A studio draft with general sensitivity + consented subject, and
        the outbox item approved (approved_manual). This is the minimal
        state where every real release check passes."""
        from ofn.adapters.outbox import APPROVED_MANUAL
        from ofn.kernel.domain import RiskTier
        scope = registry.scope("studio")
        # General collection + draft with a caption.
        if node.studio is not None:
            node.studio.add_collection("studio", "coll-1", "عمومی",
                                       sensitivity="general",
                                       now_epoch_s=self.NOW)
            node.studio.add_draft("studio", draft_id,
                                  collection_id="coll-1", caption=caption,
                                  now_epoch_s=self.NOW)
        # Subject with a live telegram_channel release, attached to draft.
        if node.consent is not None:
            node.consent.add_subject("studio", "s1", "خودم",
                                     now_epoch_s=self.NOW)
            node.consent.record_release(
                "r1", "s1", scope="telegram_channel",
                signed_at=self.NOW - 86_400, document_ref="box",
                document_sha256="0" * 64, recorded_by="ari")
            node.consent.add_to_draft(draft_id, "s1", added_by="saba",
                                      now_epoch_s=self.NOW)
        # The item itself: approved for manual delivery.
        payload = {"draft_id": draft_id, "platform": "telegram_channel",
                   "caption": caption, "framing": "community",
                   "adult_label": False}
        node.outbox.enqueue(scope, idem, "studio:publish", payload,
                            RiskTier.RED, "2026-08-10T12:00:00Z")
        node.outbox.approve_manual(scope, idem,
                                   "2026-08-10T12:00:00Z", approved_by="owner")
        item = node.outbox.get(scope, idem)
        self.assertEqual(item.status, APPROVED_MANUAL)
        return scope

    def test_dry_run_returns_diff_without_network(self):
        node, d, registry = self._node()
        scope = self._green_item(node, registry)
        out = node.publish_to_telegram(
            scope, idem_key="k1", dry_run=True, confirmed_twice=True)
        self.assertTrue(out["ok"])
        self.assertTrue(out["dry_run"])
        self.assertEqual(out["rule"], "adapter:dry-run")
        # No ledger mutation of a real send.
        events = node.ledger.read(scope, limit=5)
        self.assertEqual(len(events), 1)   # the dry-run ledger event

    def test_dry_run_leaves_the_item_approved(self):
        """A dry-run is a preview: it must not consume the item."""
        from ofn.adapters.outbox import APPROVED_MANUAL
        node, d, registry = self._node()
        scope = self._green_item(node, registry)
        node.publish_to_telegram(
            scope, idem_key="k1", dry_run=True, confirmed_twice=True)
        item = node.outbox.get(scope, "k1")
        self.assertEqual(item.status, APPROVED_MANUAL)

    def test_kill_switch_blocks(self):
        node, d, registry = self._node(killed=True)
        scope = self._green_item(node, registry)
        out = node.publish_to_telegram(
            scope, idem_key="k1", dry_run=False, confirmed_twice=True)
        self.assertFalse(out["ok"])
        self.assertEqual(out["rule"], "release:kill-switch-active")

    def test_second_confirmation_required_for_real(self):
        node, d, registry = self._node()
        scope = self._green_item(node, registry)
        out = node.publish_to_telegram(
            scope, idem_key="k1", dry_run=False, confirmed_twice=False)
        self.assertFalse(out["ok"])
        self.assertEqual(out["rule"], "release:owner-two-step-required")

    def test_caption_cap(self):
        """Over the platform matrix's telegram caption_max (1024) the
        matrix screen refuses first — the real rule, not a hardcoded cap.
        (The release switch reports any screen failure as
        platform:screen-failed.)"""
        node, d, registry = self._node()
        scope = self._green_item(node, registry, caption="x" * 5000)
        out = node.publish_to_telegram(
            scope, idem_key="k1", dry_run=False, confirmed_twice=True)
        self.assertFalse(out["ok"])
        self.assertEqual(out["rule"], "platform:screen-failed")

    def test_no_channel_configured(self):
        node, d, registry = self._node()
        node._telegram_channel_id = ""
        scope = self._green_item(node, registry)
        out = node.publish_to_telegram(
            scope, idem_key="k1", dry_run=False, confirmed_twice=True)
        self.assertFalse(out["ok"])
        self.assertEqual(out["rule"], "publish:no-channel")

    # ── P0-2: the outbox is the only exit ────────────────────────────────
    def test_no_outbox_item_is_refused(self):
        """There is no send without an outbox item — the P0-2 fix."""
        node, d, registry = self._node()
        scope = registry.scope("studio")
        out = node.publish_to_telegram(
            scope, idem_key="ghost", dry_run=False, confirmed_twice=True)
        self.assertFalse(out["ok"])
        self.assertEqual(out["rule"], "outbox:not-approved-manual")

    def test_item_still_pending_is_refused(self):
        """Approval must have happened; a pending item cannot be sent."""
        from ofn.kernel.domain import RiskTier
        node, d, registry = self._node()
        scope = registry.scope("studio")
        node.outbox.enqueue(scope, "k1", "studio:publish",
                            {"caption": "x", "draft_id": "d1"},
                            RiskTier.RED, "2026-08-10T12:00:00Z")
        out = node.publish_to_telegram(
            scope, idem_key="k1", dry_run=False, confirmed_twice=True)
        self.assertFalse(out["ok"])
        self.assertEqual(out["rule"], "outbox:not-approved-manual")

    def test_already_sent_item_cannot_be_sent_again(self):
        """A completed item is refused: at-most-once by construction."""
        from ofn.kernel.domain import RiskTier
        node, d, registry = self._node()
        scope = registry.scope("studio")
        node.outbox.enqueue(scope, "k1", "studio:publish",
                            {"caption": "x", "draft_id": "d1"},
                            RiskTier.RED, "2026-08-10T12:00:00Z")
        node.outbox.complete_manual(
            scope, "k1", "2026-08-10T13:00:00Z",
            completed_by="owner", channel="telegram")
        out = node.publish_to_telegram(
            scope, idem_key="k1", dry_run=False, confirmed_twice=True)
        self.assertFalse(out["ok"])
        self.assertEqual(out["rule"], "outbox:not-approved-manual")

    # ── P0-3: real release checks, nothing hardcoded True ────────────────
    def test_no_consent_store_blocks(self):
        node, d, registry = self._node(wire_consent=False, wire_studio=False)
        scope = registry.scope("studio")
        node.outbox.enqueue(scope, "k1", "studio:publish",
                            {"caption": "x", "draft_id": "d1"},
                            RiskTier.RED,
                            "2026-08-10T12:00:00Z")
        node.outbox.approve_manual(scope, "k1",
                                   "2026-08-10T12:00:00Z", approved_by="owner")
        out = node.publish_to_telegram(
            scope, idem_key="k1", dry_run=False, confirmed_twice=True)
        self.assertFalse(out["ok"])
        self.assertNotEqual(out["rule"], "release:ok")
        self.assertIn(out["rule"],
                      ("consent:invalid-or-missing",
                       "advisor:restricted-never-leaves"))

    def test_unconsented_subject_blocks(self):
        """Consent exists but nobody is cleared → refuse (real consent)."""
        node, d, registry = self._node()
        scope = self._green_item(node, registry)
        # Revoke the only release: consent is now broken.
        node.consent.revoke("r1", now_epoch_s=self.NOW)
        out = node.publish_to_telegram(
            scope, idem_key="k1", dry_run=False, confirmed_twice=True)
        self.assertFalse(out["ok"])
        self.assertEqual(out["rule"], "consent:invalid-or-missing")

    def test_restricted_content_never_leaves(self):
        """Restricted collection → advisor:restricted-never-leaves, even
        with everything else green."""
        node, d, registry = self._node()
        scope = registry.scope("studio")
        if node.studio is not None:
            node.studio.add_collection("studio", "coll-r", "خصوصی",
                                       sensitivity="restricted",
                                       now_epoch_s=self.NOW)
            node.studio.add_draft("studio", "d1", collection_id="coll-r",
                                  caption="x", now_epoch_s=self.NOW)
        if node.consent is not None:
            node.consent.add_subject("studio", "s1", "خودم",
                                     now_epoch_s=self.NOW)
            node.consent.record_release(
                "r1", "s1", scope="telegram_channel",
                signed_at=self.NOW - 86_400, document_ref="box",
                document_sha256="0" * 64, recorded_by="ari")
            node.consent.add_to_draft("d1", "s1", added_by="saba",
                                      now_epoch_s=self.NOW)
        node.outbox.enqueue(scope, "k1", "studio:publish",
                            {"caption": "x", "draft_id": "d1"},
                            RiskTier.RED,
                            "2026-08-10T12:00:00Z")
        node.outbox.approve_manual(scope, "k1",
                                   "2026-08-10T12:00:00Z", approved_by="owner")
        out = node.publish_to_telegram(
            scope, idem_key="k1", dry_run=False, confirmed_twice=True)
        self.assertFalse(out["ok"])
        self.assertEqual(out["rule"], "advisor:restricted-never-leaves")

    def test_caption_is_taken_from_the_item_not_the_caller(self):
        """The caller cannot inject text: the item's payload is the only
        caption that can be sent."""
        import inspect
        from ofn.node import Node
        node, d, registry = self._node()
        self._green_item(node, registry, caption="متن واقعی آیتم")
        scope = registry.scope("studio")
        # Structural: the method no longer ACCEPTS a caption. The send is
        # bound to the outbox item, so there is nothing to inject.
        params = inspect.signature(Node.publish_to_telegram).parameters
        self.assertNotIn("caption", params)
        out = node.publish_to_telegram(
            scope, idem_key="k1", dry_run=True, confirmed_twice=True)
        self.assertTrue(out["ok"])


class TestSetTelegramChannel(unittest.TestCase):
    """O11: channel id is set by the owner; publish then works in dry-run."""

    def _node(self):
        import os
        from ofn.adapters.consent_store import ConsentStore
        from ofn.adapters.facts import FactStore
        from ofn.adapters.ledger import Ledger
        from ofn.adapters.outbox import Outbox
        from ofn.adapters.studio_store import StudioStore
        from ofn.kernel.callbudget import CallBudget
        from ofn.kernel.domain import PackSpec, TenantId
        from ofn.kernel.quota import NodeQuota
        from ofn.kernel.tenancy import TenantRegistry
        from ofn.node import Node
        from tests.tmpdir import temp_dir
        d = temp_dir(self)
        registry = TenantRegistry({
            "studio": PackSpec(tenant=TenantId("studio"),
                               capacity_units_per_week=5, quota_share=1.0)})
        node = Node(
            registry=registry,
            quota=NodeQuota(estimated_capacity_tokens=1_000_000,
                            utilisation=1.0, shares={"studio": 1.0}),
            ledger=Ledger(os.path.join(d, "l.sqlite")),
            facts=FactStore(os.path.join(d, "f.sqlite")),
            outbox=Outbox(os.path.join(d, "o.sqlite")),
            studio=StudioStore(os.path.join(d, "s.sqlite")),
            consent=ConsentStore(os.path.join(d, "c.sqlite")),
            now_epoch_s=lambda: 1_785_000_000,
            now_iso=lambda: "2026-08-10T12:00:00Z",
            _telegram_token="t:test",
        )
        node.call_budget = CallBudget()
        self.addCleanup(node.close)
        return node, registry

    def _green_item(self, node, registry, *, idem="k1", caption="متن"):
        from ofn.kernel.domain import RiskTier
        scope = registry.scope("studio")
        node.studio.add_collection("studio", "coll-1", "عمومی",
                                   sensitivity="general",
                                   now_epoch_s=1_785_000_000)
        node.studio.add_draft("studio", "d1", collection_id="coll-1",
                              caption=caption, now_epoch_s=1_785_000_000)
        node.consent.add_subject("studio", "s1", "خودم",
                                 now_epoch_s=1_785_000_000)
        node.consent.record_release(
            "r1", "s1", scope="telegram_channel",
            signed_at=1_785_000_000 - 86_400, document_ref="box",
            document_sha256="0" * 64, recorded_by="ari")
        node.consent.add_to_draft("d1", "s1", added_by="saba",
                                  now_epoch_s=1_785_000_000)
        node.outbox.enqueue(scope, idem, "studio:publish",
                            {"draft_id": "d1", "platform": "telegram_channel",
                             "caption": caption, "framing": "community",
                             "adult_label": False},
                            RiskTier.RED, "2026-08-10T12:00:00Z")
        node.outbox.approve_manual(scope, idem, "2026-08-10T12:00:00Z",
                                   approved_by="owner")
        return scope

    def test_set_then_dry_run_works(self):
        node, registry = self._node()
        out = node.set_telegram_channel("@testchannel")
        self.assertTrue(out["ok"])
        scope = self._green_item(node, registry)
        r = node.publish_to_telegram(
            scope, idem_key="k1", dry_run=True, confirmed_twice=True)
        self.assertTrue(r["ok"])
        self.assertEqual(r["rule"], "adapter:dry-run")

    def test_empty_channel_refused(self):
        node, _ = self._node()
        out = node.set_telegram_channel("   ")
        self.assertFalse(out["ok"])

    def test_http_route_owner_only(self):
        import json as _j
        from ofn.adapters.http_api import ApiApp, HostMap
        from ofn.kernel.auth import issue_session
        node, registry = self._node()
        app = ApiApp(
            registry,
            HostMap(tenants={"s.test": "studio"}, owner_host="panel.test"),
            bot_tokens={}, session_secret="sec",
            owner_user_ids=("1",), partner_user_ids={},
            now=lambda: 1_785_000_000,
            set_telegram_channel=node.set_telegram_channel,
        )
        # Anonymous → 401
        resp = app.handle("POST", "/api/v1/owner/telegram/channel",
                          {"host": "panel.test"}, b"{}")
        self.assertEqual(resp.status, 401)
        # Owner → 200
        s = issue_session("owner", "1", "sec", now_epoch_s=1_785_000_000)
        resp = app.handle(
            "POST", "/api/v1/owner/telegram/channel",
            {"host": "panel.test", "authorization": "Bearer " + s},
            _j.dumps({"channel_id": "@x"}).encode())
        self.assertEqual(resp.status, 200)
        self.assertTrue(resp.body.get("ok"))

    def test_invite_link_refused(self):
        node, _ = self._node()
        out = node.set_telegram_channel("t.me/+1XvvqhnRSe81ZjZl")
        self.assertFalse(out["ok"])
        self.assertEqual(out["rule"], "telegram:invite-link-not-usable")
        # A public @username or numeric id is accepted.
        out = node.set_telegram_channel("@giftmesh")
        self.assertTrue(out["ok"])
        out = node.set_telegram_channel("-1001234567890")
        self.assertTrue(out["ok"])
