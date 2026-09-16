# AUDITOR HANDOFF — ممیز مستقل D1 (آماده‌سازی PHASE01 4-5، 2026-08-16)

> انتخاب **نامِ** ممیز فقط با مالک است. این سند فقط می‌گوید ممیز دقیقاً چه
> می‌گیرد و چطور خودش تأیید می‌کند — بدون اعتماد به هیچ ادعای ایجنت.

## ممیز چه دریافت می‌کند (بستهٔ ثابت)

| قلم | مسیر | ماهیت |
|---|---|---|
| بستهٔ اصلی D1 | `_ops/D1-AUDIT-PACKAGE-2026-08-15/` | MANIFEST.txt + امضای Ed25519 مالک + RUN-AUDIT.ps1 + SCOPE |
| بستهٔ شواهد زنده (AEB) | `_ops/audit/bundles/AEB-*.json/.txt(+.sig)` | هر فکت با observed_at/TTL + نردبان وضعیت |
| مرز اعتماد | `4d_system/config/trust-boundary.json(+.sig)` | digest چهارده فایل TCB + پاکت NO-GO |
| اسکن راز | `_ops/tests/_baselines/gitleaks-full-20260815.json` | ۷۸۱ یافته، redacted |
| دفتر تناقض‌ها | `01-TRUTH/CONTRADICTIONS.md` | C-001..C-017 + وضعیت هر یک |
| ریشهٔ git | remote `E:/germline/octopus.git` | قفلِ provenance — ممیز باید HEAD را با AEB مقایسه کند |

## فرمان‌های تأیید (ممیز خودش اجرا می‌کند — خواندنی/فقط-خواندن)

```powershell
# ۱) امضای مالک (هر دو)
openssl pkeyutl -verify -pubin -inkey _ops/owner-signing/octopus-owner-ed25519-public.pem `
  -rawin -in 4d_system/config/trust-boundary.json -sigfile 4d_system/config/trust-boundary.json.sig
openssl pkeyutl -verify -pubin -inkey _ops/owner-signing/octopus-owner-ed25519-public.pem `
  -rawin -in _ops/audit/bundles/AEB-20260816-000508.txt -sigfile _ops/audit/bundles/AEB-20260816-000508.txt.sig

# ۲) یکپارچگی TCB (سایه/فعال — مستقل از ارگانیسم)
cd 4d_system; py -X utf8 -c "from brain import guardrails; import json; print(json.dumps(guardrails.check_trust_boundary(), ensure_ascii=False))"

# ۳) رانر حسابرسی فقط-خواندن (خروجی خام → ممیز امضا می‌کند)
powershell -NoProfile -ExecutionPolicy Bypass -File _ops/D1-AUDIT-PACKAGE-2026-08-15/RUN-AUDIT.ps1 -RepoRoot <مسیر کپی تمیز>

# ۴) پاکت NO-GO مستقل
py -X utf8 _ops/tests/test_no_go_envelope.py   # انتظار: 9/9

# ۵) وضعیت سیاست صف (R16 اعمال‌شده)
py -X utf8 4d_system/scripts/hypothesis_queue_report.py  # فقط-خواندن
```

## قاعدهٔ تازگی
باندل AEB باید **حداکثر ۲۴ ساعت** قبل از شروع ممیزی بازتولید شود (فرمان:
`py _ops/audit/generate_aeb.py`)؛ ممیز خروجی خام را دوباره اجرا کند، نه
گزارش ایجنت را. تغییر TCB/ارزیاب/زمان‌بند/PEP ⇒ ممیزی مجدد الزامی.

## مرز ممیز
فقط-خواندن روی درخت زنده؛ دیتابیس‌ها mode=ro؛ هیچ کلیدی به او داده نمی‌شود؛
نتیجه‌اش append-only در بستهٔ خودش ثبت می‌شود.
