#!/bin/bash
# install_systemd.sh — خدمات و تایمرهای Lane I (رأی Q7) روی بورد
# اجرا با: sudo bash tools/install_systemd.sh
set -eu
AGENTS=/home/ari/ofn/ofn/agents
SECRETS=/home/ari/.config/ofn/secrets.env
U=/etc/systemd/system

mk_svc() {  # name cmd
  cat > "$U/octopus-$1.service" <<EOF
[Unit]
Description=OCTOPUS $1
After=network-online.target

[Service]
Type=oneshot
User=ari
EnvironmentFile=$SECRETS
Environment=OCTOPUS_WIRE_LEAD_OUTBOUND=1
Environment=PYTHONUNBUFFERED=1
WorkingDirectory=$AGENTS
ExecStart=$2
EOF
}

mk_svc imap     "python3 $AGENTS/imap_listener.py"
mk_svc followup "python3 $AGENTS/followup_worker.py"
mk_svc digest   "python3 $AGENTS/daily_digest.py"
mk_svc heartbeat "python3 $AGENTS/heartbeat.py"
mk_svc backup   "bash /home/ari/ofn/tools/backup_ofn.sh && python3 $AGENTS/rotate_logs.py"
mk_svc drill    "bash /home/ari/ofn/tools/restore_drill.sh"
mk_svc quote    "python3 $AGENTS/quote_pipeline.py"

mk_timer() {  # name calendar [boot]
  if [ "${3:-}" = persistent ]; then
    cat > "$U/octopus-$1.timer" <<EOF
[Unit]
Description=OCTOPUS $1 timer

[Timer]
OnCalendar=$2
Persistent=true

[Install]
WantedBy=timers.target
EOF
  else
    cat > "$U/octopus-$1.timer" <<EOF
[Unit]
Description=OCTOPUS $1 timer

[Timer]
OnCalendar=$2

[Install]
WantedBy=timers.target
EOF
  fi
}

mk_timer imap "*:0/15"
mk_timer quote "*:0/30"
mk_timer followup "*-*-* 01:00:00" persistent
mk_timer digest "*-*-* 21:00:00" persistent
mk_timer heartbeat "hourly"
mk_timer backup "*-*-* 03:00:00" persistent
mk_timer drill "Sun *-*-* 04:00:00" persistent

systemctl daemon-reload
for t in imap quote followup digest heartbeat backup drill; do
  systemctl enable --now "octopus-$t.timer"
done
systemctl list-timers --no-pager | grep octopus || true
echo "OK — seven timers armed"
