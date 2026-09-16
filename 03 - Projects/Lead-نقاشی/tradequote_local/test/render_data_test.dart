import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:tradequote_local/domain/enums.dart';
import 'package:tradequote_local/domain/render_data.dart';

void main() {
  DocumentRenderData sample() => DocumentRenderData(
        docType: DocType.invoice,
        docNumber: 'INV-1001',
        issueDateMs: 1752900000000,
        dueDateMs: 1754100000000,
        supplier: const RenderSupplier(
          legalName: 'Test Painting Pty Ltd',
          abn: '51824753556',
          gstRegistered: true,
          address: '1 Example St, Sydney NSW',
        ),
        customer: const RenderCustomer(
            name: 'John Smith', address: '15 George St, Parramatta'),
        siteAddress: '15 George St, Parramatta',
        scopeOfWork: 'Interior painting',
        lines: const [
          RenderLine(
            description: 'Painting work',
            quantityMilli: 1000,
            unitPriceCents: 275000,
            gstApplicable: true,
            lineTotalCents: 275000,
          ),
        ],
        gstMode: GstMode.inclusive,
        subtotalExGstCents: 250000,
        gstCents: 25000,
        totalCents: 275000,
        bank: const RenderBank(
            accountName: 'Test Painting', bsb: '062-000', accountNumber: '12345678'),
      );

  test('JSON round-trip preserves every rendered field', () {
    final original = sample();
    final decoded = DocumentRenderData.fromJson(
        (jsonDecode(jsonEncode(original.toJson())) as Map)
            .cast<String, dynamic>());
    expect(decoded.docNumber, original.docNumber);
    expect(decoded.docType, original.docType);
    expect(decoded.supplier.legalName, original.supplier.legalName);
    expect(decoded.supplier.abn, original.supplier.abn);
    expect(decoded.customer.name, original.customer.name);
    expect(decoded.lines, hasLength(1));
    expect(decoded.lines.first.lineTotalCents, 275000);
    expect(decoded.gstMode, GstMode.inclusive);
    expect(decoded.totalCents, 275000);
    expect(decoded.bank.bsb, '062-000');
  });

  test('title follows ATO rules', () {
    expect(sample().title, 'TAX INVOICE');
    final unregistered = DocumentRenderData.fromJson(sample().toJson()
      ..['supplier'] = const RenderSupplier(
              legalName: 'X', gstRegistered: false)
          .toJson());
    expect(unregistered.title, 'INVOICE');
    final quote = DocumentRenderData.fromJson(
        sample().toJson()..['docType'] = 'quote');
    expect(quote.title, 'QUOTE');
  });

  test('stored totals match recomputation (snapshot consistency)', () {
    final t = sample().recomputeTotals();
    expect(t.totalCents, 275000);
    expect(t.gstCents, 25000);
    expect(t.subtotalExGstCents, 250000);
  });

  test('fromJson tolerates missing optional fields', () {
    final minimal = DocumentRenderData.fromJson(const {
      'docType': 'quote',
      'docNumber': 'Q-1',
      'issueDateMs': 0,
      'lines': <Object>[],
      'gstMode': 'none',
    });
    expect(minimal.docNumber, 'Q-1');
    expect(minimal.lines, isEmpty);
    expect(minimal.supplier.legalName, '');
    expect(minimal.bank.hasDetails, isFalse);
  });
}
