import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../data/db/database.dart';
import '../../providers.dart';
import '../../shared/widgets.dart';

/// Customer list. In [pickerMode] (started from NEW QUOTE / NEW INVOICE)
/// tapping a customer returns it to the caller; recent customers appear as
/// large cards so the common case is one tap.
class CustomersScreen extends ConsumerStatefulWidget {
  const CustomersScreen({super.key, this.pickerMode = false});

  final bool pickerMode;

  @override
  ConsumerState<CustomersScreen> createState() => _CustomersScreenState();
}

class _CustomersScreenState extends ConsumerState<CustomersScreen> {
  final _search = TextEditingController();
  String _query = '';

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  Future<void> _addNew() async {
    final created =
        await context.push<CustomerRow>('/customers/new');
    if (!mounted || created == null) return;
    if (widget.pickerMode) {
      context.pop(created);
    }
  }

  void _select(CustomerRow customer) {
    if (widget.pickerMode) {
      context.pop(customer);
    } else {
      context.push('/customers/${customer.id}');
    }
  }

  @override
  Widget build(BuildContext context) {
    final repo = ref.watch(customerRepositoryProvider);
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.pickerMode ? 'Choose customer' : 'Customers'),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 8, 20, 4),
            child: TextField(
              controller: _search,
              onChanged: (v) => setState(() => _query = v),
              decoration: InputDecoration(
                hintText: 'Search name, phone or address',
                prefixIcon: const Icon(Icons.search, size: 26),
                suffixIcon: _query.isEmpty
                    ? null
                    : IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          _search.clear();
                          setState(() => _query = '');
                        },
                      ),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 8, 20, 8),
            child: BigButton(
              label: 'Add new customer',
              icon: Icons.person_add_alt,
              onPressed: _addNew,
            ),
          ),
          Expanded(
            child: StreamBuilder<List<CustomerRow>>(
              stream: repo.watchAll(query: _query),
              builder: (context, snapshot) {
                final customers = snapshot.data ?? const <CustomerRow>[];
                if (snapshot.connectionState == ConnectionState.waiting &&
                    customers.isEmpty) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (customers.isEmpty) {
                  return EmptyState(
                    icon: Icons.people_outline,
                    message: _query.isEmpty
                        ? 'No customers yet.\nAdd your first customer to '
                            'start a quote.'
                        : 'No customers match "$_query".',
                  );
                }
                return ListView.separated(
                  padding: const EdgeInsets.fromLTRB(20, 4, 20, 24),
                  itemCount: customers.length,
                  separatorBuilder: (_, __) => const Divider(height: 1),
                  itemBuilder: (context, i) {
                    final c = customers[i];
                    final detail = [
                      if ((c.mobile ?? '').isNotEmpty) c.mobile!,
                      if ((c.siteAddress ?? '').isNotEmpty) c.siteAddress!,
                    ].join('  ·  ');
                    return ListTile(
                      contentPadding:
                          const EdgeInsets.symmetric(vertical: 6),
                      leading: CircleAvatar(
                        radius: 24,
                        child: Text(
                          c.name.isEmpty
                              ? '?'
                              : c.name.substring(0, 1).toUpperCase(),
                          style: const TextStyle(fontSize: 20),
                        ),
                      ),
                      title: Text(c.name),
                      subtitle: detail.isEmpty ? null : Text(detail),
                      trailing:
                          const Icon(Icons.chevron_right, size: 30),
                      onTap: () => _select(c),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
