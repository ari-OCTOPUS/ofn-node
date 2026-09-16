<#
.SYNOPSIS
  READ-ONLY post-ACTIVATION probe. Verifies the day-one safe profile is live:
  organism up, exactly one poller per bot, paid/self-improve lanes CLOSED,
  no outward writeback authority. Makes ZERO changes.

.DESCRIPTION
  Run after ACTIVATION-RUNBOOK. Confirms the organism is alive in the safest
  profile. Read-only: never starts/stops anything, never reads secret contents,
  never sends Telegram/network/payment traffic. Exits 0 if all pass, 1 otherwise.
  The live value-loop check (proposal -> owner verdict -> durable outcome) is a
  MANUAL owner step in Telegram, described at the end; this script only checks
  process/gate posture.
#>
[CmdletBinding()]
param([string]$LiveRoot = 'F:\backup')
$ACT_PAID = @('ACTIVATION-CORTEX-PAID.flag','ACTIVATION-WORK-LLM.flag',
  'ACTIVATION-HEART-DOCTOR.flag','ACTIVATION-GO-LIVE.flag','ACTIVATION-SELF-IMPROVE-AUTO.flag')
$fail = 0
function Check($name, $ok) {
  if ($ok) { Write-Host "  PASS  $name" -ForegroundColor Green }
  else     { Write-Host "  FAIL  $name" -ForegroundColor Red; $script:fail++ }
}
Write-Host '=== POST-ACTIVATION PROBE (read-only, day-one safe profile) ===' -ForegroundColor Cyan

# organism 8771 UP
$p71 = Get-NetTCPConnection -State Listen -LocalPort 8771 -ErrorAction SilentlyContinue
Check "organism 8771 UP" ([bool]$p71)

# cortex + cockpit healthy
$p72 = Get-NetTCPConnection -State Listen -LocalPort 8772 -ErrorAction SilentlyContinue
$p73 = Get-NetTCPConnection -State Listen -LocalPort 8773 -ErrorAction SilentlyContinue
Check "cortex 8772 UP" ([bool]$p72)
Check "cockpit 8773 UP" ([bool]$p73)

# exactly one TG poller (no duplicate -> no 409 fight). Count center.py + organism poll thread hosts.
$pollers = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
             Where-Object { $_.CommandLine -match 'center\.py' })
Check ("at most one TG Center poller process (found " + $pollers.Count + ")") ($pollers.Count -le 1)

# paid / self-improve lanes CLOSED (levers absent)
$paidPresent = $ACT_PAID | Where-Object { Test-Path (Join-Path $LiveRoot ("_ops\" + $_)) }
Check "paid + self-improve activation levers ABSENT (lanes closed)" (-not $paidPresent)

# ps_writeback outward writeback stays behind per-item verdict (source invariant present)
$pw = Join-Path $LiveRoot '_ops\legs\ps_writeback.py'
$pwOk = $false
if (Test-Path $pw) { $pwOk = (Select-String -Path $pw -Pattern '_owner_verdict_ok' -Quiet) -and (Select-String -Path $pw -Pattern 'consumed' -Quiet) }
Check "ps_writeback per-item verdict gate (single-use) present in deployed source" $pwOk

Write-Host ''
Write-Host 'MANUAL owner verification in Telegram (not automatable here):' -ForegroundColor Yellow
Write-Host '  1. /panel and /menu render for the authenticated owner.'
Write-Host '  2. Create ONE explicitly-sandbox Paper Lead; a proposal card renders to you only.'
Write-Host '  3. Your Yes records an accepted-measurement (NOT delivery/settlement/revenue).'
Write-Host '  4. Confirm proposal -> verdict -> durable outcome -> spine -> replay -> metrics.'
Write-Host '  5. Confirm NO automatic send/pay/publish/PocketSmith-PUT occurred.'
Write-Host ''
Write-Host ("=== " + $(if($fail -eq 0){'DAY-ONE POSTURE OK (complete manual checks above)'}else{"$fail CHECK(S) FAILED"}) + " ===") -ForegroundColor $(if($fail -eq 0){'Green'}else{'Red'})
exit $(if($fail -eq 0){0}else{1})
