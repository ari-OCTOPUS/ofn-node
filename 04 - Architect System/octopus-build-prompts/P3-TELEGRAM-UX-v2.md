---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft-for-build
created_by: agent
relates_to: "[[P3-TELEGRAM]] · _ops/budget/approval_channel.py"
tags: [octopus, telegram, ux, redesign, propose-only]
created: 2026-07-09
updated: 2026-07-09
---

# P3 TELEGRAM UX v2 — لاغر + زیبا (اختاپوس)

> بازطراحیِ سطحِ کاربریِ تلگرام. **verdict آری:** حذفِ ۳ قابلیت + سبکِ غنی/رنگی. حذف = فقط سطحِ نمایش؛ هیچ ناوردیِ ایمنی کم نمی‌شود.

## ۱. تصمیم‌ها
- **حذف:** 🧪 آزمایشگاه (T-4: /start_exp, /reveal) · 🧬 کارتِ RFC دکتر (T-6) · ↩️ Re-entry packet (دایجستِ T-7).
- **می‌ماند:** منوی اصلی · ✅ کارتِ تأیید (T-2) · 🎯 لید (T-3) · 🐙 وضعیت (T-5) · ⏹ /stop kill-switch.
- **سبک:** غنی/رنگی — HTML parse_mode، رنگِ حالتِ قلب 🟢🟡🔴، خط‌جداکننده، آیکن.

## ۲. سطحِ باقی‌مانده (mockup، HTML)
**منوی اصلی (`/start`):**
```
🐙 اختاپوس — کنترلِ تو
[🐙 وضعیت]  [✅ تأییدها]
[🎯 لید نو]  [⏹ توقف]
```
**کارتِ تأیید (T-2، هستهٔ human-append):**
```
🐙 تأییدِ لازم · 🔴 برگشت‌ناپذیر
──────────
📌 پیشنهاد: «کوتِ نقاشیِ لیدِ ۰۰۳»
💰 مبلغ: AU$ ۰ (paper)
🛡 گارد: organ ✅ · money 🔒 · cap ✅
⚠️ ریسک: هیچ
──────────
[✅ تأیید]  [❌ رد]  [⏳ بعداً]
```
**وضعیت (T-5، داشبورد):**
```
🐙 اختاپوس · 🟢 GREEN · STEADY
──────────
♥️ ضربان ~۹۰s · HRV خوب
💵 خرج: امروز $۰ · ماه $۰/۸۰
📊 σ ۰.۹ · تعارض ۰
💾 germline: تازه (۲h) · 📥 صفِ تأیید: ۰
```
**لید (T-3):** راهنمای گام‌به‌گام (نام→کار→کانال) → کارتِ تأییدِ ثبت:
```
🎯 لیدِ نو · LEAD-20260709-001
draft quote آماده
[✅ ثبتِ proposal]  [✏️ ویرایش]
```
**توقف:** `/stop` → `🔴 STOP نوشته شد — ارگانیسم متوقف.` (فایلِ STOP authoritative)

## ۳. رنگِ حالت = حالتِ واقعیِ قلب
🟢 GREEN · 🟡 AMBER · 🔴 RED از mode-mapِ Chrono-Rhythm خوانده می‌شود — UI هم قشنگ است هم آینهٔ وضعیتِ سیستم. **کاهشِ نویز:** ping فقط برای تأیید + آلارمِ 🔴؛ بقیه در کارتِ وضعیت.

## ۴. ناوردی‌های حفظ‌شده (حذف اینها را لمس نمی‌کند)
- approve = human-append (is_human=1) = **تنها مسیرِ EffectorGate.settle** (TINV-7).
- توکن فقط env · هر ورودی = DATA (quarantine) · فقط chat_idِ مالک.
- **/stop kill-switch می‌ماند** (فقط دایجستِ بازگشت حذف شد، نه خودِ توقف).
- **merge‌ی RFCِ دکتر → پنلِ محلی ۸۷۹۰** (چون کارتِ تلگرامش حذف شد) — دکتر بی‌کانالِ تأیید نمی‌ماند.

## ۵. پرامپتِ GLM
```
تو کارگرِ کدنویسِ Octopus (GLM) هستی. UXِ تلگرام را به v2 ببر (لاغر + غنی). additive/اصلاحی، propose-only، commit با مالک. ناوردیِ ایمنی را نشکن.
گام ۰: _ops/budget/approval_channel.py را بخوان (TelegramApprovalChannel، T-1..T-7). اول PLAN.
تغییرات:
1) حذف/غیرفعال: هندلرهای آزمایشگاه (/start_exp, /reveal + lab)، کارتِ RFC دکتر (T-6)، و دایجستِ Re-entry (T-7). خودِ /stop kill-switch را نگه‌دار.
2) merge‌ی RFCِ دکتر را به پنلِ _ops/panel (8790) منتقل کن (نه حذفِ کامل؛ فقط از تلگرام بردار).
3) منوی اصلی (/start): اینلاین‌کیبورد [🐙 وضعیت][✅ تأییدها][🎯 لید نو][⏹ توقف].
4) کارت‌ها را با parse_mode=HTML و سبکِ §۲ بازنویسی کن (آیکن، خط‌جداکننده، 🟢🟡🔴 حالت). escapeِ HTML را درست رعایت کن (<, >, & در محتوای کاربر).
5) رنگِ حالت را از mode-mapِ Chrono (GREEN/AMBER/RED) بخوان؛ اگر لایهٔ ریتم هنوز نیست، fallback به STEADY/🟢.
6) کاهشِ نویز: ping فقط برای کارتِ تأیید و آلارمِ RED.
خطِ قرمز (نقض=رد): approve تنها مسیرِ settle (TINV-7) · توکن env-only · DATA-quarantine · owner allowlist · /stop می‌ماند · بدونِ git commit · additive.
تست‌ها ($0 آفلاین): (الف) هندلرهای حذف‌شده دیگر پاسخ نمی‌دهند · (ب) کارتِ تأیید هنوز end-to-end approve/deny می‌کند (paper) و فقط approve settle می‌کند · (ج) /stop هنوز STOP می‌نویسد · (د) HTML بدونِ خطای parse رندر می‌شود (تستِ escape) · (ه) توکن هرگز در repr/log. خروجیِ خامِ run_all را paste کن.
DoD: UX v2 تست‌سبز، ۳ قابلیت حذف، ایمنی دست‌نخورده، merge دکتر روی پنل. ORGANISM-SPEC §5 + HANDOFF آپدیت. هر ابهام → «⚑ برای معمار».
```

## Sources
[[P3-TELEGRAM]] · `_ops/budget/approval_channel.py` · [[CHRONO-RHYTHM-LAYER-SPEC]] (mode 🟢🟡🔴) · verdict آری (session 41)
