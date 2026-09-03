<#
rotate_all.ps1 - one-command secret rotation checklist (D-29 Q-08, owner-ruled).

What this is: the tool that makes rotation a single owner session instead of a
scattered afternoon. It reads a NAMES-ONLY manifest, verifies each secret NAME
is actually present where the manifest says (without ever reading or printing
a value), prints the plan, and - only with -Apply plus the manifest's confirm
word - walks the owner through marking each secret rotated, writing a receipt.

What this deliberately never does:
  * print, copy, back up, or transmit any secret VALUE
  * rotate anything itself - every real rotation happens in the provider's
    own console by the owner; this tool verifies presence and records destiny
  * touch the outbound WAL, flags, services, or databases

Usage:
  powershell -NoProfile -ExecutionPolicy Bypass -File deploy\rotate_all.ps1 -Manifest deploy\rotate-manifest.json
  powershell ... -File deploy\rotate_all.ps1 -Apply -ConfirmWord ROTATE ...

Exit codes: 0 = plan/apply completed; 2 = manifest missing/broken;
            3 = -Apply without the correct -ConfirmWord.

ASCII-only on purpose: Windows PowerShell 5.1 reads BOM-less files as ANSI.
#>

param(
    [string]$Manifest = "deploy/rotate-manifest.json",
    [switch]$Apply,
    [string]$ConfirmWord = "",
    [string]$ReceiptDir = "state/rotation-receipts"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Manifest)) {
    Write-Output "manifest missing: $Manifest"
    exit 2
}
try {
    $parsed = Get-Content -LiteralPath $Manifest -Raw -Encoding UTF8 | ConvertFrom-Json
} catch {
    Write-Output "manifest not valid json"
    exit 2
}
if (-not $parsed.secrets) {
    Write-Output "manifest has no secrets array"
    exit 2
}

if ($Apply -and $ConfirmWord -ne $parsed.confirm_word) {
    Write-Output "apply refused: -ConfirmWord must match the manifest confirm_word"
    exit 3
}

function Find-NameInFile([string]$Path, [string]$Name) {
    # returns one of: file-absent, name-present, name-absent
    if ($Path -like "~*") { $Path = Join-Path $env:USERPROFILE $Path.Substring(1) }
    if (-not (Test-Path -LiteralPath $Path)) { return "file-absent" }
    try {
        $text = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 -ErrorAction Stop
    } catch {
        return "file-absent"
    }
    # NAME only - never capture or echo what follows the equals sign
    if ($text -match ("(?m)^\s*(?:export\s+)?" + [regex]::Escape($Name) + "\s*=")) {
        return "name-present"
    }
    return "name-absent"
}

$plan = @()
foreach ($secret in $parsed.secrets) {
    $states = @()
    foreach ($location in $secret.locations) {
        $states += (Find-NameInFile -Path $location -Name $secret.name)
    }
    $located = $true
    foreach ($state in $states) {
        if ($state -ne "name-present") { $located = $false }
    }
    $plan += [pscustomobject]@{
        name     = $secret.name
        service  = $secret.service
        location = ($secret.locations -join ",")
        state    = ($states -join ",")
        verdict  = $(if ($located) { "located" } else { "location-unverified" })
        ref      = $secret.rotation_ref
    }
}

Write-Output ("rotate_all dry-run - {0} secrets, values never read" -f $plan.Count)
$plan | Format-Table name, verdict, state, service -AutoSize | Out-String | Write-Output

if (-not $Apply) {
    Write-Output "dry-run only. apply with: -Apply -ConfirmWord (the manifest confirm_word)"
    exit 0
}

$receipts = @()
foreach ($item in $plan) {
    Write-Output ""
    Write-Output ("SECRET: {0} ({1})" -f $item.name, $item.service)
    Write-Output ("  how:  {0}" -f $item.ref)
    $answer = Read-Host "  rotated in the provider console and replaced everywhere? (y/N)"
    $receipts += [pscustomobject]@{
        name        = $item.name
        service     = $item.service
        verdict     = $item.verdict
        destiny     = $(if ($answer -eq "y" -or $answer -eq "Y") { "rotated" } else { "skipped" })
        rotated_at  = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        by          = $env:USERNAME
        host        = $env:COMPUTERNAME
    }
}

New-Item -ItemType Directory -Force -Path $ReceiptDir | Out-Null
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$receiptPath = Join-Path $ReceiptDir ("ROTATION-RECEIPT-" + $stamp + ".jsonl")
foreach ($receipt in $receipts) {
    ($receipt | ConvertTo-Json -Compress) | Add-Content -LiteralPath $receiptPath -Encoding UTF8
}
Write-Output ("receipt written: {0}" -f $receiptPath)
$rotatedCount = @($receipts | Where-Object { $_.destiny -eq "rotated" }).Count
$skippedCount = @($receipts | Where-Object { $_.destiny -ne "rotated" }).Count
Write-Output ("rotated: {0}  skipped: {1}" -f $rotatedCount, $skippedCount)
exit 0
