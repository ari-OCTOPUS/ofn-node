import 'package:drift/drift.dart' show Value;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/abn.dart';
import '../../data/db/database.dart';
import '../../providers.dart';
import '../../shared/widgets.dart';

/// Quick-add first (name is enough), everything else under "More details".
/// Pops with the saved CustomerRow so picker flows can chain.
class CustomerEditScreen extends ConsumerStatefulWidget {
  const CustomerEditScreen({super.key, this.customerId});

  final String? customerId;

  @override
  ConsumerState<CustomerEditScreen> createState() =>
      _CustomerEditScreenState();
}

class _CustomerEditScreenState extends ConsumerState<CustomerEditScreen> {
  final _formKey = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _mobile = TextEditingController();
  final _email = TextEditingController();
  final _siteAddress = TextEditingController();
  final _contactName = TextEditingController();
  final _abn = TextEditingController();
  final _billingAddress = TextEditingController();
  final _notes = TextEditingController();
  bool _isBusiness = false;
  String? _preferredContact;
  bool _loading = false;
  bool _saving = false;
  CustomerRow? _existing;

  @override
  void initState() {
    super.initState();
    if (widget.customerId != null) {
      _loading = true;
      Future.microtask(_load);
    }
  }

  Future<void> _load() async {
    final row = await ref
        .read(customerRepositoryProvider)
        .byId(widget.customerId!);
    if (!mounted) return;
    setState(() {
      _existing = row;
      _loading = false;
      if (row != null) {
        _name.text = row.name;
        _mobile.text = row.mobile ?? '';
        _email.text = row.email ?? '';
        _siteAddress.text = row.siteAddress ?? '';
        _contactName.text = row.contactName ?? '';
        _abn.text = row.abn == null ? '' : Abn.format(row.abn!);
        _billingAddress.text = row.billingAddress ?? '';
        _notes.text = row.notes ?? '';
        _isBusiness = row.isBusiness;
        _preferredContact = row.preferredContact;
      }
    });
  }

  @override
  void dispose() {
    for (final c in [
      _name, _mobile, _email, _siteAddress, _contactName, _abn,
      _billingAddress, _notes,
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  String? _nullable(TextEditingController c) {
    final t = c.text.trim();
    return t.isEmpty ? null : t;
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);
    final repo = ref.read(customerRepositoryProvider);
    try {
      final abnRaw = _abn.text.trim();
      final values = CustomersCompanion(
        isBusiness: Value(_isBusiness),
        name: Value(_name.text.trim()),
        contactName: Value(_nullable(_contactName)),
        email: Value(_nullable(_email)),
        mobile: Value(_nullable(_mobile)),
        abn: Value(abnRaw.isEmpty ? null : Abn.normalize(abnRaw)),
        billingAddress: Value(_nullable(_billingAddress)),
        siteAddress: Value(_nullable(_siteAddress)),
        notes: Value(_nullable(_notes)),
        preferredContact: Value(_preferredContact),
      );
      CustomerRow saved;
      if (_existing == null) {
        saved = await repo.createFull(values);
      } else {
        await repo.saveEdits(_existing!.id, values);
        saved = (await repo.byId(_existing!.id))!;
      }
      if (mounted) {
        showSuccessSnack(context, 'Saved. ${saved.name} is ready to use.');
        context.pop(saved);
      }
    } catch (e) {
      if (mounted) showErrorSnack(context, e);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Customer')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }
    return Scaffold(
      appBar: AppBar(
        title: Text(_existing == null ? 'New customer' : 'Edit customer'),
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            TextFormField(
              controller: _name,
              autofocus: _existing == null,
              textCapitalization: TextCapitalization.words,
              decoration: const InputDecoration(
                labelText: 'Customer or business name *',
              ),
              validator: (v) => (v == null || v.trim().isEmpty)
                  ? 'Please enter a name'
                  : null,
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _mobile,
              keyboardType: TextInputType.phone,
              decoration: const InputDecoration(
                labelText: 'Mobile',
                helperText: 'Optional',
              ),
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _email,
              keyboardType: TextInputType.emailAddress,
              decoration: const InputDecoration(
                labelText: 'Email',
                helperText: 'Optional — used for "Prepare in Gmail"',
              ),
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _siteAddress,
              textCapitalization: TextCapitalization.words,
              maxLines: 2,
              minLines: 1,
              decoration: const InputDecoration(
                labelText: 'Job address',
                helperText: 'Optional — where the painting work happens',
              ),
            ),
            const SizedBox(height: 8),
            ExpansionTile(
              title: const Text('More details'),
              tilePadding: EdgeInsets.zero,
              children: [
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('This is a business customer'),
                  value: _isBusiness,
                  onChanged: (v) => setState(() => _isBusiness = v),
                ),
                TextFormField(
                  controller: _contactName,
                  textCapitalization: TextCapitalization.words,
                  decoration:
                      const InputDecoration(labelText: 'Contact person'),
                ),
                const SizedBox(height: 14),
                TextFormField(
                  controller: _abn,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Customer ABN',
                    helperText:
                        'Optional — useful on invoices of \$1,000 or more',
                  ),
                  validator: (v) {
                    final t = (v ?? '').trim();
                    if (t.isEmpty) return null;
                    return Abn.isValid(t)
                        ? null
                        : 'This ABN does not appear to be valid. Check the '
                            '11 digits, or leave it blank.';
                  },
                ),
                const SizedBox(height: 14),
                TextFormField(
                  controller: _billingAddress,
                  textCapitalization: TextCapitalization.words,
                  maxLines: 2,
                  minLines: 1,
                  decoration: const InputDecoration(
                      labelText: 'Billing address (if different)'),
                ),
                const SizedBox(height: 14),
                DropdownButtonFormField<String?>(
                  initialValue: _preferredContact,
                  decoration: const InputDecoration(
                      labelText: 'Prefers to be contacted by'),
                  items: const [
                    DropdownMenuItem(value: null, child: Text('No preference')),
                    DropdownMenuItem(
                        value: 'telegram', child: Text('Telegram')),
                    DropdownMenuItem(value: 'email', child: Text('Email')),
                    DropdownMenuItem(
                        value: 'phone', child: Text('Phone / SMS')),
                    DropdownMenuItem(value: 'other', child: Text('Other')),
                  ],
                  onChanged: (v) => setState(() => _preferredContact = v),
                ),
                const SizedBox(height: 14),
                TextFormField(
                  controller: _notes,
                  maxLines: 3,
                  minLines: 2,
                  decoration: const InputDecoration(labelText: 'Notes'),
                ),
                const SizedBox(height: 8),
              ],
            ),
            const SizedBox(height: 20),
            BigButton(
              label: _saving ? 'Saving…' : 'Save customer',
              onPressed: _saving ? null : _save,
            ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }
}
