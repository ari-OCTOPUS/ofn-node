# waits for the hourly's gitwrite lock to clear (up to 45 min), then runs the daily backup
$deadline = (Get-Date).AddMinutes(45)
while ((Get-Date) -lt $deadline) {
    $lock = "F:\backup\_ops\backup\gitwrite.lock"
    $packAlive = Get-CimInstance Win32_Process -Filter "Name='git.exe'" |
        Where-Object { $_.CommandLine -match 'pack-objects|push' }
    if (-not (Test-Path $lock) -and -not $packAlive) { break }
    Start-Sleep -Seconds 30
}
Write-Output ("lock cleared at " + (Get-Date -Format HH:mm:ss) + " - starting backup")
& "F:\backup\04 - Architect System\scripts\germline-backup.ps1"
Write-Output ("backup rc=" + $LASTEXITCODE)
exit $LASTEXITCODE
