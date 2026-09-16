# OCTOPUS - K9 three-seed pre-reg payload sign 2026-08-20  (ASCII)
# Owner-only. Do not run from an agent session.
# Signing this is NOT permission to run K=9 now.
# Execution condition: ONLY_AFTER_4H_SOAK_PASS
# Expect SHA256: 1AAA7D544A24D06C4C332DBCD5051B332C93147FC9F5735D409249AF68981FA7

if (-not (Get-Command openssl -ErrorAction SilentlyContinue)) {
    $env:Path += ";C:\Program Files\Git\usr\bin"
}

Set-Location F:\backup
$pay = "02-DECISIONS\PRE-REG-K9-THREE-SEED-2026-08-20.json"
$sig = "02-DECISIONS\PRE-REG-K9-THREE-SEED-2026-08-20.json.sig"
$expect = "1AAA7D544A24D06C4C332DBCD5051B332C93147FC9F5735D409249AF68981FA7"
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

Write-Host "DONE. K=9 remains gated: ONLY_AFTER_4H_SOAK_PASS. Do not run K=9 now."
