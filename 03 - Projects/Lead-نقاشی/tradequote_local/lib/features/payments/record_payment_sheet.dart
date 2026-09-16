import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/dates.dart';
import '../../core/errors.dart';
import '../../core/money.dart';
import '../../data/db/database.dart';
import '../../domain/enums.dart';
import '../../providers.dart';
import '../../shared/widgets.dart';

/// Bottom sheet for recording a payment. Amount is prefilled with the
/// balance so "they paid it all" is one tap; partial payments just change
/// the number. Overpayment is blocked with a plain message (D-007).
Future<void> showRecordPaymentSheet(BuildContext context, WidgetRef ref,
    DocumentRow invoice, int balanceCents) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (sheetContext) => Padding(
      padding: EdgeInsets.only(
          bottom: MediaQuery.of(sheetContext).viewInsets.bottom),
      child: _RecordPaymentForm(invoice: invoice, balanceCents: balanceCents),
    ),
  );
}

class _RecordPaymentForm extends ConsumerStatefulWidget {
  const _RecordPaymentForm(
      {required this.invoice, required this.balanceCents});

  final DocumentRow invoice;
  final int balanceCents;

  @override
  ConsumerState<_RecordPaymentForm> createState() =>
      _RecordPaymentFormState();
}

class _RecordPaymentFormState extends ConsumerState<_RecordPaymentForm> {
  late final TextEditingController _amount;
  final _reference = TextEditingController();
  DateTime _paidOn = DateTime.now();
  PaymentMethod _method = PaymentMethod.bankTransfer;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    final b = widget.balanceCents;
    _amount = TextEditingController(
        text: b % 100 == 0 ? '${b ~/ 100}' : (b / 100).toStringAsFixed(2));
  }

  @override
  void dispose() {
    _amount.dispose();
    _reference.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final cents = Money.tryParse(_amount.text);
    if (cents == null || cents <= 0) {
      showErrorSnack(context,
          const AppException('Please enter the amount that was paid.'));
      return;
    }
    setState(() => _saving = true);
    try {
      await ref.read(paymentRepositoryProvider).record(
            invoiceId: widget.invoice.id,
            paidAtMs: _paidOn.millisecondsSinceEpoch,
            amountCents: cents,
            method: _method,
            reference: _reference.text,
          );
      if (mounted) {
        final remaining = widget.balanceCents - cents;
        // Capture the messenger before popping — the sheet's context is
        // disposed by the pop.
        final messenger = ScaffoldMessenger.of(context);
        Navigator.of(context).pop();
        messenger
          ..clearSnackBars()
          ..showSnackBar(SnackBar(
            content: Text(remaining <= 0
                ? 'Payment recorded. ${widget.invoice.docNumber} is now '
                    'PAID in full.'
                : 'Payment recorded. Still owing: '
                    '${Money.format(remaining)}.'),
            duration: const Duration(seconds: 4),
          ));
      }
    } on OverpaymentException catch (e) {
      if (mounted) {
        showErrorSnack(
            context,
            AppException('That is more than the amount still owing '
                '(${Money.format(e.balanceCents)}). Enter up to that '
                'amount — you can note any extra in the reference.'));
      }
    } catch (e) {
      if (mounted) showErrorSnack(context, e);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 4, 20, 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Record payment for ${widget.invoice.docNumber}',
                style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 6),
            Text('Still owing: ${Money.format(widget.balanceCents)}',
                style: Theme.of(context).textTheme.bodyLarge),
            const SizedBox(height: 16),
            TextField(
              controller: _amount,
              autofocus: true,
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: true),
              style: const TextStyle(
                  fontSize: 28, fontWeight: FontWeight.w700),
              decoration: const InputDecoration(
                labelText: 'Amount paid',
                prefixText: r'$ ',
                prefixStyle: TextStyle(
                    fontSize: 28, fontWeight: FontWeight.w700),
              ),
            ),
            const SizedBox(height: 14),
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.event, size: 28),
              title: const Text('Paid on'),
              subtitle:
                  Text(formatAuDate(_paidOn.millisecondsSinceEpoch)),
              trailing: const Icon(Icons.edit_calendar_outlined),
              onTap: () async {
                final picked = await showDatePicker(
                  context: context,
                  initialDate: _paidOn,
                  firstDate: DateTime(2020),
                  lastDate: DateTime.now().add(const Duration(days: 1)),
                );
                if (picked != null) setState(() => _paidOn = picked);
              },
            ),
            const SizedBox(height: 6),
            DropdownButtonFormField<PaymentMethod>(
              initialValue: _method,
              decoration: const InputDecoration(labelText: 'How they paid'),
              items: [
                for (final m in PaymentMethod.values)
                  DropdownMenuItem(value: m, child: Text(m.label)),
              ],
              onChanged: (v) =>
                  setState(() => _method = v ?? PaymentMethod.other),
            ),
            const SizedBox(height: 14),
            TextField(
              controller: _reference,
              decoration: const InputDecoration(
                labelText: 'Reference',
                helperText: 'Optional — e.g. bank receipt number',
              ),
            ),
            const SizedBox(height: 20),
            BigButton(
              label: _saving ? 'Saving…' : 'RECORD PAYMENT',
              onPressed: _saving ? null : _save,
            ),
          ],
        ),
      ),
    );
  }
}
