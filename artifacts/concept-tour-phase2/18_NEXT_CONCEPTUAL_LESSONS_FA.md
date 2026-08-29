# درس‌های مفهومی بعدی

این roadmap اجرا یا مجوز تغییر نیست؛ همهٔ گام‌های writer/runtime نیازمند تصمیم تازهٔ مالک‌اند.

## درس ۱ — حقیقت، projection و cache

هدف: با یک event نمونه، تفاوت `events`، `outbox`، `episodes`، Vault، ask cache و KV cache را رسم و failure هرکدام را توضیح دهید.  
معیار یادگیری: هیچ cache به‌عنوان source of truth نامیده نشود.  
شواهد محلی: [03_EVENT_AND_MEMORY_TOUR_FA.md](03_EVENT_AND_MEMORY_TOUR_FA.md).

## درس ۲ — crash consistency

هدف: به‌صورت صرفاً مفهومی نقاط crash «قبل commit»، «بعد commit/قبل queue»، «هنگام handler» و «بعد effect/قبل done» را تحلیل کنید.  
معیار: at-least-once/replay و duplicate external effect جدا شوند.  
نیاز آینده: test sandbox و owner approval؛ روی DB زنده اجرا نشود.

## درس ۳ — identity anchor

هدف: internal chain را از public attestation، signature و external checkpoint جدا کنید.  
معیار: tail truncation limitation توضیح داده شود.  
شواهد: [04_IDENTITY_AND_CONTINUITY_FA.md](04_IDENTITY_AND_CONTINUITY_FA.md).

## درس ۴ — pure read API

هدف: routeها را به pure read، local write، DB write، inference و network side effect دسته‌بندی کنید.  
معیار: GET به‌طور خودکار safe فرض نشود.  
نیاز آینده: ADR و compatibility plan با تأیید مالک.

## درس ۵ — mandatory retrieval contract

هدف: specification برای `memory_reads_per_cycle`، receipt، failure mode و metric بنویسید.  
معیار: recall wired با enforcement یکی فرض نشود.  
نیاز آینده: unit/integration test و migration احتمالی.

## درس ۶ — v1/v2 bridge

هدف: mapping idempotent، hash preservation، time semantics، causal parent و identity anchor را طراحی کنید.  
معیار: chain v1 و v2 merge صوری نشوند.  
شواهد: [07_OFN_L4_FUTURE_FA.md](07_OFN_L4_FUTURE_FA.md).

## درس ۷ — Active Inference کوچک

هدف: یک POMDP کاملاً آفلاین با stateهای کم برای thermal/memory bins روی کاغذ تعریف کنید: شکل و normalization `A,B,C,D,E`، belief update، risk، ambiguity و information gain.  
معیار: هیچ act مستقیم؛ خروجی فقط proposal برای arbiter.  
blocker اجرا: `pymdp` present نیست و این mission installation را ممنوع کرده است.

## درس ۸ — WBE بدون سوءاستفاده

هدف: exponent کل و specific rate را برای 0.75/0.81/0.85 تبدیل و تفاوت asymptotic/finite window را توضیح دهید.  
معیار: هیچ exponent به timer یا safety threshold وصل نشود.  
شواهد: [08_WBE_CONCEPT_FA.md](08_WBE_CONCEPT_FA.md).

## درس ۹ — APC و block-size

هدف: stable prefix، full-block reuse، salt isolation، tail waste، cold/warm و Pareto را روی دادهٔ synthetic تحلیل کنید.  
معیار: sha256 artifact با GPU benchmark اشتباه نشود؛ winner همچنان none.  
شواهد: [10_VLLM_PREFIX_CACHE_FA.md](10_VLLM_PREFIX_CACHE_FA.md) و [11_VLLM_BLOCK_SIZE_FA.md](11_VLLM_BLOCK_SIZE_FA.md).

## درس ۱۰ — Hybrid/Mamba

هدف: full/sliding/local/Mamba groupها و page-size/padding را برای یک architecture فرضی توضیح دهید، ولی مقدار واقعی حدس نزنید.  
معیار: unresolved fields `UNKNOWN` بمانند.  
شواهد: [12_HYBRID_MAMBA_CACHE_FA.md](12_HYBRID_MAMBA_CACHE_FA.md).

## roadmap عملی فقط پس از owner approval

1. backup قابل restore و manifest Git/source/unit.
2. disk retention و permission threat model.
3. source/runtime reconciliation و schema migration plan.
4. pure-read endpoint split.
5. mandatory retrieval instrumentation.
6. L4 bridge + tests + shadow mode.
7. optional tiny Active Inference sandbox.
8. GPU-host preflight، W4 histogram، metric completeness.
9. owner-approved canary.
10. deployment فقط با winner empirical، rollback و تأیید جدا.

## چیزی که همین حالا ممکن است

تمام درس‌های مفهومی ۱ تا ۱۰ را می‌توان با فایل‌های محلی و بدون GPU/vLLM اجرا مطالعه کرد. فقط مراحل empirical GPU، external anchor واقعی، backup destination و WAN teacher execution به زیرساخت بیرونی نیاز دارند.

ریسک/approval هر مرحله در [15_RISKS_AND_GAPS_FA.md](15_RISKS_AND_GAPS_FA.md) آمده است.

پاورقی مأموریت: [00_OWNER_ANSWER_FA.md#پاورقی-ماموریت](00_OWNER_ANSWER_FA.md#پاورقی-ماموریت).
