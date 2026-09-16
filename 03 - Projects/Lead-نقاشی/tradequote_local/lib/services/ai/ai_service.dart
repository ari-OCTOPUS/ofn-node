import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../../core/errors.dart';

/// Optional AI assistance — OFF by default (D-012).
///
/// The owner's AI API ("Fugu") is configured at runtime in Settings:
/// endpoint + model in SharedPreferences, the API key ONLY in secure
/// storage. The adapter speaks the OpenAI-compatible `POST
/// {endpoint}/chat/completions` shape, which most hosted and self-hosted
/// gateways accept; adapting to a different shape is documented in
/// docs/integrations/FUGU_API_SETUP.md.
///
/// Rules enforced here and in the UI:
/// - Nothing is ever sent without an explicit user tap.
/// - Output is a SUGGESTION the user reviews before it is applied.
/// - Failures degrade to manual entry with a friendly message.
/// - The core app never needs this service to function.
class AiSettings {
  const AiSettings({
    required this.enabled,
    required this.endpoint,
    required this.model,
    required this.hasKey,
  });

  final bool enabled;
  final String endpoint;
  final String model;
  final bool hasKey;

  bool get isConfigured =>
      enabled && endpoint.trim().isNotEmpty && model.trim().isNotEmpty && hasKey;
}

class AiService {
  AiService(this._prefs, {FlutterSecureStorage? storage, http.Client? client})
      : _secure = storage ?? const FlutterSecureStorage(),
        _client = client ?? http.Client();

  static const _kEnabled = 'ai.enabled';
  static const _kEndpoint = 'ai.endpoint';
  static const _kModel = 'ai.model';
  static const _kSecureKey = 'ai.apiKey';

  final SharedPreferences _prefs;
  final FlutterSecureStorage _secure;
  final http.Client _client;

  Future<AiSettings> settings() async {
    final key = await _secure.read(key: _kSecureKey);
    return AiSettings(
      enabled: _prefs.getBool(_kEnabled) ?? false,
      endpoint: _prefs.getString(_kEndpoint) ?? '',
      model: _prefs.getString(_kModel) ?? '',
      hasKey: key != null && key.isNotEmpty,
    );
  }

  Future<void> saveSettings({
    required bool enabled,
    required String endpoint,
    required String model,
    String? apiKey,
  }) async {
    await _prefs.setBool(_kEnabled, enabled);
    await _prefs.setString(_kEndpoint, endpoint.trim());
    await _prefs.setString(_kModel, model.trim());
    if (apiKey != null && apiKey.trim().isNotEmpty) {
      await _secure.write(key: _kSecureKey, value: apiKey.trim());
    }
  }

  /// "Disconnect AI": wipes the key and disables every feature.
  Future<void> disconnect() async {
    await _secure.delete(key: _kSecureKey);
    await _prefs.setBool(_kEnabled, false);
  }

  /// Rewrites a short customer message more politely/clearly. The caller
  /// shows the result beside the original with Use / Keep mine buttons.
  Future<String> improveMessage(String message) async {
    final reply = await _chat(
      system:
          'You improve short business messages for an Australian painting '
          'company. Keep the meaning, keep it brief and polite, use '
          'Australian English. Return ONLY the improved message text with '
          'no preamble and no quotation marks.',
      user: message,
    );
    return reply.trim();
  }

  /// Settings-screen "Test connection" button.
  Future<bool> testConnection() async {
    try {
      final reply = await _chat(
        system: 'Reply with the single word OK.',
        user: 'Connection test.',
      );
      return reply.trim().isNotEmpty;
    } on AiUnavailableException {
      return false;
    }
  }

  Future<String> _chat({required String system, required String user}) async {
    final s = await settings();
    if (!s.isConfigured) {
      throw const AiUnavailableException();
    }
    final key = await _secure.read(key: _kSecureKey);
    var base = s.endpoint.trim();
    while (base.endsWith('/')) {
      base = base.substring(0, base.length - 1);
    }
    final uri = Uri.parse(base.endsWith('/chat/completions')
        ? base
        : '$base/chat/completions');
    try {
      final response = await _client
          .post(
            uri,
            headers: {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer $key',
            },
            body: jsonEncode({
              'model': s.model,
              'messages': [
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': user},
              ],
              'temperature': 0.4,
            }),
          )
          .timeout(const Duration(seconds: 20));
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw const AiUnavailableException();
      }
      final json =
          (jsonDecode(response.body) as Map).cast<String, dynamic>();
      final choices = json['choices'] as List?;
      if (choices == null || choices.isEmpty) {
        throw const AiUnavailableException();
      }
      final first = (choices.first as Map).cast<String, dynamic>();
      final msg = (first['message'] as Map?)?.cast<String, dynamic>();
      final content = msg?['content'] as String?;
      if (content == null || content.trim().isEmpty) {
        throw const AiUnavailableException();
      }
      return content;
    } on AiUnavailableException {
      rethrow;
    } catch (_) {
      // Timeouts, DNS failures, malformed responses — same friendly outcome.
      throw const AiUnavailableException();
    }
  }
}
