---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, cockpit-v2, owner-queue, p1]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P1-QUEUE-IDENTITY]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/runtime-provenance-20260828T230743Z/CHECKPOINT]]"
---

# P1 — Metadata-only Owner Queue Projection

```
P1_SEAM_ADDED=true
P1_SOURCE_COMMIT=a27eb0536793c7fc040917bb645e9057707298f4
P1_RUNTIME_LOADED=false
MESH_ITEMS_UNCHANGED=true
OWNER_ITEMS_VISIBLE=true
IDEMPOTENCY_PARITY=true
PII_LEAKS=0
PURITY_SUITE_PASSED=true
TARGETED_COLLECTED=73
TARGETED_PASSED=73
TARGETED_FAILED=0
TARGETED_ERRORS=0
TARGETED_SKIPPED=0
TARGETED_DURATION_SECONDS=7.733
FULL_COLLECTED=2076
FULL_PASSED=2065
FULL_FAILED=0
FULL_ERRORS=1
FULL_SKIPPED=10
FULL_DURATION_SECONDS=24.756
FULL_NEW_FAILURES=0
SPARSE_COMMIT_CLEAN=true
RUNTIME_CHANGES=0
EXTERNAL_EFFECTS=0
MARK_AS_FIXED=NO
NEXT=P2_DISCOVERY
```

## تغییر

فقط چهار فایل در repository واقعی ۱۳۸:

- `ofn/node.py` — `owner_queue_metadata()`؛ مشتق از `owner_queue()`، فقط شش فیلد allowlisted.
- `ofn/run.py` — callback اختیاری `owner_queue_metadata` در seam موجود.
- `ofn/adapters/cockpit_v2_read_model.py` — گروه additive به نام `data.owner_items`.
- `tests/test_cockpit_v2_owner_queue.py` — ۱۱ تست رفتاری؛ guessed-interface test از discovery خارج و در evidence نگه داشته شد.

هیچ endpoint، adapter، DB، queue، command bus یا UI تازه ساخته نشد. `http_api.py` دست‌نخورده است.

## RED → GREEN

RED واقعی: ۱۱ تست، ۸ error. دو علت:

1. `Node.owner_queue_metadata` وجود نداشت.
2. `data.owner_items` وجود نداشت.

لاگ RED نشان می‌دهد `items` mesh از قبل پایدار بود و keys فقط
`items/limit/next_cursor/total` بودند.

GREEN:

- targeted Cockpit suites: ۷۳/۷۳.
- shadow: `owner_items_visible=true`, `idempotency_parity=true`,
  `mesh_items_unchanged=true`, `pii_leaks=0`.
- hash پاسخ shadow:
  `2e31f8b404430df33662ca705ca0af06a81fa2921c971cc0bd78cc7ad16964fa`.

## Full suite

یک‌بار اجرا شد:

```
Ran 2076 tests in 24.756s
FAILED (errors=1, skipped=10)
```

تنها error همان baseline تاریخی است:
`test_greeting_name` → relative import بدون package parent.
با baseline ۲۸ اوت (۲۰۲۸/۲۰۱۷/۱/۱۰)، افزایش ۴۸ تست = ۳۷ تست spine + ۱۱ تست P1؛ error تازه صفر.

## Identity semantics

`data.items` دقیقاً از نظر shape/ID قبلی حفظ شد؛ id آن همچنان `message_id` است.
این انتخاب برای backcompat بر دستور متناقض «هم unchanged و هم `mesh:` prefix»
مقدم شد. Business ID namespaced است: `business:<tenant:idem>`.

## Truth / failure semantics

- callback غایب یا exception → `owner_items=null` + endpoint `degraded` + warning.
- callback معتبر و خالی → `owner_items=[]` (صفر واقعی).
- duplicate/malformed → degraded؛ یک native ID حداکثر یک row.
- raw payload، customer data، phone، email، source_ref و token در projection نیست.
- مقادیر ناقص `null` و row truth=`UNKNOWN`؛ چیزی ساخته نمی‌شود.

## Runtime boundary

process PID `1351408` قبل از این source commit شروع شده و restart نشد.
پس P1 در source ثابت شده، اما runtime زنده هنوز آن را load نکرده است.
Instrumentation داخل تست باقی مانده تا owner پس از restart/canary تأیید کند.

## Sparse-checkout

روی `/home/ari/ofn`:

- `core.sparseCheckout` unset.
- `git sparse-checkout list` → worktree not sparse.
- هیچ commit با `ucp-forensic` پیدا نشد.
- recent commits همان audit/discovery/spine ثبت‌شده‌اند.

`SPARSE_COMMIT_CONTAMINATION` برای این worktree مشاهده نشد.

## Vault validators

- frontmatter: ۸۵۱ نوت، ۴۸۳ خطا، exit 1.
- broken links: ۴۱۵۵ نوت، ۱۹ لینک شکسته در لایهٔ دست‌چین، exit 1.
- هیچ خطا/لینک تازه‌ای از مسیرهای این بسته گزارش نشد؛ بدهی‌ها pre-existing
  هستند و برای سبزکردن validator تغییر داده نشدند.
