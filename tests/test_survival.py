"""Survival: boot gating, SAFE MODE, backup verification, and the watchdog
that refuses to lie about a wedged process.
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest

from ofn.adapters.backup import (
    MANIFEST_NAME, backup, prune, restore, sha256_file, verify_backup,
)
from ofn.adapters.boot import (
    MIN_PLAUSIBLE_EPOCH, BootSupervisor, Mode, Severity, closed_gates_for,
)
from ofn.adapters.facts import FactStore
from ofn.adapters.ledger import Ledger
from ofn.adapters.outbox import HELD, Outbox
from ofn.adapters.watchdog import HealthGate, Notifier, beat, watchdog_interval_s
from ofn.kernel.domain import Confidence, RiskTier, TenantId
from ofn.kernel.tenancy import TenantScope

A = TenantScope(TenantId("alpha"))
GOOD_NOW = 1_785_000_000
T0 = "2026-08-03T10:00:00Z"


class Tmp(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.dir = self._d.name
        self.led_path = os.path.join(self.dir, "ledger.sqlite")
        self.fact_path = os.path.join(self.dir, "facts.sqlite")
        self.ob_path = os.path.join(self.dir, "outbox.sqlite")

    def tearDown(self):
        self._d.cleanup()

    def supervisor(self, now=GOOD_NOW, ram=None) -> BootSupervisor:
        return BootSupervisor(
            db_paths={"ledger": self.led_path, "facts": self.fact_path,
                      "outbox": self.ob_path},
            tenants=[TenantId("alpha")], now_epoch_s=lambda: now,
            state_dir=self.dir,
            free_ram_bytes=(lambda: ram) if ram is not None else None)


# ══ boot ════════════════════════════════════════════════════════════════
class TestBootClock(Tmp):
    def test_unsynced_clock_forces_safe_mode(self):
        """No RTC on this board: before NTP lands the clock is near-epoch, and
        every freshness and quota decision downstream would be wrong."""
        rep = self.supervisor(now=1000).run()
        self.assertIs(rep.mode, Mode.SAFE)
        self.assertTrue(any(c.name == "clock" and c.severity is Severity.CRITICAL
                            for c in rep.checks))

    def test_plausible_clock_passes(self):
        rep = self.supervisor(now=MIN_PLAUSIBLE_EPOCH + 1).run()
        self.assertTrue(any(c.name == "clock" and c.severity is Severity.OK
                            for c in rep.checks))


class TestBootDatabases(Tmp):
    def test_missing_databases_are_not_an_error(self):
        rep = self.supervisor().run()
        self.assertIs(rep.mode, Mode.NORMAL)

    def test_healthy_databases_pass_and_wal_is_folded(self):
        led = Ledger(self.led_path); led.append(A, "NOTE", {"a": 1}, T0); led.close()
        rep = self.supervisor().run()
        self.assertIs(rep.mode, Mode.NORMAL)
        self.assertTrue(any(c.name == "db:ledger" and c.severity is Severity.OK
                            for c in rep.checks))

    def test_corrupt_database_forces_safe_mode(self):
        led = Ledger(self.led_path); led.append(A, "NOTE", {"a": 1}, T0); led.close()
        with open(self.led_path, "r+b") as fh:      # scribble on the header
            fh.seek(30); fh.write(b"\xff" * 200)
        rep = self.supervisor().run()
        self.assertIs(rep.mode, Mode.SAFE)


class TestBootChain(Tmp):
    def test_edited_history_forces_safe_mode(self):
        led = Ledger(self.led_path)
        for i in range(4):
            led.append(A, "NOTE", {"i": i}, T0)
        led.close()
        raw = sqlite3.connect(self.led_path)
        raw.execute("UPDATE ledger SET payload = ? WHERE seq = 2", ('{"i":42}',))
        raw.commit(); raw.close()

        led = Ledger(self.led_path)
        rep = self.supervisor().run(ledger=led)
        led.close()
        self.assertIs(rep.mode, Mode.SAFE)
        self.assertTrue(any(c.name == "chain:alpha" and
                            c.severity is Severity.CRITICAL for c in rep.checks))

    def test_intact_chain_passes(self):
        led = Ledger(self.led_path)
        led.append(A, "NOTE", {"a": 1}, T0)
        rep = self.supervisor().run(ledger=led)
        led.close()
        self.assertIs(rep.mode, Mode.NORMAL)


class TestBootOutboxRecovery(Tmp):
    def test_interrupted_send_is_held_and_reported(self):
        ob = Outbox(self.ob_path)
        ob.enqueue(A, "q1", "email", {"to": "x"}, RiskTier.RED, T0)
        ob.claim(A, "q1", T0)
        ob.close()                                   # power cut

        ob = Outbox(self.ob_path)
        rep = self.supervisor().run(outbox=ob, now_iso=T0)
        self.assertEqual(rep.recovered_outbox, 1)
        self.assertEqual(ob.get(A, "q1").status, HELD)
        self.assertIs(rep.mode, Mode.NORMAL)         # healthy, just needs a human
        self.assertTrue(any(c.name == "outbox" and c.severity is Severity.WARN
                            for c in rep.checks))
        ob.close()

    def test_clean_shutdown_leaves_nothing_to_recover(self):
        ob = Outbox(self.ob_path)
        ob.enqueue(A, "q1", "email", {}, RiskTier.YELLOW, T0)
        rep = self.supervisor().run(outbox=ob, now_iso=T0)
        self.assertEqual(rep.recovered_outbox, 0)
        ob.close()


class TestSafeModeIsExpressedAsAClosedGate(Tmp):
    def test_safe_mode_adds_a_gate(self):
        rep = self.supervisor(now=1000).run()
        gates = closed_gates_for(rep, ["secret_rotation"])
        self.assertIn("safe_mode", gates)
        self.assertIn("secret_rotation", gates)

    def test_normal_mode_adds_nothing(self):
        rep = self.supervisor().run()
        self.assertEqual(closed_gates_for(rep, ["x"]), ("x",))

    def test_summary_is_operator_readable(self):
        self.assertIn("SAFE", self.supervisor(now=1000).run().summary())
        self.assertIn("OK", self.supervisor().run().summary())


class TestBootResources(Tmp):
    def test_low_ram_warns_but_does_not_stop_boot(self):
        rep = self.supervisor(ram=10 * 1024 * 1024).run()
        self.assertIs(rep.mode, Mode.NORMAL)
        self.assertTrue(any(c.name == "ram" and c.severity is Severity.WARN
                            for c in rep.checks))

    def test_unreadable_ram_is_only_a_warning(self):
        rep = self.supervisor(ram=-1).run()
        self.assertIs(rep.mode, Mode.NORMAL)


# ══ backup ══════════════════════════════════════════════════════════════
class TestBackup(Tmp):
    def _populate(self):
        led = Ledger(self.led_path)
        for i in range(5):
            led.append(A, "NOTE", {"i": i}, T0)
        led.close()
        fs = FactStore(self.fact_path)
        fs.assert_fact(A, "production", "capacity", 6,
                       Confidence.OWNER_CONFIRMED, observed_at=T0)
        fs.close()

    def test_backup_copies_and_verifies(self):
        self._populate()
        dest = os.path.join(self.dir, "b1")
        res = backup({"ledger": self.led_path, "facts": self.fact_path},
                     dest, stamp="20260803")
        self.assertTrue(res.ok, res.detail)
        self.assertEqual(len(res.entries), 2)
        self.assertTrue(all(e.verified for e in res.entries))
        self.assertTrue(os.path.exists(os.path.join(dest, MANIFEST_NAME)))

    def test_backup_of_a_live_database_is_consistent(self):
        """The online API must produce a usable copy while a writer holds the
        source open — the case a plain file copy gets wrong."""
        led = Ledger(self.led_path)
        led.append(A, "NOTE", {"a": 1}, T0)
        dest = os.path.join(self.dir, "b-live")
        res = backup({"ledger": self.led_path}, dest, stamp="s")
        led.append(A, "NOTE", {"a": 2}, T0)          # writer keeps going
        led.close()
        self.assertTrue(res.ok, res.detail)

    def test_missing_source_is_skipped_not_fatal(self):
        dest = os.path.join(self.dir, "b2")
        res = backup({"nope": os.path.join(self.dir, "absent.sqlite")},
                     dest, stamp="s")
        self.assertTrue(res.ok)
        self.assertEqual(len(res.entries), 0)

    def test_verify_detects_bit_rot(self):
        self._populate()
        dest = os.path.join(self.dir, "b3")
        res = backup({"ledger": self.led_path}, dest, stamp="s")
        target = res.entries[0].path
        with open(target, "r+b") as fh:
            fh.seek(2000); fh.write(b"\x00\x01\x02\x03")
        ok, why = verify_backup(dest)
        self.assertFalse(ok)
        self.assertIn("checksum", why)

    def test_verify_detects_a_missing_file(self):
        self._populate()
        dest = os.path.join(self.dir, "b4")
        res = backup({"ledger": self.led_path}, dest, stamp="s")
        os.remove(res.entries[0].path)
        ok, why = verify_backup(dest)
        self.assertFalse(ok)
        self.assertIn("missing", why)

    def test_verify_without_manifest(self):
        empty = os.path.join(self.dir, "empty"); os.makedirs(empty)
        ok, _ = verify_backup(empty)
        self.assertFalse(ok)


class TestRestore(Tmp):
    def test_round_trip_restores_real_data(self):
        led = Ledger(self.led_path)
        for i in range(6):
            led.append(A, "NOTE", {"i": i}, T0)
        led.close()
        dest = os.path.join(self.dir, "b")
        self.assertTrue(backup({"ledger": self.led_path}, dest, stamp="s").ok)

        os.remove(self.led_path)                      # disaster
        ok, why = restore(dest, {"ledger": self.led_path})
        self.assertTrue(ok, why)

        led = Ledger(self.led_path)
        chain_ok, chain_why = led.verify(A)
        self.assertTrue(chain_ok, chain_why)          # chain survives restore
        self.assertEqual(led.count(A), 6)
        led.close()

    def test_restore_refuses_an_unverified_backup(self):
        led = Ledger(self.led_path); led.append(A, "NOTE", {"a": 1}, T0); led.close()
        dest = os.path.join(self.dir, "b")
        res = backup({"ledger": self.led_path}, dest, stamp="s")
        with open(res.entries[0].path, "r+b") as fh:
            fh.seek(1500); fh.write(b"\xde\xad\xbe\xef")
        ok, why = restore(dest, {"ledger": self.led_path})
        self.assertFalse(ok)
        self.assertIn("refusing", why)

    def test_restore_moves_the_broken_file_aside(self):
        led = Ledger(self.led_path); led.append(A, "NOTE", {"a": 1}, T0); led.close()
        dest = os.path.join(self.dir, "b")
        backup({"ledger": self.led_path}, dest, stamp="s")
        ok, _ = restore(dest, {"ledger": self.led_path}, keep_corrupt_as="broken")
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(self.led_path + ".broken"))

    def test_restore_removes_stale_sidecars(self):
        """A leftover -wal belongs to the database being replaced; leaving it
        next to a restored file is a documented way to corrupt it."""
        led = Ledger(self.led_path); led.append(A, "NOTE", {"a": 1}, T0); led.close()
        dest = os.path.join(self.dir, "b")
        backup({"ledger": self.led_path}, dest, stamp="s")
        open(self.led_path + "-wal", "wb").write(b"stale")
        restore(dest, {"ledger": self.led_path})
        self.assertFalse(os.path.exists(self.led_path + "-wal"))

    def test_restore_with_no_matching_name(self):
        led = Ledger(self.led_path); led.append(A, "NOTE", {"a": 1}, T0); led.close()
        dest = os.path.join(self.dir, "b")
        backup({"ledger": self.led_path}, dest, stamp="s")
        ok, why = restore(dest, {"other": self.fact_path})
        self.assertFalse(ok)


class TestPrune(Tmp):
    def test_keeps_the_newest(self):
        root = os.path.join(self.dir, "backups")
        for name in ("20260801", "20260802", "20260803", "20260804"):
            os.makedirs(os.path.join(root, name))
        removed = prune(root, keep=2)
        self.assertEqual(sorted(removed), ["20260801", "20260802"])
        self.assertEqual(sorted(os.listdir(root)), ["20260803", "20260804"])

    def test_keep_must_be_positive(self):
        with self.assertRaises(ValueError):
            prune(self.dir, keep=0)

    def test_missing_root_is_harmless(self):
        self.assertEqual(prune(os.path.join(self.dir, "nope"), keep=1), ())


# ══ watchdog ════════════════════════════════════════════════════════════
class TestWatchdog(unittest.TestCase):
    def test_disabled_without_a_socket(self):
        n = Notifier(address="")
        if os.environ.get("NOTIFY_SOCKET"):
            self.skipTest("running under a supervisor")
        self.assertFalse(n.enabled)
        self.assertFalse(n.ready())      # no-op, does not raise
        self.assertFalse(n.ping())

    def test_interval_is_half_the_timeout(self):
        os.environ["WATCHDOG_USEC"] = str(30 * 1_000_000)
        try:
            self.assertEqual(watchdog_interval_s(), 15.0)
        finally:
            del os.environ["WATCHDOG_USEC"]

    def test_interval_falls_back_on_garbage(self):
        os.environ["WATCHDOG_USEC"] = "not-a-number"
        try:
            self.assertEqual(watchdog_interval_s(default=9.0), 9.0)
        finally:
            del os.environ["WATCHDOG_USEC"]

    def test_healthy_probe_pings(self):
        g = HealthGate(lambda: True)
        self.assertTrue(g.should_ping())
        self.assertEqual(g.consecutive_failures, 0)

    def test_wedged_service_eventually_stops_pinging(self):
        """The whole point: a running-but-broken process must be allowed to
        be killed, not kept alive by an unconditional heartbeat."""
        g = HealthGate(lambda: False, tolerate_failures=2)
        self.assertTrue(g.should_ping())    # 1st failure, inside tolerance
        self.assertTrue(g.should_ping())    # 2nd
        self.assertFalse(g.should_ping())   # 3rd — go silent
        self.assertEqual(g.consecutive_failures, 3)

    def test_recovery_resets_the_counter(self):
        state = {"ok": False}
        g = HealthGate(lambda: state["ok"], tolerate_failures=0)
        g.should_ping()
        self.assertEqual(g.consecutive_failures, 1)
        state["ok"] = True
        self.assertTrue(g.should_ping())
        self.assertEqual(g.consecutive_failures, 0)

    def test_a_raising_probe_counts_as_unhealthy(self):
        def boom() -> bool:
            raise RuntimeError("db gone")
        g = HealthGate(boom, tolerate_failures=0)
        self.assertFalse(g.should_ping())

    def test_beat_returns_whether_it_pinged(self):
        n = Notifier(address="")
        self.assertFalse(beat(n, HealthGate(lambda: True)))   # no socket
        self.assertFalse(beat(n, HealthGate(lambda: False, tolerate_failures=0)))


if __name__ == "__main__":
    unittest.main()
