#!/usr/bin/env python3
"""Cross-validation of TradeQuote Local financial algorithms.

The Flutter/Dart toolchain cannot run in the cloud workspace (pub.dev and
storage.googleapis.com are firewalled), so the money-critical algorithms are
implemented here in Python with EXACTLY the same integer arithmetic as the
Dart implementation in lib/core/, and executed against table-driven cases.
The same tables are copied into the Dart tests (test/gst_test.dart,
test/abn_test.dart) to be executed on the build machine.

Sources:
- ABN checksum: ABR "Format of the ABN" https://abr.business.gov.au/Help/AbnFormat
  (accessed 2026-07-19)
- GST rounding: GST Act s 9-90 (round to nearest cent, 0.5 up) and ATO
  "Tax invoices" page rounding guidance (accessed 2026-07-19)

All money is integer cents. Quantities are integer thousandths (milli).
Rounding is half-up implemented with pure integer arithmetic:
  half_up(a / b) == (2*a + b) // (2*b)   for a >= 0, b > 0
"""

ABN_WEIGHTS = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]


def abn_normalize(raw: str) -> str:
    return "".join(ch for ch in raw if ch.isdigit())


def abn_is_valid(raw: str) -> bool:
    digits = abn_normalize(raw)
    if len(digits) != 11:
        return False
    if digits[0] == "0":
        return False  # first digit must be 1-9 after ABR rules
    nums = [int(c) for c in digits]
    nums[0] -= 1
    total = sum(d * w for d, w in zip(nums, ABN_WEIGHTS))
    return total % 89 == 0


def half_up_div(a: int, b: int) -> int:
    """Round a/b to nearest integer, 0.5 up. Requires a >= 0, b > 0."""
    assert a >= 0 and b > 0
    return (2 * a + b) // (2 * b)


def line_total_cents(qty_milli: int, unit_price_cents: int) -> int:
    return half_up_div(qty_milli * unit_price_cents, 1000)


def gst_from_exclusive(taxable_ex_cents: int) -> int:
    # 10% GST, rounded half-up to the cent (total method, s 9-90)
    return half_up_div(taxable_ex_cents, 10)


def gst_portion_of_inclusive(taxable_inc_cents: int) -> int:
    # GST component is 1/11 of the GST-inclusive price
    return half_up_div(taxable_inc_cents, 11)


failures = []


def check(name, actual, expected):
    ok = actual == expected
    if not ok:
        failures.append((name, actual, expected))
    print(f"{'PASS' if ok else 'FAIL'}  {name}: got {actual}, expected {expected}")


# ---------------------------------------------------------------- ABN cases
print("== ABN checksum (ABR modulus-89) ==")
check("ABR example 51 824 753 556", abn_is_valid("51 824 753 556"), True)
check("Telstra 33 051 775 556", abn_is_valid("33051775556"), True)
check("ATO 51 824 753 556 with mutation", abn_is_valid("51 824 753 557"), False)
check("Too short", abn_is_valid("5182475355"), False)
check("Letters stripped then invalid length", abn_is_valid("ABN: 51-824-753-55"), False)
check("Valid with punctuation", abn_is_valid("ABN 51 824 753 556"), True)
check("Leading zero invalid", abn_is_valid("01 824 753 556"), False)
check("Empty", abn_is_valid(""), False)

# ---------------------------------------------------------------- rounding
print("== half-up rounding primitive ==")
check("0.5 rounds up (5/10)", half_up_div(5, 10), 1)
check("0.4 rounds down (4/10)", half_up_div(4, 10), 0)
check("2.5 rounds up (25/10)", half_up_div(25, 10), 3)
check("exact (30/10)", half_up_div(30, 10), 3)

# ---------------------------------------------------------------- line totals
print("== line totals (qty milli x unit cents) ==")
check("1 x $2,500.00", line_total_cents(1000, 250000), 250000)
check("2.5 h x $45.00", line_total_cents(2500, 4500), 11250)
check("1.333 x $3.00", line_total_cents(1333, 300), 400)  # 399.9 -> 400
check("0.333 x $1.00", line_total_cents(333, 100), 33)    # 33.3 -> 33
check("3 x $33.33", line_total_cents(3000, 3333), 9999)

# ---------------------------------------------------------------- GST
print("== GST exclusive mode (add 10%) ==")
check("$2,500.00 ex -> GST $250.00", gst_from_exclusive(250000), 25000)
check("$0.05 ex -> GST 1c (0.5 up)", gst_from_exclusive(5), 1)
check("$3.33 ex -> GST 33c", gst_from_exclusive(333), 33)
check("$99.99 ex -> GST $10.00", gst_from_exclusive(9999), 1000)
check("$0.00 ex -> 0", gst_from_exclusive(0), 0)

print("== GST inclusive mode (1/11 of total) ==")
check("$1,100.00 inc -> GST $100.00", gst_portion_of_inclusive(110000), 10000)
check("$82.50 inc -> GST $7.50", gst_portion_of_inclusive(8250), 750)
check("$9.99 inc -> GST 91c", gst_portion_of_inclusive(999), 91)   # 90.818 -> 91
check("$2,750.00 inc -> GST $250.00", gst_portion_of_inclusive(275000), 25000)
check("$0.11 inc -> 1c", gst_portion_of_inclusive(11), 1)
check("$0.05 inc -> 0c", gst_portion_of_inclusive(5), 0)  # 0.4545 -> 0

# ------------------------------------------------- document-level scenarios
print("== document scenarios ==")
# Senior quick-quote: one price $2,500 entered, company mode 'exclusive'
sub = line_total_cents(1000, 250000)
gst = gst_from_exclusive(sub)
check("quick quote ex: total", sub + gst, 275000)
# Same job entered as $2,750 'inclusive'
inc = line_total_cents(1000, 275000)
gsti = gst_portion_of_inclusive(inc)
check("quick quote inc: gst", gsti, 25000)
check("quick quote inc: ex subtotal", inc - gsti, 250000)
# Acceptance-checklist case: $1,100 GST-inclusive quote
inc2 = 110000
check("S23 checklist $1,100 inc GST", gst_portion_of_inclusive(inc2), 10000)
# Mixed lines, exclusive mode: $100 taxable + $50 GST-free
taxable = line_total_cents(1000, 10000)
free = line_total_cents(1000, 5000)
g = gst_from_exclusive(taxable)
check("mixed: gst only on taxable", g, 1000)
check("mixed: grand total", taxable + free + g, 16000)
# Partial payments: invoice $2,750, pay $1,000 then $1,750
balance = 275000 - 100000
check("balance after partial", balance, 175000)
check("paid when zero", balance - 175000, 0)

print()
if failures:
    print(f"RESULT: {len(failures)} FAILURES")
    raise SystemExit(1)
print("RESULT: ALL CASES PASSED")
