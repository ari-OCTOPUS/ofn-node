# 02-ACCEPTANCE — ۱۰ گفت‌وگوی end-to-end (2026-08-12)

## نتیجه: ۱۰/۱۰ PASS

| # | سؤال | kind | run_id | ext |
|---|------|------|--------|-----|
| ۱ | اختاپوس، درباره من چی می‌دونی؟ | **memory** | run_8f27f288d514 | False ✅ |
| ۲ | نقشهٔ کامل خودت رو ساده توضیح بده. | **selfmap** | run_79193a462f76 | False ✅ |
| ۳ | Cortex و Business Brain چه فرقی دارند؟ | **architecture** | run_9566d130ab84 | False ✅ |
| ۴ | معادله BCM چه کاری می‌کند و الان چقدر اختیار دارد؟ | **equation** | run_f2bbb22e8a8d | False ✅ |
| ۵ | سیگما الان diagnostic است یا روی تصمیم اثر دارد؟ شاهدت چیست؟ | **evidence** | run_5c0a8c6f089c | False ✅ |
| ۶ | قلب سوم به کدام فایل و کدام caller وصل است؟ | **architecture** | run_e550cce26be3 | False ✅ |
| ۷ | آخرین shadow decision چه بود؟ | **memory** | run_c864fafccb4d | False ✅ |
| ۸ | چرا این improve را پیشنهاد دادی؟ | **memory** | run_4797aa0336d9 | False ✅ |
| ۹ | این تصمیم من را یادت بماند. | **memory-proposal** | run_1dfce23bdaf6 | False ✅ |
| ۱۰ | الان چه چیزی را نمی‌دانی یا به آن وصل نیستی؟ | **limitations** | run_b04eca21832c | False ✅ |

## checks

- all `external_effect` = False: **True** ✅
- all have `run_id`: **True** ✅
- kinds: memory · selfmap · architecture · equation · evidence · memory-proposal · limitations
- هیچ clarify نیامد ✅
- may_authorize همیشه False ✅

## TDR decisions

| فناوری | مشکل | تصمیم | دلیل |
|--------|------|-------|------|
| SSE | model path 20-40s blocking | **TRIAL** | TTFT بهبود برای model path |
| WebSocket | دوطرفه لازم نیست (هنوز) | **DEFER** | SSE برای streaming کافی |
| FastAPI | ThreadingHTTPServer کار می‌کند | **DEFER** | p50=0.6ms deterministic |
| NATS | single process کافی | **DEFER** | event volume داخلی |
| Temporal | DBOS/journal موجود | **DEFER/REJECT** | duplication |
| Qdrant | Chroma نصب ولی arm نشده | **DEFER** | بدون benchmark |
| GraphRAG | conflict/provenance اول | **DEFER** | دادهٔ آلوده |
| tiktoken | context overflow | **ADOPT** ✅ | نصب است، budget کار می‌کند |
| OpenTelemetry | trace داخلی کافی | **DEFER** | event log موجود |

## run durability

`PROCESS_DURABLE` — فایل روی دیسک (JSONL)، ولی no cross-process guarantee.
pause/resume ادعا نمی‌شود (طبق runbook).

## event overhead

p50 deterministic: **0.6ms** (بدون event overhead قابل تشخیص)
event chain کامل: ۶ event در <۲ms.

## Truth Layer

BCM evidence → **VERIFIED** (bcm.py وجود دارد) ✅
σ evidence → **VERIFIED** (spectral.py وجود دارد) ✅

## باقی‌مانده (صادق)

- SSE streaming واقعی برای model path (DeepSeek stream:true) — TRIAL هنوز اجرا نشده
- session memory backend کامل‌تر (الان فقط preview کوتاه)
- CR-B1 کوراموتو runtime وصل نیست
- v2 σ فقط shadow
