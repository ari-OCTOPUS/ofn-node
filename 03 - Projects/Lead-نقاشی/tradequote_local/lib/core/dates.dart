// Timestamps are stored as **epoch milliseconds UTC** (D-008) and displayed
// in Australian day-first format.
import 'package:intl/intl.dart';

final DateFormat _auDate = DateFormat('dd/MM/yyyy');
final DateFormat _auDateLong = DateFormat('d MMMM yyyy');

int nowMs() => DateTime.now().millisecondsSinceEpoch;

DateTime fromMs(int ms) => DateTime.fromMillisecondsSinceEpoch(ms);

/// `19/07/2026`
String formatAuDate(int ms) => _auDate.format(fromMs(ms));

/// `19 July 2026`
String formatAuDateLong(int ms) => _auDateLong.format(fromMs(ms));

/// Start of today's date plus [days] days, at end-of-day local time — used
/// for due/expiry defaults so "due in 14 days" includes the whole day.
int daysFromNowMs(int days) {
  final now = DateTime.now();
  final d = DateTime(now.year, now.month, now.day + days, 23, 59, 59);
  return d.millisecondsSinceEpoch;
}

/// Whether [ms] is before the start of today (used for overdue derivation).
bool isPastDate(int ms) {
  final now = DateTime.now();
  final startOfToday = DateTime(now.year, now.month, now.day);
  return fromMs(ms).isBefore(startOfToday);
}

/// First instant of the current month (local) in epoch ms.
int startOfCurrentMonthMs() {
  final now = DateTime.now();
  return DateTime(now.year, now.month).millisecondsSinceEpoch;
}
