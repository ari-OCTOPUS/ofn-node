# 💰 Accounting — نقشهٔ ایجنت (اول این را بخوان)

> قلبِ مالیِ اکوسیستم. جایی که درآمد **همهٔ** پروژه‌ها تجمیع و برای ATO آماده می‌شود.
> tenant #1 (ترتیب D-26: Accounting → Lead → Mining).
> **وضعیت:** manifest کامل، اجرا صفر. هیچ دفتری زنده نیست.

## 🎯 ماموریت
دفاتر audit-ready برای Pty Ltd، تا آری بتواند قراردادهای بزرگ‌تر بگیرد.

## ⚠️ دو بلاکر حیاتی (فقط مالک)
1. **انتخاب حسابدار** — بدون او هیچ قاعدهٔ `[Unverified]` تأیید نمی‌شود.
2. **تصمیم ساختار:** یک Pty Ltd یا چند شرکت برای نقاشی/ماینینگ/Project-F؟

## 📦 جعبهٔ سیاه چیست؟
این پروژه هنوز **کد اجرایی ندارد** ولی **طراحیِ کاملِ red-team‌شده** دارد. دادهٔ خام غنی موجود:

| Organ | نقش | وضعیت |
|---|---|---|
| **ANZ CSV importer** | بزرگ‌ترین کاهش کار دستی (بانک→draft→verdict) | طراحی v1.1، ساخته‌نشده |
| **compliance monitor** | Div 7A / no-ABN / BAS-due اسکن | طراحی، ساخته‌نشده |
| **receipt OCR** | عکس→draft (۴ عکس خاموش در data/) | طراحی، ساخته‌نشده |
| **raw ledgers** | ۶ فایل xlsx (PII) | موجود، فقط-ساختار استخراج شد |
| **Tax research** | Tax Map + Loan Guide + Architecture | ✅ کامل و citeشده |

## 🔌 اتصال به مغز مرکزی
- **قرارداد:** `MANIFEST.yaml`
- **رابط:** `contracts/adapter.yaml`
- **نقشهٔ جریان پول:** `docs/Ecosystem-Rollout-Plan.md §2` (mermaid)

## 🗂️ ساختار پوشه
```
Accounting/
├── README.md              ← تو اینجایی
├── MANIFEST.yaml          ← قرارداد جعبهٔ سیاه
├── PROJECT.md             ← شناسنامه + رجیستر انطباق
├── INDEX.md / DecisionLog.md / OpenQuestions.md
├── Accounting.md          ← لاگ تلگرام (۴۳۴ خط — PII)
├── contracts/adapter.yaml ← رابط API + tax touchpoints
├── docs/                  ← Tax Map, Loan Guide, Architecture, Rollout
└── data/
    ├── حساب کتاب/          ← ۶ فایل xlsx (PII) + نوت‌های ساختاری
    └── receipts/           ← ۴ عکس رسید
```

## 🔗 جریان پول (قلب اکوسیستم)
- **Lead-نقاشی** → business income + GST (منبع اصلی)
- **Mining** → crypto at AUD value + electricity (INFORM only)
- **Crypto-eToro** → CGT شخصی (احتمالاً نه Pty Ltd)
- **Project-F** → ۵۰٪ سهم آری، کد «Project-F» (privacy)
- **Ziman** → income + COGS
