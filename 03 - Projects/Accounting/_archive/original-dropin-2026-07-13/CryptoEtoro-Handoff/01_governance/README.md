# 📈 Crypto - etoro — نقشهٔ ایجنت (اول این را بخوان)

> مدیریت پرتفوی eToro + تحقیق داده‌محور. **Tenant لاغر** روی مغز مادر (langar).
> **وضعیت:** معماری کامل، داده کهنه، اجرا paper-only.

## 🎯 ماموریت
تصمیم‌گذاری بهتر با تحقیق داده‌محور — زیرِ حاکمیت سخت: **BUY همیشه انسانی؛ SELL خودکار فقط از exit_rules.**

## ⚠️ قواعد ثابت (Standing Rules)
1. رویداد باینری → trim به ۲-۳٪ (اگر exit_rules ثبت شده).
2. **BUY فقط انسانی** — ایجنت فقط evidence جمع می‌کند.
3. SELL خودکار فقط از exit_rules + ۳ شرط (Gate + Ledger + Telegram).
4. کلیدهای exchange: **off-box، صفر LLM** (D-11).
5. مسیر اجرای خودکار وجود ندارد → alert-only.
6. cross-model check قبل از ارائه به انسان (D-09).

## 📦 جعبه‌های سیاه
| Organ | نقش | وضعیت |
|---|---|---|
| **QuantumAlphaBot** | L3 scouting: GemHunter→Forensics→Veto→LLM→Kelly | 🟡 ساخته‌شده ولی EdgeClassifier سیم‌نشده → NO_ACTION |
| **Sentinel** | ingestion: CryptoQuant/LunarCrush/Coinalyze | 🟡 ساخته، کلیدها rotated out |
| **Fleet Manager** | L7: REST :7700 + worker + oracle | 🟡 مشترک با Mining، ۳ شکاف |
| **Coordinator** | confluence: QA×0.45+Sent×0.55، ۶ gate | 🟡 ساخته، propose-only |
| **Portfolio Registry** | پوزیشن‌ها + exit_rules | ❌ **خالی** |

## 🔌 اتصال
- **قرارداد:** `MANIFEST.yaml` · **رابط:** `contracts/adapter.yaml`
- **وابسته به langar** (مغز مادر — غایب در اینجا، در `04-Architect System`).

## 🗂️ ساختار پوشه
```
Crypto - etoro/
├── README.md / MANIFEST.yaml / contracts/adapter.yaml
├── PROJECT.md / INDEX / DecisionLog / OpenQuestions
├── Standing Rules.md            ← ۶ قاعدهٔ ثابت معاملات
├── Portfolio Registry.md        ← ❌ خالی (پر کردن = مالک)
├── Research Template.md         ← قالب تحقیق
├── Crypto - etoro.md            ← لاگ تلگرام (۱۸۱KB)
├── CRYPTO_ARCHITECTURE_v1.md    ← Tenant لاغر L0-L9
├── docs/                        ← L3/L7 design، Data Stack، PDFs (۹)، OrangePi Hub
├── data/                        ← عکس‌ها
└── archive/raw-data-2026-06/    ← ~110MB داده کهنه + summaries
```

## ⚠️ نکته
`docs/MISFILED-spacing_x_expectancy_protocol.md` یک طرح علمی self-suggestion است که ربطی به کریپتو ندارد — احتمالاً اشتباهاً اینجاست.

## 🔗 خواهرها
- **Accounting:** CGT رویدادها → شخصی (نه Pty Ltd).
- **Mining:** coin_hunter_bot + fleet مشترک (siblings).
