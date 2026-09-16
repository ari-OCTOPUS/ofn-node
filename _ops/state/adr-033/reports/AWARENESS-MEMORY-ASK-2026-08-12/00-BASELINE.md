# 00-BASELINE — Awareness/Memory/Ask (2026-08-12, pre-implementation)

> فاز A: فقط خواندن + پروب ایستا. کد نوشته نشد.

## ۱. فرآیندهای زنده (۷ python.exe)

| proc | PID | flags-loaded snapshot | boot |
|------|-----|----------------------|------|
| miniapp-gateway | 26584 | `_ops/state/flags-loaded-miniapp-gateway.json` | 12:05 |
| organism | — | `flags-loaded-organism.json` (09:42) | — |
| cortex | — | `flags-loaded-cortex.json` (09:41) | — |
| center | — | `flags-loaded-center.json` (10:06) | — |
| live | — | `flags-loaded-live.json` (07:35) | — |

ORGNISM-STATE: beat=32648, halted=None (زنده، 14:17).

## ۲. فلگ‌های کلیدی (همه ON در gateway زنده)

| flag | flags.cmd | flags-loaded gateway |
|------|-----------|---------------------|
| OCTOPUS_WIRE_COLLAB | =1 (line 1363) | **1** |
| OCTOPUS_COLLAB_USE_MODEL | =1 (line 1387) | **1** |
| OCTOPUS_WIRE_MEMORY_GATE | =1 (line 358) | **1** |
| OCTOPUS_WIRE_MEMORY_DECISION | =1 (line 868) | **1** |
| OCTOPUS_TG_ASK_VAULT | =1 (line 862) | **1** |
| OCTOPUS_WIRE_VAULT_RAG | =1 (line 1205) | **1** |
| OCTOPUS_NEURAL_LEARNED_APPLY | =1 (line 1197) | **1** |
| OCTOPUS_WIRE_WEB_RESEARCH | =1 (line 89) | **1** |
| OCTOPUS_WIRE_NEURAL | =1 (line 1025) | **1** |

load_shortfall: 0 missing.

## ۳. Trails (روی دیسک زنده، در حال رشد)

| trail | lines | آخرین |
|-------|-------|-------|
| `state/memory/self-loop-ingest.jsonl` | **395** | 2026-08-12T04:13:53 |
| `state/memory/research-ingest.jsonl` | **29** | 2026-08-12T04:15:27 |
| `state/memory/memory-decision-ingest.jsonl` | **MISSING** | — |

State age: self-knowledge-latest 14:13 · ORGANISM-STATE 14:17 · arbiter-latest 14:19 (همه امروز، زنده).

## ۴. شکاف‌های تأییدشده (تحلیل ایستای مسیر کد)

### G1 — Ask/`ask_brain` MemoryGate را صدا نمی‌زند ✅ تأیید
مسیر `/api/ask` (miniapp_gateway.py:593-681):
```
ask_vault.query → ask_brain.ask → collab-fallback
```
هیچ‌کدام `MemoryStore.search` یا `collab_memory.recent` یا `MemoryGate` را صدا نمی‌زنند.
`ask_brain.py` صرفاً model_router + quota است — هیچ recall.

### G2 — `_self_context` فقط مدل-collab، بدون memory cite ✅ تأیید
`collab_model_adapter._self_context()` (line 113) شامل:
- ORGANISM-STATE snippet (beat/halted/pain)
- CURRENT-TRUTH (18 خط فیلترشده)
- status.blockers() + runtime_truth()
**نبود:** MemoryGate.recall · اشارهٔ صریح به دو مغز (cortex + business_brain) · note «4d وصل نیست».

### G3 — ask_vault flag ON ولی شفافیت UI ناشناخته
flag=1 تأیید شد. ولی وقتی hit ندهد، UI پیام صادق «vault خاموش» ندارد (flag روشن است ولی خالی).
نیاز: وقتی sources خالی → پیام صادق، نه فقط escalate بی‌صدا.

### G4 — selfmap هست ولی به chat وصل نیست ✅ تأیید
`/api/selfmap` در `READ_API_PATHS` (line 82) — read-only upstream.
هیچ intent در conversation/collab آن را cite نمی‌کند.

### G5 — ingest رشد می‌کند ولی Ask round-trip ندارد ✅ تأیید
trails در حال رشد‌اند ولی هیچ مسیری ingest→cite در یک نوبت Ask وجود ندارد.

### G6 — doc drift
HEARTS-BRAINS-4D-STATUS §۲ هنوز احتمالاً APPLY=0 (با reconciliation هم‌راستا نشده).

## ۵. ساختار پاسخ collab (برای فیلد `data.facts`)

`collaborator.handle()` خروجی `data` dict دارد با:
- `rationale` (stub/model)
- `tier`, `memory_turn_id`, `memory_kind`
- `policy_version`, `response_mode="draft"`, `evidence_plane`
- `external_effect=False`, `send_attempted=False`
**نبود:** `facts[]` یا `sources[]` با cite واقعی حافظه.

## ۶. API موجود برای پل C

- `MemoryStore.search(query, namespace, k, min_trust, ...)` — FTS5/LIKE retrieval
- `collab_memory.recent(limit, state_dir)` — read recent entries
- `MemoryGate.flag_on()` — gate check

## ۷. پروب HTTP

**نمی‌توانم پروب زنده انجام دهم** — initData/_token مالک secret است و من نباید آن را چاپ/استفاده کنم.
تحلیل ایستای مسیر کد جایگزین شد. پروب زنده فاز G (مالک) خواهد زد.

## ۸. جمع‌بندی baseline

- سیستم **زنده و سالم** است (beat 32648، ۷ فرآیند، trails در حال رشد).
- تمام فلگ‌های لازم **روشن‌اند**.
- شکاف اصلی (G1+G2): مسیر Ask/collab **هیچ recall حافظه‌ای** ندارد و `_self_context` **حافظه cite نمی‌کند**.
- این یعنی: حتی با 395 یادگیری روی دیسک، سؤال «آخرین improve چی بود؟» جواب بدون شاهد می‌دهد.

→ **فاز B-H اجرا می‌شود.**
