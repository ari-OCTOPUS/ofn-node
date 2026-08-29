# دلتا از فاز ۱

اعداد runtime snapshot هستند و serviceهای زنده ممکن است sequence/row/time را پس از snapshot جلو ببرند. presence فایل به معنی activation نیست.

## اندازه و شمارش

- `/opt/octopus` allocated: فاز ۱ `~815 MiB`؛ پیش از خروجی فاز ۲ `815M`؛ نتیجه `بدون تغییر معنادار`.
- apparent bytes فاز ۲: `829,572,399`.
- file count: فاز ۱ `~8042`؛ pre-output فاز ۲ `8081` (`+39`)؛ post-output اعتبارسنجی‌شده `8101` چون دقیقاً ۲۰ report مجاز اضافه شد.
- directory count excluding root: فاز ۱ `~1236`؛ pre-output `1237` (`+1`)؛ post-output اعتبارسنجی‌شده `1238` به‌علت report directory جدید.
- root usage: فاز ۱ `89% / ~6.6 GiB free`؛ فاز ۲ `89% / 6.54 GiB free`.
- model: فاز ۱ `~410 MiB`؛ فاز ۲ `410M allocated` و `428,970,080` بایت فایل مدل.

`[RUNTIME-VERIFIED] du/os.walk/df/stat snapshot؛ شمارش post-output در validation نهایی کنترل شد`.

## لایه‌های baseline

- authoritative organism path: unchanged، `/opt/octopus/lab/ofn/organism`.
- disk package version: `0.6.0 → 0.6.0`.
- DB path: unchanged، `/opt/octopus/lab/lab-data/organism.db`.
- OFN-L4/gateway/models/runtime paths: unchanged و present.
- local cortex: unchanged؛ llama.cpp + Qwen3-0.6B روی loopback 8081.
- organism listeners: unchanged؛ loopback و board identity روی 8090.
- public health/autonomy: `STABLE / PROPOSE_ONLY → STABLE / PROPOSE_ONLY`.
- identity: `valid → valid`.
- soak: `running/no abort → running/no abort`.

`[RUNTIME-VERIFIED] service/listener/sanitized state؛ [LOCAL-CODE] organism/__init__.py:1-2`.

## شواهد تازهٔ فاز ۲

- DB integrity/quick check هر دو `ok`، FK violation صفر.
- event/episode/outbox snapshot هرکدام 319؛ outbox همه done.
- event hash mismatch صفر و node sequence پیوسته.
- identity ledger 195 entry در 19 boot و cryptographic verification معتبر.
- sidecar modes هر سه 0644.
- source/runtime mismatch به‌صورت timestamp + schema تأیید شد.
- `memory_reads_per_cycle` در source/meta غایب، با وجود recall wiring.
- OFN-L4 دقیقاً ۱۰ فایل، بدون runtime/test/var/8091.
- vLLM، cbor2، pymdp و torch present نیستند.
- Rockchip DRM/NPU node present است، ولی CUDA/ROCm-compatible GPU evidence نیست.
- Git coverage: 40 tracked، 491 untracked، 2 commit.
- systemd exposure: gateway 9.6 UNSAFE؛ چهار service اصلی دیگر 9.0 UNSAFE.

## تعارض source/runtime

قدیم/فاز۱: «source جدیدتر از process و schema زنده» گزارش شده بود.  
فاز۲ validation:

- process start: `08:52:03 UTC`
- `persistence/db.py` mtime: `08:58:38 UTC`
- `cognition/wan.py` mtime: `08:59:23 UTC`
- source table: `wan_fetches`
- live sqlite_master: table absent

نتیجه همچنان `RUNTIME_SOURCE_MISMATCH` است. `[CONFLICT] service metadata؛ persistence/db.py:143-165؛ SQLite schema`.

## vLLM evidence

- sha256 offline: passed/status OK.
- sha256_cbor: unavailable/optional skip because cbor2 missing.
- block-size harness: 51 new tests passed in existing record.
- GPU benchmark: not run.
- empirical rows: 0.
- winner: none.
- deployment/canary: none.

`[LOCAL-OFFLINE-LAB] artifacts/prefix-cache؛ artifacts/vllm-block-size؛ local execution record`.

## چیزهایی که عمداً scan نشد

secret value، private letter/utterance، raw prompt، token، process environment/active command line، binary model content، archive و vendor/venv internals. این exclusions به‌عنوان `UNSCANNED_PATHS` ثبت شده‌اند، نه این‌که absent فرض شوند.

## final status fields

- `LOCAL_CONCEPT_COVERAGE=COMPLETE_FOR_REQUESTED_STUDY_WITH_EXECUTION_GAPS`
- `LIVE_RUNTIME_COVERAGE=PARTIAL`
- `OFFLINE_LAB_COVERAGE=STRONG_PARTIAL`
- `OFN_L4_COVERAGE=SCAFFOLD_ONLY`
- `EVIDENCE_COVERAGE=HIGH_WITH_DECLARED_EXCLUSIONS`
- `UNSCANNED_PATHS=PROTECTED_OR_NONESSENTIAL_CONTENT`
- `SOURCE_RUNTIME_MATCH=false`
- `MEMORY_READ_ENFORCED=false`
- `IDENTITY_CHAIN_VALID=true`
- `SOAK_STATUS=RUNNING_NO_ABORT_AT_SNAPSHOT`
- `DISK_RISK=HIGH`
- `GIT_REPRODUCIBILITY=POOR`
- `BACKUP_RELIABILITY=LOW_BLOCKED`
- `VLLM_RUNTIME_PRESENT=false`
- `GPU_PRESENT=false_for_vLLM`

`FINAL_STATUS=CONCEPTUAL_KNOWLEDGE_LOCAL_WITH_GAPS; RUNTIME_SOURCE_MISMATCH; LOCAL_ARTIFACTS_AT_RISK`.

پاسخ نهایی و footer بدون side effect در [00_OWNER_ANSWER_FA.md#پاورقی-ماموریت](00_OWNER_ANSWER_FA.md#پاورقی-ماموریت) است.
