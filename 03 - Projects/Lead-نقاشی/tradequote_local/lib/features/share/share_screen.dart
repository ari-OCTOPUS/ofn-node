import 'dart:io';
import 'dart:typed_data';

import 'package:drift/drift.dart' show Value;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/errors.dart';
import '../../core/money.dart';
import '../../data/db/database.dart';
import '../../domain/enums.dart';
import '../../providers.dart';
import '../../services/pdf/pdf_builder.dart';
import '../../shared/widgets.dart';

/// The big share screen (addendum §8): the PDF is saved BEFORE any external
/// app opens; the app never claims delivery — after coming back it asks
/// "What happened?" and only the user's answer marks the document as sent.
class ShareScreen extends ConsumerStatefulWidget {
  const ShareScreen({super.key, required this.documentId, this.kind});

  final String documentId;

  /// null → quote/invoice message by type; 'reminder' → reminder message.
  final String? kind;

  @override
  ConsumerState<ShareScreen> createState() => _ShareScreenState();
}

class _ShareScreenState extends ConsumerState<ShareScreen> {
  DocumentRow? _doc;
  CustomerRow? _customer;
  String _subject = '';
  final _message = TextEditingController();
  bool _loading = true;
  bool _busy = false;
  Uint8List? _pdfBytes;
  String _pdfName = 'document.pdf';

  @override
  void initState() {
    super.initState();
    Future.microtask(_load);
  }

  Future<void> _load() async {
    try {
      final docRepo = ref.read(documentRepositoryProvider);
      final detail = await docRepo.getDetail(widget.documentId);
      final customer = await ref
          .read(customerRepositoryProvider)
          .byId(detail.doc.customerId);
      final kind = widget.kind == 'reminder'
          ? 'reminder'
          : DocType.fromName(detail.doc.docType).name;
      final filled = await ref.read(messageTemplateServiceProvider).fill(
            kind: kind,
            doc: detail.doc,
            balanceCents: detail.balanceCents,
          );
      final render = await docRepo.renderDataFor(widget.documentId);
      final bytes = await PdfBuilder.build(render);
      if (!mounted) return;
      setState(() {
        _doc = detail.doc;
        _customer = customer;
        _subject = filled.subject;
        _message.text = filled.body;
        _pdfBytes = bytes;
        _pdfName = PdfBuilder.fileNameFor(render);
        _loading = false;
      });
    } catch (e) {
      if (mounted) {
        showErrorSnack(context, e);
        context.pop();
      }
    }
  }

  @override
  void dispose() {
    _message.dispose();
    super.dispose();
  }

  Future<File> _pdfFile() => ref
      .read(shareServiceProvider)
      .writePdfToShareCache(_pdfName, _pdfBytes!);

  Future<void> _afterShare(ShareChannel channel, ShareOutcome outcome) async {
    final repo = ref.read(documentRepositoryProvider);
    await repo.recordShareEvent(widget.documentId, channel, outcome);
    await ref.read(lastShareChannelProvider.notifier).set(channel.name);
    if (!mounted) return;
    if (outcome == ShareOutcome.failedToOpen) {
      showErrorSnack(
          context,
          const AppException('That app could not be opened. Your document '
              'is safe. Try "More sharing options" instead.'));
      return;
    }
    await _askWhatHappened(channel);
  }

  Future<void> _askWhatHappened(ShareChannel channel) async {
    final doc = _doc!;
    final result = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (sheetContext) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 4, 20, 20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text('What happened to ${doc.docNumber}?',
                  style: Theme.of(sheetContext).textTheme.titleLarge),
              const SizedBox(height: 16),
              BigButton(
                label: 'I sent it',
                icon: Icons.check_circle_outline,
                onPressed: () => Navigator.of(sheetContext).pop('sent'),
              ),
              const SizedBox(height: 10),
              BigOutlinedButton(
                label: 'I saved it for later',
                onPressed: () => Navigator.of(sheetContext).pop('later'),
              ),
              const SizedBox(height: 10),
              BigOutlinedButton(
                label: 'Nothing was sent',
                onPressed: () => Navigator.of(sheetContext).pop('nothing'),
              ),
            ],
          ),
        ),
      ),
    );
    if (!mounted) return;
    if (result == 'sent') {
      try {
        await ref
            .read(documentRepositoryProvider)
            .markIssued(widget.documentId, confirmedSent: true);
        await ref.read(documentRepositoryProvider).recordShareEvent(
            widget.documentId, channel, ShareOutcome.manuallyConfirmedSent);
        if (mounted) {
          showSuccessSnack(context, '${doc.docNumber} is marked as sent.');
          context.pop();
        }
      } catch (e) {
        if (mounted) showErrorSnack(context, e);
      }
    } else if (result == 'later') {
      if (mounted) {
        showSuccessSnack(context,
            'No problem — ${doc.docNumber} is saved and ready when you are.');
      }
    }
  }

  Future<void> _run(Future<void> Function() action) async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      await action();
    } catch (e) {
      if (mounted) showErrorSnack(context, e);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _telegram() => _run(() async {
        final file = await _pdfFile();
        final service = ref.read(shareServiceProvider);
        await ref.read(documentRepositoryProvider).recordShareEvent(
            widget.documentId, ShareChannel.telegram, ShareOutcome.prepared);
        final outcome = await service.shareViaSheet(
            pdf: file, message: _message.text, subject: _subject);
        await _afterShare(ShareChannel.telegram, outcome);
      });

  Future<void> _moreOptions() => _run(() async {
        final file = await _pdfFile();
        final service = ref.read(shareServiceProvider);
        await ref.read(documentRepositoryProvider).recordShareEvent(
            widget.documentId, ShareChannel.system, ShareOutcome.prepared);
        final outcome = await service.shareViaSheet(
            pdf: file, message: _message.text, subject: _subject);
        await _afterShare(ShareChannel.system, outcome);
      });

  Future<void> _gmail() => _run(() async {
        var email = _customer?.email;
        if (email == null || email.trim().isEmpty) {
          email = await _askForEmail();
          if (email == null) return;
        }
        final file = await _pdfFile();
        final service = ref.read(shareServiceProvider);
        await ref.read(documentRepositoryProvider).recordShareEvent(
            widget.documentId, ShareChannel.email, ShareOutcome.prepared);
        final outcome = await service.prepareEmail(
          pdf: file,
          to: email,
          subject: _subject,
          body: _message.text,
        );
        await _afterShare(ShareChannel.email, outcome);
      });

  Future<void> _savePdf() => _run(() async {
        final saved = await ref
            .read(shareServiceProvider)
            .savePdf(_pdfName, _pdfBytes!);
        await ref.read(documentRepositoryProvider).recordShareEvent(
            widget.documentId,
            ShareChannel.savePdf,
            saved ? ShareOutcome.prepared : ShareOutcome.cancelledOrUnknown);
        if (mounted && saved) {
          showSuccessSnack(context, 'PDF saved to your phone.');
        }
      });

  Future<String?> _askForEmail() async {
    final controller = TextEditingController();
    var remember = true;
    final email = await showModalBottomSheet<String>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (sheetContext) => Padding(
        padding: EdgeInsets.only(
            bottom: MediaQuery.of(sheetContext).viewInsets.bottom),
        child: SafeArea(
          child: StatefulBuilder(
            builder: (sheetContext, setSheetState) => Padding(
              padding: const EdgeInsets.fromLTRB(20, 4, 20, 20),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text('What is their email address?',
                      style: Theme.of(sheetContext).textTheme.titleLarge),
                  const SizedBox(height: 14),
                  TextField(
                    controller: controller,
                    autofocus: true,
                    keyboardType: TextInputType.emailAddress,
                    decoration:
                        const InputDecoration(labelText: 'Email address'),
                  ),
                  CheckboxListTile(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('Remember it for this customer'),
                    value: remember,
                    onChanged: (v) =>
                        setSheetState(() => remember = v ?? true),
                  ),
                  const SizedBox(height: 8),
                  BigButton(
                    label: 'Continue',
                    onPressed: () {
                      final t = controller.text.trim();
                      if (t.contains('@') && t.contains('.')) {
                        Navigator.of(sheetContext).pop(t);
                      }
                    },
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
    if (email != null && remember && _customer != null) {
      await ref.read(customerRepositoryProvider).saveEdits(
          _customer!.id, CustomersCompanion(email: Value(email)));
    }
    controller.dispose();
    return email;
  }

  @override
  Widget build(BuildContext context) {
    final doc = _doc;
    if (_loading || doc == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Send')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }
    final type = DocType.fromName(doc.docType);
    final isReminder = widget.kind == 'reminder';
    return Scaffold(
      appBar: AppBar(title: Text('Send ${doc.docNumber}')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          SectionCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  isReminder
                      ? 'Reminder for ${type.label.toLowerCase()} '
                          '${doc.docNumber} is ready'
                      : '${type.label} ${doc.docNumber} is ready',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 8),
                Text('Customer: ${doc.customerNameCache}',
                    style: Theme.of(context).textTheme.bodyLarge),
                Text('Total: ${Money.format(doc.totalCents)}',
                    style: Theme.of(context).textTheme.bodyLarge),
              ],
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _message,
            maxLines: 5,
            minLines: 3,
            decoration: const InputDecoration(
              labelText: 'Message to send with the PDF',
              helperText: 'You can change this before sending.',
            ),
          ),
          Consumer(builder: (context, ref, _) {
            final ai = ref.watch(aiSettingsProvider).value;
            if (ai == null || !ai.isConfigured) {
              return const SizedBox.shrink();
            }
            return Align(
              alignment: Alignment.centerRight,
              child: TextButton.icon(
                onPressed: _busy ? null : _improveMessage,
                icon: const Icon(Icons.auto_awesome, size: 22),
                label: const Text('Improve message (AI)'),
              ),
            );
          }),
          const SizedBox(height: 16),
          BigButton(
            label: 'SEND WITH TELEGRAM',
            icon: Icons.send,
            onPressed: _busy ? null : _telegram,
          ),
          const SizedBox(height: 6),
          Center(
            child: Text(
              'Your phone\'s share menu will open — tap Telegram.',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
          const SizedBox(height: 14),
          BigButton(
            label: 'PREPARE IN GMAIL',
            icon: Icons.mail_outline,
            color: Theme.of(context).colorScheme.tertiary,
            onPressed: _busy ? null : _gmail,
          ),
          const SizedBox(height: 6),
          Center(
            child: Text(
              'Gmail opens with everything filled in — you press Send.',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
          const SizedBox(height: 14),
          BigOutlinedButton(
            label: 'More sharing options',
            icon: Icons.share_outlined,
            onPressed: _busy ? null : _moreOptions,
          ),
          const SizedBox(height: 12),
          BigOutlinedButton(
            label: 'Save PDF to phone',
            icon: Icons.download_outlined,
            onPressed: _busy ? null : _savePdf,
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: BigOutlinedButton(
                  label: 'Preview again',
                  onPressed: _busy
                      ? null
                      : () =>
                          context.push('/documents/${doc.id}/preview'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: BigOutlinedButton(
                  label: 'Back',
                  onPressed: () => context.pop(),
                ),
              ),
            ],
          ),
          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Future<void> _improveMessage() => _run(() async {
        final ai = ref.read(aiServiceProvider);
        String improved;
        try {
          improved = await ai.improveMessage(_message.text);
        } on AiUnavailableException catch (e) {
          if (mounted) showErrorSnack(context, e);
          return;
        }
        if (!mounted) return;
        final useIt = await showModalBottomSheet<bool>(
          context: context,
          showDragHandle: true,
          isScrollControlled: true,
          builder: (sheetContext) => SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(20, 4, 20, 20),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text('Suggested message',
                      style: Theme.of(sheetContext).textTheme.titleLarge),
                  const SizedBox(height: 6),
                  Text(
                    'This suggestion came from your AI service. '
                    'Check it before using it.',
                    style: Theme.of(sheetContext).textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: Theme.of(sheetContext)
                          .colorScheme
                          .surfaceContainerHighest,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(improved,
                        style:
                            Theme.of(sheetContext).textTheme.bodyLarge),
                  ),
                  const SizedBox(height: 16),
                  BigButton(
                    label: 'Use this message',
                    onPressed: () => Navigator.of(sheetContext).pop(true),
                  ),
                  const SizedBox(height: 10),
                  BigOutlinedButton(
                    label: 'Keep my message',
                    onPressed: () => Navigator.of(sheetContext).pop(false),
                  ),
                ],
              ),
            ),
          ),
        );
        if (useIt == true && mounted) {
          setState(() => _message.text = improved);
        }
      });
}
