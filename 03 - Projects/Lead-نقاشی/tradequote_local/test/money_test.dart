import 'package:flutter_test/flutter_test.dart';
import 'package:tradequote_local/core/money.dart';

void main() {
  group('Money.tryParse', () {
    test('plain dollars', () => expect(Money.tryParse('2500'), 250000));
    test('with cents', () => expect(Money.tryParse('2500.50'), 250050));
    test('single decimal digit means tens of cents',
        () => expect(Money.tryParse('2500.5'), 250050));
    test('dollar sign and commas',
        () => expect(Money.tryParse(r' $2,500.00 '), 250000));
    test('zero is allowed by parser',
        () => expect(Money.tryParse('0'), 0));
    test('garbage is null', () => expect(Money.tryParse('abc'), isNull));
    test('negative is null', () => expect(Money.tryParse('-5'), isNull));
    test('three decimals is null',
        () => expect(Money.tryParse('1.234'), isNull));
    test('empty is null', () => expect(Money.tryParse('  '), isNull));
  });

  group('Money.format', () {
    test('formats cents with thousands separators',
        () => expect(Money.format(275000), r'$2,750.00'));
    test('formats zero', () => expect(Money.format(0), r'$0.00'));
    test('formats odd cents', () => expect(Money.format(91), r'$0.91'));
  });

  group('Quantity', () {
    test('parse whole', () => expect(Quantity.tryParseMilli('2'), 2000));
    test('parse decimal', () => expect(Quantity.tryParseMilli('2.5'), 2500));
    test('parse three decimals',
        () => expect(Quantity.tryParseMilli('0.333'), 333));
    test('reject four decimals',
        () => expect(Quantity.tryParseMilli('1.2345'), isNull));
    test('format round-trip', () {
      expect(Quantity.format(2500), '2.5');
      expect(Quantity.format(1000), '1');
      expect(Quantity.format(333), '0.333');
    });
  });
}
