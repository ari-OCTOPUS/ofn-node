/// ABN validation per the Australian Business Register checksum
/// (https://abr.business.gov.au/Help/AbnFormat, accessed 2026-07-19).
///
/// Algorithm: subtract 1 from the first digit, multiply the 11 digits by the
/// weighting factors (10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19), sum, and the
/// total must be divisible by 89. Validated by execution in
/// tool/validate_financial_logic.py against the ABR worked example
/// 51 824 753 556 and known real ABNs.
library;

const List<int> _abnWeights = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19];

class Abn {
  Abn._();

  /// Strips everything except digits.
  static String normalize(String raw) =>
      raw.replaceAll(RegExp(r'[^0-9]'), '');

  /// True when [raw] contains a checksum-valid 11-digit ABN.
  static bool isValid(String raw) {
    final digits = normalize(raw);
    if (digits.length != 11) return false;
    if (digits.codeUnitAt(0) == 0x30) return false; // first digit can't be 0
    var total = 0;
    for (var i = 0; i < 11; i++) {
      var d = digits.codeUnitAt(i) - 0x30;
      if (i == 0) d -= 1;
      total += d * _abnWeights[i];
    }
    return total % 89 == 0;
  }

  /// Formats a normalized ABN for display: `51 824 753 556`.
  /// Returns the input unchanged if it is not 11 digits.
  static String format(String raw) {
    final d = normalize(raw);
    if (d.length != 11) return raw;
    return '${d.substring(0, 2)} ${d.substring(2, 5)} '
        '${d.substring(5, 8)} ${d.substring(8, 11)}';
  }
}
