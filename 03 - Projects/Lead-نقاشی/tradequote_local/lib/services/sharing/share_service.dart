import 'dart:io';
import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter_email_sender/flutter_email_sender.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

import '../../domain/enums.dart';

/// Sharing is honest by design (invariant 6): opening a share sheet or a
/// mail compose screen NEVER proves delivery. This service only reports what
/// verifiably happened; the UI then asks the user "What happened?" and only
/// their answer can mark a document as sent.
///
/// Telegram: Android does not let us verify a Telegram send, and share_plus
/// 13 does not target a specific package — the reliable, standards-based
/// flow is the system share sheet where the user taps Telegram (D-010).
class ShareService {
  /// Writes the PDF into an app-private share cache and returns the file.
  Future<File> writePdfToShareCache(String fileName, Uint8List bytes) async {
    final tmp = await getTemporaryDirectory();
    final dir = Directory(p.join(tmp.path, 'share'));
    await dir.create(recursive: true);
    await _cleanOldFiles(dir);
    final file = File(p.join(dir.path, fileName));
    await file.writeAsBytes(bytes, flush: true);
    return file;
  }

  /// Opens the system share sheet with the PDF + message.
  Future<ShareOutcome> shareViaSheet({
    required File pdf,
    required String message,
    String? subject,
  }) async {
    try {
      final result = await SharePlus.instance.share(ShareParams(
        text: message,
        subject: subject,
        files: [XFile(pdf.path, mimeType: 'application/pdf')],
      ));
      switch (result.status) {
        case ShareResultStatus.success:
          return ShareOutcome.shareSheetOpened;
        case ShareResultStatus.dismissed:
          return ShareOutcome.cancelledOrUnknown;
        case ShareResultStatus.unavailable:
          return ShareOutcome.failedToOpen;
      }
    } catch (_) {
      return ShareOutcome.failedToOpen;
    }
  }

  /// Opens the default mail app's compose screen with recipient, subject,
  /// body and the PDF attached ("Prepare in Gmail" — D-011). Falls back to
  /// the share sheet if no mail app can handle the intent.
  Future<ShareOutcome> prepareEmail({
    required File pdf,
    String? to,
    required String subject,
    required String body,
  }) async {
    try {
      final email = Email(
        recipients: [if (to != null && to.trim().isNotEmpty) to.trim()],
        subject: subject,
        body: body,
        attachmentPaths: [pdf.path],
      );
      await FlutterEmailSender.send(email);
      return ShareOutcome.prepared;
    } catch (_) {
      // No mail app / intent failure — offer the generic sheet instead.
      final fallback = await shareViaSheet(
          pdf: pdf, message: body, subject: subject);
      return fallback == ShareOutcome.shareSheetOpened
          ? ShareOutcome.shareSheetOpened
          : ShareOutcome.failedToOpen;
    }
  }

  /// Saves the PDF through the system save dialog (SAF). Returns true when
  /// the user picked a location.
  Future<bool> savePdf(String fileName, Uint8List bytes) async {
    final path = await FilePicker.platform.saveFile(
      dialogTitle: 'Save PDF',
      fileName: fileName,
      type: FileType.custom,
      allowedExtensions: ['pdf'],
      bytes: bytes,
    );
    return path != null;
  }

  Future<void> _cleanOldFiles(Directory dir) async {
    try {
      final cutoff = DateTime.now().subtract(const Duration(days: 7));
      await for (final entity in dir.list()) {
        if (entity is File) {
          final stat = await entity.stat();
          if (stat.modified.isBefore(cutoff)) {
            await entity.delete();
          }
        }
      }
    } catch (_) {
      // Cache cleanup is best-effort; never block sharing on it.
    }
  }
}
