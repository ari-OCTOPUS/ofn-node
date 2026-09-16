import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../providers.dart';
import '../../shared/widgets.dart';
import '../onboarding/company_form.dart';

/// Business details (same form as onboarding). Changing details here NEVER
/// rewrites documents that were already issued — they keep their snapshot.
class BusinessSettingsScreen extends ConsumerWidget {
  const BusinessSettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(companySettingsProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('My business')),
      body: settings.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => EmptyState(
            icon: Icons.error_outline,
            message: 'Settings could not be loaded.\nPlease try again.'),
        data: (row) => Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 0),
              child: Text(
                'Changes apply to NEW documents. Quotes and invoices you '
                'already issued stay exactly as they were.',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ),
            Expanded(
              child: CompanyForm(
                initial: row,
                submitLabel: 'Save changes',
                showNumbering: true,
                onSubmit: (values) async {
                  try {
                    await ref
                        .read(settingsRepositoryProvider)
                        .save(values);
                    if (context.mounted) {
                      showSuccessSnack(context, 'Saved.');
                      context.pop();
                    }
                  } catch (e) {
                    if (context.mounted) showErrorSnack(context, e);
                  }
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
