# register-tg-center-watchdog.ps1 — OWNER-GATED registration of the Telegram-centre watchdog task.
#
# WHAT: registers a Windows Scheduled Task that runs _ops\tg-center-watchdog.ps1 every 5 minutes,
#       so the TG group command centre (center.py) is auto-revived after an UNPLANNED death.
#       Mirrors the cadence/pattern of the cortex/live watchdog tasks; the centre currently has
#       NO registered task (deployment-audit gap) — this script is the registration design for it.
#
# WHY a wrapper (not a bare schtasks line): the centre watchdog MUST run SINGLE-INSTANCE
# (MultipleInstances=IgnoreNew) so two 5-min ticks never overlap and spawn two centres that
# 409-fight over TG_CENTER_BOT_TOKEN, and with WorkingDirectory=F:\backup\_ops so its relative
# Join-Path calls resolve. The plain `schtasks /Create` CLI cannot set MultipleInstances; the
# ScheduledTasks cmdlets can — hence this wrapper. (schtasks-XML fallback is in the design note.)
#
# SAFETY — this file is SOURCE ONLY and does NOTHING by default:
#   * No args = DRY-RUN: prints the task it *would* create, registers nothing.
#   * Only `-Apply` calls Register-ScheduledTask. Registration touches a system setting and is
#     an OWNER action (the owner-gated deploy step), never the author's.
#
# The watchdog it schedules already yields to (enforced inside tg-center-watchdog.ps1 itself):
#   * HALT-ALL        (F:\backup\_ops\HALT-ALL)        — global panic, senior to all
#   * architect STOP  (F:\backup\STOP)                 — architect-level kill
#   * STOP-TG-CENTER  (F:\backup\_ops\STOP-TG-CENTER)  — owner off-switch for the centre
# so the scheduled task never revives the centre while any of those markers exist.
#
# Owner usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File F:\backup\_ops\register-tg-center-watchdog.ps1          # dry-run
#   powershell -NoProfile -ExecutionPolicy Bypass -File F:\backup\_ops\register-tg-center-watchdog.ps1 -Apply   # actually register
# Remove later:
#   Unregister-ScheduledTask -TaskName 'OCTOPUS-TG-Center-Watchdog' -Confirm:$false
#   (equivalently: schtasks /Delete /TN "OCTOPUS-TG-Center-Watchdog" /F)

[CmdletBinding()]
param([switch]$Apply)

$ErrorActionPreference = 'Stop'

$TaskName = 'OCTOPUS-TG-Center-Watchdog'
$Ops      = 'F:\backup\_ops'
$Script   = Join-Path $Ops 'tg-center-watchdog.ps1'
$PsExe    = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'

if (-not (Test-Path $Script)) {
    throw "watchdog script not found: $Script (refusing to register a task pointing at a missing file)"
}

$action = New-ScheduledTaskAction `
    -Execute  $PsExe `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Script`"" `
    -WorkingDirectory $Ops

# Every 5 minutes, indefinitely (mirrors cortex/live watchdog cadence).
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 5) `
    -RepetitionDuration ([TimeSpan]::MaxValue)

# SINGLE-INSTANCE: never let two ticks overlap (would 409-fight over the bot token).
# ExecutionTimeLimit caps a wedged tick so it cannot pin the slot forever.
$settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 4) `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

if (-not $Apply) {
    Write-Host "DRY-RUN (no -Apply): would register scheduled task '$TaskName'"
    Write-Host "  Execute  : $PsExe"
    Write-Host "  Argument : -NoProfile -ExecutionPolicy Bypass -File `"$Script`""
    Write-Host "  WorkDir  : $Ops"
    Write-Host "  Trigger  : every 5 min (indefinite)"
    Write-Host "  Instances: IgnoreNew (single-instance)   TimeLimit: 4 min"
    Write-Host "Re-run with -Apply to actually register (OWNER action; touches a system setting)."
    return
}

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action   $action `
    -Trigger  $trigger `
    -Settings $settings `
    -Description 'Auto-revive the Telegram group command centre (center.py). Yields to HALT-ALL / architect STOP / STOP-TG-CENTER.' `
    -Force | Out-Null
Write-Host "Registered scheduled task '$TaskName'."
