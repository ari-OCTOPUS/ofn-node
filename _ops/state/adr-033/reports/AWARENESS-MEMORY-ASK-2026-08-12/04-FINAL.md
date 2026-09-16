# 04-FINAL — اتصال Chat Box به مغز، حافظه، معادلات و معماری (2026-08-12)

> فازهای O→U. Improve don't rewrite · Existing organs first · Truth over appearance.
> مگاپرامپت مالک اجرا شد — همهٔ شواهد از فایل/runtime، نه چت.

---

## Reuse شد (بدون بازنویسی)

| جزء | فایل | نقش |
|-----|------|------|
| gateway | `miniapp_gateway.py` | ورودی واحد، auth، redact دولایه، timeouts |
| collaborator | `collaborator.py` | روتر/assembler مکالمه (تقویت‌شده) |
| conversation | `conversation.py` | intents (تقویت‌شده) |
| owner_recall | `memory/owner_recall.py` | cite-only حافظه |
| equation_advice | `memory/equation_advice.py` | advice-only معادلات |
| collab_memory | `collab_memory.py` | episodic digest |
| collab_model_adapter | `collab_model_adapter.py` | _self_context + مدل (تقویت‌شده) |
| shadow/limited | J→N موجود | بدون تغییر در این موج |

## جدید ساخته شد (additive)

| فایل | فاز | رفتار |
|------|-----|--------|
| `memory/unified_context.py` | P | assembler واحد (self_context/shadow/effects/architecture/facts) |
| `memory/equation_explainer.py` | Q | ۱۳ معادله، ۵ سطح، status واقعی، شاهد |
| `memory/architecture_explainer.py` | Q | ۱۱ جزء با path/caller/gates |
| `memory/session_memory.py` | S | session موقت + memory proposal |
| `tests/test_chatbox_unified.py` | U | ۱۳ تست |
| `app.js` (گسترش) | R | پنل شاهد/معادلات/سایه/اثر + vault paths |
| گزارش‌ها 00-04 | O-U | evidence pack |

## فایل‌های تغییرکرده (این موج)

`conversation.py` · `collaborator.py` · `collab_model_adapter.py` · `app.js` ·
`memory/unified_context.py` (جدید) · `memory/equation_explainer.py` (جدید) ·
`memory/architecture_explainer.py` (جدید) · `memory/session_memory.py` (جدید) ·
`tests/test_chatbox_unified.py` (جدید) · گزارش‌ها.

**فایل‌های قفل‌شده:** flags.cmd، registries، run_all.py، ADR-033-037، pulse_arbiter،
rhythm، ledger، policy_gate — **صفر تغییر در این موج** (تغییرات موجود از Math Atlas است).

## تست‌ها

| suite | نتیجه |
|-------|-------|
| test_chatbox_unified (نو) | **13/13** ✅ |
| awareness 6/6 · memory_recall 6/6 · gateway 49/49 · phase_jn 13/13 · verdicts 15/15 · rhythm · pulse_arbiter | ✅ همه |
| node --check app.js | ✅ |

## هنوز وصل نیست (صادق)

- **C2 (ADR-036): بسته شد** — مالک رأی داد؛ `ADR-036-math-control-spine.md` ساخته شد (ACCEPTED). ✅
- **M9 (localStorage): بسته شد** — askLog حالا در tab switch/باز کردن persist می‌شود (`octopus.asklog.v1`، آخرین ۲۴ نوبت، preview بدون secret). ✅
- C1 (chrono-rhythm TESTED/SHADOW): **حل شد** — validator ok (ادعا ≤ شواهد).
- ask_vault RAG بُعدی (OCTOPUS_WIRE_VAULT_RAG=1 هست ولی semantic write arm نشده).
- CR-B1 کوراموتو runtime وصل نیست (فقط pure helper).
- v2 σ (connectivity_ratio) فقط shadow.
- session memory backend فقط preview/text کوتاه (کامل‌تر = موج بعد، نیازمند رأی).

## اثرها — فقط proposal ✅

- Chat layer هیچ اجرایی ندارد — `applied=false` همیشه
- `ALLOWED_AS_PROPOSAL` ← PolicyGate مرجع
- effect request در چت → «پیشنهاد ساخته شد/رد شد»، هرگز «انجام شد»
- limited_effect رأی‌خوان (value=3) ولی اجرای واقعی فقط از PolicyGate

## Conflictهای زنده

| id | شرح | وضعیت |
|----|------|--------|
| C1 | TESTED/SHADOW | حل شد (validator ok) |
| C2 | ADR-036 missing | **بسته شد** — رأی مالک → ADR-036 ساخته شد ✅ |

## Rollback دقیق

| تغییر | برگشت |
|-------|--------|
| intents جدید در conversation.py | حذف بلوک‌های `_EQUATION/_ARCHITECTURE/_EVIDENCE/_BUSINESS/_EFFECT/_SESSION_MEM` |
| unified_context در collaborator | حذف بلوک `unified_context` |
| session_memory در adapter/collaborator | حذف بلوک‌های session |
| app.js پنل + localStorage | حذف `buildSourcesPanel` بخش‌های جدید + `octopus.asklog.v1` (UI قدیمی بی‌شکست می‌ماند) |
| ماژول‌های جدید | حذف ۴ فایل — هیچ مصرف‌کنندهٔ قفل‌شده‌ای به آن‌ها وابسته نیست |
| ADR-036 | حذف فایل (رأی ثبت‌شده در owner-verdicts باقی می‌ماند) |

## DoD مگاپرامت — وضعیت

| شرط | وضعیت |
|-----|--------|
| طبیعی حرف زدن | ✅ (10 intent جدید + 17 قدیمی) |
| حافظهٔ خودش با شاهد | ✅ owner_recall cite-only |
| تفاوت دو مغز | ✅ architecture_explainer |
| معماری ساده و فنی | ✅ دو حالت |
| سؤال دربارهٔ هر معادله | ✅ equation_explainer (۱۳) |
| وضعیت واقعی اثر معادلات | ✅ status واقعی + advice_only |
| آخرین shadow/proposal | ✅ unified_context.shadow/effects |
| منبع هر ادعا | ✅ facts + evidence panel |
| «یادت بماند» → proposal | ✅ session_memory.propose_remember |
| بدون authority/execution از Chat/Memory/Equation | ✅ may_authorize=false · applied=false |

## جملهٔ نهایی برای مالک

> مینی‌اپ را **ببند و باز کن**؛ در تب «پرسش» بپرس «از چی تشکیل شدی؟» — جواب با دو مغز و
> شاهد runtime می‌آید. بعد بپرس «معادله BCM چیه؟» — توضیح با status و شاهد فایل.
> پنل «شاهد / معادلات / وضعیت» زیر هر پاسخ همکار باز می‌شود. هیچ اثری اجرا نمی‌شود؛
> همه‌چیز advice/proposal با PolicyGate مرجع.
