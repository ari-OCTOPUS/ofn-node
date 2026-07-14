# ⛏️ Mining — نقشهٔ ایجنت (اول این را بخوان)

> شکار کوین‌های نوظهور CPU/ARM-پذیر با ناوگان Orange Pi 5 Pro + ESP32.
> tenant #3. معیار: **survival-based** (D2)، نه payback.

## 🎯 ماموریت
آزمایش بلندمدت mine-and-hold کوین‌های تازه‌لانچ، زیرِ قیدِ برق (<$0.05/kWh یا خورشیدی).

## ⚠️ قیود حاکمیتی (D-سری)
- **D2:** مرگ = فقط death-watch (dev مرده/زنجیره متوقف/جامعه خالی). payback/نقدشوندگی = فیلد اطلاعاتی.
- **D-10:** execution مالی HARD_STOP — فقط INFORM.
- **D-20:** SSH مستقیم ممنوع — فقط repo+deploy gate.
- **D-11:** دسترسی کیف پول ممنوع.

## 📦 جعبه‌های سیاه
| Organ | نقش | وضعیت |
|---|---|---|
| **SCOUT-B** | ۲۵ الگوی ARM mining (hashrate-per-watt، الگوریتم، orchestration) | ✅ پژوهش کامل |
| **Coin Scouting** | چارچوب + قالب death-watch | ✅ تعریف‌شده |
| **Coin Hunter Bot** | GemHunter→Forensics→Veto→LLM→Kelly | 🟡 PDF README، کد در `_code/` |
| **Fleet Manager** | REST :7700 + worker + watchdog + oracle | 🟡 کد موجود، ۳ شکاف |
| **Orange Pi Hub v2** | ESP32→OPi5→VPS (Podman/Nomad) | 🟡 طراحی نهایی، deploy نشده |

## 🔌 اتصال
- **قرارداد:** `MANIFEST.yaml` · **رابط:** `contracts/adapter.yaml`
- **اشتراکی با Crypto:** fleet_manager + coin_hunter_bot (L7↔L3)

## 🗂️ ساختار پوشه
```
Mining/
├── README.md / MANIFEST.yaml / contracts/adapter.yaml
├── PROJECT.md / INDEX / DecisionLog / OpenQuestions
├── Mining.md                   ← لاگ تلگرام (۴۳۵۵ خط)
├── Coin Scouting Framework.md  ← معیار + death-watch
├── Hardware Registry & Runbook.md ← رجیستری ناوگان (همه [To measure])
├── 01 - Docs/                  ← Strategy (۷ PDF)، Bot System (۳ PDF)، Orange Pi arch
├── 03 - Rigs/                  ← Hcash، Mining E، Verus cluster
├── 04 - Research/              ← SCOUT-B + Quantum dataset (۷ PDF)
├── data/photos/                ← ۵ عکس (۱۴ و ۲۷ ژانویه ۲۰۲۶)
└── _archive/                   ← shortcuts
```

## 🔗 خواهرها
- **Accounting:** کوین mined → business income (AUD لحظهٔ دریافت).
- **Crypto:** fleet + coin_hunter مشترک.
