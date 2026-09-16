---
megaprompt_title: EQUIP موج C1 — گروه ۱ ارکستراسیون پایدار
version: "1.0"
sequence: 5
group: 1
wave: C
requires: "Wave B SCAN not FAIL"
next: "MEGAPROMPT-EQUIP-06-G3-PERCEPTION-2026-08-16.md"
written_by: "Cursor Grok 4.6 — 2026-08-16"
branch_name: "equip/g1-orchestration-20260816"
---

# پیست

۱) SHARED · ۲) همین فایل.
این گروه **پنجم** اجرا می‌شود نه اول. حافظه، تله‌متری، هویت و containment
باید قبل از orchestrator جدید بسته شده باشند.

# ماموریت: Durable Multi-Agent Orchestration

agent loopها، handoffها، queues، schedulers، state transitions، retries،
pause/resume و recovery پس از restart را map کن.

هدف: ماموریت چندمرحله‌ای پس از crash/restart/timeout بدون تکرار side effect
از آخرین checkpoint معتبر ادامه یابد.

## حقیقت این vault

- حلقهٔ زنده: organism / center / gateway / live / cortex (+ daemonهای جدا).
- صف‌ها: `_octopus/queue/` · telegram tool-requests · debate survivors ·
  deep-think slots.
- APScheduler / Windows Task Scheduler برای observatory hourly و Watch.
- LangGraph/Temporal **احتمالاً در tree نیستند** — discovery اجباری.
  framework دوم اضافه نکن اگر یک state machine کافی است.
- الگوی پژوهشی اجباری: task state **بیرون** context مدل
  (Manage-Execute-Audit).

## الزامات vertical slice

- canonical Run ID، Task ID، Agent ID، Correlation ID، Causation ID.
- state machine صریح: CREATED, PLANNED, APPROVAL_PENDING, RUNNING, PAUSED,
  RETRYING, COMPLETED, FAILED, CANCELLED, COMPENSATING.
- transition غیرمجاز = رد + audit.
- checkpoint پایدار و versioned.
- idempotency key برای هر side effect.
- retry bounded + exponential backoff + jitter. poison task / retry storm.
- cancellation از NBB-CP و kill switch منتشر شود.
- worker پس از restart task تکمیل‌شده را دوباره اجرا نکند.
- اگر Temporal/LangGraph/Celery/NATS موجود است، همان را تکمیل کن.

## سناریوی acceptance

workflow آزمایشی سه‌مرحله‌ای. در مرحلهٔ ۲ process را عمداً متوقف کن،
restart کن، ثابت کن از checkpoint درست ادامه می‌یابد و side effect مرحلهٔ
۱ تکرار نمی‌شود.

## اسکن تخصصی

duplicate execution · lost task · stale lock · dead letter · race ·
split-brain worker · infinite retry · cancellation propagation ·
checkpoint corruption · replay determinism.

## TECHNOLOGY OPTIONS — GROUP 1

تحقیق جدا 2026-08-16.

PRIMARY:

- LangGraph 1.2.11 (2026-08-11): `add_node(trace_policy=...)`،
  checkpoint 4.2.0، checkpoint-postgres 3.1.2.
  https://github.com/langchain-ai/langgraph/releases/tag/1.2.11
  اگر از قبل در tree است pin کن؛ orchestrator دوم نساز.
- Temporal v1.31.2 (2026-07-08): replication streaming authorized؛
  CVE-2026-5724 MEDIUM فیکس شده. `system.disableStreamingAuthorizer`
  را روشن نکن مگر لازم — روشن کردنش endpoint را آسیب‌پذیر می‌گذارد.
  https://github.com/temporalio/temporal/releases/tag/v1.31.2
  https://github.com/advisories/GHSA-q98v-9f9w-f49q
  Temporal فقط برای مأموریت irreversible/cross-crash. برای لپ‌تاپ شخصی
  ممکن است سنگین باشد — gap را ثابت کن قبل از نصب.
- ByteDance deer-flow (~80k★): SuperAgent harness روی LangGraph.
  https://github.com/bytedance/deer-flow
  **جایگزین هستهٔ Octopus نیست** — الگوی sandbox+subagent را بخوان.
- Restate / Inngest / Upstash Workflow / Mastra: فقط اگر stack مناسب است
  (Mastra = TypeScript).

PAPERS:

- LongHorizon-Harness 2608.01964 (2026-08-03): MEA loop؛ state بیرون context.
  https://huggingface.co/papers/2608.01964
  https://github.com/AMAP-ML/LongHorizon-Harness
- SkillOrchestra 2602.19672 · The Long-Horizon Task Mirage 2604.11978

DO

- Manage-Execute-Audit به‌صورت state machine صریح.
- LangGraph checkpoint **یا** Temporal — نه هر دو مگر نقش‌ها جدا و مستند.

DO NOT

- toy آرشیوشده. orchestrator دوم. self-evolving harness به‌عنوان runtime.

## خروجی

`06-EVIDENCE/EQUIP-G1-ORCHESTRATION-2026-08-16.md`.
