---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft-for-build
created_by: agent
relates_to: "[[TELEGRAM-BRAIN-COCKPIT-v1]] (اسپکِ پایه) · [[P3-TELEGRAM-UX-v2]] · _ops/budget/approval_channel.py · _ops/unified_bus.py"
tags: [octopus, telegram, cockpit, glm-prompt, propose-only]
created: 2026-07-09
updated: 2026-07-09
---
# BRAIN COCKPIT v1 — پرامپتِ GLMِ سفت‌شده (grounded در برابرِ master)

> مرورِ معمار (Claude) روی [[TELEGRAM-BRAIN-COCKPIT-v1]] در برابرِ کدِ **واقعیِ** master. اسپک منسجم و ایمن است؛ این نسخه ۳ گپِ زمینی را می‌بندد تا GLM روی فرضِ اشتباه نسازد. جایگزینِ §۵ اسپکِ اصلی.

## آنچه راستی‌آزمایی شد (زمینی، 2026-07-09)
- **پایهٔ واقعیِ تلگرام = `_ops/budget/approval_channel.py`** (نه فقط اسپکِ P3-UX-v2): T-1 لوله + **T-2 کارت‌های تأیید** (approve/deny/later، ردِ approvalِ جعلی، **settle فقط با approve**) + ورودِ lead + وضعیت. ۴۰ تست در `_ops/tests/test_telegram_channel.py`. خط‌قرمزهای §۴ **از قبل enforce شده‌اند** — cockpit نباید settle/approval را بازپیاده‌سازی کند، فقط لایهٔ VIEW+routing روی همین کانال است.
- **`_ops/unified_bus.py` فقط `publish()`/`replay()` دارد — هیچ API صفِ تجمیعی.**
- **`_ops/legs/` فقط `lead_leg.py` را دارد** (۱ از ۶ پا واقعی). ۵ پای دیگر ماژول ندارند.
- `chrono_rhythm/rhythm.py` = منبعِ mode/HRV. `panel/server.py` = الگویِ اسکنِ `PROJECT.md` (`_scan_projects`).

## ۳ اصلاحِ الزامی نسبت به پرامپتِ اصلی
1. **صفِ تأییدِ تجمیعی را «استخراج» کن، نه «از unified_bus بگیر».** منبع: (الف) رجیستریِ `_pending` کارت‌های T-2 در همان `approval_channel` + (ب) `unified_bus.replay(event_type="MONEY_ATTRIBUTION")` فیلترشده به state ∈ {PROPOSAL, CLAIMED} (منتظرِ verdict). یک تابعِ `pending_across_legs()` بساز که این‌ها را جمع و dedup کند.
2. **وضعیتِ ۶ پا:** `lead` از `legs/lead_leg.py`؛ **۵ پای دیگر از اسکنِ `PROJECT.md`** (همان `_scan_projects` پنل). فرض نکن ۶ leg-module هست.
3. **پول را از SoT بخوان، هاردکد نکن:** cap ماهانه از `_ops/budget/budgets.yaml` (`global.cap_monthly`) + خرجِ جاری از `organ_gate.status()`/`budget-state.json`. ⚠️ **تعارضِ عدد:** اسپک «ماه $۰/۸۰» می‌گوید ولی budgets.yaml قبلاً `cap_monthly: 30` بود — مالک باید عددِ درست را در budgets.yaml قفل کند؛ cockpit همان SoT را نشان دهد.

---

## پرامپتِ GLMِ اصلاح‌شده (build-ready)

```
تو کارگرِ کدنویسِ Octopus (GLM) هستی. کاکپیتِ چندپروژه‌ایِ آری را بساز. additive، propose-only، commit با مالک (path-scoped).

بخوان (به‌ترتیب، کدِ واقعی مقدم بر اسپک):
- _ops/budget/approval_channel.py  ← پایهٔ واقعیِ تلگرام (T-1+T-2). settle/approval را از همین‌جا استفاده کن، بازپیاده‌سازی نکن.
- _ops/tests/test_telegram_channel.py  ← قراردادهای رفتاری/ایمنی که نباید بشکنند.
- _ops/unified_bus.py (publish/replay) · _ops/budget/organ_gate.py + budgets.yaml (پول SoT) · _ops/chrono_rhythm/rhythm.py (mode/HRV) · _ops/legs/lead_leg.py · _ops/panel/server.py (الگوی _scan_projects) · هر PROJECT.md پاها.
- اسپک: octopus-build-prompts/TELEGRAM-BRAIN-COCKPIT-v1.md + P3-TELEGRAM-UX-v2.md.
اول PLAN بده (چه فایلی، چه توابعی، کجا وصل).

بساز (HTML غنی، §۲ اسپک) — cockpit یک لایهٔ VIEW+routing روی approval_channel است:
- منو + 🐙 ارگانیسم (mode/HRV از rhythm، σ/گیت/دکتر/germline از state) + رنگِ mode از Chrono.
- ✅ صفِ تأییدِ تجمیعی: تابعِ نو pending_across_legs() = _pending کارت‌های T-2 + unified_bus.replay(MONEY_ATTRIBUTION) فیلتر به state∈{PROPOSAL,CLAIMED}، dedup بر attribution_id. هر کارت: [پروژه] اقدام · مبلغ · گارد · [✅][❌][⏳].
- 📊 وضعیتِ ۶ پا: lead از lead_leg؛ ۵ تای دیگر از اسکنِ PROJECT.md (کپیِ الگوی panel._scan_projects).
- 💵 پولِ shadow: cap از budgets.yaml (SoT، هاردکد نکن) · خرج از organ_gate.status().
- 🔔 آلارمِ RED فقط · 📅 بریفِ روز (از ledger/replay) · ⏹ /stop.

خط‌قرمز (نقض=رد کلِ کار):
- approve تنها مسیرِ settle — از همان approval_channel، بازپیاده‌سازی نکن (تست‌های موجود سبز بمانند).
- money قفل (live_gate/capability_gate دست‌نخورده) · توکن فقط env، هرگز log/commit · quarantine ورودی=DATA · فقط chat_idِ آری.
- **Project-F فقط «درفت در صف»**: منطقِ تجمیع هرگز رسانه/متن/هویتِ صبا را نخواند یا نشان ندهد — فقط شمارش/وضعیت. (چک‌لیستِ پایین.)
- بدونِ git commit (مالک path-scoped می‌زند).

تست‌ها ($0، به test_telegram_channel اضافه یا فایلِ نو):
- pending_across_legs از ≥۲ منبع (کارت T-2 + MONEY_ATTRIBUTION replay) درست جمع/dedup می‌شود.
- approve فقط از کانالِ موجود settle می‌کند (paper) — تستِ موجودِ approve/deny دست‌نخورده سبز.
- اسکنِ ۵ پا از PROJECT.md درست وضعیت می‌دهد؛ lead از lead_leg.
- پولِ cap از budgets.yaml خوانده می‌شود نه هاردکد.
- آلارمِ RED رندر می‌شود · Project-F هیچ رسانه/هویت لو نمی‌دهد · /stop کار می‌کند.
خروجیِ خامِ run_all را paste کن.

DoD: cockpit تست‌سبز، صفِ تجمیعیِ استخراج‌شده، ۵-پا-از-PROJECT.md، پولِ SoT، جداییِ Project-F حفظ، ایمنیِ موجود دست‌نخورده (۴۰ تستِ telegram سبز). ORGANISM-SPEC §5 + HANDOFF آپدیت. هر ابهام → «⚑ برای معمار».
```

## چک‌لیستِ ایمنیِ Project-F (باید در PR سبز باشد)
- [ ] `pending_across_legs()` برای Project-F فقط `{project, action_label, state}` برمی‌گرداند — نه ref/متن/رسانه/handle.
- [ ] رندرِ ۶-پا برای Project-F فقط «🎬 Project-F 🟡 … · درفت در صف» — صفر جزئیات.
- [ ] هیچ مسیرِ cockpit به پوشهٔ پروژهٔ اونلی‌فنز/Content-Studio رسانه/هویت نمی‌خواند.
- [ ] تستِ صریح: یک PROPOSALِ Project-F با متن/ref پرشده → خروجیِ cockpit صفر نشت.

## Sources
[[TELEGRAM-BRAIN-COCKPIT-v1]] · [[P3-TELEGRAM-UX-v2]] · `_ops/budget/approval_channel.py` · `_ops/unified_bus.py` · `_ops/legs/lead_leg.py` · `_ops/panel/server.py` · `_ops/chrono_rhythm/rhythm.py`
