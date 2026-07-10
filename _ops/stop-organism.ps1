# stop-organism.ps1  —  cleanly stop the running organism AND clear any leftover STOP
# flags, so it can be relaunched fresh. Only stops/cleans; never launches.
$killed = 0
# 1) end any old RUN-ORGANISM launcher windows
Get-CimInstance Win32_Process -Filter "Name='cmd.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -match 'RUN-ORGANISM' } |
  ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop; $killed++ } catch {} }
# 2) end the python process listening on 8771 (the organism itself)
$c = Get-NetTCPConnection -LocalPort 8771 -State Listen -ErrorAction SilentlyContinue
if ($c) { try { Stop-Process -Id $c.OwningProcess -Force -ErrorAction Stop; $killed++ } catch {} }
Start-Sleep -Milliseconds 900
# 3) clear leftover STOP flags that would make a fresh organism exit immediately
foreach ($f in @('F:\backup\_ops\STOP-ORGANISM','F:\backup\_ops\RESTART-REQUESTED','F:\backup\STOP')) {
  if (Test-Path $f) { try { Remove-Item $f -Force -ErrorAction Stop; Write-Host "  cleared old flag: $f" -ForegroundColor DarkGray } catch {} }
}
# 4) confirm the port is free
$still = Get-NetTCPConnection -LocalPort 8771 -State Listen -ErrorAction SilentlyContinue
Write-Host ""
if ($still) {
  Write-Host "  Still something on port 8771 - tell your assistant." -ForegroundColor Yellow
} else {
  Write-Host "  OK - old organism stopped, stop-flags cleared, port 8771 is free." -ForegroundColor Green
}
Write-Host ""
