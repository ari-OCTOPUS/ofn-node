# Register the genome-system schedule on Windows (Task Scheduler).
# Run once, in PowerShell, as your normal user:  .\scripts\install_schedule.ps1
#
# Cadence:
#   * loop (cheap: perception + guardian + creativity) 3x/day  -> 09:00, 15:00, 21:00
#   * full (adds the Opus Doctor pass) weekly                   -> Monday 08:00
#   * backup daily                                             -> 23:30
# The loop is plan-gated: it idles automatically once plan.yaml is complete,
# so these tasks are safe to leave installed.

$ErrorActionPreference = "Stop"
$dir = (Resolve-Path "$PSScriptRoot\..").Path
$py  = (Get-Command python).Source

function New-GenomeTask($name, $arg, $sched, $extra) {
    $action  = "cmd /c cd /d `"$dir`" && `"$py`" $arg"
    schtasks /Create /TN "genome\$name" /TR $action /F $sched $extra | Out-Null
    Write-Host "  registered: genome\$name"
}

New-GenomeTask "loop-morning" "run.py loop" "/SC DAILY /ST 09:00" ""
New-GenomeTask "loop-midday"  "run.py loop" "/SC DAILY /ST 15:00" ""
New-GenomeTask "loop-evening" "run.py loop" "/SC DAILY /ST 21:00" ""
New-GenomeTask "doctor-weekly" "run.py full" "/SC WEEKLY /ST 08:00" "/D MON"
New-GenomeTask "backup-daily" "scripts\backup.py" "/SC DAILY /ST 23:30" ""

Write-Host ""
Write-Host "Done. Optional: set your API key so ideas are real, not the offline stub:"
Write-Host "  setx ANTHROPIC_API_KEY sk-ant-..."
Write-Host "Remove later with:  schtasks /Delete /TN genome\<name> /F"
