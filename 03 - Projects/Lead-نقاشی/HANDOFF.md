# HANDOFF — Lead-نقاشی / Painting-OS

> **تاریخ:** 2026-07-12
> **ایجنت قبلی:** ZCode GLM-5
> **وضعیت:** P1-P3 کامل · 42 تست سبز · همه کمیت شده
> **اول بخوان:** `PROJECT.md` بعد `README.md` بعد `کاریابی/08_Painting-OS_Roadmap_v2.md`

---

## ✅ چه ساخته شد (جمع‌بندی)

### Painting-OS — ۴ ستون

| ستون | فایل‌ها | تست | کد |
|------|---------|------|-----|
| **P1 کوتیشن** | `_ops/legs/pricing.py` `lead_quote.py` | 19 | pricing: نرخ سیدنی $18-65/m², QuoteIntake 14 فیلد, estimate_price() ranges; lead_quote: create/revise/history, QT-YYYYMMDD-NNN, render_quote_html() |
| **P2 فاکتور** | `_ops/legs/invoice.py` | 8 | ATO Tax Invoice, ABN, GST 10%, INV-FY{YY}-{NNN}, PAID from attribution CONFIRMED, invoices_pending/all dashboard |
| **P3 ایمیل** | `_ops/legs/email_inbound.py` | 9 | Gmail OAuth readonly (stdlib urllib), flag-gated (OCTOPUS_WIRE_EMAIL), parse_lead_from_email, poll_and_digest |
| **reconcile v2** | `_ops/budget/reconcile.py` | 8 (attribution) | گروه‌بندی CSV بر lead_id → partial payment (deposit + balance) |
| **intake پارس** | `_ops/tests/test_lead_intake.py` | 6 | parse_lead_intake(): 7+ field format / backward-compat 2-field |
| **config** | `_ops/budget/budgets.yaml` | — | business section (ABN, name, address, bank) + email section (Gmail OAuth) |

### کمیت‌ها (master)
```
076d232 feat(painting-os): P1 quotation + P2 invoice + P3 email inbound (real _ops)
a7bedfc docs(painting-os): 10-stage roadmap v2 with competitor research + market analysis
```

### کمیت‌ها (worktree: telegram-governance-integration-832984)
```
de16794 feat(p1-quotation): structured quoting engine + partial payment reconcile
da3b0e2 feat(p2p3-painting-os): invoice engine + email inbound + structured intake
```

### تحقیق بازار ( کامل)
- ServiceM8 ($29-79/ماه) · Tradify ($70+/user) · AroFlo ($120+) · QuoteIQ ($150-700 USD)
- hipages ($129+/ماه + $20-50/لید) · Airtasker+Oneflare (12-20% کار) · ServiceSeeking
- NSW Fair Trading · Home Building Act §8 · ATO GST rules
- ServiceTitan 2025 AU Tradies Report · IBISWorld · PaintersLink · Brushworks
- **نتیجه:** هیچ ابزار مساگر یکپارچه AU-m painting-specific doesn't exist

---

## 📋 مراحل بعدی (اولویت‌بندی‌شده)

详细的 ۱۰ مرحله در `کاریابی/08_Painting-OS_Roadmap_v2.md`.

### فوری (مرحله ۱-۳)
1. **وایر `/lead` تلگرام:** `approval_channel.py` `_cmd_lead_parse` → `parse_lead_intake()` → `lead_quote.create_quote()` → `render_quote_html()`. backward-compat: 2 فیلد → رفتار قدیمی.
2. **ABN واقعی:** `budgets.yaml` → `business.abn`, `trading_name`, `address`, `bank_details`. بدون این، فاکتورها تستی هستند.
3. **Gmail OAuth E2E:** Google Cloud Console → OAuth client → token → `OCTOPUS_WIRE_EMAIL=1` → تست `poll_and_digest()`.

### میان‌مدت (مرحله ۴-۷)
4. فرم/وب‌سایت → ایمیل → لید
5. PDF کوتیشن (WeasyPrint یا FPDF)
6. فاکتور خودکار + ارسال تلگرام
7. پیگیری کوتیشن (day 3, 7)

### بلندمدت (مرحله ۸-۱۰)
8. داشبورد `/dash` تلگرام
9. SEO + Google Business Profile
10. قیمت‌گذاری پیشرفته (یادگیری از داده)

---

## 🔧 محدودیت‌ها (همیشه رعایت کن)

| محدودیت | توضیح |
|---------|-------|
| **propose-only** | هیچ ارسالی بدون تأیید انسان. پا فقط Proposal تولید. |
| **$0 stdlib-only** | وابستگی خارجی ممنوع. فقط `urllib`, `json`, `re`, `sqlite3`, ... |
| **صفر راز جدید** | credentials فقط در `.env` / `budgets.yaml`. نه hardcode. |
| **backward-compat** | فرمت قدیمی `/lead` byte-identical. هیچ تغییر breaking بدون owner approval. |
| **fail-soft** | هر تابع بدون data → `{}` یا `[]` بدون خطا. |
| **tests first** | هر تغییر کد → تست جدید → همه سبز → کمیت. |

---

## 🗂️ نقشهٔ فایل‌های مهم

```
_ops/
├── legs/
│   ├── pricing.py          ← P1: نرخ سیدنی + QuoteIntake + estimate_price()
│   ├── lead_quote.py       ← P1: create/revise/history + QT numbers
│   ├── invoice.py          ← P2: ATO Tax Invoice + INV-FY + PAID
│   ├── email_inbound.py    ← P3: Gmail OAuth readonly + lead parsing
│   ├── lead_leg.py         ← Worker: LeadLeg(Leg) intake/draft/claim
│   └── lead_draft.py       ← backward-compat: build_and_persist
├── budget/
│   ├── reconcile.py        ← v2: partial payment (grouped by lead_id)
│   ├── budgets.yaml        ← config: business + email sections
│   └── attribution.py      ← 5-state lifecycle, fold(), confirm()
└── tests/
    ├── harness.py          ← isolated test environment (temp vault)
    ├── test_pricing.py     ← 10 tests ✅
    ├── test_lead_quote.py  ← 9 tests ✅
    ├── test_lead_intake.py ← 6 tests ✅
    ├── test_invoice.py     ← 8 tests ✅
    └── test_email_inbound.py ← 9 tests ✅

کاریابی/
├── 07_Painting-OS_P1_Quotation_Design.md  ← طراحی P1
└── 08_Painting-OS_Roadmap_v2.md           ← ۱۰ مرحلهٔ بعدی
```

---

## ⚠️ نکات فنی

1. **harness واقعی از `_ops/` (نه worktree) import می‌کند.** وقتی فایلی در `_ops/legs/` عوض می‌شود، `__pycache__` را پاک کن.
2. **inv_seq.json** در `state/legs/invoices/` است — شماره‌گذاری INV-FY. `invoices_pending()` و `invoices_all()` فقط `schema=="invoice.v1"` را می‌شمارند.
3. **Gmail OAuth:** scope = `gmail.readonly`, 1B quota/day, app = "Testing" status. token در `state/email/gmail_token.json`.
4. **NSW deposit cap:** حداکثر 10% قیمت قرارداد (Home Building Act §8) — در هر فاکتور نمایش داده می‌شود.
5. **ATO Tax Invoice:** label "Tax Invoice" الزامی، ABN، GST 10% جداگانه، >$1000 → نام/ABN مشتری.

---

## 🏗️ معماری کلی

```
/lead (Telegram)          email (Gmail)        فرم وب
       │                        │                  │
       ▼                        ▼                  ▼
  parse_lead_intake()    parse_lead_from_email()  → email → inbox
       │                        │
       ▼                        ▼
  lead_quote.create_quote() → Proposal (QT-...)
       │
       ▼
  render_quote_html() → تلگرام → مشتری
       │
       ▼ (تأیید مشتری)
  invoice.create_invoice() → INV-FY... → تلگرام/PDF
       │
       ▼ (پرداخت CSV اپراتور)
  reconcile.run() → CONFIRMED
       │
       ▼
  invoice.mark_paid() → PAID (مشتق از attribution)
```

هر مرحله human-gated. سیستم هیچ چیزی بدون تأیید آری ارسال نمی‌کند.

---

## 🔍 مشکلات شناخته

- [ ] ABN واقعی هنوز در `budgets.yaml` خالی است
- [ ] Gmail OAuth token هنوز صادر نشده
- [ ] `parse_lead_intake()` فقط در test نوشته شده — باید در `approval_channel.py` وایر شود
- [ ] `test_lead_ui.py` 4/5 تست شکست (pre-existing، ربطی به Painting-OS ندارد — inline keyboard rendering)
