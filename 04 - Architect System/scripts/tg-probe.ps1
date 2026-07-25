# tg-probe.ps1 - READ ONLY Telegram liveness probe.
# Reads tokens from F:\backup\.env, NEVER prints them, and calls only safe read-only
# endpoints (getMe / getWebhookInfo / getChat). Does NOT call getUpdates, so it cannot
# steal updates from a live poller.

$ErrorActionPreference = "SilentlyContinue"
$envPath = "F:\backup\.env"
if (-not (Test-Path $envPath)) { Write-Host "no .env at $envPath"; exit 1 }

$map = @{}
foreach ($line in (Get-Content $envPath)) {
    if ($line -match '^\s*([A-Za-z0-9_]+)\s*=\s*(.+?)\s*$') {
        $map[$Matches[1]] = $Matches[2].Trim('"').Trim("'")
    }
}

function Probe([string]$label, [string]$varName, [string]$chatId) {
    Write-Host ""
    Write-Host "=== $label  (env: $varName) ==="
    $tok = $map[$varName]
    if (-not $tok) { Write-Host "  token NOT SET in .env"; return }
    Write-Host ("  token present: yes  (length {0}, id prefix {1})" -f $tok.Length, $tok.Split(':')[0])

    $me = Invoke-RestMethod -Uri "https://api.telegram.org/bot$tok/getMe" -TimeoutSec 20
    if ($me.ok) {
        Write-Host ("  getMe          : OK  @{0}  id={1}  name='{2}'" -f $me.result.username, $me.result.id, $me.result.first_name)
        Write-Host ("  can join groups: {0}   reads all group msgs: {1}" -f $me.result.can_join_groups, $me.result.can_read_all_group_messages)
    } else {
        Write-Host "  getMe          : FAILED - token rejected by Telegram"
        return
    }

    $wh = Invoke-RestMethod -Uri "https://api.telegram.org/bot$tok/getWebhookInfo" -TimeoutSec 20
    if ($wh.ok) {
        $url = $wh.result.url
        if ([string]::IsNullOrEmpty($url)) {
            Write-Host ("  webhook        : none (long-poll mode)  pending_updates={0}" -f $wh.result.pending_update_count)
        } else {
            Write-Host ("  webhook        : SET -> {0}   pending={1}" -f $url, $wh.result.pending_update_count)
        }
        if ($wh.result.last_error_message) {
            Write-Host ("  last error     : {0}  (at {1})" -f $wh.result.last_error_message, ([datetimeoffset]::FromUnixTimeSeconds($wh.result.last_error_date)).LocalDateTime)
        }
    }

    if ($chatId) {
        $c = Invoke-RestMethod -Uri "https://api.telegram.org/bot$tok/getChat?chat_id=$chatId" -TimeoutSec 20
        if ($c.ok) {
            Write-Host ("  group          : OK  '{0}'  type={1}  forum={2}" -f $c.result.title, $c.result.type, $c.result.is_forum)
        } else {
            Write-Host ("  group          : NOT REACHABLE (bot removed from group, or wrong chat_id)")
        }
        $cm = Invoke-RestMethod -Uri "https://api.telegram.org/bot$tok/getChatMemberCount?chat_id=$chatId" -TimeoutSec 20
        if ($cm.ok) { Write-Host ("  group members  : {0}" -f $cm.result) }
    }
}

$GROUP = "-1004475788460"   # from _ops/state/telegram/center-config.json

Write-Host "TELEGRAM PROBE  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')   (read-only, no getUpdates)"
Probe "BOT #1  Octopus Unified (approval / private DM)" "TELEGRAM_BOT_TOKEN"   $GROUP
Probe "BOT #2  TG Center (group command centre)"        "TG_CENTER_BOT_TOKEN"  $GROUP

Write-Host ""
Write-Host "=== other bot tokens present in .env (existence only) ==="
foreach ($k in ($map.Keys | Sort-Object)) {
    if ($k -match 'TOKEN' -and $k -match 'TELEGRAM|TG_') {
        $v = $map[$k]
        $state = if ($v -and $v.Length -gt 20 -and $v -notmatch 'placeholder|xxx|TODO|<') { "set" } else { "empty/placeholder" }
        Write-Host ("  {0,-34} {1}" -f $k, $state)
    }
}
Write-Host ""
Write-Host "done - nothing was changed, no updates consumed."
