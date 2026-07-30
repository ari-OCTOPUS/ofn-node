# live-watchdog.ps1 — keep the live cockpit (port 8773) always-on.
#
# Owner chose "always-on (supervisor)" for the live cockpit (truth-map P9, 2026-07-17).
# Register ONCE (owner action — system setting):
#   schtasks /Create /TN "OCTOPUS-Live-Watchdog" /SC MINUTE /MO 5 ^
#     /TR "powershell -NoProfile -ExecutionPolicy Bypass -File F:\backup\_ops\live-watchdog.ps1" /F
# Off switch (stop auto-revival without deleting the task):
#   create the file  F:\backup\_ops\STOP-LIVE   (watchdog then leaves 8773 down)
# Remove the task:
#   schtasks /Delete /TN "OCTOPUS-Live-Watchdog" /F
#
# SCOPE / SPLIT-BRAIN SAFETY: this supervises ONLY the live cockpit (8773) via
# run-live-headless.bat. It is a SEPARATE concern from organism-watchdog (8771),
# so it does NOT touch the organism-watchdog split-brain (the registered
# "organism-watchdog" task points at the 04-Architect-System\scripts twin). Do NOT
# fold cockpit revival into the organism watchdog — keep the two tasks independent.

$ErrorActionPreference = 'SilentlyContinue'
$ops = 'F:\backup\_ops'
$logDir = Join-Path $ops 'state'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$log = Join-Path $logDir 'live-watchdog-log.txt'

# 0) D-G (2026-07-20): global panic (HALT-ALL) or architect STOP overrides EVERY supervisor -> never
#    revive under panic. (Previously this watchdog saw only STOP-LIVE and ignored the global kill.)
if ((Test-Path (Join-Path $ops 'HALT-ALL')) -or (Test-Path (Join-Path (Split-Path $ops -Parent) 'STOP')) -or (Test-Path (Join-Path (Split-Path $ops -Parent) '04 - Architect System\STOP'))) {
    Add-Content -Path $log -Value "$(Get-Date -Format s) global HALT-ALL/architect-STOP present - not reviving 8773"
    exit 0
}
# 1) owner off-switch: STOP-LIVE means "leave the cockpit down on purpose"
if (Test-Path (Join-Path $ops 'STOP-LIVE')) {
    Add-Content -Path $log -Value "$(Get-Date -Format s) STOP-LIVE present - not reviving 8773"
    exit 0
}

# 2) already up? nothing to do
if (Get-NetTCPConnection -LocalPort 8773 -State Listen -ErrorAction SilentlyContinue) {
    exit 0
}

# 3) down -> revive headless (no browser spam)
Add-Content -Path $log -Value "$(Get-Date -Format s) 8773 down - launching run-live-headless.bat"
Start-Process -FilePath (Join-Path $ops 'run-live-headless.bat') -WindowStyle Hidden
# C-watchdog (2026-07-30): tell the owner. Until now a die/revive/die cycle on the
# cockpit lived only in live-watchdog-log.txt. AFTER the launch + fail-soft on purpose.
# "incident" is LOAD-BEARING (measured 2026-07-30): event_bridge.py pushes ONLY
# alert lines matching _CRITICAL_KW - without it the alert is file-only and the
# owner never sees it. And no varying numbers: opslib.alert dedups on the text
# hash, so a changing number defeats the 6h window + escalation marks.
try { & python -X utf8 (Join-Path $ops "watchdog.py") --alert "WATCHDOG REVIVE incident (live cockpit :8773) - port dead - relaunched run-live-headless.bat" 2>$null | Out-Null } catch {}
