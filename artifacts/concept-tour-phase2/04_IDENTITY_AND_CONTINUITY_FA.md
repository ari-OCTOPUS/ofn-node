# هویت و تداوم: چه چیزی واقعاً verify می‌شود؟

## زنجیرهٔ v1

هر entry شامل sequence، organism ID، boot ID، event type، payload، nanosecond timestamp و previous hash است. canonical JSON با SHA-256 به `entry_hash` تبدیل می‌شود. genesis باید sequence 1 و previous hash آن ۶۴ صفر باشد. `[LOCAL-CODE] /opt/octopus/lab/ofn/organism/identity/ledger.py:13-53,70-103`.

Verifier این موارد را بررسی می‌کند:

- chain خالی نباشد؛
- entry اول `chain_genesis` باشد؛
- organism ID همان `board-life-001` باشد؛
- boot ID خالی نباشد؛
- sequence پیوسته باشد؛
- previous hash با entry قبلی برابر باشد؛
- hash محاسبه‌شده با stored hash برابر باشد.

`[LOCAL-CODE] identity/ledger.py:56-174`.

append قبل از نوشتن، کل chain موجود را verify می‌کند؛ سپس داخل `BEGIN IMMEDIATE` entry جدید را append یا rollback می‌کند. `[LOCAL-CODE] identity/ledger.py:197-284`.

## boot continuity

boot ID در شروع process جدید ساخته می‌شود و در heartbeat، health transition، process start/stop و LAN-listen event وارد ledger می‌گردد. genesis فقط یک‌بار ساخته می‌شود؛ bootهای بعدی همان chain را ادامه می‌دهند. `[LOCAL-CODE] runtime/app.py:46-48,147-167,644-723؛ identity/heartbeat.py:14-65`.

snapshot فاز ۲:

- 195 entry
- 19 boot ID متمایز
- اولین event: `chain_genesis`
- آخرین event هنگام snapshot: `identity_heartbeat`
- cryptographic/internal verification: valid

`[RUNTIME-VERIFIED] read-only SQLite identity_ledger hash verification`.

### استعارهٔ «شناسنامهٔ مهرشده»

A) **Vibe Coding:** هر boot صفحه‌ای تازه در شناسنامه است و مهر صفحهٔ قبل را با خود دارد.  
B) **ترجمهٔ مهندسی:** append-only hash chain با sequence، boot provenance و previous hash.  
C) **محدودیت:** hash-chain شخص، خودآگاهی یا حیات نمی‌سازد؛ فقط تغییر داخلی ناسازگار را قابل کشف می‌کند.

## tamper، truncation و anchor

- تغییر payload، sequence، organism ID یا previous hash در بخش موجود chain کشف می‌شود. `[LOCAL-CODE] identity/ledger.py:84-158`.
- حذف میانی باعث شکست sequence/previous hash می‌شود.
- **حذف tail ممکن است کشف نشود**، چون verifier نمی‌داند آخرین hash مورد انتظار خارج از DB چه بوده است.
- کد صریحاً `external_anchor=None` و `tail_truncation_detectable=False` برمی‌گرداند. `[LOCAL-CODE] identity/ledger.py:164-174,271-284`.

پس «identity chain valid» یعنی `INTERNAL_HASH_CHAIN_CONSISTENCY`، نه public PKI، نه timestamp authority و نه اثبات عمومی عدم truncation.

## attestation

attestation یک projection محلی از organism ID، stage، health، identity hash، place/source، school و external API است و خودش hash می‌شود. note صریح می‌گوید public PKI anchor نیست. `[LOCAL-CODE] /opt/octopus/lab/ofn/organism/identity/attestation.py:12-46؛ /opt/octopus/lab/state/ATTESTATION.json:5-16`.

وضعیت آن `LIVE_WITH_GAP` است:

- LIVE چون life tick آن را می‌نویسد و فایل فعلی identity valid را نشان می‌دهد. `[LOCAL-LIVE] runtime/life_cycle.py:385-387`.
- GAP چون signer مستقل، key-bound signature، remote witness و external anchor ندارد.

## `OWNER_ALIVE_C`

این مقدار در SQLite meta به‌عنوان `first_stage_label` ثبت شده و public status آن را منتشر می‌کند. `[RUNTIME-VERIFIED] SQLite meta.first_stage_label=OWNER_ALIVE_C؛ runtime/public_status.py:24-29,64-95`.

تفسیر درست:

- label مالک/مرحله است.
- معیار علمی حیات زیستی یا آگاهی نیست.
- package آینده نیز صریحاً `ALIVE_CLAIM=False` و `CONSCIOUS_CLAIM=False` دارد. `[LOCAL-SCAFFOLD] /opt/octopus/ofn-l4/ofnl4/__init__.py:1-13`.

## تداوم در برابر مدل

اگر Qwen از دسترس خارج شود، health می‌تواند `DEGRADED` شود؛ ولی identity ledger و SQLite باقی می‌مانند. کد نیز `model_failure_is_organism_failure=False` را اعلام می‌کند. `[LOCAL-CODE] runtime/app.py:175-215`.

این تفکیک مهم است:

```text
identity continuity = ledger + DB + boot provenance
language fluency    = llama.cpp/Qwen availability
owner label         = governance metadata
consciousness       = ادعا نشده و از این شواهد نتیجه نمی‌شود
```

## شکاف‌های آینده با OFN-L4

v2 مواد hash متفاوت، event_id و event linkage متفاوت و monotonic timestamp دارد. chain v1 و v2 را نمی‌توان با rename جدول یکی کرد. bridge باید terminal v1 hash را به‌عنوان migration anchor در اولین event v2 ثبت، mapping idempotent بسازد و chainهای اصلی را immutable نگه دارد. `[CONFLICT] v1 identity/ledger.py:31-53؛ v2 /opt/octopus/ofn-l4/ofnl4/identity.py:20-43`.

طرح bridge کامل در [07_OFN_L4_FUTURE_FA.md](07_OFN_L4_FUTURE_FA.md).

پاورقی مأموریت: [00_OWNER_ANSWER_FA.md#پاورقی-ماموریت](00_OWNER_ANSWER_FA.md#پاورقی-ماموریت).
