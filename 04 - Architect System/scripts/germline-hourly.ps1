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

    # incremental push of all branches + tags (object transfer is integrity-checked by git)
    git -C $VAULT push --quiet $BARE --all
    if ($LASTEXITCODE -ne 0) { throw "push --all failed (exit $LASTEXITCODE)" }
    git -C $VAULT push --quiet $BARE --tags
    if ($LASTEXITCODE -ne 0) { throw "push --tags failed (exit $LASTEXITCODE)" }

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

    Log "OK push+state"
    exit 0
}
catch {
    Log ("FAIL " + $_.Exception.Message)
    exit 1
}
