# 🐙 مگاپرامپت: ارتقای موتور حسابداری خودکار مولتی‌ایجنت
## برای: ایجنت بعدی | تاریخ تهیه: ۲۰۲۶-۰۷-۱۶ | وضعیت: راهنمای اجرا

---

## ⚠️ قوانین طلایی (اول این‌ها را بخوان — نقض نکن)

1. **پول = سنت (integer cents)، هرگز float.** هیچ محاسبهٔ مالی با float نکن.
2. **Propose-only.** هیچ تراکنش/entry بدون تأیید انسان به وضعیت `posted` نمی‌رود. صفر حرکت خودکار پول.
3. **کلیدها فقط در `F:\backup\.env` (gitignore).** هرگز کلید را در کد/چت/commit نگذار.
4. **اولاما محلی پیش‌فرض.** فقط دادهٔ scrub-شده (بی‌نام/بی‌شماره) به Fugu می‌رود. پرچم `OCTOPUS_WIRE_ACCT_CLOUD` کنترلش می‌کند.
5. **AI فقط برای موارد مبهم.** بهترین AI دنیا (Gemini 3.1 Pro) در بنچمارک DualEntry فقط ۶۶٪ تسک حسابداری را درست انجام داد. پس rule-first، AI-second، human-always برای confidence < ۹۰٪.
6. **قبل از هر تغییر، تست‌های موجود را اجرا کن. بعد از هر تغییر، سبز بمانند.**
7. **Immutability:** entry با وضعیت `posted` تغییر نمی‌کند — فقط با یک entry معکوس اصلاح می‌شود.

---

## 🎯 مأموریت تو (در یک جمله)

سیستم فعلی (single-entry, ۳ ptype, owner=account-holder) را به یک موتور حسابداری واقعی ارتقا بده: **double-entry ledger + Chart of Accounts + جداسازی Entity/Agent** — بدون شکستن معماری propose-only موجود.

---

## 📊 وضعیت فعلی (As-Is) — چیزی که تحویل گرفتی

```
PocketSmith API (۴۲۶ تراکنش زنده, دسته: ArminNew/AbbasNew/salary)
  → txn_store (سنت، dedup content-hash، reconcile)
  → attributor (قاعده: حقوق/transfer/فروشنده)
  → txn_categorize (اولاما 7B → Fugu، propose)
  → صف بازبینی
  → موتور سنت (گزارش per-owner، transfer حذف)
  → تب /finance تلگرام
```

**کسب‌وکار واقعی:** نقاشی ساختمان در استرالیا. ۲ شریک (Armin, Abbas) + ۳ کارگر/پیمانکار (Behzad, Maliheh, Sume Asadi) + اجاره (Rent) + مشتریان + فروشندگان. «همه با همه» = یک شرکت با لایه‌های مختلف، نه شبکهٔ همتا-به-همتا.

---

## 🔴 ۳ اشتباه بنیادین که باید حل کنی (P0)

### اشتباه ۱: single-entry به جای double-entry
- **الان:** هر تراکنش یک رکورد `{owner, type, amount}`. `درآمد - خرج = خالص`.
- **مشکل:** نمی‌شود اثبات کرد books بالانس است. اگر عددی گم شود، پیدا نمی‌شود.
- **باید:** هر تراکنش ≥۲ entry (debit + credit). `Σ debit = Σ credit = 0`.

### اشتباه ۲: خلط «صاحب حساب بانکی» با «ذی‌نفع اقتصادی»
- **الان:** ArminNew → owner=Armin. یعنی هر تراکنش روی حساب آرمین = مال آرمین.
- **مشکل:** از حساب آرمین ممکن است حقوق بهزاد، اجاره، یا برداشت عباس برود. این‌ها ماهیت متفاوت دارند.
- **باید:** مدل REA — Resource (bank account) + Event (transaction) + Agent (payer/payee/beneficiary). یک agent چند نقش می‌تواند داشته باشد.

### اشتباه ۳: نبود Chart of Accounts
- **الان:** فقط ۳ نوع (income/expense/transfer).
- **باید:** COA کامل زیر.

---

## 🟡 اشتباهات ثانویه (P1)

- **Dedup شکننده:** content-hash → باید external_ref (PocketSmith transaction ID). این باعث double-counting شد (عباس $۷۸k = ۲× واقعی) چون API و CSV یک داده با ID متفاوت بودند.
- **نبود Immutable Ledger:** PocketSmith منبع است نه دفترکل. باید یک دفترکل داخلی تغییرناپذیر با pending→posted داشته باشی.
- **Transfer مبهم:** transfer بین دو حساب یک شخص (net=0) با پرداخت به شخص دیگر (رویداد اقتصادی) فرق دارد. نباید صرفاً «پول از A به B» را transfer فرض کرد.

---

## 📋 CHART OF ACCOUNTS (این را پیاده کن)

```
دارایی (Assets) — debit normal
  1000  Bank Account - Armin
  1010  Bank Account - Abbas
  1100  Accounts Receivable (طلب از مشتری)
  1200  Materials Inventory
  1300  Tools & Equipment
  1400  Due from Abbas
  1410  Due from Armin

بدهی (Liabilities) — credit normal
  2000  Accounts Payable
  2010  GST Payable
  2020  Due to Armin
  2030  Due to Abbas

سرمایه (Equity) — credit normal
  3000  Armin Capital
  3010  Armin Drawings
  3100  Abbas Capital
  3110  Abbas Drawings
  3200  Retained Earnings

درآمد (Revenue) — credit normal
  4000  Painting Services - Residential
  4010  Painting Services - Commercial
  4020  Other Income

هزینهٔ مستقیم (COGS) — debit normal
  5000  Paint & Materials
  5010  Subcontractor - Behzad
  5020  Subcontractor - Maliheh
  5030  Subcontractor - Sume Asadi
  5040  Equipment Rental

هزینهٔ عملیاتی (Expenses) — debit normal
  6000  Rent
  6010  Fuel & Vehicle
  6020  Insurance
  6030  Marketing
  6040  Tools & Supplies
```

**قانون debit/credit (حفظ کن):**
| نوع حساب | Debit | Credit |
|----------|-------|--------|
| Asset    | +     | −      |
| Liability| −     | +      |
| Equity   | −     | +      |
| Revenue  | −     | +      |
| Expense  | +     | −      |

---

## 🏗️ معماری هدف (To-Be)

```
DataSource (PocketSmith API + CSV)
        │
        ▼
[Input Pipeline]
  - dedup روی external_ref (نه content-hash)
  - enrich: agent mapping (payer/payee/beneficiary)
  - classify: rules اول → AI بعد
  - propose double-entry (Σ=0 validation)
        │
        ▼
[Review Queue]
  - AI confidence < 90%
  - payee جدید
  - amount anomaly
        │ (human approves)
        ▼
[IMMUTABLE LEDGER]  ← منبع حقیقت جدید
  transaction_id | external_ref | date
  status: pending → posted
  entries[]: {account_code, dr_cr, amount_cents}
  invariant: Σ entries = 0
        │ (فقط posted)
        ▼
[Report Engine]
  Trial Balance | P&L | Balance Sheet
  Partner Capital | Job Profitability | GST Summary
  → /finance Telegram
```

---

## 🔄 مدل داده پیشنهادی

```python
# Ledger Transaction (immutable once posted)
{
  "transaction_id": "uuid",
  "external_ref": "pocketsmith_txn_id",   # کلید dedup
  "date": "2025-12-08",
  "status": "pending" | "posted",          # posted = قفل
  "source": "pocketsmith" | "csv",
  "description": "raw text",
  "entries": [                             # حداقل ۲ تا
    {"account_code": 5000, "dr_cr": "DR", "amount_cents": 50000},
    {"account_code": 1000, "dr_cr": "CR", "amount_cents": 50000}
  ],
  "agents": [                              # REA
    {"name": "Armin", "role": "payer"},
    {"name": "PaintShop", "role": "payee"}
  ],
  "job_code": "optional_project_id",       # برای job costing
  "confidence": "HIGH" | "MEDIUM" | "LOW",
  "reviewed_by": "human_id" | null
}
# invariant اجباری: sum(DR) == sum(CR)
```

---

## 🤖 پرامپت‌های AI (برای txn_categorize)

### System prompt:
```
You are an accounting assistant for a painting/construction business in Australia.

[درج کامل CHART OF ACCOUNTS بالا]

KNOWN AGENTS:
- Armin: partner/owner → equity 3000-3010
- Abbas: partner/owner → equity 3100-3110
- Behzad: subcontractor → COGS 5010
- Maliheh: subcontractor → COGS 5020
- Sume Asadi: subcontractor → COGS 5030
- Suppliers (paint/hardware) → COGS 5000 or Expense 6000s
- Clients → Revenue 4000s
- Landlord → Rent 6000

DETERMINISTIC RULES (apply BEFORE any AI guess):
1. Description contains subcontractor name → COGS 50xx
2. Round amount from known client → Revenue 4000
3. "rent" in description → Expense 6000
4. Transfer Armin↔Abbas accounts → check context:
   - regular similar amounts → profit distribution (Equity)
   - large one-off → loan (Due to/from)
   - small irregular → reimbursement
5. Never invent an account not in the COA.
```

### Per-transaction prompt:
```
TRANSACTION:
  External Ref: {external_ref}
  Date: {date}
  Bank Account: {bank_account_name}
  Amount: {amount_cents} cents ({sign})
  Description: {description}

TASK:
1. Economic event type (sale/purchase/payment/receipt/transfer)
2. ALL agents involved (payer, payee, beneficiary)
3. Double-entry (≥2 entries):
   DR: [code] [name] $[amount]
   CR: [code] [name] $[amount]
4. Confidence: HIGH(>90%) / MEDIUM(70-90%) / LOW(<70%)
5. Reasoning (1 sentence)

VALIDATION: DR total MUST equal CR total. If unsure → LOW confidence.
```

---

## ✅ خروجی‌های مورد نیاز (فقط از entries با status=posted)

1. **Trial Balance** — همهٔ حساب‌ها، شرط صحت: `Σ DR = Σ CR`
2. **P&L** — `Revenue(4xxx) − COGS(5xxx) − Expenses(6xxx) = Net Profit`
3. **Balance Sheet** — `Assets(1xxx) = Liabilities(2xxx) + Equity(3xxx)`
4. **Partner Capital** — `Capital = initial + profit_share − drawings` برای هر شریک
5. **Job Profitability** (اگر job_code داری) — `Revenue − Materials − Labor per project`
6. **GST Summary** — `GST collected − GST paid = net GST` (استرالیا: اگر turnover > $75k باید register شود)

---

## 📈 نقشهٔ راه اجرا (به این ترتیب)

| گام | اقدام | خروجی قابل تست |
|-----|-------|----------------|
| ۱ | تعریف COA به‌عنوان ثابت/config | لیست حساب‌ها لود می‌شود |
| ۲ | مدل داده Ledger Transaction با entries[] | schema + validation Σ=0 |
| ۳ | تبدیل dedup به external_ref | تست: API+CSV یکسان → یک رکورد |
| ۴ | rule engine (قوانین قطعی COA) | تست: هر rule درست map می‌کند |
| ۵ | تولید double-entry از هر تراکنش | تست: هر txn دو entry بالانس |
| ۶ | pending→posted state machine | تست: posted تغییرناپذیر |
| ۷ | AI فقط برای LOW/MEDIUM باقی‌مانده | تست: confidence routing |
| ۸ | Report engine روی posted | تست: trial balance = 0 |
| ۹ | مهاجرت ۴۲۶ تراکنش زنده به مدل جدید | reconcile با اعداد قبلی |

**بعد از هر گام:** commit جدا + تست سبز + یادداشت در حافظه.

---

## 🧪 اعتبارسنجی نهایی (قبل از commit نهایی)

- [ ] هر تراکنش دقیقاً `Σ DR = Σ CR`
- [ ] Trial Balance کل = صفر
- [ ] Balance Sheet: `Assets = Liabilities + Equity`
- [ ] هیچ double-count نیست (external_ref یکتا)
- [ ] عباس ≈ +$۳۶۰ (نزدیک عدد اپ واقعی) — نه $۷۸k
- [ ] حقوق آرمین ≈ $۱۲٬۲۸۵ حفظ شده
- [ ] هیچ entry با status=posted بعداً تغییر نکرده
- [ ] همهٔ تست‌های قبلی + جدید سبز
- [ ] هیچ float در محاسبات مالی نیست
- [ ] هیچ کلید در کد/commit نیست

---

## ❓ سوالاتی که باید از کاربر بپرسی (ابهامات تجاری)

1. **ساختار حقوقی چیست؟** sole trader / partnership / company؟ (روی equity و مالیات اثر دارد)
2. **بهزاد/ملیحه/صومعه employee هستند یا subcontractor (ABN دارند)؟** (STP/PAYG vs COGS ساده)
3. **آرمین و عباس چطور سود تقسیم می‌کنند؟** ۵۰/۵۰؟ درصد مشخص؟
4. **آیا turnover از $۷۵k رد شده؟** (آستانهٔ ثبت GST در استرالیا)
5. **آیا کد پروژه (job) دارید؟** (برای job costing لازم است)
6. **۵ CSV قدیمی (behzad/maliheh/sume/rent) — بازهٔ زمانی و رابطه با API چیست؟**

---

## 📚 منابع مرجع (برای عمق بیشتر)

- Modern Treasury — "Accounting for Developers I-III" + "Enforcing Immutability" + "How to Scale a Ledger I-VI" → استاندارد double-entry API-ledger
- DualEntry Labs — "AI Fails One-Third of Accounting Tasks" (۲۰۲۶) → چرا human-in-loop لازم است
- McCarthy (1982) — REA Model → جداسازی Resource/Event/Agent
- GS Advisory + ConcreteBK → Chart of Accounts برای کسب‌وکار نقاشی
- ATO — Single Touch Payroll + Record Keeping → الزامات استرالیا
- Deltek/NetSuite — Construction Job Costing → سودآوری per-project

**تحلیل کامل در:** `F:\backup\theory--accounting-engineering-review.md`

---

## 🎬 خط شروع تو

```
۱. theory--accounting-engineering-review.md را بخوان
۲. تست‌های فعلی را اجرا کن (baseline سبز)
۳. ۶ سوال بالا را از کاربر بپرس
۴. گام ۱ نقشهٔ راه (COA) را شروع کن
۵. propose-only را هرگز نشکن
```
