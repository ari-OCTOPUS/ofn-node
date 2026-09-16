# restart-organism-patient.ps1 -- FAULT-LLMLEARN-20260908 lane variant:
# same semantics as _ops/agent-restart-organism.ps1 but 900s grace (tick cycles can
# exceed 300s; STOP is checked once per loop iteration at organism.py:570).
# Agent marker only; aborts if an OWNER STOP-ORGANISM already exists (never touch it).
$ErrorActionPreference = "Continue"
$ops = "F:\backup\_ops"
$stopF = Join-Path $ops "STOP-ORGANISM"
$bat = Join-Path $ops "RUN-ORGANISM.bat"
function Get-Org {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
        Where-Object { $_.CommandLine -match 'organism\.py' } | Select-Object -First 1
}
if (Test-Path $stopF) { Write-Host "OWNER STOP PRESENT - aborting."; exit 5 }
$before = Get-Org
if (-not $before) { Write-Host "not running - fresh launch"; Start-Process -FilePath $bat -WindowStyle Hidden; exit 0 }
Write-Host ("before pid=" + $before.ProcessId)
try {
    Set-Content -Path $stopF -Value ("agent-restart-patient " + (Get-Date -Format s)) -Encoding utf8
    $deadline = (Get-Date).AddSeconds(900)
    while ((Get-Date) -lt $deadline) {
        $still = Get-Org
        if (-not $still -or $still.ProcessId -ne $before.ProcessId) { break }
        Start-Sleep -Seconds 15
    }
} finally {
    if (Test-Path $stopF) { Remove-Item $stopF -Force -ErrorAction SilentlyContinue; Write-Host "agent stop marker cleaned" }
}
$after = Get-Org
if ($after -and $after.ProcessId -eq $before.ProcessId) { Write-Host "DID NOT EXIT in 900s"; exit 3 }
if (-not $after) {
    Write-Host "exited clean - relaunching"
    Start-Process -FilePath $bat -WindowStyle Hidden
    Start-Sleep -Seconds 25
    $after = Get-Org
}
if ($after) { Write-Host ("after pid=" + $after.ProcessId + " started " + $after.CreationDate.ToString("HH:mm:ss")); exit 0 }
Write-Host "NOT RUNNING after relaunch"; exit 4
