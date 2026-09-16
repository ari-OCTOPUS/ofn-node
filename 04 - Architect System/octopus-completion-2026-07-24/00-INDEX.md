---
type: index
title: OCTOPUS Completion — Index & Status
date: 2026-07-24
owner: ari
status: active
---

# 🐙 OCTOPUS — پاک‌سازی + تکمیلِ موازی — ایندکسِ اصلی (2026-07-24)

این پوشه همه‌چیزِ نشستِ پاک‌سازی/تکمیل را نگه می‌دارد. نقطهٔ شروع همین فایل است.

## 📊 چه شد (خلاصهٔ اجرایی)
- **worktrees: ۳۸ → ۱** (فقط ارگانیسمِ زندهٔ `octopus-event-bridge-aligned`). این سنگینیِ اصلیِ دیسک بود.
- **branches: ۸۸ → ۳۴** (بعد از حذفِ منسوخ‌ها → ۲۳ می‌شود).
- **صفر گم‌شدن:** هر کارِ کامیت‌نشده در `refs/rescue/*`، هر برنچِ حذف‌شده در `archive/*` tag. → [[06-PRESERVATION-INDEX|OCTOPUS-PRESERVATION-INDEX-2026-07-24]].
- **۲۵ برنچ کامل مرور شد** (فایل‌به‌فایل نسبت به master). → [[01-REVIEW-COMPLETE|OCTOPUS-REVIEW-COMPLETE-2026-07-24]].

## 🗺️ اسناد
| سند | نقش |
|---|---|
| [[01-REVIEW-COMPLETE|OCTOPUS-REVIEW-COMPLETE-2026-07-24]] | بررسیِ کاملِ ۲۵ برنچ + دسته‌بندی |
| [[02-PARALLEL-COMPLETION-PLAN|OCTOPUS-PARALLEL-COMPLETION-PLAN-2026-07-24]] | پلنِ master: ۱۰ workstream + موج‌بندی |
| [[03-MEGAPROMPTS-WAVE1|MEGAPROMPTS-WAVE1-2026-07-24]] | WS-2 قلب · WS-3 router · WS-4 tick · WS-6 امنیت |
| [[04-MEGAPROMPTS-WAVE2|MEGAPROMPTS-WAVE2-2026-07-24]] | WS-1 C6 · WS-5 lead-gen · WS-10 infra |
| [[05-MEGAPROMPTS-SUBPROJECTS|MEGAPROMPTS-SUBPROJECTS-2026-07-24]] | WS-7 Project-F · WS-8 Ziman · WS-9 Painting-OS |
| [[06-PRESERVATION-INDEX|OCTOPUS-PRESERVATION-INDEX-2026-07-24]] | فهرستِ حفاظت + دستورِ بازیابی |

## ✅ وضعیتِ workstreamها
| WS | عنوان | مگا-پرامپت | اجرا |
|---|---|---|---|
| WS-2 | فیکسِ باگ‌های قلب | ✅ | 🟡 **اجرا شد** توسط ایجنت (worktree ایزوله، uncommitted، سوئیت در حالِ اجرا) |
| WS-3 | model_router | ✅ | 🟡 با WS-2 در همان worktree |
| WS-4 | tick-timing | ✅ | 🟡 با WS-2 |
| WS-6 | پکِ امنیتی M1–M7 | ✅ | 🟡 با WS-2 (⚠️ armِ M3/cortex-revive تصمیمِ مالک) |
| WS-1 | C6 خودبهبودی | ✅ | ⏳ آمادهٔ ایجنت |
| WS-5 | lead-gen | ✅ | ⏳ |
| WS-10 | control-plane infra | ✅ | ⏳ (verify-first) |
| WS-7 | Project-F/Saba | ✅ | ⏳ (زیرپروژه) |
| WS-8 | Ziman/بات‌مامان | ✅ | ⏳ (زیرپروژه) |
| WS-9 | Painting-OS | ✅ | ⏳ (زیرپروژه، اولویتِ کسب‌وکار) |

## 🗑️ حذفِ ۱۱ برنچِ منسوخ (حفاظت‌شده، فقط ref می‌رود)
همه از قبل `archive/superseded-2026-07-24/*` tag خورده‌اند (برگشت‌پذیر). حذفِ ref نیازِ اجرای native دارد (پلِ دستگاه حذف نمی‌کند). روی PowerShell:

```powershell
Set-Location F:\backup
$del=@('claude/optimistic-maxwell-252c15','claude/project-analysis-planning-4b34df','claude/saba-vaultbank-tests-b17770',
 'claude/higgsfield-integration-setup-b8892a','claude/ollama-fugu-brain-54c897','claude/architecture-docs-5d67ea',
 'claude/octopus-architecture-refactor-c5e979','claude/octopus-qa-red-team-findings-32cf81','claude/kind-kirch-44b3ff',
 'claude/session-f92f3d','claude/three-heartbeat-systems-523a74')
foreach($b in $del){ git show-ref --verify --quiet "refs/heads/$b"; if($LASTEXITCODE -eq 0){ git branch -D $b 2>&1|Out-Host } }
git tag -d archive/superseded-2026-07-24/TEST 2>$null   # پاک‌سازیِ tagِ آزمایشی
Write-Host ("branches_now={0}" -f ((git for-each-ref refs/heads/|Measure-Object).Count))
```
> پس از این: ۳۴ → ۲۳ برنچ (۱۴ کارِ زنده/کانونی + ۷ `backup/*` + master + live). هرکدام لازم شد: `git branch <name> archive/superseded-2026-07-24/<name>`.

## ➡️ گام‌های بعدی (owner-gated)
1. سوئیتِ موجِ ۱ تمام شود → اگر تنها ۲ خطای نامرتبط بود، ایجنت روی برنچِ خودش commit کند (نه master).
2. اجرای موجِ ۲ + زیرپروژه‌ها (هر مگا-پرامپت = یک ایجنت).
3. merge به master / arm فلگ‌ها **فقط با راست‌آزمایی + OKِ صریحِ تو** (§۱ پلن).
4. اجرای اسکریپتِ حذفِ بالا (کاهشِ نهاییِ حجم).
