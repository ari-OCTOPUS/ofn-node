import 'package:drift/drift.dart';

import '../../core/dates.dart';
import '../db/database.dart';

/// Single-row company settings + message templates.
class SettingsRepository {
  SettingsRepository(this._db);

  final AppDatabase _db;

  Future<CompanySettingsRow> get() async =>
      (_db.select(_db.companySettings)..where((t) => t.id.equals(1)))
          .getSingle();

  Stream<CompanySettingsRow> watch() =>
      (_db.select(_db.companySettings)..where((t) => t.id.equals(1)))
          .watchSingle();

  /// Partial update; always bumps updatedAt.
  Future<void> save(CompanySettingsCompanion patch) async {
    await (_db.update(_db.companySettings)..where((t) => t.id.equals(1)))
        .write(patch.copyWith(updatedAt: Value(nowMs())));
  }

  Future<void> completeOnboarding(CompanySettingsCompanion values) async {
    await save(values.copyWith(onboardingComplete: const Value(true)));
  }

  // ------------------------------------------------------------- templates

  Future<MessageTemplateRow?> template(String id) async =>
      (_db.select(_db.messageTemplates)..where((t) => t.id.equals(id)))
          .getSingleOrNull();

  Future<List<MessageTemplateRow>> allTemplates() =>
      _db.select(_db.messageTemplates).get();

  Future<void> saveTemplate(String id, {String? subject, required String body}) async {
    await _db.into(_db.messageTemplates).insertOnConflictUpdate(
          MessageTemplatesCompanion(
            id: Value(id),
            subject: Value(subject),
            body: Value(body),
          ),
        );
  }

  // --------------------------------------------------------------- appMeta

  Future<String?> meta(String key) async {
    final row = await (_db.select(_db.appMeta)
          ..where((t) => t.key.equals(key)))
        .getSingleOrNull();
    return row?.value;
  }

  Future<void> setMeta(String key, String value) async {
    await _db.into(_db.appMeta).insertOnConflictUpdate(
        AppMetaCompanion(key: Value(key), value: Value(value)));
  }
}
