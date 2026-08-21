# OCTOPUS - SIGN OWNER_SIGNATURE_BUNDLE_V1 root  (ASCII)
# Owner-only. Do not run from an agent session.
# Abort on ANY hash mismatch BEFORE any sign.
# Prints BUNDLE_ROOT_SIGNATURE_VERIFIED only if the detached root signature
# verifies against the anchor public key.
# Never prints private key, PEM contents, or any secret.

if (-not (Get-Command openssl -ErrorAction SilentlyContinue)) {
    $env:Path += ";C:\Program Files\Git\usr\bin"
}

Set-Location F:\backup

$pub  = "_ops\owner-signing\octopus-owner-ed25519-public.pem"
$priv = "$HOME\.octopus-signing\octopus-owner-ed25519-private.pem"
$dir  = "_ops\owner-signing\bundle-v1"

# fingerprint anchor check (fail-closed before ANY sign)
# NOTE: never pipe binary DER through the PowerShell pipeline (text corruption
# produces a wrong fingerprint -> false abort). Write DER to a temp file and
# hash the file bytes with Get-FileHash instead.
$tmp = Join-Path $env:TEMP "octopus-pubkey-der.bin"
openssl pkey -pubin -in $pub -outform DER -out $tmp 2>$null
if (-not (Test-Path $tmp)) {
    Write-Host "FINGERPRINT COMPUTE FAILED - ABORT before any sign"
    exit 1
}
$fp = (Get-FileHash $tmp -Algorithm SHA256).Hash.ToLower()
Remove-Item $tmp -ErrorAction SilentlyContinue
Write-Host "pubkey fingerprint: $fp"
if ($fp -ne "2413e9746f13afc900b31ad4d966a6783d73662f661fa0d6dc578e9b244ab6b2") {
    Write-Host "FINGERPRINT MISMATCH - ABORT before any sign"
    exit 1
}

$expected = Get-Content "$dir\bundle-hashes-expected.json" -Raw | ConvertFrom-Json
$rootFile = "$dir\OWNER_SIGNATURE_BUNDLE_V1.root-payload.txt"
$sigFile  = "$dir\OWNER_SIGNATURE_BUNDLE_V1.root-payload.txt.sig"

Write-Host "======================================================"
Write-Host "STEP 0 - Hash manifest + root payload (abort before sign)"
Write-Host "======================================================"

$manifestHash = (Get-FileHash "$dir\OWNER_SIGNATURE_MANIFEST_V1.json" -Algorithm SHA256).Hash.ToLower()
$rootHash     = (Get-FileHash $rootFile -Algorithm SHA256).Hash.ToLower()
Write-Host "manifest got $manifestHash"
Write-Host "manifest want $($expected.manifest_sha256)"
Write-Host "root     got $rootHash"
Write-Host "root     want $($expected.bundle_root)"

if ($manifestHash -ne $expected.manifest_sha256 -or $rootHash -ne $expected.bundle_root) {
    Write-Host "HASH MISMATCH - ABORT before any sign"
    exit 1
}

Write-Host "======================================================"
Write-Host "STEP 1 - Sign bundle root payload (owner private key)"
Write-Host "======================================================"
openssl pkeyutl -sign -inkey $priv -rawin -in $rootFile -out $sigFile
if ($LASTEXITCODE -ne 0) { Write-Host "SIGN FAILED"; exit 1 }

Write-Host "======================================================"
Write-Host "STEP 2 - Verify detached root signature (anchor public key)"
Write-Host "======================================================"
openssl pkeyutl -verify -pubin -inkey $pub -rawin -in $rootFile -sigfile $sigFile
if ($LASTEXITCODE -ne 0) { Write-Host "VERIFY FAILED"; exit 1 }

Write-Host ""
Write-Host "BUNDLE_ROOT_SIGNATURE_VERIFIED"
Write-Host "STOP. Return the .sig path to the agent for fan-out receipts."
Write-Host "Do not start any operational execution from this script."
exit 0
