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

# 1b) D-G HALT-ALL (2026-07-21): a GLOBAL panic marker is senior to persistence too. The _ops
# watchdogs (cortex-watchdog / live-watchdog) already refuse to revive under HALT-ALL; this TWIN
# supervises BOTH organism (8771) and cortex (8772) below, so it must match - a global halt must
# never be silently out-lived. ADD-only: the STOP + STOP-ORGANISM yields above are untouched.
if (Test-Path (Join-Path $VAULT "_ops\HALT-ALL")) { exit 0 }   # silent yield to global HALT-ALL

# helper: TCP liveness probe (exclusive bind doubles as the liveness lock)
function Test-PortAlive([int]$p) {
    try {
        $c = New-Object Net.Sockets.TcpClient
        $ok = $c.BeginConnect("127.0.0.1", $p, $null, $null).AsyncWaitHandle.WaitOne(1500)
        $alive = ($ok -and $c.Connected)
        $c.Close()
        return $alive
    } catch { return $false }
}

# 2) ORGANISM (8771): only REVIVE - never first-birth (prior-run evidence required)
if (-not (Test-PortAlive $PORT)) {
    $state = Join-Path $VAULT "_ops\state\ORGANISM-STATE.json"
    if (Test-Path $state) {
        Start-Process -FilePath (Join-Path $VAULT "_ops\RUN-ORGANISM.bat") -WorkingDirectory (Join-Path $VAULT "_ops") -WindowStyle Hidden
        Log "revived organism (port $PORT was dead, no STOP flags)"
    }
}

# 3) CORTEX (8772) - Program 5, 2026-07-16 (supervision-gap fix: cortex died 07-10 unplanned
# and nothing watched it while the organism got revived 5x). Mirrored revive with BACKOFF+CAP
# (M3 lesson: never crash-loop a brain): max 3 revivals per 6h window, tracked in a state file.
# Same seniority: STOP flags already exited above. First/ceremonial start stays with the owner
# (RUN-CORTEX.bat is idempotent + double port-guarded).
$CPORT = 8772
if (-not (Test-PortAlive $CPORT)) {
    $cstate = Join-Path $VAULT "_ops\state\cortex\cortex-state.json"
    $cbat   = Join-Path $VAULT "_ops\RUN-CORTEX.bat"
    if ((Test-Path $cstate) -and (Test-Path $cbat)) {
        $track = Join-Path $VAULT "_ops\state\cortex-watchdog.json"
        $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        $attempts = @()
        if (Test-Path $track) {
            try {
                $j = Get-Content $track -Raw -Encoding utf8 | ConvertFrom-Json
                foreach ($t in $j.attempts) { if (($now - [long]$t) -lt 21600) { $attempts += [long]$t } }
            } catch {}
        }
        if ($attempts.Count -lt 3) {
            $attempts += $now
            try {
                @{ attempts = $attempts } | ConvertTo-Json -Compress | Out-File -FilePath $track -Encoding utf8
            } catch {}
            Start-Process -FilePath $cbat -WorkingDirectory (Join-Path $VAULT "_ops") -WindowStyle Hidden
            Log "revived cortex (port $CPORT was dead; attempt $($attempts.Count)/3 in 6h window)"
        } else {
            Log "cortex dead but revival CAP reached (3/6h) - yielding to owner (crash-loop guard)"
        }
    }
}
exit 0
