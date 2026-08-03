---
type: master-plan
title: OCTOPUS — Parallel-Completion Plan
date: 2026-07-24
owner: ari
status: proposed
scope: "تکمیلِ موازیِ کارِ ارزشمندِ ۲۵ برنچ توسط ایجنت‌های بعدی + حذفِ منسوخ‌ها + مرتب‌سازیِ Obsidian"
source_of_truth: "کد + git (نه گزارشِ ایجنت). هر merge پشتِ safe-patch protocol."
---

# 🐙 OCTOPUS — پلنِ تکمیلِ موازی (2026-07-24)

## ۰) وضعیتِ فعلی (بعد از پاک‌سازی)
- worktrees: **۳۸ → ۱** (فقط ارگانیسمِ زندهٔ `octopus-event-bridge-aligned`).
- branches: **۸۸ → ۳۴** (۲۵ مرور‌شده + ۷ `backup/*` + master + live).
- **حفظِ کامل:** ۲۰ `refs/rescue/*` (دلتای worktreeها) + ۲ `rescue-base` tag + ۱۱ `archive/pc-2026-07-24/*` tag + پچ‌ها. → صفر گم‌شدن، همه برگشت‌پذیر.

## ۱) اصولِ سختِ همهٔ ایجنت‌ها (کپی در سرِ هر مگا-پرامپت)
1. **منبعِ حقیقت = کد + git.** قبل از هر ادعا، `git show`/`git diff` بزن.
2. **safe-patch protocol:** بکاپ → `assert s.count(OLD)==1` → `compile()` قبلِ نوشتن → دو `sha256` → `try/except` دفاعی → **پشتِ فلگِ خاموش**.
3. **TCB دست‌نخورده:** پول / کلیدها / genome / kill-switch. هرگز.
4. **در worktreeِ ایزوله کار کن** (`git worktree add ../wt-<ws> <branch>`)، نه رو درختِ زنده.
5. **flag-off = رفتارِ دقیقاً قبلی** (رگرسیونِ صفر). `_ops/tests/run_all.py` باید سبز بمونه.
6. **kill-switch را محترم بشمار** (`STOP_ORGANISM`/`master_halted()` per-tick).
7. اگر merge باعثِ تغییرِ رفتارِ زنده می‌شه → **پشتِ فلگ + propose-only**، تصمیمِ arm با مالک.

## ۲) workstreamها (هر کدام = یک ایجنتِ مستقل)

| WS | عنوان | منبع (branch / rescue-ref) | خروجیِ مورد انتظار | ریسک |
|---|---|---|---|---|
| **WS-2** | فیکسِ ۵ باگِ قلب | `claude/heart-vessels-debug-52687c` | ۵ فیکس در heart/* + cardiac اعمال، run_all سبز | پایین |
| **WS-3** | یکسان‌سازیِ model_router | `claude/octopus-fugu-everywhere` (+ `model_router.py` از fail-closed) | call-siteهای LLM → model_router، flag-gated | پایین |
| **WS-4** | رصدِ tick-timing | `claude/octopus-tick-decoupling` | `tick_timing.py` + probe، صفر تغییرِ رفتار | خیلی پایین |
| **WS-6** | پکِ امنیتی M1–M7 | `claude/fail-closed-human-guard` | ۷ ماژولِ `now_moves/*` additive/flag-off + تست | پایین |
| **WS-1** | C6 خودبهبودی | `claude/octopus-reproduction-c6` + `claude/c6-self-improvement-ignition-c73186` | `c6_trigger.py` + هوکِ organism (flag-gated) + پچِ memory-index | متوسط |
| **WS-5** | پایپ‌لاینِ lead-gen | `phase-d` | D3–D7 (harvest→funnel→speed-to-lead→release/send→owner-notify)، flag-off | متوسط |
| **WS-7** | Project-F / Saba | `claude/project-f-agent-build-aa512f` | تکمیلِ زیرپروژه (BUILD-ALL، ۴۵۹ تست) | جدا |
| **WS-8** | Ziman / بات‌مامان | `claude/ziman-gif-deep-scan-19ef9a` | `ziman_leg.py` + `mom-bot/` تکمیل | جدا |
| **WS-9** | Painting-OS | `claude/telegram-governance-integration-832984` | کوت/اینویس/ایمیل/intake — verify vs فعلی + تکمیل | ویژه (کسب‌وکار) |
| **WS-10** | control-plane infra | `claude/obsidian-vault-org-swarm-796424` | verify-first: logger/self_model/improve/panic/FLAG-REGISTRY | متوسط |

**Add-onهای verify-first (داخلِ WS نزدیک):**
- `cranky-chandrasekhar` → anti-replayِ پول (approvalِ تک‌مصرف/consume اتمیک/TTL) → **در WS-6** (اگر در master نیست). ⚠️ TCB-adjacent.
- `three-heart-rhythm-math` → `pulse_arbiter.py` → **در WS-2** (اگر تازه).
- `wave1/a-telegram` → Menu v2 + durable OutcomeStore → **در WS-9/telegram** (اگر تازه).

## ۳) موج‌بندیِ اجرا (موازیِ ایمن)

**موجِ ۱ — مستقل، کم‌ریسک، همه با هم:** `WS-2` · `WS-3` · `WS-4` · `WS-6`
> این‌ها additive/flag-off‌اند و فایل‌های مختلف را لمس می‌کنند → تداخلِ merge کم. با worktreeِ جدا موازی.

**موجِ ۲ — متوسط، بعد از سبزشدنِ موجِ ۱:** `WS-1` (C6) · `WS-5` (lead) · `WS-10` (infra)
> C6 به organism هوک می‌زنه؛ بعد از پایدارشدنِ heart/router اجرا شه.

**زیرپروژه‌های مستقل — هر زمان، جدا از هسته:** `WS-7` (Project-F) · `WS-8` (Ziman) · `WS-9` (Painting-OS)

**نقطهٔ همگام‌سازی:** بعد از هر موج، `run_all.py` کاملِ ارگانیسم سبز + مالک deploy/arm را تأیید کند.

## ۴) حذفِ منسوخ‌ها (۱۲ برنچ) — بعد از ساختِ مگا-پرامپت‌ها
**پروتکل:** برای هر برنچ اول `git tag -f archive/superseded-2026-07-24/<name> <branch>` (برگشت‌پذیر)، بعد `git branch -D`.
- منسوخ‌بودنشان چون محتوا در برنچِ کانونیِ نگه‌داشته‌شده هست: `optimistic-maxwell`،`project-analysis-planning`،`saba-vaultbank-tests` → WS-7 · `higgsfield-integration-setup` → WS-8 · `ollama-fugu-brain` → WS-5 · `architecture-docs-5d67ea`،`octopus-architecture-refactor`،`octopus-qa-red-team-findings`،`kind-kirch`،`session-f92f3d` → verify سریع، بعد حذف.
> هیچ برنچی بدونِ archive-tag و OK مالک حذف نمی‌شود.

## ۵) مرتب‌سازیِ Obsidian (گامِ آخر)
- این پلن + مگا-پرامپت‌ها در یک پوشهٔ واحد در vault (مثلاً `04 - Architect System/completion-2026-07-24/`).
- یک نوتِ index با لینکِ `[[...]]` به هر WS.
- نوتِ «نیت‌های حفظ‌شده» (از `session-f92f3d`: fusion-lab، WLOS) قبل از حذفِ برنچ.

## ۶) پیگیریِ وضعیت
| WS | مگا-پرامپت | اجرا | merge سبز |
|---|---|---|---|
| WS-1..WS-10 | ⏳ در حالِ ساخت | — | — |
