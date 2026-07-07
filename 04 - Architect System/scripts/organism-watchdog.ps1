# organism-watchdog.ps1 - C2 (verdict 2026-07-07 #1): revive the organism after an UNPLANNED death.
# persistence, not resistance: yields unconditionally to any STOP flag - never fights a kill.
# Start-condition: port 8771 dead AND no STOP flags AND organism ran before (state file exists).
# The FIRST/ceremonial start stays with the owner (double-click RUN-ORGANISM.bat).

$ErrorActionPreference = "Stop"

$VAULT = "F:\backup"
$PORT  = 8771
$LOG   = Join-Path $VAULT "_ops\state\watchdog.log"

function Log([string]$msg) {
    Add-Content -Path $LOG -Value ("{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg) -Encoding utf8
}

# 1) yield to kill-switches (checked FIRST - kill is senior to persistence)
$stops = @(
    (Join-Path $VAULT "STOP"),
    (Join-Path $VAULT "_ops\STOP-ORGANISM")
)
foreach ($s in $stops) {
    if (Test-Path $s) { exit 0 }   # silent yield - a STOP is an owner decision, not an anomaly
}

# 2) is the organism alive? (exclusive bind on 8771 doubles as its liveness lock)
$alive = $false
try {
    $c = New-Object Net.Sockets.TcpClient
    $ok = $c.BeginConnect("127.0.0.1", $PORT, $null, $null).AsyncWaitHandle.WaitOne(1500)
    if ($ok -and $c.Connected) { $alive = $true }
    $c.Close()
} catch { $alive = $false }
if ($alive) { exit 0 }

# 3) only REVIVE - never first-birth: require evidence of a prior run
$state = Join-Path $VAULT "_ops\state\ORGANISM-STATE.json"
if (-not (Test-Path $state)) { exit 0 }

# 4) revive, detached and hidden
Start-Process -FilePath (Join-Path $VAULT "_ops\RUN-ORGANISM.bat") -WorkingDirectory (Join-Path $VAULT "_ops") -WindowStyle Hidden
Log "revived organism (port $PORT was dead, no STOP flags)"
exit 0
