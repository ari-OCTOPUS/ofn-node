# RESTART-CORTEX.ps1 - clean restart of the cortex process (owner-run).
#
# Why this script exists (2026-07-28):
#   RUN-CORTEX.bat does NOT kill the running instance. If you launch it while
#   the old process still holds port 8772, the new one cannot bind and exits
#   silently - you get "restarted" with the OLD code still running. That is
#   exactly what happened twice today: cortex kept running 3h-old code and
#   overwrote the organism's freshly calibrated stress value every ~45s.
#
# The documented clean kill is the STOP-CORTEX marker, but cortex only checks
# it at the TOP of each ~120s cycle. Deleting the marker too early means the
# process never sees it. This script removes that timing race: it waits for
# the port to actually free before deleting the marker and relaunching.
#
# On timeout it deletes the marker anyway and reports failure - a stray
# STOP-CORTEX would keep the brain asleep forever, which is worse than a
# failed restart.
#
# Output is ASCII-only on purpose: Persian strings pasted back into a console
# get re-executed as commands and produce confusing errors.

$ErrorActionPreference = "Stop"
$ops   = "F:\backup\_ops"
$stop  = Join-Path $ops "STOP-CORTEX"
$bat   = Join-Path $ops "RUN-CORTEX.bat"
$port  = 8772
$waitS = 300

function Test-CortexUp {
    $c = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    return [bool]$c
}

if (-not (Test-Path $bat)) { Write-Host "ERROR: RUN-CORTEX.bat not found"; exit 1 }

$before = Get-CimInstance Win32_Process -Filter "Name LIKE 'python%'" |
          Where-Object { $_.CommandLine -like "*cortex.py*" } |
          Select-Object -First 1
if ($before) {
    # NOTE: Get-CimInstance returns CreationDate already as [DateTime].
    # ConvertToDateTime() only exists on Get-WmiObject results - calling it here
    # threw MethodNotFound and, with $ErrorActionPreference="Stop", aborted the
    # whole script before it did anything.
    Write-Host ("BEFORE : cortex pid={0} started {1}" -f $before.ProcessId,
                $before.CreationDate.ToString("HH:mm:ss"))
} else {
    Write-Host "BEFORE : no cortex process running"
}

if (-not (Test-Path $stop)) { New-Item -ItemType File -Path $stop | Out-Null }
Write-Host "STOP marker created - waiting for cortex to exit (up to $waitS s)..."

$deadline = (Get-Date).AddSeconds($waitS)
while ((Get-Date) -lt $deadline -and (Test-CortexUp)) { Start-Sleep -Seconds 10 }

if (Test-CortexUp) {
    Remove-Item $stop -Force -ErrorAction SilentlyContinue
    Write-Host "TIMEOUT: port $port still held. STOP marker removed (never leave one behind)."
    Write-Host "         Nothing was restarted. Report this."
    exit 2
}

Remove-Item $stop -Force
Write-Host "Port freed. STOP marker removed. Launching RUN-CORTEX.bat ..."
Start-Process -FilePath $bat -WindowStyle Hidden

$deadline = (Get-Date).AddSeconds(90)
while ((Get-Date) -lt $deadline -and -not (Test-CortexUp)) { Start-Sleep -Seconds 5 }

$after = Get-CimInstance Win32_Process -Filter "Name LIKE 'python%'" |
         Where-Object { $_.CommandLine -like "*cortex.py*" } |
         Select-Object -First 1
if ($after) {
    Write-Host ("AFTER  : cortex pid={0} started {1}" -f $after.ProcessId,
                $after.CreationDate.ToString("HH:mm:ss"))
    if ($before -and $after.ProcessId -eq $before.ProcessId) {
        Write-Host "WARNING: same pid - the old process never exited."
        exit 3
    }
    Write-Host "OK: cortex restarted with fresh code."
    exit 0
}
Write-Host "WARNING: cortex is not listening yet. The 5-min watchdog will revive it."
exit 4
