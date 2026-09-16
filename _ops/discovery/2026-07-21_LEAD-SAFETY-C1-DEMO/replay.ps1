# replay.ps1 — LEAD-SAFETY-C1 dry-run demo، ۵ فرمان برای مالک (worktree-only، صفر ارسال).
# اجرا:  powershell -ExecutionPolicy Bypass -File replay.ps1
# هیچ فلگِ زنده‌ای عوض نمی‌شود؛ همه‌چیز در sandboxِ موقتِ خودِ demo_run.py.

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

Write-Host "── ۱) کلِ قوس در sandbox (synthetic → gate → NOT_ARMED) → چک‌لیست ۹/۹ ──" -ForegroundColor Cyan
python -X utf8 demo_run.py

Write-Host "`n── ۲) receiptهای خواندنی (event_type/correlation، بدونِ secret) ──" -ForegroundColor Cyan
Get-Content (Join-Path $here 'last-run-receipts.json') | Select-Object -First 60

Write-Host "`n── ۳) گیتِ per-effect: تست ۱۳/۱۳ (footgun بسته، synthetic/market_signal deny) ──" -ForegroundColor Cyan
python -X utf8 (Join-Path $here '..\..\tests\test_lead_effect_gate.py')

Write-Host "`n── ۴) staleness + صداقتِ audit: تست ۹/۹ ──" -ForegroundColor Cyan
python -X utf8 (Join-Path $here '..\..\tests\test_effector_gate_bridge.py')

Write-Host "`n── ۵) تأییدِ ایمنی: صفر فلگِ ACTIVATION مسلح روی درختِ زنده ──" -ForegroundColor Cyan
$flags = Get-ChildItem 'F:\backup\_ops' -Filter 'ACTIVATION-*.flag' -Recurse -ErrorAction SilentlyContinue
if ($flags) { Write-Host "⚠ فلگِ مسلح: $($flags.Name)" -ForegroundColor Red } else { Write-Host "✅ صفر ACTIVATION-*.flag — لِینِ ارسال/پول بسته" -ForegroundColor Green }
