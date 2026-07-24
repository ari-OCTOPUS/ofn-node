# cortex-watchdog.ps1 - supervises cortex (brain, port 8772).
# Deliberately separate from organism-watchdog.ps1 (split-brain note R-19):
# that file supervises ONLY organism (8771) and refuses cortex to avoid
# a duplicate scheduled task. This file is the missing cortex twin.
#
# Verdict 2026-07-18 integration-debug: cortex was alive but unsupervised;
# if it crashes there was no auto-revive. This script closes that gap.
#
# Owner registers ONCE:
#   schtasks /Create /TN "OCTOPUS-Cortex-Watchdog" /SC MINUTE /MO 5 /TR "powershell -NoProfile -ExecutionPolicy Bypass -File F:\backup\_ops\cortex-watchdog.ps1"
# Remove:
#   schtasks /Delete /TN "OCTOPUS-Cortex-Watchdog" /F
#
# Manual boot:
#   schtasks /Create /TN "OCTOPUS-Cortex" /SC ONLOGON /TR "F:\backup\_ops\RUN-CORTEX.bat"
#
# Logic: ping port 8772; if not listening for 2 consecutive checks → REVIVE.
# STOP-CORTEX file always wins (clean kill). Watchdog never overrides a stop.

$ops = Split-Path -Parent $MyInvocation.MyCommand.Path
$logDir = Join-Path $ops "state"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$log = Join-Path $logDir "watchdog-log.txt"
$stopFile = Join-Path $ops "STOP-CORTEX"
$staleFile = Join-Path $logDir "cortex-watchdog.json"

# D-G (2026-07-20): global panic (HALT-ALL) or architect STOP overrides EVERY supervisor -> never
# revive under panic. (Previously this watchdog saw only STOP-CORTEX and ignored the global kill.)
if ((Test-Path (Join-Path $ops 'HALT-ALL')) -or (Test-Path (Join-Path (Split-Path $ops -Parent) 'STOP')) -or (Test-Path (Join-Path (Split-Path $ops -Parent) '04 - Architect System\STOP'))) {
    Add-Content -Path $log -Value "$(Get-Date -Format s) cortex: global HALT-ALL/architect-STOP present (no revive)"
    return
}
# STOP-CORTEX always wins — do nothing (clean kill honored).
if (Test-Path $stopFile) {
    Add-Content -Path $log -Value "$(Get-Date -Format s) cortex: STOP-CORTEX honored (no revive)"
    return
}

# Port probe (single source of truth: 8772 LISTEN).
$listening = $false
try {
    $conn = Get-NetTCPConnection -LocalPort 8772 -State Listen -ErrorAction SilentlyContinue
    if ($conn) { $listening = $true }
} catch {
    # Get-NetTCPConnection may fail on some Windows builds; fall back to Test-NetConnection.
    try {
        $tnc = Test-NetConnection -ComputerName 127.0.0.1 -Port 8772 -WarningAction SilentlyContinue
        if ($tnc.TcpTestSucceeded) { $listening = $true }
    } catch { $listening = $false }
}

$now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()

if ($listening) {
    # Cortex alive — reset attempts, write heartbeat.
    $stale = @{ status = "alive"; attempts = @(); last_check = $now } | ConvertTo-Json -Compress
    [System.IO.File]::WriteAllText($staleFile, $stale, [System.Text.UTF8Encoding]::new($false))
    Add-Content -Path $log -Value "$(Get-Date -Format s) cortex: alive on 8772"
    return
}

# Not listening — read prior attempts to count consecutive failures.
$attempts = @()
try {
    $prior = Get-Content $staleFile -Raw -ErrorAction Stop | ConvertFrom-Json
    if ($prior.attempts) { $attempts = @($prior.attempts) }
} catch { $attempts = @() }

# Only keep attempts from the last 15 minutes (3 missed 5-min checks).
$cutoff = $now - 900
$attempts = @($attempts | Where-Object { $_ -gt $cutoff })
$attempts += $now

if ($attempts.Count -ge 2) {
    # 2 consecutive misses → REVIVE (single-shot; reset attempts to avoid pile-up).
    Add-Content -Path $log -Value "$(Get-Date -Format s) cortex: REVIVE (2 consecutive misses)"
    Start-Process -FilePath (Join-Path $ops "RUN-CORTEX.bat") -WindowStyle Hidden
    Add-Content -Path $log -Value "$(Get-Date -Format s) cortex: launched RUN-CORTEX.bat"
    $attempts = @()  # reset; give it a fresh window
}

$stale = @{ status = "dead"; attempts = $attempts; last_check = $now } | ConvertTo-Json -Compress
[System.IO.File]::WriteAllText($staleFile, $stale, [System.Text.UTF8Encoding]::new($false))
Add-Content -Path $log -Value "$(Get-Date -Format s) cortex: dead (miss $($attempts.Count)/2)"
