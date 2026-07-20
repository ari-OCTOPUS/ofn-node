import 'package:go_router/go_router.dart';

import '../domain/enums.dart';
import '../features/customers/customer_detail_screen.dart';
import '../features/customers/customer_edit_screen.dart';
import '../features/customers/customers_screen.dart';
import '../features/documents/document_detail_screen.dart';
import '../features/documents/documents_screen.dart';
import '../features/documents/pdf_preview_screen.dart';
import '../features/home/home_screen.dart';
import '../features/onboarding/onboarding_screen.dart';
import '../features/quote_flow/quick_flow_screen.dart';
import '../features/settings/ai_settings_screen.dart';
import '../features/settings/business_settings_screen.dart';
import '../features/settings/data_settings_screen.dart';
import '../features/settings/display_settings_screen.dart';
import '../features/settings/messages_settings_screen.dart';
import '../features/settings/settings_screen.dart';
import '../features/share/share_screen.dart';

GoRouter buildRouter({required bool onboarded}) {
  return GoRouter(
    initialLocation: onboarded ? '/' : '/onboarding',
    routes: [
      GoRoute(
        path: '/onboarding',
        builder: (context, state) => const OnboardingScreen(),
      ),
      GoRoute(
        path: '/',
        builder: (context, state) => const HomeScreen(),
      ),
      GoRoute(
        path: '/customers',
        builder: (context, state) => CustomersScreen(
          pickerMode: state.uri.queryParameters['pick'] == '1',
        ),
      ),
      GoRoute(
        path: '/customers/new',
        builder: (context, state) => const CustomerEditScreen(),
      ),
      GoRoute(
        path: '/customers/:id/edit',
        builder: (context, state) =>
            CustomerEditScreen(customerId: state.pathParameters['id']),
      ),
      GoRoute(
        path: '/customers/:id',
        builder: (context, state) =>
            CustomerDetailScreen(customerId: state.pathParameters['id']!),
      ),
      GoRoute(
        path: '/flow/:type',
        builder: (context, state) => QuickFlowScreen(
          docType: state.pathParameters['type'] == 'invoice'
              ? DocType.invoice
              : DocType.quote,
          existingDocumentId: state.uri.queryParameters['doc'],
        ),
      ),
      GoRoute(
        path: '/documents',
        builder: (context, state) => DocumentsScreen(
          initialFilter: state.uri.queryParameters['filter'],
        ),
      ),
      GoRoute(
        path: '/documents/:id/share',
        builder: (context, state) => ShareScreen(
          documentId: state.pathParameters['id']!,
          kind: state.uri.queryParameters['kind'],
        ),
      ),
      GoRoute(
        path: '/documents/:id/preview',
        builder: (context, state) =>
            PdfPreviewScreen(documentId: state.pathParameters['id']!),
      ),
      GoRoute(
        path: '/documents/:id',
        builder: (context, state) =>
            DocumentDetailScreen(documentId: state.pathParameters['id']!),
      ),
      GoRoute(
        path: '/settings',
        builder: (context, state) => const SettingsScreen(),
      ),
      GoRoute(
        path: '/settings/business',
        builder: (context, state) => const BusinessSettingsScreen(),
      ),
      GoRoute(
        path: '/settings/messages',
        builder: (context, state) => const MessagesSettingsScreen(),
      ),
      GoRoute(
        path: '/settings/data',
        builder: (context, state) => const DataSettingsScreen(),
      ),
      GoRoute(
        path: '/settings/display',
        builder: (context, state) => const DisplaySettingsScreen(),
      ),
      GoRoute(
        path: '/settings/ai',
        builder: (context, state) => const AiSettingsScreen(),
      ),
    ],
  );
}
