/// Domain enums. Stored in the database by `name` — never reorder or rename
/// existing values without a migration.
library;

enum DocType {
  quote,
  invoice;

  static DocType fromName(String name) =>
      DocType.values.firstWhere((v) => v.name == name, orElse: () => quote);

  String get label => this == quote ? 'Quote' : 'Invoice';
}

/// One status set for both document types; validity per type is enforced by
/// the repository (see docs/architecture/DOCUMENT_LIFECYCLE.md).
/// `overdue` is intentionally absent — it is derived, never stored.
enum DocStatus {
  draft,
  sent,
  accepted,
  declined,
  expired,
  cancelled,
  issued,
  partiallyPaid,
  paid,
  voided;

  static DocStatus fromName(String name) => DocStatus.values
      .firstWhere((v) => v.name == name, orElse: () => DocStatus.draft);

  String get label => switch (this) {
        draft => 'Draft',
        sent => 'Sent',
        accepted => 'Accepted',
        declined => 'Declined',
        expired => 'Expired',
        cancelled => 'Cancelled',
        issued => 'Awaiting payment',
        partiallyPaid => 'Partly paid',
        paid => 'Paid',
        voided => 'Voided',
      };

  bool get isDraft => this == draft;

  /// Invoice statuses that still owe money.
  bool get isOpenInvoice => this == issued || this == partiallyPaid;
}

enum GstMode {
  /// Prices entered include GST; GST portion is 1/11 of the total.
  inclusive,

  /// Prices entered exclude GST; 10% is added.
  exclusive,

  /// Business not registered for GST — no GST on documents.
  none;

  static GstMode fromName(String name) =>
      GstMode.values.firstWhere((v) => v.name == name, orElse: () => inclusive);

  String get label => switch (this) {
        inclusive => 'Prices include GST',
        exclusive => 'Prices exclude GST (GST added)',
        none => 'No GST (not registered)',
      };
}

enum PaymentMethod {
  bankTransfer,
  cash,
  card,
  cheque,
  other;

  static PaymentMethod fromName(String name) => PaymentMethod.values
      .firstWhere((v) => v.name == name, orElse: () => other);

  String get label => switch (this) {
        bankTransfer => 'Bank transfer',
        cash => 'Cash',
        card => 'Card',
        cheque => 'Cheque',
        other => 'Other',
      };
}

enum ShareChannel {
  telegram,
  email,
  system,
  savePdf;

  static ShareChannel fromName(String name) => ShareChannel.values
      .firstWhere((v) => v.name == name, orElse: () => system);
}

/// Honest share outcomes — the app never records "delivered" (invariant 6).
enum ShareOutcome {
  prepared,
  shareSheetOpened,
  manuallyConfirmedSent,
  failedToOpen,
  cancelledOrUnknown;

  static ShareOutcome fromName(String name) => ShareOutcome.values
      .firstWhere((v) => v.name == name, orElse: () => cancelledOrUnknown);
}

/// Painting-trade work types — suggestions, stored as free text.
const List<String> kWorkTypes = [
  'Interior',
  'Exterior',
  'Roof',
  'Deck',
  'Fence',
  'Commercial',
  'Residential',
  'Maintenance',
  'Other',
];

/// Quick description templates (editable free text once inserted).
const List<String> kDescriptionTemplates = [
  'Interior painting — walls and ceilings, preparation included',
  'Exterior painting — full prep, undercoat and two top coats',
  'Roof painting — clean, seal and two coats',
  'Deck staining and sealing',
  'Fence painting — both sides',
  'Touch-up and maintenance painting',
  'Preparation and repairs — gap filling, sanding, priming',
  'Labour',
  'Paint and materials',
];
