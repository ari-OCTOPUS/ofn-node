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
    (Join-Path $VAULT "04 - Architect System\STOP"),
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
#    Heart v2 (2026-08-25, owner order "bring it all to the real world"): the revive
#    decision now defers to the CANONICAL Python verdict (_ops/watchdog.py --json),
#    which also detects silent in-process stalls (stale ts / frozen beat counter).
#    This closes the documented split-brain (watchdog.py header note): stall detection
#    now actually runs in production. STOP supremacy above is unchanged and still wins.
$canon = Join-Path $VAULT "_ops\watchdog.py"
$verdict = $null
if (Test-Path $canon) {
    try {
        $raw = & python -X utf8 $canon --json 2>$null
        if ($LASTEXITCODE -eq 0 -and $raw) { $verdict = ($raw | Out-String | ConvertFrom-Json) }
    } catch {}
}
if ($verdict -and $verdict.should_revive) {
    $state = Join-Path $VAULT "_ops\state\ORGANISM-STATE.json"
    if (Test-Path $state) {
        Start-Process -FilePath (Join-Path $VAULT "_ops\RUN-ORGANISM.bat") -WorkingDirectory (Join-Path $VAULT "_ops") -WindowStyle Hidden
        Log "revived organism (canonical verdict: $($verdict.reason))"
    }
} elseif ($verdict -and $verdict.stall) {
    # ── SEMANTIC-LIVENESS RECOVERY (2026-09-07, owner GO + advisor rec#1) ──────────
    # Stall = port open AND (ts stale OR beat frozen) — the "silent failure" class
    # (FailureAtlas Loud/Silent): port probes can never see it. Two wedges measured
    # 2026-09-07 (15:1x and 16:23, beats frozen with live port) survived exactly
    # because this branch only alerted. Now, in order:
    #   1) capture the STACK of the wedged holder FIRST (evidence before action) —
    #      py-spy dump, saved under _ops/state/stall-stacks/;
    #   2) only if the owner armed stall-revive (marker file WATCHDOG-STALL-REVIVE,
    #      the only arming path that reaches a Scheduled Task — see watchdog.py
    #      "arming that is actually provable"): kill the wedged port-holder and
    #      relaunch, under a 3-per-6h cap (crash-loop guard, cortex-twin pattern);
    #   3) disarmed -> previous behavior (log + alert), zero kills.
    # STOP/HALT-ALL seniority already exited above and always wins.
    $why = "$($verdict.reason)"
    $holderPid = $null
    try {
        $line = (netstat -ano | Select-String "127.0.0.1:8771\s.*LISTENING" | Select-Object -First 1).Line
        if ($line) { $holderPid = [int]($line.Trim() -split "\s+")[-1] }
    } catch {}
    $stackPath = $null
    if ($holderPid) {
        $stackDir = Join-Path $VAULT "_ops\state\stall-stacks"
        if (-not (Test-Path $stackDir)) { New-Item -ItemType Directory -Path $stackDir | Out-Null }
        $stackPath = Join-Path $stackDir ("{0}-pid{1}.txt" -f (Get-Date -Format "yyyyMMdd-HHmmss"), $holderPid)
        try {
            & "C:\Users\Armin\AppData\Roaming\Python\Python313\Scripts\py-spy.exe" dump --pid $holderPid 2>$null | Out-File -FilePath $stackPath -Encoding utf8
        } catch {}
    }
    $armed = Test-Path (Join-Path $VAULT "_ops\WATCHDOG-STALL-REVIVE")
    if ($armed) {
        $track = Join-Path $VAULT "_ops\state\stall-revive-attempts.json"
        $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        $attempts = @()
        if (Test-Path $track) {
            try {
                $j = Get-Content $track -Raw -Encoding utf8 | ConvertFrom-Json
                foreach ($t in $j.attempts) { if (($now - [long]$t) -lt 21600) { $attempts += [long]$t } }
            } catch {}
        }
        if ($attempts.Count -lt 3 -and $holderPid) {
            $attempts += $now
            try { @{ attempts = $attempts } | ConvertTo-Json -Compress | Out-File -FilePath $track -Encoding utf8 } catch {}
            try { Stop-Process -Id $holderPid -Force } catch {}
            Log ("STALL recovery: killed wedged holder pid=$holderPid (stack: $stackPath; $why; attempt $($attempts.Count)/3 in 6h)")
            Start-Sleep -Seconds 3
            Start-Process -FilePath (Join-Path $VAULT "_ops\RUN-ORGANISM.bat") -WorkingDirectory (Join-Path $VAULT "_ops") -WindowStyle Hidden
            Log "STALL recovery: relaunched RUN-ORGANISM.bat"
            try {
                & python -X utf8 $canon --alert "WATCHDOG STALL incident (organism :8771) - stack captured, wedged holder killed and relaunched (armed recovery, capped 3/6h)" | Out-Null
            } catch {}
        } elseif (-not $holderPid) {
            Log "STALL but no holder pid resolved - no kill, alerting ($why)"
            try { & python -X utf8 $canon --alert "WATCHDOG STALL incident (organism :8771) - port open, in-process loop dead, holder pid unresolvable" | Out-Null } catch {}
        } else {
            Log "STALL recovery CAP reached (3/6h) - yielding to owner ($why)"
            try { & python -X utf8 $canon --alert "WATCHDOG STALL incident (organism :8771) - recovery cap reached 3 per 6h - owner decision required" | Out-Null } catch {}
        }
    } else {
        Log "STALL detected (disarmed - no kill): $why (stack: $stackPath)"
        try {
            & python -X utf8 $canon --alert "WATCHDOG STALL incident (organism :8771) - port open but in-process loop dead - owner decision required" | Out-Null
        } catch {}
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
