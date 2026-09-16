# run-miniapp-tunnel.ps1 -- cloudflared quick tunnel for the miniapp gateway (127.0.0.1:8774).
# PLAN-T4 + owner GO 2026-07-31. Deploy-time script: started by the orchestrator, NEVER by tests.
# PowerShell 5.1 safe: no && chains, no ternary, ASCII-only output.
# Behavior:
#   1) starts: cloudflared tunnel --url http://127.0.0.1:<port>
#   2) parses the https://*.trycloudflare.com URL from cloudflared stderr
#   3) writes {"url","started","pid"} to _ops\state\telegram\miniapp-url.json
#   4) waits; stops politely (kills cloudflared) when _ops\STOP-MINIAPP appears
# The URL file is the ONLY handoff to the center (web_app button uses it if fresh < 24h).
# No secrets touched: cloudflared quick tunnel needs no account, no credential file.

$ErrorActionPreference = "Stop"

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path      # _ops\telegram_center
$OpsDir = Split-Path -Parent $Here                           # _ops

$Port = $env:OCTOPUS_MINIAPP_PORT
if (-not $Port) { $Port = "8774" }

$StopFile = Join-Path $OpsDir "STOP-MINIAPP"
$StateDir = Join-Path $OpsDir "state\telegram"
if (-not (Test-Path $StateDir)) {
    New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
}
$UrlFile = Join-Path $StateDir "miniapp-url.json"
$LogFile = Join-Path $StateDir "miniapp-tunnel-stderr.log"

if (Test-Path $StopFile) {
    Write-Output "STOP-MINIAPP present - refusing to start tunnel."
    exit 1
}

$cf = Get-Command cloudflared -ErrorAction SilentlyContinue
$CfExe = $null
if ($null -ne $cf) { $CfExe = $cf.Source }
if ($null -eq $CfExe) {
    # winget install location (2026-07-31) - PATH refresh only reaches NEW shells,
    # so a supervisor-launched run needs the absolute fallback.
    $Known = @("C:\Program Files (x86)\cloudflared\cloudflared.exe",
               "C:\Program Files\cloudflared\cloudflared.exe")
    foreach ($k in $Known) { if (Test-Path $k) { $CfExe = $k; break } }
}
if ($null -eq $CfExe) {
    Write-Output "cloudflared not found (PATH + known dirs) - aborting (no tunnel started)."
    exit 1
}

if (Test-Path $LogFile) {
    try { Remove-Item -Force -Confirm:$false $LogFile -ErrorAction Stop } catch {}
}

$proc = Start-Process -FilePath $CfExe `
    -ArgumentList @("tunnel", "--url", ("http://127.0.0.1:" + $Port)) `
    -RedirectStandardError $LogFile -PassThru -WindowStyle Hidden

# cloudflared prints the assigned quick-tunnel URL on stderr within ~10s.
$TunnelUrl = $null
for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Seconds 1
    if ($proc.HasExited) { break }
    if (Test-Path $LogFile) {
        $txt = ""
        try { $txt = Get-Content $LogFile -Raw -ErrorAction Stop } catch { $txt = "" }
        if ($txt -match "https://[a-z0-9-]+\.trycloudflare\.com") {
            $TunnelUrl = $Matches[0]
            break
        }
    }
}

if ($null -eq $TunnelUrl) {
    Write-Output "no trycloudflare URL parsed within 60s - killing tunnel process."
    try { Stop-Process -Id $proc.Id -Force -Confirm:$false -ErrorAction Stop } catch {}
    exit 1
}

$Started = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$JsonBody = '{"url":"' + $TunnelUrl + '","started":"' + $Started + '","pid":' + $proc.Id + '}'
# BOM-less UTF-8 (blocker B1, 2026-07-31): PS 5.1 "Set-Content -Encoding utf8"
# writes a BOM, python json.loads chokes on it, and the centre silently dropped
# the dashboard button while the tunnel was perfectly alive.
[System.IO.File]::WriteAllText($UrlFile, $JsonBody, (New-Object System.Text.UTF8Encoding($false)))
Write-Output ("tunnel up: " + $TunnelUrl)
Write-Output ("url file:  " + $UrlFile)

# polite wait loop: STOP-MINIAPP kills the tunnel; cloudflared death ends the loop.
while ($true) {
    Start-Sleep -Seconds 5
    if (Test-Path $StopFile) {
        Write-Output "STOP-MINIAPP present - stopping tunnel."
        break
    }
    if ($proc.HasExited) {
        Write-Output "cloudflared exited on its own."
        break
    }
    # Freshness keepalive (review 2026-07-31): the centre only offers the web_app
    # button while the url file is younger than 24h. A healthy long-lived tunnel
    # must not age out, so touch the file every iteration while alive.
    try { (Get-Item $UrlFile -ErrorAction Stop).LastWriteTime = Get-Date } catch {}
}

try { Stop-Process -Id $proc.Id -Force -Confirm:$false -ErrorAction Stop } catch {}

# dead URL must not look alive: mark the handoff file as stopped.
$Stopped = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$JsonDead = '{"url":"","started":"' + $Started + '","stopped":"' + $Stopped + '","pid":0}'
try {
    [System.IO.File]::WriteAllText($UrlFile, $JsonDead, (New-Object System.Text.UTF8Encoding($false)))
} catch {}
Write-Output "tunnel stopped."
exit 0
