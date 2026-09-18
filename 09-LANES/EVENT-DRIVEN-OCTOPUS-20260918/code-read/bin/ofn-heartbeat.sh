#!/bin/bash
# OFN heartbeat — ضربان زندهٔ برد برای اختاپوس ویندوزی
# هر ۳۰ ثانیه: نوشتن vitals محلی + status.json (برای پنل مالک)
# هر ~۱ دقیقه: fetch سبک ofn/wire (رصد پیام ویندوز + بک‌لاگ)
# هر ۵ ضربان (~۲.۵ دقیقه): چک عمومی /healthz چهار هاست پا
# هر ۲۰ ضربان (~۱۰ دقیقه): پوش شاخهٔ ofn/heartbeat روی GitHub
# کانال خواندن برای ویندوز: git fetch origin ofn/heartbeat → git show FETCH_HEAD:BOARD-HEARTBEAT.md
# status.json توسط sysmetrics (env: OFN_SYNC_STATUS_FILE) خوانده می‌شود → پنل مالک

HB_DIR="$HOME/.local/state/ofn-heartbeat"
HB_FILE="$HB_DIR/BOARD-HEARTBEAT.md"
STATUS_FILE="$HB_DIR/status.json"
REPO="$HB_DIR/repo"
REMOTE_URL="https://github.com/ari322/ofn-node.git"
REMOTE_BRANCH="ofn/heartbeat"
OFN_HOME="/home/ari/ofn"
WIRE_REPO="$HOME/.local/state/ofn-wire/repo"
BEAT=0
PUSHED_AT="never"
WIRE_LAST="(no windows message yet)"
BOARD_LAST=""
BACKLOG_OPEN=0
LEGS_JSON='{}'

mkdir -p "$HB_DIR"

if [ ! -d "$REPO/.git" ]; then
    git init -q -b ofn-heartbeat "$REPO"
    git -C "$REPO" remote add origin "$REMOTE_URL"
fi

while true; do
    BEAT=$((BEAT + 1))
    SVC_OFN=$(systemctl is-active ofn)
    SVC_HYPNO=$(systemctl is-active hypno-fugu-mini)
    SVC_CF=$(systemctl is-active cloudflared)
    SVC_BRIDGE=$(systemctl is-active octopus-bridge)
    NOW=$(date -Iseconds)

    {
        echo "# OFN Board Heartbeat — live 24h"
        echo ""
        echo "| فیلد | مقدار |"
        echo "|---|---|"
        echo "| beat | $BEAT |"
        echo "| time | $NOW |"
        echo "| host | $(hostname) · $(uname -rm) |"
        echo "| uptime | $(uptime -p | sed 's/up //') |"
        echo "| load | $(cut -d' ' -f1-3 /proc/loadavg) |"
        echo "| mem_available_mb | $(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo) |"
        echo "| disk_root_used | $(df / | awk 'NR==2{print $5}') |"
        echo "| temp_c | $(awk '{printf "%.1f", $1/1000}' /sys/class/thermal/thermal_zone0/temp 2>/dev/null) |"
        echo "| svc_ofn | $SVC_OFN |"
        echo "| svc_hypno | $SVC_HYPNO |"
        echo "| svc_cloudflared | $SVC_CF |"
        echo "| svc_octopus_bridge | $SVC_BRIDGE |"
        echo "| ofn_git_head | $(git -C "$OFN_HOME" rev-parse --short HEAD 2>/dev/null) |"
        echo "| ofn_dirty_files | $(git -C "$OFN_HOME" status --porcelain 2>/dev/null | wc -l) |"
        echo "| heartbeat_pushed_at | $PUSHED_AT |"
        echo "| wire_last_windows_msg | $WIRE_LAST |"
    } > "$HB_FILE"

    # رصد پیام‌ها و بک‌لاگ — هر ۲ ضربان (~۱ دقیقه)
    if [ $((BEAT % 2)) -eq 0 ] && [ -d "$WIRE_REPO/.git" ]; then
        if git -C "$WIRE_REPO" fetch -q origin ofn/wire 2>/dev/null; then
            LAST_ID=$(git -C "$WIRE_REPO" show FETCH_HEAD:MESSAGES-WINDOWS.md 2>/dev/null \
                | grep -oE 'id:[A-Za-z0-9_-]+' | tail -1)
            [ -n "$LAST_ID" ] && WIRE_LAST="$LAST_ID @ $(date -Iseconds)"
            BACKLOG_OPEN=$(git -C "$WIRE_REPO" show FETCH_HEAD:BACKLOG-FOR-OWNER.md 2>/dev/null \
                | grep -c '^- \[ \]')
        fi
        BOARD_LAST=$(grep -oE 'id:b[0-9]+' "$WIRE_REPO/MESSAGES-BOARD.md" 2>/dev/null | tail -1)
    fi

    # چک عمومی پاها — هر ۵ ضربان
    if [ $((BEAT % 5)) -eq 1 ]; then
        {
            echo ""
            echo "## legs /healthz (عمومی)"
            echo ""
            echo "| پا | کد |"
            echo "|---|---|"
        } >> "$HB_FILE"
        LEGS_JSON="{"
        LEGS_FIRST=1
        for h in panel ziman lead studio; do
            code=$(timeout 10 curl -s -o /dev/null -w "%{http_code}" \
                "https://$h.master-painting.com/healthz" 2>/dev/null || echo ERR)
            echo "| $h | $code |" >> "$HB_FILE"
            if [ "$LEGS_FIRST" -eq 0 ]; then LEGS_JSON="$LEGS_JSON, "; fi
            if [ "$code" = "200" ]; then
                LEGS_JSON="$LEGS_JSON\"$h\":200"
            else
                LEGS_JSON="$LEGS_JSON\"$h\":\"$code\""
            fi
            LEGS_FIRST=0
        done
        LEGS_JSON="$LEGS_JSON}"
    fi

    # status.json — منبع پنل مالک (بدون راز؛ همین داده‌ها در شاخهٔ عمومی heartbeat هست)
    printf '{"beat":%s,"time":"%s","services":{"ofn":"%s","hypno":"%s","cloudflared":"%s","octopus_bridge":"%s"},"legs_healthz":%s,"wire":{"last_windows_msg":"%s","last_board_msg":"%s"},"backlog_open":%s}\n' \
        "$BEAT" "$NOW" "$SVC_OFN" "$SVC_HYPNO" "$SVC_CF" "$SVC_BRIDGE" \
        "$LEGS_JSON" "$WIRE_LAST" "$BOARD_LAST" "$BACKLOG_OPEN" \
        > "$STATUS_FILE.tmp" && mv "$STATUS_FILE.tmp" "$STATUS_FILE"

    # پوش دوره‌ای — هر ۲۰ ضربان؛ همیشه یک کامیت واحد (amend + force)
    if [ $((BEAT % 20)) -eq 1 ]; then
        cp "$HB_FILE" "$REPO/BOARD-HEARTBEAT.md"
        git -C "$REPO" add BOARD-HEARTBEAT.md 2>/dev/null
        if ! git -C "$REPO" diff --cached --quiet 2>/dev/null; then
            if git -C "$REPO" log -1 --format=%s 2>/dev/null | grep -q '^heartbeat'; then
                git -C "$REPO" -c user.name="ofn-board" -c user.email="board@dietpi" \
                    commit -q --amend -m "heartbeat $(date -Iseconds)"
            else
                git -C "$REPO" -c user.name="ofn-board" -c user.email="board@dietpi" \
                    commit -q -m "heartbeat $(date -Iseconds)"
            fi
            if git -C "$REPO" push -q --force origin "ofn-heartbeat:$REMOTE_BRANCH" 2>/dev/null; then
                PUSHED_AT="$(date -Iseconds)"
            else
                PUSHED_AT="push_failed $(date +%H:%M)"
            fi
            # germline — کانال اصلی ویندوز (اگر mount باشد؛ نبودش خط نیست)
            if [ -d /mnt/octopus-germline/octopus.git ]; then
                git -C "$REPO" push -q --force germline "ofn-heartbeat:$REMOTE_BRANCH" 2>/dev/null || true
            fi
        fi
    fi

    sleep 30
done
