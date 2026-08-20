# OCTOPUS - one-shot signing wrapper for three pending pre-reg payloads.
# OWNER-DIRECTIVE-12 section 12. Owner-only; run from an interactive PowerShell.
# Signs NOTHING until the trust anchor fingerprint matches. No experiments run here.
#
#  powershell -ExecutionPolicy Bypass -File _ops\owner-runbook\SIGN-PENDING-CARDS-2026-08-20.ps1
#
# Output: per-card SIGN+VERIFY lines; "ALL_THREE_SIGNATURES_VERIFIED" only on full
# success; otherwise "PARTIAL_SIGNATURE_FAILURE". Signatures land next to payloads
# as <payload>.sig (Ed25519 pure, openssl pkeyutl -rawin).

$ErrorActionPreference = "Stop"
Set-Location F:\backup
if (-not (Get-Command openssl -ErrorAction SilentlyContinue)) {
    $env:Path += ";C:\Program Files\Git\usr\bin"
}

# ── 1) TRUST ANCHOR (fail-closed first) ───────────────────────────────────────
$ANCHOR = "2413e9746f13afc900b31ad4d966a6783d73662f661fa0d6dc578e9b244ab6b2"
$fp = (openssl pkey -pubin -in "_ops\owner-signing\octopus-owner-ed25519-public.pem" -outform DER |
       sha256sum) -split ' ')[0].ToLower()
Write-Host "anchor = $ANCHOR"
Write-Host "pemfp  = $fp"
if ($fp -ne $ANCHOR) {
    Write-Host "TRUST ANCHOR MISMATCH - refusing to sign anything (fail-closed)."
    exit 5
}
Write-Host "TRUST ANCHOR OK"

# ── 2) payloads + pinned hashes ───────────────────────────────────────────────
$cards = @(
    @{ pay = "02-DECISIONS\PAYLOAD-EVENT-TIME-PROBE-2026-08-20.json";
       sha = "E175C9430647DA26096ABDB88B52DBC1F94E3E6CDCD9A0DC4C7F1FE322CB5157" },
    @{ pay = "02-DECISIONS\PAYLOAD-JUDGE-BIAS-PHASE2-2026-08-20.json";
       sha = "D4DF6C0B7D0A9B0DF921A6354A0BD407036807E8092AAF10569E708B8E80CB84" },
    @{ pay = "02-DECISIONS\PAYLOAD-FULL-LOOP-FLASH-2026-08-20.json";
       sha = "E9DC768BF7761B3950DB9FAE5C0AEFFF0606B93808497D2073D11D994E90DFC9" }
)

# ── 3) hash check + sign + verify, per card ──────────────────────────────────
$ok = 0
foreach ($c in $cards) {
    $p = $c.pay
    $sig = "$($p).sig"
    Write-Host ""
    Write-Host "=== $p ==="
    if (-not (Test-Path $p)) { Write-Host "MISSING payload"; continue }
    $h = (Get-FileHash $p -Algorithm SHA256).Hash
    Write-Host "sha256 = $h"
    if ($h -ne $c.sha) {
        Write-Host "HASH MISMATCH - expected $($c.sha) - SKIPPED (payload drifted)"
        continue
    }
    openssl pkeyutl -sign -rawin `
      -inkey "$HOME\.octopus-signing\octopus-owner-ed25519-private.pem" `
      -in $p -out $sig
    if ($LASTEXITCODE -ne 0) { Write-Host "SIGN FAILED"; continue }
    $v = openssl pkeyutl -verify -pubin -rawin `
      -inkey "_ops\owner-signing\octopus-owner-ed25519-public.pem" `
      -in $p -sigfile $sig
    if ($LASTEXITCODE -eq 0 -and $v -match "Verified") {
        Write-Host "SIGN+VERIFY OK -> $sig"
        $ok++
    } else {
        Write-Host "VERIFY FAILED"
    }
}

Write-Host ""
if ($ok -eq 3) {
    Write-Host "ALL_THREE_SIGNATURES_VERIFIED"
    exit 0
}
Write-Host "PARTIAL_SIGNATURE_FAILURE ($ok/3)"
exit 6
