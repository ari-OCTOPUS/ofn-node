# تور قلب رویداد، SQLite و حافظه

## Event heart

رویداد v1 با JSON canonical (`sort_keys`، separator فشرده، UTF-8) و SHA-256 ساخته می‌شود؛ schema ناشناخته، priority نامعتبر و hash ناسازگار رد می‌شوند. `[LOCAL-CODE] /opt/octopus/lab/ofn/organism/contracts/events.py:5-45`.

`EventKernel.commit_event()`:

1. event را validate می‌کند.
2. duplicate ID/hash را idempotent یا conflict می‌بیند.
3. sequence بعدی را می‌گیرد.
4. داخل `BEGIN IMMEDIATE`، هم `events` و هم `outbox` را می‌نویسد.
5. commit می‌کند.
6. **پس از commit** تلاش می‌کند item را در queue محدود ۵۱۲تایی بگذارد.
7. اگر queue پر باشد، event از دست نمی‌رود؛ outbox pending با `replay_pending()` بازیابی می‌شود.

`[LOCAL-CODE] event_kernel/kernel.py:6-69,81-104؛ contracts/events.py:5-12`.

این یعنی حقیقت اصلی queue حافظه‌ای نیست؛ rowهای commit‌شده‌اند. در snapshot فاز ۲، `events=319`، `outbox=319 done`، sequence پیوسته و event hash mismatch صفر بود. `[RUNTIME-VERIFIED] SQLite tables events/outbox؛ read-only integrity snapshot`.

### استعارهٔ «قلب و صندوق پست»

A) **Vibe Coding:** قلب اول ضربان را در دفتر ثبت می‌کند، بعد نامه را به اندام‌ها می‌فرستد.  
B) **ترجمهٔ مهندسی:** transaction اتمیک events+outbox، سپس queue/dispatch و replay.  
C) **محدودیت:** SQLite قلب زیستی نیست؛ ثبت row هیچ انگیزه، احساس یا حیات تولید نمی‌کند.

## رجیستری SQLite

DB زنده: `/opt/octopus/lab/lab-data/organism.db`.

- persistent journal mode برابر WAL و synchronous snapshot برابر `2` (`FULL`) بود. source نیز `WAL`، `FULL`، FK ON و busy timeout 5000ms را برای connection فعال می‌کند. `[LOCAL-LIVE] persistence/db.py:195-209؛ SQLite PRAGMA read-only snapshot`.
- `integrity_check=ok`، `quick_check=ok` و foreign-key violation صفر. `[RUNTIME-VERIFIED] SQLite read-only URI mode=ro + query_only=1`.
- uniqueness رویداد با PK `event_id` و UNIQUE `hash`؛ episode با unique index `(source_event_id,event_type)` محافظت می‌شود. `[LOCAL-CODE] persistence/db.py:10-28,173-192`.
- sidecarهای DB/WAL/SHM همگی `0644 root:root` بودند؛ این یک ریسک محرمانگی محلی است، نه corruption اثبات‌شده. `[RUNTIME-VERIFIED] stat /opt/octopus/lab/lab-data/organism.db{,-wal,-shm}`.
- source جدول `wan_fetches` را تعریف می‌کند، ولی DB زنده آن را ندارد؛ این schema drift با source/runtime drift هم‌راستاست. `[CONFLICT] persistence/db.py:143-165؛ SQLite sqlite_master`.

## ER ساده

```text
events (event_id PK, hash UNIQUE, node_seq)
   | 1
   +------< outbox (event_id FK, status)          commit/replay truth
   |
   +------< episodes (source_event_id FK)         episodic projection
   |
   +------< self_models (source_event_id logical) self snapshots
   |
   +------< utterances (source_event_id logical)  grounded output

identity_ledger (sequence PK, previous_hash, entry_hash UNIQUE)
identity_heartbeat (legacy/body snapshots)

meta (k PK) -------- heartbeat/rhythm/state settings
ask_cache (request_hash PK) --- model-response reuse
lessons / exams / school_courses / futures / learned_topics
world_hosts / growth_habits / inner_speech

wan_fetches --- declared in current source, ABSENT in live schema
```

توجه: فقط FKهای صریح `outbox.event_id` و `episodes.source_event_id` را database enforce می‌کند؛ رابطه‌های `self_models` و `utterances` با source event در schema FK صریح ندارند. `[LOCAL-CODE] persistence/db.py:20-91`.

## snapshot شمارش row

- ask_cache 6
- episodes 319
- events 319
- outbox 319 (همه done)
- identity_heartbeat 158
- identity_ledger 195
- self_models 48
- utterances 23
- inner_speech 37
- learned_topics 4
- lessons 9، exams 10، school_courses 10، futures 9
- growth_habits 4، world_hosts 3، meta 19

`[RUNTIME-VERIFIED] read-only SQLite row-count snapshot؛ هیچ payload خصوصی خوانده/نوشته نشد`.

## event، episode و summary

`remember()` بدون `source_event_id` summary را رد می‌کند، وجود source event را بررسی می‌کند، type را برابر می‌خواهد و duplicate projection را idempotent برمی‌گرداند. `[LOCAL-CODE] memory/episodic.py:5-42`.

`recall()` episode را با event join می‌کند و hash source و `provenance_valid` می‌دهد. `[LOCAL-CODE] memory/episodic.py:44-80`.

در DB فاز ۲:

- orphan episode: 0
- type mismatch: 0
- duplicate `(source_event_id,event_type)`: 0
- تعداد episode و event هر دو 319

`[RUNTIME-VERIFIED] SQLite relationship checks`.

## شش حافظه که یکی نیستند

1. **Event Store**  
   هدف: حقیقت رویداد و ترتیب node. persistence: SQLite. writer: EventKernel. reader: replay/queries. عمر: تا حذف/خرابی DB. failure: corruption، disk full، sequence conflict. منبع حقیقت: بله.

2. **Episodic Memory**  
   هدف: projection با salience/outcome و provenance. persistence: SQLite episodes. writer: handler wildcard پس از dispatch. reader: recall و snapshot enrichment. عمر: پایدار. failure: source/type mismatch. منبع حقیقت مستقل: خیر؛ مشتق از event است.

3. **Ask Cache**  
   هدف: reuse پاسخ مدل برای request hash namespaced. persistence: SQLite ask_cache. writer/reader: AskCascade. عمر: پایدار تا پاک‌سازی. failure: stale policy/model namespace یا write error. منبع حقیقت هویت: خیر. `[LOCAL-CODE] cognition/backend.py:20-23,140-224`.

4. **Vault**  
   هدف: Markdown عمومی برای انسان/agent دیگر. persistence: فایل‌های `/opt/octopus/lab/vault/board-life-001`. writer: export در life tick. reader: انسان/ابزار. failure: drift از DB. منبع حقیقت: خیر؛ projection است. `[LOCAL-CODE] runtime/life_cycle.py:385-409`.

5. **Identity Ledger**  
   هدف: continuity/tamper evidence. persistence: SQLite identity_ledger. writer: startup/heartbeat/health transitions. reader: verifier/attestation. failure: hash break یا truncation بدون anchor. منبع حقیقت هویت داخلی: بله.

6. **LLM KV Cache**  
   هدف: reuse محاسبهٔ token در inference. persistence: معمولاً حافظهٔ engine و کوتاه‌عمر. writer/reader: vLLM scheduler/worker. lifetime: request/cache eviction/process. failure: miss/eviction/OOM؛ نباید identity یا episode شود. `[DOCUMENTED] /opt/octopus/ofn-l4/docs/SCALE-AND-ACTIVE-INFERENCE.md:238-334`.

## Mandatory retrieval: wiring واقعی و gap

`enrich_snapshot()` هر بار `recent_memory_lines()` را می‌سازد و آن تابع `recall(limit=40)` دارد؛ بنابراین retrieval در چرخهٔ snapshot فعلاً wired است. `[LOCAL-CODE] runtime/life_cycle.py:57-69,72-105`.

اما:

- هیچ symbol یا meta key به نام `memory_reads_per_cycle` در source پیدا نشد.
- SQLite meta نیز این key را ندارد.
- fail-closed contract که «هر cycle دقیقاً حداقل یک read موفق» را enforce/metric کند وجود ندارد.

نتیجه: `Mandatory Retrieval = LIVE_WITH_GAP` و `MEMORY_READ_ENFORCED=false`.

identity در [04_IDENTITY_AND_CONTINUITY_FA.md](04_IDENTITY_AND_CONTINUITY_FA.md) و cognition/cache در [06_COGNITION_AND_MODELS_FA.md](06_COGNITION_AND_MODELS_FA.md).

پاورقی مأموریت: [00_OWNER_ANSWER_FA.md#پاورقی-ماموریت](00_OWNER_ANSWER_FA.md#پاورقی-ماموریت).
