---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft
tags: [octopus, prompt, build, index]
created: 2026-07-08
updated: 2026-07-08
created_by: agent
---

# Octopus Build Prompts — INDEX (run in order)

> **برای آری:** این یک سری پرامپتِ **جدا برای هر مرحله** است. هر فایل را جداگانه به ایجنتِ کدنویس بده، به همین ترتیب. هر مرحله پیش‌نیازِ مرحلهٔ بعد است. قانونِ ثابت: هیچ‌چیز بدونِ تاییدِ تلگرامیِ تو زنده/برگشت‌ناپذیر نمی‌شود؛ صفر fabrication؛ additive.

## Order

| # | Prompt | Goal | Gate to next |
|---|---|---|---|
| 0 | `00 - Inbox/2026-07-08 Prompt - OCTOPUS Deep Recon` | نقشهٔ دقیقِ کدِ فعلی (`OCTOPUS-RECON-MAP.md`) | map complete |
| — | `00 - Inbox/2026-07-08 Prompt - OCTOPUS Master Build` | نمای کلی + قوانینِ کامل (مرجع) | — |
| 1 | `P1-HEART.md` | قلب/ضربان (Chrono substrate) — **اول و مهم‌ترین** | heartbeat + age_tick + effect-gate green |
| 2 | `P2-DOCTOR.md` | دکترِ تکاملیِ انگلی روی سر | anchored RFC loop, human-gated |
| 3 | `P3-TELEGRAM.md` | تلگرام = تنها کانال، UI برای هر کارکرد | approve/deny end-to-end (paper) |
| 4 | `P4-LEGS.md` | پروژه‌ها → پا (Worker) | Lead-نقاشی paper-$ CONFIRMED |
| 5 | `P5-STAY-ALIVE-COHERENCE.md` | پایدارماندن ۲۴/۷ + یک ارگانیسمِ واحد | 24h green + one ledger/bus |
| 6 | `P6-MONEY-LIVE.md` | پولِ واقعی — **آخر، human-gated** | all gates green + owner flag |

> **وضعیت (2026-07-08):** P1 ✅ **implemented** — کد ساخته شد (shadow ‏۱۳/۱۳ + ۶/۶ سبز؛ [[00 - Inbox/2026-07-08 OCTOPUS-P1-HEART-REPORT — قلب ساخته شد (chrono substrate)|گزارش]]). اجرای authoritative سوئیت + commit **Windows-side** مانده (torn-mount سندباکس). گیت P2 (Doctor) پس از آن باز.
> **➡️ قدمِ بعدی (verdict آری جلسه ۳۲):** پیش از هر فازِ نو، [[04 - Architect System/octopus-build-prompts/NEXT-AGENT-ROADMAP — Octopus Base-Map & Workflow|نقشهٔ پایه + ورکفلوِ واحد]] طراحی شود.

## Shared laws (every prompt enforces)
Propose-don't-execute · human-append (Telegram) for every irreversible effect · `age_tick=is_human` · additive-only (`/_legacy`) · no uncosted capability · secrets from env only · kill-switch supreme · **no live money before Phase 6** · financial-action ban (never trade/move funds) · no fabrication (cite `path:line`) · every module has $0 offline tests. Full text: the Master Build prompt §1.

> ⚠️ **2026-07-08:** قانونِ مشترکِ `age_tick=is_human` با verdictِ مالک به **heart-driven** تغییر کرد → **پیاده شد (genome v0.4.6):** age_tick با human یا heartbeat (`beat=1`، هر `CHRONO_AGE_PER_N_BEATS`=۶۰ ضربان) جلو می‌رود؛ versioned با `age_rule` تا legacy (TINV-3ِ قدیم) verify شود. تأییدِ Windows-side (سوئیت کامل) + commit مانده — [[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]].

## Prereq before Phase 1
Run Phase 0 (Recon). If `OCTOPUS-RECON-MAP.md` is missing, stop and produce it first.
