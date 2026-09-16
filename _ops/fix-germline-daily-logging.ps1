# fix-germline-daily-logging.ps1 -- redirect germline-daily task output to a log file
# (was: hidden window, output lost; nightly rc=1 undiagnosable). Receipt: task action swap.
$t = Get-ScheduledTask -TaskName "germline-daily"
Write-Host ("OLD: " + $t.Actions[0].Execute + " " + $t.Actions[0].Arguments)
$cmd = "& 'F:\backup\04 - Architect System\scripts\germline-backup.ps1' *> 'E:\germline\daily-last-run.log'"
$a = New-ScheduledTaskAction -Execute "powershell.exe" -Argument ("-NoProfile -WindowStyle Hidden -Command `"" + $cmd + "`"")
Set-ScheduledTask -TaskName "germline-daily" -Action $a | Out-Null
$c = (Get-ScheduledTask -TaskName "germline-daily").Actions[0]
Write-Host ("NEW ARGS: " + $c.Arguments)
