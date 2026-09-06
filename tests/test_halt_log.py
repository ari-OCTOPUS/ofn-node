"""HaltLog adapter — append-only latch history, not a run.

Complementary to ``halt_flag`` (live switch) and independent of
``run_store`` / ``run_gate`` (owned by open PRs). A transition is
a fact about the switch, not a send and not a half-born run.
"""

from __future__ import annotations

import json
import os
import stat
import unittest
from pathlib import Path

from ofn.adapters import halt_flag
from ofn.adapters.halt_log import HaltLog
from ofn.kernel.errors import FailClosedError
from ofn.kernel.halt_latch import HALT_ASSERTED, HALT_CLEARED
from tests.tmpdir import temp_dir

_NOW = 1780000000


class HaltLogDurability(unittest.TestCase):
    def setUp(self):
        self.root = Path(temp_dir(self))
        self.log = HaltLog(self.root / "halt-log")

    def test_dir_is_0700_on_posix(self):
        if os.name == "nt":
            self.skipTest("POSIX file mode is not a Windows fact")
        mode = self.log.root.stat().st_mode
        self.assertEqual(stat.S_IMODE(mode), 0o700)

    def test_assert_then_replay_and_reopen(self):
        tid = self.log.record(
            kind=HALT_ASSERTED, now_epoch_s=_NOW, actor="owner",
            note="supervisor armed",
        )
        self.assertTrue(tid.startswith("hlt-"))
        self.assertTrue(self.log.armed())
        rows = list(self.log.replay())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["kind"], HALT_ASSERTED)
        self.assertEqual(rows[0]["actor"], "owner")
        self.assertEqual(rows[0]["seq"], 1)
        reopened = HaltLog(self.root / "halt-log")
        self.assertTrue(reopened.armed())
        self.assertEqual(list(reopened.replay())[0]["transition_id"], tid)

    def test_file_is_0600_on_posix_after_write(self):
        if os.name == "nt":
            self.skipTest("POSIX file mode is not a Windows fact")
        self.log.record(kind=HALT_ASSERTED, now_epoch_s=_NOW, actor="owner")
        mode = (self.root / "halt-log" / "transitions.jsonl").stat().st_mode
        self.assertEqual(stat.S_IMODE(mode), 0o600)

    def test_clear_then_assert_again(self):
        self.log.record(kind=HALT_ASSERTED, now_epoch_s=_NOW, actor="owner")
        self.log.record(
            kind=HALT_CLEARED, now_epoch_s=_NOW + 1, actor="supervisor")
        self.assertFalse(self.log.armed())
        self.log.record(
            kind=HALT_ASSERTED, now_epoch_s=_NOW + 2, actor="owner")
        self.assertTrue(self.log.armed())
        self.assertEqual(len(list(self.log.replay())), 3)

    def test_double_assert_writes_nothing(self):
        self.log.record(kind=HALT_ASSERTED, now_epoch_s=_NOW, actor="owner")
        with self.assertRaises(FailClosedError):
            self.log.record(
                kind=HALT_ASSERTED, now_epoch_s=_NOW + 1, actor="owner")
        self.assertEqual(len(list(self.log.replay())), 1)

    def test_stray_clear_writes_nothing(self):
        with self.assertRaises(FailClosedError):
            self.log.record(
                kind=HALT_CLEARED, now_epoch_s=_NOW, actor="owner")
        self.assertEqual(list(self.log.replay()), [])
        self.assertFalse((self.root / "halt-log" / "transitions.jsonl").exists())


class HaltLogIsNotASend(unittest.TestCase):
    def setUp(self):
        self.root = Path(temp_dir(self))
        self.log = HaltLog(self.root / "halt-log")

    def test_sealed_kind_refused(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    self.log.record(
                        kind=name, now_epoch_s=_NOW, actor="owner")
        self.assertEqual(list(self.log.replay()), [])

    def test_grants_send_payload_is_false(self):
        self.assertIs(self.log.grants_send_payload(), False)

    def test_grants_send_payload_refuses_sealed_blob(self):
        with self.assertRaises(FailClosedError):
            self.log.grants_send_payload({"state": "quote_sent"})


class HaltLogVersusFlag(unittest.TestCase):
    def setUp(self):
        self.root = Path(temp_dir(self))
        self.flag = self.root / "halt.flag"
        self.log = HaltLog(self.root / "halt-log")

    def test_agreement_when_both_disarmed(self):
        self.assertFalse(self.log.disagrees_with_flag(self.flag))

    def test_disagreement_when_log_armed_flag_absent(self):
        self.log.record(kind=HALT_ASSERTED, now_epoch_s=_NOW, actor="owner")
        self.assertFalse(halt_flag.halt_flag_active(self.flag))
        self.assertTrue(self.log.disagrees_with_flag(self.flag))

    def test_agreement_when_both_armed_independently(self):
        self.log.record(kind=HALT_ASSERTED, now_epoch_s=_NOW, actor="owner")
        halt_flag.write_halt(self.flag)
        self.assertFalse(self.log.disagrees_with_flag(self.flag))
        # log did not write the flag; flag did not write the log
        self.assertTrue(halt_flag.halt_flag_active(self.flag))
        self.assertTrue(self.log.armed())

    def test_does_not_call_write_halt(self):
        self.log.record(kind=HALT_ASSERTED, now_epoch_s=_NOW, actor="owner")
        self.assertFalse(self.flag.exists())
        self.assertFalse(halt_flag.halt_flag_active(self.flag))


class HaltLogRefusesPlantedBodies(unittest.TestCase):
    def setUp(self):
        self.root = Path(temp_dir(self))

    def test_symlink_log_refuses_open_and_write(self):
        d = self.root / "halt-log"
        d.mkdir()
        target = self.root / "elsewhere.jsonl"
        target.write_text("{}\n", encoding="utf-8")
        (d / "transitions.jsonl").symlink_to(target)
        with self.assertRaises(FailClosedError):
            HaltLog(d)
        log = HaltLog(self.root / "fresh")
        planted = log.root / "transitions.jsonl"
        planted.symlink_to(target)
        with self.assertRaises(FailClosedError):
            log.record(kind=HALT_ASSERTED, now_epoch_s=_NOW, actor="owner")
        self.assertEqual(target.read_text(encoding="utf-8"), "{}\n")

    def test_corrupt_line_fails_closed_on_open(self):
        d = self.root / "halt-log"
        d.mkdir()
        (d / "transitions.jsonl").write_text("not-json\n", encoding="utf-8")
        with self.assertRaises(FailClosedError):
            HaltLog(d)

    def test_send_kind_planted_in_file_fails_closed(self):
        d = self.root / "halt-log"
        d.mkdir()
        planted = {
            "transition_id": "hlt-deadbeef",
            "seq": 1,
            "kind": "quote_sent",
            "ts": _NOW,
            "actor": "owner",
            "note": None,
        }
        (d / "transitions.jsonl").write_text(
            json.dumps(planted) + "\n", encoding="utf-8")
        with self.assertRaises(FailClosedError):
            HaltLog(d)


if __name__ == "__main__":
    unittest.main()
