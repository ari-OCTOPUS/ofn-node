"""The CSV, and the three details that decide whether it is useful.

All three are about the program on the other end. None of them is visible
when the file is opened in a text editor, which is why each one gets an
assertion rather than a habit.
"""

from __future__ import annotations

import csv
import io
import unittest

from ofn.adapters.export_csv import (
    BOM, COLUMNS, FORBIDDEN_HEADINGS, filename, to_csv,
)
from ofn.adapters.products import Product


def piece(sku="ZM-0001", name="گوشوارهٔ نقره", archived=None, **over) -> Product:
    base = dict(
        id=1, tenant_id="ziman", sku=sku, name=name, category=None,
        description=None, materials_cost_aud=77.5, labour_hours=0.0,
        hourly_rate_aud=0.0, packaging_cost_aud=3.0, cogs_aud=80.5,
        price_primary_aud=120.0, price_secondary_aud=None, state="for_sale",
        channel=None, listed_at=None, sold_at=None,
        marketing_status="not_started", marketing_notes=None,
        created_at="2026-08-05T09:00:00Z", updated_at=None,
        archived_at=archived)
    base.update(over)
    return Product(**base)


def rows(text: str) -> list[list[str]]:
    return list(csv.reader(io.StringIO(text.lstrip(BOM))))


class TestExcelCanRead(unittest.TestCase):
    def test_it_starts_with_a_byte_order_mark(self):
        """Excel on Windows reads a CSV without one as the local codepage,
        and every Persian character becomes mojibake. Three bytes turn "the
        export is broken" into "the export works"."""
        self.assertTrue(to_csv([piece()]).startswith(BOM))

    def test_the_bom_is_the_utf8_one(self):
        self.assertEqual(to_csv([]).encode("utf-8")[:3], b"\xef\xbb\xbf")

    def test_line_endings_are_what_a_spreadsheet_expects(self):
        self.assertIn("\r\n", to_csv([piece()]))

    def test_a_name_with_a_comma_stays_one_column(self):
        """A name containing a comma is a name, not a new column."""
        out = rows(to_csv([piece(name="گوشواره, نقره")]))
        self.assertEqual(len(out[1]), len(COLUMNS))
        self.assertEqual(out[1][1], "گوشواره, نقره")


class TestNumbersAddUp(unittest.TestCase):
    def test_digits_are_latin_not_persian(self):
        """The interface shows ۱۲۵ because she reads it. A spreadsheet shown
        ۱۲۵ stores text, and text does not add up — the column looks right
        and the total is zero."""
        text = to_csv([piece()])
        for persian in "۰۱۲۳۴۵۶۷۸۹":
            self.assertNotIn(persian, text)

    def test_a_persian_number_arriving_in_a_field_is_converted(self):
        out = rows(to_csv([piece(sku="ZM-۰۰۰۲")]))
        self.assertEqual(out[1][0], "ZM-0002")

    def test_the_cost_column_is_a_number_a_spreadsheet_accepts(self):
        out = rows(to_csv([piece()]))
        cost = out[1][[f for f, _ in COLUMNS].index("cogs_aud")]
        self.assertEqual(float(cost), 80.5)

    def test_an_empty_value_is_empty_not_the_word_none(self):
        out = rows(to_csv([piece(price_secondary_aud=None)]))
        self.assertEqual(
            out[1][[f for f, _ in COLUMNS].index("price_secondary_aud")], "")


class TestNoTaxColumn(unittest.TestCase):
    def test_no_heading_claims_a_tax_position(self):
        """Until `business.gst_registered` is answered, no figure here may
        claim to be net of tax. A column headed "after GST" computed from an
        unanswered question is the one column somebody pastes into a
        return."""
        header = " ".join(label for _, label in COLUMNS).lower()
        fields = " ".join(field for field, _ in COLUMNS).lower()
        for word in FORBIDDEN_HEADINGS:
            self.assertNotIn(word, header, word)
            self.assertNotIn(word, fields, word)

    def test_no_margin_column_either(self):
        """Margin is a claim, and right now it is a claim that leaves out her
        time — see D-12. Cost and price are facts; the subtraction is not."""
        fields = [f for f, _ in COLUMNS]
        for f in ("margin_aud", "margin_pct", "net_margin_aud"):
            self.assertNotIn(f, fields)

    def test_cost_and_price_are_both_there(self):
        """Refusing to compute margin is not refusing to give her the two
        numbers it would be computed from."""
        fields = [f for f, _ in COLUMNS]
        self.assertIn("cogs_aud", fields)
        self.assertIn("price_primary_aud", fields)


class TestWhatIsIncluded(unittest.TestCase):
    def test_an_archived_piece_is_absent_by_default(self):
        self.assertEqual(len(rows(to_csv([piece(archived="2026-08-05")]))), 1)

    def test_but_can_be_asked_for(self):
        out = rows(to_csv([piece(archived="2026-08-05")],
                          include_archived=True))
        self.assertEqual(len(out), 2)

    def test_an_empty_shelf_still_has_a_header(self):
        """A file with nothing in it must still say what it would have
        contained, or it reads as a failed export."""
        out = rows(to_csv([]))
        self.assertEqual(len(out), 1)
        self.assertEqual(len(out[0]), len(COLUMNS))

    def test_the_filename_sorts_by_date_and_names_the_business(self):
        self.assertEqual(filename("ziman", "2026-08-05"), "ziman-2026-08-05.csv")

    def test_the_filename_is_ascii(self):
        """It becomes a download name, and a filename with Persian in it is
        one some phone will mangle on the way to a laptop."""
        filename("ziman", "2026-08-05").encode("ascii")


if __name__ == "__main__":
    unittest.main()
