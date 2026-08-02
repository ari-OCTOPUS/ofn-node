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
    [switch]$WhatIf
)

$ErrorActionPreference = "Continue"
$ops     = "F:\backup\_ops"
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

$fail = @()
$targets = $order | Where-Object { $Skip -notcontains $_ }

# ---------------------------------------------------------------- PREFLIGHT --
Write-Host "=== PREFLIGHT ==="
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

# 4. the organism must write a FRESH state file. The snapshot written at shutdown
#    still says stop_organism=true; reading it too early reports a healthy restart
#    from a dead process's last words.
$fresh = $false
for ($i = 0; $i -lt 24; $i++) {
    $ts = Read-StateTs
    if ($ts) {
        try { if ([datetime]$ts -gt $startedAt) { $fresh = $true; break } } catch { }
    }
    Start-Sleep -Seconds 5
}
if (-not $fresh) {
    Write-Host "  FAIL organism has not written a fresh state file (waited 120s)"
    $fail += "organism : no fresh state"
} else {
    $j = Get-Content $stateF -Raw | ConvertFrom-Json
    $beatAfter = $j.beat
    Write-Host ("  OK   fresh state at {0}" -f $j.ts)
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
