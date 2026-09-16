# run-miniapp-tunnel-named.ps1 -- NAMED cloudflared tunnel for the miniapp gateway.
#
# WHY THIS EXISTS (2026-08-03/04):
#   run-miniapp-tunnel.ps1 starts a QUICK tunnel: `cloudflared tunnel --url ...`,
#   which mints a RANDOM *.trycloudflare.com hostname on every start. Telegram
#   has required a REGISTERED origin for Mini Apps since 2026-07-20, so a random
#   hostname cannot be registered and the app will refuse to open -- while every
#   health probe in this repo still reports green, because they all check
#   REACHABILITY and none of them checks REGISTRATION.
#   Worse: miniapp-watchdog.ps1 "heals" a stale tunnel by relaunching it, which
#   mints yet another unregistered hostname. The designed self-healing behaviour
#   was precisely the thing the new rule forbids.
#
#   This script uses a NAMED tunnel instead: one stable hostname, forever.
#
# CONTRACT (identical to the quick script, deliberately):
#   The URL file is the ONLY handoff to the centre. 14 consumers read
#   state\telegram\miniapp-url.json and none of them cares how the hostname was
#   produced -- so this is a drop-in producer. The gateway needs no change at
#   all: it never inspects Origin/Host/Referer, auth is purely initData HMAC.
#
# OWNER SETUP -- REQUIRED ONCE, CANNOT BE AUTOMATED (browser login):
#   1) cloudflared tunnel login
#        Opens a browser. Pick the zone (master-painting.com). Writes cert.pem
#        into %USERPROFILE%\.cloudflared\.
#   2) cloudflared tunnel create octopus-miniapp
#        Writes <TUNNEL-ID>.json credentials next to cert.pem. Note the ID.
#   3) cloudflared tunnel route dns octopus-miniapp app.master-painting.com
#        Creates the CNAME. Any subdomain works; keep it stable once chosen.
#   4) Then set (owner's choice of subdomain):
#        setx OCTOPUS_MINIAPP_HOSTNAME "app.master-painting.com"
#   5) BotFather: /newapp -> pick the bot -> the SAME https URL.
#      That registration is the actual Telegram-side gate. RED-tier, owner-only.
#
# Until step 1-3 exist this script exits cleanly (rc=0) with a reason, and the
# caller is expected to fall back to the quick tunnel. Nothing here overwrites a
# working quick-tunnel URL file with a broken one.
#
# ASCII-only output (schtasks console codepage). No secrets are read or echoed:
# the credentials file is referenced by path only and never opened here.

param(
    [string]$Hostname = $env:OCTOPUS_MINIAPP_HOSTNAME,
    [string]$TunnelName = "octopus-miniapp",
    [int]$Port = 0
)

$ErrorActionPreference = "Continue"
$Ops     = "F:\backup\_ops"
$UrlFile = Join-Path $Ops "state\telegram\miniapp-url.json"
$StopFile = Join-Path $Ops "STOP-MINIAPP"
if ($Port -le 0) {
    $Port = if ($env:OCTOPUS_MINIAPP_PORT) { [int]$env:OCTOPUS_MINIAPP_PORT } else { 8774 }
}

function Log($msg) { Write-Output ("{0}  {1}" -f (Get-Date -Format "HH:mm:ss"), $msg) }

if (Test-Path $StopFile) { Log "STOP-MINIAPP present - refusing to start."; exit 0 }

if (-not $Hostname) {
    Log "no OCTOPUS_MINIAPP_HOSTNAME set - named tunnel not configured. Caller should use the quick tunnel."
    exit 0
}

# cloudflared discovery: PATH first, then the two winget install locations the
# quick script already knows about (keep the two scripts in agreement).
$cf = (Get-Command cloudflared -ErrorAction SilentlyContinue).Source
if (-not $cf) {
    foreach ($p in @("C:\Program Files (x86)\cloudflared\cloudflared.exe",
                     "C:\Program Files\cloudflared\cloudflared.exe")) {
        if (Test-Path $p) { $cf = $p; break }
    }
}
if (-not $cf) { Log "cloudflared not found."; exit 0 }

# Credentials must exist BEFORE we touch the URL file. `tunnel login` is
# interactive (browser) and is deliberately never invoked from here.
$cfDir = Join-Path $env:USERPROFILE ".cloudflared"
$cert  = Join-Path $cfDir "cert.pem"
if (-not (Test-Path $cert)) {
    Log "no cert.pem in $cfDir - run 'cloudflared tunnel login' first (owner, browser)."
    exit 0
}
$creds = @(Get-ChildItem -Path $cfDir -Filter "*.json" -ErrorAction SilentlyContinue)
if ($creds.Count -eq 0) {
    Log "no tunnel credentials in $cfDir - run 'cloudflared tunnel create $TunnelName' first."
    exit 0
}

Log ("starting named tunnel '{0}' -> https://{1} (local :{2})" -f $TunnelName, $Hostname, $Port)

# A named tunnel with an inline ingress rule: no config.yml to drift out of sync
# with this script. `--no-autoupdate` so a surprise self-update cannot restart
# the process mid-session.
$args = @("tunnel", "--no-autoupdate", "run",
          "--url", ("http://127.0.0.1:" + $Port),
          $TunnelName)
$errLog = Join-Path $Ops "state\telegram\miniapp-tunnel-named-stderr.log"
$proc = Start-Process -FilePath $cf -ArgumentList $args -PassThru -WindowStyle Hidden `
        -RedirectStandardError $errLog -RedirectStandardOutput ($errLog + ".out")
if (-not $proc) { Log "failed to start cloudflared."; exit 0 }

# Unlike the quick tunnel there is nothing to scrape: the hostname is known in
# advance. Write it once the process has survived long enough to be real.
Start-Sleep -Seconds 5
if ($proc.HasExited) {
    Log ("cloudflared exited immediately (code {0}) - see {1}" -f $proc.ExitCode, $errLog)
    exit 0
}

$payload = [ordered]@{
    url     = ("https://" + $Hostname)
    started = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    pid     = $proc.Id
    kind    = "named"          # lets a reader tell a stable origin from a random one
}
# BOM-less UTF-8: center._miniapp_url reads with utf-8-sig, but miniapp_state
# reads with plain utf-8 -- writing a BOM would break that one silently.
[System.IO.File]::WriteAllText($UrlFile,
    ($payload | ConvertTo-Json -Compress),
    (New-Object System.Text.UTF8Encoding($false)))
Log ("url file written: https://{0}" -f $Hostname)

# Keepalive: the centre treats the URL file as stale after 24h, so touch it while
# the tunnel is genuinely alive. On exit, blank the url so a dead tunnel can
# never look alive (same tombstone contract as the quick script).
try {
    while (-not $proc.HasExited) {
        if (Test-Path $StopFile) { Log "STOP-MINIAPP appeared - stopping."; break }
        (Get-Item $UrlFile).LastWriteTime = Get-Date
        Start-Sleep -Seconds 5
    }
} finally {
    try { if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } } catch {}
    $dead = [ordered]@{ url = ""; started = $payload.started; stopped = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"); pid = 0; kind = "named" }
    [System.IO.File]::WriteAllText($UrlFile,
        ($dead | ConvertTo-Json -Compress),
        (New-Object System.Text.UTF8Encoding($false)))
    Log "tunnel stopped; url file blanked."
}
