# germline-hourly.ps1 - OCTOPUS P0.5 hourly layer: light incremental push + rolling state copy.
# NOT a full bundle (a 197MB bundle hourly would fill the disk - operator verdict 2026-07-07).
# Fail-visible: any failure is appended to E:\germline\hourly.log and exits non-zero.

$ErrorActionPreference = "Stop"

$VAULT  = "F:\backup"
$OFFBOX = "E:\germline"
$BARE   = Join-Path $OFFBOX "vault.git"
$LOG    = Join-Path $OFFBOX "hourly.log"

function Log([string]$msg) {
    Add-Content -Path $LOG -Value ("{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg) -Encoding utf8
}

try {
    New-Item -ItemType Directory -Force -Path $OFFBOX | Out-Null
    if (-not (Test-Path (Join-Path $BARE "HEAD"))) {
        git init --bare $BARE | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "bare init failed" }
        Log "bare repo initialized at $BARE"
    }

    # PRIMARY: incremental push (light - operator verdict). Known issue INC-2: git.exe cannot
    # write to E: under the task token (receive-pack Permission denied) while PowerShell can.
    # So on push failure -> FALLBACK: git writes a full bundle to LOCAL temp, PowerShell moves
    # it to E: as a single ROLLING file (constant disk use - never accumulates).
    # INC-2 fix (2026-07-08): route all F:\backup\.git access through the shared git-write lock
    # so it defers while a commit holds .git\index.lock and never overlaps the daily bundle.
    # Fail-loud: lock/index-lock timeout throws -> caught below -> logged, exit 1.
    . (Join-Path $PSScriptRoot "git-serialize.ps1")
    $gitLock  = Join-Path $VAULT "_ops\backup\gitwrite.lock"
    $gitFlags = Join-Path $VAULT "_ops\backup"
    $lockHandle = Enter-GitWriteLock -LockPath $gitLock -FlagDir $gitFlags
    try {
        Wait-GitIndexLock -RepoRoot $VAULT -FlagDir $gitFlags
        $ErrorActionPreference = "Continue"
        $out1 = & git -C $VAULT push --quiet $BARE --all 2>&1; $c1 = $LASTEXITCODE
        $out2 = & git -C $VAULT push --quiet $BARE --tags 2>&1; $c2 = $LASTEXITCODE
        $ErrorActionPreference = "Stop"
        if ($c1 -eq 0 -and $c2 -eq 0) {
            $mode = "push"
        } else {
            $tmpB = Join-Path $env:TEMP "germline-hourly.bundle"
            git -C $VAULT bundle create $tmpB --all
            if ($LASTEXITCODE -ne 0) { throw ("push failed AND bundle fallback failed. push: " + (@($out1 + $out2 | ForEach-Object { "$_" }) -join " | ")) }
            Move-Item -Force $tmpB (Join-Path $OFFBOX "hourly-latest.bundle")
            $mode = "bundle-fallback (push err: " + (@($out1 | Select-Object -First 1 | ForEach-Object { "$_" }) -join "") + ")"
        }
    } finally {
        Exit-GitWriteLock -Handle $lockHandle -LockPath $gitLock
    }

    # rolling state copy (single folder, overwritten hourly). SECRET-GUARD: whitelist only.
    $stateRoot = Join-Path $OFFBOX "state-hourly"
    robocopy (Join-Path $VAULT "_ops") (Join-Path $stateRoot "_ops") /E /R:2 /W:2 /NFL /NDL /NP /XD __pycache__ | Out-Null
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
