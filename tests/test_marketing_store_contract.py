"""Contract tests for the marketing store — the persisted scout memory.

The single most important property here is the one the senior-architect
review flagged: the scout's rejection memory must survive a restart. A
rejected idea that is forgotten on reboot is the loop the scout exists to
break, so this test rebuilds a fresh store from the same file and checks
the memory is still there.
"""

import os
import tempfile
import time
import unittest

from ofn.adapters.marketing_store import MarketingStore
from ofn.kernel.marketing_scout import (
    Candidate, Disposition, Memory, Note, TrendObservation, triage,
)


def _obs(term="t", **kw):
    base = dict(source_id="s", term=term, observed_at=1_000_000,
                count_value=1.0)
    base.update(kw)
    return TrendObservation(**base)


def _cand(key="k", **kw):
    base = dict(key=key, title="T", style_id="educational",
                framing="beauty", observations=(_obs(),), confidence=0.8)
    base.update(kw)
    return Candidate(**base)


class TestScoutMemoryPersistence(unittest.TestCase):
    """The blocker: memory must survive a restart."""

    def setUp(self):
        self.tmp = tempfile.mktemp(suffix=".sqlite")
        self.now = int(time.time())

    def tearDown(self):
        if os.path.exists(self.tmp):
            os.unlink(self.tmp)

    def test_rejected_hard_survives_reopen(self):
        c = _cand("foot-care")
        s1 = MarketingStore(self.tmp)
        s1.remember("studio", c,
                    Note(c.key, Disposition.REJECTED_HARD, "banned", self.now),
                    rejected_by="saba", now_epoch_s=self.now)
        s1.close()

        # A brand-new store object on the same file must see the rejection.
        s2 = MarketingStore(self.tmp)
        mem = s2.load_memory("studio")
        self.assertEqual(mem.disposition("foot-care"),
                         Disposition.REJECTED_HARD)

        # And the scout must refuse the same candidate again, automatically.
        fresh, refused = triage([c], mem, now_epoch_s=self.now)
        self.assertEqual(len(fresh), 0)
        self.assertEqual(refused[0][1].rule, "scout:already-final")
        s2.close()

    def test_two_tenants_do_not_share_memory(self):
        c = _cand("shared-key")
        s = MarketingStore(self.tmp)
        s.remember("studio", c,
                   Note(c.key, Disposition.REJECTED_HARD, "x", self.now),
                   rejected_by="saba", now_epoch_s=self.now)
        s.close()

        s = MarketingStore(self.tmp)
        # studio sees the rejection…
        self.assertEqual(s.load_memory("studio").disposition("shared-key"),
                         Disposition.REJECTED_HARD)
        # …lead does not. Tenant isolation at the memory level.
        self.assertEqual(s.load_memory("lead").disposition("shared-key"),
                         Disposition.UNSEEN)
        s.close()


class TestWeeklyCycle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mktemp(suffix=".sqlite")
        self.now = int(time.time())

    def tearDown(self):
        if os.path.exists(self.tmp):
            os.unlink(self.tmp)

    def test_open_then_current_week(self):
        s = MarketingStore(self.tmp)
        s.open_week("studio", "2026-W32", starts_at=self.now,
                    style_id="educational", focus_text="hi",
                    now_epoch_s=self.now)
        w = s.current_week("studio")
        self.assertEqual(w["week_id"], "2026-W32")
        self.assertEqual(w["status"], "open")
        s.close()

    def test_record_and_read_observations(self):
        s = MarketingStore(self.tmp)
        s.open_week("studio", "2026-W32", starts_at=self.now,
                    style_id="educational", focus_text=None,
                    now_epoch_s=self.now)
        s.record_observations(
            "studio", "2026-W32",
            [_obs("a"), _obs("b", rank_value=2)], now_epoch_s=self.now)
        got = s.observations_for_week("studio", "2026-W32")
        self.assertEqual(len(got), 2)
        s.close()

    def test_summary_returns_safe_compact_view(self):
        s = MarketingStore(self.tmp)
        summ = s.summary("studio")
        self.assertIn("current_week", summ)
        self.assertIn("trend_observations", summ)
        self.assertIn("rejected_ideas_in_memory", summ)
        s.close()


if __name__ == "__main__":
    unittest.main()
