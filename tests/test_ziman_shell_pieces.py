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
    def test_the_shell_never_says_gst(self):
        # The business is not registered, so implying a tax would be both
        # wrong and, in this market, not allowed.
        #
        # Whole words only: the font host is `fonts.gstatic.com`, and a
        # substring match there would be a test that cries wolf until
        # somebody stops listening to it.
        for word in ("gst", "vat", "tax", "مالیات"):
            with self.subTest(word=word):
                self.assertIsNone(re.search(rf"\b{word}\b", SRC, re.I))


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
        self.assertIn("money loss", SRC)

    def test_pricing_under_cost_asks_for_confirmation(self):
        self.assertIn("مطمئنید؟", SRC)


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

    def test_the_four_channels_are_offered(self):
        for word in ("اینستاگرام", "بازارچه", "Etsy", "مستقیم"):
            self.assertIn(word, SRC)

    def test_selling_asks_where(self):
        self.assertIn("کجا فروختید؟", SRC)


if __name__ == "__main__":
    unittest.main()
