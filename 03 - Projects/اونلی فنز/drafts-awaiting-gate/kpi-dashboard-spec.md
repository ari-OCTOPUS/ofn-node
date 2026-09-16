---
type: draft
status: draft-awaiting-gate
gate: بدون گیت — ساخت داخلی مجاز؛ فقط دادهٔ زنده پس از launch
created: 2026-07-10
tags: [project-f, draft, kpi, dashboard]
---

# اسپک KPI Dashboard — draft-awaiting-gate

> منبع حقیقت: فایل/شیت داخل Fable5 (مصوب: تا اتصال Notion/monday، markdown/sheet محلی). آپدیت: جمعه‌ها ≤۳۰ دقیقه (حلقهٔ مصوب منشور). صفر PII فن — فقط تجمیعی و nickname مستعار.

## ۱. جدول هفتگی (ستون‌ها)
`هفته | پست R | پست X | med-upvote | کلیک hub | کلیک OF (per-link) | free-subs تجمعی | خریدار جدید | unlock% | درآمد PPV | درآمد custom | درآمد tip | rebill% | ساعت promo | ساعت DM | $/h | هزینهٔ stack | یادداشت آزمایش`

## ۲. آستانه‌های hard-coded (تصمیم احساسی ممنوع)
| متریک | سبز | زرد | قرمز (اقدام) |
|---|---|---|---|
| کلیک تجمعی (هفتهٔ ۶) | ≥۲۰۰ | ۱۰۰–۲۰۰ | <۱۰۰ → تغییر mix کانال |
| click→follow | ≥۱۰٪ | ۵–۱۰٪ | <۵٪ → بازطراحی landing |
| unlock-rate | ۱۵–۲۵٪ | ۱۰–۱۵٪ | <۵٪ دو هفته → بازقیمت‌گذاری |
| delivery صبا | ≥۸۰٪ | ۵۰–۸۰٪ | <۵۰٪ ×۲ متوالی → گفت‌وگوی ساختار (R1) |
| free→paid (هفتهٔ ۱۲) | ≥۵٪ | ۲–۵٪ | <۲٪ → بازبینی مدل |
| warning پلتفرم | ۰ | — | هر ۱ = kill-switch همان کانال |

## ۳. Experiment Log (۶ ستون)
`ID | فرضیه | متغیر (فقط یکی) | بازه (≥۲ هفته) | آستانهٔ از-پیش-ثبت | نتیجه/تصمیم`

## ۴. سه نمودار (بیشترش زینت است)
1. Funnel هفتگی: کلیک → free-sub → خریدار
2. درآمد تجمعی vs خط G2 ‏(A$100)
3. روند unlock-rate با باند ۱۰–۲۵٪

## ۵. SOP جمعه (۳۰ دقیقه)
export دستی OF/Fansly/GAML/Social Rise → پر کردن ردیف → چک آستانه‌ها → ۳ خط گزارش به صبا (تعهد §۴.۱ بلوپرینت: حتی اگر صفر) → ثبت هر انحراف در OpenQuestions/DecisionLog → ورودی هفتگی Langar ‏(/report).
