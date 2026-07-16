# organism-watchdog.ps1 - runner twin of _ops/watchdog.py (LifeDoctrine par.4)
# Revive is an OWNER tool, not self-preservation: watchdog.py decides (STOP flags
# always win; first-birth stays owner-launched), this script only executes.
#
# Owner registers ONCE (elevated not required):
#   schtasks /Create /TN "OCTOPUS-Watchdog" /SC MINUTE /MO 5 /TR "powershell -NoProfile -ExecutionPolicy Bypass -File F:\backup\_ops\organism-watchdog.ps1"
# Boot-at-logon twin (organism itself):
#   schtasks /Create /TN "OCTOPUS-Organism" /SC ONLOGON /TR "F:\backup\_ops\RUN-ORGANISM.bat"
# Remove: schtasks /Delete /TN "OCTOPUS-Watchdog" /F
#
# --- SPLIT-BRAIN NOTE (audit R-19) --------------------------------------------
# TWIN: "04 - Architect System/scripts/organism-watchdog.ps1" is a divergent copy
# of the same name. There must be ONE authority. Current runtime authority is THIS
# _ops/ file: it is the one the owner registers (schtasks OCTOPUS-Watchdog, above)
# and the one the test-suite guards (_ops/tests/test_heart_work.py::t_j). It
# supervises ONLY the organism (port 8771) by delegating to watchdog.py; it does
# NOT watch the cortex (port 8772). The scripts/ twin is where cortex(8772)
# supervision is being built. Collapsing the two into one dual-port watchdog is
# OWNER-GATED: it needs the schtasks task re-pointed, test_heart_work.py::t_j
# updated, and cortex (brain) auto-revival accepted -- so it is deliberately NOT
# done here. Do NOT register a second scheduled task for the twin: that duplicate
# registration is the split-brain this note exists to prevent.
# ------------------------------------------------------------------------------

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
