"""What the ziman shell promises about pieces.

These read the shipped HTML rather than a copy of it, because the failure
being guarded against is a real one from this project's history: a panel that
looked trustworthy and was made entirely of typed-in numbers.

The rules worth keeping:
  * no price is ever filled in for her,
  * a loss is stated in words, not left for her to infer from two numbers,
  * nothing anywhere says GST, and
  * the numbers on the list come from the node, not from arithmetic here.
"""

import os
import re
import unittest

WEB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "web")
SRC = open(os.path.join(WEB, "ziman.html"), encoding="utf-8").read()


class TestNoTaxAnywhere(unittest.TestCase):
    def test_no_tax_line_no_tax_column_no_tax_arithmetic(self):
        # Unchanged rule: a business that is not registered may not charge or
        # imply GST, so there is no tax line, no tax column, and no rate
        # multiplied into anything in this file.
        for word in ("vat", "مالیات"):
            with self.subTest(word=word):
                self.assertIsNone(re.search(rf"\b{word}\b", SRC, re.I))
        self.assertNotIn("1.1", SRC)     # no tax arithmetic in the shell

    def test_gst_is_named_only_to_admit_it_is_unanswered(self):
        """Rule narrowed 2026-08-04, deliberately.

        It used to be "the shell never says GST". That was right while the
        answer was assumed. It is wrong now: whether this business is
        registered became a question, and an unanswered question must be
        visible rather than hidden behind a number that looks settled.

        So GST may appear here in exactly one situation — saying that the
        figures are not final because nobody has answered yet. Every mention
        has to sit behind that guard, and nothing may print a tax amount.
        """
        mentions = [m.start() for m in re.finditer(r"\bGST\b", SRC)]
        self.assertTrue(mentions, "the unanswered-state label should exist")
        for at in mentions:
            window = SRC[max(0, at - 400):at]
            self.assertIn("gstKnown", window,
                          "a GST mention that is not guarded by gstKnown")
            self.assertIn("بدون احتساب", SRC[max(0, at - 120):at + 40])

    def test_the_unanswered_state_says_the_number_is_not_final(self):
        self.assertIn("این سود نهایی نیست", SRC)


class TestPriceIsHers(unittest.TestCase):
    def test_the_price_field_is_never_prefilled_from_cost(self):
        # The two reference numbers may be shown. They may not be assigned.
        self.assertNotIn("f_price_aud').value = ", SRC)
        for mult in ("* 2", "*2", "* 2.5", "*2.5"):
            # Any multiple of cost may only appear inside the guidance line.
            for hit in re.finditer(re.escape(f"cogs {mult}"), SRC):
                window = SRC[max(0, hit.start() - 200):hit.start()]
                self.assertIn("guide", window)

    def test_both_reference_numbers_are_offered_as_comparison_only(self):
        self.assertIn("برای مقایسه", SRC)
        self.assertIn("تصمیم با خودتان است", SRC)

    def test_an_empty_floor_falls_back_to_the_listed_price(self):
        self.assertIn("اگر خالی بماند، همان قیمت اصلی ملاک است", SRC)

    def test_the_warning_is_computed_against_the_floor(self):
        # The exact case: listed price fine, floor below cost. The message
        # must name that situation rather than say "this price loses money"
        # about a price that does not.
        self.assertIn("قیمت اصلی خوب است، ولی با کمترین قیمتی که می‌پذیرید", SRC)
        self.assertIn("floor != null ? floor : listed", SRC)


class TestLossIsStatedInWords(unittest.TestCase):
    def test_a_loss_says_so_rather_than_showing_a_negative(self):
        self.assertIn("این قیمت ضرر می‌دهد", SRC)
        # The pinned bar turns red rather than printing a bare minus sign.
        self.assertIn(".cost.loss{", SRC)                    # the style exists
        # ...and is applied. Asserted as the loss branch rather than as the
        # whole expression: this used to pin the literal
        # `(gain < 0 ? 'loss' : 'good')`, which made it fail when the *other*
        # branch changed — the non-loss case stopped being unconditionally
        # "good" once her hours left the cost. Pinning a whole expression to
        # test one of its branches is a test that reports edits, not faults.
        self.assertRegex(SRC, r"gain < 0 \? 'loss'")

    def test_the_non_loss_branch_is_not_unconditionally_green(self):
        """Green means "you are fine". With labour outside `cogs_aud` nobody
        has counted the evenings, so the mark is withheld — see
        `test_time_is_not_claimed.py`."""
        self.assertRegex(SRC, r"timeCounted \? 'good' : ''")

    def test_the_loss_is_visible_while_she_types_not_after(self):
        """Rewritten 2026-08-04 with the one-question-per-screen layout.

        This used to assert a `confirm()` dialog on a below-cost price. The
        new flow says it earlier and twice: the pinned bar at the top of the
        screen flips to "ضرر روی هر دانه" as the digits go in, and the
        summary screen shows the same bar before anything is saved.

        A modal asking "are you sure?" arrives after the decision and gets
        dismissed reflexively. A number that changes under her thumb is the
        same information delivered while it can still change her mind.
        """
        self.assertIn("ضرر روی هر دانه", SRC)
        self.assertIn("refreshCost()", SRC)      # updates on every keystroke
        self.assertIn("drawSummary", SRC)        # and again before saving


class TestNumbersComeFromTheNode(unittest.TestCase):
    def test_the_list_renders_node_fields(self):
        for field in ("cogs_aud", "price_primary_aud", "price_secondary_aud",
                      "gross_margin_aud",
                      "verdicts", "days_on_sale", "net_margin_blocked"):
            with self.subTest(field=field):
                self.assertIn(field, SRC)

    def test_the_three_verdicts_are_the_agreed_three(self):
        for key, word in (("loses_money", "ضررده"),
                          ("stale", "خواب‌رفته"),
                          ("quick_sale", "زود فروخت")):
            with self.subTest(key=key):
                self.assertIn(key, SRC)
                self.assertIn(word, SRC)

    def test_a_blocked_margin_is_explained_not_blanked(self):
        self.assertIn("کارمزد این کانال هنوز ثبت نشده", SRC)

    def test_no_stock_or_batch_language_survives(self):
        for word in ("stock_qty", "batch_size", "runway", "موجودی"):
            self.assertNotIn(word, SRC)


class TestPersianInput(unittest.TestCase):
    def test_persian_and_arabic_digits_are_accepted(self):
        self.assertIn("۰۱۲۳۴۵۶۷۸۹", SRC)
        self.assertIn("٠١٢٣٤٥٦٧٨٩", SRC)

    def test_number_fields_are_text_inputs_not_number_inputs(self):
        # `type=number` rejects Persian digits outright on most keyboards.
        self.assertNotIn("type = 'number'", SRC)
        self.assertIn("inputMode", SRC)


class TestDraftIsDeviceLocal(unittest.TestCase):
    def test_the_draft_is_one_key_and_says_it_is_local(self):
        self.assertIn("ziman.draft.v1", SRC)
        self.assertIn("روی همین گوشی", SRC)

    def test_a_half_finished_piece_is_offered_back(self):
        self.assertIn("نیمه‌تمام", SRC)

    def test_saving_clears_the_draft(self):
        self.assertIn("clearDraft()", SRC)


class TestStatesAndChannels(unittest.TestCase):
    def test_the_four_states_are_in_her_language(self):
        for word in ("در دست ساخت", "برای فروش", "فروخته شد", "هدیه داده شد"):
            self.assertIn(word, SRC)

    def test_configured_zero_fee_channels_are_offered(self):
        # Only channels with fees in packs/ziman.yaml. Marketplace labels
        # stay absent until Ari sets their percent — unknown fee must not sell.
        self.assertIn(
            "const CHANNEL_FA = { direct: 'مستقیم', cash: 'نقد', payid: 'PayID' }",
            SRC,
        )
        self.assertNotIn("instagram:", SRC)
        self.assertNotIn("etsy:", SRC)
        self.assertNotIn("market:", SRC)
        self.assertNotIn("اینستاگرام", SRC)
        self.assertNotIn("بازارچه", SRC)

    def test_sale_receipt_collects_channel_and_explicit_unknowns(self):
        self.assertIn("رسید فروش واقعی", SRC)
        self.assertIn("amount_unknown", SRC)
        self.assertIn("fee_unknown", SRC)
        self.assertIn("واقعی است، آزمایشی نیست", SRC)

    def test_sale_uses_dedicated_route_never_generic_sold_save(self):
        self.assertIn("+ '/sales'", SRC)
        self.assertNotIn("state: 'sold'", SRC)
        self.assertNotIn("askChannel", SRC)
        self.assertNotIn("فروختمش", SRC)

    def test_listing_packet_and_receipt_words_are_distinct(self):
        self.assertIn("بستهٔ آگهی", SRC)
        self.assertIn("/listing-packet", SRC)
        self.assertIn("رسید فروش ثبت شد", SRC)
        self.assertIn("پرداخت تأیید شد", SRC)

    def test_api_strings_are_rendered_without_inner_html(self):
        self.assertNotRegex(SRC, r"\.innerHTML\s*=")
        self.assertIn("packet.caption", SRC)
        self.assertIn("textContent", SRC)


class TestBootReachability(unittest.TestCase):
    """The boot() function must not have a stray return that kills its tail.

    A past bug inserted a bare `return;` after `await load()`, making the
    header question count, readiness dots, safe_mode banner, and draw() all
    unreachable. The textual reachability test cannot see this (it follows
    call edges, not control flow), so this test checks the boot function's
    body directly: after `await load()` there must be no bare `return;`
    before `draw()`.
    """

    def test_no_stray_return_in_boot(self):
        # Extract the boot function body
        m = re.search(r'async function boot\(\)\s*\{(.*?)\n\}',
                      SRC, re.DOTALL)
        self.assertIsNotNone(m, "boot() function not found in ziman.html")
        boot_body = m.group(1)

        # Find the position of `await load()`
        load_pos = boot_body.find("await load()")
        self.assertGreater(load_pos, -1, "await load() not found in boot()")

        # Everything after load() should contain draw() and NOT contain
        # a bare `return;` before it.
        after_load = boot_body[load_pos:]
        draw_pos = after_load.find("draw()")
        self.assertGreater(draw_pos, -1,
                           "draw() not found after await load() in boot()")

        between = after_load[:draw_pos]
        # A bare `return;` (not inside a catch or if) would kill the tail.
        # We check for `return;` appearing outside of a catch block.
        lines = between.split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped == "return;":
                self.fail(
                    "Stray `return;` found between await load() and draw() "
                    "in boot() — this makes setDots, safe_mode, and draw "
                    "unreachable.")


if __name__ == "__main__":
    unittest.main()
