# 👣 اونلی فنز (Project-F) — نقشهٔ ایجنت (اول این را بخوان)

> Creator brand با مدل faceless (فقط پا در فاز فعلی). تیم دونفره ۵۰/۵۰.
> **وضعیت:** فاز validation. **ZERO execution** — planning/research/build only.
> ⚠️ حریم خصوصی: خارج از این پوشه فقط کد «Project-F». هیچ نام/محتوا/PII.

## 🎯 ماموریت
اعتبارسنجی مدل کسب‌وکار creator با متریک‌های صریح و گزارش زودهنگام نتیجه مالی به پارتنر (C).

## 📦 قراردادِ کنترل (موجود و کامل)
**`PROJECT-F-CONTROL-MANIFEST.json`** — قراردادِ ماشین‌خوانِ کامل برای ایجنتِ مادر:
- identity، status، ۸ hard rule قفل‌شده، gates (G0-G4)، autonomy model
- capabilities (research، content_studio، cockpit، brain_hitl، learning، experimentation)
- kill-switches، budget caps، runtime entrypoints، test suites

**این پروژه الگوی طلاییِ MANIFEST است** — بقیهٔ پاها بر اساس همین ساخته شدند.

## 🔌 اتصال به مغز مادر
- **مدل کنترل:** رصد + صف‌بندی verdict + قطع اضطراری. اجرا هرگز.
- **نقش ایجنت مادر:** OBSERVE / TASK propose-only / route verdicts / trigger kill-switches.
- **رابط:** `contracts/` (در MANIFEST موجود، section `control_surface`)

## 🗂️ ساختار پوشه
```
اونلی فنز/
├── README.md                        ← تو اینجایی
├── PROJECT-F-CONTROL-MANIFEST.json  ← 🏆 قرارداد کامل (الگوی طلایی)
├── AGENT-CONTROL-INTERFACE.md       ← روایت MANIFEST
├── CLAUDE.md                        ← منشور کاری (operating charter)
├── HOME.md                          ← داشبورد زنده Obsidian
├── PROJECT.md / INDEX / DecisionLog / OpenQuestions
├── project-master-reference.md      ← مرجع کامل
├── Knowledge_Base_Memory_Synthesis.md
├── پرسشنامه پارتنر - پاسخ‌های صبا.md  ← PII (داخل پوشه)
├── اونلی فنز.md                     ← لاگ تلگرام
├── brain/                           ← 🧠 کد زنده: project_f_brain، learning، ab_tracker
├── langar/                          ← 🎛 کاکپیت تلگرامی Operator (propose-only)
├── studio/                          ← 🌸 استودیو Creator (Saba)
├── orchestrator.py                  ← ⚠️ imports _ops/neural (غایب)
├── docs/                            ← BUILD، PLAYBOOK، BRAIN-SPEC، architecture
├── research/                        ← ACQUISITION، DECISION-MATRIX، integration rounds
├── research-results/                ← corpus کامل (P1-P13)
├── external-research-2026-07-05/    ← تحقیق بیرونی
├── drafts-awaiting-gate/            ← ۵ درفت منتظر verdict
├── _memory/                         ← حافظه بلندمدت
├── _inbox-other-projects/           ← cross-project (Ziman DM Bot، self-improvement)
└── test/                            ← تست‌ها
```

## ⚠️ بلاکر حیاتی
**GATE 0:** محل اقامت پارتنر ثبت نشده → Branch A/B انتخاب نشده → هیچ‌چیز outward اجرا نمی‌شود.

## 🔗 خواهرها
- **Accounting:** درآمد creator → فقط سهم ۵۰٪ آری، کد «Project-F» (privacy).
