# تحلیل تئوری: اشتباهات مهندسی حسابداری خودکار + مقایسه با مدل‌های جهانی
## تاریخ: ۲۰۲۶-۰۷-۱۶
## وضعیت: فقط تحلیل تئوری — فایل‌های واقعی تغییر نمی‌کنند

---

# ۱. نقشهٔ سیستم فعلی (آنچه ساختید)

```
PocketSmith API (کلید فقط‌خواندنی, ۴۲۶ تراکنش زنده)
  → txn_store (سنت، dedup، reconcile)
  → attributor (قاعده قطعی: حقوق/transfer/فروشنده)
  → txn_categorize (اولاما 7B محلی → Fugu)
  → صف بازبینی (تأیید/تصحیح = یادگیری)
  → موتور قطعی سنت (گزارش per-owner، transferها حذف)
  → تب /finance تلگرام
```

## ۱.۱ نقاط قوت (چیزهایی که درست انجام شده)
- ✅ سنت (cent) نه float — استاندارد طلایی مالی
- ✅ Propose-only — هیچ تراکنشی بدون تأیید انسان ثبت نمی‌شود
- ✅ کلید در .env — امنیت درست
- ✅ اولاما محلی برای حریم خصوصی — PII از LLM ابری رد نمی‌شود
- ✅ اتصال زنده به PocketSmith — داده واقعی، نه شبیه‌سازی

---

# ۲. اشتباهات شناسایی‌شده (به ترتیب اهمیت)

## 🔴 اشتباه #۱: فقدان دفترکل دوبل (Double-Entry Ledger)

**وضعیت فعلی:** سیستم «درآمد منهای خرج = خالص» را به ازای هر شخص حساب می‌کند. این حسابداری یک‌طرفه (single-entry) است.

**چرا این مشکل است (مرجع: Modern Treasury):**
> "Double-entry accounting is the most reliable way to track money. It ensures every financial event is recorded accurately, with a clear source and destination for funds. When software fails to track money properly, the most common failure mode is software accidentally creating or destroying records of funds."

**در عمل یعنی:** الان نمی‌توانی ثابت کنی که books بالانس است. در دفتر دوبل:
- هر تراکنش حداقل ۲ ثبت (entry) دارد: یکی بدهکار (debit) و یکی بستانکار (credit)
- جمع همهٔ debitها باید برابر جمع همهٔ creditها باشد → trial balance = صفر
- اگر بالانس نباشد → یک جای کار اشتباه است

**مثال از پروژهٔ شما:**
- الان: «آرمین $۵۰۰ خرج کرد برای رنگ» → فقط یک رکورد: {owner: Armin, type: expense, amount: -$500}
- باید باشد:
  ```
  DR: Materials Expense (COGS)    $500
  CR: Bank Account (Armin)              $500
  ```
  و اگر رنگ را عباس خریده ولی از حساب آرمین رفته:
  ```
  DR: Materials Expense (COGS)    $500
  CR: Bank Account (Armin)              $500
  DR: Due from Abbas               $500
  CR: Armin Capital                $500
  ```

---

## 🔴 اشتباه #۲: خلط «صاحب حساب» با «ذی‌نفع اقتصادی»

**وضعیت فعلی:** دستهٔ PocketSmith → owner (ArminNew → آرمین، AbbasNew → عباس). یعنی هر تراکنش روی حساب آرمین = تراکنش آرمین.

**چرا این مشکل است:**
در یک کسب‌وکار چندنفره (نقاشی ساختمان)، حسابی که به نام آرمین است لزوماً فقط برای خرج‌های شخصی آرمین نیست. از همان حساب ممکن است:
- حقوق کارگر (بهزاد) پرداخت شود → این خرجِ آرمین نیست، خرجِ کسب‌وکار است
- اجاره پرداخت شود → خرجِ عملیاتی است
- پول پروژه از مشتری بیاید → درآمدِ کسب‌وکار است، نه درآمدِ شخصِ آرمین
- عباس از حساب آرمین پول بردارد → این transfer/قرض/تسهیم سود است

**مدل درست (مرجع: REA Model - Resources, Events, Agents):**
- **بانک account** = Resource (منبع)
- **پرداخت/دریافت** = Event (رویداد اقتصادی)
- **آرمین/عباس/بهزاد/مشتری** = Agent (عامل/ذی‌نفع)

رابطهٔ agent با transaction می‌تواند چندگانه باشد: payer، payee، beneficiary، obligor.

**برای پروژهٔ شما یعنی:** یک تراکنش روی حساب آرمین باید بتواند:
- از نوع «خرج کسب‌وکار (مواد)» باشد → به COGS می‌رود
- از نوع «حقوق بهزاد» باشد → به subcontractor expense می‌رود
- از نوع «برداشت شخصی آرمین» باشد → به Owner's Draw می‌رود
- از نوع «قرض به عباس» باشد → به Due from Abbas می‌رود

---

## 🔴 اشتباه #۳: فقدان نمودار حساب (Chart of Accounts)

**وضعیت فعلی:** سیستم فقط ۳ نوع تراکنش می‌شناسد: income، expense، transfer. این برای یک سوپرمارکت کوچک هم کافی نیست، چه برسد به یک کسب‌وکار نقاشی ساختمان با چند کارگر و شریک.

**مدل درست (مرجع: Australian painting business accounting + Construction COA):**

```
دارایی‌ها (Assets) — debit normal
  1000  Bank Account - Armin
  1010  Bank Account - Abbas
  1100  Accounts Receivable (طلب از مشتری)
  1200  Materials Inventory (موجودی رنگ و مصالح)
  1300  Tools & Equipment
  1400  Due from Abbas (طلب از عباس)
  1410  Due from Armin (طلب از آرمین)

بدهی‌ها (Liabilities) — credit normal
  2000  Accounts Payable (بدهی به فروشنده)
  2010  GST Payable (مالیات بر ارزش افزوده)
  2020  Due to Armin (بدهی به آرمین)
  2030  Due to Abbas (بدهی به عباس)

سرمایه (Equity) — credit normal
  3000  Armin Capital
  3010  Armin Drawings (برداشت شخصی)
  3100  Abbas Capital
  3110  Abbas Drawings
  3200  Retained Earnings (سود انباشته)

درآمد (Revenue) — credit normal
  4000  Painting Services - Residential
  4010  Painting Services - Commercial
  4020  Other Income

هزینهٔ مستقیم (COGS) — debit normal
  5000  Paint & Materials (رنگ و مصالح)
  5010  Subcontractor - Behzad
  5020  Subcontractor - Maliheh
  5030  Subcontractor - Sume Asadi
  5040  Equipment Rental

هزینهٔ عملیاتی (Expenses) — debit normal
  6000  Rent (اجاره)
  6010  Fuel & Vehicle (بنزین و ماشین)
  6020  Insurance
  6030  Marketing
  6040  Tools & Supplies
```

---

## 🟡 اشتباه #۴: مدل‌سازی «شبکه» به جای «شرکت + ذی‌نفعان»

**وضعیت فعلی:** «همه با همه» = یک شبکهٔ چند-طرفه (Armin + Abbas + Behzad + Maliheh + Sume + Rent) که مثل یک گراف مالی به هم وصلند.

**چرا این مدل ناقص است:**
در حسابداری واقعی، یک **شخصیت حقوقی/اقتصادی** (business entity) وجود دارد که مرکز است. در استرالیا این می‌تواند sole trader، partnership، یا company باشد. همهٔ تراکنش‌ها از لنز این entity دیده می‌شوند.

**مدل درست:**
```
کسب‌وکار نقاشی ساختمان (Entity)
  │
  ├── مالکان (Equity):
  │     ├── Armin (Partner) → Armin Capital + Drawings
  │     └── Abbas (Partner) → Abbas Capital + Drawings
  │
  ├── کارگران/پیمانکاران فرعی (COGS):
  │     ├── Behzad → Subcontractor expense
  │     ├── Maliheh → Subcontractor expense
  │     └── Sume Asadi → Subcontractor expense
  │
  ├── تأمین‌کنندگان (Expense):
  │     └── Rent → Rent expense
  │
  └── مشتریان (Revenue):
        └── Various clients → Painting revenue
```

تفاوت کلیدی: 「شبکهٔ همتابه‌همتا」نیست — یک «شرکت با لایه‌های مختلف» است.

---

## 🟡 اشتباه #۵: Dedup شکننده (Content-based بدون کلید خارجی)

**وضعیت فعلی:** dedup بر اساس محتوای تراکنش (content-hash) انجام می‌شود، نه شناسهٔ یکتای بانکی.

**مشکل (که در پروژه اتفاق افتاد):**
دادهٔ API زنده (۹۹ تراکنش عباس) و فایل CSV قدیمی (۹۹ تراکنش عباس) عملاً همان داده بودند ولی ID متفاوت داشتند → dedup نشد → عباس $۷۸k نشان داد (تقریباً ۲× واقعی).

**مدل درست (مرجع: Modern Treasury — How to Scale a Ledger):**
هر تراکنش باید یک `external_reference` داشته باشد — شناسهٔ یکتای تراکنش بانکی. dedup روی این فیلد انجام می‌شود، نه روی محتوا.

**برای پروژهٔ شما:**
- PocketSmith transaction ID → external_reference
- CSVها هم باید در صورت امکان یک external_reference داشته باشند
- وقتی API و CSV هر دو یک تراکنش را دارند → external_reference یکسان → dedup اتوماتیک

---

## 🟡 اشتباه #۶: فقدان Ledger Immutable (دفترکل تغییرناپذیر)

**وضعیت فعلی:** سیستم مستقیماً از PocketSmith API می‌خواند و تحلیل می‌کند. PocketSmith منبع داده است، نه دفترکل داخلی.

**چرا این مشکل است (مرجع: Modern Treasury):**
> "Immutability in a double-entry ledger system is one of the core defining principles. If the data has been mutated, then the data is irreversibly destroyed and becomes impossible to figure out what changed."

**مدل درست:**
- PocketSmith = منبع دادهٔ ورودی (data source)
- Internal Ledger = دفترکل تغییرناپذیر (immutable) که همهٔ entries در آن ثبت می‌شود
- هر entry یک status دارد: `pending` (قابل ویرایش) → `posted` (قفل‌شده)
- هیچ entryای پس از posted شدن تغییر نمی‌کند — فقط با یک entry معکوس اصلاح می‌شود

---

## 🟡 اشتباه #۷: مدیریت Transfer مبهم

**وضعیت فعلی:** transferها «از net حذف می‌شوند» — ولی تعریف transfer مبهم است.

**در حسابداری درست:**
- **Transfer بین حساب‌های یک شخص:** از حساب A آرمین به حساب B آرمین → net effect صفر (تغییر در دارایی، نه در سود/زیان)
- **Transfer بین دو شخص مختلف:** از حساب آرمین به حساب عباس → این transfer نیست! می‌تواند:
  - تسهیم سود (profit distribution) → Dr. Armin Capital, Cr. Abbas Capital
  - قرض (loan) → Dr. Due from Abbas, Cr. Bank
  - پرداخت بابت کاری که عباس کرده (subcontractor) → Dr. COGS, Cr. Bank
  - حقوق عباس → Dr. Salary Expense, Cr. Bank

**تشخیص خودکار transfer واقعی از پرداخت اقتصادی نیاز به context دارد** و نمی‌شود صرفاً با «پول از یک حساب به حساب دیگر» قضاوت کرد.

---

## 🔴 اشتباه #۸: اعتماد بیش از حد به AI برای Categorization

**مرجع: DualEntry Labs Benchmark (مارس ۲۰۲۶)**
> ۱۹ مدل AI روی ۱۰۱ تسک واقعی حسابداری تست شدند. بهترین مدل (Gemini 3.1 Pro) فقط ۶۶٪ دقت داشت. هیچ مدلی از ۷۰٪ رد نشد. **"In finance, 66% accuracy isn't automation. It's assisted drafting."**

**مدل‌های تست‌شده و نتایج:**
- Gemini 3.1 Pro: 66.0%
- GLM-5: 65.3%
- MiniMax M2.5: 65.3%
- GPT-4: 19.8% (بدترین)

**نتیجه برای پروژهٔ شما:**
سیستم propose-only (پیشنهاد + تأیید انسان) **کاملاً درست** است. اما ۴۰۰+ تراکنش با ۶۶٪ دقت یعنی ~۱۳۶ اشتباه در هر batch. باید:
- قوانین قطعی (deterministic rules) را تا جای ممکن گسترش داد — AI فقط برای موارد واقعاً مبهم
- rule-based categorization اولویت دارد بر AI-based
- confidence score زیر ۹۰٪ → همیشه human review

---

# ۳. مقایسه با مدل‌های جهانی

## ۳.۱ Modern Treasury (آمریکا — استاندارد طلایی API-ledger)

| ویژگی | Modern Treasury | پروژهٔ شما | شکاف |
|--------|----------------|------------|------|
| Double-entry | بله — هر تراکنش ≥۲ entry | خیر — single-entry per owner | ⚠️ بزرگ |
| Immutability | posted = غیرقابل تغییر | ندارد | ⚠️ بزرگ |
| Chart of Accounts | Account Categories (graph) | ptype سه‌تایی | ⚠️ بزرگ |
| Pending→Posted | state machine کامل | ندارد | ⚠️ متوسط |
| External reference | بله | ضمنی | ⚠️ متوسط |
| API-first | بله | بله | ✅ |
| Cents | بله | بله | ✅ |

## ۳.۲ REA Model (آکادمیک — ontology حسابداری)

| مفهوم REA | معادل در پروژهٔ شما | وضعیت |
|-----------|-------------------|--------|
| Resource (منبع) | Bank account, cash | ضمنی — ثبت نشده |
| Event (رویداد) | Transaction | ✅ داری |
| Agent (عامل) | Owner (آرمین/عباس) | ⚠️ فقط ۲ agent، درحالی‌که حداقل ۶ تا داری |
| Duality (دوگانگی) | - | ❌ نداری — هر رویداد باید give + receive داشته باشد |

## ۳.۳ Australian STP (استاندارد گزارش‌دهی حقوق)

برای بهزاد/ملیحه/صومعه:
- اگر employee هستند → PAYG withholding + superannuation → باید به ATO گزارش شود
- اگر subcontractor هستند (ABN دارند) → فقط پرداخت ناخالص → COGS
- **مدل فعلی این تفکیک را ندارد**

## ۳.۴ Construction Job Costing (استاندارد صنعت ساختمان)

| نیاز | وضعیت فعلی |
|------|-----------|
| کدینگ پروژه | ❌ هیچ — نمی‌دانی کدام خرج برای کدام پروژه است |
| مقایسهٔ برآورد vs واقعی | ❌ |
| تفکیک مواد/دستمزد/پیمانکار | ❌ — همه «expense» است |
| سودآوری هر پروژه | ❌ |

---

# ۴. ورودی و خروجی باید چه باشد

## ۴.۱ ورودی (Input Pipeline)

```
مرحله ۰: دریافت تراکنش خام
  ← PocketSmith API (external_ref, date, amount_cents, description, bank_account)
  ← CSV files (با external_ref اگر موجود باشد)

مرحله ۱: Dedup بر اساس external_ref
  ← اگر external_ref تکراری → skip
  ← اگر external_ref ندارد → content-hash + human review

مرحله ۲: شناسایی Agent
  ← Map description → known agents (Armin, Abbas, Behzad, Maliheh, Sume, clients, suppliers)
  ← نقش agent در این تراکنش: payer/payee/beneficiary؟

مرحله ۳: طبقه‌بندی در COA (قطعی + AI)
  ← قوانین قطعی اول: exact match description → COA code
  ← AI پیشنهاد می‌دهد برای باقی‌مانده
  ← همهٔ AIها → human review queue

مرحله ۴: تولید Double-Entry
  ← برای هر تراکنش یک:
      Dr: {account_code}  $amount
      Cr: {account_code}  $amount
  ← مجموع Dr = مجموع Cr = صفر (validation)

مرحله ۵: ذخیره در Ledger
  ← external_ref | date | status=pending | entries: [{account, dr_cr, amount}]
  ← پس از human review → status=posted

خروجی نهایی: فقط entries با status=posted وارد گزارش‌ها می‌شوند
```

## ۴.۲ خروجی (Reports — فقط از posted entries)

```
۱. Trial Balance (تراز آزمایشی)
   همهٔ account ها با جمع debit و credit
   شرط صحت: Σ debit = Σ credit

۲. Profit & Loss (صورت سود و زیان)
   Revenue (4000-4090) - COGS (5000-5090) - Expenses (6000-6090)
   = Net Profit/Loss

۳. Balance Sheet (ترازنامه)
   Assets (1000-1990) = Liabilities (2000-2990) + Equity (3000-3990)

۴. Partner Capital Report
   Armin Capital = initial + share_of_profit - drawings
   Abbas Capital = initial + share_of_profit - drawings

۵. Job Profitability (اگر job code داری)
   Per project: Revenue - Materials - Labor - Subcontractor = Margin

۶. Tax Summary
   GST collected (on revenue) - GST paid (on expenses) = net GST
```

---

# ۵. پیشنهادات مشخص (بدون تغییر فایل)

## ۵.۱ معماری هدف (To-Be)

```
DataSource (PocketSmith API + CSV)
        │
        ▼
┌───────────────────────────┐
│  Input Pipeline           │
│  - dedup (external_ref)   │
│  - enrich (agent mapping) │
│  - classify (rules → AI)  │
│  - propose double-entry   │
└───────────┬───────────────┘
            │
            ▼
┌───────────────────────────┐
│  Review Queue             │
│  - AI confidence < 90%    │
│  - new payee              │
│  - amount anomaly         │
└───────────┬───────────────┘
            │ (human approves)
            ▼
┌───────────────────────────┐
│  IMMUTABLE LEDGER         │
│  - transaction_id         │
│  - external_ref           │
│  - date                   │
│  - status: posted         │
│  - entries[]:             │
│    {account, dr_cr, amt}  │
│  - Σ entries = 0          │
└───────────┬───────────────┘
            │
            ▼
┌───────────────────────────┐
│  Report Engine            │
│  - Trial Balance          │
│  - P&L                    │
│  - Balance Sheet          │
│  - Partner Capital        │
│  - /finance Telegram      │
└───────────────────────────┘
```

## ۵.۲ پرامپت‌های پیشنهادی برای AI Categorizer

### پرامپت اصلی (سیستم):

```
You are an accounting assistant for a painting/construction business in Australia.

CHART OF ACCOUNTS:
[درج COA کامل از بالا]

KNOWN AGENTS:
- Armin: business partner/owner → equity accounts 3000-3010
- Abbas: business partner/owner → equity accounts 3100-3110
- Behzad: subcontractor/painter → COGS account 5010
- Maliheh: subcontractor/painter → COGS account 5020
- Sume Asadi: subcontractor/painter → COGS account 5030
- Various suppliers (paint shops, hardware) → COGS 5000 or Expense 6000s
- Various clients → Revenue 4000s
- Rent/landlord → Expense 6000

RULES (apply before AI suggestion):
1. If description contains known subcontractor name → COGS 50xx
2. If amount is round and from known client → Revenue 4000
3. If description contains "rent" → Expense 6000
4. If transfer between Armin and Abbas accounts → check context:
   - Regular similar amounts →可能是 profit distribution (Equity)
   - Large one-off →可能是 loan (Due to/from)
   - Small irregular →可能是 reimbursement
5. Salary/wage payments → 7 specific transactions already identified
```

### پرامپت هر تراکنش:

```
TRANSACTION:
  External Ref: {external_ref}
  Date: {date}
  Bank Account: {bank_account_name}
  Amount: {amount_cents} cents ({sign})
  Description: {description}

TASK:
1. Identify the economic event type (sale, purchase, payment, receipt, transfer)
2. Identify ALL agents involved (who pays, who receives, who benefits)
3. Propose double-entry (at least 2 entries):
   DR: [account_code] [account_name] $[amount]
   CR: [account_code] [account_name] $[amount]
4. Confidence: HIGH (>90%) / MEDIUM (70-90%) / LOW (<70%)
5. Reasoning (1 sentence)

VALIDATION: DR total must equal CR total.
```

---

# ۶. اولویت‌بندی اقدامات (اگر تصمیم به بازسازی گرفتی)

| اولویت | اقدام | دلیل |
|--------|-------|------|
| 🔴 P0 | ساخت COA (نمودار حساب) | پایهٔ همهٔ طبقه‌بندی‌های بعدی |
| 🔴 P0 | پیاده‌سازی double-entry ledger | books باید بالانس شود |
| 🔴 P0 | تفکیک entity از agent | دیگر «owner» را با «bank account holder» اشتباه نگیری |
| 🟡 P1 | Immutable ledger با pending→posted | Modern Treasury standard |
| 🟡 P1 | Dedup بر اساس external_ref | جلوگیری از double-counting |
| 🟡 P1 | تعریف دقیق transfer | چه زمانی transfer است و چه زمانی یک رویداد اقتصادی |
| 🟢 P2 | Job costing | سودآوری هر پروژه |
| 🟢 P2 | STP-style payroll tracking | اگر کارگرها employee هستند |
| 🔵 P3 | Rule-first categorization | AI فقط برای ambiguous cases |

---

# ۷. نتیجهٔ نهایی

سیستمی که ساختید **برای prototype عالی است** — ۷ ماژول، ۴۰+ تست، اتصال زنده، propose-only با human-in-the-loop. این از ۹۰٪ پروژه‌های مشابه جلوتر است.

اما برای ورود به **production accounting** (یعنی جایی که پول واقعی و مالیات واقعی مطرح است)، ۳ کمبود بنیادین دارد:

1. **Double-entry ledger** — بدون این، books قابل ممیزی نیست
2. **Chart of Accounts** — بدون این، طبقه‌بندی بی‌معناست
3. **Entity/Agent separation** — بدون این، نمی‌دانی پولِ کی برای چی خرج شد

این ۳ تا اگر درست شوند، بقیه روی همان پایه سوار می‌شوند.

---

# منابع

- Modern Treasury, "Accounting for Developers, Part I-III" (2025)
- Modern Treasury, "Enforcing Immutability in your Double-Entry Ledger" (2021)
- Modern Treasury, "How to Scale a Ledger, Parts I-VI"
- DualEntry Labs, "AI Still Fails One-Third of Real Accounting Tasks" (March 2026)
- McCarthy, W.E., "The REA Accounting Model: A Generalized Framework" (The Accounting Review, 1982)
- GS Advisory, "Accounting for Painting Business in Australia" (2024)
- ConcreteBK, "The Ultimate Chart of Accounts for Painting Businesses"
- ATO, "Single Touch Payroll" & "Record Keeping for Small Business"
- Deltek, "Job Costing in Construction" (2026)
