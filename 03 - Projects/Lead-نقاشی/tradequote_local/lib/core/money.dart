// All persisted money in TradeQuote Local is **integer AUD cents** (D-001).
// Quantities are integer thousandths (`quantityMilli`, 1000 = 1.0).
//
// The arithmetic here is mirrored 1:1 by `tool/validate_financial_logic.py`,
// which was executed with 36 table-driven cases (all passing) because the
// cloud build workspace cannot run Dart. Keep both files in sync.
import 'package:intl/intl.dart';

/// Rounds `a / b` to the nearest integer with **0.5 rounding up**, using pure
/// integer arithmetic. Requires `a >= 0`, `b > 0`.
///
/// This implements the rounding rule of GST Act s 9-90 ("rounded to the
/// nearest cent, rounding 0.5 cents upwards").
int halfUpDiv(int a, int b) {
  assert(a >= 0, 'halfUpDiv requires a >= 0');
  assert(b > 0, 'halfUpDiv requires b > 0');
  return (2 * a + b) ~/ (2 * b);
}

/// Line total in cents for a quantity in thousandths and a unit price in
/// cents: `halfUp(quantityMilli * unitPriceCents / 1000)`.
int lineTotalCents(int quantityMilli, int unitPriceCents) =>
    halfUpDiv(quantityMilli * unitPriceCents, 1000);

class Money {
  Money._();

  // Deliberately not locale-driven: avoids intl locale-data initialisation
  // pitfalls. Produces "$2,750.00" style output, correct for AUD display.
  static final NumberFormat _fmt =
      NumberFormat.currency(symbol: r'$', decimalDigits: 2);

  /// Formats integer cents as `$1,234.56`.
  static String format(int cents) => _fmt.format(cents / 100);

  /// Formats without cents when whole dollars (`$2,500` / `$2,500.50`).
  static String formatCompact(int cents) =>
      cents % 100 == 0 ? _fmt.format(cents ~/ 100).replaceAll('.00', '') : format(cents);

  /// Parses user input such as `2500`, `2,500.50`, `$2500.5` into cents.
  /// Returns null for anything invalid or negative.
  static int? tryParse(String input) {
    final s = input.trim().replaceAll(r'$', '').replaceAll(',', '').trim();
    if (s.isEmpty) return null;
    final match = RegExp(r'^(\d+)(?:\.(\d{1,2}))?$').firstMatch(s);
    if (match == null) return null;
    final dollars = int.tryParse(match.group(1)!);
    if (dollars == null) return null;
    var cents = dollars * 100;
    final frac = match.group(2);
    if (frac != null) {
      cents += frac.length == 1 ? int.parse(frac) * 10 : int.parse(frac);
    }
    return cents;
  }
}

class Quantity {
  Quantity._();

  /// Parses `2`, `2.5`, `0.333` into thousandths (2000, 2500, 333).
  static int? tryParseMilli(String input) {
    final s = input.trim().replaceAll(',', '');
    if (s.isEmpty) return null;
    final match = RegExp(r'^(\d+)(?:\.(\d{1,3}))?$').firstMatch(s);
    if (match == null) return null;
    final whole = int.tryParse(match.group(1)!);
    if (whole == null) return null;
    var milli = whole * 1000;
    final frac = match.group(2);
    if (frac != null) {
      milli += int.parse(frac.padRight(3, '0'));
    }
    return milli;
  }

  /// Formats 2500 → `2.5`, 1000 → `1`, 333 → `0.333`.
  static String format(int quantityMilli) {
    final whole = quantityMilli ~/ 1000;
    final frac = quantityMilli % 1000;
    if (frac == 0) return '$whole';
    var f = frac.toString().padLeft(3, '0');
    while (f.endsWith('0')) {
      f = f.substring(0, f.length - 1);
    }
    return '$whole.$f';
  }
}
