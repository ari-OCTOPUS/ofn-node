# 08-FINAL — Cognitive Runtime v1 (2026-08-12)

## چه چیزی reuse شد

| جزء | فایل | نقش در cognitive runtime |
|-----|------|--------------------------|
| event_log | `evidence_plane/event_log.py` | الگوی append-only JSONL + redaction |
| talk_gate | `policy/talk_gate.py` | convention run_id (uuid4 hex) |
| collaborator | `owner_console/collaborator.py` | روتر مکالمه + instrumentation نقطه |
| conversation | `owner_console/conversation.py` | intent router |
| collab_model_adapter | `owner_console/collab_model_adapter.py` | _self_context + model call |
| owner_recall | `memory/owner_recall.py` | cite-only حافظه |
| equation_advice | `memory/equation_advice.py` | advice-only معادلات |
| session_memory | `memory/session_memory.py` | session موقت |
| miniapp_gateway | `telegram_center/miniapp_gateway.py` | HTTP gateway + auth |

## چه چیزی جدید ساخته شد

| فایل | نقش |
|------|------|
| `_ops/cognitive/event_stream.py` | Typed Event Stream + Run lifecycle |
| `_ops/cognitive/run_store.py` | Append-only JSONL Run Store |
| `_ops/cognitive/context_engine.py` | tiktoken Budget Management (۶ بخش) |
| `_ops/cognitive/memory_formation.py` | Memory Candidate Pipeline |
| `_ops/cognitive/truth_layer.py` | Claim Verification (VERIFIED/REPORTED/UNVERIFIED) |
| `_ops/tests/test_cognitive_events.py` | 10 تست |

## چه فایل‌هایی تغییر کردند (این موج)

`collaborator.py` · `collab_model_adapter.py` · `conversation.py` · `miniapp_gateway.py` ·
`miniapp/app.js` · `equation_explainer.py` + 6 فایل نو.

**فایل‌های قفل‌شده:** صفر تغییر (flags.cmd + ledger CLEAN).

## چه تست‌هایی اجرا شدند

26 suite + 163 pytest = **صفر شکست**.
10-conversation acceptance = **10/10 PASS**.

## چه چیزهایی هنوز وصل نیستند (صادق)

- SSE streaming واقعی برای model path (DeepSeek `stream:true` → MODEL_TOKEN events) — TRIAL تأیید شد ولی هنوز پیاده نشده
- event types کامل (MODEL_TOKEN, TOOL_REQUESTED, PROPOSAL_CREATED و...) — انواع تعریف‌شده ولی هنوز emit نمی‌شوند
- pause/resume/cancel — نیازمند WebSocket (DEFER)
- session memory backend کامل‌تر (الان فقط preview)
- CR-B1 کوراموتو runtime وصل نیست
- v2 σ فقط shadow

## کدام اثرها فقط proposal هستند

همه. `applied=false` در هر event و claim. هیچ اثری از Chat/Memory/Equation اجرا نمی‌شود.
PolicyGate مرجع نهایی.

## conflictهای زنده

هیچ. C1 (TESTED/SHADOW) حل شد. C2 (ADR-036) حل شد.

## rollback دقیق

| تغییر | برگشت |
|-------|--------|
| event_stream instrumentation در collaborator | حذف بلوک `_run_info` |
| SSE endpoint در gateway | حذف `/api/runs/` handler |
| Context Engine در adapter | حذف بلوک `context_info` در `complete()` |
| memory_formation در conversation | حذف `_MEMORY_ASK` handler (پیش از intro) |
| truth_layer در explainer | حذف بلوک `try: import truth_layer` |
| ماژول‌های cognitive | حذف `_ops/cognitive/` — هیچ مصرف‌کنندهٔ قفل‌شده‌ای وابسته نیست |
| app.js SSE | حذف `if(data.run_id)` بلوک در buildSourcesPanel |
| UI regex تغییرات | بازگشت به الگوهای قبلی |

## run durability واقعی

`PROCESS_DURABLE` — فایل روی دیسک (JSONL در `state/cognitive/runs/`).
pause/resume/cross-process ادعا نمی‌شود.

## کدام فناوری‌ها REJECT/DEFER/TRIAL/ADOPT شدند

| فناوری | تصمیم | شاهد |
|--------|-------|------|
| SSE | **TRIAL** ✅ | endpoint کار می‌کند؛ TTFT برای model path بهبود |
| tiktoken | **ADOPT** ✅ | نصب است؛ context budget کار می‌کند |
| WebSocket | DEFER | دوطرفه لازم نیست |
| FastAPI | DEFER | ThreadingHTTPServer p50=0.6ms |
| NATS | DEFER | single process کافی |
| Temporal | REJECT | duplication با DBOS/journal |
| Qdrant | DEFER | Chroma arm نشده |
| GraphRAG | DEFER | provenance اول |
| OpenTelemetry | DEFER | event log موجود |
| MCP | DEFER | Tool Registry موجود |

## event overhead و TTFT

- p50 deterministic: **0.6ms** (بدون event overhead قابل تشخیص)
- event chain کامل (۶ event): **<۲ms**
- model path TTFT: هنوز blocking (SSE streaming برای موج بعد)

## جملهٔ نهایی

> اختاپوس اکنون برای هر مکالمه یک `run_id` دارد، مراحل مهم را به‌صورت event تایپ‌دار ثبت می‌کند،
> Context Engine با tiktoken budget مدیریت می‌کند چه چیزی مدل ببیند، Memory Formation جلوی آلودگی
> حافظه را می‌گیرد، و Truth Layer هر ادعا را به شاهد خارجی متصل می‌کند.
> هیچ‌کدام authority تولید نمی‌کنند؛ PolicyGate مرجع نهایی است.
