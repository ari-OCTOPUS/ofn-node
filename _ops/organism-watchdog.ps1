# organism-watchdog.ps1 - runner twin of _ops/watchdog.py (LifeDoctrine par.4)
# Revive is an OWNER tool, not self-preservation: watchdog.py decides (STOP flags
# always win; first-birth stays owner-launched), this script only executes.
#
# Owner registers ONCE (elevated not required):
#   schtasks /Create /TN "OCTOPUS-Watchdog" /SC MINUTE /MO 5 /TR "powershell -NoProfile -ExecutionPolicy Bypass -File F:\backup\_ops\organism-watchdog.ps1"
# Boot-at-logon twin (organism itself):
#   schtasks /Create /TN "OCTOPUS-Organism" /SC ONLOGON /TR "F:\backup\_ops\RUN-ORGANISM.bat"
# Remove: schtasks /Delete /TN "OCTOPUS-Watchdog" /F

$ops = Split-Path -Parent $MyInvocation.MyCommand.Path
$logDir = Join-Path $ops "state"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$log = Join-Path $logDir "watchdog-log.txt"

$decision = & python -X utf8 (Join-Path $ops "watchdog.py") 2>$null
if (-not $decision) { $decision = "ERROR: watchdog.py produced no output" }
Add-Content -Path $log -Value "$(Get-Date -Format s) $decision"

if ("$decision" -like "REVIVE*") {
    Start-Process -FilePath (Join-Path $ops "RUN-ORGANISM.bat") -WindowStyle Hidden
    Add-Content -Path $log -Value "$(Get-Date -Format s) launched RUN-ORGANISM.bat"
}
