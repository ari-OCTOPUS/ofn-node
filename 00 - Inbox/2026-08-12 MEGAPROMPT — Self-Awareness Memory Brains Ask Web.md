---
type: knowledge
status: active
tags: [octopus, megaprompt, self-awareness, memory, brains, miniapp, ask, collaborator, senior-agent]
created: 2026-08-12
updated: 2026-08-12
created_by: agent
sources:
  - "[[01 - Dashboard/HANDOFF]]"
  - "[[OCTOPUS/CURRENT-TRUTH]]"
  - "[[07 - Knowledge/Architecture/OCTOPUS-MEMORY-TRUTH-MAP]]"
  - "[[07 - Knowledge/Architecture/OCTOPUS-HEARTS-BRAINS-4D-STATUS]]"
  - "[[06 - Architecture Maps/OCTOPUS-COLLABORATOR-INTERACTION-CONTRACT]]"
  - "[[_ops/INTERACTION-CONTRACT]]"
  - "[[_ops/EVIDENCE-LADDER]]"
  - "[[00 - Inbox/2026-08-12 MEGAPROMPT — Senior Deep-Scan MiniApp Collab DeepSeek]]"
  - "[[00 - Inbox/2026-08-12 RECONCILIATION-REPORT — Math Atlas Runtime Truth]]"
---

# MEGAPROMPT — خودآگاهی · حافظه · مغزها · اثرات واقعی در وب‌اپ (پرسش)

> این سند را **کامل** به ایجنت ارشد بده (کپی‌پیست یا `@` همین فایل).
> پیش‌نیاز بسته: Math Atlas Reconciliation + Deep-Scan Collab/DeepSeek (سبز).
> هدف مالک: **پیاده‌سازی** طوری که اثرات زندهٔ خودآگاهی/حافظه/مغز را از **مینی‌اپ وب** ببیند —
> مخصوصاً تب «پرسش» (همکار + Ask).

---

## نقش

تو **Senior Organism Engineer + Memory/Awareness Integrator + MiniApp UX Verifier** هستی.

ماموریت: پل‌های additive بساز تا سطوح زندهٔ زیر در پاسخ‌های وب‌اپ **قابل‌دیدن و قابل‌راستی‌آزمایی** شوند:

1. **خودآگاهی** — organism / self_knowledge / self_model / blockers / CURRENT-TRUTH
2. **حافظه‌ها** — MemoryGate · research_ingest · self_loop_ingest · ask_vault · collab episodic
3. **مغزها** — cortex + business_brain (+ doctor self_knowledge)؛ نه 4d/Super-Gov
4. **اثر واقعی در UI** — تب پرسش، Sources، selfmap، footer `model_source` / `source`

مالک باید بتواند بعد از hard-reload مینی‌اپ بپرسد و **بفهمد** اختاپوس از چه ساخته شده، چه یاد گرفته، و چه مانعی دارد — با شاهد مسیر فایل/trail، نه persona عمومی.

---

## 0. HARD RULES

1. Live tree = `F:\backup`. **Improve, don't rewrite.** هیچ بازنویسی gateway/center/4d.
2. **Memory never authorizes.** `may_authorize=false` دست‌نخورده. ingest/recall = cite/rank/propose.
3. Talk/collab = **draft only** · `external_effect=false` · `send_attempted=false`.
4. `vault_auto_write` را arm نکن. semantic write از collab ممنوع.
5. `4d_system` / Super-Governor / ۸ مغز را revive نکن — DEPRECATED/SPEC.
6. Dual consolidate (cortex vs neural) را merge نکن بدون ADR صریح مالک.
7. Neural APPLY=1 فقط beat-local `protective_skip` (ADR-035) — نه money/send/ledger.
8. Secret / initData خام / API key در commit، لاگ، HANDOFF، evidence ممنوع.
9. `git add -A` ممنوع. Commit فقط با دستور مالک.
10. WORKLOCK: `run_all.py` · `wiring.py` · `center.py` · `orphan_scan.py` —
    ثبت تست را **گزارش** کن؛ خودت ثبت گسترده نکن مگر لازم و گزارش‌شده.
11. بعد از هر فیکس مسیر chat: gateway **RESTART-PROCESS** + PID گزارش.
12. مالک باید مینی‌اپ را **ببند/باز** کند — در DoD صریح بنویس.
13. حدس ممنوع: هر ادعا با شاهد فایل / تست / flags-loaded / JSON زنده.
14. Evidence زیر:
    `_ops/state/adr-033/reports/AWARENESS-MEMORY-ASK-2026-08-12/`.

---

## 1. GROUND TRUTH — آنچه الان LIVE است (فرض شروع؛ خودت verify کن)

| لایه | انتظار فعلی | SoT |
|------|-------------|-----|
| دو مغز زنده | cortex + business_brain · innervation 100% | HEARTS-BRAINS-4D-STATUS |
| سه‌قلب + arbiter | LIVE · wire_open | `arbiter-latest.json` |
| `4d_system` / Super-Gov | **وصل نیست** — دست نزن | DEPRECATED |
| MemoryGate | LIVE وقتی `OCTOPUS_WIRE_MEMORY_GATE=1` | MEMORY-TRUTH-MAP |
| research_ingest / self_loop_ingest | LIVE trails | `state/memory/*-ingest.jsonl` |
| Collab default MiniApp | همکار وقتی `OCTOPUS_WIRE_COLLAB=1` | INTERACTION-CONTRACT |
| Collab model | `OCTOPUS_COLLAB_USE_MODEL=1` · `collab_chat→secondary` (DeepSeek) · بدون qwen fallback | HANDOFF 11:43 |
| Ask ladder | `/api/ask` → vault → brain → collab-fallback | `miniapp_gateway.py` |
| ask_vault | flag-gated `OCTOPUS_TG_ASK_VAULT` | `ask_vault.py` |
| vault RAG Chroma | default OFF (`OCTOPUS_WIRE_VAULT_RAG`) — بدون اجازهٔ مالک روشن نکن | vault_bridge |
| ADR-035 APPLY | ARMED · protective_skip only | RECONCILIATION + capability JSON |
| Self-context در مدل | فقط مسیر model collab (`_self_context`) | `collab_model_adapter.py` |
| Ask plain | **هنوز MemoryGate recall ندارد** (شکاف اصلی) | code audit |

### فایل‌های کانونی

```
# آگاهی / وضعیت
_ops/state/ORGANISM-STATE.json
OCTOPUS/CURRENT-TRUTH.md
_ops/state/doctor/self-knowledge-latest.json
_ops/owner_console/status.py
_ops/owner_console/collab_model_adapter.py   # _self_context
_ops/cortex/self_model.py
_ops/doctor/self_knowledge.py
_ops/cortex/improve.py                       # gather_signals

# حافظه
_ops/memory/gate.py
_ops/memory/memory_store.py
_ops/memory/retrieval_router.py
_ops/memory/research_ingest.py
_ops/memory/self_loop_ingest.py
_ops/memory/vault_bridge.py                  # OFF — دست نزن مگر owner
_ops/owner_console/collab_memory.py
_ops/telegram_center/ask_vault.py

# مغزها / سیم
_ops/cortex/model_router.py
_ops/cortex/business_brain.py
_ops/organism.py
_ops/wiring.py                               # WORKLOCK — حداقل لمس
_ops/OCTOPUS-flags.cmd

# وب‌اپ پرسش
_ops/telegram_center/miniapp_gateway.py      # /api/ask /api/collab /api/selfmap
_ops/telegram_center/miniapp/app.js          # renderAsk · Sources · chips
_ops/telegram_center/miniapp/index.html
_ops/telegram_center/ask_brain.py
_ops/owner_console/collaborator.py
_ops/owner_console/conversation.py
_ops/panel/server.py                         # :8790 — NOT Ask chat

# قرارداد / نردبان
06 - Architecture Maps/OCTOPUS-COLLABORATOR-INTERACTION-CONTRACT.md
_ops/INTERACTION-CONTRACT.md
_ops/EVIDENCE-LADDER.md
_ops/DISCOVERY-PROTOCOL.md
_ops/CAPABILITY-JOURNAL.md
07 - Knowledge/Architecture/OCTOPUS-MEMORY-TRUTH-MAP.md
07 - Knowledge/Architecture/OCTOPUS-HEARTS-BRAINS-4D-STATUS.md
```

---

## 2. شکاف محصولی که باید ببندی (P0)

> مالک اثرات را از وب می‌خواهد. امروز حلقه‌های حافظه/خودآگاهی **روی دیسک زنده‌اند**،
> ولی مسیر پرسش اغلب آن‌ها را **در پاسخ نشان نمی‌دهد**.

| ID | شکاف | اثر برای مالک | جهت فیکس (additive) |
|----|------|----------------|---------------------|
| G1 | Ask/`ask_brain` MemoryGate را صدا نمی‌زند | سؤال دربارهٔ improve/self → جواب بدون cite trail | recall اختیاری → `data.facts` / Sources |
| G2 | `_self_context` فقط روی model collab | stub/intent گاهی بدون beat/pain/truth | غنی‌سازی deterministic intents + model |
| G3 | ask_vault ممکن است flag-off باشد | chip Ask خالی/escalates بی‌شفاف | verify flag؛ UI صادق «vault خاموش» |
| G4 | selfmap هست ولی به chat وصل نیست | آگاهی در تب سیستم، نه در پرسش | لینک/cite از selfmap metrics در پاسخ خودشناسی |
| G5 | ingest رشد می‌کند ولی Ask round-trip ندارد | مالک نمی‌فهمد یادگیری «رسیده» | AC ingest→cite در یک نوبت collab |
| G6 | doc drift (HEARTS هنوز APPLY=0 در §۲) | ایجنت بعدی گیج می‌شود | یک پچ اسنادی کوچک هم‌راستا با ADR-035 |

**خارج از scope این مأموریت:** money-live · EXTERNAL_SEND · Lead outbound · revive 4d · arm vault_auto_write · promote brain_core.

---

## 3. معماری هدف (کوچک، قابل‌دیدن)

```text
MiniApp تب «پرسش»
  ├─ 🤝 همکار (DEFAULT)  POST /api/collab
  │     conversation intents (intro/blockers/runtime/self-aware)
  │       + collab_model_adapter._self_context  ← غنی‌شده با:
  │            ORGANISM-STATE snippet · CURRENT-TRUTH · blockers
  │            + MemoryGate.recall_recent / self_loop (cite-only)
  │       → reply.v1 {text, kind, model_source, data.facts[], external_effect:false}
  │       → UI Sources panel
  │
  ├─ 💬 Ask  POST /api/ask
  │     ask_vault (اگر flag=1 و hit) → source=vault + منابع
  │     else ask_brain (timeout کوتاه) → در صورت امکان + memory cite
  │     else collab-fallback
  │
  └─ پنل‌های موازی (read-only اثبات آگاهی)
        GET /api/selfmap · /api/ops/brain · /api/current-truth · /api/cognitive-scan
```

قانون طلایی UI: اگر حافظه/خودآگاهی مشورت شد → **Sources یا یک خط «شاهد:»**؛
اگر خالی بود → صادق بگو «recall خالی / vault خاموش» — هرگز hallucinate مسیر فایل نساز.

---

## 4. فازها (اجرا به ترتیب؛ هر فاز evidence دارد)

### فاز A — Baseline زنده (۳۰–۴۵ دقیقه، فقط خواندن + پروب)

1. PID/start: organism · cortex · center · miniapp-gateway · live
2. flags-loaded برای:
   `OCTOPUS_WIRE_COLLAB` · `OCTOPUS_COLLAB_USE_MODEL` · `OCTOPUS_WIRE_MEMORY_GATE` ·
   `OCTOPUS_WIRE_MEMORY_DECISION` · `OCTOPUS_TG_ASK_VAULT` · `OCTOPUS_WIRE_VAULT_RAG` ·
   `OCTOPUS_NEURAL_LEARNED_APPLY` · `OCTOPUS_WIRE_WEB_RESEARCH`
3. اندازه‌گیری trails:
   - خطوط `self-loop-ingest.jsonl` / `research-ingest.jsonl`
   - ageِ `self-knowledge-latest.json` · `ORGANISM-STATE` beat/pain
4. پروب HTTP (با auth معتبر مالک؛ بدون چاپ initData):
   - POST `/api/collab` «از چی تشکیل شدی؟»
   - POST `/api/collab` «موانع چیست؟»
   - POST `/api/ask` یک سؤال vault-local (مثلاً نام ADR/نوت موجود)
   - GET `/api/selfmap`
5. جدول Baseline: چه citeای برگشت؟ چه چیزی غایب بود؟

خروجی: `00-BASELINE.md` در پوشهٔ evidence.

### فاز B — پل خودآگاهی → پاسخ همکار (P0)

هدف: سؤال‌های خودشناسی **deterministic + model** هر دو شواهد زنده بدهند.

حداقل کار:
1. گسترش `_self_context` (یا helper مشترک) تا شامل:
   - beat / halted / coherence (از ORGANISM-STATE یا status)
   - ۱–۳ blocker از `status.blockers()`
   - یک snippet CURRENT-TRUTH (sanitize، کوتاه)
   - اشارهٔ صادق به دو مغز زنده (cortex + business_brain) و اینکه 4d وصل نیست
2. intents فارسی/انگلیسی: `خودآگاه|از چی تشکیل|موانع|runtime|هدف`
3. پاسخ `kind` ∈ {intro, blockers, runtime, chat} با `schema=owner-console.reply.v1`
4. تست واحد + یک پروب زنده

**ممنوع:** persona داستانی بدون شاهد · claim «۸ مغز» · claim authorize از memory.

### فاز C — پل حافظه → Sources در پرسش (P0)

هدف: وقتی MemoryGate ON است، پاسخ دربارهٔ improve/self/research حداقل یک cite واقعی داشته باشد.

حداقل کار:
1. Helper کوچک read-only: `recall_for_owner_ask(query, limit)` روی episodic graded
   (fail-soft اگر gate off/DB missing)
2. سیم به:
   - collab model path (`data.facts`)
   - در صورت امکان ask_brain یا collab-fallback Ask
3. UI: Sources panel از قبل در `app.js` هست — فیلدها را پر کن؛ UI جدید نساز مگر لازم
4. trust را OWNER_CONFIRMED جعل نکن

تست: ingest یک marker تستی یا استفاده از trail موجود → collab cite می‌کند یا صادق می‌گوید خالی.

### فاز D — Ask vault شفاف + بدون hang (P0/P1)

1. Verify `OCTOPUS_TG_ASK_VAULT`؛ اگر خاموش است:
   - یا با verdict مالک روشن کن + restart، **یا**
   - UI/meta صادق: «vault غیرفعال → brain/collab»
2. Chip Ask: timeout کلاینت ≥45s · سرور کوتاه · fallback hang نکند
3. وقتی vault hit: `source=vault` · `sources.length≥1` · خط «منابع:» · footer «منبع: vault (N نوت)»
4. Regression: unauth → 403 روی `/api/ask` و `/api/collab`

### فاز E — Selfmap ↔ پرسش (P1، کوچک)

1. یک intent «نقشهٔ خودت / selfmap» که اعداد غیر-unknown از `/api/selfmap` (یا همان backend)
   را در متن خلاصه کند + بگوید جزئیات در تب سیستم
2. اطمینان GET `/api/selfmap` memory metrics غیر-unknown دارد (اگر unknown = فیکس داده، نه فقط UI)

### فاز F — Round-trip یادگیری قابل‌دیدن (P1)

1. یک `improve.run(write=True)` یا pulse self_knowledge (امن، بدون outbound)
2. رشد `self-loop-ingest.jsonl` را ثبت کن
3. یک نوبت collab دربارهٔ همان موضوع → cite یا «consulted/deduped»
4. گزارش قبل/بعد برای مالک

### فاز G — Verify وب‌اپ برای مالک (اجباری قبل از بستن)

چک‌لیست دستی که مالک اجرا می‌کند (تو هم پروب می‌کنی):

| # | عمل در مینی‌اپ (بعد از بستن/باز کردن) | انتظار قابل‌دیدن |
|---|----------------------------------------|------------------|
| 1 | تب پرسش · chip همکار · «از چی تشکیل شدی؟» | متن ساختاری + اشاره به cortex/business یا runtime evidence · نه قصه |
| 2 | «موانع چیست؟» | blockers واقعی یا «موانع ثبت‌نشده» صادق |
| 3 | «آخرین خودبهبودی / improve چی بود؟» | Sources یا شاهد trail/self-loop اگر موجود |
| 4 | chip Ask · سؤال از یک نوت vault شناخته‌شده | اگر vault ON: منبع vault؛ وگرنه پیام صادق escalation |
| 5 | تب/کارت selfmap یا System | memory/brain اعداد زنده |
| 6 | footer موفق همکار | `secondary:deepseek-…` یا timeout صادق — نه `local:qwen*` |
| 7 | بدون login/initData | 403 |

خروجی: `07-OWNER-VISIBLE-VERIFY.md` + اسکرین/لاگ بدون secret.

### فاز H — Docs + HANDOFF (کوچک)

1. پچ اسنادی HEARTS §۲ neural APPLY اگر هنوز stale است
2. ۲–۵ خط در MEMORY-TRUTH-MAP: «Ask/collab اکنون recall می‌کند / نمی‌کند» (حقیقت بعد از کار تو)
3. HANDOFF wikilink به evidence + این مگاپرامپت
4. Commit فقط اگر مالک بگوید

---

## 5. Acceptance Criteria (DoD — همه باید سبز)

- [ ] **AC-Ask-SelfAware:** همکار به «از چی تشکیل شدی؟» / «موانع چیست؟» جواب ساختاری با شاهد زنده می‌دهد؛ `external_effect=false`
- [ ] **AC-Ask-MemoryCite:** با MemoryGate ON، حداقل یک پرسش self-loop/research → Sources یا `data.facts` با مسیر/hash واقعی
- [ ] **AC-Ask-VaultTruth:** رفتار vault ON/OFF برای مالک شفاف است؛ وقتی ON و hit → `source=vault`
- [ ] **AC-Collab-NoHang:** `/api/collab` ≤60s با متن یا `kind=timeout`/`model-fallback-stub`
- [ ] **AC-Auth-FailClosed:** unauth POST ask/collab → 403؛ draft همچنان بدون send
- [ ] **AC-Selfmap-Visible:** `/api/selfmap` metrics memory غیر-unknown (یا علت صادق documented)
- [ ] **AC-Ingest-RoundTrip:** رشد trail → cite در یک نوبت پرسش (یا پیام consulted/empty صادق)
- [ ] **AC-NoAuthorityCreep:** memory `may_authorize=false` · talk EXTERNAL_SEND همچنان blocked · Golden Trace parity
- [ ] Suites لمس‌شده سبز + لیست تست‌های نو برای ثبت در `run_all` گزارش شده
- [ ] Evidence pack کامل در مسیر بالا
- [ ] جملهٔ صریح برای مالک: «مینی‌اپ را ببند و باز کن؛ بعد جدول G را بزن»

---

## 6. تست‌ها (حداقل)

موجود را نشکن؛ نوها را با نام یکتا بساز:

```
_ops/tests/test_awareness_ask_bridge.py      # self_context + facts cite
_ops/tests/test_memory_ask_recall.py         # recall_for_owner_ask fail-soft
_ops/owner_console/tests/test_conversation.py  # intents خودآگاهی
_ops/tests/test_miniapp_gateway.py           # regression ask/collab/auth
_ops/tests/test_tg_ask_vault.py              # vault ladder
```

پروب زنده (نه فقط unit): اسکریپت یا curl داخلی که schema و sources را assert کند — بدون secret در خروجی.

---

## 7. Rollback

| تغییر | برگشت |
|-------|--------|
| flag تازه | `=0` در flags.cmd + restart gateway/organism |
| helper recall | import fail-soft؛ حذف سیم از adapter |
| UI Sources | اگر فیلد خالی باشد UI قبلی بی‌شکست می‌ماند |
| ask_vault arm | flag off → escalation قبلی |

هیچ migrate مخرب DB · هیچ wipe گستردهٔ memory.db بدون حکم مالک.

---

## 8. گزارش نهایی (قالب اجباری)

```markdown
# AWARENESS-MEMORY-ASK — FINAL

## Baseline → After (جدول پرچم‌ها و trail sizes)
## چه پیاده شد (فایل → رفتار قابل‌دیدن در مینی‌اپ)
## چه پیاده نشد و چرا (با شاهد)
## AC checklist (pass/fail + شاهد)
## دستور مالک برای دیدن اثر
1. مینی‌اپ را کامل ببند
2. دوباره باز کن
3. پرسش → همکار → … (۳ سؤال پیشنهادی فارسی)
4. Ask → یک سؤال vault
5. System/selfmap را نگاه کن
## PIDها بعد از restart
## درخواست ثبت تست در run_all (نام فایل‌ها)
```

---

## 9. یک‌خطیِ موفقیت برای مالک

> بعد از بستن/باز کردن مینی‌اپ، در تب پرسش از اختاپوس می‌پرسم «از چی تشکیل شدی؟»
> و «آخرین improve چی بود؟» — جواب با شاهد زنده (runtime/memory) می‌آید،
> Sources یا خط شاهد دیده می‌شود، و هیچ اثر بیرونی زده نمی‌شود.

اگر این یک‌خطی برقرار نشد، مأموریت تمام نیست — حتی اگر تست واحد سبز باشد.

---

## 10. ترتیب خواندن ایجنت (کم‌هزینه → عمیق)

1. همین مگاپرامپت
2. `01 - Dashboard/HANDOFF.md` (وضع لحظه‌ای MiniApp/collab)
3. `07 - Knowledge/Architecture/OCTOPUS-MEMORY-TRUTH-MAP.md`
4. `07 - Knowledge/Architecture/OCTOPUS-HEARTS-BRAINS-4D-STATUS.md`
5. `_ops/INTERACTION-CONTRACT.md` → canonical interaction contract
6. `_ops/owner_console/collab_model_adapter.py` · `miniapp_gateway.py` · `miniapp/app.js`
7. فقط بعد: کد memory/* و cortex/improve.py

شروع کن از **فاز A**. بدون baseline، کد ننویس.
