#!/usr/bin/env python3
"""test_consolidation_fold_rich.py — تثبیتِ فیکسِ «تا خوردن داخلِ ردیفِ غنی» (C-012/T1b).

پس‌زمینهٔ اندازه‌گیری‌شده (فایلِ زندهٔ `_ops/neural/consolidation.json`، ۲۰۲۶-۰۸-۱۵):
  از سیکلِ ۵۳۷ (۲۰۲۶-۰۷-۲۸، روشن‌شدنِ OCTOPUS_WIRE_LATENT_PERSIST در flags.cmd:732)
  هر ردیفی latent_vector دارد (۸۹/۸۹). شرطِ «مقصدِ fold نباید بردار داشته باشد»
  در مسیرِ بدون‌فلگ — که برای محافظتِ دادهٔ کمیابِ ۳-برداریِ آن روز نوشته شده بود —
  یعنی «هیچ‌وقت تا نشو»: ۲۰ ردیفِ عیناً یکسانِ پیاپیِ «فیکس‌های تأییدشده: 3 ·
  آگاهیِ میانگین: 0.73» (08-12 تا 08-15). فیکس: fold مجاز شد؛ بردار حفظ و توسط
  sync_latent (تطبیقِ last_cycle) تازه می‌شود.

$0 آفلاین، stdlib فقط، همهٔ نوشتن‌ها در tmpdir. هیچ لمسِ state واقعی.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
import harness

ENV = harness.setup("consolidation-fold-rich")   # ایزولاسیون — قبل از هر importِ opslib

from neural.consolidation import ConsolidationCycle


_SOURCES_A = {"school_awareness": {"mean_awareness": 0.73}}
_SOURCES_A2 = {"school_awareness": {"mean_awareness": 0.73}}   # عیناً همان
_SOURCES_B = {"school_awareness": {"mean_awareness": 0.80}}    # واقعاً متفاوت


class TestFoldIntoRichRow:
    """مسیرِ بدون‌فلگ (compress خاموش) — ردیفِ قبلیِ دارایِ بردار."""

    def setup_method(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "consolidation.json"
        # سیکلِ اول — ردیفِ عادی
        cyc = ConsolidationCycle(self.path)
        r1 = cyc.run(_SOURCES_A)
        # شبیه‌سازیِ LATENT_PERSIST: ردیفِ اول غنی می‌شود (مسیرِ زندهٔ امروز)
        import dataclasses
        rich_vec = [0.1, 0.2, 0.3]
        cyc.history  # noqa: B018 — فقط برای خوانایی
        row = json.loads(self.path.read_text(encoding="utf-8"))[-1]
        row["latent_vector"] = rich_vec
        self.path.write_text(json.dumps([row], ensure_ascii=False), encoding="utf-8")
        self.rich_vec = rich_vec

    def teardown_method(self):
        self.tmp.cleanup()

    def _rows(self):
        return json.loads(self.path.read_text(encoding="utf-8"))

    def test_identical_next_cycle_folds_no_new_row(self):
        cyc = ConsolidationCycle(self.path)
        n_before = len(self._rows())
        r2 = cyc.run(_SOURCES_A2)
        rows = self._rows()
        assert len(rows) == n_before, "ردیفِ تکراریِ عیناً-یکسان append شد — گارد باز هم فریز بود"
        assert rows[-1]["repeats"] == 2
        assert rows[-1]["last_cycle"] == r2.cycle
        assert rows[-1]["latent_vector"] == self.rich_vec, "بردارِ مقصد در fold له شد"

    def test_sync_latent_refreshes_vector_on_folded_row(self):
        cyc = ConsolidationCycle(self.path)
        r2 = cyc.run(_SOURCES_A2)
        r2.latent_vector = [0.9, 0.9, 0.9]
        changed = cyc.sync_latent(r2)
        rows = self._rows()
        assert changed is True
        assert len(rows) == 1, "sync_latent نباید ردیفِ نو بسازد"
        assert rows[-1]["latent_vector"] == [0.9, 0.9, 0.9], "بردارِ تازه روی ردیفِ تا‌شده ننشست"

    def test_genuinely_new_insight_still_appends(self):
        cyc = ConsolidationCycle(self.path)
        n_before = len(self._rows())
        cyc.run(_SOURCES_B)
        rows = self._rows()
        assert len(rows) == n_before + 1, "بینشِ متفاوت نباید تا شود"
        assert rows[-1]["insights"] == ["آگاهیِ میانگین: 0.80"]

    def test_cycle_counter_monotonic_across_folds(self):
        cyc = ConsolidationCycle(self.path)
        r2 = cyc.run(_SOURCES_A2)
        cyc3 = ConsolidationCycle(self.path)   # ری‌استارتِ پروسه
        r3 = cyc3.run(_SOURCES_A2)
        assert r3.cycle == r2.cycle + 1, "شمارنده پس از fold باید یکنوا پیش برود (درسِ 2026-07-30)"


def main():
    t = TestFoldIntoRichRow()
    for name in dir(t):
        if name.startswith("test_"):
            t.setup_method()
            try:
                getattr(t, name)()
                print(f"PASS {name}")
            finally:
                t.tmp.cleanup()


if __name__ == "__main__":
    main()
