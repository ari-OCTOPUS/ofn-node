# tg-center-watchdog.ps1 — keep the Telegram group command centre (center.py) alive.
#
# Owner chose "زنده کن + سرپرست" for the group command centre (2026-07-18).
# The centre is a poller (no HTTP port), so liveness is checked by process command-line,
# not by port. If it is down, relaunch RUN-TG-CENTER.bat.
#
# Register ONCE (owner action — system setting):
#   schtasks /Create /TN "OCTOPUS-TG-Center-Watchdog" /SC MINUTE /MO 5 ^
#     /TR "powershell -NoProfile -ExecutionPolicy Bypass -File F:\backup\_ops\tg-center-watchdog.ps1" /F
# Off switch (stop auto-revival AND cleanly stop the centre):
#   create the file  F:\backup\_ops\STOP-TG-CENTER   (centre exits next cycle; watchdog won't relaunch)
# Remove the task:
#   schtasks /Delete /TN "OCTOPUS-TG-Center-Watchdog" /F
#
# SCOPE: supervises ONLY the group centre (center.py, TG_CENTER_BOT_TOKEN). Independent of
# organism-watchdog (8771) and live-watchdog (8773) — a separate concern, separate task.

$ErrorActionPreference = 'SilentlyContinue'
$ops = 'F:\backup\_ops'
$logDir = Join-Path $ops 'state'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$log = Join-Path $logDir 'tg-center-watchdog-log.txt'

# 0) D-G (2026-07-21): global panic (HALT-ALL) or architect STOP overrides EVERY supervisor -> never
#    revive under panic. (Previously this watchdog saw only STOP-TG-CENTER and ignored the global kill.)
if ((Test-Path (Join-Path $ops 'HALT-ALL')) -or (Test-Path (Join-Path (Split-Path $ops -Parent) 'STOP'))) {
    Add-Content -Path $log -Value "$(Get-Date -Format s) global HALT-ALL/architect-STOP present - not reviving centre"
    exit 0
}
# 1) owner off-switch: STOP-TG-CENTER means "leave the centre down on purpose"
if (Test-Path (Join-Path $ops 'STOP-TG-CENTER')) {
    Add-Content -Path $log -Value "$(Get-Date -Format s) STOP-TG-CENTER present - not reviving centre"
    exit 0
}

# 2) already covered? RUN-TG-CENTER.bat is itself a self-restarting LOOP, so we must
#    check for BOTH the centre python AND a live loop launcher. If either exists, do
#    nothing — otherwise we would spawn a SECOND loop during the loop's brief respawn
#    gap and end up with two centres 409-fighting over the same TG_CENTER_BOT_TOKEN.
$center = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
          Where-Object { $_.CommandLine -match 'center\.py' }
$loop = Get-CimInstance Win32_Process -Filter "Name='cmd.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'RUN-TG-CENTER' }
if ($center -or $loop) { exit 0 }

# 3) neither centre nor its loop is alive -> relaunch the loop launcher (hidden)
Add-Content -Path $log -Value "$(Get-Date -Format s) centre+loop both down - launching RUN-TG-CENTER.bat"
Start-Process -FilePath (Join-Path $ops 'telegram_center\RUN-TG-CENTER.bat') -WindowStyle Hidden
