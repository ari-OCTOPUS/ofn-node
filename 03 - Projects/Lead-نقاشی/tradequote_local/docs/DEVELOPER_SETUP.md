# Developer setup

Short version: install Flutter stable + Android Studio, then follow
**docs/BUILD_AND_RELEASE.md §0–§1** — it is the authoritative,
step-by-step path (create platforms → pub get → build_runner →
analyze → test).

Orientation for a new developer or agent:

1. Read `PROJECT_STATE.md` (live status + exact next tasks), then
   `docs/architecture/ARCHITECTURE.md` and `DECISIONS.md`.
2. The money/GST/ABN engine (`lib/core/`) is the contract — its behaviour
   is locked by `tool/validate_financial_logic.py` (executed evidence)
   and mirrored Dart tests. Change both together or not at all.
3. Business rules live ONLY in `lib/data/repositories/` — UI never
   touches drift directly; keep it that way.
4. Issued documents are frozen snapshots (invariant 2). If a change makes
   an issued document render differently, it is a bug by definition.
5. Honesty rules from the build brief still bind: never claim a command
   ran or a test passed unless it did; record real outputs in
   docs/testing/.

Useful loops:

```bash
dart run build_runner watch --delete-conflicting-outputs   # drift codegen
flutter test test/gst_test.dart                            # fast money loop
flutter run                                                # device loop
python3 tool/check_sources.py                              # import/paren sanity
```
