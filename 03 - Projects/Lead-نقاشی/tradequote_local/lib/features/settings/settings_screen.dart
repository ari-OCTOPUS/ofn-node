import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../providers.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(companySettingsProvider).value;
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          _Group(
            icon: Icons.storefront_outlined,
            title: 'My business',
            subtitle: settings == null || settings.legalName.isEmpty
                ? 'Business details, GST, bank account'
                : settings.legalName,
            onTap: () => context.push('/settings/business'),
          ),
          _Group(
            icon: Icons.chat_outlined,
            title: 'Messages',
            subtitle: 'The messages sent with quotes and invoices',
            onTap: () => context.push('/settings/messages'),
          ),
          _Group(
            icon: Icons.save_outlined,
            title: 'My data',
            subtitle: 'Back up my data · Restore my data',
            onTap: () => context.push('/settings/data'),
          ),
          _Group(
            icon: Icons.text_fields,
            title: 'Display',
            subtitle: 'Text size · Light or dark',
            onTap: () => context.push('/settings/display'),
          ),
          _Group(
            icon: Icons.auto_awesome_outlined,
            title: 'Optional online features',
            subtitle: 'AI assistance — off unless you turn it on',
            onTap: () => context.push('/settings/ai'),
          ),
          const SizedBox(height: 24),
          Center(
            child: Text(
              '$kAppName $kAppVersion\n'
              'Everything is stored on this phone. No account. No cloud.\n'
              'This app keeps records — it is not tax or accounting advice.',
              textAlign: TextAlign.center,
              style: Theme.of(context)
                  .textTheme
                  .bodyMedium
                  ?.copyWith(color: Theme.of(context).colorScheme.outline),
            ),
          ),
        ],
      ),
    );
  }
}

class _Group extends StatelessWidget {
  const _Group({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        leading: Icon(icon, size: 32),
        title: Text(title),
        subtitle: Text(subtitle, maxLines: 2),
        trailing: const Icon(Icons.chevron_right, size: 30),
        onTap: onTap,
      ),
    );
  }
}
