---
type: runbook
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft-for-execution
tags: [octopus, queue, ui, brain, telegram, glm, autonomous]
created: 2026-07-09
updated: 2026-07-09
---

# QUEUE-3 — UI + مغزِ Project-F (صفِ خودگردانِ GLM)

> یک پیست به GLM. از بالا به پایین اجرا می‌کند؛ هر ماژول offline/$0 ساخته و تست می‌شود (توکن فقط برای اجرای زنده لازم است، نه ساخت). روی هر قرمز هارد-استاپ + گزارشِ ⚑ در `00 - Inbox/UI-BUILD-LOG.md`.

## قراردادِ خودگردانی (حاکم بر هر آیتم)
```
تو کارگرِ کدنویسِ خودگردانِ Octopus/Project-F (GLM) هستی. قواعدِ ثابت:
- هر آیتم: پرامپتِ داخلِ فایلِ ارجاع‌شده را بخوان و اجرا کن → python _ops/tests/run_all.py → اگر همه سبز نبود، بایست + نوتِ ⚑ STOP در 00 - Inbox/UI-BUILD-LOG.md، آیتمِ بعد را شروع نکن.
- روی سبز: checkpoint-commit path-scoped (git reset -- "**/*.db" "_ops/state/*.db"؛ commit «ui-build <آیتم>: green»).
- ناوردی‌ها بی‌استثنا: propose-only · approve=تنها settle (TINV-7) · توکن env-only · DATA-quarantine · money قفل · صفر git از سندباکس · Project-F: صفر رسانه/هویت/PII، دوکلیده، محدودهٔ صبا مقدم · λ_persist<0 + Ethics-Guard.
- توکنِ بات لازم نیست (ساخت offline/$0؛ تست‌ها با http فیک). گزارشِ هر آیتم + خروجیِ خام در UI-BUILD-LOG.
- هر ابهام → «⚑ برای معمار (Claude)».
```

## ترتیب (وابستگی‌محور)
1. **P3 UX v2 (تلگرامِ لاغرِ آری)** — پرامپت: `P3-TELEGRAM-UX-v2.md §۵`. پایهٔ بقیه. → سبز → commit.
2. **Brain Cockpit (آری، چندپروژه)** — پرامپت: `TELEGRAM-BRAIN-COCKPIT-v1.md §۵`. روی P3-UX-v2. → سبز → commit.
3. **Content Studio v2 (صبا)** — پرامپت: `03 - Projects/اونلی فنز/TELEGRAM-CONTENT-STUDIO-v2.md §۴`. باتِ جدا، ایزوله. → سبز → commit.
4. **Project-F Brain (بینِ دو UI)** — پرامپت: `03 - Projects/اونلی فنز/PROJECT-F-BRAIN-SPEC.md §۶`. بازاستفاده از `_ops/doctor/box`. → سبز → commit.

## پایان
خلاصهٔ ۱۰خطی در بالای `00 - Inbox/UI-BUILD-LOG.md`: چه سبز شد، ⚑ها، کارهای فقط‌مالک.

---

## go-live (فقط‌مالک — ۵ فرمان/اقدام، بعد از ساخت)
```
1) بات: در تلگرام @BotFather → /newbot → توکن. chat_id از api.telegram.org/bot<TOKEN>/getUpdates.
   در .env:  TELEGRAM_BOT_TOKEN=...   TELEGRAM_OWNER_CHAT_ID=...
   (Project-F: توکن/chat_idِ جدا برای باتِ صبا.)
2) Scheduled Task: powershell -File F:\backup\scripts\organism-watchdog.ps1  (At log on + هر ۵ دقیقه)
   + germline-hourly.ps1 (ساعتی).
3) off-site: credentialِ کلاود فقط در .env، سپس restore-drill.ps1 یک‌بار.
4) اجرای ۲۴h: ارگانیسم via Scheduled Task بالا → بعد ۲۴h: python _ops/smoke_24h.py → PASS.
5) اولین لیدِ paper: در تلگرام /lead → draft quote → CSV در پنجرهٔ ۷ روز → CONFIRMED.
```
پول (P6) دست نزن — قفل تا ۲۰۲۶-۰۷-۲۱ + پرچمِ تو.
