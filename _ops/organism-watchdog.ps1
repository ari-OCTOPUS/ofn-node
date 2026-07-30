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
# --- !! NOT THE FILE PRODUCTION RUNS (measured 2026-07-30) --------------------
# Get-ScheduledTask output, verbatim:
#     Name   : organism-watchdog
#     State  : Ready
#     Action : powershell.exe -NoProfile -WindowStyle Hidden -File
#              "F:\backup\04 - Architect System\scripts\organism-watchdog.ps1"
# So the REGISTERED task runs the TWIN, not this file. The twin contains ZERO
# references to watchdog.py: it has its own inline logic and revives 8771/8772
# itself. Consequence, stated plainly: the stall detection in watchdog.py
# (port open but beat stale / beat counter frozen) DOES NOT RUN IN PRODUCTION for
# the organism. This file is correct but unreached. Re-pointing the task or
# editing the twin is OWNER-GATED (see the split-brain note below - a second
# registration is exactly the failure that note exists to prevent), so it is
# deliberately NOT done here.
# The only production-reachable entry point of watchdog.py today is `--alert`,
# called by the three OTHER registered tasks (OCTOPUS-Cortex-Watchdog,
# OCTOPUS-Live-Watchdog, OCTOPUS-TG-Center-Watchdog), which DO point at _ops\.
# ------------------------------------------------------------------------------
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

# C-watchdog (2026-07-30) - SILENT DEATH / SILENT REVIVAL, closed.
# Before: this leg only Add-Content'd to watchdog-log.txt, so a die/revive/die cycle was
# invisible unless the owner opened the log by hand. Now watchdog.py itself calls
# opslib.alert on EVERY revive verdict AND on a STALL (port open but beat stale), so the
# organism leg needs no alert call here - with one exception: watchdog.py returning
# nothing at all. A supervisor whose own decision path is dead was pure silence.
$decision = & python -X utf8 (Join-Path $ops "watchdog.py") 2>$null
if (-not $decision) {
    $decision = "ERROR: watchdog.py produced no output"
    # best-effort and fail-soft: if the alert path is dead too, we still log and continue.
    # The word "incident" is LOAD-BEARING, not decoration: telegram_center/event_bridge.py
    # only pushes alert lines whose text matches _CRITICAL_KW. Without a qualifying word
    # the alert is file-only and the owner never sees it. No varying numbers in the text
    # either - opslib.alert hashes the text for dedup, so a changing number defeats the
    # 6-hour window and the escalation marks.
    try { & python -X utf8 (Join-Path $ops "watchdog.py") --alert "WATCHDOG BLIND incident (organism): watchdog.py produced no output - the supervisor's own decision path is dead" 2>$null | Out-Null } catch {}
}
Add-Content -Path $log -Value "$(Get-Date -Format s) $decision"

if ("$decision" -like "REVIVE*") {
    Start-Process -FilePath (Join-Path $ops "RUN-ORGANISM.bat") -WindowStyle Hidden
    Add-Content -Path $log -Value "$(Get-Date -Format s) launched RUN-ORGANISM.bat"
}
