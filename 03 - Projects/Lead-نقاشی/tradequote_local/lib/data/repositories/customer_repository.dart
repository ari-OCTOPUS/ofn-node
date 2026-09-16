import 'package:drift/drift.dart';

import '../../core/dates.dart';
import '../../core/ids.dart';
import '../db/database.dart';

class CustomerRepository {
  CustomerRepository(this._db);

  final AppDatabase _db;

  Stream<List<CustomerRow>> watchAll({
    String query = '',
    bool includeArchived = false,
  }) {
    final q = _db.select(_db.customers);
    if (!includeArchived) {
      q.where((t) => t.archivedAt.isNull());
    }
    final needle = query.trim();
    if (needle.isNotEmpty) {
      q.where((t) =>
          t.name.contains(needle) |
          t.contactName.contains(needle) |
          t.mobile.contains(needle) |
          t.email.contains(needle) |
          t.billingAddress.contains(needle) |
          t.siteAddress.contains(needle));
    }
    q.orderBy([(t) => OrderingTerm.desc(t.updatedAt)]);
    return q.watch();
  }

  Stream<List<CustomerRow>> watchRecent(int limit) {
    final q = _db.select(_db.customers)
      ..where((t) => t.archivedAt.isNull())
      ..orderBy([(t) => OrderingTerm.desc(t.updatedAt)])
      ..limit(limit);
    return q.watch();
  }

  Future<CustomerRow?> byId(String id) =>
      (_db.select(_db.customers)..where((t) => t.id.equals(id)))
          .getSingleOrNull();

  Stream<CustomerRow?> watchById(String id) =>
      (_db.select(_db.customers)..where((t) => t.id.equals(id)))
          .watchSingleOrNull();

  /// Senior quick-add: name is enough; everything else optional.
  Future<CustomerRow> quickCreate({
    required String name,
    String? mobile,
    String? email,
    String? siteAddress,
  }) async {
    final now = nowMs();
    final row = CustomerRow(
      id: newId(),
      isBusiness: false,
      name: name.trim(),
      contactName: null,
      email: _nullIfBlank(email),
      mobile: _nullIfBlank(mobile),
      abn: null,
      billingAddress: null,
      siteAddress: _nullIfBlank(siteAddress),
      notes: null,
      preferredContact: null,
      archivedAt: null,
      createdAt: now,
      updatedAt: now,
    );
    await _db.into(_db.customers).insert(row);
    await _audit('customer', row.id, 'created');
    return row;
  }

  Future<void> saveEdits(String id, CustomersCompanion patch) async {
    await (_db.update(_db.customers)..where((t) => t.id.equals(id)))
        .write(patch.copyWith(updatedAt: Value(nowMs())));
    await _audit('customer', id, 'updated');
  }

  Future<CustomerRow> createFull(CustomersCompanion values) async {
    final now = nowMs();
    final id = newId();
    await _db.into(_db.customers).insert(values.copyWith(
          id: Value(id),
          createdAt: Value(now),
          updatedAt: Value(now),
        ));
    await _audit('customer', id, 'created');
    return (await byId(id))!;
  }

  /// Customers with documents are archived, never hard-deleted.
  Future<void> archive(String id) async {
    await (_db.update(_db.customers)..where((t) => t.id.equals(id))).write(
        CustomersCompanion(
            archivedAt: Value(nowMs()), updatedAt: Value(nowMs())));
    await _audit('customer', id, 'archived');
  }

  Future<void> unarchive(String id) async {
    await (_db.update(_db.customers)..where((t) => t.id.equals(id))).write(
        CustomersCompanion(
            archivedAt: const Value(null), updatedAt: Value(nowMs())));
    await _audit('customer', id, 'unarchived');
  }

  Future<bool> hasDocuments(String id) async {
    final rows = await (_db.select(_db.documents)
          ..where((t) => t.customerId.equals(id))
          ..limit(1))
        .get();
    return rows.isNotEmpty;
  }

  Future<void> _audit(String type, String id, String action) async {
    await _db.into(_db.auditEvents).insert(AuditEventsCompanion.insert(
          id: newId(),
          entityType: type,
          entityId: id,
          action: action,
          createdAt: nowMs(),
        ));
  }

  String? _nullIfBlank(String? s) {
    final t = s?.trim();
    return (t == null || t.isEmpty) ? null : t;
  }
}
