---
type: execution-prompts
title: OCTOPUS Final Execution — Delete + Reconcile
date: 2026-07-24
note: "دو پرامپتِ standalone برای ایجنتِ نیتیو (یا اجرای مستقیمِ مالک). هر کدام امن + رول‌بک‌دار + گزارش‌ده."
---

# ⚙️ اجرای نهایی — حذفِ منسوخ‌ها + آشتیِ split-brain

> **چطور اجرا شود:** روی ویندوز (native)، مثلِ موج ۱ و ۲. EXEC-A مستقل و بی‌خطر است؛ EXEC-B فازِ زندهٔ خود را **فقط با go/no-go تو** انجام می‌دهد. بعد از هر کدام، خروجی را برای راست‌آزمایی به من بده.

---

## EXEC-A — حذفِ ۱۱ برنچِ منسوخ  (بی‌خطر، برگشت‌پذیر)

**نقش:** اپراتورِ دقیقِ git. **پیش‌شرط:** هر ۱۱ برنچ از قبل `archive/superseded-2026-07-24/*` tag دارند (برگشت‌پذیر) — پس `-D` امن است.

```powershell
Set-Location F:\backup
$del=@('claude/optimistic-maxwell-252c15','claude/project-analysis-planning-4b34df','claude/saba-vaultbank-tests-b17770',
 'claude/higgsfield-integration-setup-b8892a','claude/ollama-fugu-brain-54c897','claude/architecture-docs-5d67ea',
 'claude/octopus-architecture-refactor-c5e979','claude/octopus-qa-red-team-findings-32cf81','claude/kind-kirch-44b3ff',
 'claude/session-f92f3d','claude/three-heartbeat-systems-523a74')
foreach($b in $del){ git show-ref --verify --quiet "refs/heads/$b"; if($LASTEXITCODE -eq 0){ Write-Host "del $b"; git branch -D $b 2>&1|Out-Host } else { Write-Host "absent $b" } }
git tag -d archive/superseded-2026-07-24/TEST 2>$null
Write-Host ("`nbranches_now={0} (انتظار: 23)" -f ((git for-each-ref refs/heads/|Measure-Object).Count))
git branch --format='%(refname:short)' | Sort-Object
```
**بازیابیِ هر کدام:** `git branch <name> archive/superseded-2026-07-24/<name>`
**گزارش بده:** لیستِ حذف‌شده + عددِ نهایی.

---

## EXEC-B — آشتیِ split-brain (عمدی؛ فازِ زنده owner-gated)

**نقش:** مهندسِ ارشد + مهندسِ ایمنی. **هدف:** آوردنِ کارِ master به ارگانیسمِ زنده، بدونِ شکستنِ چیزِ در حالِ اجرا.
**قوانینِ سخت:** TCB دست‌نخورده · هیچ فلگی arm نشود · قبلِ cutoverِ زنده، ارگانیسم خاموش · رول‌بک آماده · merge از قبل تست‌شده.

### فاز ۰ — نقاطِ رول‌بک
```powershell
Set-Location F:\backup
git tag backup/live-pre-reconcile-2026-07-24  claude/octopus-event-bridge-aligned
git tag backup/master-pre-reconcile-2026-07-24 master
```
### فاز ۱ — پیش‌آزمون در worktreeِ ایزوله (ارگانیسم **روشن می‌ماند**؛ اینجا فقط تست)
```powershell
git worktree add ../oct-reconcile claude/octopus-event-bridge-aligned
Set-Location ..\oct-reconcile
git merge master     # انتظار: CLEAN (۲ فایلِ مشترک — event_bridge.py/center.py — بایت‌یکسان‌اند). اگر conflictِ غیرمنتظره: به‌نفعِ hardeningِ تازه‌ترِ master، TCB را دست نزن، گزارش بده.
$env:REAL_VAULT=(Resolve-Path .).Path
python _ops\tests\run_all.py    # باید کامل سبز باشد (جز خطاهای نامرتبطِ شناخته‌شده اگر بود)
Write-Host "armed dangerous flags? (باید خالی باشد):"
findstr /n /c:"=1" _ops\OCTOPUS-flags.cmd | findstr /i "C6_RESEARCH KILL_SEAM CORTEX_REVIVE LEAD_OUTBOUND"
```
### ⏸️ ایست + گزارش (قبل از هر لمسِ زنده)
نتیجهٔ سوئیت + تأییدِ clean بودنِ merge + وضعیتِ فلگ‌ها را بده. **go/no-go برای cutoverِ زنده با مالک.**

### فاز ۲ — cutoverِ زنده (فقط با «برو»ی مالک)
```powershell
# ۱) HALT: STOP-ORGANISM.flag بساز یا /panic؛ فریزِ state/pulse را تأیید کن.
# ۲) merge روی درختِ زنده (خاموش، merge از قبل تست‌شده):
Set-Location F:\backup
git merge master
# ۳) restart:
.\RESTART-ORGANISM.bat
# ۴) تأیید: بوت سالم · 8771/8772 بالا · run_all سبز · هیچ فلگی armنشده · kill-switch کار می‌کند.
```
### رول‌بکِ فوری (اگر هرچیزی خراب شد)
```powershell
# ارگانیسم را خاموش کن، بعد:
git reset --hard backup/live-pre-reconcile-2026-07-24
.\RESTART-ORGANISM.bat
```
**گزارش بده:** clean بودنِ merge · عددِ سوئیت · وضعیتِ فلگ‌ها · (اگر cutover شد) سلامتِ بوت.

---

## بعد از EXEC-B (اختیاری، جدا)
برنچِ موج‌ها (`megaprompts-octopus-review @ 59dcdc7`) حالا تمیز روی زندهٔ آشتی‌شده merge می‌شود → قلب/امنیت/lead-gen/هوکِ C6 زنده و قابلِ arm. arm همیشه دستِ توست.
