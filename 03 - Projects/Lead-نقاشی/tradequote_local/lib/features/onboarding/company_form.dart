import 'package:drift/drift.dart' show Value;
import 'package:flutter/material.dart';

import '../../core/abn.dart';
import '../../data/db/database.dart';
import '../../domain/enums.dart';
import '../../shared/widgets.dart';

/// Shared company form used by onboarding and Settings → Business details.
/// Progressive disclosure: essentials first, everything else under
/// "More options".
class CompanyForm extends StatefulWidget {
  const CompanyForm({
    super.key,
    this.initial,
    required this.submitLabel,
    required this.onSubmit,
    this.showNumbering = false,
  });

  final CompanySettingsRow? initial;
  final String submitLabel;
  final Future<void> Function(CompanySettingsCompanion values) onSubmit;
  final bool showNumbering;

  @override
  State<CompanyForm> createState() => _CompanyFormState();
}

class _CompanyFormState extends State<CompanyForm> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _legalName;
  late final TextEditingController _tradingName;
  late final TextEditingController _abn;
  late final TextEditingController _address;
  late final TextEditingController _phone;
  late final TextEditingController _email;
  late final TextEditingController _bankAccountName;
  late final TextEditingController _bsb;
  late final TextEditingController _accountNumber;
  late final TextEditingController _paymentInstructions;
  late final TextEditingController _paymentTermsDays;
  late final TextEditingController _quoteValidityDays;
  late final TextEditingController _quotePrefix;
  late final TextEditingController _invoicePrefix;
  late final TextEditingController _defaultTerms;
  late final TextEditingController _footer;
  late bool _gstRegistered;
  late GstMode _gstMode;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    final i = widget.initial;
    _legalName = TextEditingController(text: i?.legalName ?? '');
    _tradingName = TextEditingController(text: i?.tradingName ?? '');
    _abn = TextEditingController(
        text: i?.abn == null ? '' : Abn.format(i!.abn!));
    _address = TextEditingController(text: i?.address ?? '');
    _phone = TextEditingController(text: i?.phone ?? '');
    _email = TextEditingController(text: i?.email ?? '');
    _bankAccountName = TextEditingController(text: i?.bankAccountName ?? '');
    _bsb = TextEditingController(text: i?.bsb ?? '');
    _accountNumber = TextEditingController(text: i?.accountNumber ?? '');
    _paymentInstructions =
        TextEditingController(text: i?.paymentInstructions ?? '');
    _paymentTermsDays = TextEditingController(
        text: '${i?.defaultPaymentTermsDays ?? 14}');
    _quoteValidityDays = TextEditingController(
        text: '${i?.defaultQuoteValidityDays ?? 30}');
    _quotePrefix = TextEditingController(text: i?.quotePrefix ?? 'Q-');
    _invoicePrefix = TextEditingController(text: i?.invoicePrefix ?? 'INV-');
    _defaultTerms = TextEditingController(text: i?.defaultTerms ?? '');
    _footer = TextEditingController(text: i?.documentFooter ?? '');
    _gstRegistered = i?.gstRegistered ?? false;
    final mode = GstMode.fromName(i?.gstMode ?? 'inclusive');
    _gstMode = mode == GstMode.none ? GstMode.inclusive : mode;
  }

  @override
  void dispose() {
    for (final c in [
      _legalName, _tradingName, _abn, _address, _phone, _email,
      _bankAccountName, _bsb, _accountNumber, _paymentInstructions,
      _paymentTermsDays, _quoteValidityDays, _quotePrefix, _invoicePrefix,
      _defaultTerms, _footer,
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  String? _nullable(TextEditingController c) {
    final t = c.text.trim();
    return t.isEmpty ? null : t;
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);
    try {
      final abnRaw = _abn.text.trim();
      await widget.onSubmit(CompanySettingsCompanion(
        legalName: Value(_legalName.text.trim()),
        tradingName: Value(_nullable(_tradingName)),
        abn: Value(abnRaw.isEmpty ? null : Abn.normalize(abnRaw)),
        gstRegistered: Value(_gstRegistered),
        gstMode: Value(_gstRegistered ? _gstMode.name : GstMode.none.name),
        address: Value(_nullable(_address)),
        phone: Value(_nullable(_phone)),
        email: Value(_nullable(_email)),
        bankAccountName: Value(_nullable(_bankAccountName)),
        bsb: Value(_nullable(_bsb)),
        accountNumber: Value(_nullable(_accountNumber)),
        paymentInstructions: Value(_nullable(_paymentInstructions)),
        defaultPaymentTermsDays:
            Value(int.tryParse(_paymentTermsDays.text.trim()) ?? 14),
        defaultQuoteValidityDays:
            Value(int.tryParse(_quoteValidityDays.text.trim()) ?? 30),
        quotePrefix: Value(_quotePrefix.text.trim().isEmpty
            ? 'Q-'
            : _quotePrefix.text.trim()),
        invoicePrefix: Value(_invoicePrefix.text.trim().isEmpty
            ? 'INV-'
            : _invoicePrefix.text.trim()),
        defaultTerms: Value(_nullable(_defaultTerms)),
        documentFooter: Value(_nullable(_footer)),
      ));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          SectionCard(
            title: 'Your business',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextFormField(
                  controller: _legalName,
                  textCapitalization: TextCapitalization.words,
                  decoration: const InputDecoration(
                    labelText: 'Business name *',
                    helperText: 'For example: Your Painting Company Pty Ltd',
                  ),
                  validator: (v) => (v == null || v.trim().isEmpty)
                      ? 'Please enter your business name'
                      : null,
                ),
                const SizedBox(height: 14),
                TextFormField(
                  controller: _abn,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'ABN',
                    helperText:
                        'Your 11-digit ABN. You can leave it blank for now.',
                  ),
                  validator: (v) {
                    final t = (v ?? '').trim();
                    if (t.isEmpty) return null;
                    return Abn.isValid(t)
                        ? null
                        : 'This ABN does not appear to be valid. Check the '
                            '11 digits, or leave it blank for now.';
                  },
                ),
                const SizedBox(height: 14),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Registered for GST'),
                  subtitle: const Text(
                      'Turn this on if you charge GST on your invoices'),
                  value: _gstRegistered,
                  onChanged: (v) => setState(() => _gstRegistered = v),
                ),
                if (_gstRegistered) ...[
                  const SizedBox(height: 6),
                  Text('When you type a price, that price…',
                      style: Theme.of(context).textTheme.bodyMedium),
                  const SizedBox(height: 8),
                  SegmentedButton<GstMode>(
                    segments: const [
                      ButtonSegment(
                          value: GstMode.inclusive,
                          label: Text('Includes GST')),
                      ButtonSegment(
                          value: GstMode.exclusive,
                          label: Text('GST added on top')),
                    ],
                    selected: {_gstMode},
                    onSelectionChanged: (s) =>
                        setState(() => _gstMode = s.first),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 16),
          SectionCard(
            title: 'Contact details (shown on your documents)',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextFormField(
                  controller: _address,
                  textCapitalization: TextCapitalization.words,
                  maxLines: 2,
                  minLines: 1,
                  decoration: const InputDecoration(labelText: 'Address'),
                ),
                const SizedBox(height: 14),
                TextFormField(
                  controller: _phone,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(labelText: 'Phone'),
                ),
                const SizedBox(height: 14),
                TextFormField(
                  controller: _email,
                  keyboardType: TextInputType.emailAddress,
                  decoration: const InputDecoration(labelText: 'Email'),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          SectionCard(
            title: 'Getting paid (shown on invoices)',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextFormField(
                  controller: _bankAccountName,
                  textCapitalization: TextCapitalization.words,
                  decoration:
                      const InputDecoration(labelText: 'Account name'),
                ),
                const SizedBox(height: 14),
                Row(
                  children: [
                    Expanded(
                      child: TextFormField(
                        controller: _bsb,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(labelText: 'BSB'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      flex: 2,
                      child: TextFormField(
                        controller: _accountNumber,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(
                            labelText: 'Account number'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                TextFormField(
                  controller: _paymentInstructions,
                  maxLines: 2,
                  minLines: 1,
                  decoration: const InputDecoration(
                    labelText: 'Payment instructions',
                    helperText: 'Optional, e.g. "Payment within 7 days"',
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          ExpansionTile(
            title: const Text('More options'),
            tilePadding: EdgeInsets.zero,
            childrenPadding: const EdgeInsets.only(bottom: 8),
            children: [
              TextFormField(
                controller: _tradingName,
                textCapitalization: TextCapitalization.words,
                decoration: const InputDecoration(
                  labelText: 'Trading name',
                  helperText: 'Only if different from your business name',
                ),
              ),
              const SizedBox(height: 14),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: _paymentTermsDays,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                          labelText: 'Invoices due in (days)'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextFormField(
                      controller: _quoteValidityDays,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                          labelText: 'Quotes valid for (days)'),
                    ),
                  ),
                ],
              ),
              if (widget.showNumbering) ...[
                const SizedBox(height: 14),
                Row(
                  children: [
                    Expanded(
                      child: TextFormField(
                        controller: _quotePrefix,
                        decoration: const InputDecoration(
                            labelText: 'Quote number prefix'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: TextFormField(
                        controller: _invoicePrefix,
                        decoration: const InputDecoration(
                            labelText: 'Invoice number prefix'),
                      ),
                    ),
                  ],
                ),
              ],
              const SizedBox(height: 14),
              TextFormField(
                controller: _defaultTerms,
                maxLines: 4,
                minLines: 2,
                decoration: const InputDecoration(
                  labelText: 'Standard terms for new documents',
                  helperText: 'Shown at the bottom of quotes and invoices',
                ),
              ),
              const SizedBox(height: 14),
              TextFormField(
                controller: _footer,
                decoration: const InputDecoration(
                  labelText: 'Document footer',
                  helperText: 'Optional, e.g. licence or insurance details',
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          BigButton(
            label: _saving ? 'Saving…' : widget.submitLabel,
            onPressed: _saving ? null : _submit,
          ),
          const SizedBox(height: 40),
        ],
      ),
    );
  }
}
