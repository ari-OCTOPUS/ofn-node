# PROJECT_STATE

Updated: 2026-07-20 · end of cloud build session #1 (Claude, claude-fable-5)

## HANDOFF — read this first, next agent

You are resuming a **complete, uncompiled MVP**. Your job is the compile →
fix → test → APK loop that the authoring workspace could not run
(pub.dev / storage.googleapis.com / dl.google.com are firewalled there;
verified, not assumed).

Do, in order (details in docs/BUILD_AND_RELEASE.md §1):

1. `flutter create . --org au.com.placeholder --project-name tradequote_local --platforms android`
2. `flutter pub get`  (if flutter_email_sender ^9 fails to resolve → ^8)
3. `dart run build_runner build --delete-conflicting-outputs`
4. `flutter analyze` → fix what it flags. Expected first-compile risk
   spots are pre-listed in docs/DEPENDENCIES.md §Known API-freshness
   risks (dropdown initialValue, theme *ThemeData types, ShareParams,
   Email(), drift unique()/KeyAction). Everything else static-checked
   clean (tool/check_sources.py — PASS, output committed).
5. `flutter test` → all suites must go green. Money/GST/ABN expectations
   are LOCKED by executed evidence (tool/validate_financial_logic.py,
   36/36) — if a money test fails, fix the code, never the expectation.
6. `flutter run` on the S23 FE → walk docs/testing/MANUAL_ACCEPTANCE_CHECKLIST.md.
7. `flutter build apk --release` → sha256 → deliver. Record real outputs
   in docs/testing/TEST_RESULTS.md (create it; no fabricated results).
8. Commit pubspec.lock + android/ config edits; update this file.

Rules that bind you: DECISIONS.md (D-001…D-014), invariants in
docs/architecture/ARCHITECTURE.md, honesty rules (§20 of the brief).

## Scope decided with owner (2026-07-19)

MVP senior-first core: onboarding/settings, customers, quick quote/invoice,
GST engine, PDFs, Telegram/Gmail sharing, conversion, payments, dashboard,
backup/restore, optional AI message-improvement (owner has a real AI API,
"Fugu"; configured at runtime, off by default). Phase 2 (not built,
designed): photos, signatures, reports/CSV, projects, Gmail API drafts,
encryption — see REQUIREMENTS_TRACEABILITY R31–R37.

## What is DONE in this session

- Research w/ cited primary sources + package audit (docs/research/)
- Financial algorithms executed & validated in Python (36/36; output in
  docs/testing/python_validation_output.txt)
- Architecture docs, ERD, lifecycle, backup format, data dictionary, ADR,
  14 decisions
- Full implementation: 48 Dart files (~8.3k lines) — core engine, drift
  schema v1 + repositories (numbering/snapshots/conversion/payments/audit),
  senior-friendly UI (16 screens), PDF builder, share service, backup
  service with atomic swap, AI adapter
- Tests written: gst/abn/money/render_data/repository + widget form suite
- Static consistency check over all sources: PASS (output committed)
- Docs set complete; traceability matrix complete (R1–R38)
- Git milestone commits in-repo

## Build status

Cloud workspace: compile impossible (network policy) — documented above.
Owner machine: NOT yet attempted. APK: not yet produced (R30).

## Test status

- Executed here: Python financial validation 36/36 PASS; source static
  check PASS.
- Dart/widget/db tests: written, NOT yet executed (need Flutter).

## Known issues / risks (open, honest)

1. First-compile fix pass expected (docs/DEPENDENCIES.md risk list).
2. repository_test needs loadable sqlite3 on Windows (TEST_PLAN §Env).
3. flutter_email_sender 9.0.0 was hours old at research time.
4. PDF visual polish (long descriptions, page breaks) needs device pass.
5. DatabaseHolder swap after restore needs a real-device round-trip test.
6. `.g.dart` intentionally absent until build_runner runs.

## Blockers

None for the next agent on a normal PC with Flutter. Nothing awaits the
owner except running the build guide (and, later, entering real business
details in-app — never in Git).
