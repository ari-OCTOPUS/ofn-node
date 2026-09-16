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


class TestInspirationCardsNeverFake(unittest.TestCase):
    """الهام امروز: the hard rule is zero observations means zero cards.

    A fabricated trend on a partner's screen is worse than an honest empty
    state, because it teaches her to trust invented evidence. So the store
    builds cards only from real observation rows, and an empty store yields
    an empty list — which the UI renders as the candid "nothing yet" line.
    """

    def setUp(self):
        self.tmp = tempfile.mktemp(suffix=".sqlite")
        self.now = int(time.time())
        self.store = MarketingStore(self.tmp)

    def tearDown(self):
        self.store.close()
        if os.path.exists(self.tmp):
            os.unlink(self.tmp)

    def test_empty_store_yields_no_cards(self):
        self.assertEqual(self.store.inspiration_cards("studio"), [])

    def test_summary_includes_empty_inspiration_when_no_observations(self):
        summ = self.store.summary("studio")
        self.assertEqual(summ["inspiration_cards"], [])

    def test_real_observation_becomes_a_card_with_real_fields(self):
        self.store.open_week("studio", "W1", starts_at=self.now,
                             style_id="educational", focus_text=None,
                             now_epoch_s=self.now)
        self.store.record_observations(
            "studio", "W1",
            [_obs("foot-care", source_id="manual", count_value=12.0,
                  source_url="https://trends.example/x")],
            now_epoch_s=self.now)
        cards = self.store.inspiration_cards("studio")
        self.assertEqual(len(cards), 1)
        c = cards[0]
        # Every field is real evidence, nothing invented.
        self.assertEqual(c["title_fa"], "foot-care")
        self.assertEqual(c["source_id"], "manual")
        self.assertEqual(c["observed_at"], 1_000_000)
        self.assertEqual(c["source_url"], "https://trends.example/x")
        self.assertIn("۱۲", c["count_or_rank_fa"])  # persian digits, real count
        # why_now/why_saba are NOT invented here — a later proposal step fills
        # them. Honest None, never a fabricated sentence.
        self.assertIsNone(c["why_now_fa"])
        self.assertIsNone(c["why_saba_fa"])

    def test_no_fabricated_idea_keys_or_invented_terms(self):
        # A card must never carry a term that wasn't an observation row.
        self.store.open_week("studio", "W1", starts_at=self.now,
                             style_id="educational", focus_text=None,
                             now_epoch_s=self.now)
        self.store.record_observations(
            "studio", "W1", [_obs("only-real")], now_epoch_s=self.now)
        cards = self.store.inspiration_cards("studio")
        titles = {c["title_fa"] for c in cards}
        self.assertEqual(titles, {"only-real"})
        # No sample/demo/placeholder terms smuggled in.
        self.assertNotIn("نمونه", titles)
        self.assertNotIn("sample", titles)


if __name__ == "__main__":
    unittest.main()
