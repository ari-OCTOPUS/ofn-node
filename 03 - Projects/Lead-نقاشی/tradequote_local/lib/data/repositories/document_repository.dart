import 'dart:convert';

import 'package:drift/drift.dart';

import '../../core/dates.dart';
import '../../core/errors.dart';
import '../../core/gst.dart';
import '../../core/ids.dart';
import '../../domain/enums.dart';
import '../../domain/render_data.dart';
import '../db/database.dart';

/// Input for a draft line item coming from the UI.
class DraftLineInput {
  const DraftLineInput({
    required this.description,
    this.quantityMilli = 1000,
    this.unitLabel,
    required this.unitPriceCents,
    this.gstApplicable = true,
  });

  final String description;
  final int quantityMilli;
  final String? unitLabel;
  final int unitPriceCents;
  final bool gstApplicable;
}

/// Everything a detail screen needs, loaded in one call.
class DocumentDetail {
  const DocumentDetail({
    required this.doc,
    required this.lines,
    required this.payments,
    required this.paidCents,
    required this.balanceCents,
    required this.isOverdue,
    required this.hasSnapshot,
  });

  final DocumentRow doc;
  final List<LineItemRow> lines;
  final List<PaymentRow> payments;
  final int paidCents;
  final int balanceCents;
  final bool isOverdue;
  final bool hasSnapshot;

  DocStatus get status => DocStatus.fromName(doc.status);
  DocType get type => DocType.fromName(doc.docType);
}

/// Owns every document invariant: transactional numbering (D-004),
/// snapshot-on-issue (invariant 2), conversion (invariant 4), honest share
/// events (invariant 6). See docs/architecture/DOCUMENT_LIFECYCLE.md.
class DocumentRepository {
  DocumentRepository(this._db);

  final AppDatabase _db;

  // ---------------------------------------------------------------- create

  /// Creates a draft with an allocated number in ONE transaction.
  Future<DocumentRow> createDraft({
    required DocType type,
    required CustomerRow customer,
  }) {
    return _db.transaction(() async {
      final settings = await (_db.select(_db.companySettings)
            ..where((t) => t.id.equals(1)))
          .getSingle();
      final number = await _allocateNumber(type, settings);
      final now = nowMs();
      final gstMode = settings.gstRegistered
          ? GstMode.fromName(settings.gstMode)
          : GstMode.none;
      final row = DocumentRow(
        id: newId(),
        docType: type.name,
        docNumber: number,
        customerId: customer.id,
        customerNameCache: customer.name,
        status: DocStatus.draft.name,
        issueDate: now,
        expiryDate: type == DocType.quote
            ? daysFromNowMs(settings.defaultQuoteValidityDays)
            : null,
        dueDate: type == DocType.invoice
            ? daysFromNowMs(settings.defaultPaymentTermsDays)
            : null,
        gstMode: gstMode.name,
        siteAddress: customer.siteAddress,
        workType: null,
        scopeOfWork: null,
        terms: settings.defaultTerms,
        customerNotes: null,
        internalNotes: null,
        subtotalExGstCents: 0,
        gstCents: 0,
        totalCents: 0,
        sourceQuoteId: null,
        convertedInvoiceId: null,
        sentAt: null,
        voidedAt: null,
        createdAt: now,
        updatedAt: now,
      );
      await _db.into(_db.documents).insert(row);
      await _audit('document', row.id, 'created', {'number': number});
      return row;
    });
  }

  Future<String> _allocateNumber(
      DocType type, CompanySettingsRow settings) async {
    final seqId = type.name;
    final seq = await (_db.select(_db.numberSequences)
          ..where((t) => t.id.equals(seqId)))
        .getSingle();
    await (_db.update(_db.numberSequences)..where((t) => t.id.equals(seqId)))
        .write(NumberSequencesCompanion(nextNumber: Value(seq.nextNumber + 1)));
    final prefix =
        type == DocType.quote ? settings.quotePrefix : settings.invoicePrefix;
    return '$prefix${seq.nextNumber}';
  }

  // ------------------------------------------------------------------ read

  Future<DocumentRow?> byId(String id) =>
      (_db.select(_db.documents)..where((t) => t.id.equals(id)))
          .getSingleOrNull();

  Stream<DocumentRow?> watchById(String id) =>
      (_db.select(_db.documents)..where((t) => t.id.equals(id)))
          .watchSingleOrNull();

  Future<List<LineItemRow>> linesFor(String documentId) =>
      (_db.select(_db.lineItems)
            ..where((t) => t.documentId.equals(documentId))
            ..orderBy([(t) => OrderingTerm.asc(t.position)]))
          .get();

  Future<DocumentDetail> getDetail(String id) async {
    final doc = await byId(id);
    if (doc == null) {
      throw const AppException('This document could not be found.');
    }
    final lines = await linesFor(id);
    final payments = await (_db.select(_db.payments)
          ..where((t) => t.invoiceId.equals(id) & t.deletedAt.isNull())
          ..orderBy([(t) => OrderingTerm.desc(t.paidAt)]))
        .get();
    final paid = payments.fold<int>(0, (t, x) => t + x.amountCents);
    final balance = doc.totalCents - paid;
    final status = DocStatus.fromName(doc.status);
    final overdue = status.isOpenInvoice &&
        doc.dueDate != null &&
        isPastDate(doc.dueDate!) &&
        balance > 0;
    final snap = await (_db.select(_db.documentSnapshots)
          ..where((t) => t.documentId.equals(id)))
        .getSingleOrNull();
    return DocumentDetail(
      doc: doc,
      lines: lines,
      payments: payments,
      paidCents: paid,
      balanceCents: balance,
      isOverdue: overdue,
      hasSnapshot: snap != null,
    );
  }

  /// Payments/lines updates always bump documents.updatedAt inside the same
  /// transaction, so watching the row is a sufficient refresh trigger.
  Stream<DocumentDetail?> watchDetail(String id) =>
      watchById(id).asyncMap((doc) async {
        if (doc == null) return null;
        return getDetail(id);
      });

  // ---------------------------------------------------------------- update

  /// Draft-only content update; replaces lines and recomputes totals.
  Future<void> updateDraft({
    required String id,
    String? scopeOfWork,
    String? siteAddress,
    String? workType,
    GstMode? gstMode,
    int? issueDate,
    int? expiryDate,
    int? dueDate,
    String? terms,
    String? customerNotes,
    String? internalNotes,
    List<DraftLineInput>? lines,
  }) {
    return _db.transaction(() async {
      final doc = await byId(id);
      if (doc == null) {
        throw const AppException('This document could not be found.');
      }
      if (!DocStatus.fromName(doc.status).isDraft) {
        throw const AppException(
            'This document has been issued and can no longer be edited. '
            'You can duplicate it to make a new one.');
      }
      final mode = gstMode ?? GstMode.fromName(doc.gstMode);

      var patch = DocumentsCompanion(
        scopeOfWork: scopeOfWork == null ? const Value.absent() : Value(scopeOfWork),
        siteAddress: siteAddress == null ? const Value.absent() : Value(siteAddress),
        workType: workType == null ? const Value.absent() : Value(workType),
        gstMode: Value(mode.name),
        issueDate: issueDate == null ? const Value.absent() : Value(issueDate),
        expiryDate: expiryDate == null ? const Value.absent() : Value(expiryDate),
        dueDate: dueDate == null ? const Value.absent() : Value(dueDate),
        terms: terms == null ? const Value.absent() : Value(terms),
        customerNotes:
            customerNotes == null ? const Value.absent() : Value(customerNotes),
        internalNotes:
            internalNotes == null ? const Value.absent() : Value(internalNotes),
        updatedAt: Value(nowMs()),
      );

      if (lines != null) {
        await (_db.delete(_db.lineItems)
              ..where((t) => t.documentId.equals(id)))
            .go();
        var position = 0;
        final gstLines = <GstLine>[];
        for (final line in lines) {
          final total = GstLine(
            quantityMilli: line.quantityMilli,
            unitPriceCents: line.unitPriceCents,
            gstApplicable: line.gstApplicable,
          );
          gstLines.add(total);
          await _db.into(_db.lineItems).insert(LineItemsCompanion.insert(
                id: newId(),
                documentId: id,
                position: position++,
                description: line.description,
                quantityMilli: Value(line.quantityMilli),
                unitLabel: Value(line.unitLabel),
                unitPriceCents: line.unitPriceCents,
                gstApplicable: Value(line.gstApplicable),
                lineTotalCents: total.totalCents,
              ));
        }
        final totals = GstCalculator.compute(mode, gstLines);
        patch = patch.copyWith(
          subtotalExGstCents: Value(totals.subtotalExGstCents),
          gstCents: Value(totals.gstCents),
          totalCents: Value(totals.totalCents),
        );
      } else if (gstMode != null) {
        // GST mode changed without touching lines — recompute from stored lines.
        final stored = await linesFor(id);
        final totals = GstCalculator.compute(
          mode,
          stored
              .map((l) => GstLine(
                    quantityMilli: l.quantityMilli,
                    unitPriceCents: l.unitPriceCents,
                    gstApplicable: l.gstApplicable,
                  ))
              .toList(),
        );
        patch = patch.copyWith(
          subtotalExGstCents: Value(totals.subtotalExGstCents),
          gstCents: Value(totals.gstCents),
          totalCents: Value(totals.totalCents),
        );
      }

      await (_db.update(_db.documents)..where((t) => t.id.equals(id)))
          .write(patch);
    });
  }

  // ------------------------------------------------------- issue / freeze

  /// Builds the render model from LIVE rows (drafts) — issued documents must
  /// use [renderDataFor], which prefers the frozen snapshot.
  Future<DocumentRenderData> buildLiveRenderData(String id) async {
    final doc = await byId(id);
    if (doc == null) {
      throw const AppException('This document could not be found.');
    }
    final settings = await (_db.select(_db.companySettings)
          ..where((t) => t.id.equals(1)))
        .getSingle();
    final customer = await (_db.select(_db.customers)
          ..where((t) => t.id.equals(doc.customerId)))
        .getSingleOrNull();
    final lines = await linesFor(id);
    return DocumentRenderData(
      docType: DocType.fromName(doc.docType),
      docNumber: doc.docNumber,
      issueDateMs: doc.issueDate,
      expiryDateMs: doc.expiryDate,
      dueDateMs: doc.dueDate,
      supplier: RenderSupplier(
        legalName: settings.legalName,
        tradingName: settings.tradingName,
        abn: settings.abn,
        gstRegistered: settings.gstRegistered,
        address: settings.address,
        phone: settings.phone,
        email: settings.email,
      ),
      customer: RenderCustomer(
        name: customer?.name ?? doc.customerNameCache,
        contactName: customer?.contactName,
        address: customer?.billingAddress,
        email: customer?.email,
        mobile: customer?.mobile,
        abn: customer?.abn,
      ),
      siteAddress: doc.siteAddress,
      workType: doc.workType,
      scopeOfWork: doc.scopeOfWork,
      lines: lines
          .map((l) => RenderLine(
                description: l.description,
                quantityMilli: l.quantityMilli,
                unitLabel: l.unitLabel,
                unitPriceCents: l.unitPriceCents,
                gstApplicable: l.gstApplicable,
                lineTotalCents: l.lineTotalCents,
              ))
          .toList(),
      gstMode: GstMode.fromName(doc.gstMode),
      subtotalExGstCents: doc.subtotalExGstCents,
      gstCents: doc.gstCents,
      totalCents: doc.totalCents,
      terms: doc.terms,
      customerNotes: doc.customerNotes,
      bank: RenderBank(
        accountName: settings.bankAccountName,
        bsb: settings.bsb,
        accountNumber: settings.accountNumber,
        instructions: settings.paymentInstructions,
      ),
      footer: settings.documentFooter,
    );
  }

  /// Snapshot if frozen, live data for drafts.
  Future<DocumentRenderData> renderDataFor(String id) async {
    final snap = await (_db.select(_db.documentSnapshots)
          ..where((t) => t.documentId.equals(id)))
        .getSingleOrNull();
    if (snap != null) {
      return DocumentRenderData.fromJson(
          (jsonDecode(snap.snapshotJson) as Map).cast<String, dynamic>());
    }
    return buildLiveRenderData(id);
  }

  Future<void> _freezeIfNeeded(String id) async {
    final existing = await (_db.select(_db.documentSnapshots)
          ..where((t) => t.documentId.equals(id)))
        .getSingleOrNull();
    if (existing != null) return;
    final render = await buildLiveRenderData(id);
    await _db.into(_db.documentSnapshots).insert(
          DocumentSnapshotsCompanion.insert(
            documentId: id,
            snapshotJson: jsonEncode(render.toJson()),
            createdAt: nowMs(),
          ),
        );
  }

  /// Leaves draft: freezes the snapshot and moves the status forward
  /// (quote → sent, invoice → issued). [confirmedSent] also stamps sentAt.
  Future<void> markIssued(String id, {bool confirmedSent = false}) {
    return _db.transaction(() async {
      final doc = await byId(id);
      if (doc == null) {
        throw const AppException('This document could not be found.');
      }
      final status = DocStatus.fromName(doc.status);
      final type = DocType.fromName(doc.docType);
      await _freezeIfNeeded(id);
      var newStatus = status;
      if (status.isDraft) {
        newStatus = type == DocType.quote ? DocStatus.sent : DocStatus.issued;
      }
      await (_db.update(_db.documents)..where((t) => t.id.equals(id))).write(
        DocumentsCompanion(
          status: Value(newStatus.name),
          sentAt: confirmedSent ? Value(nowMs()) : const Value.absent(),
          updatedAt: Value(nowMs()),
        ),
      );
      await _audit('document', id, confirmedSent ? 'markedSent' : 'issued');
    });
  }

  Future<void> acceptQuote(String id) => _setQuoteStatus(id, DocStatus.accepted);

  Future<void> declineQuote(String id) => _setQuoteStatus(id, DocStatus.declined);

  Future<void> _setQuoteStatus(String id, DocStatus newStatus) {
    return _db.transaction(() async {
      final doc = await byId(id);
      if (doc == null || DocType.fromName(doc.docType) != DocType.quote) {
        throw const AppException('This action only applies to quotes.');
      }
      await _freezeIfNeeded(id);
      await (_db.update(_db.documents)..where((t) => t.id.equals(id))).write(
        DocumentsCompanion(
            status: Value(newStatus.name), updatedAt: Value(nowMs())),
      );
      await _audit('document', id, newStatus.name);
    });
  }

  Future<void> cancelDraft(String id) {
    return _db.transaction(() async {
      final doc = await byId(id);
      if (doc == null) return;
      if (!DocStatus.fromName(doc.status).isDraft) {
        throw const AppException('Only drafts can be cancelled this way.');
      }
      await (_db.update(_db.documents)..where((t) => t.id.equals(id))).write(
        DocumentsCompanion(
            status: Value(DocStatus.cancelled.name),
            updatedAt: Value(nowMs())),
      );
      await _audit('document', id, 'cancelled');
    });
  }

  /// Deletes an abandoned draft entirely (lines cascade). Numbers are not
  /// reused — the gap is acceptable (D-004, D-013).
  Future<void> deleteDraft(String id) {
    return _db.transaction(() async {
      final doc = await byId(id);
      if (doc == null) return;
      if (!DocStatus.fromName(doc.status).isDraft) {
        throw const AppException('Issued documents cannot be deleted. '
            'You can void an invoice instead.');
      }
      await _audit('document', id, 'draftDeleted', {'number': doc.docNumber});
      await (_db.delete(_db.documents)..where((t) => t.id.equals(id))).go();
    });
  }

  /// Voids an issued invoice — recorded, never deleted; number never reused.
  Future<void> voidInvoice(String id, {String? reason}) {
    return _db.transaction(() async {
      final doc = await byId(id);
      if (doc == null || DocType.fromName(doc.docType) != DocType.invoice) {
        throw const AppException('Only invoices can be voided.');
      }
      final status = DocStatus.fromName(doc.status);
      if (status == DocStatus.paid) {
        throw const AppException(
            'A paid invoice cannot be voided. Reverse its payments first.');
      }
      await _freezeIfNeeded(id);
      await (_db.update(_db.documents)..where((t) => t.id.equals(id))).write(
        DocumentsCompanion(
          status: Value(DocStatus.voided.name),
          voidedAt: Value(nowMs()),
          updatedAt: Value(nowMs()),
        ),
      );
      await _audit('document', id, 'voided', {'reason': reason ?? ''});
    });
  }

  // ------------------------------------------------------------ conversion

  /// One-button conversion. Preserves the quote, creates a linked invoice
  /// from the quote's frozen data, in a single transaction (invariant 4).
  Future<DocumentRow> convertQuoteToInvoice(String quoteId,
      {bool force = false}) {
    return _db.transaction(() async {
      final quote = await byId(quoteId);
      if (quote == null || DocType.fromName(quote.docType) != DocType.quote) {
        throw const AppException('Only quotes can be converted to invoices.');
      }
      if (quote.convertedInvoiceId != null) {
        throw const AppException(
            'This quote already has an invoice. Open it from the quote screen.');
      }
      final status = DocStatus.fromName(quote.status);
      final allowed = status == DocStatus.accepted ||
          (force &&
              (status == DocStatus.sent ||
                  status == DocStatus.draft ||
                  status == DocStatus.expired));
      if (!allowed) {
        throw AppException(
            'A ${status.label.toLowerCase()} quote cannot be converted.');
      }

      await _freezeIfNeeded(quoteId);
      final settings = await (_db.select(_db.companySettings)
            ..where((t) => t.id.equals(1)))
          .getSingle();
      final quoteLines = await linesFor(quoteId);
      final number = await _allocateNumber(DocType.invoice, settings);
      final now = nowMs();

      final invoice = DocumentRow(
        id: newId(),
        docType: DocType.invoice.name,
        docNumber: number,
        customerId: quote.customerId,
        customerNameCache: quote.customerNameCache,
        status: DocStatus.issued.name,
        issueDate: now,
        expiryDate: null,
        dueDate: daysFromNowMs(settings.defaultPaymentTermsDays),
        gstMode: quote.gstMode,
        siteAddress: quote.siteAddress,
        workType: quote.workType,
        scopeOfWork: quote.scopeOfWork,
        terms: quote.terms,
        customerNotes: quote.customerNotes,
        internalNotes: quote.internalNotes,
        subtotalExGstCents: quote.subtotalExGstCents,
        gstCents: quote.gstCents,
        totalCents: quote.totalCents,
        sourceQuoteId: quote.id,
        convertedInvoiceId: null,
        sentAt: null,
        voidedAt: null,
        createdAt: now,
        updatedAt: now,
      );
      await _db.into(_db.documents).insert(invoice);

      for (final line in quoteLines) {
        await _db.into(_db.lineItems).insert(LineItemsCompanion.insert(
              id: newId(),
              documentId: invoice.id,
              position: line.position,
              description: line.description,
              quantityMilli: Value(line.quantityMilli),
              unitLabel: Value(line.unitLabel),
              unitPriceCents: line.unitPriceCents,
              gstApplicable: Value(line.gstApplicable),
              lineTotalCents: line.lineTotalCents,
            ));
      }

      await (_db.update(_db.documents)..where((t) => t.id.equals(quoteId)))
          .write(DocumentsCompanion(
        convertedInvoiceId: Value(invoice.id),
        updatedAt: Value(now),
      ));

      // The invoice is issued immediately — freeze its own snapshot now.
      await _freezeIfNeeded(invoice.id);

      await _audit('document', quoteId, 'convertedToInvoice',
          {'invoiceId': invoice.id, 'invoiceNumber': number});
      await _audit('document', invoice.id, 'createdFromQuote',
          {'quoteId': quoteId, 'quoteNumber': quote.docNumber});
      return invoice;
    });
  }

  /// New editable draft copied from any document (new number, no links).
  Future<DocumentRow> duplicateAsDraft(String id) {
    return _db.transaction(() async {
      final source = await byId(id);
      if (source == null) {
        throw const AppException('This document could not be found.');
      }
      final settings = await (_db.select(_db.companySettings)
            ..where((t) => t.id.equals(1)))
          .getSingle();
      final type = DocType.fromName(source.docType);
      final number = await _allocateNumber(type, settings);
      final now = nowMs();
      final copy = DocumentRow(
        id: newId(),
        docType: source.docType,
        docNumber: number,
        customerId: source.customerId,
        customerNameCache: source.customerNameCache,
        status: DocStatus.draft.name,
        issueDate: now,
        expiryDate: type == DocType.quote
            ? daysFromNowMs(settings.defaultQuoteValidityDays)
            : null,
        dueDate: type == DocType.invoice
            ? daysFromNowMs(settings.defaultPaymentTermsDays)
            : null,
        gstMode: source.gstMode,
        siteAddress: source.siteAddress,
        workType: source.workType,
        scopeOfWork: source.scopeOfWork,
        terms: source.terms,
        customerNotes: source.customerNotes,
        internalNotes: source.internalNotes,
        subtotalExGstCents: source.subtotalExGstCents,
        gstCents: source.gstCents,
        totalCents: source.totalCents,
        sourceQuoteId: null,
        convertedInvoiceId: null,
        sentAt: null,
        voidedAt: null,
        createdAt: now,
        updatedAt: now,
      );
      await _db.into(_db.documents).insert(copy);
      final lines = await linesFor(id);
      for (final line in lines) {
        await _db.into(_db.lineItems).insert(LineItemsCompanion.insert(
              id: newId(),
              documentId: copy.id,
              position: line.position,
              description: line.description,
              quantityMilli: Value(line.quantityMilli),
              unitLabel: Value(line.unitLabel),
              unitPriceCents: line.unitPriceCents,
              gstApplicable: Value(line.gstApplicable),
              lineTotalCents: line.lineTotalCents,
            ));
      }
      await _audit('document', copy.id, 'duplicatedFrom',
          {'sourceId': id, 'sourceNumber': source.docNumber});
      return copy;
    });
  }

  // -------------------------------------------------------------- watchers

  Stream<List<DocumentRow>> watchRecent(int limit) {
    final q = _db.select(_db.documents)
      ..orderBy([(t) => OrderingTerm.desc(t.updatedAt)])
      ..limit(limit);
    return q.watch();
  }

  Stream<List<DocumentRow>> watchDrafts() {
    final q = _db.select(_db.documents)
      ..where((t) => t.status.equals(DocStatus.draft.name))
      ..orderBy([(t) => OrderingTerm.desc(t.updatedAt)]);
    return q.watch();
  }

  /// Invoices still owing money (overdue derived by callers from dueDate).
  Stream<List<DocumentRow>> watchOpenInvoices() {
    final q = _db.select(_db.documents)
      ..where((t) =>
          t.docType.equals(DocType.invoice.name) &
          t.status.isIn([
            DocStatus.issued.name,
            DocStatus.partiallyPaid.name,
          ]))
      ..orderBy([(t) => OrderingTerm.asc(t.dueDate)]);
    return q.watch();
  }

  Stream<List<DocumentRow>> watchQuotesAwaitingResponse() {
    final q = _db.select(_db.documents)
      ..where((t) =>
          t.docType.equals(DocType.quote.name) &
          t.status.equals(DocStatus.sent.name))
      ..orderBy([(t) => OrderingTerm.desc(t.updatedAt)]);
    return q.watch();
  }

  Stream<List<DocumentRow>> watchAll({
    DocType? type,
    List<DocStatus>? statuses,
    String query = '',
  }) {
    final q = _db.select(_db.documents);
    if (type != null) {
      q.where((t) => t.docType.equals(type.name));
    }
    if (statuses != null && statuses.isNotEmpty) {
      q.where((t) => t.status.isIn(statuses.map((s) => s.name).toList()));
    }
    final needle = query.trim();
    if (needle.isNotEmpty) {
      q.where((t) =>
          t.docNumber.contains(needle) |
          t.customerNameCache.contains(needle) |
          t.siteAddress.contains(needle) |
          t.scopeOfWork.contains(needle));
    }
    q.orderBy([(t) => OrderingTerm.desc(t.updatedAt)]);
    return q.watch();
  }

  Stream<List<DocumentRow>> watchForCustomer(String customerId) {
    final q = _db.select(_db.documents)
      ..where((t) => t.customerId.equals(customerId))
      ..orderBy([(t) => OrderingTerm.desc(t.updatedAt)]);
    return q.watch();
  }

  /// Invoices issued in the current month (dashboard "invoiced this month").
  Stream<List<DocumentRow>> watchInvoicedThisMonth() {
    final start = startOfCurrentMonthMs();
    final q = _db.select(_db.documents)
      ..where((t) =>
          t.docType.equals(DocType.invoice.name) &
          t.status.isIn([
            DocStatus.issued.name,
            DocStatus.partiallyPaid.name,
            DocStatus.paid.name,
          ]) &
          t.issueDate.isBiggerOrEqualValue(start));
    return q.watch();
  }

  // ----------------------------------------------------------- share events

  Future<void> recordShareEvent(
      String documentId, ShareChannel channel, ShareOutcome outcome) async {
    await _db.into(_db.shareEvents).insert(ShareEventsCompanion.insert(
          id: newId(),
          documentId: documentId,
          channel: channel.name,
          outcome: outcome.name,
          createdAt: nowMs(),
        ));
  }

  // ------------------------------------------------------------------ audit

  Future<void> _audit(String type, String id, String action,
      [Map<String, Object?>? details]) async {
    await _db.into(_db.auditEvents).insert(AuditEventsCompanion.insert(
          id: newId(),
          entityType: type,
          entityId: id,
          action: action,
          detailsJson:
              details == null ? const Value.absent() : Value(jsonEncode(details)),
          createdAt: nowMs(),
        ));
  }
}
