# ============================================================================
# OCTOPUS - OWNER COMMANDS 2026-08-16   (ASCII-only + UTF-8 BOM)
# Run blocks ONE BY ONE in PowerShell. Read each result before the next.
# ============================================================================

# openssl resolution: PATH first, Git fallback
if (-not (Get-Command openssl -ErrorAction SilentlyContinue)) {
    $env:Path += ";C:\Program Files\Git\usr\bin"
}

Write-Host "======================================================"
Write-Host "STEP 1 - Sign trust-boundary.json (Ed25519, owner key)"
Write-Host "======================================================"
cd F:\backup
openssl pkeyutl -sign `
  -inkey "$HOME\.octopus-signing\octopus-owner-ed25519-private.pem" `
  -rawin -in "4d_system\config\trust-boundary.json" `
  -out "4d_system\config\trust-boundary.json.sig"
if ($LASTEXITCODE -ne 0) { Write-Host "SIGN FAILED - stop here"; exit 1 }

Write-Host ""
Write-Host "--- VERIFY STEP 1 (expect: Signature Verified Successfully) ---"
openssl pkeyutl -verify `
  -pubin -inkey "_ops\owner-signing\octopus-owner-ed25519-public.pem" `
  -rawin -in "4d_system\config\trust-boundary.json" `
  -sigfile "4d_system\config\trust-boundary.json.sig"

# ============================================================================
Write-Host ""
Write-Host "======================================================"
Write-Host "STEP 2 - Sign AEB bundle txt (same key)"
Write-Host "======================================================"
openssl pkeyutl -sign `
  -inkey "$HOME\.octopus-signing\octopus-owner-ed25519-private.pem" `
  -rawin -in "_ops\audit\bundles\AEB-20260816-000508.txt" `
  -out "_ops\audit\bundles\AEB-20260816-000508.txt.sig"
if ($LASTEXITCODE -ne 0) { Write-Host "SIGN FAILED - stop here"; exit 1 }

Write-Host ""
Write-Host "--- VERIFY STEP 2 (expect: Signature Verified Successfully) ---"
openssl pkeyutl -verify `
  -pubin -inkey "_ops\owner-signing\octopus-owner-ed25519-public.pem" `
  -rawin -in "_ops\audit\bundles\AEB-20260816-000508.txt" `
  -sigfile "_ops\audit\bundles\AEB-20260816-000508.txt.sig"

# ============================================================================
# ONLY AFTER BOTH VERIFICATIONS PASS:
# ============================================================================
Write-Host ""
Write-Host "======================================================"
Write-Host "STEP 3 - Enable TCB enforce (trust boundary halts edits)"
Write-Host "======================================================"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
Copy-Item "_ops\OCTOPUS-flags.cmd" "_ops\OCTOPUS-flags.cmd.prev-$stamp"
Add-Content -Path "_ops\OCTOPUS-flags.cmd" -Value "set OCTOPUS_TCB_MANIFEST_ENFORCE=1" -Encoding ascii
Write-Host "backup: _ops\OCTOPUS-flags.cmd.prev-$stamp"

Write-Host ""
Write-Host "--- RESTART (official procedure; ~5 min, cortex may need a 2nd try) ---"
powershell -NoProfile -ExecutionPolicy Bypass -File "_ops\RESTART-ALL.ps1"

Write-Host ""
Write-Host "--- VERIFY STEP 3: flag loaded + organism fresh + beat advancing ---"
(Get-Content "_ops\state\flags-loaded-organism.json" -Raw | ConvertFrom-Json).flags.OCTOPUS_TCB_MANIFEST_ENFORCE
Get-Content "_ops\state\ORGANISM-STATE.json" -Raw | ConvertFrom-Json |
  Select-Object beat, started, ts, stop_organism, halted, frozen

Write-Host ""
Write-Host "Expected: flag = 1 | stop_organism = False | halted = null | beat > before"
Write-Host "DONE. Next: reply the votes (R16 / DA-1..3 / auditor / FUZZY) in chat."
