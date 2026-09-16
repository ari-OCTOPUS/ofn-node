# setup-telegram.ps1  —  one-time helper.
# Moves the Telegram creds from _ops\OCTOPUS.env into the real secrets file F:\backup\.env,
# then shows the result. Safe to re-run. No secret value is ever printed.
$src = 'F:\backup\_ops\OCTOPUS.env'
$dst = 'F:\backup\.env'
$enc = New-Object System.Text.UTF8Encoding($false)
$add = ''
if (Test-Path $src) {
  foreach ($l in [IO.File]::ReadAllLines($src)) {
    if ($l.Trim() -match '^(?i:set)\s+(TELEGRAM_[A-Z_]+)=(.*)$') { $add += "$($matches[1])=$($matches[2])`n" }
  }
}
if ($add -ne '') {
  [IO.File]::AppendAllText($dst, "`n" + $add, $enc)
  [IO.File]::WriteAllText($src, "REM moved to F:\backup\.env - no longer read`n", $enc)
  Write-Host ""
  Write-Host "  OK - Telegram token moved into F:\backup\.env" -ForegroundColor Green
} else {
  Write-Host ""
  Write-Host "  (no 'set TELEGRAM' line found in OCTOPUS.env - maybe already moved)" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "  Result below - you want 'set' next to TELEGRAM_BOT_TOKEN:" -ForegroundColor Cyan
Write-Host ""
python -X utf8 "F:\backup\_ops\budget\env_loader.py"
Write-Host ""
Write-Host "  If TELEGRAM_BOT_TOKEN shows 'set' above, STEP 1 IS DONE." -ForegroundColor Green
Write-Host ""
