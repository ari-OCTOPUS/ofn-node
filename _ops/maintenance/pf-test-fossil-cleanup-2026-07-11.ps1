# pf-test-fossil-cleanup-2026-07-11.ps1  (ASCII only - session 47)
# Owner-run maintenance. Decisions were delegated ("khodet tasmim begir") and taken in
# session 47; live-vault mutation is owner-scope, so this script executes them under
# the owner's hand. NOTHING is deleted: originals are quarantined under _Archive first.
# Idempotent - every step checks before acting. Safe while the organism is running
# (no restart, no process kill). Steps:
#   1) tag + fast-forward merge of the suite-hygiene branch into master
#   2) quarantine PF test fossils to _Archive + reset drafts.json/archive.json to []
#   3) untrack runtime projections fitness-latest/replication-latest + gitignore lines
#   4) re-run the full suite on the live tree (refreshes CAPABILITY-OK honestly)

$ErrorActionPreference = 'Stop'
$LIVE = 'F:\backup'
$BR   = 'claude/exciting-vaughan-26c965'
$TAG  = 'pre-merge-20260711-suite-hygiene'
$QUAR = Join-Path $LIVE '_Archive\Logs\test-contamination-2026-07-11\live-originals'
$PF   = Join-Path $LIVE '03 - Projects\____PF____'   # placeholder replaced below
# real PF folder name contains Persian; build it from unicode escapes to keep this file ASCII:
$pfName = [char]0x0627 + [char]0x0648 + [char]0x0646 + [char]0x0644 + [char]0x06CC + ' ' + [char]0x0641 + [char]0x0646 + [char]0x0632
$PF   = Join-Path $LIVE ("03 - Projects\" + $pfName)

function Step($msg) { Write-Host "== $msg" -ForegroundColor Cyan }

# --- 1) merge branch into master (tag first) --------------------------------
Step "1) merge $BR into master"
Set-Location $LIVE
$merged = (git merge-base --is-ancestor $BR master 2>$null; $LASTEXITCODE -eq 0)
if ($merged) {
    Write-Host "   already merged - skip"
} else {
    git tag $TAG master 2>$null
    git merge --ff-only $BR
    if ($LASTEXITCODE -ne 0) { throw "ff-merge failed - run: git merge $BR (then re-run this script)" }
    Write-Host "   merged OK (rollback tag: $TAG)"
}

# --- 2) quarantine fossils + reset business state to [] ---------------------
Step "2) quarantine PF test fossils"
New-Item -ItemType Directory -Force $QUAR | Out-Null
$drafts = Join-Path $PF 'studio\drafts.json'
$bak    = Join-Path $PF 'studio\drafts.json.bak'
$arch   = Join-Path $PF 'brain\archive.json'
$hebb   = Join-Path $PF 'brain\hebb_orch.json'
$stray  = Join-Path $LIVE '_ops\2026-07-21'
foreach ($f in @($drafts, $arch)) {
    if ((Test-Path $f) -and -not (Test-Path (Join-Path $QUAR (Split-Path $f -Leaf)))) {
        Copy-Item $f (Join-Path $QUAR (Split-Path $f -Leaf))
        Write-Host "   quarantine copy: $(Split-Path $f -Leaf)"
    }
}
foreach ($f in @($hebb, $bak)) {
    if (Test-Path $f) { Move-Item $f (Join-Path $QUAR (Split-Path $f -Leaf)) -Force; Write-Host "   moved out: $(Split-Path $f -Leaf)" }
}
if (Test-Path $stray) { Move-Item $stray (Join-Path $QUAR '_ops-2026-07-21-stray') -Force; Write-Host "   moved stray _ops\2026-07-21" }
# reset to [] (all 244 drafts + all archive entries were test fixtures - proven session 47)
foreach ($f in @($drafts, $arch)) {
    if (Test-Path $f) { [IO.File]::WriteAllText($f, '[]') ; Write-Host "   reset to []: $(Split-Path $f -Leaf)" }
}
git add -- $drafts $arch $hebb $bak 2>$null
git commit -m "chore(pf): quarantine test-state fossils to _Archive, reset drafts/archive (session 47 delegated cleanup)" 2>$null
if ($LASTEXITCODE -eq 0) { Write-Host "   committed" } else { Write-Host "   nothing to commit (already clean)" }

# --- 3) untrack runtime projections + gitignore ------------------------------
Step "3) untrack fitness-latest/replication-latest (runtime projections)"
$gi = Join-Path $LIVE '.gitignore'
$giText = [IO.File]::ReadAllText($gi)
$lines = @('_ops/state/fitness-latest.json', '_ops/state/replication-latest.json')
$added = $false
foreach ($l in $lines) {
    if ($giText -notmatch [regex]::Escape($l)) { [IO.File]::AppendAllText($gi, "$l`n"); $added = $true }
}
foreach ($l in $lines) { git rm --cached --quiet -- $l 2>$null }
git add -- .gitignore
git commit -m "chore(git): ignore runtime projections fitness/replication-latest (verdict 07-07 no.8 completion)" 2>$null
if ($LASTEXITCODE -eq 0) { Write-Host "   committed" } else { Write-Host "   nothing to commit" }

# --- 4) full suite on live tree (marker refresh) -----------------------------
Step "4) full suite on live tree (refreshes CAPABILITY-OK with live fingerprint)"
Set-Location (Join-Path $LIVE '_ops\tests')
python -X utf8 run_all.py
if ($LASTEXITCODE -ne 0) { throw "suite RED - capability marker revoked (fail-closed). Check output above." }
Set-Location $LIVE
Write-Host ""
Step "DONE - git status now:"
git -c core.quotepath=off status --porcelain
Write-Host "(expected: only runtime M files like HEARTBEAT/ledger/governor-alerts/neural jsons)"
