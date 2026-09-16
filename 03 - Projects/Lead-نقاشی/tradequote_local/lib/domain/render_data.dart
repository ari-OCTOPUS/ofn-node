import '../core/gst.dart';
import 'enums.dart';

/// The frozen, self-contained render model for a document (invariant 2).
///
/// When a document leaves `draft`, a `DocumentRenderData` JSON snapshot is
/// stored in `document_snapshots`. PDFs for issued documents render ONLY
/// from this snapshot, so later edits to customers or company settings can
/// never rewrite an issued quote or tax invoice.
///
/// Hand-written JSON (D-002). `schema` guards future format changes.
class RenderSupplier {
  const RenderSupplier({
    required this.legalName,
    this.tradingName,
    this.abn,
    required this.gstRegistered,
    this.address,
    this.phone,
    this.email,
  });

  final String legalName;
  final String? tradingName;
  final String? abn;
  final bool gstRegistered;
  final String? address;
  final String? phone;
  final String? email;

  String get displayName =>
      (tradingName != null && tradingName!.trim().isNotEmpty)
          ? tradingName!
          : legalName;

  Map<String, dynamic> toJson() => {
        'legalName': legalName,
        'tradingName': tradingName,
        'abn': abn,
        'gstRegistered': gstRegistered,
        'address': address,
        'phone': phone,
        'email': email,
      };

  factory RenderSupplier.fromJson(Map<String, dynamic> j) => RenderSupplier(
        legalName: (j['legalName'] as String?) ?? '',
        tradingName: j['tradingName'] as String?,
        abn: j['abn'] as String?,
        gstRegistered: (j['gstRegistered'] as bool?) ?? false,
        address: j['address'] as String?,
        phone: j['phone'] as String?,
        email: j['email'] as String?,
      );
}

class RenderCustomer {
  const RenderCustomer({
    required this.name,
    this.contactName,
    this.address,
    this.email,
    this.mobile,
    this.abn,
  });

  final String name;
  final String? contactName;
  final String? address;
  final String? email;
  final String? mobile;
  final String? abn;

  Map<String, dynamic> toJson() => {
        'name': name,
        'contactName': contactName,
        'address': address,
        'email': email,
        'mobile': mobile,
        'abn': abn,
      };

  factory RenderCustomer.fromJson(Map<String, dynamic> j) => RenderCustomer(
        name: (j['name'] as String?) ?? '',
        contactName: j['contactName'] as String?,
        address: j['address'] as String?,
        email: j['email'] as String?,
        mobile: j['mobile'] as String?,
        abn: j['abn'] as String?,
      );
}

class RenderLine {
  const RenderLine({
    required this.description,
    required this.quantityMilli,
    this.unitLabel,
    required this.unitPriceCents,
    required this.gstApplicable,
    required this.lineTotalCents,
  });

  final String description;
  final int quantityMilli;
  final String? unitLabel;
  final int unitPriceCents;
  final bool gstApplicable;
  final int lineTotalCents;

  Map<String, dynamic> toJson() => {
        'description': description,
        'quantityMilli': quantityMilli,
        'unitLabel': unitLabel,
        'unitPriceCents': unitPriceCents,
        'gstApplicable': gstApplicable,
        'lineTotalCents': lineTotalCents,
      };

  factory RenderLine.fromJson(Map<String, dynamic> j) => RenderLine(
        description: (j['description'] as String?) ?? '',
        quantityMilli: (j['quantityMilli'] as num?)?.toInt() ?? 1000,
        unitLabel: j['unitLabel'] as String?,
        unitPriceCents: (j['unitPriceCents'] as num?)?.toInt() ?? 0,
        gstApplicable: (j['gstApplicable'] as bool?) ?? true,
        lineTotalCents: (j['lineTotalCents'] as num?)?.toInt() ?? 0,
      );
}

class RenderBank {
  const RenderBank({
    this.accountName,
    this.bsb,
    this.accountNumber,
    this.instructions,
  });

  final String? accountName;
  final String? bsb;
  final String? accountNumber;
  final String? instructions;

  bool get hasDetails =>
      (accountName ?? '').isNotEmpty ||
      (bsb ?? '').isNotEmpty ||
      (accountNumber ?? '').isNotEmpty ||
      (instructions ?? '').isNotEmpty;

  Map<String, dynamic> toJson() => {
        'accountName': accountName,
        'bsb': bsb,
        'accountNumber': accountNumber,
        'instructions': instructions,
      };

  factory RenderBank.fromJson(Map<String, dynamic> j) => RenderBank(
        accountName: j['accountName'] as String?,
        bsb: j['bsb'] as String?,
        accountNumber: j['accountNumber'] as String?,
        instructions: j['instructions'] as String?,
      );
}

class DocumentRenderData {
  const DocumentRenderData({
    required this.docType,
    required this.docNumber,
    required this.issueDateMs,
    this.expiryDateMs,
    this.dueDateMs,
    required this.supplier,
    required this.customer,
    this.siteAddress,
    this.workType,
    this.scopeOfWork,
    required this.lines,
    required this.gstMode,
    required this.subtotalExGstCents,
    required this.gstCents,
    required this.totalCents,
    this.terms,
    this.customerNotes,
    required this.bank,
    this.footer,
  });

  static const int schemaVersion = 1;

  final DocType docType;
  final String docNumber;
  final int issueDateMs;
  final int? expiryDateMs;
  final int? dueDateMs;
  final RenderSupplier supplier;
  final RenderCustomer customer;
  final String? siteAddress;
  final String? workType;
  final String? scopeOfWork;
  final List<RenderLine> lines;
  final GstMode gstMode;
  final int subtotalExGstCents;
  final int gstCents;
  final int totalCents;
  final String? terms;
  final String? customerNotes;
  final RenderBank bank;
  final String? footer;

  /// Document title per ATO rules (RESEARCH_REPORT §1): "Tax Invoice" only
  /// when the supplier is GST-registered; quotes are always "Quote".
  String get title {
    if (docType == DocType.quote) return 'QUOTE';
    return supplier.gstRegistered ? 'TAX INVOICE' : 'INVOICE';
  }

  /// True when every line is GST-applicable (affects the wording
  /// "Total price includes GST" vs an asterisked mixed presentation).
  bool get allLinesTaxable => lines.every((l) => l.gstApplicable);

  Map<String, dynamic> toJson() => {
        'schema': schemaVersion,
        'docType': docType.name,
        'docNumber': docNumber,
        'issueDateMs': issueDateMs,
        'expiryDateMs': expiryDateMs,
        'dueDateMs': dueDateMs,
        'supplier': supplier.toJson(),
        'customer': customer.toJson(),
        'siteAddress': siteAddress,
        'workType': workType,
        'scopeOfWork': scopeOfWork,
        'lines': lines.map((l) => l.toJson()).toList(),
        'gstMode': gstMode.name,
        'subtotalExGstCents': subtotalExGstCents,
        'gstCents': gstCents,
        'totalCents': totalCents,
        'terms': terms,
        'customerNotes': customerNotes,
        'bank': bank.toJson(),
        'footer': footer,
      };

  factory DocumentRenderData.fromJson(Map<String, dynamic> j) =>
      DocumentRenderData(
        docType: DocType.fromName((j['docType'] as String?) ?? 'quote'),
        docNumber: (j['docNumber'] as String?) ?? '',
        issueDateMs: (j['issueDateMs'] as num?)?.toInt() ?? 0,
        expiryDateMs: (j['expiryDateMs'] as num?)?.toInt(),
        dueDateMs: (j['dueDateMs'] as num?)?.toInt(),
        supplier: RenderSupplier.fromJson(
            (j['supplier'] as Map?)?.cast<String, dynamic>() ?? {}),
        customer: RenderCustomer.fromJson(
            (j['customer'] as Map?)?.cast<String, dynamic>() ?? {}),
        siteAddress: j['siteAddress'] as String?,
        workType: j['workType'] as String?,
        scopeOfWork: j['scopeOfWork'] as String?,
        lines: ((j['lines'] as List?) ?? const [])
            .map((e) =>
                RenderLine.fromJson((e as Map).cast<String, dynamic>()))
            .toList(),
        gstMode: GstMode.fromName((j['gstMode'] as String?) ?? 'inclusive'),
        subtotalExGstCents: (j['subtotalExGstCents'] as num?)?.toInt() ?? 0,
        gstCents: (j['gstCents'] as num?)?.toInt() ?? 0,
        totalCents: (j['totalCents'] as num?)?.toInt() ?? 0,
        terms: j['terms'] as String?,
        customerNotes: j['customerNotes'] as String?,
        bank: RenderBank.fromJson(
            (j['bank'] as Map?)?.cast<String, dynamic>() ?? {}),
        footer: j['footer'] as String?,
      );

  /// Recomputes totals from lines — used by tests to prove the snapshot is
  /// internally consistent.
  DocumentTotals recomputeTotals() => GstCalculator.compute(
        gstMode,
        lines
            .map((l) => GstLine(
                  quantityMilli: l.quantityMilli,
                  unitPriceCents: l.unitPriceCents,
                  gstApplicable: l.gstApplicable,
                ))
            .toList(),
      );
}
