# germline-backup.ps1 - OCTOPUS P0.5 daily layer: ROLLING bundle + tested restore-drill.
# Origin: operator P0.5 script (2026-07-07).
#
# CHANGE 2026-07-25 (owner verdict: "backup must be overwritten, not accumulate"):
#   1. Bundle name is now FIXED (vault-latest.bundle) instead of vault-$STAMP.bundle.
#      Disk use is constant (~250MB) instead of growing ~250MB/day.
#   2. State copy is now a FIXED folder (state-latest) mirrored with robocopy /MIR.
#   3. SAFETY REORDER: the restore-drill now runs on the TEMP bundle BEFORE it replaces
#      the live rolling copy. A bundle that fails the drill never overwrites the last
#      known-good one. (With retention=1 this is essential: the old code moved first and
#      drilled second, which would have destroyed the good copy on a bad build.)
#   4. TEMP scratch is removed in finally{} - a crashed run no longer leaves a ~250MB
#      orphan on C:\...\Temp. That leak was the main consumer of system-drive space.
#   5. Legacy timestamped artifacts (vault-2*.bundle, state-2*) are pruned once, here.
#
# fail-closed: a broken chain never goes off-box; the drill must ERROR on suspicious counts.
# Never writes into the live vault - reads only; writes go to OFFBOX + a temp scratch.

$ErrorActionPreference = "Stop"

$VAULT      = "F:\backup"
$OFFBOX     = "E:\germline"
$STATE_DIRS = @("_ops")
$MIN_NOTES  = 300

$STAMP = Get-Date -Format "yyyy-MM-dd_HHmm"

if ($VAULT.Substring(0,2).ToUpper() -eq $OFFBOX.Substring(0,2).ToUpper()) {
    throw "OFFBOX is on the same drive as VAULT - not off-box."
}
New-Item -ItemType Directory -Force -Path $OFFBOX | Out-Null

# rolling targets (fixed names - overwritten every run, never accumulate)
$bundle    = Join-Path $OFFBOX "vault-latest.bundle"
$prevGood  = Join-Path $OFFBOX "vault-latest.bundle.prev"
$stateRoot = Join-Path $OFFBOX "state-latest"

# temp scratch (fixed names so a crashed run cannot leave a uniquely-named orphan)
$tmpBundle = Join-Path $env:TEMP "germline-vault-build.bundle"
$scratch   = Join-Path $env:TEMP "germline_drill_scratch"

function Remove-Scratch {
    foreach ($p in @($tmpBundle, $scratch)) {
        if (Test-Path $p) { Remove-Item $p -Recurse -Force -ErrorAction SilentlyContinue }
    }
}

try {
    # -- 1+2) integrity gates + bundle, under the INC-2 git-write lock --
    . (Join-Path $PSScriptRoot "git-serialize.ps1")
    $gitLock  = Join-Path $VAULT "_ops\backup\gitwrite.lock"
    $gitFlags = Join-Path $VAULT "_ops\backup"
    Remove-Scratch
    $lockHandle = Enter-GitWriteLock -LockPath $gitLock -FlagDir $gitFlags
    try {
        Wait-GitIndexLock -RepoRoot $VAULT -FlagDir $gitFlags
        Write-Host "[1/5] integrity gates (fsck + ledger verify)..."
        # 2026-09-08 (root cause of nightly rc=1 since 09-02): this repo's fsck exits
        # nonzero with dangling-ONLY output (18 unreachable objects; no missing/broken/
        # corrupt anywhere in output). Dangling objects are normal git housekeeping
        # (resets/quarantines), NOT chain damage - the fail-closed contract is about a
        # BROKEN chain. Gate is now corruption-precise: only non-dangling error lines
        # abort. Output goes to a temp file via cmd so PS 5.1 EAP=Stop never chokes on
        # git's stderr. A clean-rc run that still prints hard lines also aborts.
        $fsckLog = Join-Path $env:TEMP "germline-fsck-out.txt"
        cmd /c "git -C `"$VAULT`" fsck --full > `"$fsckLog`" 2>&1"
        $fsckRc = $LASTEXITCODE
        $fsckHard = @()
        if (Test-Path $fsckLog) {
            $fsckHard = @(Get-Content $fsckLog -ErrorAction SilentlyContinue |
                Where-Object { $_ -match '\S' -and $_ -notmatch 'dangling' })
        }
        if ($fsckHard.Count -gt 0) {
            # 2026-09-08 (run 2 finding): agents/organism commit into this repo WITHOUT the
            # gitwrite lock, so fsck can race a concurrent write/repack and report objects
            # that are mid-flight as "missing". Re-verify each missing-object line with
            # cat-file: exists-now = transient race, not damage. Anything still absent -
            # or any other error class - stays fatal (fail-closed contract intact).
            $still = @()
            foreach ($l in $fsckHard) {
                if ($l -match '^missing\s+\S+\s+([0-9a-f]{40,64})') {
                    git -C $VAULT cat-file -e $Matches[1]
                    if ($LASTEXITCODE -eq 0) { continue }
                }
                $still += $l
            }
            if ($still.Count -gt 0) {
                throw ("GIT FSCK FAILED - backup aborted: " + ($still -join " | "))
            }
            Write-Host "    fsck hard lines were transient (objects exist on re-check) - allowed"
        }
        if ($fsckRc -ne 0) {
            Write-Host "    fsck rc=$fsckRc with dangling-only output - allowed (unreachable != broken chain)"
        }
        python "$VAULT\07 - Knowledge\genome-system\ledger\ledger.py" "$VAULT\07 - Knowledge\genome-system\ledger\ledger.jsonl" verify
        if ($LASTEXITCODE -ne 0) { throw "LEDGER VERIFY FAILED - backup aborted" }
        Write-Host "[2/5] bundle (to temp)..."
        git -C $VAULT bundle create $tmpBundle --all
        if ($LASTEXITCODE -ne 0) { throw "BUNDLE FAILED" }
    } finally {
        Exit-GitWriteLock -Handle $lockHandle -LockPath $gitLock
    }

    # -- 3) restore-drill ON THE TEMP BUNDLE, before it is allowed to replace the good copy --
    Write-Host "[3/5] restore-drill (on candidate, pre-promotion)..."
    git clone --quiet $tmpBundle $scratch
    if (-not (Test-Path (Join-Path $scratch ".git"))) { throw "DRILL: clone from bundle failed" }
    git -C $scratch fsck --full
    if ($LASTEXITCODE -ne 0) { throw "DRILL: fsck on restored copy FAILED" }
    $noteCount = (Get-ChildItem $scratch -Recurse -Filter *.md -ErrorAction SilentlyContinue).Count
    Write-Host "    notes restored: $noteCount"
    if ($noteCount -lt $MIN_NOTES) { throw "DRILL: only $noteCount notes (< $MIN_NOTES) - germline NOT proven" }
    python "$scratch\07 - Knowledge\genome-system\ledger\ledger.py" "$scratch\07 - Knowledge\genome-system\ledger\ledger.jsonl" verify
    if ($LASTEXITCODE -ne 0) { throw "DRILL: restored ledger chain FAILED" }
    Remove-Item $scratch -Recurse -Force

    # -- 4) PROMOTE: drill passed, so this candidate may now replace the rolling copy.
    # Keep exactly one generation of overlap (.prev) so promotion is never a moment
    # with zero valid bundles on disk. .prev is deleted right after, so use stays constant.
    Write-Host "[4/5] promote (drill PASS)..."
    if (Test-Path $bundle) { Move-Item -Force $bundle $prevGood }
    Move-Item -Force $tmpBundle $bundle
    if (Test-Path $prevGood) { Remove-Item $prevGood -Force }

    # state mirror: fixed folder, /MIR so deleted source files do not linger in the copy.
    # SECRET-GUARD: whitelist only, never .env.
    foreach ($d in $STATE_DIRS) {
        $src = Join-Path $VAULT $d
        if (Test-Path $src) {
            robocopy $src (Join-Path $stateRoot $d) /MIR /R:2 /W:2 /NFL /NDL /NP /XD __pycache__ | Out-Null
        }
    }
    $stateFiles = @()
    $cdb = Join-Path $VAULT "_launchpad\second-brain-live\control-brain\core.db"
    if (Test-Path $cdb) { $stateFiles += (Get-Item $cdb) }
    $stateFiles += @(Get-ChildItem (Join-Path $VAULT "_launchpad") -Recurse -Filter "events.jsonl" -File -ErrorAction SilentlyContinue)
    $copiedFiles = @()
    foreach ($f in $stateFiles) {
        if ($f.Name -ne "core.db" -and $f.Name -ne "events.jsonl") { throw "SECRET-GUARD: unexpected state file $($f.FullName)" }
        if ($f.FullName -match '\.env|secret|wallet|seed') { throw "SECRET-GUARD: refused $($f.FullName)" }
        $rel = $f.FullName.Substring($VAULT.Length + 1)
        $dst = Join-Path $stateRoot $rel
        New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
        Copy-Item $f.FullName $dst -Force
    }

    # manifest: germline_lag = 0
    @{
        stamp          = $STAMP
        bundle         = $bundle
        bundle_bytes   = (Get-Item $bundle).Length
        notes_verified = $noteCount
        state_files    = $copiedFiles
        ledger_chain   = "OK (source + restored)"
        drill          = "PASS"
        retention      = "rolling-1 (owner verdict 2026-07-25)"
    } | ConvertTo-Json | Set-Content -Encoding utf8 -Path (Join-Path $OFFBOX "last_backup_manifest.json")

    # -- 5) prune legacy timestamped artifacts (one-time migration; no-op afterwards) --
    Write-Host "[5/5] prune legacy timestamped artifacts..."
    $pruned = 0
    foreach ($b in @(Get-ChildItem $OFFBOX -Filter "vault-2*.bundle" -File -ErrorAction SilentlyContinue)) {
        Remove-Item $b.FullName -Force; $pruned++
    }
    foreach ($s in @(Get-ChildItem $OFFBOX -Directory -Filter "state-2*" -ErrorAction SilentlyContinue)) {
        Remove-Item $s.FullName -Recurse -Force; $pruned++
    }
    Write-Host "    pruned: $pruned legacy item(s)"

    Write-Host ""
    Write-Host "[OK] GERMLINE SAFE - rolling bundle + drill green, germline_lag=0 ($STAMP), notes=$noteCount"
}
finally {
    Remove-Scratch
}
