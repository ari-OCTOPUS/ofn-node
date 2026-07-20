<#
.SYNOPSIS
  Roll the LIVE tree back to the pre-deploy state from a snapshot made by deploy-to-live.ps1.
  DEFAULT = DRY-RUN. Acts only with -Apply -IUnderstand.

.DESCRIPTION
  Reverts the live working tree to the recorded pre-deploy commit and restores untracked
  runtime work from the snapshot. Does NOT touch STOP-ORGANISM. Does NOT restart the organism.
  After rollback, the owner restarts cortex/cockpit if desired (same class as deploy).

.PARAMETER SnapshotDir
  The E:\deploy-snapshots\live-<sha> directory produced by deploy-to-live.ps1.

.PARAMETER PreDeploySha
  The commit the live tree was on before deploy (default: read from the snapshot dir name).
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$SnapshotDir,
  [string]$LiveRoot = 'F:\backup',
  [string]$PreDeploySha = '',
  [switch]$Apply,
  [switch]$IUnderstand
)
$ErrorActionPreference = 'Stop'
$EXPECTED_STOP_SHA = 'C8FE7176514E3DA8629DBF0A4C411D2909138EDE12C2739C2F8E8D43295CD099'
$STOP = Join-Path $LiveRoot '_ops\STOP-ORGANISM'
$DoIt = $Apply -and $IUnderstand
function Step($m){ if($DoIt){Write-Host "[APPLY]   $m"}else{Write-Host "[DRY-RUN] would $m"} }
function Abort($m){ Write-Error "ABORT: $m"; exit 1 }

if (-not (Test-Path $SnapshotDir)) { Abort "snapshot dir not found: $SnapshotDir" }
if (Test-Path $STOP) {
  $h = (Get-FileHash -Algorithm SHA256 $STOP).Hash
  if ($h -ne $EXPECTED_STOP_SHA) { Abort "STOP-ORGANISM not the expected owner marker ($h) - refusing." }
}
if (-not $PreDeploySha) {
  $leaf = Split-Path $SnapshotDir -Leaf     # live-<shortsha>
  $PreDeploySha = ($leaf -replace '^live-','')
}
Write-Host "=== rollback to $PreDeploySha from $SnapshotDir ($(if($DoIt){'APPLY'}else{'DRY-RUN'})) ===" -ForegroundColor Cyan

Push-Location $LiveRoot
try {
  Step "git checkout -f $PreDeploySha (restore tracked tree to pre-deploy commit)"
  if ($DoIt) { git checkout -f $PreDeploySha 2>&1 | Out-Null }
  Step "restore untracked runtime work from $SnapshotDir\worktree"
  if ($DoIt) {
    $wt = Join-Path $SnapshotDir 'worktree'
    if (Test-Path $wt) { Copy-Item (Join-Path $wt '*') $LiveRoot -Recurse -Force -ErrorAction SilentlyContinue }
  }
  Step "verify STOP-ORGANISM intact"
  if ($DoIt) {
    $h = (Get-FileHash -Algorithm SHA256 $STOP).Hash
    if ($h -ne $EXPECTED_STOP_SHA) { Abort "STOP changed during rollback." }
    Write-Host "=== rollback OK - live tree at $PreDeploySha, STOP intact. Restart cortex/cockpit manually if desired. ===" -ForegroundColor Green
  } else {
    Write-Host "=== DRY-RUN complete - no live change. ===" -ForegroundColor Yellow
  }
}
finally { Pop-Location }
