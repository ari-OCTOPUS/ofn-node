# OCTOPUS - B1 payload sign 2026-08-20  (ASCII + UTF-8 BOM)
# Owner-only. Do not run from an agent session.
# Expect SHA256: E11F45E9A0913C066DE99F0A25EE1B7AA1621C2A7929B817F48BE4D5D9C72290

if (-not (Get-Command openssl -ErrorAction SilentlyContinue)) {
    $env:Path += ";C:\Program Files\Git\usr\bin"
}

Set-Location F:\backup
$pay = "02-DECISIONS\B1-SIGNING-PAYLOAD-2026-08-20.json"
$sig = "02-DECISIONS\B1-SIGNING-PAYLOAD-2026-08-20.json.sig"
$expect = "E11F45E9A0913C066DE99F0A25EE1B7AA1621C2A7929B817F48BE4D5D9C72290"

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
  -inkey "$HOME\.octopus-signing\octopus-owner-ed25519-private.pem" `
  -rawin -in $pay `
  -out $sig
if ($LASTEXITCODE -ne 0) { Write-Host "SIGN FAILED - stop here"; exit 1 }

Write-Host ""
Write-Host "--- VERIFY (expect: Signature Verified Successfully) ---"
openssl pkeyutl -verify `
  -pubin -inkey "_ops\owner-signing\octopus-owner-ed25519-public.pem" `
  -rawin -in $pay `
  -sigfile $sig
if ($LASTEXITCODE -ne 0) { Write-Host "VERIFY FAILED"; exit 1 }

Write-Host "DONE. Next: mark B1-SIGNING-CARD status SIGNED, then freeze restart baseline."
