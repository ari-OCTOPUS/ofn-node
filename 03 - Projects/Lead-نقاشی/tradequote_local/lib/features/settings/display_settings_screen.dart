import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers.dart';
import '../../shared/widgets.dart';

class DisplaySettingsScreen extends ConsumerWidget {
  const DisplaySettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final scale = ref.watch(textScaleProvider);
    final mode = ref.watch(themeModeProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Display')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          SectionCard(
            title: 'Text size',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _choice(context, 'Normal', scale == 1.0,
                    () => ref.read(textScaleProvider.notifier).set(1.0)),
                _choice(context, 'Large (recommended)', scale == 1.15,
                    () => ref.read(textScaleProvider.notifier).set(1.15)),
                _choice(context, 'Extra large', scale == 1.3,
                    () => ref.read(textScaleProvider.notifier).set(1.3)),
                const SizedBox(height: 8),
                Text(
                  'This works together with your phone\'s own font size '
                  'setting.',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          SectionCard(
            title: 'Appearance',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _choice(context, 'Light', mode == ThemeMode.light,
                    () => ref.read(themeModeProvider.notifier).set(ThemeMode.light)),
                _choice(context, 'Dark', mode == ThemeMode.dark,
                    () => ref.read(themeModeProvider.notifier).set(ThemeMode.dark)),
                _choice(context, 'Same as phone', mode == ThemeMode.system,
                    () => ref.read(themeModeProvider.notifier).set(ThemeMode.system)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _choice(BuildContext context, String label, bool selected,
      VoidCallback onTap) {
    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: Icon(
        selected ? Icons.radio_button_checked : Icons.radio_button_off,
        size: 30,
        color: selected ? Theme.of(context).colorScheme.primary : null,
      ),
      title: Text(label),
      onTap: onTap,
    );
  }
}
