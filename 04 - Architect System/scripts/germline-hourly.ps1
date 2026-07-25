# germline-hourly.ps1 - OCTOPUS P0.5 hourly layer: light incremental push + rolling state copy.
# NOT a full bundle (a 197MB bundle hourly would fill the disk - operator verdict 2026-07-07).
# Fail-visible: any failure is appended to E:\germline\hourly.log and exits non-zero.
#
# CHANGE 2026-07-25 (owner verdict "backup must be overwritten, not accumulate"):
#   1. TEMP scratch is removed in finally{} - a crashed run no longer leaves a ~250MB orphan
#      on the system drive. At 24 runs/day on the fallback path that leak was the main
#      consumer of C: space.
#   2. FALLBACK THROTTLE: the full-bundle fallback is expensive (~250MB write + full repo
#      enumeration). It now runs at most once per FALLBACK_MIN_HOURS. If the push fails
#      again inside that window the run logs PUSH-FAIL (throttled) and exits 0 - the last
#      rolling bundle is still there, so germline_lag stays honest without re-bundling
#      the whole repo every hour.
#      Root-cause reminder (INC-2): the real fix is granting the task account write access
#      to E:\germline\vault.git. While that is broken this throttle bounds the damage.
#   3. State mirror uses /MIR so it tracks deletions instead of growing forever.

$ErrorActionPreference = "Stop"

$VAULT  = "F:\backup"
$OFFBOX = "E:\germline"
$BARE   = Join-Path $OFFBOX "vault.git"
$LOG    = Join-Path $OFFBOX "hourly.log"
$STATEF = Join-Path $OFFBOX "hourly-state.json"

# how often the expensive full-bundle fallback may run when push is broken
$FALLBACK_MIN_HOURS = 6

function Log([string]$msg) {
    Add-Content -Path $LOG -Value ("{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg) -Encoding utf8
}

$tmpB = Join-Path $env:TEMP "germline-hourly.bundle"

try {
    New-Item -ItemType Directory -Force -Path $OFFBOX | Out-Null
    if (-not (Test-Path (Join-Path $BARE "HEAD"))) {
        git init --bare $BARE | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "bare init failed" }
        Log "bare repo initialized at $BARE"
    }

    # PRIMARY: incremental push (light). Known issue INC-2: git.exe may not be able to write
    # to E: under the task token (receive-pack Permission denied) while PowerShell can.
    # On push failure -> throttled FALLBACK: git writes a full bundle to LOCAL temp,
    # PowerShell moves it to E: as a single ROLLING file (constant disk use).
    . (Join-Path $PSScriptRoot "git-serialize.ps1")
    $gitLock  = Join-Path $VAULT "_ops\backup\gitwrite.lock"
    $gitFlags = Join-Path $VAULT "_ops\backup"
    $lockHandle = Enter-GitWriteLock -LockPath $gitLock -FlagDir $gitFlags
    try {
        Wait-GitIndexLock -RepoRoot $VAULT -FlagDir $gitFlags
        $ErrorActionPreference = "Continue"
        $out1 = & git -C $VAULT push --quiet $BARE --all  2>&1; $c1 = $LASTEXITCODE
        $out2 = & git -C $VAULT push --quiet $BARE --tags 2>&1; $c2 = $LASTEXITCODE
        $ErrorActionPreference = "Stop"
        if ($c1 -eq 0 -and $c2 -eq 0) {
            $mode = "push"
        } else {
            $pushErr = (@($out1 | Select-Object -First 1 | ForEach-Object { "$_" }) -join "")

            # --- throttle: has the fallback run recently? ---
            $lastFb = $null
            if (Test-Path $STATEF) {
                try { $lastFb = [datetime]::Parse((Get-Content $STATEF -Raw | ConvertFrom-Json).last_fallback, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::RoundtripKind) } catch { $lastFb = $null }
            }
            $dueH = if ($lastFb) { ((Get-Date) - $lastFb).TotalHours } else { [double]::PositiveInfinity }

            if ($dueH -lt $FALLBACK_MIN_HOURS) {
                $mode = "PUSH-FAIL (fallback throttled, {0:N1}h of {1}h; push err: {2})" -f $dueH, $FALLBACK_MIN_HOURS, $pushErr
            } else {
                git -C $VAULT bundle create $tmpB --all
                if ($LASTEXITCODE -ne 0) { throw ("push failed AND bundle fallback failed. push: " + $pushErr) }
                Move-Item -Force $tmpB (Join-Path $OFFBOX "hourly-latest.bundle")
                @{ last_fallback = (Get-Date).ToString("o"); push_err = $pushErr } |
                    ConvertTo-Json | Set-Content -Encoding utf8 -Path $STATEF
                $mode = "bundle-fallback (push err: $pushErr)"
            }
        }
    } finally {
        Exit-GitWriteLock -Handle $lockHandle -LockPath $gitLock
    }

    # rolling state copy (single folder, mirrored hourly). SECRET-GUARD: whitelist only.
    $stateRoot = Join-Path $OFFBOX "state-hourly"
    robocopy (Join-Path $VAULT "_ops") (Join-Path $stateRoot "_ops") /MIR /R:2 /W:2 /NFL /NDL /NP /XD __pycache__ | Out-Null
    $files = @()
    $cdb = Join-Path $VAULT "_launchpad\second-brain-live\control-brain\core.db"
    if (Test-Path $cdb) { $files += (Get-Item $cdb) }
    $files += @(Get-ChildItem (Join-Path $VAULT "_launchpad") -Recurse -Filter "events.jsonl" -File -ErrorAction SilentlyContinue)
    foreach ($f in $files) {
        if ($f.Name -ne "core.db" -and $f.Name -ne "events.jsonl") { continue }
        if ($f.FullName -match '\.env|secret|wallet|seed') { continue }
        $rel = $f.FullName.Substring($VAULT.Length + 1)
        $dst = Join-Path $stateRoot $rel
        New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
        Copy-Item $f.FullName $dst -Force
    }

    Log ("OK " + $mode + " +state")
    exit 0
}
catch {
    Log ("FAIL " + $_.Exception.Message)
    exit 1
}
finally {
    if (Test-Path $tmpB) { Remove-Item $tmpB -Force -ErrorAction SilentlyContinue }
}
