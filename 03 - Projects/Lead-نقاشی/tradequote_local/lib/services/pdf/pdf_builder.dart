import 'dart:typed_data';

import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import '../../core/abn.dart';
import '../../core/dates.dart';
import '../../core/ids.dart';
import '../../core/money.dart';
import '../../domain/enums.dart';
import '../../domain/render_data.dart';

/// Builds professional A4 PDFs from a [DocumentRenderData] — and ONLY from
/// render data, so issued documents always print from their frozen snapshot
/// (invariant 2). Uses the pdf package's built-in Helvetica fonts (D-009):
/// no network, no assets, correct for Australian English documents.
class PdfBuilder {
  PdfBuilder._();

  static const PdfColor _ink = PdfColor.fromInt(0xFF1A1A1A);
  static const PdfColor _muted = PdfColor.fromInt(0xFF555555);
  static const PdfColor _accent = PdfColor.fromInt(0xFF0B5394);
  static const PdfColor _tableHeader = PdfColor.fromInt(0xFFE8EEF6);
  static const PdfColor _line = PdfColor.fromInt(0xFFCCCCCC);

  static String fileNameFor(DocumentRenderData d) {
    final type = d.docType == DocType.quote ? 'Quote' : 'Invoice';
    return sanitizeFileName('$type-${d.docNumber}-${d.customer.name}') + '.pdf';
  }

  static Future<Uint8List> build(DocumentRenderData d,
      {String? watermarkText}) async {
    final doc = pw.Document(
      title: '${d.title} ${d.docNumber}',
      producer: 'TradeQuote Local',
    );

    doc.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.fromLTRB(40, 36, 40, 40),
        header: (ctx) =>
            ctx.pageNumber == 1 ? pw.SizedBox() : _smallHeader(d),
        footer: (ctx) => _footer(d, ctx),
        build: (ctx) => [
          if (watermarkText != null) _watermarkBanner(watermarkText),
          _bigHeader(d),
          pw.SizedBox(height: 18),
          _partiesBlock(d),
          if ((d.scopeOfWork ?? '').trim().isNotEmpty) ...[
            pw.SizedBox(height: 16),
            _sectionTitle('Scope of work'),
            pw.Paragraph(
              text: d.scopeOfWork!.trim(),
              style: const pw.TextStyle(fontSize: 10.5, lineSpacing: 3),
            ),
          ],
          pw.SizedBox(height: 12),
          _lineTable(d),
          pw.SizedBox(height: 10),
          _totalsBlock(d),
          pw.SizedBox(height: 18),
          if (d.docType == DocType.invoice && d.bank.hasDetails)
            _paymentBlock(d),
          if ((d.customerNotes ?? '').trim().isNotEmpty) ...[
            pw.SizedBox(height: 14),
            _sectionTitle('Notes'),
            pw.Paragraph(
              text: d.customerNotes!.trim(),
              style: const pw.TextStyle(fontSize: 10, lineSpacing: 3),
            ),
          ],
          if ((d.terms ?? '').trim().isNotEmpty) ...[
            pw.SizedBox(height: 14),
            _sectionTitle('Terms'),
            pw.Paragraph(
              text: d.terms!.trim(),
              style: pw.TextStyle(
                  fontSize: 9, lineSpacing: 2.5, color: _muted),
            ),
          ],
          if (d.docType == DocType.quote) ...[
            pw.SizedBox(height: 26),
            _acceptanceBlock(d),
          ],
        ],
      ),
    );

    return doc.save();
  }

  // ------------------------------------------------------------ header/footer

  static pw.Widget _bigHeader(DocumentRenderData d) {
    final s = d.supplier;
    return pw.Row(
      crossAxisAlignment: pw.CrossAxisAlignment.start,
      children: [
        pw.Expanded(
          child: pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.Text(s.displayName,
                  style: pw.TextStyle(
                      fontSize: 20,
                      fontWeight: pw.FontWeight.bold,
                      color: _accent)),
              if (s.tradingName != null &&
                  s.tradingName!.trim().isNotEmpty &&
                  s.tradingName != s.legalName)
                pw.Text(s.legalName,
                    style: pw.TextStyle(fontSize: 10, color: _muted)),
              pw.SizedBox(height: 4),
              if ((s.abn ?? '').isNotEmpty)
                pw.Text('ABN ${Abn.format(s.abn!)}',
                    style: pw.TextStyle(fontSize: 10, color: _ink)),
              if ((s.address ?? '').isNotEmpty)
                pw.Text(s.address!,
                    style: pw.TextStyle(fontSize: 10, color: _muted)),
              pw.Row(children: [
                if ((s.phone ?? '').isNotEmpty)
                  pw.Text(s.phone!,
                      style: pw.TextStyle(fontSize: 10, color: _muted)),
                if ((s.phone ?? '').isNotEmpty && (s.email ?? '').isNotEmpty)
                  pw.Text('  ·  ',
                      style: pw.TextStyle(fontSize: 10, color: _muted)),
                if ((s.email ?? '').isNotEmpty)
                  pw.Text(s.email!,
                      style: pw.TextStyle(fontSize: 10, color: _muted)),
              ]),
            ],
          ),
        ),
        pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.end,
          children: [
            pw.Text(d.title,
                style: pw.TextStyle(
                    fontSize: 22, fontWeight: pw.FontWeight.bold)),
            pw.SizedBox(height: 4),
            pw.Text(d.docNumber,
                style: pw.TextStyle(
                    fontSize: 13, fontWeight: pw.FontWeight.bold)),
            pw.SizedBox(height: 4),
            _metaLine('Date', formatAuDate(d.issueDateMs)),
            if (d.docType == DocType.quote && d.expiryDateMs != null)
              _metaLine('Valid until', formatAuDate(d.expiryDateMs!)),
            if (d.docType == DocType.invoice && d.dueDateMs != null)
              _metaLine('Due date', formatAuDate(d.dueDateMs!)),
          ],
        ),
      ],
    );
  }

  static pw.Widget _smallHeader(DocumentRenderData d) => pw.Container(
        margin: const pw.EdgeInsets.only(bottom: 12),
        padding: const pw.EdgeInsets.only(bottom: 6),
        decoration: const pw.BoxDecoration(
            border: pw.Border(bottom: pw.BorderSide(color: _line))),
        child: pw.Row(
          mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
          children: [
            pw.Text(d.supplier.displayName,
                style: pw.TextStyle(fontSize: 10, color: _muted)),
            pw.Text('${d.title} ${d.docNumber} — continued',
                style: pw.TextStyle(fontSize: 10, color: _muted)),
          ],
        ),
      );

  static pw.Widget _footer(DocumentRenderData d, pw.Context ctx) {
    return pw.Container(
      margin: const pw.EdgeInsets.only(top: 10),
      padding: const pw.EdgeInsets.only(top: 6),
      decoration: const pw.BoxDecoration(
          border: pw.Border(top: pw.BorderSide(color: _line))),
      child: pw.Row(
        mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
        children: [
          pw.Expanded(
            child: pw.Text((d.footer ?? '').trim(),
                style: pw.TextStyle(fontSize: 8.5, color: _muted)),
          ),
          pw.Text('Page ${ctx.pageNumber} of ${ctx.pagesCount}',
              style: pw.TextStyle(fontSize: 8.5, color: _muted)),
        ],
      ),
    );
  }

  static pw.Widget _watermarkBanner(String text) => pw.Container(
        width: double.infinity,
        margin: const pw.EdgeInsets.only(bottom: 12),
        padding: const pw.EdgeInsets.all(8),
        decoration: pw.BoxDecoration(
          color: const PdfColor.fromInt(0xFFFDE8E8),
          border: pw.Border.all(color: const PdfColor.fromInt(0xFFB91C1C)),
        ),
        child: pw.Text(text,
            textAlign: pw.TextAlign.center,
            style: pw.TextStyle(
                fontSize: 14,
                fontWeight: pw.FontWeight.bold,
                color: const PdfColor.fromInt(0xFFB91C1C))),
      );

  // ----------------------------------------------------------------- parties

  static pw.Widget _partiesBlock(DocumentRenderData d) {
    final c = d.customer;
    final label = d.docType == DocType.quote ? 'Quote for' : 'Bill to';
    return pw.Row(
      crossAxisAlignment: pw.CrossAxisAlignment.start,
      children: [
        pw.Expanded(
          child: pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              _sectionTitle(label),
              pw.Text(c.name,
                  style: pw.TextStyle(
                      fontSize: 11.5, fontWeight: pw.FontWeight.bold)),
              if ((c.contactName ?? '').isNotEmpty)
                pw.Text(c.contactName!,
                    style: const pw.TextStyle(fontSize: 10)),
              if ((c.address ?? '').isNotEmpty)
                pw.Text(c.address!, style: const pw.TextStyle(fontSize: 10)),
              if ((c.abn ?? '').isNotEmpty)
                pw.Text('ABN ${Abn.format(c.abn!)}',
                    style: const pw.TextStyle(fontSize: 10)),
              if ((c.mobile ?? '').isNotEmpty)
                pw.Text(c.mobile!, style: const pw.TextStyle(fontSize: 10)),
              if ((c.email ?? '').isNotEmpty)
                pw.Text(c.email!, style: const pw.TextStyle(fontSize: 10)),
            ],
          ),
        ),
        pw.SizedBox(width: 24),
        if ((d.siteAddress ?? '').trim().isNotEmpty)
          pw.Expanded(
            child: pw.Column(
              crossAxisAlignment: pw.CrossAxisAlignment.start,
              children: [
                _sectionTitle('Job address'),
                pw.Text(d.siteAddress!.trim(),
                    style: const pw.TextStyle(fontSize: 10)),
                if ((d.workType ?? '').trim().isNotEmpty) ...[
                  pw.SizedBox(height: 4),
                  pw.Text('Work type: ${d.workType!.trim()}',
                      style: pw.TextStyle(fontSize: 10, color: _muted)),
                ],
              ],
            ),
          ),
      ],
    );
  }

  static pw.Widget _sectionTitle(String text) => pw.Container(
        margin: const pw.EdgeInsets.only(bottom: 4),
        child: pw.Text(text.toUpperCase(),
            style: pw.TextStyle(
                fontSize: 8.5,
                fontWeight: pw.FontWeight.bold,
                color: _muted,
                letterSpacing: 0.8)),
      );

  // ------------------------------------------------------------------- table

  static pw.Widget _lineTable(DocumentRenderData d) {
    final showGstColumn =
        d.gstMode != GstMode.none && !d.allLinesTaxable;
    final headers = [
      'Description',
      'Qty',
      'Unit price',
      if (showGstColumn) 'GST',
      'Amount',
    ];
    final rows = d.lines.map((l) {
      final qty = l.unitLabel == null || l.unitLabel!.isEmpty
          ? Quantity.format(l.quantityMilli)
          : '${Quantity.format(l.quantityMilli)} ${l.unitLabel}';
      return [
        l.description,
        qty,
        Money.format(l.unitPriceCents),
        if (showGstColumn) (l.gstApplicable ? 'GST' : 'GST-free'),
        Money.format(l.lineTotalCents),
      ];
    }).toList();

    return pw.TableHelper.fromTextArray(
      headers: headers,
      data: rows,
      border: null,
      headerDecoration: const pw.BoxDecoration(color: _tableHeader),
      headerStyle: pw.TextStyle(
          fontSize: 9.5, fontWeight: pw.FontWeight.bold, color: _ink),
      cellStyle: const pw.TextStyle(fontSize: 10),
      cellPadding:
          const pw.EdgeInsets.symmetric(horizontal: 6, vertical: 5),
      rowDecoration: const pw.BoxDecoration(
          border: pw.Border(bottom: pw.BorderSide(color: _line, width: 0.5))),
      cellAlignments: {
        0: pw.Alignment.centerLeft,
        1: pw.Alignment.centerRight,
        2: pw.Alignment.centerRight,
        if (showGstColumn) 3: pw.Alignment.centerRight,
        (showGstColumn ? 4 : 3): pw.Alignment.centerRight,
      },
      columnWidths: {
        0: const pw.FlexColumnWidth(5),
        1: const pw.FlexColumnWidth(1.4),
        2: const pw.FlexColumnWidth(1.8),
        if (showGstColumn) 3: const pw.FlexColumnWidth(1.3),
        (showGstColumn ? 4 : 3): const pw.FlexColumnWidth(1.8),
      },
    );
  }

  // ------------------------------------------------------------------ totals

  static pw.Widget _totalsBlock(DocumentRenderData d) {
    final rows = <pw.Widget>[];

    void addRow(String label, String value,
        {bool bold = false, double size = 10.5}) {
      rows.add(pw.Container(
        padding: const pw.EdgeInsets.symmetric(vertical: 2.5),
        child: pw.Row(
          mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
          children: [
            pw.Text(label,
                style: pw.TextStyle(
                    fontSize: size,
                    fontWeight:
                        bold ? pw.FontWeight.bold : pw.FontWeight.normal)),
            pw.Text(value,
                style: pw.TextStyle(
                    fontSize: size,
                    fontWeight:
                        bold ? pw.FontWeight.bold : pw.FontWeight.normal)),
          ],
        ),
      ));
    }

    String? note;
    switch (d.gstMode) {
      case GstMode.none:
        addRow('Total', Money.format(d.totalCents), bold: true, size: 13);
        note = d.docType == DocType.invoice
            ? 'No GST has been charged.'
            : null;
        break;
      case GstMode.exclusive:
        addRow('Subtotal (ex GST)', Money.format(d.subtotalExGstCents));
        addRow('GST (10%)', Money.format(d.gstCents));
        rows.add(pw.Divider(color: _line, height: 6));
        addRow('Total (inc GST)', Money.format(d.totalCents),
            bold: true, size: 13);
        break;
      case GstMode.inclusive:
        if (d.allLinesTaxable) {
          addRow('Total (inc GST)', Money.format(d.totalCents),
              bold: true, size: 13);
          // ATO-permitted presentation when GST is exactly 1/11 of the price.
          note =
              'Total price includes GST of ${Money.format(d.gstCents)}.';
        } else {
          addRow('Subtotal (ex GST)', Money.format(d.subtotalExGstCents));
          addRow('GST', Money.format(d.gstCents));
          rows.add(pw.Divider(color: _line, height: 6));
          addRow('Total (inc GST)', Money.format(d.totalCents),
              bold: true, size: 13);
          note = 'Some items are GST-free (shown in the GST column).';
        }
        break;
    }

    return pw.Row(
      mainAxisAlignment: pw.MainAxisAlignment.end,
      children: [
        pw.Container(
          width: 230,
          child: pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.stretch,
            children: [
              ...rows,
              if (note != null)
                pw.Container(
                  margin: const pw.EdgeInsets.only(top: 4),
                  child: pw.Text(note,
                      textAlign: pw.TextAlign.right,
                      style: pw.TextStyle(fontSize: 9, color: _muted)),
                ),
            ],
          ),
        ),
      ],
    );
  }

  // ---------------------------------------------------------------- payment

  static pw.Widget _paymentBlock(DocumentRenderData d) {
    final b = d.bank;
    return pw.Container(
      width: double.infinity,
      padding: const pw.EdgeInsets.all(10),
      decoration: pw.BoxDecoration(
        color: const PdfColor.fromInt(0xFFF5F7FA),
        border: pw.Border.all(color: _line, width: 0.5),
        borderRadius: pw.BorderRadius.circular(4),
      ),
      child: pw.Column(
        crossAxisAlignment: pw.CrossAxisAlignment.start,
        children: [
          _sectionTitle('How to pay'),
          if ((b.accountName ?? '').isNotEmpty)
            pw.Text('Account name: ${b.accountName}',
                style: const pw.TextStyle(fontSize: 10)),
          pw.Row(children: [
            if ((b.bsb ?? '').isNotEmpty)
              pw.Text('BSB: ${b.bsb}',
                  style: const pw.TextStyle(fontSize: 10)),
            if ((b.bsb ?? '').isNotEmpty &&
                (b.accountNumber ?? '').isNotEmpty)
              pw.Text('    ', style: const pw.TextStyle(fontSize: 10)),
            if ((b.accountNumber ?? '').isNotEmpty)
              pw.Text('Account: ${b.accountNumber}',
                  style: const pw.TextStyle(fontSize: 10)),
          ]),
          if ((b.instructions ?? '').isNotEmpty)
            pw.Text(b.instructions!,
                style: const pw.TextStyle(fontSize: 10)),
          pw.SizedBox(height: 3),
          pw.Text('Please use ${d.docNumber} as the payment reference.',
              style: pw.TextStyle(fontSize: 9.5, color: _muted)),
        ],
      ),
    );
  }

  // ------------------------------------------------------------- acceptance

  static pw.Widget _acceptanceBlock(DocumentRenderData d) {
    pw.Widget signatureLine(String label) => pw.Expanded(
          child: pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.Container(
                height: 26,
                decoration: const pw.BoxDecoration(
                    border:
                        pw.Border(bottom: pw.BorderSide(color: _ink))),
              ),
              pw.SizedBox(height: 3),
              pw.Text(label,
                  style: pw.TextStyle(fontSize: 9, color: _muted)),
            ],
          ),
        );

    return pw.Column(
      crossAxisAlignment: pw.CrossAxisAlignment.start,
      children: [
        _sectionTitle('Acceptance'),
        pw.Text(
          'I accept this quote and authorise the work described above.',
          style: const pw.TextStyle(fontSize: 10),
        ),
        pw.SizedBox(height: 16),
        pw.Row(children: [
          signatureLine('Signature'),
          pw.SizedBox(width: 20),
          signatureLine('Name'),
          pw.SizedBox(width: 20),
          signatureLine('Date'),
        ]),
      ],
    );
  }

  static pw.Widget _metaLine(String label, String value) => pw.Row(
        mainAxisSize: pw.MainAxisSize.min,
        children: [
          pw.Text('$label:  ',
              style: pw.TextStyle(fontSize: 10, color: _muted)),
          pw.Text(value, style: const pw.TextStyle(fontSize: 10)),
        ],
      );
}
