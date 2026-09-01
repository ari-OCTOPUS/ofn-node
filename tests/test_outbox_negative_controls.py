"""Outbox negative controls (S6-D12) — the guard_target lesson, applied.

The outbox state machine was already two-phase and idempotent; what it
lacked was proof of the REFUSED directions. These tests pin every refusal
path so a future regression cannot hide behind "the happy path is green".
"""
from __future__ import annotations

import os
import tempfile
import threading
import unittest

from ofn.adapters.outbox import (APPROVED_MANUAL, COMPLETED, HELD,
                                 IN_FLIGHT, PENDING, REJECTED, SENT, Outbox)
from ofn.kernel.domain import RiskTier, TenantId
from ofn.kernel.tenancy import TenantRegistry, TenantScope

T0 = "2026-09-01T00:00:00Z"
T1 = "2026-09-01T00:01:00Z"
T2 = "2026-09-01T00:02:00Z"


class Case(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.addCleanup(self._d.cleanup)
        self.path = os.path.join(self._d.name, "o.sqlite")
        self.ob = Outbox(self.path)
        self.addCleanup(self.ob.close)
        self.scope = TenantScope(TenantId("lead"))

    def q(self, key="k1", tier=RiskTier.YELLOW):
        self.ob.enqueue(self.scope, key, "email", {"t": "x"}, tier, T0)


class TestNegativeControls(Case):
    def test_mark_sent_from_pending_is_refused(self):
        """The two-phase contract: only a CLAIMED row may be marked sent."""
        self.q()
        self.ob.mark_sent(self.scope, "k1", T1)   # must NOT take effect
        item = self.ob.get(self.scope, "k1")
        self.assertNotEqual(item.status, "sent")
        self.assertEqual(item.status, "pending")

    def test_double_claim_second_is_refused(self):
        self.q()
        self.assertTrue(self.ob.claim(self.scope, "k1", T1))
        self.assertFalse(self.ob.claim(self.scope, "k1", T1))

    def test_complete_manual_on_rejected_is_refused(self):
        self.q(tier=RiskTier.RED)
        self.ob.approve_manual(self.scope, "k1", T1, approved_by="o")
        self.ob.reject(self.scope, "k1", T1, note="no")
        self.ob.complete_manual(self.scope, "k1", "2026-09-01T00:02:00Z",
                                completed_by="o", channel="telegram")
        item = self.ob.get(self.scope, "k1")
        self.assertEqual(item.status, "rejected")

    def test_reject_after_sent_is_refused(self):
        self.q()
        self.ob.claim(self.scope, "k1", T1)
        self.ob.mark_sent(self.scope, "k1", T1)
        self.ob.reject(self.scope, "k1", T1, note="late")
        item = self.ob.get(self.scope, "k1")
        self.assertEqual(item.status, "sent")

    def test_duplicate_enqueue_single_row(self):
        self.q()
        self.assertFalse(self.ob.enqueue(
            self.scope, "k1", "email", {"t": "y"}, RiskTier.YELLOW, T1))
        self.assertEqual(self.ob.counts(self.scope)["pending"], 1)

    def test_same_key_two_tenants_coexist(self):
        """The composite key: identical raw keys under different tenants
        are two rows, not a collision (the a:b:c prefix bug is gone)."""
        other = TenantScope(TenantId("studio"))
        self.q()
        self.ob.enqueue(other, "k1", "email", {}, RiskTier.YELLOW, T0)
        self.assertEqual(self.ob.counts(self.scope)["pending"], 1)
        self.assertEqual(self.ob.counts(other)["pending"], 1)

    def test_prefix_collision_class_is_impossible_now(self):
        """The collision the string composition allowed (tenant a + key b:c
        vs tenant a:b + key c) is closed at TWO layers: the domain refuses
        ':' in a TenantId, and the composite PK stores raw keys so no
        composition exists to collide."""
        with self.assertRaises(ValueError):
            TenantId("a:b")            # domain guard: ':' is illegal
        a = TenantScope(TenantId("a"))
        self.ob.enqueue(a, "b:c", "email", {}, RiskTier.YELLOW, T0)
        item = self.ob.get(a, "b:c")
        self.assertEqual(item.idem_key, "b:c")  # stored raw, not "a:b:c"

    def test_stale_inflight_defaults_to_held_no_resend(self):
        """Crash recovery is fail-closed: resend=False keeps HELD, it never
        re-sends an item whose delivery state is unknown."""
        self.q()
        self.ob.claim(self.scope, "k1", T1)
        self.ob.recover_stale("2026-09-01T09:00:00Z")  # hours later
        item = self.ob.get(self.scope, "k1")
        self.assertEqual(item.status, "held")

    def test_empty_key_is_refused(self):
        with self.assertRaises(Exception):
            self.ob.enqueue(self.scope, "", "email", {}, RiskTier.YELLOW, T0)

    def test_legacy_prefixed_file_migrates_to_raw(self):
        """Old files (single PK, prefixed keys) rebuild onto the composite
        key with prefixes stripped; idempotent on second open."""
        import sqlite3
        path = os.path.join(self._d.name, "legacy.sqlite")
        conn = sqlite3.connect(path)
        conn.execute(
            "CREATE TABLE outbox (idem_key TEXT PRIMARY KEY, tenant TEXT,"
            " kind TEXT, payload TEXT, tier TEXT, status TEXT,"
            " attempts INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT,"
            " note TEXT DEFAULT '')")
        conn.execute(
            "INSERT INTO outbox VALUES ('lead:old1', 'lead', 'email', '{}',"
            " 'yellow', 'pending', 0, 't0', 't0', '')")
        conn.commit(); conn.close()
        ob = Outbox(path)
        self.addCleanup(ob.close)
        item = ob.get(self.scope, "lead:old1")
        self.assertIsNotNone(item)
        pk = [r[1] for r in ob._conn.execute("PRAGMA table_info(outbox)")
              if r[5] > 0]
        self.assertEqual(pk, ["tenant", "idem_key"])


if __name__ == "__main__":
    unittest.main()


class TestFinalStatusV2Item1(Case):
    """The five named refusal directions. Happy path is not rewritten here.

    Each test is a negative: if the matching WHERE/default/from_status
    guard is deleted, the assertion goes red.
    """

    def test_1_mark_sent_from_pending_must_fail(self):
        """mark_sent from PENDING must FAIL (not succeed)."""
        self.q()
        self.ob.mark_sent(self.scope, "k1", T1)
        item = self.ob.get(self.scope, "k1")
        self.assertEqual(item.status, PENDING)
        self.assertNotEqual(item.status, SENT)
        self.assertEqual(item.updated_at, T0)  # zero rows written
        self.assertEqual(len(self.ob.pending(self.scope)), 1)

    def test_2_complete_manual_on_rejected_is_refused(self):
        """complete_manual on REJECTED must be rejected."""
        self.q(tier=RiskTier.RED)
        self.assertTrue(self.ob.approve_manual(
            self.scope, "k1", T1, approved_by="o"))
        self.assertTrue(self.ob.reject(self.scope, "k1", T1, note="no"))
        ok = self.ob.complete_manual(
            self.scope, "k1", T2, completed_by="o", channel="telegram")
        self.assertFalse(ok)
        item = self.ob.get(self.scope, "k1")
        self.assertEqual(item.status, REJECTED)

    def test_3_concurrent_claim_exactly_one_winner(self):
        """concurrent claim() on the same idem_key: exactly one winner."""
        self.q()
        barrier = threading.Barrier(2)
        results: list[bool] = []
        errors: list[BaseException] = []

        def go():
            other = Outbox(self.path)
            try:
                barrier.wait()
                results.append(other.claim(self.scope, "k1", T1))
            except BaseException as exc:
                errors.append(exc)
            finally:
                other.close()

        threads = [threading.Thread(target=go) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(errors, [])
        self.assertEqual(sorted(results), [False, True])
        item = self.ob.get(self.scope, "k1")
        self.assertEqual(item.status, IN_FLIGHT)
        self.assertEqual(item.attempts, 1)

    def test_4_reject_on_sent_and_completed_leaves_them_immutable(self):
        """reject() on SENT/COMPLETED must leave them immutable."""
        self.q("sent-key")
        self.assertTrue(self.ob.claim(self.scope, "sent-key", T1))
        self.ob.mark_sent(self.scope, "sent-key", T1)
        self.assertFalse(self.ob.reject(self.scope, "sent-key", T2, note="late"))
        self.assertEqual(self.ob.get(self.scope, "sent-key").status, SENT)

        self.q("done-key", tier=RiskTier.RED)
        self.assertTrue(self.ob.approve_manual(
            self.scope, "done-key", T1, approved_by="o"))
        self.assertTrue(self.ob.complete_manual(
            self.scope, "done-key", T1, completed_by="o", channel="sms"))
        self.assertFalse(self.ob.reject(self.scope, "done-key", T2, note="late"))
        self.assertEqual(self.ob.get(self.scope, "done-key").status, COMPLETED)

    def test_5_restart_must_not_silently_send_held(self):
        """Restart must NOT silently send a HELD item (do-not-resend default)."""
        self.q()
        self.assertTrue(self.ob.claim(self.scope, "k1", T1))
        self.ob.recover_stale("2026-09-01T09:00:00Z")
        self.assertEqual(self.ob.get(self.scope, "k1").status, HELD)
        # Second recover = process restart. HELD is not IN_FLIGHT, so it
        # must stay HELD; pending() is what a sender would drain.
        moved = self.ob.recover_stale("2026-09-01T10:00:00Z")
        self.assertEqual(moved, 0)
        item = self.ob.get(self.scope, "k1")
        self.assertEqual(item.status, HELD)
        self.assertEqual(list(self.ob.pending(self.scope)), [])
        self.assertEqual(len(self.ob.held(self.scope)), 1)
