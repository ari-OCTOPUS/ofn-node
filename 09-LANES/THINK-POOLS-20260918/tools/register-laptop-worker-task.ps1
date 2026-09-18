# Register the nightly laptop worker task (owner decision 2026-09-18: nightly window).
# StopIfGoingOnBatteries = the decree's "power" preemption at the OS level;
# in-agent GetLastInputInfo preemption covers owner interaction; lid/sleep is
# covered by the lease net (item returns to queue, resumes next night).
$ErrorActionPreference = 'Stop'
$py = 'C:\Program Files\Python313\python.exe'
$worker = 'F:\backup\09-LANES\THINK-POOLS-20260918\tools\laptop_worker.py'
$action = New-ScheduledTaskAction -Execute $py `
    -Argument "$worker --root F:/octo-exec/LAPTOP-WORKER-20260918 --seed --until 07:00" `
    -WorkingDirectory 'F:\backup\09-LANES\THINK-POOLS-20260918\tools'
$trigger = New-ScheduledTaskTrigger -Daily -At 01:00
# Battery behavior is left at the safe defaults of this PowerShell version:
# DisallowStartIfOnBatteries=true (no start on battery) and
# StopIfGoingOnBatteries=true (AC->battery stops the task) — the decree's
# power preemption at the OS level.
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 6 -Minutes 30) `
    -StartWhenAvailable:$false -WakeToRun:$false
Register-ScheduledTask -TaskName 'OctopusLaptopWorker-Nightly' -Action $action `
    -Trigger $trigger -Settings $settings -Force `
    -Description 'OCTOPUS laptop worker: shards 3/4/5 of the 9700-test suite, hard 50% CPU (6/12 cores), lease+preemption. Nightly 01:00 local; stops on battery; owner interaction preempts; work returns to the queue.' | Out-Null
Get-ScheduledTask -TaskName 'OctopusLaptopWorker-Nightly' | Select-Object TaskName, State |
    Format-List
(Get-ScheduledTask -TaskName 'OctopusLaptopWorker-Nightly').Settings |
    Select-Object ExecutionTimeLimit, StopIfGoingOnBatteries, MultipleInstances, WakeToRun |
    Format-List
