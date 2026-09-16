import 'package:uuid/uuid.dart';

const Uuid _uuid = Uuid();

/// Stable, locally generated identifier (UUID v4) for all domain entities.
String newId() => _uuid.v4();

/// Makes a string safe for use in a file name (PDF/backup exports).
String sanitizeFileName(String input) {
  var s = input.replaceAll(RegExp(r'[^A-Za-z0-9._ -]'), '').trim();
  s = s.replaceAll(RegExp(r'\s+'), '-');
  if (s.length > 60) s = s.substring(0, 60);
  return s.isEmpty ? 'document' : s;
}
