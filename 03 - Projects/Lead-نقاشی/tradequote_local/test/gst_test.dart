import 'package:flutter_test/flutter_test.dart';
import 'package:tradequote_local/core/gst.dart';
import 'package:tradequote_local/core/money.dart';
import 'package:tradequote_local/domain/enums.dart';

/// Table-driven GST tests. EVERY case here was executed and verified in
/// tool/validate_financial_logic.py (36/36 PASS on 2026-07-19) — the Dart
/// implementation must produce identical results. If you change one file,
/// change both.
void main() {
  group('halfUpDiv (GST Act s 9-90 rounding: nearest cent, 0.5 up)', () {
    test('0.5 rounds up', () => expect(halfUpDiv(5, 10), 1));
    test('0.4 rounds down', () => expect(halfUpDiv(4, 10), 0));
    test('2.5 rounds up', () => expect(halfUpDiv(25, 10), 3));
    test('exact division', () => expect(halfUpDiv(30, 10), 3));
  });

  group('line totals (quantityMilli x unitPriceCents)', () {
    const cases = [
      (1000, 250000, 250000, '1 x \$2,500.00'),
      (2500, 4500, 11250, '2.5 h x \$45.00'),
      (1333, 300, 400, '1.333 x \$3.00 -> 399.9 -> 400'),
      (333, 100, 33, '0.333 x \$1.00 -> 33.3 -> 33'),
      (3000, 3333, 9999, '3 x \$33.33'),
    ];
    for (final (qty, price, expected, label) in cases) {
      test(label, () => expect(lineTotalCents(qty, price), expected));
    }
  });

  group('GST exclusive mode (10% added)', () {
    const cases = [
      (250000, 25000, '\$2,500.00 ex -> GST \$250.00'),
      (5, 1, '\$0.05 ex -> 1c (0.5 up)'),
      (333, 33, '\$3.33 ex -> 33c'),
      (9999, 1000, '\$99.99 ex -> \$10.00'),
      (0, 0, 'zero'),
    ];
    for (final (ex, gst, label) in cases) {
      test(label, () {
        final t = GstCalculator.compute(GstMode.exclusive,
            [GstLine(quantityMilli: 1000, unitPriceCents: ex)]);
        expect(t.gstCents, gst);
        expect(t.subtotalExGstCents, ex);
        expect(t.totalCents, ex + gst);
      });
    }
  });

  group('GST inclusive mode (1/11 of total)', () {
    const cases = [
      (110000, 10000, '\$1,100.00 inc -> GST \$100.00'),
      (8250, 750, '\$82.50 inc -> GST \$7.50'),
      (999, 91, '\$9.99 inc -> 91c (90.818 -> 91)'),
      (275000, 25000, '\$2,750.00 inc -> GST \$250.00'),
      (11, 1, '\$0.11 inc -> 1c'),
      (5, 0, '\$0.05 inc -> 0c (0.4545 -> 0)'),
    ];
    for (final (inc, gst, label) in cases) {
      test(label, () {
        final t = GstCalculator.compute(GstMode.inclusive,
            [GstLine(quantityMilli: 1000, unitPriceCents: inc)]);
        expect(t.gstCents, gst);
        expect(t.totalCents, inc);
        expect(t.subtotalExGstCents, inc - gst);
      });
    }
  });

  group('document scenarios', () {
    test('senior quick quote, exclusive: \$2,500 -> total \$2,750', () {
      final t = GstCalculator.compute(GstMode.exclusive,
          [const GstLine(quantityMilli: 1000, unitPriceCents: 250000)]);
      expect(t.totalCents, 275000);
    });

    test('S23 FE acceptance case: \$1,100 GST-inclusive quote', () {
      final t = GstCalculator.compute(GstMode.inclusive,
          [const GstLine(quantityMilli: 1000, unitPriceCents: 110000)]);
      expect(t.gstCents, 10000);
      expect(t.subtotalExGstCents, 100000);
    });

    test('mixed lines: GST only on taxable subset (exclusive)', () {
      final t = GstCalculator.compute(GstMode.exclusive, const [
        GstLine(quantityMilli: 1000, unitPriceCents: 10000),
        GstLine(
            quantityMilli: 1000, unitPriceCents: 5000, gstApplicable: false),
      ]);
      expect(t.gstCents, 1000);
      expect(t.totalCents, 16000);
    });

    test('not GST registered: no GST regardless of lines', () {
      final t = GstCalculator.compute(GstMode.none,
          [const GstLine(quantityMilli: 1000, unitPriceCents: 123456)]);
      expect(t.gstCents, 0);
      expect(t.totalCents, 123456);
    });

    test('empty document totals are zero', () {
      final t = GstCalculator.compute(GstMode.inclusive, const []);
      expect(t.totalCents, 0);
      expect(t.gstCents, 0);
    });
  });
}
