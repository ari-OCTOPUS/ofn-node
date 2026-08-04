"""When her hours are not in the cost, no screen may call the rest "profit".

The two time questions were removed at the owner's decision, so `cogs_aud`
is now what was *bought*. The subtraction `price - cogs` still happens and is
still arithmetic. What changed is what it means, and nothing on the screen
knew that: the same green bar, the same bare number in the margin column, the
same word "سود".

    716 tests were green while the system said "you made $20"
    about a piece that took twenty-four hours

Not one of them was wrong. They asserted the arithmetic, and the arithmetic
was right. The claim attached to it was what became false, and a claim is not
a thing this suite had any way to check — the same shape as the name leak: an
assertion about content where the fault was in what the content asserted.

So the flag travels with the number rather than the number being hidden.
Materials really are covered, and that is worth knowing. What must not happen
is a green mark meaning "you are fine" when nobody counted the evenings.
"""

from __future__ import annotations

import os
import re
import unittest

from ofn.adapters.packloader import load_pack
from ofn.adapters.products import Product, money_view

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHELL = os.path.join(ROOT, "web", "ziman.html")
PACK = os.path.join(ROOT, "packs", "ziman.yaml")


def piece(cogs=180.0, primary=280.0, secondary=200.0) -> Product:
    return Product(
        id=1, tenant_id="ziman", sku="ZM-0001", name="باکس", category=None,
        description=None, materials_cost_aud=cogs, labour_hours=0.0,
        hourly_rate_aud=0.0, packaging_cost_aud=0.0, cogs_aud=cogs,
        price_primary_aud=primary, price_secondary_aud=secondary,
        state="for_sale", channel=None, listed_at=None, sold_at=None,
        marketing_status="not_started", marketing_notes=None,
        created_at="2026-08-04T00:00:00Z", updated_at=None)


class TestTheViewSaysWhatItKnows(unittest.TestCase):
    def test_the_flag_travels_with_the_numbers(self):
        v = money_view(piece(), gst_rate=0.0, gst_known=True,
                       time_counted=False)
        self.assertFalse(v["time_counted"])

    def test_the_figure_is_not_hidden(self):
        """Hiding it would be its own lie. Materials really are covered."""
        v = money_view(piece(), gst_rate=0.0, gst_known=True,
                       time_counted=False)
        self.assertAlmostEqual(v["margin_aud"], 20.0)

    def test_counting_time_is_still_the_default(self):
        """A caller that has not been updated must not silently start
        claiming less than it knows — or more."""
        v = money_view(piece(), gst_rate=0.0, gst_known=True)
        self.assertTrue(v["time_counted"])

    def test_a_real_loss_is_still_a_real_loss(self):
        """Below this price the money spent on materials does not come back.
        That is true whether or not anybody counted the hours, and softening
        it would trade one false reading for another."""
        v = money_view(piece(cogs=300.0, primary=280.0, secondary=200.0),
                       gst_rate=0.0, gst_known=True, time_counted=False)
        self.assertTrue(v["loses_money"])

    def test_not_losing_money_is_not_the_same_as_profitable(self):
        """The exact pair that made this necessary: the recorded piece cost
        $180 in materials and was priced at $200. Before the change the
        screen read "$700 loss"; after it, "$20 profit"; the truth is that
        twenty-four hours are in neither number."""
        v = money_view(piece(), gst_rate=0.0, gst_known=True,
                       time_counted=False)
        self.assertFalse(v["loses_money"])
        self.assertFalse(v["time_counted"])


class TestThePackIsTheSourceOfTruth(unittest.TestCase):
    def test_the_ziman_pack_declares_no_labour_term(self):
        pack = load_pack(PACK)
        self.assertEqual(pack.labour_hours_field, "")
        self.assertEqual(pack.labour_rate_field, "")

    def test_the_flag_is_derived_not_hardcoded(self):
        """So that the day a labour term is declared again, the screens go
        back to saying "profit" without anybody editing a string."""
        src = open(os.path.join(ROOT, "ofn", "node.py"), encoding="utf-8").read()
        self.assertIn("pack.labour_hours_field and pack.labour_rate_field", src)


class TestTheShellDoesNotClaimProfit(unittest.TestCase):
    def setUp(self):
        src = open(SHELL, encoding="utf-8").read()
        self.js = re.sub(r"/\*.*?\*/|<!--.*?-->", "", src, flags=re.S)

    def test_the_shell_reads_the_flag(self):
        self.assertIn("data.time_counted", self.js)

    def test_an_absent_flag_is_read_the_safe_way(self):
        """An older node that does not send it must not be treated as having
        said "yes". `!== false` claims less, not more."""
        self.assertIn("data.time_counted !== false", self.js)

    def test_the_word_profit_is_conditional_everywhere_it_appears(self):
        """Every remaining "سود" in a label position has to be guarded by the
        flag. This is the assertion the old suite had no way to express."""
        for line in self.js.splitlines():
            if "'سود'" in line:
                self.assertIn("time_counted", line,
                              f"unconditional profit label: {line.strip()}")

    def test_the_running_bar_has_a_different_word(self):
        self.assertIn("بیشتر از خرج مواد", self.js)

    def test_green_is_withheld_when_time_is_uncounted(self):
        """A green mark means "you are fine"."""
        self.assertRegex(self.js, r"timeCounted \? 'good' : ''")

    def test_the_detail_screen_says_it_in_words_once(self):
        self.assertIn("وقتی که روی این قطعه", self.js)

    def test_the_multiplier_guidance_is_qualified(self):
        """2x and 2.5x assume the cost being multiplied includes labour.
        Against materials alone the rule of thumb turns a missing input into
        a recommendation."""
        guide = re.search(r"برای مقایسه.*?\)\);", self.js, re.S)
        self.assertIsNotNone(guide)
        self.assertIn("timeCounted", guide.group(0))


if __name__ == "__main__":
    unittest.main()
