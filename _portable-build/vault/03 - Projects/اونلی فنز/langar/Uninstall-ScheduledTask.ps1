# ============================================================
# Uninstall-ScheduledTask.ps1 — حذف Scheduled Task بات لنگر
# Project-F · 2026-07-16
# ============================================================

$taskName = "ProjectF-Langar-Bot"

if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "✅ Scheduled Task حذف شد: $taskName" -ForegroundColor Green
} else {
    Write-Host "task وجود ندارد: $taskName" -ForegroundColor Yellow
}
