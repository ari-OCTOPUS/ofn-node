---
megaprompt_title: EQUIP موج C2 — گروه ۳ ادراک (Evidence-Grounded Perception)
version: "1.0"
sequence: 6
group: 3
wave: C
requires: "G1 evidence not FAIL"
next: "MEGAPROMPT-EQUIP-SCAN-INDEPENDENT-2026-08-16.md (Wave C)"
scan_after: true
written_by: "Cursor Grok 4.6 — 2026-08-16"
branch_name: "equip/g3-perception-20260816"
---

# پیست

۱) SHARED · ۲) همین فایل.

# ماموریت: Evidence-Grounded Perception Layer

sensorها، observatory adapters، browserها، API clients، document parsers،
GitHub connector و allowlistهای اینترنتی را کشف کن.

هدف: هیچ دادهٔ بیرونی مستقیماً به دستور قابل‌اجرا یا memory معتبر تبدیل نشود.

## حقیقت این vault

- `_ops/observatory/observation_v1.py` — پارس قطعی روی body از قبل fetchشده؛
  هیچ شبکه؛ USGS/HN؛ در غیر این صورت PARSE_DRIFT. **extend کن نه جایگزین.**
- ADR-041 internet observatory. آداپتور فاز ۳ historically ناقص بود؛
  تست‌های 2026-08-16 ممکن است sliceهایی اضافه کرده باشند — discovery.
- allowlist امضاشده را حفظ کن. SSRF در reader لگ‌ها قبلاً فیکس شده
  (`fc735f9`) — بازش نکن.
- GitHub/HF connectors اگر هستند: حداقل scope. HealthKit/Finance اگر در
  این گروه ظاهر شدند فقط envelope read-only — write مال گروه ۹ است.

## الزامات vertical slice

- envelope استاندارد Observation: source، fetched_at، content_type، hash،
  signature، trust_level، parser_version، raw_reference، extraction_confidence.
- content را از instruction جدا کن.
- redirect / DNS rebinding / SSRF / دانلود فایل ناشناس کنترل شود.
- timeout، size limit، MIME validation، content hash.
- parser output = untrusted data.
- citation chain از observation تا hypothesis.
- raw evidence بدون retention policy دائمی ذخیره نشود.

## سناریوی acceptance

یک منبع allowlisted و یک منبع غیرمجاز. مجاز → observation معتبر.
غیرمجاز → قبل از fetch مسدود + audit.

## اسکن تخصصی

SSRF · prompt injection in documents · malicious redirects ·
decompression bomb · parser exploit · oversized response ·
forged content type · stale data · unsigned evidence ·
sensitive-data retention.

## TECHNOLOGY OPTIONS — GROUP 3

تحقیق جدا 2026-08-16.

PRIMARY:

- Observation envelope موجود را کامل کن قبل از OCR جدید.
- Playwright فقط اگر browsing پویا gap دارد؛ network default-deny.
- Trafilatura / Unstructured / Docling / MarkItDown — ارزان‌ترین parser
  کافی؛ dual-pass فقط وقتی کیفیت اندازه گرفته شده.
- MinerU-Skill / PaddleOCR-VL — parser خروجی = untrusted.
- Unlimited OCR 2606.23050 — https://huggingface.co/papers/2606.23050
  https://github.com/baidu/Unlimited-OCR — مدل سنگین؛ برای Octopus شخصی
  پیش‌فرض **نصب نکن** مگر سند تصویری واقعی در pipeline باشد.
- MonkeyOCRv2 2607.11562 · PaddleOCR-VL-1.6 2606.03264
- mcp-scan / MCPShield روی ورودی ابزار و منابع خارجی (prompt injection /
  tool poisoning).

DO

- dual-pass فقط با measurement. parser ≠ instruction.
- unsigned evidence وارد long-term نشود (باید از Write Gate گروه ۲ بگذرد).

DO NOT

- مدل OCR چندگیگ را بدون dual-use/budget justification.
- fetch از خارج allowlist.

## خروجی

`06-EVIDENCE/EQUIP-G3-PERCEPTION-2026-08-16.md`.
سپس اسکن Wave C توسط ایجنت مستقل.
