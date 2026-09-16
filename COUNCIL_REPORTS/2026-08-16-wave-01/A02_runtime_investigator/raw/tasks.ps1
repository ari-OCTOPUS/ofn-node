Get-ScheduledTask | Where-Object { $_.TaskName -match 'OCTOPUS|organism|cortex|watchdog|telegram|tg-|live|miniapp|cloudflare|board|octo' } | ForEach-Object {
  $info = $_ | Get-ScheduledTaskInfo -ErrorAction SilentlyContinue
  $act = ($_.Actions | ForEach-Object { ($_.Execute + ' ' + $_.Arguments) }) -join ' ; '
  "TASK: $($_.TaskName) | PATH: $($_.TaskPath) | STATE: $($_.State) | LASTRUN: $($info.LastRunTime) | NEXTRUN: $($info.NextRunTime)"
  "  ACTION: $act"
}
