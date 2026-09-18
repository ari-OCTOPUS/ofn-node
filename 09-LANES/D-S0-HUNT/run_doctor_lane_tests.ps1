# D-S0-HUNT — run only the five test_doctor_lane_*.py files. No suite, no _ops/tests.
$ErrorActionPreference = "Stop"
$OfnRoot = "F:\ofn-node"
$LaneRoot = "F:\backup\09-LANES\D-S0-HUNT"
$Receipts = Join-Path $LaneRoot "receipts"
$Python = "C:\Program Files\Python313\python.exe"
$Utc = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmZ")
$Log = Join-Path $Receipts "pytest-doctor-lane-$Utc.txt"

$Files = @(
    "tests\test_doctor_lane_cli.py",
    "tests\test_doctor_lane_round.py",
    "tests\test_doctor_lane_backlog.py",
    "tests\test_doctor_lane_destiny.py",
    "tests\test_doctor_lane_contract_map.py"
)

if (-not (Test-Path $Python)) { throw "python missing: $Python" }
if (-not (Test-Path $OfnRoot)) { throw "ofn-node missing: $OfnRoot" }
New-Item -ItemType Directory -Force -Path $Receipts | Out-Null

foreach ($rel in $Files) {
    $full = Join-Path $OfnRoot $rel
    if (-not (Test-Path $full)) { throw "test file missing: $full" }
}

$abs = $Files | ForEach-Object { Join-Path $OfnRoot $_ }
$utf8 = New-Object System.Text.UTF8Encoding $false
$header = @(
    "lane: D-S0-HUNT"
    "cwd: $OfnRoot"
    "python: $Python"
    "utc: $Utc"
    "files:"
) + ($abs | ForEach-Object { "  $_" }) + @("---- pytest ----")

Set-Location $OfnRoot
$lines = & $Python -m pytest @abs -v --tb=short 2>&1 | ForEach-Object { $_.ToString() }
$code = $LASTEXITCODE
$body = @($header + $lines + "" + "---- exit_code=$code ----") -join "`n"
[System.IO.File]::WriteAllText($Log, $body, $utf8)
Write-Host ($lines -join "`n")
Write-Host "LOG=$Log"
Write-Host "EXIT=$code"
exit $code
