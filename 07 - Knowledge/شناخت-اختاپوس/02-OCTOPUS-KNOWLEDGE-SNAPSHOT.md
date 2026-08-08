---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, source-of-truth]
created: 2026-07-18
updated: 2026-08-08
---

# 🐙 شناخت اختاپوس — Snapshot (۲۰۲۶-۰۸-۰۴)

> **به‌روزرسانیِ ۲۰۲۶-۰۸-۰۴.** نسخهٔ ۲۰۲۶-۰۷-۱۷ سؤالاتِ بازِ زیادی داشت
> («Source of Truth کدام است؟») که حالا پاسخ داده شده. نسخهٔ پیشین در git موجود است.

---

## ۱. پاسخِ حیاتی: Source of Truth اجرایی کدام است؟

[FACT] **`_ops` بدنِ زندهٔ اجرایی است.** این سؤالِ بازِ ۲۰۲۶-۰۷-۱۷ حالا پاسخ دارد:

```text
اگر امروز فقط یکی را «بدن زنده» بنامیم: _ops/organism.py رویِ 8771.
```

لایه‌های دیگر نقش‌های متمایز دارند، نه رقابت بر سر SoT:

| لایه | مسیر | نقشِ تأییدشده (۲۰۲۶-۰۸) |
|---|---|---|
| **بدنِ اجرایی/زنده** | `_ops` | organism, cortex, heart, budget, legs, doctor, chrono, state — **این می‌دود** |
| مغزِ پژوهشی | `4d_system` | SOG / Brain-OS / self-model — پشتِ `OCTOPUS_WIRE_NEURAL`، paper-mode |
| کنترل‌پلینِ پول/گیت | `app` | NBB Control Plane، invariants، human verdict — مرجعِ پول |
| پروژه‌ها/پاها | `03 - Projects` | پایِ lead (نقاشی، فعال)، ziman، + اندام‌های skeleton |
| ابزارِ نقشه‌برداری | cartographer (در `_ops`) | vault scanner، drift — read-only |

[INFERENCE] پس split-brain و drift که ۲۰۲۶-۰۷-۱۷ می‌ترساندیم، حل شده: **`_ops` حاکم
است، بقیه افزونه‌اند.**

---

## ۲. مدلِ اندامیِ زنده

```text
Owner / GOALS / Verdict / Kill
        ↓
_ops/organism.py  (8771)  ← حلقهٔ اصلی، پشتِ RUN-ORGANISM.bat
        ↓  (هر beat: allostatic، نه clock)
[cortex]    تصمیم، synthesis، route، self-model (پشتِ OCTOPUS_WIRE_*)
[heart]     ضربانِ allostatic، کنترل، work pump
[budget]    متابولیسم، پول، گیت، fitness، cardiac-budget
[legs]      پاهایِ propose-only (lead، ziman، cartographer، ...)
[doctor]    خودبهبود، RFC (پشتِ CHRONO_DOCTOR_EVERY_N_BEATS=1440 ≈ روزانه)
[chrono]    gated_effect + release_effect (بهترین احرازِ ریپو)
[state]     حافظه، events، chrono.db، telemetry
        ↓
telegram_center/center.py (پلِ تلگرام) → miniapp_gateway.py (8774)
        ↓
مالک (تلگرام/مینی‌اپ)
```

---

## ۳. یافته‌هایِ کلیدیِ تأییدشده (۲۰۲۶-۰۸)

### ۳.۱ `_ops` واقعاً زنده است (برخلافِ ۲۰۲۶-۰۷-۱۷ که `[UNKNOWN]` بود)
[FACT] پنج+ پروسهٔ پایتون می‌دوند: organism (8771), center (پلِ تلگرام), gateway (8774),
cortex, live/server. state files هر چند ثانیه به‌روز می‌شوند. beat در حالِ پیشرفت است.

### ۳.۲ DNA حاکمیتی (تأییدشده در چند لایه)
- propose-only (پاها فقط پیشنهاد می‌دهند، اجرا مالک/گیت)
- human verdict برای اقدامِ برگشت‌ناپذیر
- budget cap (`cardiac-budget`، daily cap)
- kill-switch (`STOP-ORGANISM`، `HALT-ALL`)
- fail-closed (هر خطا = بسته، نه باز)
- ledger append-only (`genome-system/ledger`)
- quarantine برایِ boundary text
- no self-law-edit

### ۳.۳ حلقهٔ میانی (the broken middle) — تمرکزِ کارِ امروز
[FACT] هوش (`cortex`، `doctor`، LLM routing) از قبل ساخته شده. آنچه شکسته بود تبدیلِ
**تصمیمِ ثبت‌شده → اثرِ مقیدشده → رسید** بود. مگاپرامپت §۲ این را قلبِ کار می‌داند.

### ۳.۴ عددِ پاها (اصلاحِ ۲۰۲۶-۰۷-۱۷)
[FACT] امروز: یه پایِ lead فعال (`lead-naghshi`، money_link=active، propose_only=true)،
به‌اضافهٔ ziman/cartographer/sync_agent و چند skeleton (mining/crypto/accounting/knowledge).

---

## ۴. مکانیزمِ مسلح vs. خاموش (۲۰۲۶-۰۸)

### مسلح (کار می‌کنند)
- `chrono.release_effect` — binding + ضدِ replay + ضدِ TOCTOU (بهترین احراز).
- `outcomes/pending_card_recovery.py` — FSM ِ رسیدِ اجباری.
- `legs/leg_tasks` — فایل‌محور، تنها حلقهٔ نوشتنِ تلگرامیِ اثباتاً کارکن.
- `live_state_guard` + `check_state_isolation.py` — گاردِ تستِ زنده.
- مسیرِ lead تا کارتِ تأیید (submit_candidate → lead_pipeline → کارت → تلگرام).

### نیمه‌مسلح / گپ‌دار
- `OCTOPUS_WIRE_LEAD_VERDICT_EFFECT` — روشن، ولی organism باید با فلگِ تازه بالا بیاید.
- `OCTOPUS_LEAD_FA_VOCAB` — **خاموش**؛ لیدِ فارسی score=0 می‌گیرد و skip می‌شود.
- `/api/lifecycle` — route ثبت شد (۲۰۲۶-۰۸-۰۴) ولی هنوز مصرف‌کننده‌ای در UI ندارد.
- `governor/obsidian` در miniapp_state — توابع گم‌شده؛ تست‌ها شکست می‌خورند.

---

## ۵. قابِ کارِ بعدی

مهم‌ترین سؤالِ امروز (نه ۲۰۲۶-۰۷-۱۷):

```text
چطور اولین تأییدِ واقعیِ مالک رویِ کارتِ لید را به سه سنجهٔ اثبات‌پذیر
(gated_effect + owner_approved + outcomes) تبدیل کنیم؟
```

مسیر مسلح است؛ فقط **لمسِ واقعیِ مالک** مانده. بعد از آن: رفعِ گپِ scorer فارسی،
تحقیقِ governor/obsidian گم‌شده، و اولویت ۲ (card_registry).

---

## ۶. قانونِ طلایی (بدون تغییر از ۲۰۲۶-۰۷-۱۷، چون درست بود)

```text
هیچ ادعایی بدون شاهد.
هیچ secret خوانده نشود.
هیچ اسکنِ کور/عظیم انجام نشود مگر مالک خواسته باشد.
هر شک باید به task قابل‌آزمون تبدیل شود.
```
