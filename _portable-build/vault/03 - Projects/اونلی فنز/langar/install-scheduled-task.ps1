# ============================================================
# install-scheduled-task.ps1 — نصب Scheduled Task برای بات لنگر
# Project-F · 2026-07-16
#
# اجرا (در PowerShell با دسترسی ادمین):
#   powershell -ExecutionPolicy Bypass -File install-scheduled-task.ps1
#
# اثر: یک task می‌سازد که در startup و با لاگین، run-langar.bat را اجرا می‌کند.
# اگر بات crash کند، run-langar.bat خودش restart می‌دهد (loop).
# حذف: Uninstall-ScheduledTask.ps1
# ============================================================

$ErrorActionPreference = "Stop"

$taskName = "ProjectF-Langar-Bot"
$batPath  = Join-Path $PSScriptRoot "run-langar.bat"

if (-not (Test-Path $batPath)) {
    Write-Error "run-langar.bat یافت نشد در: $batPath"
    exit 1
}

# اگه task قبلاً وجود دارد، حذف کن
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Write-Host "task قبلاً وجود دارد — حذف و بازسازی..."
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

$action    = New-ScheduledTaskAction -Execute $batPath -WorkingDirectory $PSScriptRoot
$trigger   = New-ScheduledTaskTrigger -AtLogOn
$settings  = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero)

$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Project-F Langar bot — auto-start on login, auto-restart on crash" | Out-Null

Write-Host ""
Write-Host "✅ Scheduled Task نصب شد: $taskName" -ForegroundColor Green
Write-Host "   bat: $batPath"
Write-Host ""
Write-Host "تست فوری:"
Write-Host "   Start-ScheduledTask -TaskName '$taskName'"
Write-Host ""
Write-Host "وضعیت:"
Write-Host "   Get-ScheduledTask -TaskName '$taskName' | Get-ScheduledTaskInfo"
Write-Host ""
Write-Host "حذف:"
Write-Host "   .\Uninstall-ScheduledTask.ps1"
