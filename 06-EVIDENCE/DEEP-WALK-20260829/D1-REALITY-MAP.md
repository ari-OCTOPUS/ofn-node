---
type: reality-map
schema: deep-walk-reality-map/1
experiment_id: deepwalk-20260829-discovery
gate: DISCOVERY_ONLY
captured_at_utc: 2026-08-29T06:31:13Z
method: read-only SSH + local FS + SQLite mode=ro probes (no writes, no installs, no restarts)
author: zcode session (owner-directed deep walk)
---

# D1 — REALITY MAP (معماری واقعی از روی کد و سیستم زنده)

هر گزاره‌ی زیر FACT است با شاهد اجرایی؛ منبعِ هر بخش در انتهای سطر آمده.
نقش نودها **از روی سرویس‌ها و فایل‌های واقعی** استخراج شده، نه از مستندات.

## 0. خلاصه ۳۰ ثانیه‌ای

- لپ‌تاپ Hub زنده است: `organism.py` + `cortex.py` + `live/server.py` + `telegram_center` در حال اجرا.
  Heart v2 **فعال و RUNNING** (beat 2073, green_streak 181, brain ok=188/degraded=4, advisory_only=true).
- حافظه‌ی لپ‌تاپ **سه ذخیره‌گاه** دارد: `spine.db` (رویدادها، 13502) → `memory.db` (حافظه‌ی کنسولیده‌شده، 834، با FTS5) → ژنوم‌لجر (`ledger.jsonl`، 15094 سطر).
- مسیر «خواندن» حافظه **وجود دارد و می‌تپد** (`memory-read-latest.json` beat 54400، reads=3/cycle، readback=read_ok)
  ولی یکی از سه نقطه‌ی خواندن (`search_vault`) **همیشه خالی** برمی‌گرداند و متن رکوردهای experiment فقط `"spine"` است (سیگنال پایین).
- قیف تصمیم روی لپ‌تاپ: در spine.db از ۲۱ `proposal-issued` فقط **۳ `decided`** — گلوگاهِ «Use» همین‌جاست.
- برد ۱۸۰ دو لایه دارد: `octopus-mesh` (حمل‌ونقل spine: outbox/processing/receipts) + `/opt/octopus` lab organism
  (حافظه‌ی شناختی `organism.db`: episodes=6177، **lessons=9**، memory_read_receipts=26094، decision_evidence=19781).
- برد ۱۳۸ ستون فقرات کسب‌وکار است: ۸ سرویس فعال (bridge/router/control-router/cycle-settler/supervisor/verify-dispatcher/ofn/hypno)
  + `octopus-mesh` با receipts=4335. `owner_decision.py` یک **قرارداد داده‌ی کارت ۱۲-فیلدی مالک** است، نه موتور decide().
- برد ۱۸۲ سنسوریوم+شاهد است: NATS JetStream + ۷ سرویس (fusiond/reflex/metacontrol/world-model/skill-tracker/stability/sensorium)
  + دفتر شاهد: events=161094، verdicts=1192 (آخرین: `disputed` روی auto-verify، 2026-08-29T06:26Z)، owner_control_receipts=2.
  ⚠️ outbox آن **1198 آیتم** انبار شده.

## 1. نودها (از hostname واقعی)

| نود | hostname | SSH | TZ | نقشِ مشاهده‌شده در کد |
|---|---|---|---|---|
| لپ‌تاپ | (PC، F:\backup) | local | AUSEST (UTC+10) | Hub + قلب + حافظه‌ی مرکزی |
| 180 | octopus-continuity-180 | root@ (کلید) | UTC | cognition/proposal + lab organism + gateway L0 فقط‌خواندنی |
| 138 | DietPi | ari@ (کلید) | AEST (UTC+10) | business spine + router + settler + verify-dispatcher |
| 182 | sensorium-opi5pro | root@ (کلید) | UTC | sensorium (NATS/fusion) + شاهد (witness verdicts) + receipt مالک |

ساعت‌ها در لحظه‌ی probe سازگار بودند (همگی ≈06:25–06:31 UTC). `clock_skew` در schema رویدادهای spine وجود دارد ولی فعلاً مقدار ثابت خالی دیده شد.

## 2. لپ‌تاپ (Hub)

### 2.1 فرایندهای زنده (tasklist/CIM)
- PID 16860 `python -X utf8 organism.py`
- PID 10052 `python -X utf8 cortex\cortex.py`
- PID 18096 `python -X utf8 live\server.py`
- PID 23808 `telegram_center\center.py` + PID 26892 `miniapp_gateway.py`

### 2.2 Git
- branch: `rescue/octopus-live-tree-20260821` @ `7d65f2d2e66424c64b85795c7e1de24c838d892b`
- dirty: 1271 فایل؛ remote: `germline → E:/germline/octopus.git` (بare محلی؛ GitHub در این remote نیست)

### 2.3 معماری حافظه (سه ذخیره‌گاه + یک پل)

```
[نوشتن]  beat_scheduler / organs → _ops/spine/event_spine.py
              ↓ (append-only, bitemporal, idempotency_key, trust)
         _ops/state/spine/spine.db  (events=13502)
              ↓ (consolidation: admission/trust/supersede)
         _ops/state/memory/memory.db  (memory=834 + FTS5)   [_ops/memory/memory_store.py]
              ↓ (روایت بلندمدت)
         07 - Knowledge/genome-system/ledger/ledger.jsonl  (15094) + tip.json
[خواندن] _ops/memory_read_loop.py  (تیکِ خواندنِ زنده، ۳ نقطه):
            query_experiments · get_pending_hypotheses · search_vault
            + retrieve_similar_failures · retrieve_owner_decisions   [_ops/memory/cycle_context.py]
         → state/pulse/memory-context-latest.json  (memory-context/1)
         → مصرف‌کننده: _ops/cortex/improve.py (تصمیم‌ها با memory_context_id)
                        _ops/organism.py (pulse["memory_context"])
```

### 2.4 قرارداد خواندن (سندِ داخل کد، `memory_read_loop.py` خط ۸–۱۶)
- هر خواندن با `decision_time` فیلتر bitemporal می‌شود: `occurred_at<=dt AND recorded_at<=dt`؛ رکورد ناهل = حذف (FUTURE_DATA)، نه اصلاح ساعت.
- تلمتری: `memory_reads_per_cycle`؛ صفر ماندن = `MEMORY_STILL_WRITE_ONLY`.
- read-back: نوشتن در چرخه‌ی N باید در N+1 قابل بازیابی باشد.

### 2.5 وضعیت زنده‌ی خواندن (state/pulse، 2026-08-29T16:24 local)
- `memory-read-latest.json`: beat 54400، reads=3، `readback=read_ok`، last_id/newest_id جلو می‌رود → حلقه‌ی خواندن **زنده** است.
- `memory-context-latest.json`: ۲۱ experiment_id + ۲۴ hypothesis_id خوانده شد؛ **`vault_ids: []`** (search_vault خالی).
- متنِ رکوردهای experiment خوانده‌شده فقط `"spine"` است؛ رزولوشن محتوایی نزدیک صفر.

### 2.6 قیف رویدادهای spine.db (event_type → count)
```
system.beat 11399 · failed 1182 · outcome-recorded 559 · system.booted 181
accepted-measurement 97 · delivered 34 · hebb.observation 24
proposal-issued 21 · decided 3 · rejected 2
```
→ گلوگاه «Use»: ۲۱ پیشنهاد / ۳ تصمیم.

### 2.7 schemaهای کلیدی (برای memtest.py)

- `spine.db.events(event_id, idempotency_key, event_type, domain, occurred_at, recorded_at, producer, producer_sequence, correlation_id, mission_id, subject, trust, schema_version, payload_json, occurred_at_real, event_time_source, time_precision, legacy_no_event_time, clock_skew)`
- `memory.db.memory(memory_id, namespace, mkey, content, content_sha256, trust, provenance_json, confidence, salience, valid_from, valid_to, supersedes, privacy, schema_version, created_at, admission_state, tenant_id, project_id, scope, agent_id, task_id, classification, policy_version, evidence_ref, confidence_source, confidence_method)` + `memory_fts` (FTS5)
  ← schema از قبل consolidation-محور است: provenance اجباری، supersede با valid_from/valid_to، confidence با source/method.
- `chrono.db`: heartbeat=54400، checkpoint=54399، experience_meter=53906، heart_beat=2006، heart_event=456، heart_run=7، heart_outbox=0، gated_effect=0، anticipation_queue=0 (user_version=4, WAL)

### 2.8 یافته‌های write-only/مرده روی لپ‌تاپ
- `_ops/state/memory.db` (مسیر قدیمی) **خالی است** (صفر جدول) ولی کنار `state/memory/memory.db` واقعی زندگی می‌کند → فایل مرده/گمراه‌کننده (خطر mis-path در ابزارهای جدید).
- `vault_bridge.search_vault_evidence` خروجی [] می‌دهد (flag-gated) → یک‌سومِ نقاط خواندن عملاً خاموش.
- experimentهای `"spine"`-متنی با timestamp یکسان دسته‌ای نوشته می‌شوند → آلودگی حافظه با سیگنال پایین.

## 3. برد 180 (octopus-continuity-180)

### 3.1 لایه‌ها
- **حمل‌ونقل**: `/root/octopus-mesh` (git نیست — بدون branch/HEAD؛ deployment کپی است)
  صف‌ها: outbox=27 (شامل `180-to-138-partner-brief-20260829` و `180-to-138-megaprompt-build-20260829` — تولیدِ امروز)،
  processing=0، rejected=2، dead-letter=2 (`SUPERSEDED_TYPE_MISMATCH`)، receipts=16 claim + receipts/control=2.
- **شناخت**: `octopus-organism-lab.service` → `python3 -m ofn.organism.runtime.app --db /opt/octopus/lab/lab-data/organism.db`
- **سرویس‌های فعال**: afferent-lab، gateway (L0 فقط‌خواندنی، uvicorn)، llama-lab (llama.cpp محلی)، organism-lab.
- **تایمرها**: heartbeat و mesh-heartbeat هر ۶۰s؛ drain هر ۵min؛ mirror هر ۱۵min؛ cognitive-worker (اجرای `--once`؛ در لحظه‌ی probe 100% CPU).
- `octopus_cognitive_worker.py` **هیچ هوک حافظه‌ای ندارد** (grep: بدون memory/episode/lesson/organism.db) → کارگر شناختی فقط حمل‌ونقل است.

### 3.2 organism.db (حافظه‌ی شناختی ۱۸۰)
```
events 6177 · episodes 6177 · outbox 6177 · memory_read_receipts 26094
decision_evidence 19781 · identity_ledger 1859 · identity_heartbeat 1741
self_models 1631 · inner_speech 1620 · utterances 753 · lessons 9 · learned_topics 4
exams 10 · school_courses 10 · growth_habits 13 · futures 9 · ask_cache 6 · world_hosts 3
```
schemaهای کلیدی:
```
events(event_id, event_type, priority, payload_json, created_at, schema_version, hash, node_seq)
episodes(episode_id, source_event_id, event_type, salience, outcome, body_json, created_at)
lessons(lesson_id, created_at, source, topic, fact, evidence, status)
memory_read_receipts(receipt_id, purpose, decision_time, recorded_at, occurred_at, created_at,
                     rows_returned, future_use_count, ok, error, query_json)
decision_evidence(evidence_id, purpose, decision_time, receipt_id, event_ids_json,
                  episode_ids_json, created_at, executable)
outbox(delivery_id, event_id, hash, status, attempts, created_at, done_at)
```
- آخرین receipt خواندن: purpose=`school.C-memory`، rows_returned=16، ok=1، **future_use_count=0** — زنجیره‌ی receipt→تصمیم ثبت می‌شود ولی «استفاده‌ی آینده» هنوز صفر.
- آخرین lesson: `L-school` از parent («مدرسه AGI-SCHOOL-001 …») — درس‌های نوزده‌گانه بیشتر parent-taught هستند تا تجربه-مشتق (6177 episode → 9 lesson؛ نسبت 0.15%).

## 4. برد 138 (DietPi — business spine)

- `/home/ari/ofn` @ `integration/138-business-spine-20260828`، HEAD `a27eb0536793c7fc040917bb645e9057707298f4`، dirty=1، remote germline (mount محلی).
  ⚠️ HEAD از `68813370` (شروع کار قبلی) جلو کشیده شده.
- سرویس‌های فعال: `octopus-bridge`، `octopus-control-router`، `octopus-cycle-settler`، `octopus-router`، `octopus-supervisor`، `octopus-verify-dispatcher`، `ofn-heartbeat`، `ofn`، `hypno`.
- تایمرها: bridge-watchdog 2min، sync-watchdog 5min، heartbeat ~5min، budget-monitor 5min، scheduler 15min، backup روزانه.
- `/home/ari/octopus-mesh`: outbox=11، inbox=5، processing=0، dead-letter=0، **receipts=4335**، state=14.
- پروسه‌ها از `/home/ari/octopus-mesh/bin/` اجرا می‌شوند (supervisor/control_router/cycle_settler/router/verify_dispatcher).

### 4.1 API واقعی ماژول‌های بحرانی (برای chaintest/ادامه‌ی کار EDGE-6)
- `ofn/adapters/owner_decision.py`: `class OwnerDecision` + `render_fake()` + `validate()`.
  **قرارداد**: کارتِ ۱۲-فیلدی تصمیم مالک — decision_id، run_id، lane، action، recipient_masked،
  exact_payload، payload_sha، artifact_sha، verdict_sha، idempotency_key، expires_at، rollback.
  فلسفه (docstring): «رندر و اعتبارسنجی می‌شود، هرگز ارسال نمی‌شود» — نود برای اکشن RED کارت می‌سازد و مالک تصمیم می‌گیرد.
  **نتیجه**: هر تستی که `decide()/approve()` انتظار داشته باشد (مثل RED test قبلی) با طراحی واقعی ناسازگار است؛
  یالِ گم‌شده «ساخت کارت از سوی نود → تأیید مالک → enqueue در Outbox» است.
- `ofn/adapters/outbox.py`: `class OutboxItem` + `class Outbox` (+ `_migrate_manual_columns`).
- state نود در `ofn/` نیست؛ داده‌ی زنده در `/home/ari/octopus-mesh` و دیتای ایستا در `ofn/data/` است.

## 5. برد 182 (sensorium-opi5pro — شاهد/سنسوریوم)

- سرویس‌ها: `nats-server` (JetStream)، `octopus-fusiond` (S1: registry contract + sensor state + fusion frame)،
  `octopus-reflex` (A0 فقط‌مشاهده)، `octopus-metacontrol` (shadow)، `octopus-world-model` (پیش‌بین)،
  `octopus-skill-tracker`، `octopus-stability` (Prometheus 9101)، `octopus-sensorium`.
- دفتر شاهد `/root/octopus-mesh/state/witness/`: **events=161094، verdicts=1192، owner_control_receipts=2**.
  آخرین verdict (2026-08-29T06:26:16Z): `outcome=delivered_acked, verdict=disputed, idempotency_key=auto-verify:b08acb12…`.
- صف‌های mesh در 182: outbox=**1198** (انبار بزرگ)، processing=4، dead-letter=0.
- ریجستری‌ها: `/root/OCTOPUS-REGISTRY-100` (SIGNED-REGISTRY-BUNDLE + current-hashes.sha256)، `/root/OCTOPUS-REGISTRY-V6-META-SHADOW`.
- `/opt/octopus` پکیج کامل پایتون (cognition/core/schemas/ledger.py/releases).

## 6. جریان بین‌بردی مشاهده‌شده

```
لپ‌تاپ (Hub/قلب/حافظه) ⇄ 138 (business spine، receipts 4335) ⇄ 180 (proposal/cognition، outbox 27)
                                        ↓                          ↓
                              182 (witness verdicts 1192، sensorium NATS/fusion)
```
- امروز دو payload زنده در outbox ۱۸۸→۱۳۸ دیده شد (partner-brief و megaprompt-build هر دو 20260829).
- 138 خودش verify-dispatcher و cycle-settler دارد → حلقه‌ی settle-و-verify محلی.
- 182 verdict «disputed» روی auto-verify ثبت کرده → مسیر اختلاف‌ثبتی فعال است.

## 7. تناقض‌ها و بدهی‌های ثبت‌شده (اشاره به contradictions.jsonl)

1. برچسب نقش‌ها در پیام‌ها (۱۳۸=شاهد، ۱۸۲=receipt) با کد سازگار نیست: کد ۱۸۲ را شاهد (verdicts) و ۱۳۸ را ستون business + receipt-claim نشان می‌دهد.
2. `search_vault` در چرخه‌ی زنده همیشه خالی → یکی از سه نقطه‌ی خواندن عملاً مرده.
3. `_ops/state/memory.db` خالی کنار مسیر واقعی `state/memory/memory.db`.
4. RED test قبلی بر پایه‌ی API فرضی نوشته شده بود؛ API واقعی owner_decision کارت ۱۲-فیلدی است.
5. dead-letter ۱۸۰ (`SUPERSEDED_TYPE_MISMATCH`) و انبار ۱۱۹۸تایی outbox ۱۸۲ بدون مصرف‌کننده‌ی مشخص.

## 8. محدودیت‌های این نقشه

- مخزن GitHub از بیرون قابل خواندن نبود؛ remoteهای واقعی germline محلی‌اند → «GitHub Archaeology» به سطح
  commit-های محلی و فایل‌سیستم نودها محدود شد. Actions/CI بررسی نشد (نبود دسترسی).
- شمارش‌ها snapshot لحظه‌ای‌اند؛ سیستم زنده است و هر beat (~96s) مقادیر تغییر می‌کنند.
- محتوای payload ها فقط با نگاهِ هدر/متادیتا بررسی شد؛ `.env` و رازها هرگز خوانده نشدند.
