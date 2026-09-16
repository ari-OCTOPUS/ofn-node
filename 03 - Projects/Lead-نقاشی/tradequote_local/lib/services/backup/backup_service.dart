import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:archive/archive.dart';
import 'package:crypto/crypto.dart';
import 'package:file_picker/file_picker.dart';
import 'package:intl/intl.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:sqlite3/sqlite3.dart' as sqlite;

import '../../core/errors.dart';
import '../../data/db/database.dart';

/// Backup format v1 — see docs/architecture/BACKUP_FORMAT.md.
/// A backup is a zip with a checksummed manifest and a consistent
/// `VACUUM INTO` copy of the database. Restore goes through staging,
/// validation, an automatic safety backup and an atomic swap.
class BackupInfo {
  const BackupInfo({
    required this.appVersion,
    required this.schemaVersion,
    required this.createdAtIso,
    required this.fileCount,
  });

  final String appVersion;
  final int schemaVersion;
  final String createdAtIso;
  final int fileCount;
}

class BackupService {
  BackupService({
    required AppDatabase Function() getDb,
    required Future<void> Function(File stagedDbFile) swapDatabase,
    required this.appVersion,
  })  : _getDb = getDb,
        _swapDatabase = swapDatabase;

  final AppDatabase Function() _getDb;

  /// Provided by the providers layer: closes the live DB, swaps the files
  /// (keeping a rollback copy), reopens, and republishes the handle.
  final Future<void> Function(File stagedDbFile) _swapDatabase;

  final String appVersion;

  static const int backupFormatVersion = 1;
  static const String _dbEntryName = 'database/tradequote.sqlite';

  // ----------------------------------------------------------------- create

  Future<Uint8List> createBackupBytes() async {
    final db = _getDb();
    final support = await getApplicationSupportDirectory();
    final tmpCopy = File(p.join(support.path,
        'backup-tmp-${DateTime.now().millisecondsSinceEpoch}.sqlite'));
    if (tmpCopy.existsSync()) await tmpCopy.delete();

    // Consistent snapshot of the live database without closing it.
    await db.customStatement('VACUUM INTO ?', [tmpCopy.path]);
    try {
      final dbBytes = await tmpCopy.readAsBytes();
      final files = <Map<String, Object>>[
        {
          'path': _dbEntryName,
          'sha256': sha256.convert(dbBytes).toString(),
          'bytes': dbBytes.length,
        },
      ];
      final manifest = <String, Object>{
        'backupFormatVersion': backupFormatVersion,
        'appVersion': appVersion,
        'schemaVersion': db.schemaVersion,
        'createdAt': DateTime.now().toUtc().toIso8601String(),
        'files': files,
      };
      final manifestBytes = utf8.encode(jsonEncode(manifest));

      final archive = Archive()
        ..addFile(ArchiveFile('manifest.json', manifestBytes.length,
            manifestBytes))
        ..addFile(ArchiveFile(_dbEntryName, dbBytes.length, dbBytes));
      final zipped = ZipEncoder().encode(archive);
      if (zipped == null) {
        throw const BackupException('The backup could not be created.');
      }
      return Uint8List.fromList(zipped);
    } finally {
      if (tmpCopy.existsSync()) await tmpCopy.delete();
    }
  }

  String suggestedFileName() {
    final stamp = DateFormat('yyyyMMdd-HHmmss').format(DateTime.now());
    return 'tradequote-backup-$stamp.tqbackup.zip';
  }

  /// Creates the archive and hands it to the system save dialog. The user
  /// may choose local storage, an SD card, or the Google Drive entry if the
  /// Drive app is installed — no Google APIs or accounts are involved.
  Future<bool> saveBackupViaPicker() async {
    final bytes = await createBackupBytes();
    final path = await FilePicker.platform.saveFile(
      dialogTitle: 'Save backup',
      fileName: suggestedFileName(),
      type: FileType.any,
      bytes: bytes,
    );
    return path != null;
  }

  // ---------------------------------------------------------------- restore

  /// Validates the archive fully (checksums, sqlite integrity, schema
  /// compatibility) and stages the database file. Returns metadata for the
  /// confirmation screen. Nothing live is touched yet.
  Future<(BackupInfo, File)> validateAndStage(Uint8List archiveBytes) async {
    final Archive archive;
    try {
      archive = ZipDecoder().decodeBytes(archiveBytes, verify: true);
    } catch (_) {
      throw const BackupException(
          'This file is not a valid TradeQuote backup.');
    }

    ArchiveFile? manifestFile;
    final entries = <String, ArchiveFile>{};
    for (final f in archive.files) {
      if (!f.isFile) continue;
      final name = f.name.replaceAll('\\', '/');
      // Path-traversal defence.
      if (name.contains('..') || name.startsWith('/')) {
        throw const BackupException(
            'This backup contains unsafe file paths and was rejected.');
      }
      if (name == 'manifest.json') {
        manifestFile = f;
      } else {
        entries[name] = f;
      }
    }
    if (manifestFile == null) {
      throw const BackupException(
          'This backup has no manifest and cannot be restored.');
    }

    final Map<String, dynamic> manifest;
    try {
      manifest = (jsonDecode(utf8.decode(manifestFile.content as List<int>))
              as Map)
          .cast<String, dynamic>();
    } catch (_) {
      throw const BackupException('The backup manifest is unreadable.');
    }

    final version = (manifest['backupFormatVersion'] as num?)?.toInt() ?? -1;
    if (version != backupFormatVersion) {
      throw BackupException(
          'This backup uses format $version, which this app version '
          'cannot restore.');
    }

    final files = ((manifest['files'] as List?) ?? const [])
        .map((raw) => (raw as Map).cast<String, dynamic>())
        .toList();
    for (final f in files) {
      final path = f['path'] as String? ?? '';
      final expected = f['sha256'] as String? ?? '';
      final entry = entries[path];
      if (entry == null) {
        throw BackupException('The backup is missing "$path".');
      }
      final actual =
          sha256.convert(entry.content as List<int>).toString();
      if (actual != expected) {
        throw const BackupException(
            'The backup failed its integrity check (checksum mismatch). '
            'It may be damaged — try another copy.');
      }
    }

    final dbEntry = entries[_dbEntryName];
    if (dbEntry == null) {
      throw const BackupException('The backup contains no database.');
    }

    // Stage and verify the database itself.
    final support = await getApplicationSupportDirectory();
    final staging = Directory(p.join(support.path, 'restore-staging'));
    if (staging.existsSync()) await staging.delete(recursive: true);
    await staging.create(recursive: true);
    final stagedDb = File(p.join(staging.path, 'tradequote.sqlite'));
    await stagedDb.writeAsBytes(dbEntry.content as List<int>, flush: true);

    int stagedSchema;
    try {
      final raw = sqlite.sqlite3.open(stagedDb.path);
      try {
        final integrity = raw.select('PRAGMA integrity_check');
        final ok = integrity.isNotEmpty &&
            integrity.first.values.first.toString() == 'ok';
        if (!ok) {
          throw const BackupException(
              'The database inside this backup is damaged.');
        }
        stagedSchema =
            raw.select('PRAGMA user_version').first.values.first as int;
      } finally {
        raw.dispose();
      }
    } on BackupException {
      rethrow;
    } catch (_) {
      throw const BackupException(
          'The database inside this backup could not be opened.');
    }

    final currentSchema = _getDb().schemaVersion;
    if (stagedSchema > currentSchema) {
      throw BackupException(
          'This backup was made by a newer version of the app '
          '(data version $stagedSchema). Update the app first.');
    }

    return (
      BackupInfo(
        appVersion: manifest['appVersion'] as String? ?? 'unknown',
        schemaVersion: stagedSchema,
        createdAtIso: manifest['createdAt'] as String? ?? 'unknown',
        fileCount: files.length,
      ),
      stagedDb,
    );
  }

  /// Performs the restore: automatic safety backup of CURRENT data first,
  /// then the atomic swap (delegated to the providers layer).
  Future<void> restoreStaged(File stagedDb) async {
    // 1. Safety backup of current data into app storage.
    final support = await getApplicationSupportDirectory();
    final safetyDir = Directory(p.join(support.path, 'safety-backups'));
    await safetyDir.create(recursive: true);
    final stamp = DateFormat('yyyyMMdd-HHmmss').format(DateTime.now());
    final safetyFile =
        File(p.join(safetyDir.path, 'pre-restore-$stamp.sqlite'));
    await _getDb().customStatement('VACUUM INTO ?', [safetyFile.path]);

    // 2. Atomic swap + reopen (rolls back on failure).
    await _swapDatabase(stagedDb);
  }
}
