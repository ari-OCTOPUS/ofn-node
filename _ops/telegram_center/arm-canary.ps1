# arm-canary.ps1 — controlled Telegram Center restart for the bounded owner canary.
# No secrets are read, printed, or written. The launcher (RUN-TG-CENTER.bat) keeps
# the original environment; OCTOPUS-flags.cmd carries the non-secret durable flag.
$ErrorActionPreference = "Stop"

$before = Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -match "telegram_center[\\/]center\.py" }
$beforePid = ($before | Select-Object -First 1).ProcessId
if (-not $beforePid) { Write-Output "NO_CENTER_RUNNING"; exit 2 }

Write-Output ("BEFORE_PID=" + $beforePid)

# Snapshot state before the restart (offsets/queues are read by the caller from
# state files; here we only record liveness markers).
$lock = Get-NetTCPConnection -LocalPort 8776 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -First 1
Write-Output ("BEFORE_LOCK_PID=" + ($lock.OwningProcess))

Stop-Process -Id $beforePid -Force -ErrorAction SilentlyContinue

# The launcher loop relaunches center within ~10s. Bounded wait (max 90s).
$newPid = $null
for ($i = 0; $i -lt 18; $i++) {
    Start-Sleep -Seconds 5
    $cur = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match "telegram_center[\\/]center\.py" } |
        Select-Object -First 1
    if ($cur -and $cur.ProcessId -ne $beforePid) { $newPid = $cur.ProcessId; break }
}
if (-not $newPid) { Write-Output "RELAUNCH_TIMEOUT"; exit 3 }

Write-Output ("AFTER_PID=" + $newPid)

# Wait for the singleton lock port to be owned by the new process (bounded).
$owned = $false
for ($i = 0; $i -lt 12; $i++) {
    Start-Sleep -Seconds 5
    $lock2 = Get-NetTCPConnection -LocalPort 8776 -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($lock2 -and $lock2.OwningProcess -eq $newPid) { $owned = $true; break }
}
Write-Output ("LOCK_OWNED_BY_NEW=" + $owned)
if (-not $owned) { exit 4 }
Write-Output "RESTART_OK"
