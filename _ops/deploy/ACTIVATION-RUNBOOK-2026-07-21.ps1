<#
.SYNOPSIS
  ACTIVATION runbook - the SEPARATE, FINAL owner vote. Brings the organism to life in the
  safest day-one profile. DEFAULT = DRY-RUN. Acts only with -Apply -IUnderstand.
  This is the ONLY script permitted to remove STOP-ORGANISM.

.DESCRIPTION
  Run this ONLY after: (1) deploy-to-live.ps1 has put the canonical code on the live tree,
  (2) the Telegram bot token has been rotated via BotFather and placed in F:\backup\.env
  (owner-only - this script never reads or writes the token), (3) the owner has said
  "activation: yes".

  Safest day-one profile enabled by default:
    * organism + Telegram LIVE, everything PROPOSE-ONLY
    * paid LLM tier CLOSED  (no ACTIVATION-CORTEX-PAID/WORK-LLM/HEART-DOCTOR/GO-LIVE created)
    * self-improve auto CLOSED (no ACTIVATION-SELF-IMPROVE-AUTO created)
    * PocketSmith writeback stays behind per-item owner verdict (fail-closed)
    * drawdown guard stays SHADOW alert-only (HH_DRAWDOWN_ENFORCE not set)
    * callback tokens ON (needs OCTOPUS_CB_SECRET already provisioned by owner)

  Core value-loop WIRE flags are turned on (all propose-only / observe-only / measurement-only).
  The paid ACTIVATION-*.flag levers are intentionally NOT created - activation of any paid or
  self-modifying lane is a further, explicit owner act (create the specific .flag by hand).

.PARAMETER CoreFlags
  The WIRE_* flags to enable (safe propose-only defaults). Edit to taste before running.

.PARAMETER EnableCbToken
  Turn on OCTOPUS_WIRE_CB_TOKEN. Requires OCTOPUS_CB_SECRET already set (owner). If the secret
  is absent, the callback layer fails CLOSED - so this is safe to leave on.
#>
[CmdletBinding()]
param(
  [string]$LiveRoot = 'F:\backup',
  [string[]]$CoreFlags = @(
    'OCTOPUS_WIRE_MENU_V2',
    'OCTOPUS_WIRE_VERDICT_OUTCOME',
    'OCTOPUS_WIRE_SPINE',
    'OCTOPUS_WIRE_CONTEXT_FENCE',
    'OCTOPUS_WIRE_LEAD_OUTCOME',
    'OCTOPUS_WIRE_MEMORY_GATE',
    'OCTOPUS_WIRE_PROPOSAL_BUTTONS',
    'OCTOPUS_WIRE_MISSION_RUNNER'
  ),
  [switch]$EnableCbToken = $true,
  [switch]$Apply,
  [switch]$IUnderstand
)
$ErrorActionPreference = 'Stop'
$EXPECTED_STOP_SHA = 'C8FE7176514E3DA8629DBF0A4C411D2909138EDE12C2739C2F8E8D43295CD099'
$STOP = Join-Path $LiveRoot '_ops\STOP-ORGANISM'
$ENVFILE = Join-Path $LiveRoot '.env'
$DoIt = $Apply -and $IUnderstand
function Step($m){ if($DoIt){Write-Host "[APPLY]   $m"}else{Write-Host "[DRY-RUN] would $m"} }
function Note($m){ Write-Host "          $m" }
function Abort($m){ Write-Error "ABORT: $m"; exit 1 }

Write-Host "=== ACTIVATION runbook 2026-07-21 ($(if($DoIt){'APPLY'}else{'DRY-RUN'})) ===" -ForegroundColor Cyan
Write-Host "    safest day-one profile: propose-only, paid CLOSED, self-improve CLOSED, writeback per-item, drawdown shadow" -ForegroundColor DarkCyan

# --- preconditions the owner must have satisfied (checked, not performed, here) ---
if (-not (Test-Path $ENVFILE)) { Abort ".env not found - the (rotated) Telegram token must be provisioned by the owner first." }
Note ".env present (token content NOT read by this script)"
if (Test-Path $STOP) {
  $h = (Get-FileHash -Algorithm SHA256 $STOP).Hash
  if ($h -ne $EXPECTED_STOP_SHA) { Abort "STOP-ORGANISM is not the expected owner marker ($h) - refusing to proceed." }
  Note "STOP-ORGANISM present + verified ($h)"
} else {
  Note "STOP-ORGANISM already absent (organism may already be activatable)"
}

# --- 1. core WIRE flags (safe, propose-only). Written to the OS/user env, NOT to a bat backup. ---
foreach ($f in $CoreFlags) {
  Step "set env $f=1 (User scope)"
  if ($DoIt) { [Environment]::SetEnvironmentVariable($f, '1', 'User') }
}
if ($EnableCbToken) {
  if (-not [Environment]::GetEnvironmentVariable('OCTOPUS_CB_SECRET','User') -and -not $env:OCTOPUS_CB_SECRET) {
    Note "WARNING: OCTOPUS_WIRE_CB_TOKEN requested but OCTOPUS_CB_SECRET not set - callback layer will fail CLOSED (safe). Provision the secret to actually use signed callbacks."
  }
  Step "set env OCTOPUS_WIRE_CB_TOKEN=1 (User scope)"
  if ($DoIt) { [Environment]::SetEnvironmentVariable('OCTOPUS_WIRE_CB_TOKEN','1','User') }
}
Note "NOT set (intentionally): HH_DRAWDOWN_ENFORCE, OCTOPUS_WIRE_PS_WRITEBACK, and every ACTIVATION-*.flag paid/self-improve lever."

# --- 2. remove the kill-switch (the ONLY script allowed to) ---
Step "remove STOP-ORGANISM (kill-switch) - organism may now start"
if ($DoIt -and (Test-Path $STOP)) { Remove-Item $STOP -Force }

# --- 3. start organism + TG center (fresh processes) ---
Step "launch organism  (RUN-ORGANISM.bat, detached)"
Step "launch TG center (telegram_center\RUN-TG-CENTER.bat, detached)"
if ($DoIt) {
  Start-Process -FilePath (Join-Path $LiveRoot '_ops\RUN-ORGANISM.bat') -WorkingDirectory (Join-Path $LiveRoot '_ops') -WindowStyle Hidden
  Start-Sleep -Seconds 3
  Start-Process -FilePath (Join-Path $LiveRoot '_ops\telegram_center\RUN-TG-CENTER.bat') -WorkingDirectory (Join-Path $LiveRoot '_ops') -WindowStyle Hidden
}

# --- 4. post-activation probes ---
Step "probe: 8771 up, cortex 8772 up, cockpit 8773 up, TG poller alive, paid_gate CLOSED"
if ($DoIt) {
  Start-Sleep -Seconds 8
  $p71 = Get-NetTCPConnection -State Listen -LocalPort 8771 -ErrorAction SilentlyContinue
  Note ("organism 8771 up? = " + [bool]$p71)
  Note "Verify manually in Telegram: /panel renders; a proposal card's Yes records an accepted-measurement (NOT a delivery/settlement); paid LLM stays gated; no PocketSmith PUT without a per-item verdict."
  if (-not $p71) { Note "organism did not bind 8771 - check _ops logs; STOP was removed so re-create it to halt if needed." }
  Write-Host "=== ACTIVATION applied. Roll back = create STOP-ORGANISM (33B 'telegram kill-switch') to halt, then deploy rollback if needed. ===" -ForegroundColor Green
} else {
  Write-Host "=== DRY-RUN complete - nothing activated. Re-run with -Apply -IUnderstand ONLY after 'activation: yes'. ===" -ForegroundColor Yellow
}
