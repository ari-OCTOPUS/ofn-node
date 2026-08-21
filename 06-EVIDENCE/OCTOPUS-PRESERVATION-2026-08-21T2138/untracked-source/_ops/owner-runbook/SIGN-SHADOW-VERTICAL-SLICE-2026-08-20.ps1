# OCTOPUS - Shadow vertical slice payload sign 2026-08-20  (ASCII)
# Owner-only. Do not run from an agent session.
# Expect SHA256: 4C80264D2E3149E41C0600543BE98D8CBD339364F360F13ACA5318E29FF6A8A8

if (-not (Get-Command openssl -ErrorAction SilentlyContinue)) {
    $env:Path += ";C:\Program Files\Git\usr\bin"
}

Set-Location F:\backup
$pay = "02-DECISIONS\OWNER-VERDICT-SHADOW-VERTICAL-SLICE-2026-08-20.json"
$sig = "02-DECISIONS\OWNER-VERDICT-SHADOW-VERTICAL-SLICE-2026-08-20.json.sig"
$expect = "4C80264D2E3149E41C0600543BE98D8CBD339364F360F13ACA5318E29FF6A8A8"
$pub = "_ops\owner-signing\octopus-owner-ed25519-public.pem"
$priv = "$HOME\.octopus-signing\octopus-owner-ed25519-private.pem"

Write-Host "======================================================"
Write-Host "STEP 0 - Hash payload (must match expect)"
Write-Host "======================================================"
$h = (Get-FileHash $pay -Algorithm SHA256).Hash
Write-Host "got   $h"
Write-Host "want  $expect"
if ($h -ne $expect) {
    Write-Host "HASH MISMATCH - do not sign"
    exit 1
}

Write-Host ""
Write-Host "======================================================"
Write-Host "STEP 1 - Sign payload (Ed25519, owner key)"
Write-Host "======================================================"
openssl pkeyutl -sign `
  -inkey $priv `
  -rawin -in $pay `
  -out $sig
if ($LASTEXITCODE -ne 0) { Write-Host "SIGN FAILED - stop here"; exit 1 }

Write-Host ""
Write-Host "--- VERIFY (expect: Signature Verified Successfully) ---"
openssl pkeyutl -verify `
  -pubin -inkey $pub `
  -rawin -in $pay `
  -sigfile $sig
if ($LASTEXITCODE -ne 0) { Write-Host "VERIFY FAILED"; exit 1 }

Write-Host "DONE. Do not start soak from this script. Wrapper is SIGN-ALL-PENDING-2026-08-20.ps1"
