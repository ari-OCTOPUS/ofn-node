---
type: proposal
subtype: PHASE_PLAN
status: verified-by-owner
priority: P1
created: 2026-07-09
created_by: agent
verdict: "آری — نگاشت تأیید شد (۲۰۲۶-۰۷-۰۹)"
sources:
  - "[[04 - Architect System/octopus-build-prompts/OCTOPUS-BASE-MAP-v1]]"
  - "[[00 - Inbox/2026-07-09 PROPOSAL — core-restore runbook + E16 human-append guard wiring]]"
  - "[[04 - Architect System/octopus-build-prompts/OVERNIGHT-QUEUE]]"
  - "[[04 - Architect System/octopus-build-prompts/GATEWAY-WIRING-PROPOSAL]]"
tags: [octopus, phase-plan, reverse-map, gates, propose-only]
---

# PHASE PLAN — reverse-map کدهای درختی → فایل/گپِ واقعی (owner-verified)

> کدهای `B5/B7/B8/B6 · C9/C10/C11 · A1/A2` از تری‌مپِ بیرونیِ آری‌اند و در repo تعریف نشده بودند.
> این نگاشت از (۱) توضیحِ دسته‌ایِ آری، (۲) repoِ واقعی (HEAD، post core-restore)، (۳) اسنادِ بالا استنتاج و در ۲۰۲۶-۰۷-۰۹ توسط آری **تأیید** شد.

## ⚠️ integrity caveat (باز — کارِ فقط‌مالک)
core-restore محتوای ۷ فایلِ هستهٔ `_ops/` را از HEADِ سالم بازنویسی کرد (همه parse می‌شوند)، ولی git index از داخلِ sandbox نوشتنی نبود و یک `.git/index.lock` (~۱۲۸KB) جا ماند.
**قبل از هر git (Windows-side):** `del F:\backup\.git\index.lock` → `git status` → در صورت modified بودنِ ۷ فایل: `git restore -- "_ops/wiring.py" "_ops/organism.py" "_ops/unified_bus.py" "_ops/live_loop.py" "_ops/chrono.py" "_ops/doctor/doctor.py" "_ops/doctor/box/sensors.py"`.

## نگاشتِ تأییدشده

### دسته B — روابط ایمن (additive · $0 · propose-only)
| کد | آیتم | فایل مقصد | تگ |
|---|---|---|---|
| B5 | سیم‌کشیِ `human_append_guard` → `unified_bus.publish` (E16؛ params optional، گارد DISABLED) | `_ops/unified_bus.py` + `_ops/budget/human_append_guard.py` | `[FACT]` patch+test موجود |
| B7 | تکمیل/تأییدِ `consolidation` → live loop پشت flag | `_ops/live_loop.py` + `_ops/neural/consolidation.py` | `[FACT]` commit c77238b |
| B8 | خروجیِ doctor BOX B3 → `submit_for_approval` (propose-only) | `_ops/doctor/doctor.py` + `_ops/doctor/box/` | `[FACT]` OVERNIGHT-QUEUE #7 |
| B6 (فاز۲) | کوپلینگِ BOX B4: `φ_t` → Dreamer novelty (ablation on/off) | `_ops/doctor/box/` | `[EST]` شماره |

### دسته C — پاکسازیِ ورودی‌های مرده
| کد | آیتم | فایل مقصد | تگ |
|---|---|---|---|
| C9 | یکسان‌سازیِ drift نسخهٔ ledger `0.4.6 ↔ 0.4.5` | `_ops/unified_bus.py` ↔ `test_chrono_langar` | `[FACT]` drift |
| C10 | reconcileِ تصادمِ alias در LANGAR | `LANGAR-ALIAS-REGISTRY.md` + reconcile | `[OPEN]` |
| C11 (بعداً) | پاکسازیِ لینک شکسته/orphan/ورودیِ مردهٔ afferent | `find_broken_links.py` · `_ops/afferent/sensory_bus.py` | `[FACT]` اسکریپت هست |

### دسته A — زنجیرهٔ پولِ Track-B («راه ب»، پشت flag خاموش)
| کد | آیتم | فایل مقصد | تگ |
|---|---|---|---|
| A1 | سیم‌کشیِ workerهای `glm-coder`+`deepseek-bulk` روی LiteLLM (shadow، loopback، env-only) | `litellm_config.yaml` · `docker-compose.yml` · `.env.example` | `[FACT]` GATEWAY §۲–۳ |
| A2 | سقفِ per-worker در `budgets.yaml` (فقط verdict آری) + NOTE(INFRA_PROPOSAL)؛ shadow/$0 تا ۲۰۲۶-۰۷-۲۱ | `budgets.yaml` (read-only برای agent) · ledger | `[FACT]` GATEWAY §۴–۶ |

### Epistemics (SHADOW-THEORY)
- فاز A (آف‌لوپ): scoringِ shadow + تگِ `[FACT/EST/OPEN]`، بدون اثرِ live. سوبسترا: `04 - Architect System/scripts/governor_shadow.py`.
- فاز B (پشت flag): تزریقِ نمرهٔ shadow به gatingِ governor/doctor، flag پیش‌فرض خاموش.

## ترتیبِ فازها
۱) B5 · B7 · B8 · C9 · C10  ۲) B6  ۳) A1 · A2  ۴) Epistemics-A  ۵) Epistemics-B

## ناوردی‌های حاکم (از OVERNIGHT-QUEUE §قرارداد + Hard Rules)
propose-only · sandbox · human-append برای هر merge · money قفل تا ۲۰۲۶-۰۷-۲۱ · secret فقط env · `budgets.yaml`/HRV/genome/charter دست‌نخورده · هیچ اثرِ live/شبکه/پول · هر feature-flag پیش‌فرض **خاموش** · ledger فقط append (بدون schema-change/spend).
