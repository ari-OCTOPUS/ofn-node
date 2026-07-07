# germline-backup.ps1 - OCTOPUS P0.5 daily layer: full bundle + tested restore-drill + retention prune.
# fail-closed: a broken chain never goes off-box; the drill must ERROR on suspicious note counts.
# Never writes into the live vault - reads only; writes go to OFFBOX + a temp scratch.
# Origin: operator P0.5 script (2026-07-07) + unified-order step 2 (STATE_FILES: core.db,
# events.jsonl - NEVER .env / secrets) + step 3 (retention: 7 daily / 4 weekly).

$ErrorActionPreference = "Stop"

$VAULT      = "F:\backup"
$OFFBOX     = "E:\germline"
$STATE_DIRS = @("_ops")
$MIN_NOTES  = 300
$KEEP_DAILY = 7
$KEEP_WEEKS = 4

$STAMP = Get-Date -Format "yyyy-MM-dd_HHmm"

if ($VAULT.Substring(0,2).ToUpper() -eq $OFFBOX.Substring(0,2).ToUpper()) {
    throw "OFFBOX is on the same drive as VAULT - not off-box."
}
New-Item -ItemType Directory -Force -Path $OFFBOX | Out-Null

# -- 1) integrity gates (fail-closed) --
Write-Host "[1/5] integrity gates (fsck + ledger verify)..."
git -C $VAULT fsck --full
if ($LASTEXITCODE -ne 0) { throw "GIT FSCK FAILED - backup aborted" }
python "$VAULT\07 - Knowledge\genome-system\ledger\ledger.py" "$VAULT\07 - Knowledge\genome-system\ledger\ledger.jsonl" verify
if ($LASTEXITCODE -ne 0) { throw "LEDGER VERIFY FAILED - backup aborted" }

# -- 2) snapshot: bundle + state (dirs + explicit ground-truth files) --
# INC-2 lesson: git.exe cannot write to E: under the task token -> git writes to LOCAL temp,
# PowerShell (which CAN write to E:) moves the finished bundle into OFFBOX.
Write-Host "[2/5] bundle + state copy..."
$bundle = Join-Path $OFFBOX "vault-$STAMP.bundle"
$tmpBundle = Join-Path $env:TEMP "vault-$STAMP.bundle"
git -C $VAULT bundle create $tmpBundle --all
if ($LASTEXITCODE -ne 0) { throw "BUNDLE FAILED" }
Move-Item -Force $tmpBundle $bundle

$stateRoot = Join-Path $OFFBOX "state-$STAMP"
foreach ($d in $STATE_DIRS) {
    $src = Join-Path $VAULT $d
    if (Test-Path $src) {
        robocopy $src (Join-Path $stateRoot $d) /E /R:2 /W:2 /NFL /NDL /NP /XD __pycache__ | Out-Null
    }
}
# explicit state FILES (untracked ground-truth). SECRET-GUARD: whitelisted names only, never .env.
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
    Copy-Item $f.FullName $dst
    $copiedFiles += $rel
}

# -- 3) restore-drill: restore into scratch and verify (never the live vault) --
Write-Host "[3/5] restore-drill..."
$scratch = Join-Path $env:TEMP "germline_drill_$STAMP"
git clone --quiet $bundle $scratch
if (-not (Test-Path (Join-Path $scratch ".git"))) { throw "DRILL: clone from bundle failed" }
git -C $scratch fsck --full
if ($LASTEXITCODE -ne 0) { throw "DRILL: fsck on restored copy FAILED" }
$noteCount = (Get-ChildItem $scratch -Recurse -Filter *.md -ErrorAction SilentlyContinue).Count
Write-Host "    notes restored: $noteCount"
if ($noteCount -lt $MIN_NOTES) { throw "DRILL: only $noteCount notes (< $MIN_NOTES) - germline NOT proven" }
python "$scratch\07 - Knowledge\genome-system\ledger\ledger.py" "$scratch\07 - Knowledge\genome-system\ledger\ledger.jsonl" verify
if ($LASTEXITCODE -ne 0) { throw "DRILL: restored ledger chain FAILED" }
Remove-Item $scratch -Recurse -Force

# -- 4) manifest: germline_lag = 0 --
Write-Host "[4/5] manifest..."
@{
    stamp          = $STAMP
    bundle         = $bundle
    bundle_bytes   = (Get-Item $bundle).Length
    notes_verified = $noteCount
    state_files    = $copiedFiles
    ledger_chain   = "OK (source + restored)"
    drill          = "PASS"
} | ConvertTo-Json | Set-Content -Encoding utf8 -Path (Join-Path $OFFBOX "last_backup_manifest.json")

# -- 5) retention prune (operator verdict: keep 7 daily + newest-of-week for 4 weeks) --
Write-Host "[5/5] retention prune..."
$cal = [System.Globalization.CultureInfo]::InvariantCulture.Calendar
$bundles = @(Get-ChildItem $OFFBOX -Filter "vault-*.bundle" -File | Sort-Object LastWriteTime -Descending)
$keep = @($bundles | Select-Object -First $KEEP_DAILY | ForEach-Object Name)
$weekGroups = $bundles | Group-Object {
    "{0}-W{1:d2}" -f $_.LastWriteTime.Year, $cal.GetWeekOfYear($_.LastWriteTime, "FirstFourDayWeek", "Monday")
} | Sort-Object Name -Descending | Select-Object -First $KEEP_WEEKS
foreach ($g in $weekGroups) {
    $keep += ($g.Group | Sort-Object LastWriteTime -Descending | Select-Object -First 1).Name
}
$keep = $keep | Sort-Object -Unique
$pruned = 0
foreach ($b in $bundles) {
    if ($keep -notcontains $b.Name) { Remove-Item $b.FullName -Force; $pruned++ }
}
$states = @(Get-ChildItem $OFFBOX -Directory -Filter "state-2*" | Sort-Object LastWriteTime -Descending)
$states | Select-Object -Skip $KEEP_DAILY | ForEach-Object { Remove-Item $_.FullName -Recurse -Force; $pruned++ }
Write-Host "    pruned: $pruned item(s)"

Write-Host ""
Write-Host "[OK] GERMLINE SAFE - bundle + drill green, germline_lag=0 ($STAMP), notes=$noteCount"
