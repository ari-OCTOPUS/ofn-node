---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft-for-build
created_by: agent
relates_to: "[[P3-TELEGRAM-UX-v2]] (پایه) · [[OCTOPUS-BASE-MAP-v0]] · همهٔ پاها"
tags: [octopus, telegram, cockpit, multi-project, brain, propose-only]
created: 2026-07-09
updated: 2026-07-09
---

# BRAIN COCKPIT v1 — کاکپیتِ آری (مغزِ انسانیِ اختاپوس)

> سطحِ تلگرامِ آری: پیچیده‌تر از تک‌پروژه، چون آری **مغزِ انسانیِ** کلِ ارگانیسم است — تنها نقطهٔ human-append برای همهٔ پاها + ناظرِ سلامتِ ارگانیسم. لاغر ولی چندلایه. propose-only، همه shadow.

## ۱. اصل
آری = **meta-approver + استراتژِ** همهٔ پاها. کاکپیت باید در یک‌نگاه بدهد: (الف) صفِ تأییدِ **تجمیعیِ** همهٔ پروژه‌ها، (ب) وضعیتِ هر پا، (ج) سلامتِ ارگانیسم (قلب/گیت/دکتر)، (د) نمای پول، (ه) آلارمِ RED، (و) بریفِ روز. صبا فقط Project-F را می‌بیند؛ آری همه را.

## ۲. سطحِ کاربری (HTML غنی)
```
🧠 مغزِ اختاپوس — کاکپیتِ آری · 🟢 GREEN
[🐙 ارگانیسم]   [✅ صفِ تأیید (N)]
[📊 پروژه‌ها]    [💵 پول (shadow)]
[🔔 آلارم‌ها]    [📅 بریفِ روز]
[⏹ توقف]
```
- **🐙 ارگانیسم:** mode 🟢🟡🔴 · ♥️ ضربان/HRV · σ · دکتر (RFCهای در صف) · germline · uptime · نسبتِ afferent (هشدارِ «رؤیا»).
- **✅ صفِ تأیید (تجمیعی):** یک صف از **همهٔ** پاها؛ هر کارت: `[پروژه] اقدام · مبلغ · گارد · [✅][❌][⏳]`. آری تنها نقطهٔ human-append.
- **📊 پروژه‌ها (۶ پا، هرکدام یک‌خط):**
  `🎯 Lead-نقاشی 🟢 درآمد#۱ · lead فعال` ·
  `🎬 Project-F 🟡 validation · درفت در صف` ·
  `📈 Crypto 🔵 read-only · بریفِ روز` ·
  `🧮 Accounting 🔵 گزارش` · `⛏ Mining ⚪ scouting` · `🖼 Ziman ⚪ پلن`.
- **💵 پول (shadow):** خرجِ تجمیعی امروز $۰ · ماه $۰/۸۰ · money-gate 🔒 تا ۲۰۲۶-۰۷-۲۱ · هر پا money_link.
- **🔔 آلارم‌ها:** فقط RED (safety breach · cost-cap · gate-conflict · afferent پایین · germline کهنه).
- **📅 بریفِ روز:** ۳ کارِ مهمِ امروز · چه چیزی منتظرِ تأیید · چه تغییر کرد (از ledger).
- **⏹ توقف:** kill-switch.

## ۳. تفاوت با سطحِ صبا
| | صبا (Content Studio) | آری (Brain Cockpit) |
|---|---|---|
| دامنه | فقط Project-F | همهٔ ۶ پا + ارگانیسم |
| صفِ تأیید | ثبتِ درفت → می‌رود بالا | **دریافت + verdictِ** تجمیعی |
| پول | نمی‌بیند | نمای shadowِ تجمیعی |
| ارگانیسم | نمی‌بیند | قلب/گیت/دکتر/HRV |

## ۴. خطوطِ قرمز (baked)
approve = تنها مسیرِ settle (TINV-7) · توکن env-only · DATA-quarantine · فقط chat_idِ آری · money قفل · /stop می‌ماند · propose-only · Project-F فقط وضعیتِ تجمیعی (صفر رسانه/هویتِ صبا در کاکپیتِ آری — فقط «درفت در صف»).

## ۵. پرامپتِ GLM
```
تو کارگرِ کدنویسِ Octopus (GLM) هستی. کاکپیتِ آری (چندپروژه‌ای) را بساز، روی پایهٔ P3-UX-v2. additive، propose-only، commit با مالک.
بخوان: TELEGRAM-BRAIN-COCKPIT-v1.md + P3-TELEGRAM-UX-v2.md + _ops/budget/approval_channel.py + unified_bus.py (منبعِ رویدادِ پاها) + هر PROJECT.md پاها برای وضعیت. PLAN بده.
بساز (HTML غنی، §۲): منو + 🐙 ارگانیسم + ✅ صفِ تأییدِ تجمیعی (از همهٔ پاها via unified_bus) + 📊 وضعیتِ ۶ پا + 💵 پولِ shadowِ تجمیعی + 🔔 آلارمِ RED + 📅 بریفِ روز + ⏹ توقف. رنگِ mode از Chrono.
خطِ قرمز (نقض=رد): approve تنها مسیرِ settle · توکن env-only · quarantine · فقط chat_id آری · money قفل · Project-F فقط «درفت در صف» (صفر رسانه/هویتِ صبا در کاکپیت) · بدونِ git commit.
تست‌ها ($0): صفِ تجمیعی از چند پا درست جمع می‌شود · approve فقط از این کانال settle می‌کند (paper) · آلارمِ RED رندر · Project-F هیچ رسانه/هویت لو نمی‌دهد · /stop کار می‌کند. خروجیِ خامِ run_all را paste کن.
DoD: کاکپیت تست‌سبز، صفِ تجمیعی، جداییِ Project-F حفظ، ایمنی دست‌نخورده. ORGANISM-SPEC §5 + HANDOFF آپدیت. هر ابهام → «⚑ برای معمار».
```

## Sources
[[P3-TELEGRAM-UX-v2]] · [[OCTOPUS-BASE-MAP-v0]] · `_ops/unified_bus.py` · [[CHRONO-RHYTHM-LAYER-SPEC]] (mode/HRV)
