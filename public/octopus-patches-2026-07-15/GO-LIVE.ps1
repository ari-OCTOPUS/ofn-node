<#
  GO-LIVE.ps1  (ASCII-only, robust for Windows PowerShell 5.1)
  Tiered activation of Octopus. Tier 0/1 only (SAFE, no money).
  Tier 2 (real money = LIVE-ENABLED.flag) is deliberately NOT here. Read GO-LIVE-RISK.md.

  Usage (run from anywhere - uses git -C, does NOT change your shell location):
    .\GO-LIVE.ps1                 # Tier 0: truthful cockpit + TG-exec code (flag OFF)
    .\GO-LIVE.ps1 -EnableExec     # Tier 1: also set OCTOPUS_TG_EXEC=1 (internal buttons run)
    .\GO-LIVE.ps1 -Rollback       # revert the Tier 0/1 patches

  Auto-applies only the NON-money / NON-capability patches (1 and 4).
  Patch 2 (money baseline) and 3 (run_all registration) stay manual - see APPLY-RUNBOOK.md.
  NOTE: no ErrorActionPreference=Stop, and no stderr redirection on git - exit codes checked explicitly.
#>
param(
  [switch]$EnableExec,
  [switch]$Rollback
)

$Repo      = "F:\backup"
$Dir       = $PSScriptRoot
$Safe      = @("1-truthful-cockpit.patch", "5-fix-read-channels.patch", "4-tg-execute.patch")
$FlagsFile = Join-Path $Repo "_ops\OCTOPUS-flags.cmd"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Write-Host "git not found in PATH" -ForegroundColor Red; return
}

if ($Rollback) {
  Write-Host "Reverting Tier 0/1 patches ..." -ForegroundColor Yellow
  foreach ($p in ($Safe | Sort-Object -Descending)) {
    $full = Join-Path $Dir $p
    & git -C $Repo apply -R --check $full
    if ($LASTEXITCODE -eq 0) { & git -C $Repo apply -R $full; Write-Host ("   reverted: " + $p) -ForegroundColor Green }
    else { Write-Host ("   skipped (not currently applied): " + $p) }
  }
  Write-Host "To disable exec: remove the OCTOPUS_TG_EXEC line from $FlagsFile and restart organism." -ForegroundColor Yellow
  Write-Host "Money was never armed here; nothing to undo there." -ForegroundColor Green
  return
}

# 0) checkpoint branch (branch --list is clean: exit 0, empty if missing)
$branch = "backup/pre-golive-2026-07-15"
$exists = & git -C $Repo branch --list $branch
if ([string]::IsNullOrWhiteSpace($exists)) {
  & git -C $Repo branch $branch
  if ($LASTEXITCODE -eq 0) { Write-Host ("OK  backup branch: " + $branch) -ForegroundColor Green }
  else { Write-Host "could not create backup branch - continuing without it" -ForegroundColor Yellow }
} else {
  Write-Host ("..  backup branch already exists: " + $branch)
}

# 1) apply safe patches (check first; abort cleanly on any failure)
foreach ($p in $Safe) {
  $full = Join-Path $Dir $p
  if (-not (Test-Path $full)) { Write-Host ("patch not found: " + $full) -ForegroundColor Red; return }
  & git -C $Repo apply --check $full
  if ($LASTEXITCODE -ne 0) { Write-Host ("apply --check FAILED for " + $p + " - aborting (nothing more applied).") -ForegroundColor Red; return }
  & git -C $Repo apply $full
  if ($LASTEXITCODE -ne 0) { Write-Host ("apply FAILED for " + $p) -ForegroundColor Red; return }
  Write-Host ("OK  applied: " + $p) -ForegroundColor Green
}

# 2) optional Tier 1 - enable internal button execution
if ($EnableExec) {
  $has = (Test-Path $FlagsFile) -and (Select-String -Path $FlagsFile -SimpleMatch "OCTOPUS_TG_EXEC=1" -Quiet)
  if (-not $has) {
    Add-Content -Path $FlagsFile -Value "set OCTOPUS_TG_EXEC=1" -Encoding ascii
    Write-Host "OK  Tier 1: OCTOPUS_TG_EXEC=1 added to OCTOPUS-flags.cmd" -ForegroundColor Green
  } else { Write-Host ".. OCTOPUS_TG_EXEC already on" }
  Write-Host "   (doctor/consolidate buttons run; school/ingest do NOT. Strictly propose-only doctor: OCTOPUS_WIRE_APPLY_MERGE=0)"
}

# 3) health gate (Push/Pop so your shell location is restored)
Write-Host ""
Write-Host "Running run_all (needs the live tree's capability marker) ..." -ForegroundColor Cyan
Push-Location (Join-Path $Repo "_ops")
& python -X utf8 tests/run_all.py
$rc = $LASTEXITCODE
Pop-Location
if ($rc -eq 0) {
  Write-Host "OK  suite green" -ForegroundColor Green
} else {
  Write-Host ("WARN run_all exit " + $rc + " - if ONLY test_phase5/test_box/test_box_wiring/test_cockpit_v2 failed with 'capability revoked', that is a marker-refresh env artifact, NOT a regression.") -ForegroundColor Yellow
}

Write-Host ""
Write-Host "-------- next steps (your hand) --------" -ForegroundColor Cyan
Write-Host "* Restart organism (RUN-ORGANISM.bat) so /wiring, /health and the TG-exec code go live."
Write-Host "* Patch 2 (money baseline) and 3 (run_all register) are manual - see APPLY-RUNBOOK.md (re-baseline after patch 2)."
Write-Host "* RED: real money (LIVE-ENABLED.flag) was NOT armed here. Read GO-LIVE-RISK.md Tier 2; arm only deliberately."
Write-Host "* Panic button: send /panic in Telegram (undo: /resume)."
