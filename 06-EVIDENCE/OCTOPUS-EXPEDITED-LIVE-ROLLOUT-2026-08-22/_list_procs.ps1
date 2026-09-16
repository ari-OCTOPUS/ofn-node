
$procs = Get-CimInstance Win32_Process | Where-Object {
  $_.CommandLine -and (
    $_.CommandLine -match 'telegram_center\\center\.py' -or
    $_.CommandLine -match 'RUN-TG-CENTER' -or
    $_.CommandLine -match 'tg-poller'
  )
} | Select-Object ProcessId, Name, CommandLine
$procs | ConvertTo-Json -Depth 4 | Set-Content -Encoding utf8 'F:\backup\06-EVIDENCE\OCTOPUS-EXPEDITED-LIVE-ROLLOUT-2026-08-22\_procs.json'
