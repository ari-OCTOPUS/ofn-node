# 🎨 Lead-نقاشی — نقشهٔ ایجنت (اول این را بخوان)

> **منبع درآمد اصلی آری** — بیزنس نقاشی/renovation ساختمان در سیدنی.
> tenant #2 (D-26). معیار موفقیت: **لید واقعی، نه کلیک.**

## 🎯 ماموریت
لیدگیری برای بیزنس نقاشی با آزمایش‌های کنترل‌شده (یک‌در‌هر‌زمان)، برای segments: residential / strata / builder.

## 🖌️ Painting-OS — محصول اصلی (P1-P3 ساخته شده ✅)

سیستم یکپارچه: **لید → کوتیشن → فاکتور → ایمیل** — مخصوص نقاشی سیدنی.

| ستون | فایل | وضعیت |
|------|------|--------|
| **P1 کوتیشن** | `_ops/legs/pricing.py` + `lead_quote.py` | ✅ 19 تست |
| **P2 فاکتور** | `_ops/legs/invoice.py` | ✅ 8 تست |
| **P3 ایمیل** | `_ops/legs/email_inbound.py` | ✅ 9 تست |
| **reconcile v2** | `_ops/budget/reconcile.py` | ✅ partial payment |
| **intake پارس** | `_ops/tests/test_lead_intake.py` | ✅ 6 تست |
| **مجموع** | **42 تست سبز** | ✅ |

**نقشهٔ راه ۱۰ مرحله‌ای:** `کاریابی/08_Painting-OS_Roadmap_v2.md`
**طراحی P1:** `کاریابی/07_Painting-OS_P1_Quotation_Design.md`

### رقبای بازار (تحقیق‌شده)
| ابزار | قیمت | نقطهٔ ضعف |
|--------|-------|----------|
| ServiceM8 | $0-79/ماه | بدون AI، بدون لید |
| Tradify | ~$70-80/یوزر/ماه | گران، بدون AI |
| QuoteIQ | $150-700 USD/ماه | آمریکایی، بدون AU |
| hipages | $129+/ماه + $20-50/لید | فقط لید، بدون ابزار |

**مزیت Painting-OS:** $0 + مالکیت کامل + یکپارچه + AU-calibrated.

### مراحل بعدی (روoadmap)
1. وایر `/lead` تلگرام → کوتیشن با نرخ واقعی
2. ABN واقعی → فاکتور واقعی ATO-compliant
3. Gmail OAuth E2E → ایمیل → لید → کوتیشن
4. فرم/وب‌سایت → مشتری → سیستم
5. PDF کوتیشن حرفه‌ای
6. فاکتور خودکار + ارسال
7. پیگیری کوتیشن (day 3, day 7)
8. داشبورد `/dash` تلگرام
9. SEO + Google Business Profile
10. قیمت‌گذاری پیشرفته (یادگیری از داده)

## 📦 سه زیرمغز (هرکدام جعبهٔ سیاه مستقل)

| Organ | نقش | وضعیت | کد کجاست |
|---|---|---|---|
| **Painting-OS** | کوتیشن + فاکتور + ایمیل + لید | ✅ P1-P3 DONE | `_ops/legs/` |
| **Brushline** | lead-gen/marketing: ۶ Worker + Gate + Queue | ✅ ۸/۹ فاز DONE | `_code/` (AiFarm-Lead) |
| **کاریابی bot** | ربات مناقصه دولتی NSW (۳ منبع) | ✅ ۳۳ تست سبز، خاموش | `_code/` (کاریابی/bot) |
| **Hunter** | کشف خودکار کانال‌های جدید | 🟡 فقط پرامپت | ساخته‌نشده |

## 🔌 اتصال
- **قرارداد:** `MANIFEST.yaml` · **رابط:** `contracts/adapter.yaml`
- **۳ invariant Brushline:** INV-1 (no publish without approve) · INV-2 (PII hash) · INV-3 (kill+cap+audit)

## 🗂️ ساختار پوشه
```
Lead-نقاشی/
├── README.md / MANIFEST.yaml / contracts/adapter.yaml
├── PROJECT.md / INDEX / DecisionLog / OpenQuestions
├── HANDOFF.md                         ← دستورالعمل ایجنت بعدی
├── کاریابی/
│   ├── 07_Painting-OS_P1_Quotation_Design.md
│   └── 08_Painting-OS_Roadmap_v2.md   ← نقشهٔ راه ۱۰ مرحله‌ای
├── Lead Pipeline & Experiments.md
├── Lead-نقاشی.md                      ← لاگ تلگرام
├── AiFarm-Lead/                       ← Brushline معماری
├── کاریابی/                           ← ربات مناقصه
├── docs/                              ← Sydney Channels, Outreach, KB
└── data/portfolio/                    ← ۱۵۹ عکس پروژه
```

## 🔗 خواهرها
- **Accounting:** درآمد نقاشی → business income + GST (منبع اصلی قلب مالی).
