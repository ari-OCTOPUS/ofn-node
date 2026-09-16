---
type: research
project: "[[04 - Architect System/architect/PROJECT]]"
status: archived
tags: [doctor, learning]
created: 2026-07-18
updated: 2026-08-08
---

> **⚠️ سندِ تاریخی (۲۰۲۶-۰۷-۱۷/۱۸).** این گزارشِ پروبِ آن تاریخ است و
> بازتابِ وضعیتِ **پیش از** برش‌های ۰-۳ ِ طرحِ هیدرید کنترل‌پلین. سؤالاتِ بازِ این
> سند (مثل «Source of Truth کدام است؟») در `02-OCTOPUS-KNOWLEDGE-SNAPSHOT.md` پاسخ
> داده شده‌اند. برایِ شناختِ به‌روز `00-README-START-HERE.md` و `04-NEXT-AGENT-MEGAPROMPT.md`
> را بخوان. این دادهٔ پروب برایِ پشت‌زمینه نگه داشته شده، نه برایِ عمل.

# ⚡ بهینه‌سازیِ یادگیریِ دکتر — ایده‌ها از رقبا/SOTA

> **تاریخ:** 2026-07-18 | **هدف:** حلقهٔ خودشناسیِ دکتر (`_ops/doctor/self_knowledge.py`)
> را سریع‌تر و ارزان‌تر کنیم، بر اساسِ آنچه شرکت‌ها/مقالاتِ پیشرو واقعاً می‌کنند.
> **روش:** تحقیقِ موازیِ سه‌زاویه‌ای (self-reflection · agentic-memory · adaptive-compute).

## مشکل (پیش از بهینه‌سازی)

حلقه هر ~۳۰ دقیقه، **بی‌قیدوشرط** ۲ کالِ کاملِ LLM (Ollama 7B روی 1660Ti، هرکدام
~۱۵-۳۰s) می‌زد — حتی وقتی هیچ‌چیزِ اختاپوس عوض نشده بود. کلِ snapshot را هر بار دوباره
می‌خواند و از صفر سنتز می‌کرد. بزرگ‌ترین اتلاف: **کالِ LLM روی وضعیتِ بی‌تغییر**.

## نقشهٔ ایده‌ها (منبع → مکانیزم → کاربرد در دکتر)

| ایده | منبع (شرکت/مقاله) | چطور ارزان/سریع | effort | وضعیت |
|---|---|---|---|---|
| **change-gate با hashِ محتوا** | CDC (Databricks) · GPTCache (exact cache) · **Generative Agents** (reflect ۲-۳×/روز نه هر tick) | تصویرِ بی‌تغییر → صفر forward pass | S | ✅ **شیپ شد** |
| **hop-2 تطبیقی (confidence-gated)** | **Self-Refine** (stopping criterion) · adaptive test-time compute · early-exit LLMs | چرخهٔ پایدار → یک کال به‌جای دو | S | ✅ **شیپ شد** |
| no-op version suppression | Idempotent CDC (Databricks) | history روی بی‌تغییر رشد نمی‌کند | S | ✅ (جزوِ change-gate) |
| cascade مدل (1.5B→7B→paid) | **FrugalGPT** (~۹۸٪ صرفه) · RouteLLM · خودِ `model_router`/`route_scorer` | pass روزمره روی مدلِ کوچک | M | ⏳ بعدی (اکثراً wiring) |
| delta-prompting (diff نه fullِ snapshot) | **Reflexion** (بازخوردِ فشرده نه replayِ کامل) | ورودی نصف → روی 1660Ti که prompt-eval-bound است، latency نصف | M | ⏳ |
| retrieval محدودِ hop-2 | **Mem0** (~۹۰٪ کاهشِ توکن) · Generative-Agents relevance | فقط اسلایس‌های مرتبط با focus | M | ⏳ |
| کتابخانهٔ درس‌های تأییدشده (retrieve نه re-derive) | **Voyager** (skill library، top-5 retrieval) | پاتولوژیِ تکراری = lookup نه generation | L | ⏳ (کاتالوگِ خطاهای شناخته‌مان دقیقاً همین است) |
| tiered memory (core=فهم، archival=فایل‌های خام) | **MemGPT/Letta** · Mem0 consolidation | هرگز fullِ state در هر prompt | L | ⏳ |
| دو-سرعته (vitalsِ ارزان هر tick، RCA فقط روی anomaly) | **Datadog Watchdog** (baseline→alert→analyze) | تحلیلِ گران فقط وقتِ ناهنجاری | M | ⏳ (`doctor.mine()` همین vitals را دارد) |

## آنچه شیپ شد (commit `b81ecdf`)

هر tick حالا:
- **بی‌تغییر → ۰ کالِ LLM** (فقط یک مقایسهٔ hash، میکروثانیه). `source=cached:no-change`،
  `stable_cycles++`، نه version بالا می‌رود نه به history اضافه می‌شود.
- **تغییر + focusِ پایدار + مطمئن → ۱ کال** (فقط hop-1).
- **تغییر + focusِ نو / کم‌اطمینان / پاتولوژیِ بحرانی → ۲ کال** (hop-1 + deep-dive).

`_hash_digest` فقط زیرمجموعهٔ **معنادار** را hash می‌کند (لِگ‌ها/سیم‌کشی/ترس/پول/نقاط‌مرده/
*نوعِ* خطاها/RFC) و کلاکِ خام (beat/ts) و شمارشِ نوسانی را حذف می‌کند. در ارگانیسمِ کند،
بیشترِ پنجره‌های ۳۰دقیقه‌ای بی‌تغییرند → **اکثریتِ کال‌ها حذف می‌شوند** بدونِ کم‌شدنِ عمق.

مشاهده‌پذیری: `rec` حالا `snapshot_hash/stable_cycles/llm_calls/deep_dive_ran` دارد.

## قدمِ بعدیِ پیشنهادی (به‌ترتیبِ ROI)

۱. **cascade مدل** (M، اکثراً wiring): hop-1 را از `qwen2.5:1.5b` رد کن، به 7B/paid فقط
   روی سختِ نو escalate کن — با سیاستِ خودت («$0 محلی روزمره، Fugu = cortisol») یکی است.
۲. **delta-prompting** (M): در تغییر، فقط diff + فهمِ قبلی را بده، نه هر ۱۰ فایل.
۳. **کتابخانهٔ درس‌های تأییدشده** (L): پاتولوژیِ تکراری (SLA-artifact pacemaker، nociceptorِ
   گرسنه، PriceNotLocked) را به‌جای re-derive، از یک storeِ embedding-indexed retrieve کن.

*مبنا: workflow تحقیقِ سه‌ایجنتی 2026-07-18؛ خروجیِ کامل در taskِ همان جلسه.
همه‌چیز در همان پاکتِ ایمن: $0 محلی، فقط‌خواندنی، threadِ daemon، مستقل از ترس.*
