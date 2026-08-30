"""Phase I — open P2 findings (17, 19, 36) with Python-side fixes.

- finding 17: shell/boot route is throttled (10 per 60s, stage coalescing)
- finding 19: lead LIKE search escapes % _ \\ server-side
- finding 36: .part files older than the sweep age are removed
"""

from __future__ import annotations

import os
import time
import unittest

from ofn.adapters.lead_store import LeadStore
from ofn.adapters.media import MediaStore
from ofn.adapters.http_api import ApiApp, HostMap
from ofn.kernel.domain import PackSpec, TenantId
from ofn.kernel.tenancy import TenantRegistry

from tests.tmpdir import temp_dir

NOW = 1_785_000_000
NOW_ISO = "2026-08-10T12:00:00"


class TestShellBootThrottle(unittest.TestCase):
    """Finding 17: the public boot route must not amplify log volume."""

    def setUp(self):
        self.dir = temp_dir(self)
        registry = TenantRegistry({
            "studio": PackSpec(tenant=TenantId("studio"),
                               capacity_units_per_week=5, quota_share=1.0),
        })
        # A mutable clock: each request advances 1s so coalescing (same
        # stage within 10s) never swallows distinct requests, and the window
        # cap (10 per 60s) is what gets tested.
        self._clock = [NOW]
        self.app = ApiApp(
            registry,
            HostMap(tenants={"st.test": "studio"}, owner_host="panel.test"),
            bot_tokens={"studio": "t"},
            session_secret="s",
            owner_user_ids=("1",),
            partner_user_ids={"studio": ("2",)},
            now=lambda: self._clock[0],
        )
        self._boot_body = b'{"stage": "no-shell", "detail": "x"}'

    def _hit(self, n: int):
        out = []
        for i in range(n):
            self._clock[0] = NOW + i * 3   # 3s apart — past the 10s coalesce
            resp = self.app.handle("POST", "/api/v1/shell/boot",
                                   {"host": "st.test"}, self._boot_body)
            out.append(resp.body)
        return out

    def test_repeated_stages_are_coalesced(self):
        # Same stage at the same instant: first logs, the rest coalesce.
        self._clock[0] = NOW
        bodies = []
        for _ in range(5):
            bodies.append(self.app.handle(
                "POST", "/api/v1/shell/boot",
                {"host": "st.test"}, self._boot_body).body)
        logged = [b for b in bodies if not b.get("coalesced")
                  and not b.get("throttled")]
        self.assertEqual(len(logged), 1)
        self.assertTrue(bodies[1].get("coalesced"))

    def test_burst_over_10_is_throttled(self):
        # 20 distinct valid stages, 3s apart: coalescing never applies,
        # so the window cap (10 logs per 60s) is what gets tested.
        stages = ["opened", "no-shell", "no-sdk", "no-initdata", "rejected",
                  "not-allowed", "unreachable", "error", "threw", "live",
                  "opened", "no-shell", "no-sdk", "no-initdata", "rejected",
                  "not-allowed", "unreachable", "error", "threw", "live"]
        bodies = []
        for i, stage in enumerate(stages):
            self._clock[0] = NOW + i * 3
            resp = self.app.handle(
                "POST", "/api/v1/shell/boot", {"host": "st.test"},
                ('{"stage": "%s", "detail": "x"}' % stage).encode())
            bodies.append(resp.body)
        throttled = [b for b in bodies if b.get("throttled")]
        self.assertTrue(throttled, "burst should be throttled")
        passed = [b for b in bodies if not b.get("throttled")]
        self.assertLessEqual(len(passed), 10)


class TestLeadLikeEscape(unittest.TestCase):
    """Finding 19: % and _ in a lead query are literal, not wildcards."""

    def setUp(self):
        self.dir = temp_dir(self)
        self.store = LeadStore(os.path.join(self.dir, "lead.sqlite"))
        self.addCleanup(self.store.close)
        # Two leads with distinct ids: source_ref differentiates them
        # (create_lead builds lead_id from source-source_ref-timestamp and
        # upserts on conflict).
        self.store.create_lead("lead", {
            "customer_name": "علی 50% تخفیف", "phone": "1", "message": "x",
            "source": "test", "source_ref": "p1",
        }, now_iso=NOW_ISO)
        self.store.create_lead("lead", {
            "customer_name": "علی معمولی", "phone": "2", "message": "x",
            "source": "test", "source_ref": "p2",
        }, now_iso=NOW_ISO)

    def test_percent_query_matches_only_literal(self):
        rows = self.store.list_leads("lead", q="50%")
        self.assertEqual(len(rows), 1)
        self.assertIn("50%", rows[0]["customer_name"])

    def test_percent_query_is_not_wildcard(self):
        # If % were a wildcard, "50%" would match everything.
        rows = self.store.list_leads("lead", q="50%")
        names = [r["customer_name"] for r in rows]
        self.assertEqual(names, ["علی 50% تخفیف"])

    def test_underscore_is_literal(self):
        self.store.create_lead("lead", {
            "customer_name": "a_b", "phone": "3", "message": "x",
            "source": "test", "source_ref": "p3",
        }, now_iso=NOW_ISO)
        self.store.create_lead("lead", {
            "customer_name": "axb", "phone": "4", "message": "x",
            "source": "test", "source_ref": "p4",
        }, now_iso=NOW_ISO)
        rows = self.store.list_leads("lead", q="a_b")
        names = [r["customer_name"] for r in rows]
        self.assertEqual(names, ["a_b"])


class TestPartSweeper(unittest.TestCase):
    """Finding 36: stale .part files are removed, fresh ones are kept."""

    def setUp(self):
        self.dir = temp_dir(self)
        self.media = MediaStore(os.path.join(self.dir, "photos"))

    def test_stale_part_removed(self):
        path = os.path.join(self.dir, "photos", "old.jpg.part")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(b"x")
        # Make it old
        old = time.time() - 7200
        os.utime(path, (old, old))
        removed = self.media.sweep_stale_parts(max_age_s=3600)
        self.assertEqual(removed, 1)
        self.assertFalse(os.path.exists(path))

    def test_fresh_part_kept(self):
        path = os.path.join(self.dir, "photos", "new.jpg.part")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(b"x")
        removed = self.media.sweep_stale_parts(max_age_s=3600)
        self.assertEqual(removed, 0)
        self.assertTrue(os.path.exists(path))

    def test_real_files_never_touched(self):
        real = os.path.join(self.dir, "photos", "pic.jpg")
        os.makedirs(os.path.dirname(real), exist_ok=True)
        with open(real, "wb") as fh:
            fh.write(b"x")
        old = time.time() - 7200
        os.utime(real, (old, old))
        removed = self.media.sweep_stale_parts(max_age_s=3600)
        self.assertEqual(removed, 0)
        self.assertTrue(os.path.exists(real))


if __name__ == "__main__":
    unittest.main()
