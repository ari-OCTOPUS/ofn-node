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

# 2026-08-03: this used to filter "Name like '%'" and match CommandLine alone, which
# also matches the SHELL that invoked this script - its own command line contains the
# pattern text. Consequence, observed live: the gateway was killed, this watchdog was
# invoked one second later, matched the calling shell, logged "OK - gateway up" and
# never revived it. The tunnel branch is worse: it calls Stop-Process on every match,
# so a self-match could kill the invoking shell instead of the tunnel. Same class of
# bug RESTART-PROCESS.ps1 documents ("that false positive made a probe report six
# supervisor loops when there were two").
#
# Two independent guards, because either alone is insufficient:
#   1. $imageNames - filter on the executable first (a python gateway is python.exe,
#      never powershell.exe). Does not help when the target IS a powershell script.
#   2. $SelfChain  - exclude this process and its whole ancestor chain, which is what
#      catches the powershell-matching-powershell case.
$script:SelfChain = @()
try {
    $walk = Get-CimInstance Win32_Process -Filter "ProcessId=$PID" -ErrorAction SilentlyContinue
    $hops = 0
    while ($walk -and $hops -lt 12) {
        $script:SelfChain += [int]$walk.ProcessId
        if (-not $walk.ParentProcessId) { break }
        $walk = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $walk.ParentProcessId) -ErrorAction SilentlyContinue
        $hops++
    }
} catch { $script:SelfChain = @([int]$PID) }

function Get-Procs($pattern, [string[]]$imageNames) {
    $procs = if ($imageNames -and $imageNames.Count -gt 0) {
        $clauses = ($imageNames | ForEach-Object { "Name='$_'" }) -join " OR "
        Get-CimInstance Win32_Process -Filter $clauses -ErrorAction SilentlyContinue
    } else {
        Get-CimInstance Win32_Process -ErrorAction SilentlyContinue
    }
    $procs | Where-Object {
        $_.CommandLine -and $_.CommandLine -match $pattern -and
        ($script:SelfChain -notcontains [int]$_.ProcessId)
    }
}

if (Test-Path $StopFile) {
    Log "STOP-MINIAPP present - stopping gateway+tunnel, no revive."
    foreach ($p in @(Get-Procs "miniapp_gateway\.py" @("python.exe","pythonw.exe"))) {
        try { Stop-Process -Id $p.ProcessId -Force -Confirm:$false -ErrorAction Stop } catch {}
    }
    foreach ($p in @(Get-Procs "trycloudflare|cloudflared.*127\.0\.0\.1:$Port" @("cloudflared.exe"))) {
        try { Stop-Process -Id $p.ProcessId -Force -Confirm:$false -ErrorAction Stop } catch {}
    }
    exit 0
}

# --- 1) gateway ------------------------------------------------------------
$gw = @(Get-Procs "miniapp_gateway\.py" @("python.exe","pythonw.exe"))
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
    # 2026-08-03 (owner decision, Slice 3 security review): this used to
    # unconditionally overwrite OCTOPUS_TG_MINIAPP with "1" AFTER loading
    # OCTOPUS.env above -- so a "0" placed there to turn the gateway off was
    # silently discarded on every watchdog tick (every 10 min), making the
    # flag lie about what actually controlled the process. Only default to
    # "1" when OCTOPUS.env left it unset; an explicit "0" now sticks.
    # STOP-MINIAPP remains the hard, unconditional kill switch (checked above).
    if (-not $env:OCTOPUS_TG_MINIAPP) {
        $env:OCTOPUS_TG_MINIAPP = "1"
    }
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
$tunnelAlive = @(Get-Procs "cloudflared" @("cloudflared.exe")).Count -gt 0
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
    # powershell matching powershell: the image filter cannot separate the tunnel
    # script from the shell running this watchdog, so $SelfChain is the load-bearing
    # guard here - without it this Stop-Process kills the caller.
    foreach ($p in @(Get-Procs "run-miniapp-tunnel(-named)?\.ps1" @("powershell.exe","pwsh.exe"))) {
        try { Stop-Process -Id $p.ProcessId -Force -Confirm:$false -ErrorAction Stop } catch {}
    }
    # 2026-08-03/04: prefer the NAMED tunnel. Telegram requires a registered
    # origin since 2026-07-20, and the quick tunnel mints a NEW random hostname
    # on every relaunch -- so this very "self-heal" was the thing breaking the
    # Mini App, silently, while every probe here still reported green (they all
    # check reachability, none checks registration).
    # The named script exits rc=0 without touching the URL file when it is not
    # configured yet, so this stays safe before the owner has run
    # `cloudflared tunnel login` / `tunnel create` / `tunnel route dns`.
    $named = Join-Path $Ops "telegram_center\run-miniapp-tunnel-named.ps1"
    $quick = Join-Path $Ops "telegram_center\run-miniapp-tunnel.ps1"
    $cfDir = Join-Path $env:USERPROFILE ".cloudflared"
    $namedReady = $env:OCTOPUS_MINIAPP_HOSTNAME -and (Test-Path (Join-Path $cfDir "cert.pem")) `
                  -and (@(Get-ChildItem -Path $cfDir -Filter "*.json" -ErrorAction SilentlyContinue).Count -gt 0)
    $script = if ($namedReady -and (Test-Path $named)) { $named } else { $quick }
    if (-not $namedReady) {
        Log "named tunnel not configured (need OCTOPUS_MINIAPP_HOSTNAME + cert.pem + credentials) - using quick tunnel; Telegram may refuse this origin."
    }
    try {
        Start-Process -FilePath "powershell" `
            -ArgumentList @("-ExecutionPolicy","Bypass","-File", $script) `
            -WindowStyle Hidden | Out-Null
        Log ("tunnel script relaunched: " + (Split-Path $script -Leaf))
    } catch { Log ("tunnel relaunch FAILED: " + $_.Exception.Message) }
} else {
    Log "OK - gateway up, tunnel up, url fresh."
}
exit 0
