# 🌸 Ziman Galerry — نقشهٔ ایجنت (اول این را بخوان)

> بیزنسِ هدیهٔ محلیِ سیدنی. تیمِ دونفره: آری (مارکتینگ) + مادر (تولید).
> **وضعیت:** فاز validation — صفر فروش ثبت‌شده. همه‌چیز propose-only.

## 🎯 ماموریت
تبدیلِ گل‌آراییِ مصنوعی و شادوباکس به برندِ هدیهٔ لوکسِ سیدنی، زیرِ **سقفِ ظرفیت (D4)**: اول ظرفیت، بعد کمپین.

## 📦 جعبهٔ سیاه چیست؟
این پروژه **یک organ زندهٔ تست‌شده** دارد که کدش منتقل شده (`control-brain/` + `ziman-agent/`):

| Organ | نقش | وضعیت | کجاست |
|---|---|---|---|
| **control-brain** | مغز: روشن/خاموش/تست/RBAC | ✅ ۲۱ تست سبز | `_code/` یا `_launchpad/ziman-live/` |
| **ziman-agent** | ورکر مارکتینگ + گارد D4 | ✅ ساخته‌شده | همان |
| **video engine** | کیت ویدیوی Higgsfield (۱۰ روش) | 🟡 کیت آماده، عکس نیازمند | `content/higgsfield-video-kit-2026-07-07.md` |
| **funnel tracker** | تراکر قیف فروش | 🟡 قالب آماده، دیتا صفر | `content/Ziman-FirstSale-Tracker.xlsx` |

## 🔌 اتصال به مغزِ مرکزی
- **قرارداد ماشین‌خوان:** `MANIFEST.yaml`
- **رابط API (read-only):** `contracts/adapter.yaml`
- **autonomy floor:** propose-only (تا Security Gate باز شود)

## 🗂️ ساختار پوشه
```
Ziman Galerry/
├── README.md              ← تو اینجایی
├── MANIFEST.yaml          ← قرارداد جعبهٔ سیاه
├── PROJECT.md             ← شناسنامه + Active Context
├── INDEX.md               ← MOC (نقشهٔ محتوا)
├── DecisionLog.md         ← تصمیمات + دلیل
├── Strategy-DecisionLog.md ← تصمیمات استراتژیک مارکتینگ
├── OpenQuestions.md       ← مجهول‌ها
├── TODO.md                ← اقدامات باز
├── contracts/adapter.yaml ← رابط API
├── docs/                  ← اسناد: سیستم، runbook، معماری، بیزنس
├── content/               ← خروجی‌ها: first-sale-pack، video kit، tracker
└── Ziman-System.canvas    ← بورد بصری Obsidian
```

## ⏭️ قدم بعدی (owner)
1. **ثبت عدد ظرفیت** در `docs/Capacity-and-Channels.md` (فعلاً ۳۰ [Measured] از Business-Zeiman).
2. **پیدا کردن کد** (`control-brain/` + `ziman-agent/`) — احتمالاً در `_code/` یا `F:\backup`.
3. **عکس محصول** برای video engine.
4. **توکن تلگرام** (BotFather) + کلید Claude (KeePassXC).

## 🔗 خواهرها
- **Accounting:** درآمد فروش → business income + COGS.
