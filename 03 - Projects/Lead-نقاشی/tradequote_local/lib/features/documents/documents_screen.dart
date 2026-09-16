import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/db/database.dart';
import '../../domain/enums.dart';
import '../../providers.dart';
import '../../shared/widgets.dart';
import '../home/home_screen.dart' show DocumentTile;

/// All documents with plain-language filters and search.
class DocumentsScreen extends ConsumerStatefulWidget {
  const DocumentsScreen({super.key, this.initialFilter});

  final String? initialFilter;

  @override
  ConsumerState<DocumentsScreen> createState() => _DocumentsScreenState();
}

class _DocumentsScreenState extends ConsumerState<DocumentsScreen> {
  final _search = TextEditingController();
  String _query = '';
  late String _filter;

  static const _filters = <String, String>{
    'all': 'All',
    'quotes': 'Quotes',
    'invoices': 'Invoices',
    'unpaid': 'Unpaid',
    'drafts': 'Drafts',
  };

  @override
  void initState() {
    super.initState();
    _filter = _filters.containsKey(widget.initialFilter)
        ? widget.initialFilter!
        : 'all';
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  Stream<List<DocumentRow>> _stream() {
    final repo = ref.read(documentRepositoryProvider);
    switch (_filter) {
      case 'quotes':
        return repo.watchAll(type: DocType.quote, query: _query);
      case 'invoices':
        return repo.watchAll(type: DocType.invoice, query: _query);
      case 'unpaid':
        return repo.watchAll(
          type: DocType.invoice,
          statuses: const [DocStatus.issued, DocStatus.partiallyPaid],
          query: _query,
        );
      case 'drafts':
        return repo.watchAll(
            statuses: const [DocStatus.draft], query: _query);
      default:
        return repo.watchAll(query: _query);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Documents')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 8, 20, 0),
            child: TextField(
              controller: _search,
              onChanged: (v) => setState(() => _query = v),
              decoration: InputDecoration(
                hintText: 'Search number, customer or address',
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
          SizedBox(
            height: 60,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding:
                  const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
              children: [
                for (final entry in _filters.entries)
                  Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ChoiceChip(
                      label: Text(entry.value),
                      selected: _filter == entry.key,
                      onSelected: (_) =>
                          setState(() => _filter = entry.key),
                    ),
                  ),
              ],
            ),
          ),
          Expanded(
            child: StreamBuilder<List<DocumentRow>>(
              stream: _stream(),
              builder: (context, snapshot) {
                final docs = snapshot.data ?? const <DocumentRow>[];
                if (snapshot.connectionState == ConnectionState.waiting &&
                    docs.isEmpty) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (docs.isEmpty) {
                  return const EmptyState(
                    icon: Icons.folder_open_outlined,
                    message: 'Nothing here yet.\nCreate a quote from the '
                        'Home screen to get started.',
                  );
                }
                return ListView.separated(
                  padding: const EdgeInsets.fromLTRB(20, 4, 20, 24),
                  itemCount: docs.length,
                  separatorBuilder: (_, __) => const Divider(height: 1),
                  itemBuilder: (context, i) => DocumentTile(doc: docs[i]),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
