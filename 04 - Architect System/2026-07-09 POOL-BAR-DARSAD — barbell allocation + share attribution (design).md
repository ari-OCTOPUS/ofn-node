---
type: architecture-plan
project: "[[04 - Architect System/architect/PROJECT]]"
status: proposal
autonomy: propose-only
created_by: agent (interactive)
sources:
  - "[[04 - Architect System/2026-07-09 OCTOPUS-GOAL-MAP — ecosystem strategy (from raw project data)]]"
  - "verdict آری 2026-07-09: Ziman + Project-F = دو شاخکِ اصلیِ درآمد؛ GLM+Fugu = دو مغز؛ بامبو/ریسک‌پذیرِ متعادل"
tags: [octopus, allocation, barbell, attribution, share, governor, propose-only]
created: 2026-07-09
updated: 2026-07-09
---

# 💰 پول‌بر‌درصد — تخصیصِ barbell + انتسابِ سهم (طراحی)

> فلسفهٔ Ari: «عینِ بامبو، یک درصد باید جایی بیرون بزند؛ پس کل سیستم ریسک‌پذیر ولی متعادل.» این طراحی، همان را به مکانیزمِ عینیِ **تخصیص + انتساب** تبدیل می‌کند. propose-only؛ فعلاً تخصیصِ **کوشش/API** نه پولِ واقعیِ بیزنس (که تا capability∧approval قفل است).

---

## ۰. «پول‌بر‌درصد» یعنی دو چیز
1. **تخصیص (allocation):** منبعِ کمیاب (بودجهٔ API، کوشش، توجهِ موجود) به‌صورتِ **درصد** بینِ شاخک‌ها پخش می‌شود — نه مساوی، بلکه barbell.
2. **انتساب (attribution):** هر AUDِ واقعیِ نشسته به **شاخک + سهمِ شریک (٪)** نسبت داده می‌شود (مثلِ Project-F ۵۰/۵۰ صبا). این «درصدِ سهم» را از حرف به عدد تبدیل می‌کند.

---

## ۱. ساختارِ barbell (ریسک‌پذیر ولی متعادل)
دو سر، وسطِ خالی:

| سر | ٪ اولیه | چه‌کسی | منطق |
|---|---|---|---|
| 🟢 **CORE (امن/اثبات‌نزدیک)** | ~۷۰٪ | **Ziman + Lead-نقاشی** | نزدیک‌ترین به دلارِ واقعیِ زودهنگام؛ چراغ را روشن نگه می‌دارد |
| 🔴 **SATELLITE (انفجاری/capped)** | ~۳۰٪ | Project-F · Crypto · Mining · یک آزمایشِ نو | هر کدام **سقف‌دار** (هیچ‌کدام نمی‌تواند سیستم را غرق کند)، ولی upsideِ نامتقارن — «شاخهٔ بامبو» |

**قاعدهٔ تعادل:** هیچ satelliteِ منفرد از یک سقفِ سخت (مثلاً ۱۰٪ کل) بیشتر نمی‌گیرد → یک شکست کلِ سیستم را نمی‌کشد؛ ولی مجموعِ satelliteها اجازهٔ «بیرون‌زدن» می‌دهد. (همان دکترینِ barbellِ کریپتو، حالا در سطحِ کلِ اکوسیستم.)

> Ziman + Project-F هر دو اولویتِ درآمدی‌اند ولی در دو سرِ متفاوت: **Ziman = CORE** (فروشِ فیزیکیِ نزدیک، کم‌ریسک)، **Project-F = SATELLITE** (upsideِ بزرگ/exit ولی پشتِ GATE 0 و ریسک‌دار). این طبیعیِ barbell است.

---

## ۲. آزمون‌وخطا (حلقهٔ Governor — قلبِ «مهم‌ترین»)
درصدها ثابت نیستند؛ هر epoch بر اساسِ **نتیجهٔ واقعی** تنظیم می‌شوند:
- **سیگنالِ تنظیم = CONFIRMED AUD** (نه پیش‌بینی، نه فعالیت). شاخکی که دلارِ واقعی ساخت → درصدِ بیشتر؛ بی‌ثمر → throttle. (همان fitness/metabolic-governorِ موجود.)
- **ولی cull بر پایهٔ survival نه payback** (درسِ Mining): satelliteِ کند را زود نکَن — بامبو سال‌ها زیرِ خاک است بعد یک‌شبه می‌زند بیرون. فقط وقتی «مرده» است (سیگنالِ صفر پایدار) حذف کن.
- **hysteresis:** تغییرِ درصد آرام و کران‌دار (ضدِ نوسان)، تا یک هفتهٔ بد یک شاخک را نکُشد.

این دقیقاً «طراحی و آزمون‌وخطای پول‌بر‌درصد» است: Governor درصدها را می‌چرخاند، ledger نتیجه را ثبت می‌کند، Ari جهت را verdict می‌دهد.

---

## ۳. انتسابِ سهم (درصدِ شریک — عینی‌کردنِ «شراکت»)
- هر رویدادِ MONEY_ATTRIBUTION یک فیلدِ **share** می‌گیرد: `{tentacle, aud_confirmed, partners:[{who, pct}]}`.
- مثال: Project-F → `partners:[{Ari:50},{صبا:50}]`؛ Ziman → `partners:[{Ari, مادر}]`؛ Lead → `Ari:100`.
- خروجی: یک نمای شفافِ «چه‌کسی چه‌قدر ساخت» — همان چیزی که در کاکپیت می‌خواستی، حالا از دادهٔ واقعی نه عددِ ساختگی.

---

## ۴. walls (ریسک‌پذیرِ **متعادل**)
- فعلاً تخصیصِ **کوشش/API/توجه** است، نه جابه‌جاییِ پولِ واقعیِ بیزنس (money-lock دست‌نخورده تا capability∧approval).
- **API نامحدودِ GLM/Fugu (فاندِ Ari):** سقفِ ماهانه بالا می‌رود، ولی **kill-switch + خطِ فاجعه + alert ۵۰/۸۰٪ حفظ** — «متعادل» یعنی ریسکِ نامتقارنِ upside، نه حذفِ ترمز. یک حلقهٔ recursive نباید بی‌ترمز بسوزاند.
- هر تغییرِ تخصیص propose-only + قابلِ‌رصد در ledger؛ satelliteهای پول‌سازِ واقعی فقط با verdictِ Ari live می‌شوند.

---

## ۵. نگاشت به کد (چه چیزی ساخته/تغییر می‌کند)
- `budgets.yaml`: وزن‌های organ از مساوی → **barbell (%)**؛ سقفِ satellite؛ cap ماهانهٔ API بالا + حفظِ disaster line.
- `governor_epoch.py` + `fitness.py`: تنظیمِ درصد بر اساسِ CONFIRMED AUD + survival-cull + hysteresis.
- `attribution.py`: فیلدِ `partners[]/pct` روی رویدادِ MONEY_ATTRIBUTION.
- همه paper/propose-only؛ تستِ رفتاری: شاخکِ پول‌ساز درصدش بالا می‌رود، satellite سقفش شکسته نمی‌شود، cull فقط روی مرگ.

---
**نوتِ خواهر:** [[04 - Architect System/2026-07-09 OCTOPUS-GOAL-MAP — ecosystem strategy (from raw project data)|GOAL-MAP]] · [[04 - Architect System/2026-07-09 OCTOPUS-SKELETON — Backbone + Request-Protocol + Self-Model|SKELETON/Self-Model]].
