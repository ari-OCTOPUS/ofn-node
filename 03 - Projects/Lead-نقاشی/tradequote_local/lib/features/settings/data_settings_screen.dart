import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/dates.dart';
import '../../core/errors.dart';
import '../../providers.dart';
import '../../shared/widgets.dart';

/// "My data" — complete backup and safe restore. Wording is honest: local
/// backup needs no internet; choosing Google Drive in the picker is the
/// user's choice and needs internet only at that moment (BACKUP_FORMAT.md).
class DataSettingsScreen extends ConsumerStatefulWidget {
  const DataSettingsScreen({super.key});

  @override
  ConsumerState<DataSettingsScreen> createState() =>
      _DataSettingsScreenState();
}

class _DataSettingsScreenState extends ConsumerState<DataSettingsScreen> {
  bool _busy = false;
  String? _lastBackup;

  @override
  void initState() {
    super.initState();
    Future.microtask(_loadMeta);
  }

  Future<void> _loadMeta() async {
    final raw =
        await ref.read(settingsRepositoryProvider).meta('lastBackupAt');
    if (mounted) {
      setState(() {
        _lastBackup =
            raw == null ? null : formatAuDateLong(int.tryParse(raw) ?? 0);
      });
    }
  }

  Future<void> _backup() async {
    setState(() => _busy = true);
    try {
      final saved =
          await ref.read(backupServiceProvider).saveBackupViaPicker();
      if (saved) {
        await ref
            .read(settingsRepositoryProvider)
            .setMeta('lastBackupAt', '${nowMs()}');
        await _loadMeta();
        if (mounted) {
          showSuccessSnack(context,
              'Backup saved. Keep this file somewhere safe — it contains '
              'everything.');
        }
      }
    } catch (e) {
      if (mounted) showErrorSnack(context, e);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _restore() async {
    setState(() => _busy = true);
    try {
      final picked = await FilePicker.platform.pickFiles(
        dialogTitle: 'Choose your backup file',
        type: FileType.any,
        withData: true,
      );
      final bytes = picked?.files.single.bytes;
      if (bytes == null) return;

      final service = ref.read(backupServiceProvider);
      final (info, stagedDb) = await service.validateAndStage(bytes);
      if (!mounted) return;

      final ok = await showConfirmSheet(
        context,
        title: 'Restore this backup?',
        message: 'Backup made: ${info.createdAtIso.split("T").first}\n'
            'App version: ${info.appVersion}\n\n'
            'This will REPLACE everything currently in the app with the '
            'backup. A safety copy of your current data is made '
            'automatically first.',
        confirmLabel: 'Restore backup',
        destructive: true,
      );
      if (!ok) return;

      await service.restoreStaged(stagedDb);
      ref.invalidate(databaseProvider);
      if (mounted) {
        showSuccessSnack(
            context, 'Your backup was restored successfully.');
        context.go('/');
      }
    } on BackupException catch (e) {
      if (mounted) showErrorSnack(context, e);
    } catch (e) {
      if (mounted) showErrorSnack(context, e);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('My data')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          SectionCard(
            title: 'Back up my data',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  'Saves ONE file with all your customers, quotes, '
                  'invoices and payments. Choose where to keep it — your '
                  'phone, an SD card, or Google Drive if it is on your '
                  'phone (Drive needs internet just for that moment).',
                  style: Theme.of(context).textTheme.bodyLarge,
                ),
                if (_lastBackup != null) ...[
                  const SizedBox(height: 8),
                  Text('Last backup: $_lastBackup',
                      style: Theme.of(context).textTheme.bodyMedium),
                ],
                const SizedBox(height: 16),
                BigButton(
                  label: _busy ? 'Working…' : 'BACK UP MY DATA',
                  icon: Icons.save_outlined,
                  onPressed: _busy ? null : _backup,
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          SectionCard(
            title: 'Restore my data',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  'Brings everything back from a backup file — for example '
                  'on a new phone. Your current data is saved safely first, '
                  'and nothing is replaced until the backup passes its '
                  'safety checks.',
                  style: Theme.of(context).textTheme.bodyLarge,
                ),
                const SizedBox(height: 16),
                BigOutlinedButton(
                  label: 'Restore from a backup file',
                  icon: Icons.restore,
                  onPressed: _busy ? null : _restore,
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Text(
            'Tip: back up after busy weeks, and keep a copy somewhere '
            'other than this phone.',
            style: Theme.of(context).textTheme.bodyMedium,
          ),
        ],
      ),
    );
  }
}
