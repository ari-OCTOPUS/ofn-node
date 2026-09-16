import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../data/db/database.dart';
import '../../domain/enums.dart';
import '../../providers.dart';
import '../../shared/widgets.dart';
import '../home/home_screen.dart' show DocumentTile;

class CustomerDetailScreen extends ConsumerWidget {
  const CustomerDetailScreen({super.key, required this.customerId});

  final String customerId;

  Future<void> _newDocFor(BuildContext context, WidgetRef ref,
      CustomerRow customer, DocType type) async {
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

  Future<void> _archive(
      BuildContext context, WidgetRef ref, CustomerRow c) async {
    final confirmed = await showConfirmSheet(
      context,
      title: 'Archive ${c.name}?',
      message: 'Their quotes and invoices are kept safely. The customer '
          'just disappears from your list. You can bring them back later.',
      confirmLabel: 'Archive customer',
    );
    if (!confirmed) return;
    await ref.read(customerRepositoryProvider).archive(c.id);
    if (context.mounted) {
      showSuccessSnack(context, '${c.name} was archived.');
      context.pop();
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final customerRepo = ref.watch(customerRepositoryProvider);
    final docRepo = ref.watch(documentRepositoryProvider);
    return StreamBuilder<CustomerRow?>(
      stream: customerRepo.watchById(customerId),
      builder: (context, snapshot) {
        final c = snapshot.data;
        if (c == null) {
          return Scaffold(
            appBar: AppBar(title: const Text('Customer')),
            body: snapshot.connectionState == ConnectionState.waiting
                ? const Center(child: CircularProgressIndicator())
                : const EmptyState(
                    icon: Icons.person_off_outlined,
                    message: 'This customer could not be found.'),
          );
        }
        return Scaffold(
          appBar: AppBar(
            title: Text(c.name, overflow: TextOverflow.ellipsis),
            actions: [
              IconButton(
                tooltip: 'Edit',
                iconSize: 28,
                icon: const Icon(Icons.edit_outlined),
                onPressed: () =>
                    context.push('/customers/${c.id}/edit'),
              ),
              PopupMenuButton<String>(
                iconSize: 28,
                onSelected: (v) {
                  if (v == 'archive') _archive(context, ref, c);
                  if (v == 'unarchive') {
                    ref.read(customerRepositoryProvider).unarchive(c.id);
                  }
                },
                itemBuilder: (context) => [
                  if (c.archivedAt == null)
                    const PopupMenuItem(
                        value: 'archive', child: Text('Archive customer'))
                  else
                    const PopupMenuItem(
                        value: 'unarchive',
                        child: Text('Bring back from archive')),
                ],
              ),
            ],
          ),
          body: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              BigButton(
                label: 'NEW QUOTE FOR ${c.name.toUpperCase()}',
                icon: Icons.request_quote_outlined,
                onPressed: () =>
                    _newDocFor(context, ref, c, DocType.quote),
              ),
              const SizedBox(height: 12),
              BigOutlinedButton(
                label: 'New invoice',
                icon: Icons.receipt_long_outlined,
                onPressed: () =>
                    _newDocFor(context, ref, c, DocType.invoice),
              ),
              const SizedBox(height: 20),
              SectionCard(
                title: 'Details',
                child: Column(
                  children: [
                    if ((c.mobile ?? '').isNotEmpty)
                      InfoRow('Mobile', c.mobile!),
                    if ((c.email ?? '').isNotEmpty)
                      InfoRow('Email', c.email!),
                    if ((c.siteAddress ?? '').isNotEmpty)
                      InfoRow('Job address', c.siteAddress!),
                    if ((c.billingAddress ?? '').isNotEmpty)
                      InfoRow('Billing', c.billingAddress!),
                    if ((c.notes ?? '').isNotEmpty)
                      InfoRow('Notes', c.notes!),
                    if ((c.mobile ?? '').isEmpty &&
                        (c.email ?? '').isEmpty &&
                        (c.siteAddress ?? '').isEmpty)
                      Text(
                        'No contact details yet. Tap the pencil to add a '
                        'mobile number or email.',
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              StreamBuilder<List<DocumentRow>>(
                stream: docRepo.watchForCustomer(c.id),
                builder: (context, docsSnapshot) {
                  final docs = docsSnapshot.data ?? const <DocumentRow>[];
                  if (docs.isEmpty) {
                    return SectionCard(
                      title: 'Documents',
                      child: Text(
                        'No quotes or invoices yet.',
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    );
                  }
                  return SectionCard(
                    title: 'Documents',
                    child: Column(
                      children: [for (final d in docs) DocumentTile(doc: d)],
                    ),
                  );
                },
              ),
              const SizedBox(height: 32),
            ],
          ),
        );
      },
    );
  }
}
