import '../../core/dates.dart';
import '../../core/money.dart';
import '../../data/db/database.dart';
import '../../data/repositories/settings_repository.dart';
import '../../domain/enums.dart';

/// Fills the editable message templates ({customerName}, {documentNumber},
/// {siteAddress}, {total}, {dueDate}, {balance}, {businessName}) and removes
/// phrases cleanly when a value is missing. The PDF remains the
/// authoritative document; messages are short by design.
class FilledMessage {
  const FilledMessage({required this.subject, required this.body});

  final String subject;
  final String body;
}

class MessageTemplateService {
  MessageTemplateService(this._settings);

  final SettingsRepository _settings;

  /// [kind]: 'quote' | 'invoice' | 'reminder'.
  Future<FilledMessage> fill({
    required String kind,
    required DocumentRow doc,
    int? balanceCents,
  }) async {
    final company = await _settings.get();
    final template = await _settings.template(kind);
    final businessName =
        (company.tradingName?.trim().isNotEmpty ?? false)
            ? company.tradingName!.trim()
            : company.legalName;

    final values = <String, String>{
      'customerName': doc.customerNameCache,
      'documentNumber': doc.docNumber,
      'siteAddress': (doc.siteAddress ?? '').trim(),
      'total': Money.format(doc.totalCents),
      'dueDate': doc.dueDate == null ? '' : formatAuDate(doc.dueDate!),
      'balance':
          balanceCents == null ? '' : Money.format(balanceCents),
      'businessName': businessName,
    };

    final defaultSubject =
        '${DocType.fromName(doc.docType).label} ${doc.docNumber} — $businessName';
    final subject =
        _fill(template?.subject ?? defaultSubject, values);
    final body = _fill(template?.body ?? '', values);
    return FilledMessage(subject: subject, body: body);
  }

  /// Phrases removed entirely when their value is empty, so messages never
  /// read "…the painting work at ." (senior-friendly rule).
  static const Map<String, List<String>> _phraseFallbacks = {
    'siteAddress': [
      ' for the painting work at {siteAddress}',
      ' at {siteAddress}',
    ],
    'dueDate': [
      ' and the due date is {dueDate}',
      ' due {dueDate}',
    ],
  };

  String _fill(String template, Map<String, String> values) {
    var out = template;
    for (final entry in values.entries) {
      final token = '{${entry.key}}';
      if (entry.value.isEmpty) {
        for (final phrase in _phraseFallbacks[entry.key] ?? const <String>[]) {
          out = out.replaceAll(phrase, '');
        }
        out = out.replaceAll(token, '');
      } else {
        out = out.replaceAll(token, entry.value);
      }
    }
    // Tidy artefacts from removed phrases.
    out = out.replaceAll(RegExp(r'  +'), ' ');
    out = out.replaceAll(' .', '.').replaceAll(' ,', ',');
    return out.trim();
  }
}
