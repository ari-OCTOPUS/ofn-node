"""Her pieces, as a file she can open.

Three details decide whether this is useful or infuriating, and all three are
about the program on the other end rather than about us.

**A byte-order mark.** Excel on Windows reads a CSV without one as the local
codepage, so every Persian字 becomes mojibake. The BOM is three bytes that
turn "the export is broken" into "the export works".

**Latin digits.** The interface shows ۱۲۵ because she reads it. A spreadsheet
shown ۱۲۵ stores text, and text does not add up — the column looks right and
the total is zero. Numerals are a display choice everywhere except here.

**No tax column.** Until `business.gst_registered` is answered, no figure in
this file may claim to be net of tax. A column headed "after GST" computed
from an unanswered question is a number with a name that makes it look
settled, and it is the one column somebody would paste into a tax return.

`csv` and `io` are stdlib and this is an adapter, so both are allowed here —
the kernel decides nothing about file formats.
"""

from __future__ import annotations

import csv
import io
from typing import Iterable, Sequence

# Persian and Arabic-Indic, to Latin. The reverse of what the shell does on
# the way in, applied on the way out for a different reader.
_TO_LATIN = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

BOM = "﻿"

# Deliberately not every column. An export is a thing somebody reads, and a
# row of twenty fields is a row nobody reads. `cogs_aud` is included and
# named as cost, `margin` is not — see `FORBIDDEN_HEADINGS`.
COLUMNS: Sequence[tuple[str, str]] = (
    ("sku", "کد"),
    ("name", "نام"),
    ("state", "وضعیت"),
    ("materials_cost_aud", "مواد"),
    ("packaging_cost_aud", "بسته‌بندی"),
    ("cogs_aud", "خرج"),
    ("price_primary_aud", "قیمت"),
    ("price_secondary_aud", "کمترین قیمت"),
    ("channel", "کانال"),
    ("listed_at", "تاریخ عرضه"),
    ("sold_at", "تاریخ فروش"),
    ("created_at", "ساخته شد"),
)

# Anything that would claim a tax position. Asserted by a test rather than
# merely avoided, because the column that appears by accident is the one
# somebody pastes into a return.
FORBIDDEN_HEADINGS = ("gst", "tax", "مالیات", "net", "خالص", "سود")


def _latin(value: object) -> str:
    if value is None:
        return ""
    return str(value).translate(_TO_LATIN)


def to_csv(products: Iterable[object], *,
           include_archived: bool = False) -> str:
    """The text of the file, BOM included.

    Returns text rather than writing it: what to do with it — a download, a
    file, an attachment — is the caller's decision, and this module has no
    business having an opinion about the filesystem.
    """
    buf = io.StringIO()
    # `\r\n` because that is what a spreadsheet expects, and QUOTE_MINIMAL
    # because a name containing a comma is a name, not a new column.
    writer = csv.writer(buf, lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)
    writer.writerow([label for _, label in COLUMNS])
    for piece in products:
        if not include_archived and getattr(piece, "archived_at", None):
            continue
        writer.writerow([_latin(getattr(piece, field, ""))
                         for field, _ in COLUMNS])
    return BOM + buf.getvalue()


def filename(tenant: str, today: str) -> str:
    """A name that sorts by date and says which business it came from.

    ASCII on purpose: this ends up as a download name, and a filename with
    Persian in it is one that some phone will mangle on the way to a laptop.
    """
    return f"{tenant}-{today}.csv"
