#!/bin/bash
# ofn-sync-watchdog — legs board (.138) germline mount + heartbeat watchdog
# Owner-approved 2026-08-17 (Sensorium agent, authorization D-series on .182;
# deploy on .138 only with owner-provided SSH access).
# What it does: if the germline CIFS mount is gone -> remount with the board's
# own credentials file; if ofn-heartbeat is inactive -> restart it. Log-only
# otherwise. It never touches code, wire content, or secrets.

LOG=/var/log/ofn-sync-watchdog.log
MOUNT_POINT=/mnt/octopus-germline
CREDS=/etc/octopus-germline.creds
SERVER=//192.168.0.191/germline

exec >>"$LOG" 2>&1
echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

if ! mount | grep -q "$MOUNT_POINT"; then
    echo "MOUNT GONE - remounting $SERVER (cache=none: git-safe over CIFS)"
    if mount -t cifs "$SERVER" "$MOUNT_POINT" -o credentials="$CREDS",vers=3.0,iocharset=utf8,cache=none,uid=ari,gid=ari,file_mode=0644,dir_mode=0755; then
        echo "REMOUNTED ok"
    else
        echo "REMOUNT FAILED (creds/server? laptop .191 reachable?)"
        exit 1
    fi
fi

if systemctl is-active --quiet ofn-heartbeat; then
    :
else
    echo "ofn-heartbeat inactive - restarting"
    systemctl restart ofn-heartbeat || echo "RESTART FAILED (see journalctl -u ofn-heartbeat)"
fi

# keep the log bounded (simple rotation, no deps)
if [ -f "$LOG" ] && [ "$(stat -c%s "$LOG")" -gt 1048576 ]; then
    tail -c 524288 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi
