# TEST-RUNNER-CONTRACT — OCTOPUS sandbox test authority

قرارداد runnerِ manifest-driven (`test-authority/run_sandbox_suite.py`). NOT a blanket
pytest collector — هر فایل در subprocess مجزا با قراردادِ درستِ خودش اجرا می‌شود.

## ۱. منبعِ حقیقتِ ثبت
`_ops/tests/run_all.py` (authoritative registry، اما ممکن است stale). runner آن را
import و reconcile می‌کند:
- `TESTS` → runner=`python` (script-native، direct-run) مگر در `PYTEST_TESTS`.
- `PYTEST_TESTS` → runner=`pytest` (pytest-native؛ direct-run آن‌ها green-lie می‌دهد).
- `EXTRA_TESTS` → مسیرهای absolute خارج از `_ops/tests`.
`test_manifest.json` از همین ساخته می‌شود.

## ۲. طبقه‌بندی (script vs pytest)
- **SCRIPT_NATIVE**: assertionها/checkهای top-level، `__main__`، و `sys.exit(1 if failed else 0)`
  قراردادِ اصلی است. اجرا: `python -X utf8 <file>`. (مثال معتبر: `test_durable_journal.py` —
  **phantom نیست**، `run_all.py:215-217`.)
- **PYTEST_NATIVE**: fixture/تابعِ pytest، بدون top-level exit. اجرا: `python -m pytest -q <file>`.
- **QUARANTINED_WITH_REASON**: فقط اگر API/ماژول در candidate واقعاً نباشد، obsolete/متناقض
  باشد، owner-only/manual باشد، یا حتی با fake ناامن باشد. **هرگز silent drop از مخرج.**

## ۳. ایزوله‌سازی (per subprocess)
- `REAL_VAULT = F:\octopus-phase0-isolated` (candidate) — کدِ تحتِ تست و داده فقط از candidate.
- `ORG_ROOT/OPS_DIR/STATE_DIR/GENOME_DIR/TEMP/TMP` → sandbox موقتِ per-run.
- seedِ سنتتیک `budgets.yaml` (از `harness.TEST_BUDGETS`) تا تست‌های config-reader به‌جای
  fallback به live، ایزوله اجرا شوند.
- secretهای env scrub؛ `OCTOPUS_TEST_FILE` per-file برای ردیابیِ evidence.

## ۴. Barrier (backstop، fail-loud)
`sandbox_barrier.py` via sitecustomize **قبل از هر import** نصب می‌شود:
- **write**: builtins/io.open, os.open(write-flags), os.remove/unlink/rmdir/mkdir/makedirs,
  os.rename/replace/link/symlink (src+dst), Path.open(w)/write_*/touch/unlink/mkdir/rename/replace,
  shutil.copy*/move/copytree/rmtree, sqlite3.connect(writable) — هر مقصدِ زیر `F:\backup` رد+ثبت.
- **network**: external رد؛ loopback مجاز به‌جز پورت‌های paid (LiteLLM 4000، Ollama 11434).
- **process**: python (sandbox-bound، ارثِ barrier via PYTHONPATH) مجاز؛ cmd/.bat/.ps1/powershell رد.
- **fail-loud**: اگر install بیفتد، child با `os._exit(97)` + مارکرِ `*.BARRIER_FAILED` می‌میرد
  (هرگز تستِ بی‌محافظ اجرا نمی‌شود — تضمینِ اعتبارِ evidence).
- **acceptance بر ATTEMPTS**: `suite_attempted_live_writes==0` (نه فقط successful). `barrier_install_failures==0`.

## ۵. مراحل (stages)
0 barrier/self · 1 unit · 2 authority/security · 3 storage/replay · 4 memory/outcome/receipt ·
5 adapter+fakes · 6 registered · 7 unregistered · 8 sandbox integration.
(heuristic فعلی: نام‌های security-critical → stage 2؛ بقیه → stage 1. توسعه‌پذیر در manifest.)

## ۶. ثبتِ per-file
file · stage · runner · returncode · duration · output-tail · result
(PASS/FAIL/TIMEOUT/MISSING) · و از barrier: attempted-live-writes، external-network-attempts،
install-failures، child-with-evidence. خروجی: `FULL-SANDBOX-TEST-REPORT.json`.

## ۷. گیتِ خروج (F-Gates)
attempted_live_writes==0 · successful_live_writes==0 · external_network_attempts==0 ·
paid_provider_calls==0 · secrets_printed==0 · barrier_install_failures==0 · همهٔ valid tests
اجرا شده و quarantineها justified.
