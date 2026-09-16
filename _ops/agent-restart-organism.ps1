# agent-restart-organism.ps1 -- one-shot: clean STOP + wait + clean marker + relaunch.
# Agent-written marker only; aborts if an OWNER STOP-ORGANISM already exists (never touch it).
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
    Set-Content -Path $stopF -Value ("agent-restart " + (Get-Date -Format s)) -Encoding utf8
    $deadline = (Get-Date).AddSeconds(300)
    while ((Get-Date) -lt $deadline) {
        $still = Get-Org
        if (-not $still -or $still.ProcessId -ne $before.ProcessId) { break }
        Start-Sleep -Seconds 10
    }
} finally {
    if (Test-Path $stopF) { Remove-Item $stopF -Force -ErrorAction SilentlyContinue; Write-Host "agent stop marker cleaned" }
}
$after = Get-Org
if ($after -and $after.ProcessId -eq $before.ProcessId) { Write-Host "DID NOT EXIT in 300s"; exit 3 }
if (-not $after) {
    Write-Host "exited clean - relaunching"
    Start-Process -FilePath $bat -WindowStyle Hidden
    Start-Sleep -Seconds 20
    $after = Get-Org
}
if ($after) { Write-Host ("after pid=" + $after.ProcessId + " started " + $after.CreationDate.ToString("HH:mm:ss")); exit 0 }
Write-Host "NOT RUNNING after relaunch"; exit 4
