import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../providers.dart';
import 'router.dart';
import 'theme.dart';

class TradeQuoteApp extends ConsumerStatefulWidget {
  const TradeQuoteApp({super.key, required this.initialOnboarded});

  final bool initialOnboarded;

  @override
  ConsumerState<TradeQuoteApp> createState() => _TradeQuoteAppState();
}

class _TradeQuoteAppState extends ConsumerState<TradeQuoteApp> {
  late final GoRouter _router;

  @override
  void initState() {
    super.initState();
    _router = buildRouter(onboarded: widget.initialOnboarded);
  }

  @override
  Widget build(BuildContext context) {
    final themeMode = ref.watch(themeModeProvider);
    final appScale = ref.watch(textScaleProvider);
    return MaterialApp.router(
      title: kAppName,
      debugShowCheckedModeBanner: false,
      routerConfig: _router,
      theme: buildAppTheme(Brightness.light),
      darkTheme: buildAppTheme(Brightness.dark),
      themeMode: themeMode,
      builder: (context, child) {
        // Multiply the system text scale by the in-app preference
        // (Normal 1.0 / Large 1.15 / Extra large 1.3 — default Large).
        final mq = MediaQuery.of(context);
        final systemFactor = mq.textScaler.scale(1.0);
        return MediaQuery(
          data: mq.copyWith(
            textScaler: TextScaler.linear(systemFactor * appScale),
          ),
          child: child ?? const SizedBox.shrink(),
        );
      },
    );
  }
}
