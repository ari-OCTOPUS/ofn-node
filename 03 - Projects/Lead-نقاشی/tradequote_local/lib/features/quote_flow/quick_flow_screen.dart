import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/dates.dart';
import '../../core/errors.dart';
import '../../core/gst.dart';
import '../../core/money.dart';
import '../../data/db/database.dart';
import '../../data/repositories/document_repository.dart';
import '../../domain/enums.dart';
import '../../providers.dart';
import '../../shared/widgets.dart';

/// The senior-friendly Quick Quote / Quick Invoice flow:
///   1. Describe the work   2. Price   3. Review → Send
/// The draft is a real database row from the start (D-013), auto-saved on
/// every step change and before anything external opens — accidental Back,
/// Home or app switches never lose work.
class QuickFlowScreen extends ConsumerStatefulWidget {
  const QuickFlowScreen({
    super.key,
    required this.docType,
    this.existingDocumentId,
  });

  final DocType docType;
  final String? existingDocumentId;

  @override
  ConsumerState<QuickFlowScreen> createState() => _QuickFlowScreenState();
}

class _LineEdit {
  _LineEdit({String description = '', String qty = '1', String price = '',
      this.gstApplicable = true})
      : description = TextEditingController(text: description),
        qty = TextEditingController(text: qty),
        price = TextEditingController(text: price);

  final TextEditingController description;
  final TextEditingController qty;
  final TextEditingController price;
  bool gstApplicable;

  void dispose() {
    description.dispose();
    qty.dispose();
    price.dispose();
  }
}

class _QuickFlowScreenState extends ConsumerState<QuickFlowScreen> {
  DocumentRow? _doc;
  int _step = 0;
  bool _starting = true;
  bool _saving = false;

  final _scope = TextEditingController();
  final _siteAddress = TextEditingController();
  final _simpleAmount = TextEditingController();
  String? _workType;
  bool _simpleMode = true;
  GstMode _gstMode = GstMode.inclusive;
  bool _gstRegistered = false;
  final List<_LineEdit> _lines = [];

  static const _stepTitles = [
    'Describe the work',
    'Price',
    'Check and send',
  ];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _start());
  }

  Future<void> _start() async {
    final settings = await ref.read(settingsRepositoryProvider).get();
    _gstRegistered = settings.gstRegistered;

    if (widget.existingDocumentId != null) {
      final repo = ref.read(documentRepositoryProvider);
      final doc = await repo.byId(widget.existingDocumentId!);
      if (doc == null) {
        if (mounted) {
          showErrorSnack(
              context, const AppException('This document could not be found.'));
          context.pop();
        }
        return;
      }
      final lines = await repo.linesFor(doc.id);
      if (!mounted) return;
      setState(() {
        _doc = doc;
        _scope.text = doc.scopeOfWork ?? '';
        _siteAddress.text = doc.siteAddress ?? '';
        _workType = doc.workType;
        _gstMode = GstMode.fromName(doc.gstMode);
        if (lines.length <= 1) {
          _simpleMode = true;
          if (lines.isNotEmpty) {
            _simpleAmount.text = _centsToInput(lines.first.lineTotalCents);
          }
        } else {
          _simpleMode = false;
          for (final l in lines) {
            _lines.add(_LineEdit(
              description: l.description,
              qty: Quantity.format(l.quantityMilli),
              price: _centsToInput(l.unitPriceCents),
              gstApplicable: l.gstApplicable,
            ));
          }
        }
        _starting = false;
      });
      return;
    }

    // Started without a draft (e.g. deep entry): pick the customer now.
    if (!mounted) return;
    final customer = await context.push<CustomerRow>('/customers?pick=1');
    if (!mounted) return;
    if (customer == null) {
      context.pop();
      return;
    }
    try {
      final doc = await ref
          .read(documentRepositoryProvider)
          .createDraft(type: widget.docType, customer: customer);
      if (!mounted) return;
      setState(() {
        _doc = doc;
        _siteAddress.text = doc.siteAddress ?? '';
        _gstMode = GstMode.fromName(doc.gstMode);
        _starting = false;
      });
    } catch (e) {
      if (mounted) {
        showErrorSnack(context, e);
        context.pop();
      }
    }
  }

  String _centsToInput(int cents) =>
      cents % 100 == 0 ? '${cents ~/ 100}' : (cents / 100).toStringAsFixed(2);

  @override
  void dispose() {
    _scope.dispose();
    _siteAddress.dispose();
    _simpleAmount.dispose();
    for (final l in _lines) {
      l.dispose();
    }
    super.dispose();
  }

  List<DraftLineInput> _collectLines() {
    if (_simpleMode) {
      final cents = Money.tryParse(_simpleAmount.text);
      if (cents == null || cents <= 0) return const [];
      return [
        DraftLineInput(
          description: 'Painting work as described',
          unitPriceCents: cents,
        ),
      ];
    }
    final out = <DraftLineInput>[];
    for (final l in _lines) {
      final price = Money.tryParse(l.price.text);
      final qty = Quantity.tryParseMilli(
          l.qty.text.trim().isEmpty ? '1' : l.qty.text);
      final desc = l.description.text.trim();
      if (price == null || qty == null || qty == 0 || desc.isEmpty) continue;
      out.add(DraftLineInput(
        description: desc,
        quantityMilli: qty,
        unitPriceCents: price,
        gstApplicable: l.gstApplicable,
      ));
    }
    return out;
  }

  DocumentTotals get _totals => GstCalculator.compute(
        _gstRegistered ? _gstMode : GstMode.none,
        _collectLines()
            .map((l) => GstLine(
                  quantityMilli: l.quantityMilli,
                  unitPriceCents: l.unitPriceCents,
                  gstApplicable: l.gstApplicable,
                ))
            .toList(),
      );

  Future<bool> _save() async {
    final doc = _doc;
    if (doc == null) return false;
    setState(() => _saving = true);
    try {
      await ref.read(documentRepositoryProvider).updateDraft(
            id: doc.id,
            scopeOfWork: _scope.text.trim(),
            siteAddress: _siteAddress.text.trim(),
            workType: _workType ?? '',
            gstMode: _gstRegistered ? _gstMode : GstMode.none,
            lines: _collectLines(),
          );
      return true;
    } catch (e) {
      if (mounted) showErrorSnack(context, e);
      return false;
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _next() async {
    if (_step == 1 && _collectLines().isEmpty) {
      showErrorSnack(context,
          const AppException('Please enter a price before going on.'));
      return;
    }
    await _save();
    if (mounted) setState(() => _step += 1);
  }

  Future<void> _back() async {
    await _save();
    if (mounted) setState(() => _step -= 1);
  }

  Future<void> _send() async {
    if (_collectLines().isEmpty) {
      setState(() => _step = 1);
      showErrorSnack(context,
          const AppException('Please enter a price before sending.'));
      return;
    }
    if (await _save() && mounted) {
      await context.push('/documents/${_doc!.id}/share');
    }
  }

  Future<void> _preview() async {
    if (await _save() && mounted) {
      await context.push('/documents/${_doc!.id}/preview');
    }
  }

  Future<void> _saveForLater() async {
    if (await _save() && mounted) {
      showSuccessSnack(context,
          '${widget.docType.label} ${_doc!.docNumber} is saved. You can '
          'continue it any time from Home.');
      context.go('/');
    }
  }

  @override
  Widget build(BuildContext context) {
    final doc = _doc;
    if (_starting || doc == null) {
      return Scaffold(
        appBar: AppBar(title: Text('New ${widget.docType.label}')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }
    return PopScope(
      onPopInvokedWithResult: (didPop, _) {
        if (didPop) unawaited(_save());
      },
      child: Scaffold(
        appBar: AppBar(
          title: Text('${widget.docType.label} ${doc.docNumber}'),
          actions: [
            Center(
              child: Padding(
                padding: const EdgeInsets.only(right: 16),
                child: Text(
                  _saving ? 'Saving…' : 'Saved',
                  style: Theme.of(context)
                      .textTheme
                      .bodyMedium
                      ?.copyWith(color: Theme.of(context).colorScheme.primary),
                ),
              ),
            ),
          ],
        ),
        body: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 4, 20, 0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  LinearProgressIndicator(
                      value: (_step + 1) / 3, minHeight: 6),
                  const SizedBox(height: 8),
                  Text(
                    'Step ${_step + 1} of 3 — ${_stepTitles[_step]}',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ],
              ),
            ),
            Expanded(
              child: switch (_step) {
                0 => _describeStep(),
                1 => _priceStep(),
                _ => _reviewStep(doc),
              },
            ),
          ],
        ),
        bottomNavigationBar: SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 8, 20, 16),
            child: _step < 2
                ? Row(
                    children: [
                      if (_step > 0)
                        Expanded(
                          child: BigOutlinedButton(
                              label: 'Back', onPressed: _back),
                        ),
                      if (_step > 0) const SizedBox(width: 12),
                      Expanded(
                        flex: 2,
                        child: BigButton(label: 'Next', onPressed: _next),
                      ),
                    ],
                  )
                : const SizedBox.shrink(),
          ),
        ),
      ),
    );
  }

  // ------------------------------------------------------- step 1: describe

  Widget _describeStep() {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        TextField(
          controller: _scope,
          maxLines: 5,
          minLines: 3,
          textCapitalization: TextCapitalization.sentences,
          decoration: const InputDecoration(
            labelText: 'What work will you do?',
            hintText: 'For example: Paint the living room and two '
                'bedrooms — walls and ceilings, two coats.',
          ),
        ),
        const SizedBox(height: 10),
        Text('Quick fill:', style: Theme.of(context).textTheme.bodyMedium),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final t in kDescriptionTemplates)
              ActionChip(
                label: Text(t.length > 34 ? '${t.substring(0, 34)}…' : t),
                onPressed: () {
                  final current = _scope.text.trim();
                  _scope.text = current.isEmpty ? t : '$current\n$t';
                },
              ),
          ],
        ),
        const SizedBox(height: 20),
        TextField(
          controller: _siteAddress,
          maxLines: 2,
          minLines: 1,
          textCapitalization: TextCapitalization.words,
          decoration: const InputDecoration(
            labelText: 'Job address',
            helperText: 'Optional — shown on the document',
          ),
        ),
        const SizedBox(height: 20),
        Text('Type of work (optional):',
            style: Theme.of(context).textTheme.bodyMedium),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final w in kWorkTypes)
              ChoiceChip(
                label: Text(w),
                selected: _workType == w,
                onSelected: (sel) =>
                    setState(() => _workType = sel ? w : null),
              ),
          ],
        ),
        const SizedBox(height: 24),
      ],
    );
  }

  // ---------------------------------------------------------- step 2: price

  Widget _priceStep() {
    final totals = _totals;
    final hasPrice = _collectLines().isNotEmpty;
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        SegmentedButton<bool>(
          segments: const [
            ButtonSegment(value: true, label: Text('One price')),
            ButtonSegment(value: false, label: Text('Item by item')),
          ],
          selected: {_simpleMode},
          onSelectionChanged: (s) => setState(() {
            _simpleMode = s.first;
            if (!_simpleMode && _lines.isEmpty) {
              _lines.add(_LineEdit(
                  description: _scope.text.trim().isEmpty
                      ? ''
                      : 'Painting work as described',
                  price: _simpleAmount.text));
            }
          }),
        ),
        const SizedBox(height: 20),
        if (_simpleMode)
          TextField(
            controller: _simpleAmount,
            keyboardType:
                const TextInputType.numberWithOptions(decimal: true),
            style: const TextStyle(
                fontSize: 30, fontWeight: FontWeight.w700),
            onChanged: (_) => setState(() {}),
            decoration: InputDecoration(
              labelText: 'Price for the whole job',
              prefixText: r'$ ',
              prefixStyle: const TextStyle(
                  fontSize: 30, fontWeight: FontWeight.w700),
              helperText: !_gstRegistered
                  ? 'You are not registered for GST, so no GST is added.'
                  : (_gstMode == GstMode.inclusive
                      ? 'This price includes GST.'
                      : 'GST (10%) will be added to this price.'),
            ),
          )
        else
          _itemEditor(),
        if (_gstRegistered) ...[
          const SizedBox(height: 14),
          ExpansionTile(
            title: const Text('More options'),
            tilePadding: EdgeInsets.zero,
            children: [
              Align(
                alignment: Alignment.centerLeft,
                child: Text('When you type a price, that price…',
                    style: Theme.of(context).textTheme.bodyMedium),
              ),
              const SizedBox(height: 8),
              SegmentedButton<GstMode>(
                segments: const [
                  ButtonSegment(
                      value: GstMode.inclusive, label: Text('Includes GST')),
                  ButtonSegment(
                      value: GstMode.exclusive,
                      label: Text('GST added on top')),
                ],
                selected: {_gstMode},
                onSelectionChanged: (s) =>
                    setState(() => _gstMode = s.first),
              ),
              const SizedBox(height: 12),
            ],
          ),
        ],
        const SizedBox(height: 18),
        if (hasPrice)
          SectionCard(
            child: Column(
              children: [
                if (totals.gstCents > 0) ...[
                  _totalRow('Before GST',
                      Money.format(totals.subtotalExGstCents)),
                  _totalRow('GST', Money.format(totals.gstCents)),
                  const Divider(),
                ],
                _totalRow('Total', Money.format(totals.totalCents),
                    big: true),
              ],
            ),
          ),
        const SizedBox(height: 24),
      ],
    );
  }

  Widget _itemEditor() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (var i = 0; i < _lines.length; i++) _lineCard(i),
        const SizedBox(height: 8),
        BigOutlinedButton(
          label: 'Add another item',
          icon: Icons.add,
          onPressed: () => setState(() => _lines.add(_LineEdit())),
        ),
      ],
    );
  }

  Widget _lineCard(int index) {
    final line = _lines[index];
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          children: [
            TextField(
              controller: line.description,
              textCapitalization: TextCapitalization.sentences,
              decoration: InputDecoration(
                labelText: 'Item ${index + 1}',
                hintText: 'e.g. Interior painting — walls',
              ),
              onChanged: (_) => setState(() {}),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: line.qty,
                    keyboardType: const TextInputType.numberWithOptions(
                        decimal: true),
                    decoration: const InputDecoration(labelText: 'Qty'),
                    onChanged: (_) => setState(() {}),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  flex: 2,
                  child: TextField(
                    controller: line.price,
                    keyboardType: const TextInputType.numberWithOptions(
                        decimal: true),
                    decoration: const InputDecoration(
                        labelText: 'Price each', prefixText: r'$ '),
                    onChanged: (_) => setState(() {}),
                  ),
                ),
              ],
            ),
            Row(
              children: [
                if (_gstRegistered)
                  Expanded(
                    child: SwitchListTile(
                      contentPadding: EdgeInsets.zero,
                      title: const Text('GST applies'),
                      value: line.gstApplicable,
                      onChanged: (v) =>
                          setState(() => line.gstApplicable = v),
                    ),
                  )
                else
                  const Spacer(),
                TextButton.icon(
                  onPressed: _lines.length == 1
                      ? null
                      : () => setState(() {
                            _lines.removeAt(index).dispose();
                          }),
                  icon: const Icon(Icons.delete_outline),
                  label: const Text('Remove'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  // --------------------------------------------------------- step 3: review

  Widget _reviewStep(DocumentRow doc) {
    final totals = _totals;
    final isQuote = widget.docType == DocType.quote;
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        SectionCard(
          title: '${widget.docType.label} ${doc.docNumber}',
          child: Column(
            children: [
              InfoRow('Customer', doc.customerNameCache),
              if (_siteAddress.text.trim().isNotEmpty)
                InfoRow('Job address', _siteAddress.text.trim()),
              if (_scope.text.trim().isNotEmpty)
                InfoRow('Work', _scope.text.trim()),
              InfoRow('Date', formatAuDate(doc.issueDate)),
              if (isQuote && doc.expiryDate != null)
                InfoRow('Valid until', formatAuDate(doc.expiryDate!)),
              if (!isQuote && doc.dueDate != null)
                InfoRow('Due date', formatAuDate(doc.dueDate!)),
            ],
          ),
        ),
        const SizedBox(height: 14),
        SectionCard(
          child: Column(
            children: [
              if (totals.gstCents > 0) ...[
                _totalRow(
                    'Before GST', Money.format(totals.subtotalExGstCents)),
                _totalRow('GST', Money.format(totals.gstCents)),
                const Divider(),
              ],
              _totalRow('Total', Money.format(totals.totalCents), big: true),
            ],
          ),
        ),
        const SizedBox(height: 20),
        BigButton(
          label: 'SEND ${widget.docType.label.toUpperCase()}',
          icon: Icons.send_outlined,
          onPressed: _send,
        ),
        const SizedBox(height: 12),
        BigOutlinedButton(
          label: 'Preview PDF',
          icon: Icons.picture_as_pdf_outlined,
          onPressed: _preview,
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: BigOutlinedButton(label: 'Back', onPressed: _back),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: BigOutlinedButton(
                  label: 'Save for later', onPressed: _saveForLater),
            ),
          ],
        ),
        const SizedBox(height: 32),
      ],
    );
  }

  Widget _totalRow(String label, String value, {bool big = false}) {
    final style = TextStyle(
      fontSize: big ? 24 : 18,
      fontWeight: big ? FontWeight.w800 : FontWeight.w500,
    );
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [Text(label, style: style), Text(value, style: style)],
      ),
    );
  }
}
