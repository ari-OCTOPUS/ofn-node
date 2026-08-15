# RUN-AUDIT.ps1 - D1 independent audit runner (read-only)
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File RUN-AUDIT.ps1 -RepoRoot <path-to-nbb-control-plane-copy>
# Writes AUDIT-OUTPUT-<timestamp>.txt next to this script. Nothing is modified.

param(
    [string]$RepoRoot = "C:\Users\Armin\Desktop\OCTOPUS-NBB-CP-WORKING\nbb-control-plane"
)
$ErrorActionPreference = "Continue"
$out = "AUDIT-OUTPUT-$(Get-Date -Format yyyyMMdd-HHmmss).txt"

function Sec([string]$t) { "=" * 12 + " $t " + "=" * 12 }

Sec "D1 AUDIT - $(Get-Date -Format o)" | Out-File $out -Encoding utf8
Sec "A. LIVE STORE HASH CHAINS (mode=ro, read-only)" | Out-File $out -Append -Encoding utf8
Push-Location $RepoRoot
try {
    python scripts\verify_live_store.py 2>&1 | Out-File $out -Append -Encoding utf8
} finally { Pop-Location }

Sec "B1. OBSERVATORY TESTS (expect: 93 passed)" | Out-File $out -Append -Encoding utf8
Push-Location $RepoRoot
try { python -m pytest _ops\observatory\tests\ -q 2>&1 | Select-Object -Last 3 | Out-File $out -Append -Encoding utf8 } finally { Pop-Location }

Sec "B2. FULL WORKING-REPO SUITE (expect: 320 passed)" | Out-File $out -Append -Encoding utf8
Push-Location $RepoRoot
try { python -m pytest -o addopts= -p no:warnings -q 2>&1 | Select-Object -Last 3 | Out-File $out -Append -Encoding utf8 } finally { Pop-Location }

Sec "C. GIT INTEGRITY" | Out-File $out -Append -Encoding utf8
Push-Location $RepoRoot
try {
    git log --oneline -5 2>&1 | Out-File $out -Append -Encoding utf8
    git status --short 2>&1 | Select-Object -First 10 | Out-File $out -Append -Encoding utf8
} finally { Pop-Location }

Sec "DONE - auditor: sign this file with your own key" | Out-File $out -Append -Encoding utf8
Write-Host "Audit output written: $out"
