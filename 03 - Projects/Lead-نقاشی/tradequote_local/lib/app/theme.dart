import 'package:flutter/material.dart';

/// Senior-friendly Material 3 theme: large type, high contrast, generous
/// touch targets (primary actions 60+dp), clear field borders, one obvious
/// primary action per screen. Never relies on colour alone for status —
/// see StatusChip in shared/widgets.dart which always pairs colour + text.
ThemeData buildAppTheme(Brightness brightness) {
  final scheme = ColorScheme.fromSeed(
    seedColor: const Color(0xFF0B5394),
    brightness: brightness,
  );
  final base = ThemeData(colorScheme: scheme, useMaterial3: true);

  final textTheme = base.textTheme.copyWith(
    displaySmall: base.textTheme.displaySmall
        ?.copyWith(fontSize: 34, fontWeight: FontWeight.w700),
    headlineMedium: base.textTheme.headlineMedium
        ?.copyWith(fontSize: 26, fontWeight: FontWeight.w700),
    titleLarge: base.textTheme.titleLarge
        ?.copyWith(fontSize: 22, fontWeight: FontWeight.w700),
    titleMedium: base.textTheme.titleMedium
        ?.copyWith(fontSize: 18, fontWeight: FontWeight.w600),
    bodyLarge: base.textTheme.bodyLarge?.copyWith(fontSize: 18, height: 1.35),
    bodyMedium:
        base.textTheme.bodyMedium?.copyWith(fontSize: 16, height: 1.35),
    labelLarge: base.textTheme.labelLarge
        ?.copyWith(fontSize: 18, fontWeight: FontWeight.w600),
  );

  return base.copyWith(
    textTheme: textTheme,
    visualDensity: VisualDensity.comfortable,
    scaffoldBackgroundColor:
        brightness == Brightness.light ? const Color(0xFFF7F8FA) : null,
    appBarTheme: AppBarTheme(
      centerTitle: false,
      titleTextStyle: textTheme.titleLarge?.copyWith(
        color: scheme.onSurface,
      ),
      backgroundColor:
          brightness == Brightness.light ? const Color(0xFFF7F8FA) : null,
      elevation: 0,
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        minimumSize: const Size.fromHeight(62),
        textStyle: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        minimumSize: const Size.fromHeight(58),
        textStyle: const TextStyle(fontSize: 19, fontWeight: FontWeight.w600),
        side: BorderSide(color: scheme.primary, width: 1.6),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        minimumSize: const Size(48, 48),
        textStyle: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
      contentPadding:
          const EdgeInsets.symmetric(horizontal: 16, vertical: 18),
      labelStyle: const TextStyle(fontSize: 17),
      hintStyle: TextStyle(fontSize: 17, color: scheme.onSurfaceVariant),
      helperStyle: const TextStyle(fontSize: 14),
      errorStyle: const TextStyle(fontSize: 15),
      filled: true,
      fillColor: brightness == Brightness.light ? Colors.white : null,
    ),
    listTileTheme: ListTileThemeData(
      minVerticalPadding: 12,
      titleTextStyle: textTheme.titleMedium,
      subtitleTextStyle:
          textTheme.bodyMedium?.copyWith(color: scheme.onSurfaceVariant),
    ),
    cardTheme: const CardThemeData(
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.all(Radius.circular(16)),
        side: BorderSide(color: Color(0x22000000)),
      ),
    ),
    snackBarTheme: const SnackBarThemeData(
      behavior: SnackBarBehavior.floating,
      contentTextStyle: TextStyle(fontSize: 17),
    ),
    dialogTheme: DialogThemeData(
      titleTextStyle: textTheme.titleLarge?.copyWith(color: scheme.onSurface),
      contentTextStyle:
          textTheme.bodyLarge?.copyWith(color: scheme.onSurface),
    ),
  );
}
