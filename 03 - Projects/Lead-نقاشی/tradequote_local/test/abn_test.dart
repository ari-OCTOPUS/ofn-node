import 'package:flutter_test/flutter_test.dart';
import 'package:tradequote_local/core/abn.dart';

/// ABN checksum per ABR "Format of the ABN" (modulus 89). Cases mirror
/// tool/validate_financial_logic.py, which executed them successfully.
void main() {
  group('Abn.isValid', () {
    test('ABR worked example 51 824 753 556 is valid',
        () => expect(Abn.isValid('51 824 753 556'), isTrue));
    test('known real ABN 33 051 775 556 is valid',
        () => expect(Abn.isValid('33051775556'), isTrue));
    test('single-digit mutation is invalid',
        () => expect(Abn.isValid('51 824 753 557'), isFalse));
    test('too short is invalid',
        () => expect(Abn.isValid('5182475355'), isFalse));
    test('punctuation is stripped before validation',
        () => expect(Abn.isValid('ABN 51-824-753-556'), isTrue));
    test('leading zero is invalid',
        () => expect(Abn.isValid('01 824 753 556'), isFalse));
    test('empty is invalid', () => expect(Abn.isValid(''), isFalse));
  });

  group('Abn.normalize / format', () {
    test('normalize strips everything but digits',
        () => expect(Abn.normalize('ABN: 51 824-753.556'), '51824753556'));
    test('format renders NN NNN NNN NNN',
        () => expect(Abn.format('51824753556'), '51 824 753 556'));
    test('format leaves non-11-digit input unchanged',
        () => expect(Abn.format('123'), '123'));
  });
}
