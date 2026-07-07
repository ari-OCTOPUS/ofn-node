---
type: knowledge
status: active
tags: [hypnosis]
epistemic_status: speculative
created: 2026-07-03
updated: 2026-07-03
---

# Roadmap.md — مسیرِ پیشِ‌رو، به‌ترتیبِ هر پروژه

## Hypnosis-Research (اولویتِ اول، طبقِ true north پروژه)
P4 (یال‌هایِ cross-domain) → P5 (پروتکلِ کاربردی) → P6 (ممیزیِ شکاکانه) → P7 (سنتزِ نهایی). ترتیب از خودِ `00_RESEARCH_PROMPTS.md` می‌آید و نباید جابه‌جا شود (هرکدام به خروجیِ قبلی وابسته است).

## Fusion-World
Rung 0 calibration (نوت‌بوکِ Qiskit، کانالِ کلاسیک خاموش، تأییدِ mutual information=۰) → Rung 1 (کاوشِ ارزان رویِ QRNG/LIGO/CMB با pre-registration) → Rung 2 (آزمایشگاهی، فقط اگر Rung 1 سرنخ داد).

## Neuro-HRV-Nof1
تأییدِ وضعیتِ فعلی با کاربر → (اگر شروع‌نشده) دو هفته baseline طبقِ حلقه‌یِ روزانه → شروعِ آزمایش‌هایِ E1–E4 → E5 (حلقه‌یِ شبانه، پراهرم‌ترین) در انتها چون نیازمندِ چند هفته ترند است.

## Silabi-Bot
رفعِ باگِ امنیتیِ خطِ ۲۱۸۸ (فوری) → تأییدِ وضعیتِ فازِ ۲ → فازِ ۳ (بازنگری با داده‌یِ واقعی، با کمکِ Claude) → فازِ ۴ (همیشه‌روشن، فقط اگر فازِ ۳ ارزشش را تأیید کند).

## SERVER_ARCHITECTURE / infra-control
Phase 0 (پایه) → Phase 1 (کنترل/Telegram bot) → Phase 2 (CI/CD) → Phase 3 (بلوغ/مانیتورینگ). طبقِ دایجست، infra-control ظاهراً از Phase 0 گذشته؛ وضعیتِ دقیق باید از آن پروژه استعلام شود.

## fusion-mvp (دایجست)
Grounding (اولویتِ ۹) → Self-model سبک (اولویتِ ۵) → IGK-as-kernel-process فقط اگر threat model عوض شود (اولویتِ ۳، عمداً معوق).

## افقِ بلندمدت (از خودِ اسناد، نه حدسِ من)
مسیرِ مهاجرت به Kubernetes تا ۲۰۲۸–۲۰۳۵ (SERVER_ARCHITECTURE، عمداً بازگذاشته‌شده، نه برنامه‌ریزی‌شده).


---
## به‌روزرسانی 2026-07-04 (agent)
Hypnosis-Research: P4 ✅ → اکنون **P5 (پروتکلِ کاربردی)** قدمِ بعدی است.

## به‌روزرسانی 2026-07-04 (agent) — زنجیره کامل
P5 ✅ · P6 ✅ · P7 ✅ → **Hypnosis-Research بسته شد (۸/۸)**. قدمِ بعدی از این پروژه = اجرای Practice (اولین جلسه طبقِ P5) و baselineِ Neuro-HRV.
