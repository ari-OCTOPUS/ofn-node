# W0-PREFLIGHT — SURGERY-v2 (2026-09-14)

## محدودهٔ PASS (دقیق)

| میزبان | فایل‌های بسته‌شده | hash-OK در restore | کامپایل | probe منفی | verdict |
|---|---|---|---|---|---|
| ۱۳۸ | ۲۸ (۲۱ کد/state + ۷ unit) | **۲۸/۲۸** | ۱۲/۱۲ py | REJECTED | **PASS** |
| ۱۸۰ | ۷ بسته‌شده + ۱ hash-pin | **۷/۷** | — (فقط unit/sh) | REJECTED | **PASS** (وابستگی مدل مستند) |

بسته‌ها: `w0-138.tar.gz` sha16=687440e7 · `w0-180.tar.gz` sha16=dfa68623 — هر دو رفت‌وبرگشت لپ‌تاپ→میزبان→restore با همان هش.

## ایزولاسیون restore (واقعی، نه monkeypatch)

- restore در اسکرچ تازه با **uid nobody** اجرا شد (مرز کرنلی DAC — نوشتن production رد شد؛ probe منفی در هر دو میزبان REJECTED).
- فایل‌ها صریحاً allowlist شدند؛ کل state/ یا home هرگز glob نشد.
- secret/.env/کلید اصلاً خوانده/کپی نشد (فقط مسیر در PROVENANCE ثبت شد).

## RESTORE_DEPENDENCY_NOT_TESTED (صادقانه)

1. **باینری مدل ۱۸۰** (qwen3-0.6b-q4_0.gguf) — فقط hash-pin شد (sha در manifest-pre.json)؛ بازسازی آن نیازمند منبع تأییدشدهٔ مالک است.
2. **رفتار کامل import در محیط ایزوله** — py_compile در اسکرچ سبز است؛ import کامل ops_agent نیازمند درخت کتابخانه (ofn package + opslib) است که بسته نشد.
3. **secrets** — بازیابی آن‌ها عمداً آزموده نشد (مرز قرمز).
4. **state فعال صف** (canary-requests) — در بسته هست اما بازیابی آن به deployment وابسته است؛ اینجا فقط بایت‌ها تأیید شد.

## W1a (کامیت محلی)

- commit `93f6ad1` + fix `58f4504` (اصلاح CRLF) در worktree `repair/ziman-cycle-4-readiness`.
- ۱۵ فایل کد + ۷ unit + PROVENANCE.json؛ restore-from-checkout **ALL OK** (۶ فایل کلیدی byte-identical با میزبان زنده).
- بدون مصرف slot Class B؛ بدون تغییر runtime.
