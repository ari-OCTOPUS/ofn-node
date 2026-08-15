# RESTART-ALL.ps1 - restart the whole organism, once, and PROVE it happened.
#
#   .\RESTART-ALL.ps1                 # restart every limb, then verify
#   .\RESTART-ALL.ps1 -Skip live      # same, minus one limb
#   .\RESTART-ALL.ps1 -WhatIf         # preflight + plan only, change nothing
#
# Why this exists (2026-08-03):
#   Restarting used to mean running RESTART-PROCESS.ps1 three or four times and
#   hand-launching the gateway, which has no .bat. Doing it by hand is how a stale
#   gateway kept serving pre-merge code for hours after "the restart". This script
#   is the one button: it delegates every limb to RESTART-PROCESS.ps1 (so the
#   PID-comparison and supervisor-loop logic lives in exactly one place) and then
#   runs an acceptance gate. A restart that is not verified is not a restart.
#
# Order is deliberate: organism LAST. Its stop marker is STOP-ORGANISM, the global
# kill switch, so the other limbs briefly see it; doing it last means they are
# already fresh and simply resume.
#
# Output is ASCII-only on purpose: Persian text pasted back into a console gets
# re-executed as commands.

[CmdletBinding()]
param(
    [string[]]$Skip = @(),
    [switch]$WhatIf,

    # Test seam (2026-08-03). The preflight guards below are pure functions of a
    # directory, but with the path hardcoded the ONLY way to answer "does it really
    # abort on a stray marker?" was to drop a real STOP-* file into the live tree -
    # the exact act that once kept the whole system down for 30 minutes, and which
    # the permission layer rightly refuses. An untestable guard is a guard nobody
    # can prove, so the root is injectable.
    #
    # Injecting it is safe by CONSTRUCTION, not by good manners: a non-canonical
    # root is preflight-only (enforced immediately below), so a test can never
    # reach the restart loop no matter what it passes.
    [string]$OpsRoot = "F:\backup\_ops"
)

$ErrorActionPreference = "Continue"
$CanonicalOps = "F:\backup\_ops"
$ops     = $OpsRoot
$runner  = Join-Path $ops "RESTART-PROCESS.ps1"
$stateF  = Join-Path $ops "state\ORGANISM-STATE.json"
$flagsF  = Join-Path $ops "OCTOPUS-flags.cmd"
$markers = @("STOP-ORGANISM", "RESTART-REQUESTED", "STOP-TG-CENTER", "STOP-CORTEX")

# cortex/center/gateway/live first, organism last - see header.
$order   = @("cortex", "center", "gateway", "live", "organism")
$match   = @{ cortex = "cortex.py"; center = "center.py"; gateway = "miniapp_gateway.py"
              live = "live\server.py"; organism = "organism.py" }

function Get-Proc([string]$m) {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
        Where-Object { $_.CommandLine -like "*$m*" } | Select-Object -First 1
}
function Read-Beat {
    try { (Get-Content $stateF -Raw | ConvertFrom-Json).beat } catch { $null }
}
function Read-StateTs {
    try { (Get-Content $stateF -Raw | ConvertFrom-Json).ts } catch { $null }
}
function Read-StateStarted {
    # `started` = boot time of the process that wrote this state (organism.py START_TS).
    # The shutdown snapshot of the OLD process keeps its own `started` — only the new
    # process writes its boot time here. This is the reliable freshness signal: `ts`
    # alone can be newer than $startedAt yet still carry stop_organism=true from the
    # dying process's last write (2026-08-03 false-negative: the gate read that
    # transient state and FAILED a healthy restart).
    try { (Get-Content $stateF -Raw | ConvertFrom-Json).started } catch { $null }
}

$fail = @()
$targets = $order | Where-Object { $Skip -notcontains $_ }

# ---------------------------------------------------------------- PREFLIGHT --
Write-Host "=== PREFLIGHT ==="

# Enforcement of the -OpsRoot seam, FIRST, before any other check: an injected root
# must be unable to reach a Stop-Process no matter what else is passed. Exit code 2
# is reserved for "the seam was misused" so a test can tell it apart from exit 1,
# which means "preflight ran and found a real problem".
$normSelf  = $ops.TrimEnd('\','/').ToLowerInvariant()
$normCanon = $CanonicalOps.TrimEnd('\','/').ToLowerInvariant()
$isCanonical = ($normSelf -eq $normCanon)
if (-not $isCanonical) {
    Write-Host ("  ops root     : {0}" -f $ops)
    Write-Host "  mode         : NON-CANONICAL ROOT - preflight only, restart loop unreachable"
    if (-not $WhatIf) {
        Write-Host "ABORT: -OpsRoot other than the canonical tree is preflight-only. Re-run with -WhatIf."
        exit 2
    }
}
if (-not (Test-Path $runner)) { Write-Host "ABORT: RESTART-PROCESS.ps1 not found."; exit 1 }

# A stray marker means something already went wrong; restarting on top of it hides
# the cause and can leave a limb asleep forever.
$stray = @()
foreach ($m in $markers) { if (Test-Path (Join-Path $ops $m)) { $stray += $m } }
if ($stray.Count -gt 0) {
    Write-Host ("ABORT: stray marker(s) present: " + ($stray -join ", "))
    Write-Host "       Someone or something halted a limb. Investigate before restarting."
    exit 1
}
Write-Host "  markers      : none (clean)"

# The flags file is read by cmd.exe. If it is LF, cmd mis-parses it and processes
# boot with a fraction of their flags - that incident cost 59 of 156 flags once.
if (-not (Test-Path $flagsF)) {
    Write-Host "ABORT: OCTOPUS-flags.cmd missing - processes would boot flagless."; exit 1
}
$bytes = [IO.File]::ReadAllBytes($flagsF)
$crlf  = 0; for ($i = 0; $i -lt $bytes.Length - 1; $i++) { if ($bytes[$i] -eq 13 -and $bytes[$i+1] -eq 10) { $crlf++ } }
if ($crlf -lt 10) {
    Write-Host "ABORT: OCTOPUS-flags.cmd has no CRLF line endings - cmd.exe will mis-parse it."
    exit 1
}
Write-Host ("  flags file   : {0} bytes, {1} CRLF lines - OK" -f $bytes.Length, $crlf)

$beatBefore = Read-Beat
$pidBefore  = @{}
foreach ($t in $targets) {
    $p = Get-Proc $match[$t]
    $pidBefore[$t] = if ($p) { $p.ProcessId } else { $null }
    $age = if ($p) { $p.CreationDate.ToString("HH:mm:ss") } else { "not running" }
    Write-Host ("  {0,-9}    : pid={1,-7} started {2}" -f $t, $pidBefore[$t], $age)
}
Write-Host ("  beat         : {0}" -f $beatBefore)
$startedAt = Get-Date

if ($WhatIf) {
    Write-Host ""
    Write-Host ("PLAN: would restart, in order: " + ($targets -join " -> "))
    Write-Host "WhatIf - nothing changed."
    exit 0
}

# ------------------------------------------------------------------ RESTART --
foreach ($t in $targets) {
    Write-Host ""
    Write-Host ("=== RESTART $t ===")
    & $runner $t
    if ($LASTEXITCODE -ne 0) {
        Write-Host ("  runner exit code {0} for '{1}'" -f $LASTEXITCODE, $t)
        $fail += ("$t : runner exit $LASTEXITCODE")
    }
}

# --------------------------------------------------------------- ACCEPTANCE --
Write-Host ""
Write-Host "=== ACCEPTANCE GATE ==="

# 1. every limb must have a NEW pid. Same pid means it never restarted, which is the
#    exact failure this whole family of scripts exists to make visible.
foreach ($t in $targets) {
    $p = Get-Proc $match[$t]
    if (-not $p) {
        Write-Host ("  FAIL {0,-9} not running" -f $t); $fail += "$t : not running"
    } elseif ($pidBefore[$t] -and $p.ProcessId -eq $pidBefore[$t]) {
        Write-Host ("  FAIL {0,-9} same pid {1} - never restarted" -f $t, $p.ProcessId)
        $fail += "$t : same pid"
    } else {
        Write-Host ("  OK   {0,-9} pid {1} -> {2}" -f $t, $pidBefore[$t], $p.ProcessId)
    }
}

# 2. no marker may survive. A stray STOP-ORGANISM keeps the whole system down.
foreach ($m in $markers) {
    if (Test-Path (Join-Path $ops $m)) {
        Write-Host ("  FAIL marker left behind: " + $m); $fail += "marker $m"
    }
}
if (-not ($fail -match "^marker")) { Write-Host "  OK   no markers left behind" }

# 3. flags must have loaded, and loaded EQUALLY. Unequal counts across processes is
#    flag drift: one limb running yesterday's decisions.
$counts = @{}
foreach ($n in @("organism", "center", "cortex", "live")) {
    $fp = Join-Path $ops ("state\flags-loaded-$n.json")
    if (-not (Test-Path $fp)) { continue }
    try {
        $j = Get-Content $fp -Raw | ConvertFrom-Json
        $c = ($j.flags | Get-Member -MemberType NoteProperty).Count
        $counts[$n] = $c
        $miss = $j.load_shortfall.missing_count
        if ($miss -ne 0) { Write-Host ("  FAIL {0} missing {1} flags" -f $n, $miss); $fail += "$n : missing flags" }
    } catch { }
}
if ($counts.Count -gt 0) {
    $restarted = $counts.Keys | Where-Object { $targets -contains $_ }
    $distinct = @($restarted | ForEach-Object { $counts[$_] } | Sort-Object -Unique)
    $summary = ($counts.Keys | Sort-Object | ForEach-Object { "$_=$($counts[$_])" }) -join " "
    if ($distinct.Count -gt 1) {
        Write-Host ("  WARN flag drift across restarted limbs: " + $summary)
    } else {
        Write-Host ("  OK   flags loaded equally: " + $summary)
    }
}

# 4. the organism must write a FRESH state file. Two independent signals must both
#    hold, because each alone has produced a false result:
#      (a) `started` >= $startedAt — the state was written by the NEW process, not
#          the dying one. The shutdown snapshot keeps the OLD process's `started`
#          (organism.py:66 START_TS), so a state from the dying process fails this.
#      (b) `ts` > $startedAt — the state was written after this restart began.
#    The 2026-08-03 false-negative checked only `ts`, read the transient shutdown
#    snapshot (stop_organism=true, old `started`), and FAILED a healthy restart.
# 2026-08-15 (test-sweep T5): پنجرهٔ 120s→300s — بوتِ ارگانیسم ~۳ دقیقه طول می‌کشد
# و گیتِ خودکار گاهی پیش از نوشته‌شدنِ state تازه می‌بست (رضایتِ دستی می‌خواست).
# ۶۰ تلاش × ۵ ثانیه = ۳۰۰s.
$fresh = $false
for ($i = 0; $i -lt 60; $i++) {
    $ts = Read-StateTs
    $startedField = Read-StateStarted
    if ($ts -and $startedField) {
        try {
            $tsNewer    = [datetime]$ts        -gt $startedAt
            $bootNewer  = [datetime]$startedField -ge $startedAt
            if ($tsNewer -and $bootNewer) { $fresh = $true; break }
        } catch { }
    }
    Start-Sleep -Seconds 5
}
if (-not $fresh) {
    Write-Host "  FAIL organism has not written a fresh state file (waited 300s)"
    $fail += "organism : no fresh state"
} else {
    $j = Get-Content $stateF -Raw | ConvertFrom-Json
    $beatAfter = $j.beat
    Write-Host ("  OK   fresh state (boot={0}) at {1}" -f $j.started, $j.ts)
    if ($j.halted)        { Write-Host ("  FAIL halted = " + $j.halted);        $fail += "organism : halted" }
    if ($j.stop_organism) { Write-Host ("  FAIL stop_organism = true");         $fail += "organism : stop flag" }
    if ($j.frozen)        { Write-Host ("  FAIL frozen = true");                $fail += "organism : frozen" }
    if ($beatBefore -and $beatAfter -le $beatBefore) {
        Write-Host ("  WARN beat has not advanced yet: {0} -> {1}" -f $beatBefore, $beatAfter)
    } else {
        Write-Host ("  OK   beat {0} -> {1}" -f $beatBefore, $beatAfter)
    }
}

Write-Host ""
if ($fail.Count -gt 0) {
    Write-Host ("RESULT: FAILED - " + ($fail -join " | "))
    exit 1
}
Write-Host "RESULT: OK - every limb restarted, verified, and beating."
exit 0
