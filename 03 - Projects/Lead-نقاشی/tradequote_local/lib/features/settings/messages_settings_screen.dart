import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../providers.dart';
import '../../shared/widgets.dart';

/// Edit the three message templates. Placeholders are filled automatically
/// when sending; empty values remove their phrase cleanly.
class MessagesSettingsScreen extends ConsumerStatefulWidget {
  const MessagesSettingsScreen({super.key});

  @override
  ConsumerState<MessagesSettingsScreen> createState() =>
      _MessagesSettingsScreenState();
}

class _MessagesSettingsScreenState
    extends ConsumerState<MessagesSettingsScreen> {
  final _controllers = <String, (TextEditingController, TextEditingController)>{};
  bool _loading = true;
  bool _saving = false;

  static const _labels = {
    'quote': 'Quote message',
    'invoice': 'Invoice message',
    'reminder': 'Reminder message',
  };

  @override
  void initState() {
    super.initState();
    Future.microtask(_load);
  }

  Future<void> _load() async {
    final rows =
        await ref.read(settingsRepositoryProvider).allTemplates();
    if (!mounted) return;
    setState(() {
      for (final id in _labels.keys) {
        final row = rows.where((r) => r.id == id).firstOrNull;
        _controllers[id] = (
          TextEditingController(text: row?.subject ?? ''),
          TextEditingController(text: row?.body ?? ''),
        );
      }
      _loading = false;
    });
  }

  @override
  void dispose() {
    for (final (a, b) in _controllers.values) {
      a.dispose();
      b.dispose();
    }
    super.dispose();
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      final repo = ref.read(settingsRepositoryProvider);
      for (final entry in _controllers.entries) {
        await repo.saveTemplate(
          entry.key,
          subject: entry.value.$1.text.trim().isEmpty
              ? null
              : entry.value.$1.text.trim(),
          body: entry.value.$2.text.trim(),
        );
      }
      if (mounted) {
        showSuccessSnack(context, 'Messages saved.');
        context.pop();
      }
    } catch (e) {
      if (mounted) showErrorSnack(context, e);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Messages')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(20),
              children: [
                Text(
                  'These words are filled in automatically:\n'
                  '{customerName}  {documentNumber}  {siteAddress}\n'
                  '{total}  {dueDate}  {balance}  {businessName}',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                const SizedBox(height: 16),
                for (final entry in _labels.entries) ...[
                  SectionCard(
                    title: entry.value,
                    child: Column(
                      children: [
                        TextField(
                          controller: _controllers[entry.key]!.$1,
                          decoration: const InputDecoration(
                              labelText: 'Email subject'),
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: _controllers[entry.key]!.$2,
                          maxLines: 5,
                          minLines: 3,
                          decoration:
                              const InputDecoration(labelText: 'Message'),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 14),
                ],
                BigButton(
                  label: _saving ? 'Saving…' : 'Save messages',
                  onPressed: _saving ? null : _save,
                ),
                const SizedBox(height: 32),
              ],
            ),
    );
  }
}
