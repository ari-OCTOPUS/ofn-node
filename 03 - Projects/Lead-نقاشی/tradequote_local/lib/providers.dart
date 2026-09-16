import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'core/errors.dart';
import 'data/db/database.dart';
import 'data/repositories/customer_repository.dart';
import 'data/repositories/document_repository.dart';
import 'data/repositories/payment_repository.dart';
import 'data/repositories/settings_repository.dart';
import 'services/ai/ai_service.dart';
import 'services/backup/backup_service.dart';
import 'services/sharing/share_service.dart';
import 'services/templates/message_templates.dart';

const String kAppVersion = '0.1.0';
const String kAppName = 'TradeQuote Local';

/// Holds the live database instance so restore can swap it atomically and
/// republish through [databaseProvider] (see BACKUP_FORMAT.md).
class DbHandle {
  DbHandle._();

  static AppDatabase? instance;

  /// Atomic swap used by restore: close → keep rollback → move staged file
  /// in → reopen. On any failure the previous database is put back.
  static Future<void> swapWith(File stagedDb) async {
    final live = await AppDatabase.databaseFile();
    final rollback = File('${live.path}.pre-restore');
    final old = instance;
    if (old != null) {
      await old.close();
    }
    // Remove stale WAL sidecars — the staged file is a clean VACUUM copy.
    for (final suffix in ['-wal', '-shm']) {
      final sidecar = File('${live.path}$suffix');
      if (sidecar.existsSync()) await sidecar.delete();
    }
    if (rollback.existsSync()) await rollback.delete();
    var movedAside = false;
    try {
      if (live.existsSync()) {
        await live.rename(rollback.path);
        movedAside = true;
      }
      await stagedDb.copy(live.path);
      instance = await AppDatabase.open();
      // Success — probe with a trivial query before discarding rollback.
      await instance!.customSelect('SELECT 1').get();
      if (rollback.existsSync()) await rollback.delete();
    } catch (e) {
      try {
        if (live.existsSync()) await live.delete();
        if (movedAside && rollback.existsSync()) {
          await rollback.rename(live.path);
        }
      } catch (_) {}
      instance = await AppDatabase.open();
      throw BackupException(
          'Restoring failed, so your previous data was kept safe.',
          e.toString());
    }
  }
}

// ------------------------------------------------------------------ wiring

final sharedPrefsProvider = Provider<SharedPreferences>(
    (ref) => throw UnimplementedError('overridden in main()'));

final databaseProvider = Provider<AppDatabase>((ref) => DbHandle.instance!);

final settingsRepositoryProvider = Provider<SettingsRepository>(
    (ref) => SettingsRepository(ref.watch(databaseProvider)));

final customerRepositoryProvider = Provider<CustomerRepository>(
    (ref) => CustomerRepository(ref.watch(databaseProvider)));

final documentRepositoryProvider = Provider<DocumentRepository>(
    (ref) => DocumentRepository(ref.watch(databaseProvider)));

final paymentRepositoryProvider = Provider<PaymentRepository>(
    (ref) => PaymentRepository(ref.watch(databaseProvider)));

final shareServiceProvider = Provider<ShareService>((ref) => ShareService());

final messageTemplateServiceProvider = Provider<MessageTemplateService>(
    (ref) => MessageTemplateService(ref.watch(settingsRepositoryProvider)));

final aiServiceProvider =
    Provider<AiService>((ref) => AiService(ref.watch(sharedPrefsProvider)));

final aiSettingsProvider = FutureProvider<AiSettings>(
    (ref) => ref.watch(aiServiceProvider).settings());

final backupServiceProvider = Provider<BackupService>((ref) => BackupService(
      getDb: () => ref.read(databaseProvider),
      swapDatabase: DbHandle.swapWith,
      appVersion: kAppVersion,
    ));

// ------------------------------------------------------------ shared streams

final companySettingsProvider = StreamProvider<CompanySettingsRow>(
    (ref) => ref.watch(settingsRepositoryProvider).watch());

final recentDocumentsProvider = StreamProvider<List<DocumentRow>>(
    (ref) => ref.watch(documentRepositoryProvider).watchRecent(6));

final draftDocumentsProvider = StreamProvider<List<DocumentRow>>(
    (ref) => ref.watch(documentRepositoryProvider).watchDrafts());

final openInvoicesProvider = StreamProvider<List<DocumentRow>>(
    (ref) => ref.watch(documentRepositoryProvider).watchOpenInvoices());

final quotesAwaitingProvider = StreamProvider<List<DocumentRow>>((ref) =>
    ref.watch(documentRepositoryProvider).watchQuotesAwaitingResponse());

final invoicedThisMonthProvider = StreamProvider<List<DocumentRow>>(
    (ref) => ref.watch(documentRepositoryProvider).watchInvoicedThisMonth());

final paymentsThisMonthProvider = StreamProvider<List<PaymentRow>>(
    (ref) => ref.watch(paymentRepositoryProvider).watchThisMonth());

// --------------------------------------------------------- display settings

class TextScaleNotifier extends Notifier<double> {
  static const _key = 'display.textScale';

  @override
  double build() =>
      ref.watch(sharedPrefsProvider).getDouble(_key) ?? 1.15;

  Future<void> set(double value) async {
    state = value;
    await ref.read(sharedPrefsProvider).setDouble(_key, value);
  }
}

final textScaleProvider =
    NotifierProvider<TextScaleNotifier, double>(TextScaleNotifier.new);

class ThemeModeNotifier extends Notifier<ThemeMode> {
  static const _key = 'display.themeMode';

  @override
  ThemeMode build() {
    final raw = ref.watch(sharedPrefsProvider).getString(_key) ?? 'light';
    return switch (raw) {
      'dark' => ThemeMode.dark,
      'system' => ThemeMode.system,
      _ => ThemeMode.light,
    };
  }

  Future<void> set(ThemeMode mode) async {
    state = mode;
    await ref.read(sharedPrefsProvider).setString(_key, switch (mode) {
      ThemeMode.dark => 'dark',
      ThemeMode.system => 'system',
      ThemeMode.light => 'light',
    });
  }
}

final themeModeProvider =
    NotifierProvider<ThemeModeNotifier, ThemeMode>(ThemeModeNotifier.new);

/// Remembers the last used share channel — shown first, never auto-sent.
class LastShareChannelNotifier extends Notifier<String?> {
  static const _key = 'share.lastChannel';

  @override
  String? build() => ref.watch(sharedPrefsProvider).getString(_key);

  Future<void> set(String channel) async {
    state = channel;
    await ref.read(sharedPrefsProvider).setString(_key, channel);
  }
}

final lastShareChannelProvider =
    NotifierProvider<LastShareChannelNotifier, String?>(
        LastShareChannelNotifier.new);
