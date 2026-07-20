import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../providers.dart';
import '../../shared/widgets.dart';

/// Optional AI assistance — OFF by default (D-012). The app works fully
/// without it. The API key lives only in the phone's secure storage.
class AiSettingsScreen extends ConsumerStatefulWidget {
  const AiSettingsScreen({super.key});

  @override
  ConsumerState<AiSettingsScreen> createState() => _AiSettingsScreenState();
}

class _AiSettingsScreenState extends ConsumerState<AiSettingsScreen> {
  final _endpoint = TextEditingController();
  final _model = TextEditingController();
  final _apiKey = TextEditingController();
  bool _enabled = false;
  bool _hasKey = false;
  bool _loading = true;
  bool _busy = false;
  String? _testResult;

  @override
  void initState() {
    super.initState();
    Future.microtask(_load);
  }

  Future<void> _load() async {
    final s = await ref.read(aiServiceProvider).settings();
    if (!mounted) return;
    setState(() {
      _enabled = s.enabled;
      _endpoint.text = s.endpoint;
      _model.text = s.model;
      _hasKey = s.hasKey;
      _loading = false;
    });
  }

  @override
  void dispose() {
    _endpoint.dispose();
    _model.dispose();
    _apiKey.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    setState(() => _busy = true);
    try {
      await ref.read(aiServiceProvider).saveSettings(
            enabled: _enabled,
            endpoint: _endpoint.text,
            model: _model.text,
            apiKey: _apiKey.text.trim().isEmpty ? null : _apiKey.text,
          );
      ref.invalidate(aiSettingsProvider);
      _apiKey.clear();
      await _load();
      if (mounted) showSuccessSnack(context, 'AI settings saved.');
    } catch (e) {
      if (mounted) showErrorSnack(context, e);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _test() async {
    setState(() {
      _busy = true;
      _testResult = null;
    });
    await ref.read(aiServiceProvider).saveSettings(
          enabled: _enabled,
          endpoint: _endpoint.text,
          model: _model.text,
          apiKey: _apiKey.text.trim().isEmpty ? null : _apiKey.text,
        );
    final ok = await ref.read(aiServiceProvider).testConnection();
    ref.invalidate(aiSettingsProvider);
    if (mounted) {
      setState(() {
        _busy = false;
        _testResult = ok
            ? 'Connected — AI assistance is working.'
            : 'Could not connect. Check the address, model name and key. '
                'The app still works fully without AI.';
      });
    }
  }

  Future<void> _disconnect() async {
    final ok = await showConfirmSheet(
      context,
      title: 'Disconnect AI?',
      message: 'The saved key is deleted from this phone and all AI '
          'features turn off. Everything else keeps working normally.',
      confirmLabel: 'Disconnect',
      destructive: true,
    );
    if (!ok) return;
    await ref.read(aiServiceProvider).disconnect();
    ref.invalidate(aiSettingsProvider);
    await _load();
    if (mounted) showSuccessSnack(context, 'AI is disconnected.');
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return Scaffold(
        appBar: AppBar(title: const Text('AI assistance')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }
    return Scaffold(
      appBar: AppBar(title: const Text('AI assistance')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            title: const Text('AI assistance'),
            subtitle: const Text(
                'Optional. Needs internet and your own AI service.'),
            value: _enabled,
            onChanged: (v) => setState(() => _enabled = v),
          ),
          const SizedBox(height: 8),
          SectionCard(
            title: 'Your AI service',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextField(
                  controller: _endpoint,
                  keyboardType: TextInputType.url,
                  decoration: const InputDecoration(
                    labelText: 'Service address',
                    helperText:
                        'For example: https://api.your-service.com/v1',
                  ),
                ),
                const SizedBox(height: 14),
                TextField(
                  controller: _model,
                  decoration: const InputDecoration(
                    labelText: 'Model name',
                  ),
                ),
                const SizedBox(height: 14),
                TextField(
                  controller: _apiKey,
                  obscureText: true,
                  decoration: InputDecoration(
                    labelText: 'API key',
                    helperText: _hasKey
                        ? 'A key is saved securely on this phone. Enter a '
                            'new one only to replace it.'
                        : 'Stored only in this phone\'s secure storage.',
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          BigButton(
            label: _busy ? 'Working…' : 'Save AI settings',
            onPressed: _busy ? null : _save,
          ),
          const SizedBox(height: 12),
          BigOutlinedButton(
            label: 'Test connection',
            icon: Icons.wifi_tethering,
            onPressed: _busy ? null : _test,
          ),
          if (_testResult != null) ...[
            const SizedBox(height: 12),
            Text(_testResult!,
                style: Theme.of(context).textTheme.bodyLarge),
          ],
          const SizedBox(height: 24),
          SectionCard(
            title: 'What is sent to your AI service?',
            child: Text(
              'Only what you choose, only when you tap an AI button. '
              'Today that is: the message text you are improving. '
              'Customer records, invoices and your business data are '
              'never sent in the background. Suggestions are always shown '
              'to you first — nothing is saved without your OK.',
              style: Theme.of(context).textTheme.bodyLarge,
            ),
          ),
          const SizedBox(height: 16),
          if (_hasKey)
            BigOutlinedButton(
              label: 'Disconnect AI and delete key',
              icon: Icons.link_off,
              onPressed: _busy ? null : _disconnect,
            ),
          const SizedBox(height: 12),
          BigOutlinedButton(
            label: 'Back',
            onPressed: () => context.pop(),
          ),
          const SizedBox(height: 32),
        ],
      ),
    );
  }
}
