---
type: architecture
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [autonomy, self-improvement, part-loops]
created: 2026-07-11
updated: 2026-07-11
created_by: agent
sources:
  - "[[06 - Architecture Maps/SPEC-OCTOPUS-2027-v0]]"
  - "[[06 - Architecture Maps/AUDIT-MATRIX-self-improvement-2026-07-10]]"
---

# Part-Loops — لوپِ یادگیری+خود-تغییر برای «هر بخش»

> رأی مالک (2026-07-11): «اتوماتیک‌تر کن؛ برای هر بخش لوپ‌های یادگیرنده و تغییردهنده طرح کن.»
> این تعمیمِ لوپِ مرکزیِ خودارتقا (self_audit+improve) به **یک لوپ per بخش** است.

## الگوی سه‌گامیِ هر بخش

هر بخش یک تابعِ لوپ در `_ops/cortex/part_loops.py` دارد که سه گام را می‌زند:

1. **observe** — probeِ فقط‌خواندنیِ stateِ خودِ بخش (heart-shadow، cortex-state، rfcs،
   telemetry، discoveries، selfheal-events، self-model). خروجی: status (🟢/🟡/🔴) + detail.
2. **learn** — مقایسهٔ مشاهده با آستانه/تاریخچه (مثلاً پول ≥۸۰٪ سقف، هم‌آهنگی <۰.۶،
   ۰ کشف در ۴۸h، ≥۵ خودترمیم/روز).
3. **propose** — پیشنهادِ بهبودِ **خودِ بخش** با change_level (tune|reconfig|code) و auto_ok.

## بخش‌های ثبت‌شده (نسخهٔ ۱)

| بخش | observe | نمونه‌پیشنهاد |
|---|---|---|
| ❤️ قلب | heart-shadow (period, Gate-0, wire) | «هنوز دادهٔ کافی ندارد؛ ~۱۲h صبر» |
| 🧠 مغز | cortex-state (coherence) | «هم‌آهنگی پایین؛ اعضای کهنه» |
| 🩺 دکتر | rfcs.json (pending) | «N پیشنهاد منتظرِ رأیِ توست» |
| 💰 پول | telemetry (month aud) | «خرج نزدیکِ سقفِ ۳۰» |
| 📚 یادگیری | discoveries (۴۸h) | «چیزی یاد نگرفته؛ کادنس تندتر (tune،auto)» |
| 🦿 اعضا | selfheal-events | «عضو ناپایدار؛ بررسیِ ریشه» |
| 🪞 خودمدلی | self-model | «N ماژول بدونِ سند» |

## ارکستریشن و حاکمیت

- `run_all(beat)` همهٔ بخش‌ها را می‌چرخاند → `state/cortex/part-loops-latest.json` +
  یک رویدادِ `task.completed` (داشبورد). در `cortex.run_cycle` هر `IMPROVE_EVERY_N` چرخه.
- پیشنهادها → `improve.gather_signals` → `/upgrades` + خانهٔ آره/نهِ تلگرام + داشبوردِ `8773/ops`.
- **propose-only مطلق:** فقط knobِ `tune` و $0 و پشتِ `ACTIVATION-SELF-IMPROVE-AUTO` می‌تواند
  auto شود؛ `reconfig`/`code` همیشه به رأیِ مالک. **هیچ بازنویسیِ خودکارِ کد** (مرزِ L4/L5 —
  [[06 - Architecture Maps/SPEC-OCTOPUS-2027-v0|SPEC §۴]]).
- fail-soft: خطای یک بخش کلِ لوپ را نمی‌کشد؛ read-only probe؛ $0.

## افزودنِ بخشِ نو

یک `_loop_<name>()` بنویس که `(status_dict, [proposals])` برگرداند و به `LOOPS` اضافه‌اش کن.
همین. بقیه (persist، رویداد، تغذیهٔ improve، نمایش در داشبورد) خودکار است.
