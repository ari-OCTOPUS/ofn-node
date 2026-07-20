import 'package:drift/drift.dart' show Value;
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tradequote_local/data/db/database.dart';
import 'package:tradequote_local/features/onboarding/company_form.dart';

void main() {
  Future<void> pumpForm(
    WidgetTester tester, {
    required Future<void> Function(CompanySettingsCompanion) onSubmit,
  }) async {
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: CompanyForm(submitLabel: 'Save and start', onSubmit: onSubmit),
      ),
    ));
  }

  testWidgets('empty business name blocks saving with a plain message',
      (tester) async {
    var submitted = false;
    await pumpForm(tester, onSubmit: (_) async => submitted = true);

    await tester.tap(find.text('Save and start'));
    await tester.pumpAndSettle();

    expect(find.text('Please enter your business name'), findsOneWidget);
    expect(submitted, isFalse);
  });

  testWidgets('invalid ABN shows the friendly senior-style message',
      (tester) async {
    var submitted = false;
    await pumpForm(tester, onSubmit: (_) async => submitted = true);

    await tester.enterText(
        find.widgetWithText(TextFormField, 'Business name *'),
        'Your Painting Company Pty Ltd');
    await tester.enterText(
        find.widgetWithText(TextFormField, 'ABN'), '11111111111');
    await tester.tap(find.text('Save and start'));
    await tester.pumpAndSettle();

    expect(
        find.textContaining('does not appear to be valid'), findsOneWidget);
    expect(submitted, isFalse);
  });

  testWidgets('valid minimal input submits normalized values',
      (tester) async {
    CompanySettingsCompanion? received;
    await pumpForm(tester, onSubmit: (v) async => received = v);

    await tester.enterText(
        find.widgetWithText(TextFormField, 'Business name *'),
        'Your Painting Company Pty Ltd');
    await tester.enterText(
        find.widgetWithText(TextFormField, 'ABN'), '51 824 753 556');
    await tester.tap(find.text('Save and start'));
    await tester.pumpAndSettle();

    expect(received, isNotNull);
    expect(received!.legalName, const Value('Your Painting Company Pty Ltd'));
    expect(received!.abn, const Value<String?>('51824753556'),
        reason: 'ABN must be stored normalized (11 digits, no spaces)');
    expect(received!.gstRegistered, const Value(false));
    expect(received!.gstMode, const Value('none'),
        reason: 'not GST registered -> documents must not show GST');
  });
}
