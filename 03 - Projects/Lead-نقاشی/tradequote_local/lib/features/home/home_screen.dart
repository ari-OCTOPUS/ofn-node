import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/dates.dart';
import '../../core/money.dart';
import '../../data/db/database.dart';
import '../../domain/enums.dart';
import '../../providers.dart';
import '../../shared/widgets.dart';

/// The owner's home: NEW QUOTE and NEW INVOICE above the fold, a To-Do
/// summary, continue-unfinished card, and a few recent documents. No charts,
/// no accounting jargon (see addendum §13).
class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  Future<void> _startFlow(
      BuildContext context, WidgetRef ref, DocType type) async {
    final customer =
        await context.push<CustomerRow>('/customers?pick=1');
    if (customer == null || !context.mounted) return;
    try {
      final doc = await ref
          .read(documentRepositoryProvider)
          .createDraft(type: type, customer: customer);
      if (context.mounted) {
        await context.push('/flow/${type.name}?doc=${doc.id}');
      }
    } catch (e) {
      if (context.mounted) showErrorSnack(context, e);
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final openInvoices = ref.watch(openInvoicesProvider).value ?? const [];
    final drafts = ref.watch(draftDocumentsProvider).value ?? const [];
    final awaiting = ref.watch(quotesAwaitingProvider).value ?? const [];
    final recent = ref.watch(recentDocumentsProvider).value ?? const [];
    final invoicedMonth =
        ref.watch(invoicedThisMonthProvider).value ?? const [];
    final paymentsMonth =
        ref.watch(paymentsThisMonthProvider).value ?? const [];

    final overdue = openInvoices
        .where((d) => d.dueDate != null && isPastDate(d.dueDate!))
        .toList();
    final invoicedTotal =
        invoicedMonth.fold<int>(0, (t, d) => t + d.totalCents);
    final receivedTotal =
        paymentsMonth.fold<int>(0, (t, x) => t + x.amountCents);
    final hour = DateTime.now().hour;
    final greeting = hour < 12
        ? 'Good morning'
        : (hour < 17 ? 'Good afternoon' : 'Good evening');

    return Scaffold(
      appBar: AppBar(
        title: Text(greeting),
        actions: [
          IconButton(
            tooltip: 'Settings',
            iconSize: 30,
            onPressed: () => context.push('/settings'),
            icon: const Icon(Icons.settings_outlined),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          BigButton(
            label: 'NEW QUOTE',
            icon: Icons.request_quote_outlined,
            onPressed: () => _startFlow(context, ref, DocType.quote),
          ),
          const SizedBox(height: 12),
          BigButton(
            label: 'NEW INVOICE',
            icon: Icons.receipt_long_outlined,
            color: theme.colorScheme.tertiary,
            onPressed: () => _startFlow(context, ref, DocType.invoice),
          ),
          if (drafts.isNotEmpty) ...[
            const SizedBox(height: 16),
            _ContinueDraftCard(draft: drafts.first),
          ],
          const SizedBox(height: 20),
          SectionCard(
            title: 'To do',
            child: Column(
              children: [
                _TodoRow(
                  icon: Icons.hourglass_bottom,
                  label: overdue.isEmpty
                      ? 'No overdue invoices'
                      : '${overdue.length} overdue '
                          '${overdue.length == 1 ? "invoice" : "invoices"}',
                  emphasis: overdue.isNotEmpty,
                  onTap: () => context.push('/documents?filter=unpaid'),
                ),
                _TodoRow(
                  icon: Icons.payments_outlined,
                  label: openInvoices.isEmpty
                      ? 'No unpaid invoices'
                      : '${openInvoices.length} unpaid '
                          '${openInvoices.length == 1 ? "invoice" : "invoices"} '
                          '(${Money.format(openInvoices.fold<int>(0, (t, d) => t + d.totalCents))})',
                  onTap: () => context.push('/documents?filter=unpaid'),
                ),
                _TodoRow(
                  icon: Icons.mark_email_unread_outlined,
                  label: awaiting.isEmpty
                      ? 'No quotes waiting for an answer'
                      : '${awaiting.length} '
                          '${awaiting.length == 1 ? "quote" : "quotes"} waiting for an answer',
                  onTap: () => context.push('/documents?filter=quotes'),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          SectionCard(
            title: 'This month',
            child: Row(
              children: [
                Expanded(
                  child: _MonthStat(
                      label: 'Invoiced', cents: invoicedTotal),
                ),
                Container(
                    width: 1, height: 44, color: theme.colorScheme.outlineVariant),
                Expanded(
                  child: _MonthStat(
                      label: 'Received', cents: receivedTotal),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          if (recent.isNotEmpty)
            SectionCard(
              title: 'Recent',
              child: Column(
                children: [
                  for (final doc in recent) DocumentTile(doc: doc),
                  TextButton(
                    onPressed: () => context.push('/documents'),
                    child: const Text('See all documents'),
                  ),
                ],
              ),
            ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: BigOutlinedButton(
                  label: 'Customers',
                  icon: Icons.people_outline,
                  onPressed: () => context.push('/customers'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: BigOutlinedButton(
                  label: 'Documents',
                  icon: Icons.folder_open_outlined,
                  onPressed: () => context.push('/documents'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 32),
        ],
      ),
    );
  }
}

class _ContinueDraftCard extends StatelessWidget {
  const _ContinueDraftCard({required this.draft});

  final DocumentRow draft;

  @override
  Widget build(BuildContext context) {
    final type = DocType.fromName(draft.docType);
    return Card(
      color: Theme.of(context).colorScheme.secondaryContainer,
      child: ListTile(
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
        leading: const Icon(Icons.edit_note, size: 34),
        title: Text('Continue where you left off'),
        subtitle: Text(
            '${type.label} ${draft.docNumber} — ${draft.customerNameCache}'),
        trailing: const Icon(Icons.chevron_right, size: 30),
        onTap: () =>
            context.push('/flow/${type.name}?doc=${draft.id}'),
      ),
    );
  }
}

class _TodoRow extends StatelessWidget {
  const _TodoRow({
    required this.icon,
    required this.label,
    this.onTap,
    this.emphasis = false,
  });

  final IconData icon;
  final String label;
  final VoidCallback? onTap;
  final bool emphasis;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final color = emphasis ? const Color(0xFF991B1B) : null;
    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: Icon(icon, size: 28, color: color),
      title: Text(label,
          style: theme.textTheme.bodyLarge?.copyWith(
              color: color,
              fontWeight: emphasis ? FontWeight.w700 : null)),
      trailing: const Icon(Icons.chevron_right),
      onTap: onTap,
    );
  }
}

class _MonthStat extends StatelessWidget {
  const _MonthStat({required this.label, required this.cents});

  final String label;
  final int cents;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      children: [
        Text(label,
            style: theme.textTheme.bodyMedium
                ?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
        const SizedBox(height: 4),
        MoneyText(cents, size: 22),
      ],
    );
  }
}

/// Shared document list tile (used on Home, Documents, Customer detail).
class DocumentTile extends StatelessWidget {
  const DocumentTile({super.key, required this.doc});

  final DocumentRow doc;

  @override
  Widget build(BuildContext context) {
    final status = DocStatus.fromName(doc.status);
    final overdue = status.isOpenInvoice &&
        doc.dueDate != null &&
        isPastDate(doc.dueDate!);
    return ListTile(
      contentPadding: EdgeInsets.zero,
      title: Text('${doc.docNumber}  ·  ${doc.customerNameCache}',
          maxLines: 1, overflow: TextOverflow.ellipsis),
      subtitle: Padding(
        padding: const EdgeInsets.only(top: 4),
        child: Row(
          children: [
            StatusChip(status, overdue: overdue),
            const SizedBox(width: 8),
            Expanded(
              child: Text(formatAuDate(doc.updatedAt),
                  style: Theme.of(context).textTheme.bodyMedium),
            ),
          ],
        ),
      ),
      trailing: MoneyText(doc.totalCents, size: 18),
      onTap: () => context.push('/documents/${doc.id}'),
    );
  }
}
