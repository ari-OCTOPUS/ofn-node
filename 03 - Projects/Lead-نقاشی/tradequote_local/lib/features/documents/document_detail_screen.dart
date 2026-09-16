import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/dates.dart';
import '../../core/money.dart';
import '../../data/db/database.dart';
import '../../data/repositories/document_repository.dart';
import '../../domain/enums.dart';
import '../../providers.dart';
import '../../shared/widgets.dart';
import '../payments/record_payment_sheet.dart';

/// One document: status, totals, and only the actions that make sense right
/// now — the primary action is always the big button on top.
class DocumentDetailScreen extends ConsumerWidget {
  const DocumentDetailScreen({super.key, required this.documentId});

  final String documentId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final repo = ref.watch(documentRepositoryProvider);
    return StreamBuilder<DocumentDetail?>(
      stream: repo.watchDetail(documentId),
      builder: (context, snapshot) {
        final detail = snapshot.data;
        if (detail == null) {
          return Scaffold(
            appBar: AppBar(title: const Text('Document')),
            body: snapshot.connectionState == ConnectionState.waiting
                ? const Center(child: CircularProgressIndicator())
                : const EmptyState(
                    icon: Icons.description_outlined,
                    message: 'This document could not be found.'),
          );
        }
        return _DetailBody(detail: detail);
      },
    );
  }
}

class _DetailBody extends ConsumerWidget {
  const _DetailBody({required this.detail});

  final DocumentDetail detail;

  Future<void> _convert(BuildContext context, WidgetRef ref,
      {required bool force}) async {
    final doc = detail.doc;
    final ok = await showConfirmSheet(
      context,
      title: 'Make an invoice from ${doc.docNumber}?',
      message: force
          ? 'This quote has not been marked as accepted yet. The quote '
              'stays exactly as it is, and a new invoice is created from it.'
          : 'The quote stays exactly as it is. A new invoice with its own '
              'number is created from it.',
      confirmLabel: 'Make invoice',
    );
    if (!ok || !context.mounted) return;
    try {
      final invoice = await ref
          .read(documentRepositoryProvider)
          .convertQuoteToInvoice(doc.id, force: force);
      if (context.mounted) {
        showSuccessSnack(context,
            'Invoice ${invoice.docNumber} was created. The quote is kept.');
        context.push('/documents/${invoice.id}');
      }
    } catch (e) {
      if (context.mounted) showErrorSnack(context, e);
    }
  }

  Future<void> _void(BuildContext context, WidgetRef ref) async {
    final ok = await showConfirmSheet(
      context,
      title: 'Void ${detail.doc.docNumber}?',
      message: 'The invoice is kept in your records and clearly marked as '
          'voided. Its number is never used again. This cannot be undone.',
      confirmLabel: 'Void invoice',
      destructive: true,
    );
    if (!ok || !context.mounted) return;
    try {
      await ref.read(documentRepositoryProvider).voidInvoice(detail.doc.id);
      if (context.mounted) {
        showSuccessSnack(context, 'Invoice was voided and kept on record.');
      }
    } catch (e) {
      if (context.mounted) showErrorSnack(context, e);
    }
  }

  Future<void> _deleteDraft(BuildContext context, WidgetRef ref) async {
    final ok = await showConfirmSheet(
      context,
      title: 'Delete this draft?',
      message: 'Draft ${detail.doc.docNumber} will be removed. '
          'Its number will not be used again.',
      confirmLabel: 'Delete draft',
      destructive: true,
    );
    if (!ok || !context.mounted) return;
    try {
      await ref.read(documentRepositoryProvider).deleteDraft(detail.doc.id);
      if (context.mounted) {
        showSuccessSnack(context, 'Draft deleted.');
        context.pop();
      }
    } catch (e) {
      if (context.mounted) showErrorSnack(context, e);
    }
  }

  Future<void> _duplicate(BuildContext context, WidgetRef ref) async {
    try {
      final copy = await ref
          .read(documentRepositoryProvider)
          .duplicateAsDraft(detail.doc.id);
      if (context.mounted) {
        showSuccessSnack(
            context, 'Copied to new draft ${copy.docNumber}.');
        context.push(
            '/flow/${DocType.fromName(copy.docType).name}?doc=${copy.id}');
      }
    } catch (e) {
      if (context.mounted) showErrorSnack(context, e);
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final doc = detail.doc;
    final type = detail.type;
    final status = detail.status;
    final isQuote = type == DocType.quote;

    return Scaffold(
      appBar: AppBar(
        title: Text(doc.docNumber),
        actions: [
          PopupMenuButton<String>(
            iconSize: 28,
            onSelected: (v) {
              switch (v) {
                case 'duplicate':
                  _duplicate(context, ref);
                case 'delete':
                  _deleteDraft(context, ref);
                case 'void':
                  _void(context, ref);
                case 'declined':
                  ref
                      .read(documentRepositoryProvider)
                      .declineQuote(doc.id)
                      .catchError((Object e) {
                    if (context.mounted) showErrorSnack(context, e);
                  });
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                  value: 'duplicate', child: Text('Copy to new draft')),
              if (status.isDraft)
                const PopupMenuItem(
                    value: 'delete', child: Text('Delete draft')),
              if (isQuote && status == DocStatus.sent)
                const PopupMenuItem(
                    value: 'declined',
                    child: Text('Customer said no')),
              if (!isQuote &&
                  (status.isOpenInvoice || status == DocStatus.draft))
                const PopupMenuItem(
                    value: 'void', child: Text('Void invoice')),
            ],
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Row(
            children: [
              StatusChip(status, overdue: detail.isOverdue),
              const Spacer(),
              Text(formatAuDate(doc.issueDate),
                  style: Theme.of(context).textTheme.bodyLarge),
            ],
          ),
          const SizedBox(height: 16),
          ..._primaryActions(context, ref),
          const SizedBox(height: 20),
          SectionCard(
            child: Column(
              children: [
                InfoRow('Customer', doc.customerNameCache),
                if ((doc.siteAddress ?? '').isNotEmpty)
                  InfoRow('Job address', doc.siteAddress!),
                if ((doc.scopeOfWork ?? '').isNotEmpty)
                  InfoRow('Work', doc.scopeOfWork!),
                if (isQuote && doc.expiryDate != null)
                  InfoRow('Valid until', formatAuDate(doc.expiryDate!)),
                if (!isQuote && doc.dueDate != null)
                  InfoRow('Due date', formatAuDate(doc.dueDate!)),
                if (doc.sentAt != null)
                  InfoRow('Marked sent', formatAuDate(doc.sentAt!)),
              ],
            ),
          ),
          const SizedBox(height: 14),
          SectionCard(
            title: 'Amount',
            child: Column(
              children: [
                if (doc.gstCents > 0) ...[
                  _row(context, 'Before GST',
                      Money.format(doc.subtotalExGstCents)),
                  _row(context, 'GST', Money.format(doc.gstCents)),
                  const Divider(),
                ],
                _row(context, 'Total', Money.format(doc.totalCents),
                    big: true),
                if (!isQuote && detail.paidCents > 0) ...[
                  const SizedBox(height: 4),
                  _row(context, 'Paid', Money.format(detail.paidCents)),
                  _row(context, 'Still owing',
                      Money.format(detail.balanceCents),
                      big: detail.balanceCents > 0),
                ],
              ],
            ),
          ),
          if (!isQuote && detail.payments.isNotEmpty) ...[
            const SizedBox(height: 14),
            SectionCard(
              title: 'Payments',
              child: Column(
                children: [
                  for (final p in detail.payments)
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      title: Text(Money.format(p.amountCents)),
                      subtitle: Text(
                          '${formatAuDate(p.paidAt)} · ${PaymentMethod.fromName(p.method).label}'
                          '${(p.reference ?? '').isEmpty ? '' : ' · ${p.reference}'}'),
                      trailing: TextButton(
                        onPressed: () async {
                          final ok = await showConfirmSheet(
                            context,
                            title: 'Remove this payment?',
                            message:
                                'The payment of ${Money.format(p.amountCents)} '
                                'will be removed and the amount owing goes '
                                'back up. This is kept in the history.',
                            confirmLabel: 'Remove payment',
                            destructive: true,
                          );
                          if (ok && context.mounted) {
                            try {
                              await ref
                                  .read(paymentRepositoryProvider)
                                  .reverse(p.id);
                              if (context.mounted) {
                                showSuccessSnack(
                                    context, 'Payment removed.');
                              }
                            } catch (e) {
                              if (context.mounted) {
                                showErrorSnack(context, e);
                              }
                            }
                          }
                        },
                        child: const Text('Remove'),
                      ),
                    ),
                ],
              ),
            ),
          ],
          if (isQuote && doc.convertedInvoiceId != null) ...[
            const SizedBox(height: 14),
            Card(
              color: Theme.of(context).colorScheme.secondaryContainer,
              child: ListTile(
                leading: const Icon(Icons.receipt_long, size: 30),
                title: const Text('This quote has an invoice'),
                trailing: const Icon(Icons.chevron_right, size: 30),
                onTap: () => context
                    .push('/documents/${doc.convertedInvoiceId}'),
              ),
            ),
          ],
          if (doc.sourceQuoteId != null) ...[
            const SizedBox(height: 14),
            Card(
              child: ListTile(
                leading: const Icon(Icons.request_quote_outlined, size: 30),
                title: const Text('Made from a quote'),
                trailing: const Icon(Icons.chevron_right, size: 30),
                onTap: () =>
                    context.push('/documents/${doc.sourceQuoteId}'),
              ),
            ),
          ],
          const SizedBox(height: 32),
        ],
      ),
    );
  }

  List<Widget> _primaryActions(BuildContext context, WidgetRef ref) {
    final doc = detail.doc;
    final status = detail.status;
    final isQuote = detail.type == DocType.quote;
    final widgets = <Widget>[];

    void add(Widget w) {
      if (widgets.isNotEmpty) widgets.add(const SizedBox(height: 12));
      widgets.add(w);
    }

    if (status.isDraft) {
      add(BigButton(
        label: 'CONTINUE EDITING',
        icon: Icons.edit_outlined,
        onPressed: () => context.push(
            '/flow/${detail.type.name}?doc=${doc.id}'),
      ));
      add(BigOutlinedButton(
        label: isQuote ? 'Send quote' : 'Send invoice',
        icon: Icons.send_outlined,
        onPressed: () => context.push('/documents/${doc.id}/share'),
      ));
    } else if (isQuote) {
      if (status == DocStatus.sent) {
        add(BigButton(
          label: 'CUSTOMER SAID YES',
          icon: Icons.check_circle_outline,
          onPressed: () async {
            try {
              await ref
                  .read(documentRepositoryProvider)
                  .acceptQuote(doc.id);
              if (context.mounted) {
                showSuccessSnack(context,
                    'Marked as accepted. You can make the invoice now.');
              }
            } catch (e) {
              if (context.mounted) showErrorSnack(context, e);
            }
          },
        ));
        add(BigOutlinedButton(
          label: 'Make invoice',
          icon: Icons.receipt_long_outlined,
          onPressed: () => _convert(context, ref, force: true),
        ));
      }
      if (status == DocStatus.accepted &&
          doc.convertedInvoiceId == null) {
        add(BigButton(
          label: 'MAKE INVOICE',
          icon: Icons.receipt_long_outlined,
          onPressed: () => _convert(context, ref, force: false),
        ));
      }
      add(BigOutlinedButton(
        label: 'Send again',
        icon: Icons.send_outlined,
        onPressed: () => context.push('/documents/${doc.id}/share'),
      ));
    } else {
      // Invoice
      if (status.isOpenInvoice) {
        add(BigButton(
          label: 'RECORD PAYMENT',
          icon: Icons.payments_outlined,
          onPressed: () => showRecordPaymentSheet(
              context, ref, detail.doc, detail.balanceCents),
        ));
        add(BigOutlinedButton(
          label: 'Send reminder',
          icon: Icons.notifications_none,
          onPressed: () => context
              .push('/documents/${doc.id}/share?kind=reminder'),
        ));
        add(BigOutlinedButton(
          label: 'Send again',
          icon: Icons.send_outlined,
          onPressed: () => context.push('/documents/${doc.id}/share'),
        ));
      } else if (status == DocStatus.paid) {
        add(BigOutlinedButton(
          label: 'Send again',
          icon: Icons.send_outlined,
          onPressed: () => context.push('/documents/${doc.id}/share'),
        ));
      }
    }

    add(BigOutlinedButton(
      label: 'Preview PDF',
      icon: Icons.picture_as_pdf_outlined,
      onPressed: () => context.push('/documents/${doc.id}/preview'),
    ));
    return widgets;
  }

  Widget _row(BuildContext context, String label, String value,
      {bool big = false}) {
    final style = TextStyle(
      fontSize: big ? 24 : 18,
      fontWeight: big ? FontWeight.w800 : FontWeight.w500,
    );
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [Text(label, style: style), Text(value, style: style)],
      ),
    );
  }
}
