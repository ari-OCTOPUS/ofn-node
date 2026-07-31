# miniapp-watchdog.ps1 -- keeps the Mini App reachable while the owner is away.
# Registered as scheduled task OCTOPUS-MiniApp-Watchdog (every 10 min, 2026-07-31).
# Watches TWO things, both required for the dashboard button to work:
#   1) the gateway process (python miniapp_gateway.py) holding 127.0.0.1:8774
#   2) the cloudflared quick tunnel + a FRESH url file (the centre only offers the
#      web_app button while state\telegram\miniapp-url.json is younger than 24h)
# Off switch (owner): create F:\backup\_ops\STOP-MINIAPP -> this script stops both
# and never revives them. ASCII-only output (schtasks console codepage).
# Never touches STOP-ORGANISM/HALT-ALL, never restarts organism/center/cortex/live.

$ErrorActionPreference = "Continue"
$Ops      = "F:\backup\_ops"
$StopFile = Join-Path $Ops "STOP-MINIAPP"
$UrlFile  = Join-Path $Ops "state\telegram\miniapp-url.json"
$LogFile  = Join-Path $Ops "state\miniapp-watchdog-log.txt"
$Port     = 8774

function Log($msg) {
    $line = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    try { Add-Content -Path $LogFile -Value $line -Encoding utf8 } catch {}
    Write-Output $line
}

function Get-Procs($pattern) {
    Get-CimInstance Win32_Process -Filter "Name like '%'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and $_.CommandLine -match $pattern }
}

if (Test-Path $StopFile) {
    Log "STOP-MINIAPP present - stopping gateway+tunnel, no revive."
    foreach ($p in @(Get-Procs "miniapp_gateway\.py")) {
        try { Stop-Process -Id $p.ProcessId -Force -Confirm:$false -ErrorAction Stop } catch {}
    }
    foreach ($p in @(Get-Procs "trycloudflare|cloudflared.*127\.0\.0\.1:$Port")) {
        try { Stop-Process -Id $p.ProcessId -Force -Confirm:$false -ErrorAction Stop } catch {}
    }
    exit 0
}

# --- 1) gateway ------------------------------------------------------------
$gw = @(Get-Procs "miniapp_gateway\.py")
if ($gw.Count -eq 0) {
    Log "gateway DOWN - relaunching."
    $envFile = Join-Path $Ops "OCTOPUS.env"
    if (Test-Path $envFile) {
        Get-Content $envFile | ForEach-Object {
            if ($_ -match '^([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
                [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], "Process")
            }
        }
    }
    $env:OCTOPUS_TG_MINIAPP = "1"
    try {
        $p = Start-Process -FilePath "python" `
             -ArgumentList @("-X","utf8", (Join-Path $Ops "telegram_center\miniapp_gateway.py")) `
             -WorkingDirectory (Join-Path $Ops "telegram_center") -WindowStyle Hidden -PassThru
        Log ("gateway relaunched pid=" + $p.Id)
    } catch { Log ("gateway relaunch FAILED: " + $_.Exception.Message) }
} else {
    if ($gw.Count -gt 1) { Log ("WARNING: " + $gw.Count + " gateway processes - expected 1") }
}

# --- 2) tunnel + url freshness --------------------------------------------
$tunnelAlive = @(Get-Procs "cloudflared").Count -gt 0
$urlFresh = $false
if (Test-Path $UrlFile) {
    try {
        $j = Get-Content $UrlFile -Raw | ConvertFrom-Json
        $ageH = ((Get-Date) - (Get-Item $UrlFile).LastWriteTime).TotalHours
        $urlFresh = ($j.url -like "https://*") -and ($ageH -lt 24)
    } catch { $urlFresh = $false }
}

if (-not $tunnelAlive -or -not $urlFresh) {
    Log ("tunnel state: alive=" + $tunnelAlive + " urlFresh=" + $urlFresh + " - restarting tunnel script.")
    foreach ($p in @(Get-Procs "run-miniapp-tunnel\.ps1")) {
        try { Stop-Process -Id $p.ProcessId -Force -Confirm:$false -ErrorAction Stop } catch {}
    }
    try {
        Start-Process -FilePath "powershell" `
            -ArgumentList @("-ExecutionPolicy","Bypass","-File", (Join-Path $Ops "telegram_center\run-miniapp-tunnel.ps1")) `
            -WindowStyle Hidden | Out-Null
        Log "tunnel script relaunched."
    } catch { Log ("tunnel relaunch FAILED: " + $_.Exception.Message) }
} else {
    Log "OK - gateway up, tunnel up, url fresh."
}
exit 0
