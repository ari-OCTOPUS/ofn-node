# 🎨 Lead-نقاشی RUNBOOK — اجرای امن منبع درآمد اصلی

> وضعیت: propose-only. هیچ outreach/publish/spend بدون verdict انسانی.

---

## اصول سخت

- هیچ پیام، تماس، ایمیل، پست، تبلیغ، quote نهایی یا spend خودکار انجام نمی‌شود.
- هر متن outreach فقط draft است.
- Spam Act / DNCR / ACL رعایت می‌شود: consent، ABN، opt-out، عدم ادعای غیرقابل‌اثبات.
- PII مشتری وارد حافظهٔ AI نمی‌شود؛ فقط hash/code.
- عکس‌های portfolio فقط اگر مالک اجازه بدهد public می‌شوند.

---

## Graph search قبل از هر کار

1. Load: `PROJECT.md`, `MANIFEST.yaml`, `contracts/adapter.yaml`, `OpenQuestions.md`, `DecisionLog.md`.
2. Follow graph edge: `LeadPainting → Accounting`.
3. Check `RISK-LADDER.md`: Lead = medium/propose-only.
4. If task includes publish/send/spend/call → write verdict request, stop.

---

## مجاز برای ایجنت

- دسته‌بندی portfolio.
- ساخت draft landing/copy/offer.
- طراحی experiment بدون اجرا.
- ساخت checklist lead pipeline.
- گزارش کردن lead sources.

## ممنوع

- ارسال پیام یا تماس.
- تبلیغ پولی.
- قول قیمت/زمان/گارانتی.
- استفاده از عکس بدون اجازه.
- جمع‌آوری PII بدون human process.

---

## Experiment #1 — طراحی امن

قبل از شروع:

```yaml
segment:
service_area:
offer:
channel:
portfolio_permission:
license_insurance_status:
weekly_capacity:
```

Output فقط:

```text
experiment-plan.md
copy-drafts.md
human-verdict checklist
```

---

## Stop conditions

- کانال شامل پیام مستقیم انبوه باشد.
- PII/phone list مطرح شود.
- claim غیرقابل اثبات باشد.
- ظرفیت معلوم نباشد.
- license/insurance ambiguity روی jobهای بزرگ باشد.
