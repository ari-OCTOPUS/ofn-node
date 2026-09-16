import 'dart:io';

import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import '../../core/dates.dart';

part 'database.g.dart';

// ---------------------------------------------------------------------------
// Schema v1 — see docs/architecture/ERD.md and DATA_DICTIONARY.md.
// Conventions: UUID text PKs, epoch-ms ints, enum names as text, money in
// integer cents, quantities in integer thousandths. No hard deletes for
// business records (archive/void instead).
// ---------------------------------------------------------------------------

@DataClassName('CompanySettingsRow')
class CompanySettings extends Table {
  IntColumn get id => integer()(); // always 1 (single row)
  TextColumn get legalName => text().withDefault(const Constant(''))();
  TextColumn get tradingName => text().nullable()();
  TextColumn get abn => text().nullable()(); // normalized 11 digits
  BoolColumn get gstRegistered =>
      boolean().withDefault(const Constant(false))();
  TextColumn get address => text().nullable()();
  TextColumn get phone => text().nullable()();
  TextColumn get email => text().nullable()();
  TextColumn get website => text().nullable()();
  TextColumn get bankAccountName => text().nullable()();
  TextColumn get bsb => text().nullable()();
  TextColumn get accountNumber => text().nullable()();
  TextColumn get paymentInstructions => text().nullable()();
  IntColumn get defaultPaymentTermsDays =>
      integer().withDefault(const Constant(14))();
  IntColumn get defaultQuoteValidityDays =>
      integer().withDefault(const Constant(30))();
  TextColumn get gstMode => text().withDefault(const Constant('inclusive'))();
  TextColumn get quotePrefix => text().withDefault(const Constant('Q-'))();
  TextColumn get invoicePrefix =>
      text().withDefault(const Constant('INV-'))();
  TextColumn get defaultTerms => text().nullable()();
  TextColumn get documentFooter => text().nullable()();
  BoolColumn get onboardingComplete =>
      boolean().withDefault(const Constant(false))();
  IntColumn get createdAt => integer()();
  IntColumn get updatedAt => integer()();

  @override
  Set<Column> get primaryKey => {id};
}

@DataClassName('NumberSequenceRow')
class NumberSequences extends Table {
  TextColumn get id => text()(); // 'quote' | 'invoice'
  IntColumn get nextNumber => integer().withDefault(const Constant(1001))();

  @override
  Set<Column> get primaryKey => {id};
}

@DataClassName('CustomerRow')
class Customers extends Table {
  TextColumn get id => text()();
  BoolColumn get isBusiness => boolean().withDefault(const Constant(false))();
  TextColumn get name => text()();
  TextColumn get contactName => text().nullable()();
  TextColumn get email => text().nullable()();
  TextColumn get mobile => text().nullable()();
  TextColumn get abn => text().nullable()();
  TextColumn get billingAddress => text().nullable()();
  TextColumn get siteAddress => text().nullable()();
  TextColumn get notes => text().nullable()();
  TextColumn get preferredContact => text().nullable()();
  IntColumn get archivedAt => integer().nullable()();
  IntColumn get createdAt => integer()();
  IntColumn get updatedAt => integer()();

  @override
  Set<Column> get primaryKey => {id};
}

@DataClassName('DocumentRow')
class Documents extends Table {
  TextColumn get id => text()();
  TextColumn get docType => text()(); // 'quote' | 'invoice'
  TextColumn get docNumber => text().unique()();
  TextColumn get customerId => text().references(Customers, #id)();
  TextColumn get customerNameCache => text()();
  TextColumn get status => text()(); // DocStatus.name — overdue is derived
  IntColumn get issueDate => integer()();
  IntColumn get expiryDate => integer().nullable()(); // quotes
  IntColumn get dueDate => integer().nullable()(); // invoices
  TextColumn get gstMode => text()(); // inclusive | exclusive | none
  TextColumn get siteAddress => text().nullable()();
  TextColumn get workType => text().nullable()();
  TextColumn get scopeOfWork => text().nullable()();
  TextColumn get terms => text().nullable()();
  TextColumn get customerNotes => text().nullable()();
  TextColumn get internalNotes => text().nullable()();
  IntColumn get subtotalExGstCents =>
      integer().withDefault(const Constant(0))();
  IntColumn get gstCents => integer().withDefault(const Constant(0))();
  IntColumn get totalCents => integer().withDefault(const Constant(0))();
  TextColumn get sourceQuoteId => text().nullable()();
  TextColumn get convertedInvoiceId => text().nullable()();
  IntColumn get sentAt => integer().nullable()(); // manual confirmation only
  IntColumn get voidedAt => integer().nullable()();
  IntColumn get createdAt => integer()();
  IntColumn get updatedAt => integer()();

  @override
  Set<Column> get primaryKey => {id};
}

@DataClassName('LineItemRow')
class LineItems extends Table {
  TextColumn get id => text()();
  TextColumn get documentId =>
      text().references(Documents, #id, onDelete: KeyAction.cascade)();
  IntColumn get position => integer()();
  TextColumn get description => text()();
  IntColumn get quantityMilli => integer().withDefault(const Constant(1000))();
  TextColumn get unitLabel => text().nullable()();
  IntColumn get unitPriceCents => integer()();
  BoolColumn get gstApplicable => boolean().withDefault(const Constant(true))();
  IntColumn get lineTotalCents => integer()();

  @override
  Set<Column> get primaryKey => {id};
}

@DataClassName('SnapshotRow')
class DocumentSnapshots extends Table {
  TextColumn get documentId =>
      text().references(Documents, #id, onDelete: KeyAction.cascade)();
  TextColumn get snapshotJson => text()();
  IntColumn get createdAt => integer()();

  @override
  Set<Column> get primaryKey => {documentId};
}

@DataClassName('PaymentRow')
class Payments extends Table {
  TextColumn get id => text()();
  TextColumn get invoiceId => text().references(Documents, #id)();
  IntColumn get paidAt => integer()();
  IntColumn get amountCents => integer()();
  TextColumn get method => text()(); // PaymentMethod.name
  TextColumn get reference => text().nullable()();
  TextColumn get notes => text().nullable()();
  IntColumn get deletedAt => integer().nullable()(); // soft delete (audit)
  IntColumn get createdAt => integer()();

  @override
  Set<Column> get primaryKey => {id};
}

@DataClassName('ShareEventRow')
class ShareEvents extends Table {
  TextColumn get id => text()();
  TextColumn get documentId =>
      text().references(Documents, #id, onDelete: KeyAction.cascade)();
  TextColumn get channel => text()(); // ShareChannel.name
  TextColumn get outcome => text()(); // ShareOutcome.name — never 'delivered'
  IntColumn get createdAt => integer()();

  @override
  Set<Column> get primaryKey => {id};
}

@DataClassName('AuditEventRow')
class AuditEvents extends Table {
  TextColumn get id => text()();
  TextColumn get entityType => text()();
  TextColumn get entityId => text()();
  TextColumn get action => text()();
  TextColumn get detailsJson => text().nullable()();
  IntColumn get createdAt => integer()();

  @override
  Set<Column> get primaryKey => {id};
}

@DataClassName('MessageTemplateRow')
class MessageTemplates extends Table {
  TextColumn get id => text()(); // 'quote' | 'invoice' | 'reminder'
  TextColumn get subject => text().nullable()(); // email subject template
  TextColumn get body => text()();

  @override
  Set<Column> get primaryKey => {id};
}

@DataClassName('AppMetaRow')
class AppMeta extends Table {
  TextColumn get key => text()();
  TextColumn get value => text()();

  @override
  Set<Column> get primaryKey => {key};
}

// ---------------------------------------------------------------------------

@DriftDatabase(tables: [
  CompanySettings,
  NumberSequences,
  Customers,
  Documents,
  LineItems,
  DocumentSnapshots,
  Payments,
  ShareEvents,
  AuditEvents,
  MessageTemplates,
  AppMeta,
])
class AppDatabase extends _$AppDatabase {
  AppDatabase(super.e);

  static const String dbFileName = 'tradequote.sqlite';

  /// The live database file location (app support dir — private, backed up
  /// only through the in-app backup feature).
  static Future<File> databaseFile() async {
    final dir = await getApplicationSupportDirectory();
    await dir.create(recursive: true);
    return File(p.join(dir.path, dbFileName));
  }

  static Future<AppDatabase> open() async {
    final file = await databaseFile();
    return AppDatabase(NativeDatabase.createInBackground(file));
  }

  @override
  int get schemaVersion => 1;

  @override
  MigrationStrategy get migration => MigrationStrategy(
        onCreate: (m) async {
          await m.createAll();
          await _seedDefaults();
        },
        onUpgrade: (m, from, to) async {
          // Schema v1 is the first release. Future migrations are added here
          // step by step and covered by tests (docs/testing/TEST_PLAN.md).
          // Never a destructive fallback (immutable constraint).
        },
        beforeOpen: (details) async {
          await customStatement('PRAGMA foreign_keys = ON');
        },
      );

  Future<void> _seedDefaults() async {
    final now = nowMs();
    await batch((b) {
      b.insertAll(companySettings, [
        CompanySettingsCompanion.insert(id: 1, createdAt: now, updatedAt: now),
      ]);
      b.insertAll(numberSequences, [
        NumberSequencesCompanion.insert(
            id: 'quote', nextNumber: const Value(1001)),
        NumberSequencesCompanion.insert(
            id: 'invoice', nextNumber: const Value(1001)),
      ]);
      b.insertAll(messageTemplates, [
        MessageTemplatesCompanion.insert(
          id: 'quote',
          subject: const Value('Quote {documentNumber} — {businessName}'),
          body:
              'Hi {customerName}, please find Quote {documentNumber} attached '
              'for the painting work at {siteAddress}. The total is {total}. '
              'Thank you, {businessName}.',
        ),
        MessageTemplatesCompanion.insert(
          id: 'invoice',
          subject: const Value('Invoice {documentNumber} — {businessName}'),
          body:
              'Hi {customerName}, please find Invoice {documentNumber} '
              'attached. The total is {total} and the due date is {dueDate}. '
              'Thank you, {businessName}.',
        ),
        MessageTemplatesCompanion.insert(
          id: 'reminder',
          subject:
              const Value('Reminder: Invoice {documentNumber} — {businessName}'),
          body:
              'Hi {customerName}, this is a friendly reminder that Invoice '
              '{documentNumber} has an outstanding balance of {balance}. '
              'Please let me know if you have any questions. '
              'Thank you, {businessName}.',
        ),
      ]);
      b.insertAll(appMeta, [
        AppMetaCompanion.insert(key: 'backupFormatVersion', value: '1'),
      ]);
    });
  }
}
