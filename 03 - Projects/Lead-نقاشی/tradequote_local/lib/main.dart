import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'app/app.dart';
import 'data/db/database.dart';
import 'data/repositories/settings_repository.dart';
import 'providers.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Friendly release-mode error surface — never a red screen of stack
  // traces for the owner. Details still go to the debug log.
  if (kReleaseMode) {
    ErrorWidget.builder = (details) => Material(
          child: Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Text(
                'Something went wrong on this screen.\n'
                'Your saved information is safe.\n'
                'Please go back and try again.',
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 18),
              ),
            ),
          ),
        );
  }

  final db = await AppDatabase.open();
  DbHandle.instance = db;
  final settings = await SettingsRepository(db).get();
  final prefs = await SharedPreferences.getInstance();

  runApp(
    ProviderScope(
      overrides: [sharedPrefsProvider.overrideWithValue(prefs)],
      child: TradeQuoteApp(initialOnboarded: settings.onboardingComplete),
    ),
  );
}
