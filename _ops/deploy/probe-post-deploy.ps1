<#
.SYNOPSIS
  READ-ONLY post-deploy probe. Verifies the live tree is on the canonical release,
  the organism is DOWN, STOP is intact, and no activation lever is present.
  Makes ZERO changes. Safe to run any time.

.DESCRIPTION
  Run after deploy-to-live.ps1 (or any time) to confirm the deploy invariants hold.
  Exits 0 if all critical checks pass, 1 otherwise. Never mutates anything, never
  starts/stops a process, never reads secret contents.

.PARAMETER ExpectedSha
  Canonical FINAL_SHA the live tree should be on. Default: live 'master' rev.
#>
[CmdletBinding()]
param(
  [string]$LiveRoot = 'F:\backup',
  [string]$ExpectedSha = ''
)
$EXPECTED_STOP_SHA = 'C8FE7176514E3DA8629DBF0A4C411D2909138EDE12C2739C2F8E8D43295CD099'
$STOP = Join-Path $LiveRoot '_ops\STOP-ORGANISM'
$ACT_FLAGS = @('ACTIVATION-CORTEX-PAID.flag','ACTIVATION-DEBATE.flag','ACTIVATION-GO-LIVE.flag',
  'ACTIVATION-HEART-DOCTOR.flag','ACTIVATION-PULSE.flag','ACTIVATION-RESEARCH-EARLY.flag',
  'ACTIVATION-SELF-IMPROVE-AUTO.flag','ACTIVATION-WORK-LLM.flag')
$fail = 0
function Check($name, $ok) {
  if ($ok) { Write-Host "  PASS  $name" -ForegroundColor Green }
  else     { Write-Host "  FAIL  $name" -ForegroundColor Red; $script:fail++ }
}
Write-Host '=== POST-DEPLOY PROBE (read-only) ===' -ForegroundColor Cyan

# STOP present + byte-identical
$stopOk = $false
if (Test-Path $STOP) { $stopOk = ((Get-FileHash -Algorithm SHA256 $STOP).Hash -eq $EXPECTED_STOP_SHA) }
Check "STOP-ORGANISM present and byte-identical (kill-switch intact)" $stopOk

# organism 8771 DOWN
$p71 = Get-NetTCPConnection -State Listen -LocalPort 8771 -ErrorAction SilentlyContinue
Check "organism 8771 DOWN (deploy must not start it)" (-not $p71)

# no Telegram poller (center.py) process
$center = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
          Where-Object { $_.CommandLine -match 'center\.py' }
Check "no TG Center poller process running" (-not $center)

# cortex 8772 + cockpit 8773 UP (restarted onto new code)
$p72 = Get-NetTCPConnection -State Listen -LocalPort 8772 -ErrorAction SilentlyContinue
$p73 = Get-NetTCPConnection -State Listen -LocalPort 8773 -ErrorAction SilentlyContinue
Check "cortex 8772 UP" ([bool]$p72)
Check "cockpit 8773 UP" ([bool]$p73)

# no activation lever present -> paid/live gates closed
$present = $ACT_FLAGS | Where-Object { Test-Path (Join-Path $LiveRoot ("_ops\" + $_)) }
Check "no ACTIVATION-*.flag present (paid/self-improve/go-live gates closed)" (-not $present)

# live tree content == FINAL_SHA
Push-Location $LiveRoot
try {
  $liveHead = (git rev-parse HEAD 2>$null)
  if (-not $ExpectedSha) { $ExpectedSha = (git rev-parse master 2>$null) }
  Check ("live HEAD == expected FINAL_SHA (" + $ExpectedSha + ")") ($liveHead -eq $ExpectedSha)
} finally { Pop-Location }

Write-Host ("=== " + $(if($fail -eq 0){'ALL DEPLOY INVARIANTS HOLD'}else{"$fail CHECK(S) FAILED"}) + " ===") -ForegroundColor $(if($fail -eq 0){'Green'}else{'Red'})
exit $(if($fail -eq 0){0}else{1})
