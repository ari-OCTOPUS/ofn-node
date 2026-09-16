# Test plan & current status

## Layers

1. **Executed in the authoring workspace (evidence committed)**
   - `tool/validate_financial_logic.py` — 36/36 PASS
     (`python_validation_output.txt`): ABN checksum incl. ABR worked
     example, half-up rounding primitive, line totals, GST
     exclusive/inclusive, mixed taxable, document scenarios, balances.
   - `tool/check_sources.py` — PASS (`static_check_output.txt`): all 48
     Dart files' imports resolve, delimiters balanced, router screens and
     providers consistent.

2. **Dart unit tests (written; run on the build machine — see
   BUILD_AND_RELEASE §1)**
   - `test/gst_test.dart` — mirrors every Python case + empties/mixed.
   - `test/abn_test.dart`, `test/money_test.dart` — parsing, formatting,
     normalization.
   - `test/render_data_test.dart` — snapshot JSON round-trip, ATO title
     rules, totals consistency, tolerant decoding.

3. **Database/business tests** — `test/repository_test.dart` on
   `NativeDatabase.memory()`: seeding, sequential prefixed numbering,
   number gaps never reused, draft totals + GST-mode recompute,
   snapshot immutability after master-data edits, issued-edit refusal,
   conversion (once-only, quote preserved, lines copied), payments
   (partial→paid, overpayment blocked, reversal rollback, quote/draft
   rejection), void rules, archiving.

4. **Widget tests** — `test/widget/company_form_test.dart`: required-name
   validation, senior-style ABN error, normalized submission values.

5. **Device/manual** — `MANUAL_ACCEPTANCE_CHECKLIST.md` on the S23 FE
   (share sheet, Gmail compose, backup via My Files, restore, large
   font). Sharing intents CANNOT be meaningfully tested off-device.

## Environment note (Windows)

`repository_test.dart` needs a loadable sqlite3 library. On Windows,
if the sqlite3 dynamic library isn't found: easiest is running tests once
in WSL/macOS/Linux, or download sqlite3.dll (sqlite.org) next to the test
runner per drift's "Testing" docs. All non-DB tests run anywhere.

## Quality gates before calling it released

dart format --set-exit-if-changed · flutter analyze (0 errors) ·
flutter test (all green) · debug + release APK build · full manual
checklist on the physical S23 FE. Record results in TEST_RESULTS.md
(create it from the first real run — no fabricated results, per the
honesty rules).

## Known untested-by-machine areas (do these on device)

PDF visual layout on long descriptions/multi-page · share-sheet return
state restoration · Gmail compose prefill on current Gmail version ·
backup/restore round-trip with the DatabaseHolder swap · text scaling
200% · process-death draft recovery.
