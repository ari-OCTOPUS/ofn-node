import 'package:drift/drift.dart';

import '../../core/dates.dart';
import '../../core/errors.dart';
import '../../core/ids.dart';
import '../../domain/enums.dart';
import '../db/database.dart';

/// Local payment records — no payment processing (constraint). Partial and
/// multiple payments supported; overpayment blocked (D-007); status roll-up
/// happens in the same transaction (invariant 5).
class PaymentRepository {
  PaymentRepository(this._db);

  final AppDatabase _db;

  Stream<List<PaymentRow>> watchForInvoice(String invoiceId) {
    final q = _db.select(_db.payments)
      ..where((t) => t.invoiceId.equals(invoiceId) & t.deletedAt.isNull())
      ..orderBy([(t) => OrderingTerm.desc(t.paidAt)]);
    return q.watch();
  }

  /// Payments received in the current month (dashboard "cash received").
  Stream<List<PaymentRow>> watchThisMonth() {
    final start = startOfCurrentMonthMs();
    final q = _db.select(_db.payments)
      ..where(
          (t) => t.deletedAt.isNull() & t.paidAt.isBiggerOrEqualValue(start));
    return q.watch();
  }

  Future<int> paidSum(String invoiceId) async {
    final rows = await (_db.select(_db.payments)
          ..where((t) => t.invoiceId.equals(invoiceId) & t.deletedAt.isNull()))
        .get();
    return rows.fold<int>(0, (t, x) => t + x.amountCents);
  }

  Future<void> record({
    required String invoiceId,
    required int paidAtMs,
    required int amountCents,
    required PaymentMethod method,
    String? reference,
    String? notes,
  }) {
    return _db.transaction(() async {
      final doc = await (_db.select(_db.documents)
            ..where((t) => t.id.equals(invoiceId)))
          .getSingleOrNull();
      if (doc == null || DocType.fromName(doc.docType) != DocType.invoice) {
        throw const PaymentException('Payments can only be added to invoices.');
      }
      final status = DocStatus.fromName(doc.status);
      if (!status.isOpenInvoice) {
        throw PaymentException(
            'This invoice cannot receive payments (${status.label.toLowerCase()}).');
      }
      if (amountCents <= 0) {
        throw const PaymentException('Enter an amount greater than zero.');
      }
      final alreadyPaid = await paidSum(invoiceId);
      final balance = doc.totalCents - alreadyPaid;
      if (amountCents > balance) {
        throw OverpaymentException(balance);
      }

      await _db.into(_db.payments).insert(PaymentsCompanion.insert(
            id: newId(),
            invoiceId: invoiceId,
            paidAt: paidAtMs,
            amountCents: amountCents,
            method: method.name,
            reference: Value(_nullIfBlank(reference)),
            notes: Value(_nullIfBlank(notes)),
            createdAt: nowMs(),
          ));

      final newPaid = alreadyPaid + amountCents;
      final newStatus = newPaid >= doc.totalCents
          ? DocStatus.paid
          : DocStatus.partiallyPaid;
      await (_db.update(_db.documents)..where((t) => t.id.equals(invoiceId)))
          .write(DocumentsCompanion(
        status: Value(newStatus.name),
        updatedAt: Value(nowMs()),
      ));
      await _audit(invoiceId, 'paymentRecorded',
          'amountCents=$amountCents method=${method.name}');
    });
  }

  /// Soft-deletes a mistaken payment and rolls the invoice status back.
  Future<void> reverse(String paymentId) {
    return _db.transaction(() async {
      final payment = await (_db.select(_db.payments)
            ..where((t) => t.id.equals(paymentId)))
          .getSingleOrNull();
      if (payment == null || payment.deletedAt != null) return;
      await (_db.update(_db.payments)..where((t) => t.id.equals(paymentId)))
          .write(PaymentsCompanion(deletedAt: Value(nowMs())));

      final doc = await (_db.select(_db.documents)
            ..where((t) => t.id.equals(payment.invoiceId)))
          .getSingle();
      final paid = await paidSum(payment.invoiceId);
      final current = DocStatus.fromName(doc.status);
      // Only adjust payment-derived statuses; a voided invoice stays voided.
      if (current == DocStatus.paid ||
          current == DocStatus.partiallyPaid ||
          current == DocStatus.issued) {
        final newStatus = paid == 0
            ? DocStatus.issued
            : (paid >= doc.totalCents ? DocStatus.paid : DocStatus.partiallyPaid);
        await (_db.update(_db.documents)
              ..where((t) => t.id.equals(payment.invoiceId)))
            .write(DocumentsCompanion(
          status: Value(newStatus.name),
          updatedAt: Value(nowMs()),
        ));
      }
      await _audit(payment.invoiceId, 'paymentReversed',
          'paymentId=$paymentId amountCents=${payment.amountCents}');
    });
  }

  Future<void> _audit(String invoiceId, String action, String details) async {
    await _db.into(_db.auditEvents).insert(AuditEventsCompanion.insert(
          id: newId(),
          entityType: 'invoice',
          entityId: invoiceId,
          action: action,
          detailsJson: Value(details),
          createdAt: nowMs(),
        ));
  }

  String? _nullIfBlank(String? s) {
    final t = s?.trim();
    return (t == null || t.isEmpty) ? null : t;
  }
}
