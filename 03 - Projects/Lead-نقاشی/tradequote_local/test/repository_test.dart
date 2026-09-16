import 'package:drift/drift.dart' show Value;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tradequote_local/core/errors.dart';
import 'package:tradequote_local/data/db/database.dart';
import 'package:tradequote_local/data/repositories/customer_repository.dart';
import 'package:tradequote_local/data/repositories/document_repository.dart';
import 'package:tradequote_local/data/repositories/payment_repository.dart';
import 'package:tradequote_local/data/repositories/settings_repository.dart';
import 'package:tradequote_local/domain/enums.dart';

/// Database + business-rule tests on an in-memory SQLite database.
/// NOTE: requires a loadable sqlite3 library on the machine running
/// `flutter test` (bundled automatically on macOS/Linux; on Windows see
/// docs/testing/TEST_PLAN.md §Environment).
void main() {
  late AppDatabase db;
  late SettingsRepository settings;
  late CustomerRepository customers;
  late DocumentRepository docs;
  late PaymentRepository payments;

  setUp(() async {
    db = AppDatabase(NativeDatabase.memory());
    settings = SettingsRepository(db);
    customers = CustomerRepository(db);
    docs = DocumentRepository(db);
    payments = PaymentRepository(db);
    // Company profile for a GST-registered business, inclusive pricing.
    await settings.save(const CompanySettingsCompanion(
      legalName: Value('Test Painting Pty Ltd'),
      abn: Value('51824753556'),
      gstRegistered: Value(true),
      gstMode: Value('inclusive'),
      onboardingComplete: Value(true),
    ));
  });

  tearDown(() async => db.close());

  Future<DocumentRow> makeQuoteWithLines(CustomerRow c,
      {int priceCents = 275000}) async {
    final quote = await docs.createDraft(type: DocType.quote, customer: c);
    await docs.updateDraft(id: quote.id, lines: [
      DraftLineInput(
          description: 'Painting work', unitPriceCents: priceCents),
    ]);
    return (await docs.byId(quote.id))!;
  }

  group('seeding and numbering', () {
    test('settings row and sequences are seeded on create', () async {
      final row = await settings.get();
      expect(row.legalName, 'Test Painting Pty Ltd');
      final t = await settings.template('quote');
      expect(t, isNotNull);
    });

    test('numbers allocate sequentially per type with prefixes', () async {
      final c = await customers.quickCreate(name: 'John Smith');
      final q1 = await docs.createDraft(type: DocType.quote, customer: c);
      final q2 = await docs.createDraft(type: DocType.quote, customer: c);
      final i1 = await docs.createDraft(type: DocType.invoice, customer: c);
      expect(q1.docNumber, 'Q-1001');
      expect(q2.docNumber, 'Q-1002');
      expect(i1.docNumber, 'INV-1001');
    });

    test('deleting a draft leaves a number gap (never reused)', () async {
      final c = await customers.quickCreate(name: 'Jane');
      final q1 = await docs.createDraft(type: DocType.quote, customer: c);
      await docs.deleteDraft(q1.id);
      final q2 = await docs.createDraft(type: DocType.quote, customer: c);
      expect(q2.docNumber, 'Q-1002');
    });
  });

  group('draft totals (inclusive company default)', () {
    test('single line \$2,750 inc -> GST \$250', () async {
      final c = await customers.quickCreate(name: 'John');
      final q = await makeQuoteWithLines(c);
      expect(q.totalCents, 275000);
      expect(q.gstCents, 25000);
      expect(q.subtotalExGstCents, 250000);
    });

    test('gst mode change without touching lines recomputes', () async {
      final c = await customers.quickCreate(name: 'John');
      final q = await makeQuoteWithLines(c, priceCents: 250000);
      await docs.updateDraft(id: q.id, gstMode: GstMode.exclusive);
      final updated = (await docs.byId(q.id))!;
      expect(updated.gstCents, 25000);
      expect(updated.totalCents, 275000);
    });
  });

  group('issue freezes a snapshot (invariant 2)', () {
    test('later edits to customer/settings never change issued data',
        () async {
      final c = await customers.quickCreate(name: 'Original Customer');
      final q = await makeQuoteWithLines(c);
      await docs.markIssued(q.id, confirmedSent: true);

      // Mutate the master records afterwards.
      await customers.saveEdits(
          c.id, const CustomersCompanion(name: Value('RENAMED')));
      await settings.save(const CompanySettingsCompanion(
          legalName: Value('RENAMED PTY LTD')));

      final render = await docs.renderDataFor(q.id);
      expect(render.customer.name, 'Original Customer');
      expect(render.supplier.legalName, 'Test Painting Pty Ltd');
      expect(render.totalCents, 275000);
      expect(render.recomputeTotals().gstCents, render.gstCents,
          reason: 'snapshot must be internally consistent');
    });

    test('issued documents refuse content edits', () async {
      final c = await customers.quickCreate(name: 'John');
      final q = await makeQuoteWithLines(c);
      await docs.markIssued(q.id);
      expect(
        () => docs.updateDraft(id: q.id, scopeOfWork: 'changed'),
        throwsA(isA<AppException>()),
      );
    });
  });

  group('quote -> invoice conversion (invariant 4)', () {
    test('accepted quote converts once, preserving quote and totals',
        () async {
      final c = await customers.quickCreate(name: 'John');
      final q = await makeQuoteWithLines(c);
      await docs.markIssued(q.id, confirmedSent: true);
      await docs.acceptQuote(q.id);

      final invoice = await docs.convertQuoteToInvoice(q.id);
      expect(invoice.docType, DocType.invoice.name);
      expect(invoice.docNumber, 'INV-1001');
      expect(invoice.status, DocStatus.issued.name);
      expect(invoice.totalCents, 275000);
      expect(invoice.sourceQuoteId, q.id);

      final quoteAfter = (await docs.byId(q.id))!;
      expect(quoteAfter.docType, DocType.quote.name,
          reason: 'quote must never mutate into an invoice');
      expect(quoteAfter.status, DocStatus.accepted.name);
      expect(quoteAfter.convertedInvoiceId, invoice.id);

      final invoiceLines = await docs.linesFor(invoice.id);
      expect(invoiceLines, hasLength(1));
      expect(invoiceLines.first.lineTotalCents, 275000);

      // Double conversion is blocked.
      expect(() => docs.convertQuoteToInvoice(q.id),
          throwsA(isA<AppException>()));
    });

    test('declined quote cannot be converted', () async {
      final c = await customers.quickCreate(name: 'John');
      final q = await makeQuoteWithLines(c);
      await docs.markIssued(q.id);
      await docs.declineQuote(q.id);
      expect(() => docs.convertQuoteToInvoice(q.id, force: true),
          throwsA(isA<AppException>()));
    });
  });

  group('payments (invariant 5, D-007)', () {
    Future<DocumentRow> issuedInvoice() async {
      final c = await customers.quickCreate(name: 'John');
      final q = await makeQuoteWithLines(c);
      await docs.markIssued(q.id);
      await docs.acceptQuote(q.id);
      return docs.convertQuoteToInvoice(q.id);
    }

    test('partial then final payment: partiallyPaid -> paid', () async {
      final inv = await issuedInvoice();
      await payments.record(
        invoiceId: inv.id,
        paidAtMs: DateTime.now().millisecondsSinceEpoch,
        amountCents: 100000,
        method: PaymentMethod.bankTransfer,
      );
      var detail = await docs.getDetail(inv.id);
      expect(detail.status, DocStatus.partiallyPaid);
      expect(detail.balanceCents, 175000);

      await payments.record(
        invoiceId: inv.id,
        paidAtMs: DateTime.now().millisecondsSinceEpoch,
        amountCents: 175000,
        method: PaymentMethod.cash,
      );
      detail = await docs.getDetail(inv.id);
      expect(detail.status, DocStatus.paid);
      expect(detail.balanceCents, 0);
    });

    test('overpayment is blocked with the remaining balance', () async {
      final inv = await issuedInvoice();
      expect(
        () => payments.record(
          invoiceId: inv.id,
          paidAtMs: DateTime.now().millisecondsSinceEpoch,
          amountCents: 275001,
          method: PaymentMethod.cash,
        ),
        throwsA(isA<OverpaymentException>()),
      );
    });

    test('reversing a payment rolls the status back', () async {
      final inv = await issuedInvoice();
      await payments.record(
        invoiceId: inv.id,
        paidAtMs: DateTime.now().millisecondsSinceEpoch,
        amountCents: 275000,
        method: PaymentMethod.card,
      );
      var detail = await docs.getDetail(inv.id);
      expect(detail.status, DocStatus.paid);

      await payments.reverse(detail.payments.single.id);
      detail = await docs.getDetail(inv.id);
      expect(detail.status, DocStatus.issued);
      expect(detail.balanceCents, 275000);
    });

    test('payments cannot attach to quotes or drafts', () async {
      final c = await customers.quickCreate(name: 'John');
      final q = await makeQuoteWithLines(c);
      expect(
        () => payments.record(
          invoiceId: q.id,
          paidAtMs: DateTime.now().millisecondsSinceEpoch,
          amountCents: 100,
          method: PaymentMethod.cash,
        ),
        throwsA(isA<PaymentException>()),
      );
    });
  });

  group('void and delete rules', () {
    test('paid invoices cannot be voided; open ones can', () async {
      final c = await customers.quickCreate(name: 'John');
      final q = await makeQuoteWithLines(c);
      await docs.markIssued(q.id);
      await docs.acceptQuote(q.id);
      final inv = await docs.convertQuoteToInvoice(q.id);

      await payments.record(
        invoiceId: inv.id,
        paidAtMs: DateTime.now().millisecondsSinceEpoch,
        amountCents: 275000,
        method: PaymentMethod.cash,
      );
      expect(() => docs.voidInvoice(inv.id), throwsA(isA<AppException>()));

      final detail = await docs.getDetail(inv.id);
      await payments.reverse(detail.payments.single.id);
      await docs.voidInvoice(inv.id, reason: 'test');
      final after = (await docs.byId(inv.id))!;
      expect(after.status, DocStatus.voided.name);
      expect(after.voidedAt, isNotNull);
    });

    test('issued documents cannot be deleted', () async {
      final c = await customers.quickCreate(name: 'John');
      final q = await makeQuoteWithLines(c);
      await docs.markIssued(q.id);
      expect(() => docs.deleteDraft(q.id), throwsA(isA<AppException>()));
    });
  });

  group('customer archiving', () {
    test('archive hides from default list but keeps documents', () async {
      final c = await customers.quickCreate(name: 'Archie');
      await makeQuoteWithLines(c);
      await customers.archive(c.id);
      expect(await customers.hasDocuments(c.id), isTrue);
      final active = await customers.watchAll().first;
      expect(active.where((x) => x.id == c.id), isEmpty);
      final all = await customers.watchAll(includeArchived: true).first;
      expect(all.where((x) => x.id == c.id), isNotEmpty);
    });
  });
}
