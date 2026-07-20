import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:printing/printing.dart';

import '../../domain/enums.dart';
import '../../providers.dart';
import '../../services/pdf/pdf_builder.dart';
import '../../shared/widgets.dart';

/// In-app PDF preview. Sharing happens on the dedicated share screen so the
/// honest "What happened?" flow is never bypassed; printing is allowed here.
class PdfPreviewScreen extends ConsumerStatefulWidget {
  const PdfPreviewScreen({super.key, required this.documentId});

  final String documentId;

  @override
  ConsumerState<PdfPreviewScreen> createState() => _PdfPreviewScreenState();
}

class _PdfPreviewScreenState extends ConsumerState<PdfPreviewScreen> {
  Uint8List? _bytes;
  String _title = 'Preview';
  bool _failed = false;

  @override
  void initState() {
    super.initState();
    Future.microtask(_build);
  }

  Future<void> _build() async {
    try {
      final repo = ref.read(documentRepositoryProvider);
      final doc = await repo.byId(widget.documentId);
      final render = await repo.renderDataFor(widget.documentId);
      final voided = doc != null && DocStatus.fromName(doc.status) == DocStatus.voided;
      final bytes = await PdfBuilder.build(
        render,
        watermarkText: voided ? 'VOIDED — NOT PAYABLE' : null,
      );
      if (mounted) {
        setState(() {
          _bytes = bytes;
          _title = '${render.title} ${render.docNumber}';
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _failed = true);
        showErrorSnack(context, e);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final bytes = _bytes;
    return Scaffold(
      appBar: AppBar(title: Text(_title)),
      body: _failed
          ? const EmptyState(
              icon: Icons.picture_as_pdf_outlined,
              message: 'The PDF could not be created.\n'
                  'Go back and try again.',
            )
          : bytes == null
              ? const Center(child: CircularProgressIndicator())
              : PdfPreview(
                  build: (format) async => bytes,
                  allowPrinting: true,
                  allowSharing: false,
                  canChangePageFormat: false,
                  canChangeOrientation: false,
                  canDebug: false,
                ),
      bottomNavigationBar: bytes == null
          ? null
          : SafeArea(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 8, 20, 16),
                child: BigButton(
                  label: 'SEND',
                  icon: Icons.send_outlined,
                  onPressed: () => context.pushReplacement(
                      '/documents/${widget.documentId}/share'),
                ),
              ),
            ),
    );
  }
}
