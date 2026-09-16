# OCTOPUS - sign both pending payloads 2026-08-20  (ASCII)
# Owner-only. Do not run from an agent session.
# Abort on hash mismatch BEFORE any sign.
# Expect A SHA256: 4C80264D2E3149E41C0600543BE98D8CBD339364F360F13ACA5318E29FF6A8A8
# Expect B SHA256: 1AAA7D544A24D06C4C332DBCD5051B332C93147FC9F5735D409249AF68981FA7
# Prints ALL_SIGNATURES_VERIFIED only if both verify.
# One success + one fail -> PARTIAL_SIGNATURE_FAILURE
# Never prints private key or PEM contents.

if (-not (Get-Command openssl -ErrorAction SilentlyContinue)) {
    $env:Path += ";C:\Program Files\Git\usr\bin"
}

Set-Location F:\backup

$pub = "_ops\owner-signing\octopus-owner-ed25519-public.pem"
$priv = "$HOME\.octopus-signing\octopus-owner-ed25519-private.pem"

$payA = "02-DECISIONS\OWNER-VERDICT-SHADOW-VERTICAL-SLICE-2026-08-20.json"
$sigA = "02-DECISIONS\OWNER-VERDICT-SHADOW-VERTICAL-SLICE-2026-08-20.json.sig"
$expA = "4C80264D2E3149E41C0600543BE98D8CBD339364F360F13ACA5318E29FF6A8A8"

$payB = "02-DECISIONS\PRE-REG-K9-THREE-SEED-2026-08-20.json"
$sigB = "02-DECISIONS\PRE-REG-K9-THREE-SEED-2026-08-20.json.sig"
$expB = "1AAA7D544A24D06C4C332DBCD5051B332C93147FC9F5735D409249AF68981FA7"

Write-Host "======================================================"
Write-Host "STEP 0 - Hash BOTH payloads (abort before any sign)"
Write-Host "======================================================"

$hashA = (Get-FileHash $payA -Algorithm SHA256).Hash
$hashB = (Get-FileHash $payB -Algorithm SHA256).Hash
Write-Host "A got  $hashA"
Write-Host "A want $expA"
Write-Host "B got  $hashB"
Write-Host "B want $expB"

if ($hashA -ne $expA -or $hashB -ne $expB) {
    Write-Host "HASH MISMATCH - ABORT before any sign"
    exit 1
}

function Sign-And-Verify {
    param(
        [string]$Label,
        [string]$Pay,
        [string]$Sig
    )
    Write-Host ""
    Write-Host "======================================================"
    Write-Host "SIGN $Label"
    Write-Host "======================================================"
    openssl pkeyutl -sign -inkey $priv -rawin -in $Pay -out $Sig
    if ($LASTEXITCODE -ne 0) {
        Write-Host "SIGN FAILED - $Label"
        return $false
    }
    Write-Host "--- VERIFY $Label (expect: Signature Verified Successfully) ---"
    openssl pkeyutl -verify -pubin -inkey $pub -rawin -in $Pay -sigfile $Sig
    if ($LASTEXITCODE -ne 0) {
        Write-Host "VERIFY FAILED - $Label"
        return $false
    }
    return $true
}

$okA = Sign-And-Verify -Label "A-SHADOW" -Pay $payA -Sig $sigA
$okB = Sign-And-Verify -Label "B-K9-PREREG" -Pay $payB -Sig $sigB

Write-Host ""
Write-Host "======================================================"
Write-Host "COMBINED RESULT"
Write-Host "======================================================"
if ($okA -and $okB) {
    Write-Host "ALL_SIGNATURES_VERIFIED"
    Write-Host "STOP. Return output to agent. Do not start soak from this script."
    exit 0
}
elseif ($okA -xor $okB) {
    Write-Host "PARTIAL_SIGNATURE_FAILURE"
    Write-Host "A=$okA B=$okB"
    exit 2
}
else {
    Write-Host "BOTH_SIGNATURES_FAILED"
    Write-Host "A=$okA B=$okB"
    exit 1
}
