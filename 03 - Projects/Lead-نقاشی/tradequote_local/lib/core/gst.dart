import '../domain/enums.dart';
import 'money.dart';

/// GST engine — total-invoice method per GST Act s 9-90 (D-003).
///
/// - `exclusive`: prices entered are ex-GST; GST = halfUp(taxableSubtotal/10).
/// - `inclusive`: prices entered include GST; GST portion =
///   halfUp(taxableTotal/11); ex-GST subtotal = total − GST.
/// - `none`: business not registered for GST — no GST is calculated and
///   documents are titled "Invoice", never "Tax Invoice".
///
/// Mirrored and executed in tool/validate_financial_logic.py (all cases pass).
class GstLine {
  const GstLine({
    required this.quantityMilli,
    required this.unitPriceCents,
    this.gstApplicable = true,
  })  : assert(quantityMilli >= 0),
        assert(unitPriceCents >= 0);

  final int quantityMilli;
  final int unitPriceCents;
  final bool gstApplicable;

  int get totalCents => lineTotalCents(quantityMilli, unitPriceCents);
}

class DocumentTotals {
  const DocumentTotals({
    required this.subtotalExGstCents,
    required this.gstCents,
    required this.totalCents,
  });

  final int subtotalExGstCents;
  final int gstCents;
  final int totalCents;

  @override
  String toString() =>
      'DocumentTotals(ex: $subtotalExGstCents, gst: $gstCents, total: $totalCents)';
}

class GstCalculator {
  GstCalculator._();

  static DocumentTotals compute(GstMode mode, List<GstLine> lines) {
    var sum = 0;
    var taxable = 0;
    for (final line in lines) {
      final t = line.totalCents;
      sum += t;
      if (line.gstApplicable) taxable += t;
    }
    switch (mode) {
      case GstMode.exclusive:
        final gst = taxable == 0 ? 0 : halfUpDiv(taxable, 10);
        return DocumentTotals(
          subtotalExGstCents: sum,
          gstCents: gst,
          totalCents: sum + gst,
        );
      case GstMode.inclusive:
        final gst = taxable == 0 ? 0 : halfUpDiv(taxable, 11);
        return DocumentTotals(
          subtotalExGstCents: sum - gst,
          gstCents: gst,
          totalCents: sum,
        );
      case GstMode.none:
        return DocumentTotals(
          subtotalExGstCents: sum,
          gstCents: 0,
          totalCents: sum,
        );
    }
  }
}
