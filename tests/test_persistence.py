"""Persistence layer: chain tamper detection, bi-temporal reads, and the
power-cut scenario the whole outbox design exists for.
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest

from ofn.adapters.facts import FactStore
from ofn.adapters.ledger import GENESIS, Ledger
from ofn.adapters.outbox import HELD, IN_FLIGHT, PENDING, SENT, Outbox
from ofn.adapters.sqlite_base import connect, integrity_ok
from ofn.kernel.domain import Confidence, RiskTier, TenantId
from ofn.kernel.tenancy import TenantScope

A = TenantScope(TenantId("alpha"))
B = TenantScope(TenantId("bravo"))
T0 = "2026-08-03T10:00:00Z"
T1 = "2026-08-03T11:00:00Z"
T2 = "2026-08-03T12:00:00Z"


class Tmp(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self._dir.name, "db.sqlite")

    def tearDown(self):
        self._dir.cleanup()


class TestDurabilityPragmas(Tmp):
    def test_wal_and_full_sync_are_set(self):
        conn = connect(self.path)
        self.assertEqual(conn.execute("PRAGMA journal_mode").fetchone()[0].lower(),
                         "wal")
        # synchronous: 2 == FULL. NORMAL (1) would trade away durability.
        self.assertEqual(conn.execute("PRAGMA synchronous").fetchone()[0], 2)
        conn.close()

    def test_integrity_check_passes_on_fresh_db(self):
        conn = connect(self.path)
        conn.execute("CREATE TABLE t (x INTEGER)")
        self.assertTrue(integrity_ok(conn))
        conn.close()


class TestLedgerChain(Tmp):
    def test_first_event_links_to_genesis(self):
        led = Ledger(self.path)
        e = led.append(A, "NOTE", {"a": 1}, T0)
        self.assertEqual(e.seq, 1)
        self.assertEqual(e.prev_hash, GENESIS)
        led.close()

    def test_chain_links_forward(self):
        led = Ledger(self.path)
        e1 = led.append(A, "NOTE", {"a": 1}, T0)
        e2 = led.append(A, "NOTE", {"a": 2}, T1)
        self.assertEqual(e2.prev_hash, e1.hash)
        self.assertEqual(e2.seq, 2)
        led.close()

    def test_verify_passes_on_untouched_chain(self):
        led = Ledger(self.path)
        for i in range(25):
            led.append(A, "BEAT", {"i": i}, T0)
        ok, why = led.verify(A)
        self.assertTrue(ok, why)
        self.assertIn("25", why)
        led.close()

    def test_editing_a_payload_is_detected(self):
        """The headline property: a direct edit in sqlite3 is caught."""
        led = Ledger(self.path)
        for i in range(5):
            led.append(A, "NOTE", {"i": i}, T0)
        led.close()

        raw = sqlite3.connect(self.path)
        raw.execute("UPDATE ledger SET payload = ? WHERE seq = 3",
                    ('{"i":999}',))
        raw.commit()
        raw.close()

        led = Ledger(self.path)
        ok, why = led.verify(A)
        self.assertFalse(ok)
        self.assertIn("seq 3", why)
        led.close()

    def test_deleting_an_event_is_detected(self):
        led = Ledger(self.path)
        for i in range(5):
            led.append(A, "NOTE", {"i": i}, T0)
        led.close()

        raw = sqlite3.connect(self.path)
        raw.execute("DELETE FROM ledger WHERE seq = 3")
        raw.commit()
        raw.close()

        led = Ledger(self.path)
        ok, why = led.verify(A)
        self.assertFalse(ok)
        self.assertIn("gap", why)
        led.close()

    def test_reordering_is_detected(self):
        led = Ledger(self.path)
        for i in range(4):
            led.append(A, "NOTE", {"i": i}, T0)
        led.close()
        raw = sqlite3.connect(self.path)
        raw.execute("UPDATE ledger SET ts = ? WHERE seq = 2", ("1999-01-01T00:00:00Z",))
        raw.commit()
        raw.close()
        led = Ledger(self.path)
        ok, _ = led.verify(A)
        self.assertFalse(ok)
        led.close()

    def test_event_cannot_be_lifted_between_tenants(self):
        """tenant and seq are inside the digest, so a row copied from one
        chain into another does not verify."""
        led = Ledger(self.path)
        led.append(A, "NOTE", {"secret": 1}, T0)
        led.close()
        raw = sqlite3.connect(self.path)
        raw.execute("UPDATE ledger SET tenant = 'bravo' WHERE seq = 1")
        raw.commit()
        raw.close()
        led = Ledger(self.path)
        ok, _ = led.verify(B)
        self.assertFalse(ok)
        led.close()

    def test_chains_are_per_tenant_and_independent(self):
        led = Ledger(self.path)
        led.append(A, "NOTE", {"x": 1}, T0)
        led.append(B, "NOTE", {"x": 1}, T0)
        led.append(A, "NOTE", {"x": 2}, T1)
        self.assertEqual(led.count(A), 2)
        self.assertEqual(led.count(B), 1)
        self.assertEqual(led.head(B).seq, 1)
        self.assertTrue(led.verify(A)[0])
        self.assertTrue(led.verify(B)[0])
        led.close()

    def test_tenant_reads_only_its_own_events(self):
        led = Ledger(self.path)
        led.append(A, "NOTE", {"owner": "alpha"}, T0)
        led.append(B, "NOTE", {"owner": "bravo"}, T0)
        for e in led.read(A):
            self.assertEqual(e.tenant, "alpha")
        self.assertEqual(len(led.read(B)), 1)
        led.close()

    def test_survives_reopen(self):
        led = Ledger(self.path)
        led.append(A, "NOTE", {"a": 1}, T0)
        led.close()
        led = Ledger(self.path)
        led.append(A, "NOTE", {"a": 2}, T1)
        ok, _ = led.verify(A)
        self.assertTrue(ok)
        self.assertEqual(led.count(A), 2)
        led.close()


class TestBiTemporalFacts(Tmp):
    def test_supersede_not_overwrite(self):
        fs = FactStore(self.path)
        fs.assert_fact(A, "production", "capacity", 30, Confidence.GUESSED,
                       observed_at=T0)
        fs.assert_fact(A, "production", "capacity", 6, Confidence.OWNER_CONFIRMED,
                       observed_at=T1)
        cur = fs.current(A, "production", "capacity")
        self.assertEqual(cur.value, 6)
        self.assertIs(cur.confidence, Confidence.OWNER_CONFIRMED)
        hist = fs.history(A, "production", "capacity")
        self.assertEqual(len(hist), 2)
        self.assertEqual(hist[0].value, 30)
        self.assertIsNotNone(hist[0].valid_to)      # closed, not deleted
        self.assertEqual(hist[0].superseded_by, hist[1].id)
        fs.close()

    def test_exactly_one_active_row_per_key(self):
        fs = FactStore(self.path)
        for i in range(6):
            fs.assert_fact(A, "s", "p", i, Confidence.MEASURED, observed_at=T0)
        active = [f for f in fs.history(A, "s", "p") if f.active]
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].value, 5)
        fs.close()

    def test_as_of_returns_the_old_belief(self):
        """The bi-temporal question: what did we think last Tuesday?"""
        fs = FactStore(self.path)
        fs.assert_fact(A, "production", "capacity", 30, Confidence.GUESSED,
                       observed_at=T0)
        fs.assert_fact(A, "production", "capacity", 6, Confidence.OWNER_CONFIRMED,
                       observed_at=T2)
        self.assertEqual(fs.as_of(A, "production", "capacity", T1).value, 30)
        self.assertEqual(fs.as_of(A, "production", "capacity", T2).value, 6)
        self.assertIsNone(fs.as_of(A, "production", "capacity",
                                   "2020-01-01T00:00:00Z"))
        fs.close()

    def test_facts_are_tenant_scoped(self):
        fs = FactStore(self.path)
        fs.assert_fact(A, "s", "p", "alpha-value", Confidence.MEASURED,
                       observed_at=T0)
        self.assertIsNone(fs.current(B, "s", "p"))
        fs.assert_fact(B, "s", "p", "bravo-value", Confidence.MEASURED,
                       observed_at=T0)
        self.assertEqual(fs.current(A, "s", "p").value, "alpha-value")
        self.assertEqual(fs.current(B, "s", "p").value, "bravo-value")
        fs.close()

    def test_evidence_map_matches_gate_input_shape(self):
        fs = FactStore(self.path)
        fs.assert_fact(A, "offer", "cogs", 12, Confidence.OWNER_CONFIRMED,
                       observed_at=T0)
        ev = fs.evidence(A, ["offer.cogs", "offer.missing"])
        self.assertEqual(ev, {"offer.cogs": Confidence.OWNER_CONFIRMED})
        self.assertNotIn("offer.missing", ev)   # absence != weakness
        fs.close()

    def test_forget_is_a_separate_explicit_act(self):
        fs = FactStore(self.path)
        fs.assert_fact(A, "person", "detail", "x", Confidence.MEASURED,
                       observed_at=T0)
        fs.assert_fact(A, "person", "detail", "y", Confidence.MEASURED,
                       observed_at=T1)
        self.assertEqual(fs.forget(A, "person", "detail"), 2)
        self.assertEqual(len(fs.history(A, "person", "detail")), 0)
        fs.close()

    def test_survives_reopen(self):
        fs = FactStore(self.path)
        fs.assert_fact(A, "s", "p", 42, Confidence.OWNER_CONFIRMED, observed_at=T0)
        fs.close()
        fs = FactStore(self.path)
        self.assertEqual(fs.current(A, "s", "p").value, 42)
        fs.close()


class TestOutboxIdempotency(Tmp):
    def test_duplicate_key_is_a_noop(self):
        ob = Outbox(self.path)
        self.assertTrue(ob.enqueue(A, "k1", "email", {"to": "x"},
                                   RiskTier.YELLOW, T0))
        self.assertFalse(ob.enqueue(A, "k1", "email", {"to": "x"},
                                    RiskTier.YELLOW, T1))
        self.assertEqual(len(ob.pending(A)), 1)
        ob.close()

    def test_same_key_in_two_tenants_is_two_items(self):
        ob = Outbox(self.path)
        self.assertTrue(ob.enqueue(A, "k1", "email", {}, RiskTier.YELLOW, T0))
        self.assertTrue(ob.enqueue(B, "k1", "email", {}, RiskTier.YELLOW, T0))
        self.assertEqual(len(ob.pending(A)), 1)
        self.assertEqual(len(ob.pending(B)), 1)
        ob.close()

    def test_claim_is_exclusive(self):
        ob = Outbox(self.path)
        ob.enqueue(A, "k1", "email", {}, RiskTier.YELLOW, T0)
        self.assertTrue(ob.claim(A, "k1", T1))
        self.assertFalse(ob.claim(A, "k1", T1))   # second sender loses
        self.assertEqual(ob.get(A, "k1").attempts, 1)
        ob.close()

    def test_claimed_item_leaves_the_pending_queue(self):
        ob = Outbox(self.path)
        ob.enqueue(A, "k1", "email", {}, RiskTier.YELLOW, T0)
        ob.claim(A, "k1", T1)
        self.assertEqual(len(ob.pending(A)), 0)
        ob.close()

    def test_pending_is_tenant_scoped(self):
        ob = Outbox(self.path)
        ob.enqueue(A, "k1", "email", {}, RiskTier.YELLOW, T0)
        self.assertEqual(len(ob.pending(B)), 0)
        ob.close()


class TestPowerCut(Tmp):
    """The scenario the design exists for: unplugged mid-send."""

    def _crash_after_claim(self) -> None:
        ob = Outbox(self.path)
        ob.enqueue(A, "quote-1", "email", {"to": "customer"},
                   RiskTier.RED, T0)
        ob.claim(A, "quote-1", T0)      # in flight...
        ob.close()                      # ...and the lights go out

    def test_in_flight_item_is_held_not_resent(self):
        self._crash_after_claim()
        ob = Outbox(self.path)          # reboot
        self.assertEqual(ob.get(A, "quote-1").status, IN_FLIGHT)
        moved = ob.recover_stale(T1)
        self.assertEqual(moved, 1)
        item = ob.get(A, "quote-1")
        self.assertEqual(item.status, HELD)
        self.assertIn("unknown", item.note)
        # crucially: it is NOT in the pending queue, so nothing resends it
        self.assertEqual(len(ob.pending(A)), 0)
        self.assertEqual(len(ob.held(A)), 1)
        ob.close()

    def test_opt_in_resend_requeues(self):
        self._crash_after_claim()
        ob = Outbox(self.path)
        ob.recover_stale(T1, resend=True)
        self.assertEqual(ob.get(A, "quote-1").status, PENDING)
        self.assertEqual(len(ob.pending(A)), 1)
        ob.close()

    def test_sent_items_are_untouched_by_recovery(self):
        ob = Outbox(self.path)
        ob.enqueue(A, "k1", "email", {}, RiskTier.YELLOW, T0)
        ob.claim(A, "k1", T0)
        ob.mark_sent(A, "k1", T0)
        ob.close()
        ob = Outbox(self.path)
        ob.recover_stale(T1)
        self.assertEqual(ob.get(A, "k1").status, SENT)
        ob.close()

    def test_no_duplicate_after_reboot_and_replay(self):
        """End to end: enqueue, crash, reboot, and the same logical action
        cannot be queued a second time."""
        self._crash_after_claim()
        ob = Outbox(self.path)
        ob.recover_stale(T1)
        self.assertFalse(ob.enqueue(A, "quote-1", "email", {"to": "customer"},
                                    RiskTier.RED, T2))
        self.assertEqual(ob.counts(A), {HELD: 1})
        ob.close()

    def test_ledger_survives_an_abrupt_close(self):
        led = Ledger(self.path)
        for i in range(10):
            led.append(A, "BEAT", {"i": i}, T0)
        # No clean close: `led` stays open exactly as a killed process would
        # leave it, and led2 must recover from that on-disk state.
        led2 = Ledger(self.path)
        ok, why = led2.verify(A)
        self.assertTrue(ok, why)
        self.assertEqual(led2.count(A), 10)
        led2.close()
        led.close()   # handle hygiene only, after the property was proven —
                      # Windows cannot delete the tmpdir while it is open


class TestOutboxStateGuard(Tmp):
    """The outbox must enforce state transitions, not just trust callers.

    mark_sent may only succeed from IN_FLIGHT (the two-phase move). A PENDING
    item that is marked sent directly — skipping claim — is a contract
    violation that must be silently rejected (zero rows updated), not an
    unconditional overwrite.
    """

    def test_mark_sent_on_pending_is_silently_ignored(self):
        ob = Outbox(self.path)
        ob.enqueue(A, "k1", "email", {}, RiskTier.YELLOW, T0)
        # No claim() — status is still PENDING.
        ob.mark_sent(A, "k1", T0)
        # The item must still be PENDING, not SENT.
        self.assertEqual(ob.get(A, "k1").status, PENDING)
        ob.close()

    def test_mark_sent_after_claim_works(self):
        ob = Outbox(self.path)
        ob.enqueue(A, "k1", "email", {}, RiskTier.YELLOW, T0)
        ob.claim(A, "k1", T0)
        ob.mark_sent(A, "k1", T0)
        self.assertEqual(ob.get(A, "k1").status, SENT)
        ob.close()

    def test_mark_failed_on_pending_works(self):
        """owner_decide rejects by calling mark_failed on a pending item."""
        ob = Outbox(self.path)
        ob.enqueue(A, "k1", "email", {}, RiskTier.RED, T0)
        ob.mark_failed(A, "k1", T0, note="rejected")
        self.assertEqual(ob.get(A, "k1").status, "failed")
        ob.close()

    def test_mark_sent_on_sent_is_idempotent(self):
        """A second mark_sent on an already-sent item should not error."""
        ob = Outbox(self.path)
        ob.enqueue(A, "k1", "email", {}, RiskTier.YELLOW, T0)
        ob.claim(A, "k1", T0)
        ob.mark_sent(A, "k1", T0)
        # Second call: status is now SENT, not IN_FLIGHT — no update.
        ob.mark_sent(A, "k1", T0)
        self.assertEqual(ob.get(A, "k1").status, SENT)
        ob.close()


if __name__ == "__main__":
    unittest.main()
