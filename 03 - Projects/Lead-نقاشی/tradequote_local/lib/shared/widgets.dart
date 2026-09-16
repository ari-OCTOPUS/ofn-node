import 'package:flutter/material.dart';

import '../core/errors.dart';
import '../core/money.dart';
import '../domain/enums.dart';

/// Reusable senior-friendly widgets: large targets, colour + text for
/// status, plain-language errors.

class BigButton extends StatelessWidget {
  const BigButton({
    super.key,
    required this.label,
    this.icon,
    this.onPressed,
    this.color,
  });

  final String label;
  final IconData? icon;
  final VoidCallback? onPressed;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final style = color == null
        ? null
        : FilledButton.styleFrom(backgroundColor: color);
    if (icon == null) {
      return FilledButton(
          onPressed: onPressed, style: style, child: Text(label));
    }
    return FilledButton.icon(
      onPressed: onPressed,
      style: style,
      icon: Icon(icon, size: 28),
      label: Text(label),
    );
  }
}

class BigOutlinedButton extends StatelessWidget {
  const BigOutlinedButton(
      {super.key, required this.label, this.icon, this.onPressed});

  final String label;
  final IconData? icon;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    if (icon == null) {
      return OutlinedButton(onPressed: onPressed, child: Text(label));
    }
    return OutlinedButton.icon(
        onPressed: onPressed, icon: Icon(icon, size: 26), label: Text(label));
  }
}

class SectionCard extends StatelessWidget {
  const SectionCard({super.key, this.title, required this.child});

  final String? title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (title != null) ...[
              Text(title!, style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 12),
            ],
            child,
          ],
        ),
      ),
    );
  }
}

class EmptyState extends StatelessWidget {
  const EmptyState({
    super.key,
    required this.icon,
    required this.message,
    this.actionLabel,
    this.onAction,
  });

  final IconData icon;
  final String message;
  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 64, color: theme.colorScheme.outline),
            const SizedBox(height: 16),
            Text(message,
                textAlign: TextAlign.center,
                style: theme.textTheme.bodyLarge
                    ?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
            if (actionLabel != null) ...[
              const SizedBox(height: 20),
              BigButton(label: actionLabel!, onPressed: onAction),
            ],
          ],
        ),
      ),
    );
  }
}

/// Colour + TEXT, never colour alone.
class StatusChip extends StatelessWidget {
  const StatusChip(this.status, {super.key, this.overdue = false});

  final DocStatus status;
  final bool overdue;

  @override
  Widget build(BuildContext context) {
    final (bg, fg, label) = _style();
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(label,
          style: TextStyle(
              color: fg, fontSize: 14.5, fontWeight: FontWeight.w700)),
    );
  }

  (Color, Color, String) _style() {
    if (overdue) {
      return (const Color(0xFFFDE8E8), const Color(0xFF991B1B), 'OVERDUE');
    }
    return switch (status) {
      DocStatus.draft => (
          const Color(0xFFE5E7EB),
          const Color(0xFF374151),
          'Draft'
        ),
      DocStatus.sent => (
          const Color(0xFFDBEAFE),
          const Color(0xFF1D4ED8),
          'Sent'
        ),
      DocStatus.accepted => (
          const Color(0xFFD1FAE5),
          const Color(0xFF065F46),
          'Accepted'
        ),
      DocStatus.declined => (
          const Color(0xFFFDE8E8),
          const Color(0xFF991B1B),
          'Declined'
        ),
      DocStatus.expired => (
          const Color(0xFFFEF3C7),
          const Color(0xFF92400E),
          'Expired'
        ),
      DocStatus.cancelled => (
          const Color(0xFFE5E7EB),
          const Color(0xFF374151),
          'Cancelled'
        ),
      DocStatus.issued => (
          const Color(0xFFDBEAFE),
          const Color(0xFF1D4ED8),
          'Unpaid'
        ),
      DocStatus.partiallyPaid => (
          const Color(0xFFFEF3C7),
          const Color(0xFF92400E),
          'Partly paid'
        ),
      DocStatus.paid => (
          const Color(0xFFD1FAE5),
          const Color(0xFF065F46),
          'Paid'
        ),
      DocStatus.voided => (
          const Color(0xFFFDE8E8),
          const Color(0xFF991B1B),
          'Voided'
        ),
    };
  }
}

class MoneyText extends StatelessWidget {
  const MoneyText(this.cents, {super.key, this.size = 20, this.bold = true});

  final int cents;
  final double size;
  final bool bold;

  @override
  Widget build(BuildContext context) {
    return Text(
      Money.format(cents),
      style: TextStyle(
        fontSize: size,
        fontWeight: bold ? FontWeight.w700 : FontWeight.w400,
        fontFeatures: const [FontFeature.tabularFigures()],
      ),
    );
  }
}

class InfoRow extends StatelessWidget {
  const InfoRow(this.label, this.value, {super.key});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 130,
            child: Text(label,
                style: theme.textTheme.bodyMedium
                    ?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
          ),
          Expanded(
            child: Text(value, style: theme.textTheme.bodyLarge),
          ),
        ],
      ),
    );
  }
}

/// Plain-language confirmation. Returns true only on explicit confirm.
Future<bool> showConfirmSheet(
  BuildContext context, {
  required String title,
  required String message,
  required String confirmLabel,
  bool destructive = false,
}) async {
  final result = await showModalBottomSheet<bool>(
    context: context,
    showDragHandle: true,
    builder: (context) => SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 4, 20, 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(title, style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 12),
            Text(message, style: Theme.of(context).textTheme.bodyLarge),
            const SizedBox(height: 24),
            BigButton(
              label: confirmLabel,
              color: destructive ? const Color(0xFFB91C1C) : null,
              onPressed: () => Navigator.of(context).pop(true),
            ),
            const SizedBox(height: 10),
            BigOutlinedButton(
              label: 'Go back',
              onPressed: () => Navigator.of(context).pop(false),
            ),
          ],
        ),
      ),
    ),
  );
  return result ?? false;
}

void showSuccessSnack(BuildContext context, String message) {
  ScaffoldMessenger.of(context)
    ..clearSnackBars()
    ..showSnackBar(SnackBar(
      content: Text(message),
      duration: const Duration(seconds: 4),
    ));
}

/// Errors follow the rule: what happened → your work is safe → what next.
void showErrorSnack(BuildContext context, Object error) {
  final message = error is AppException
      ? error.userMessage
      : 'Something went wrong. Your saved work is safe — please try again.';
  ScaffoldMessenger.of(context)
    ..clearSnackBars()
    ..showSnackBar(SnackBar(
      content: Text(message),
      duration: const Duration(seconds: 5),
    ));
}
