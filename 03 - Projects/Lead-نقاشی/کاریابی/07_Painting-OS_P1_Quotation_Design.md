# Painting-OS — P1 Quotation Design (پایه + ایراد + پرامپت‌های تحقیقاتی)

> **تاریخ:** 2026-07-12  
> **وضعیت:** ✅ P1 ساخته‌شده · propose-only · فلگ‌خاموش  
> **کامیت:** `de16794` (worktree) · `reconcile v2` در `_ops/budget/`  
> **تست‌ها:** ۲۳/۲۳ سبز (pricing 10 + lead_quote 9 + lead_draft 4)  
> **بستر:** LeadLeg + attribution + reconcile (کد موجود) + OPS-01 Framework (مشخصات)  

---

## ۱. خلاصهٔ عملگرا

**ستونِ فقرات:** کل محصول روی `attribution_id` سوار است. چهار موجودیتِ نو فقط «سند»اند؛ پول همان `attribution`+`reconcile` است. PAID مشتق از reconcile است، هرگز ذخیره نمی‌شود.

| پایه | ماژول | فلگ |
|---|---|---|
| کوتیشن | `lead_quote.py` (توسعهٔ lead_draft) | `LEAD_QUOTE_LIFECYCLE` |
| اینویس | `invoice.py` (شمارهٔ `INV-FY…`) | `OCTOPUS_WIRE_INVOICE` |
| کشفِ لید | `lead_discovery.py` (رضایت‌محور) | `OCTOPUS_WIRE_LEAD_DISCOVERY` |
| ایمیل | `email/{inbound,outbound}.py` | `OCTOPUS_WIRE_EMAIL` |

**اولویت:** P1 کوتیشن → P2 اینویس → P3 ایمیلِ inbound فقط‌خواندنی

---

## ۲. گردشِ پولِ موجود (تأییدشده با تست)

```
Telegram /lead → intake → attribution.propose (PROPOSAL)
    → lead_draft.build_and_persist → ±15% band → JSON file
    → human sends → mark_sent → claim (CLAIMED)
    → human drops CSV → reconcile.run → 4-gate → confirm (CONFIRMED+ATTRIBUTED)
    → fitness reads confirmed_revenue
```

---

## ۳. P1 — کوتیشنِ واقعی

### آنچه دارد
- `LeadLeg.draft_quote()` — موجود اما scope فقط string ساده
- `lead_draft.build_and_persist()` — موجود اما ±15% band بدون منطق قیمتی
- `OPS-01_quoting_estimation_framework.md` — مشخصاتِ کاملِ قیمتی (نرخ‌ها، متغیرها، فرمت)

### آنچه باید ساخته شود

#### 3.1 `QuoteIntake` (dataclass — در `lead_quote.py`)
```python
@dataclass(frozen=True)
class QuoteIntake:
    scope: str               # max 500 chars
    size_m2: float           # متر مربع
    surface_condition: str   # "good" | "fair" | "poor"
    prep_level: str          # "minimal" | "standard" | "heavy"
    access_type: str         # "ladder" | "scaffold" | "swing_stage"
    segment: str             # "residential" | "strata" | "pm" | "builder" | "commercial"
    paint_quality: str       # "standard" | "premium" | "trade"
    coat_count: int          # 1, 2, 3
    risk_flags: list[str]    # ["lead_paint", "asbestos", "heritage"]
    timeline: str            # "asap" | "flexible" | "fixed_date"
```

#### 3.2 `pricing.py` (جدید — CONFIG-driven)
```python
def estimate_price(intake: QuoteIntake) -> PriceBreakdown:
    """Returns PriceBreakdown with line_items, total_range, assumptions."""
    # نرخ‌ها از CONFIG: PRICING_RATES
    # ضریب‌ها: prep_level ±30%, access +15%, risk +20%
    # خروجی: {(lo, hi), line_items, assumptions_auto}
```

- نرخ‌های پایه از `.env` / `CONFIG` (نه hardcode)
- ماتریس: `{interior|exterior} × {standard|premium} × {segment}`
- بازه: همیشه `(lo, hi)` — هرگز عددِ قطعی

#### 3.3 `lead_quote.py` (توسعهٔ lead_draft)
```python
def create_quote(leg, intake: QuoteIntake, ...) -> dict:
    """intake → pricing → Proposal → persist → return"""

def revise_quote(attribution_id, changes: dict) -> dict:
    """نسخهٔ جدید: QT-YYYYMMDD-002 (append-only, old preserved)"""

def render_quote_html(rec: dict) -> str:
    """خروجی قابل‌خواندن برای Telegram"""

def quote_history(attribution_id) -> list[dict]:
    """تمام نسخ‌های یک کوتیشن"""
```

- شماره‌گذاری: `QT-{YYYYMMDD}-{NNN}` (پشتِ attribution_id)
- ذخیره: همان `state/legs/lead-drafts/{safe-id}.json`
- هر نسخهٔ قدیمی حفظ می‌شود (append-only)

#### 3.4 تغییر `lead_leg.draft_quote()`
- پذیرشِ payload ساختاریافته (به‌جای scope:string)
- سازگار با عقب: اگر scope ساده رسید، رفتار قبلی حفظ می‌شود

---

## ۴. ایراداتِ صادقانه

### 🔴 بزرگ‌ترین ریسک: پرداخت بیعانه + مابقی
**مشکل:** `reconcile.py` مقدارِ دقیق تطبیق می‌دهد. `attribution.claim()` فقط یک `amount_aud` می‌گیرد. اگر مشتری بیعانه + مابقی بدهد، CSV باید دو ردیف باشد.

**راه‌حل A (توصیه‌شده):** تغییر reconcile — جمعِ ردیف‌های CSV با یک lead_id → `~10 خط تغییر`

**راه‌حل B:** قابلیت partial claim در attribution → پیچیده‌تر

**راه‌حل C:** هر بیعانه attribution_id جداگانه → کثیف

### 🟡 PII در git
هر مسیرِ نو باید قبل از نوشتن در `.agentignore` و `.gitignore` ثبت شود.

### 🟡 رازِ Gmail
خطرناک‌ترین راز — فقط OAuth readonly. ارسال ایمیل → پشتِ تحقیق.

### 🟡 ABN / GST
از CONFIG نه hardcode. `BUSINESS_ABN` و `GST_RATE` در `.env`.

### 🟡 رضایتِ outreach
$250k جریمه — گارد بینِ کشف و ایمیل.

---

## ۵. نتایجِ تحقیق (۲۰۲۶-۰۷-۱۲)

### ساختار کوتِ AU
- فرمت استاندارد: header (business name, ABN, quote#) + scope + line items + GST + terms
- Residential معمولاً price all-inclusive؛ Commercial جدا labor vs material
- اعتبار: ۳۰–۹۰ روز
- **NSW Home Building Act §8:** بیعانه نهایتاً **۱۰٪** از کل قرارداد
- >AUD 5,000: قرارداد کتبی الزامی، Consumer Building Guide

### نرخ‌های سیدنی (AUD/m²)
| نوع | standard | premium |
|---|---|---|
| Interior wall | $18–30 | $30–45 |
| Interior ceiling | $20–35 | $35–50 |
| Exterior wall | $22–40 | $40–65 |
| Hourly rate | $65–95/hr | $65–95/hr |
| Per room (interior) | $400–1,200 | — |

**Sources:** [hipages](https://hipages.com.au/article/how_much_do_painters_cost), [service.com.au](https://www.service.com.au/articles/painters/how-much-does-house-painting-cost), [painters.edu.au](https://painters.edu.au/Consumer-Information/House-painting-cost-calculator.htm), [thequoteyard.com.au](https://www.thequoteyard.com.au/services/painter-pricing-guide-2026-nsw)

### ATO Tax Invoice
- عبارت "Tax Invoice" الزامی (اگر GST registered)
- ABN الزامی · >$1,000: ABN یا نام خریدار الزامی
- GST 10% روی تمام sales > $82.50
- پاسخ ظرف ۲۸ روز
- اگر GST registered نیست: "Invoice" نه "Tax Invoice"

### Gmail OAuth
- Scope: `https://www.googleapis.com/auth/gmail.readonly` (least-privilege)
- Free tier: 1B quota units/day; 250/sec/user
- Internal app (under 100 users): "Testing" status → بدون verification
- **توصیه:** Google Cloud project + OAuth consent screen = "Testing" + readonly scope

### P-R1: ساختار و ترمِ کوتِ AU
> در صنعت نقاشی ساختمان سیدنی 2026، ساختار استانداردِ کوتیشن شامل چه ردیف‌هایی است؟ تفکیک labor vs material رایج است؟ آیا quoting per room یا per m² رایج‌تر؟ حداکثرِ بیعانه قانونی NSW چند درصد است و آیا باید separate invoice برای بیعانه صادر شود؟

### P-R2: نرخ‌های بازارِ سیدنی 2026
> نرخ‌های فعلی نقاشی ساختمان سیدنی 2026 (interior wall, exterior, ceiling) per m² چقدر است؟ آیا rate card استانداردی از Master Painters Association NSW وجود دارد؟ تأثیر prep level, access type, و paint quality روی قیمت چند درصد تخمین زده می‌شود؟

### P-R3: الزاماتِ tax-invoiceِ ATO
> الزامات ATO برای tax invoice در NSW 2026 چیست؟ آیا از Xero/QuickBooks API می‌شود invoicing را مدیریت کرد یا build از صفر ساده‌تر است؟ قالبِ ABN + GST در invoice چه شماره‌گذاری دارد؟

### P-R4: اتصالِ امنِ Gmail
> ایمن‌ترین راه اتصالِ Gmail (فقط خواندن) در 2026 چیست؟ OAuth2 + Google API vs App Password؟ آیا免费 rate limit کافی برای business است یا نیاز به Workspace دارد؟

---

## ۶. بوتوم‌لاین

واقعی و شدنی — چون بیشترش **سیم‌کشیِ ماشینی است که ارگانیسم از قبل دارد**، نه ماشینِ نو. با P1+P2 و ارسالِ دستی + CSVِ reconcile، درآمدِ واقعیِ end-to-end بدونِ رازِ نو و بدونِ اتوماسیون داری.

**تصمیم‌های موردِ نیاز از مالک:**
1. ~~مدلِ بیعانه/پرداختِ جزئی؟~~ ✅ راه‌حل A: reconcile v2 — جمع CSV ردیف‌ها
2. ~~از P1 (کوتیشن) شروع کنم بسازم؟~~ ✅ ساخته‌شده (`de16794`)

**قدم بعدی:** P2 (اینویس) یا اتصالِ `/lead` تلگرام به `create_quote` (intake ساختاریافته)
