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
if ((Test-Path (Join-Path $ops 'HALT-ALL')) -or (Test-Path (Join-Path (Split-Path $ops -Parent) 'STOP')) -or (Test-Path (Join-Path (Split-Path $ops -Parent) '04 - Architect System\STOP'))) {
    Add-Content -Path $log -Value "$(Get-Date -Format s) global HALT-ALL/architect-STOP present - not reviving centre"
    exit 0
}
# 1) owner off-switch: STOP-TG-CENTER means "leave the centre down on purpose"
if (Test-Path (Join-Path $ops 'STOP-TG-CENTER')) {
    Add-Content -Path $log -Value "$(Get-Date -Format s) STOP-TG-CENTER present - not reviving centre"
    exit 0
}

# 2) centre alive -> nothing to do. This is the only silent-and-correct exit.
$center = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
          Where-Object { $_.CommandLine -match 'center\.py' }
if ($center) { exit 0 }

# 3) centre is DOWN. The old rule stopped here whenever a loop process existed, on the
#    theory that RUN-TG-CENTER.bat would respawn it within ~10s. On 2026-07-29 that
#    assumption failed: the centre was dead from ~20:28 to ~20:42 and this watchdog
#    logged NOTHING, because a loop process was alive. A live loop that has stopped
#    respawning looks exactly like a healthy centre. Owner verdict: fix it.
#
#    The fix needs evidence, not a guess. center.py now writes state/pulse/tg-center.json
#    every loop iteration, so "how long has the centre really been silent?" is answerable.
#    Grace window: a healthy iteration is well under 30s, so 180s is ~6x headroom and
#    leaves the loop's own respawn untouched in the normal case.
$loop = Get-CimInstance Win32_Process -Filter "Name='cmd.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'RUN-TG-CENTER' }
$pulse = Join-Path $ops 'state\pulse\tg-center.json'
$silent = 999999
if (Test-Path $pulse) {
    try {
        $ts = (Get-Content $pulse -Raw | ConvertFrom-Json).ts
        $silent = [int]((Get-Date) - [datetime]$ts).TotalSeconds
    } catch { $silent = 999999 }   # پالسِ خراب = بی‌خبری، نه سلامت
}

if ($loop -and $silent -lt 180) {
    # loop alive and the centre pulsed recently -> it is mid-respawn. Leave it alone;
    # spawning here is what would create two pollers on one token (409).
    exit 0
}

# 4) relaunch. If a stale loop exists it is not doing its job, so it is stopped FIRST —
#    otherwise we would end up with two loops, the exact 409 the old rule feared.
#
#    2026-07-29, learned the hard way an hour after writing this: killing the cmd.exe
#    loop does NOT kill its python child. A real incident that evening had TWO centres
#    alive at once (pids 23892 + 10096) both polling one token, because one loop had
#    died and left its child orphaned while a new loop spawned a second child. So the
#    child is swept too — an orphan centre has no supervisor and will never be reaped.
if ($loop) {
    Add-Content -Path $log -Value "$(Get-Date -Format s) centre down ${silent}s but loop alive - stopping $(@($loop).Count) stale loop(s)"
    foreach ($l in @($loop)) { Stop-Process -Id $l.ProcessId -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 2
    $orphans = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
                 Where-Object { $_.CommandLine -match 'center\.py' })
    if ($orphans.Count -gt 0) {
        Add-Content -Path $log -Value "$(Get-Date -Format s) reaping $($orphans.Count) orphan centre process(es)"
        foreach ($o in $orphans) { Stop-Process -Id $o.ProcessId -Force -ErrorAction SilentlyContinue }
    }
    Start-Sleep -Seconds 2
}
Add-Content -Path $log -Value "$(Get-Date -Format s) centre down (silent ${silent}s) - launching RUN-TG-CENTER.bat"
Start-Process -FilePath (Join-Path $ops 'telegram_center\RUN-TG-CENTER.bat') -WindowStyle Hidden

# 5) prove exactly one loop survived — two loops on one bot token is the failure this
#    whole function exists to avoid, and silence about it is how it went unnoticed before.
Start-Sleep -Seconds 15
$afterLoop = @(Get-CimInstance Win32_Process -Filter "Name='cmd.exe'" -ErrorAction SilentlyContinue |
               Where-Object { $_.CommandLine -match 'RUN-TG-CENTER' })
$afterCtr = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
              Where-Object { $_.CommandLine -match 'center\.py' })
if ($afterLoop.Count -ne 1 -or $afterCtr.Count -gt 1) {
    Add-Content -Path $log -Value "$(Get-Date -Format s) WARNING: $($afterLoop.Count) loop(s) + $($afterCtr.Count) centre(s) after relaunch - expected 1+1 (409 risk)"
}
