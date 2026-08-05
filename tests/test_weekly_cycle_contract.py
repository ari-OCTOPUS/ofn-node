"""Contract tests for trend sources and the weekly cycle.

Two properties matter most, both from the studio brief:

1. A trend source never sends Saba's data out, and never crashes the cycle.
2. The weekly cycle is idempotent for the same week — a re-run after a
   crash does not double-propose, because PROPOSED becomes a duplicate.
"""

import os
import tempfile
import time
import unittest

from ofn.adapters.marketing_store import MarketingStore
from ofn.adapters.trend_sources import (
    HttpTrendSource, ManualTrendSource, TrendAggregator, TrendQuery,
)
from ofn.adapters.weekly_cycle import WeeklyCycle
from ofn.kernel.marketing_scout import (
    Candidate, Disposition, TrendObservation,
)


def _obs(term="t", **kw):
    base = dict(source_id="manual", term=term, observed_at=1_700_000_000,
                count_value=1.0)
    base.update(kw)
    return TrendObservation(**base)


def _cand(key="k", **kw):
    base = dict(key=key, title="T", style_id="educational",
                framing="beauty", observations=(_obs(),), confidence=0.8)
    base.update(kw)
    return Candidate(**base)


class TestManualSource(unittest.TestCase):
    def test_filters_to_asked_terms(self):
        s = ManualTrendSource((_obs("foot"), _obs("hair")))
        got = s.observe(TrendQuery(terms=("foot",)))
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0].term, "foot")

    def test_empty_terms_returns_everything(self):
        s = ManualTrendSource((_obs("a"), _obs("b")))
        self.assertEqual(len(s.observe(TrendQuery(terms=()))), 2)

    def test_sends_saba_data_is_false(self):
        self.assertFalse(ManualTrendSource().sends_saba_data)


class TestHttpSourceFailClosed(unittest.TestCase):
    def test_no_key_returns_empty(self):
        s = HttpTrendSource(source_id="x", endpoint="http://invalid.invalid")
        self.assertEqual(s.observe(TrendQuery(terms=("a",))), ())

    def test_sends_saba_data_true_refuses_to_observe(self):
        # A source flagged as leaking partner data must not run.
        s = HttpTrendSource(source_id="x", endpoint="http://x",
                            api_key="k", sends_saba_data=True)
        self.assertEqual(s.observe(TrendQuery(terms=("a",))), ())

    def test_network_error_returns_empty_not_crash(self):
        s = HttpTrendSource(source_id="x", endpoint="http://127.0.0.1:1/",
                            api_key="k", timeout_s=1)
        # The connection fails; the source returns (), it does not raise.
        self.assertEqual(s.observe(TrendQuery(terms=("a",))), ())


class TestAggregator(unittest.TestCase):
    def test_concatenates_sources_in_order(self):
        a = ManualTrendSource((_obs("a"),))
        b = ManualTrendSource((_obs("b"),))
        agg = TrendAggregator((a, b))
        got = agg.observe(TrendQuery(terms=()))
        self.assertEqual([o.term for o in got], ["a", "b"])

    def test_one_failing_source_does_not_kill_the_cycle(self):
        class Boom:
            source_id = "boom"
            sends_saba_data = False
            def observe(self, q):
                raise RuntimeError("bang")
        agg = TrendAggregator((Boom(), ManualTrendSource((_obs("ok"),))))
        got = agg.observe(TrendQuery(terms=()))
        self.assertEqual(len(got), 1)


class TestWeeklyCycle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mktemp(suffix=".sqlite")
        self.now = int(time.time())
        self.store = MarketingStore(self.tmp)

    def tearDown(self):
        self.store.close()
        if os.path.exists(self.tmp):
            os.unlink(self.tmp)

    def _cycle(self, sources=()):
        return WeeklyCycle(self.store, TrendAggregator(sources))

    def test_fresh_candidate_survives_weak_one_refused(self):
        src = ManualTrendSource((_obs(),))
        c = self._cycle((src,))
        result = c.run(
            tenant="studio", week_id="W1", starts_at=self.now,
            style_id="educational", query=TrendQuery(terms=()),
            candidates=(_cand("good"), _cand("bad", confidence=0.1)),
            now_epoch_s=self.now,
        )
        self.assertEqual(len(result.fresh_candidates), 1)
        self.assertEqual(result.refused_count, 1)

    def test_same_week_rerun_does_not_repropose(self):
        src = ManualTrendSource((_obs(),))
        c = self._cycle((src,))
        first = c.run(
            tenant="studio", week_id="W1", starts_at=self.now,
            style_id="educational", query=TrendQuery(terms=()),
            candidates=(_cand("good"),), now_epoch_s=self.now,
        )
        self.assertEqual(len(first.fresh_candidates), 1)

        # Re-run the same week with the same candidate: it is now PROPOSED,
        # so the scout refuses it as a duplicate.
        second = c.run(
            tenant="studio", week_id="W1", starts_at=self.now,
            style_id="educational", query=TrendQuery(terms=()),
            candidates=(_cand("good"),), now_epoch_s=self.now,
        )
        self.assertEqual(len(second.fresh_candidates), 0)

    def test_rejected_hard_via_cycle_blocks_future_proposals(self):
        src = ManualTrendSource((_obs(),))
        c = self._cycle((src,))
        bad = _cand("banned")
        c.reject(tenant="studio", candidate=bad, reason="against policy",
                 rejected_by="saba", now_epoch_s=self.now)

        result = c.run(
            tenant="studio", week_id="W1", starts_at=self.now,
            style_id="educational", query=TrendQuery(terms=()),
            candidates=(bad,), now_epoch_s=self.now,
        )
        self.assertEqual(len(result.fresh_candidates), 0)

    def test_focus_text_is_derived_from_gaps(self):
        c = self._cycle()
        result = c.run(
            tenant="studio", week_id="W1", starts_at=self.now,
            style_id="teaser", query=TrendQuery(terms=()),
            candidates=(),  # no candidates this week — focus still derived
            tried_styles={"teaser": 0, "educational": 3},
            now_epoch_s=self.now,
        )
        # 'teaser' is untried → it becomes a research question.
        self.assertIn("teaser", result.focus_text.lower())


if __name__ == "__main__":
    unittest.main()
