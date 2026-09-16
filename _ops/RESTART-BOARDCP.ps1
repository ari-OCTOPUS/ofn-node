# RESTART-BOARDCP.ps1 - dedicated TLS listener for the board (board_cp/server.py)
# Same pattern as RESTART-PROCESS.ps1 gateway block: kill -> env -> launch -> port check.
# Secret (Bearer) comes from _ops/OCTOPUS.env and is never printed.
# NOTE: keep this file ASCII-only (Windows PowerShell 5.1 reads no-BOM files as ANSI).
param(
    [int]$Port = 8801
)
$ErrorActionPreference = "Stop"
$ops = Split-Path -Parent $MyInvocation.MyCommand.Path

function Get-BoardCp {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
        Where-Object { $_.CommandLine -match 'board_cp[\\/]server\.py' }
}

$before = Get-BoardCp
if ($before) {
    Write-Host ("BEFORE : pid={0}" -f $before.ProcessId)
    Stop-Process -Id $before.ProcessId -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
} else {
    Write-Host "BEFORE : not running"
}

# env - same parsing as the gateway block (OCTOPUS.env + OCTOPUS-flags.cmd)
$envFile = Join-Path $ops "OCTOPUS.env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
            [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], "Process")
        }
    }
}
$flagsFile = Join-Path $ops "OCTOPUS-flags.cmd"
if (Test-Path $flagsFile) {
    foreach ($ln in (Get-Content $flagsFile -Encoding utf8)) {
        if ($ln -match '^\s*set\s+([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
            [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2].Trim(), "Process")
        }
    }
}

$tls = Join-Path $ops "state\board_cp\tls"
if (-not ((Test-Path (Join-Path $tls "cert.pem")) -and (Test-Path (Join-Path $tls "key.pem")))) {
    Write-Host "ERROR: TLS cert missing at $tls - fail-closed. Generate first."
    exit 2
}

Write-Host "Launching..."
Start-Process -FilePath "python" `
    -ArgumentList @("-X","utf8",(Join-Path $ops "board_cp\server.py")) `
    -WorkingDirectory $ops -WindowStyle Hidden | Out-Null

$deadline = (Get-Date).AddSeconds(30)
$ok = $false
while ((Get-Date) -lt $deadline) {
    $p = Get-BoardCp
    if ($p) {
        $t = Test-NetConnection -ComputerName 127.0.0.1 -Port $Port -WarningAction SilentlyContinue
        if ($t.TcpTestSucceeded) {
            Write-Host ("AFTER  : pid={0} port={1} LISTENING (TLS)" -f $p.ProcessId, $Port)
            $ok = $true
            break
        }
    }
    Start-Sleep -Seconds 2
}
if (-not $ok) {
    Write-Host "WARNING: board-cp not listening yet."
    exit 4
}
Write-Host "OK: board-cp restarted with fresh code."
