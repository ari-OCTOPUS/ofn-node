import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../providers.dart';
import '../../shared/widgets.dart';
import 'company_form.dart';

/// First-run setup. One friendly scrolling form; everything can be changed
/// later in Settings. No account, no sign-in, nothing leaves the phone.
class OnboardingScreen extends ConsumerWidget {
  const OnboardingScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(title: const Text('Welcome')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 8, 20, 0),
            child: Text(
              'Let\'s set up your business details. They will appear on '
              'your quotes and invoices. You can change everything later '
              'in Settings.',
              style: Theme.of(context).textTheme.bodyLarge,
            ),
          ),
          Expanded(
            child: CompanyForm(
              submitLabel: 'Save and start',
              showNumbering: true,
              onSubmit: (values) async {
                try {
                  await ref
                      .read(settingsRepositoryProvider)
                      .completeOnboarding(values);
                  if (context.mounted) {
                    showSuccessSnack(
                        context, 'All set. Your details are saved.');
                    context.go('/');
                  }
                } catch (e) {
                  if (context.mounted) showErrorSnack(context, e);
                }
              },
            ),
          ),
        ],
      ),
    );
  }
}
