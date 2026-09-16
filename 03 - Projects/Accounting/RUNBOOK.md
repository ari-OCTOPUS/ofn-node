# 💰 Accounting RUNBOOK — اجرای امن قلب مالی

> وضعیت: draft/read-only تا انتخاب حسابدار و ثبت verdictهای مالک.  
> این runbook مشاوره مالیاتی نیست؛ همه قواعد `[Unverified — accountant to confirm]` مگر خلافش ثبت شود.

---

## 0. اصول غیرقابل نقض

- ایجنت هرگز lodge به ATO/ASIC نمی‌کند.
- ایجنت هرگز پول جابه‌جا/پرداخت نمی‌کند.
- ایجنت هرگز PII/amount/account-number را به LLM نمی‌فرستد.
- هر دسته‌بندی مالی = draft تا verdict انسان.
- هر tax rule = `[Unverified — accountant to confirm]` تا حسابدار تأیید کند.
- GST inclusive formula: `GST = total / 11`؛ نه `amount * 0.10`.

---

## 1. وضعیت Gate

طبق context جدید Architect/_ops:

```text
Security Gate = LIFTED 2026-07-06
```

اما برای Accounting، کف خودمختاری همچنان:

```text
read-only / draft-only
```

چون حسابدار و ساختار شرکت هنوز تصمیم نهایی ندارند.

---

## 2. ورودی‌های مجاز

| ورودی | محل | رفتار |
|---|---|---|
| receipt photo/PDF | `data/receipts/` یا Inbox | extract draft |
| bank CSV export | owner-provided, not stored public | parse local draft |
| existing XLSX ledgers | `data/حساب کتاب/` | structure-only unless owner approves |
| project income event | from sister project logs | draft tax touchpoint |

---

## 3. خروجی‌های مجاز

| خروجی | مسیر | وضعیت |
|---|---|---|
| draft categorization | future `drafts/` | no final posting |
| monthly summary | future `reports/` | `[Unverified]` |
| compliance flags | future `flags/` | human/accountant review |
| questions | `OpenQuestions.md` | safe |
| decisions | `DecisionLog.md` | safe |

---

## 4. اجرای پایلوت ۱۰ رسید

قبل از هر اتوماسیون:

1. مالک ۱۰ رسید non-sensitive یا sanitized انتخاب کند.
2. برای هر رسید این فیلدها استخراج شود:

```yaml
date:
vendor:
amount_total:
gst_component:
abn_present: yes/no/unknown
category_draft:
confidence:
needs_human_review: true
```

3. خروجی فقط draft باشد.
4. انسان verdict بدهد.
5. خطاهای دسته‌بندی ثبت شود.

---

## 5. ANZ CSV importer — طراحی ایمن

Importer وقتی ساخته شود باید:

- فقط روی فایل export مالک اجرا شود.
- dedup بر اساس ستون ID انجام دهد.
- Closing Balance reconciliation داشته باشد.
- خروجی final ledger نسازد؛ فقط draft queue.
- PII/tokenization قبل از هر LLM.

Pseudo-flow:

```text
CSV → parse → validate columns → dedup(ID) → reconcile(Closing Balance)
→ tokenise sensitive fields → categorize draft → human verdict → final ledger by human/accountant
```

---

## 6. Tax touchpoints با پروژه‌های خواهر

| پروژه | trigger | Accounting draft event |
|---|---|---|
| Lead-نقاشی | invoice/payment | business income + GST check |
| Mining | coin received | AUD value at receipt + electricity/hardware note |
| Crypto-eToro | trade closed | CGT event, likely personal |
| Project-F | platform credit | A-share only, label `Project-F` |
| Ziman | sale | income + COGS |

---

## 7. Stop conditions

هرکدام از موارد زیر یعنی توقف و سؤال از مالک/حسابدار:

- disagreement over Pty Ltd structure
- GST ambiguity
- worker vs contractor ambiguity
- Div 7A / associate loan ambiguity
- missing ABN on vendor payment > threshold
- any request to lodge/pay/move money
- any request to expose PII to LLM

---

## 8. Next safe actions

1. Fill `REGISTRY.md`.
2. Update `OpenQuestions.md` with owner-input checklist.
3. Add `VERDICT_QUEUE.md` for Accounting.
4. If owner confirms, create `drafts/` and `reports/` folders.
5. Only after accountant decision: build importer skeleton.
