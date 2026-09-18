#!/bin/bash
# deploy_evt_units.sh — create the event-driven consumer units (EVENT-DRIVEN-OCTOPUS 2026-09-18)
# Shadow-first: mode.json default=shadow, so no runner executes until a kind is flipped.
set -eu
S=/etc/systemd/system
RD=/home/ari/ofn/state/revenue-drive
AG=/home/ari/ofn/ofn/agents
GATE=/home/ari/ofn/tools/octopus_event_gate.sh

mk_service() { # mk_service <name> <dirs|-> <trigger> <cmdline>
  local name="$1" dirs="$2" trig="$3" cmd="$4"
  sudo -n tee "$S/octopus-evt-$name.service" >/dev/null <<EOF
[Unit]
Description=OCTOPUS event consumer: $name (EVENT-DRIVEN-OCTOPUS 2026-09-18)
After=network-online.target

[Service]
Type=oneshot
User=ari
Environment=OCTOPUS_EVENTS_ROOT=/home/ari/ofn/state/events
Environment=OCTOPUS_GATE_TRIGGER=$trig
EnvironmentFile=-/home/ari/.config/ofn/secrets.env
ExecStart=$GATE $name $dirs -- /bin/bash -c "$cmd"
TimeoutStartSec=900
Nice=5
EOF
}

mk_path() { # mk_path <name> <PathChanged value> [extra-directive]
  local name="$1" watch="$2" extra="${3:-}"
  sudo -n tee "$S/octopus-evt-$name.path" >/dev/null <<EOF
[Unit]
Description=OCTOPUS event watcher: $name

[Path]
$watch
[Install]
WantedBy=paths.target
EOF
  [ -n "$extra" ] && sudo -n sed -i "/^\[Install\]/i $extra" "$S/octopus-evt-$name.path"
}

EV=/home/ari/ofn/state/events/inbox

# 1. mail_seen -> reply detection + imap classification
mk_service mail "$EV/mail_seen" "nats:mail_seen" \
  "python3 $RD/reply_alert.py; python3 $AG/imap_listener.py"
mk_path mail "PathChanged=$EV/mail_seen" "DirectoryNotEmpty=$EV/mail_seen"

# 2. inbound funnel events -> replies, quotes, owner cards, state meter
mk_service inbound "$EV/inbound_reply,$EV/quote_requested,$EV/quote_accepted,$EV/opted_out,$EV/bounce" "events:inbound" \
  "python3 $RD/reply_runner.py; python3 $AG/quote_pipeline.py; python3 $RD/owner_ask.py; python3 $RD/revenue_state.py; python3 $RD/event_notify.py"
mk_path inbound "PathChanged=$EV/inbound_reply" "DirectoryNotEmpty=$EV/inbound_reply"
sudo -n sed -i "/^\[Install\]/i PathChanged=$EV/quote_requested\nPathChanged=$EV/quote_accepted\nPathChanged=$EV/opted_out\nPathChanged=$EV/bounce" "$S/octopus-evt-inbound.path"

# 3. lead_found -> enrich + phone notify + packet preparation
mk_service leads "$EV/lead_found" "nats:lead_found" \
  "python3 $RD/lead_enrich.py; python3 $RD/phone_list_notify.py; python3 $RD/money_executor.py"
mk_path leads "PathChanged=$EV/lead_found" "DirectoryNotEmpty=$EV/lead_found"

# 4. lead_enriched|draft_ready -> prepare + stage + send + state
mk_service send "$EV/draft_ready,$EV/lead_enriched" "events:send" \
  "python3 $RD/money_executor.py; python3 $RD/send_queue.py; python3 $RD/revenue_state.py"
mk_path send "PathChanged=$EV/draft_ready" "DirectoryNotEmpty=$EV/draft_ready"
sudo -n sed -i "/^\[Install\]/i PathChanged=$EV/lead_enriched" "$S/octopus-evt-send.path"

# 5. card_resolved -> state, next packets, owner cards, replies
mk_service cards "$EV/card_resolved" "nats:card_resolved" \
  "python3 $RD/revenue_state.py; python3 $RD/money_executor.py; python3 $RD/owner_ask.py; python3 $RD/reply_runner.py"
mk_path cards "PathChanged=$EV/card_resolved" "DirectoryNotEmpty=$EV/card_resolved"

# 6. owner channels: tg-inbox + go_b3 spool (direct file watch, no event files)
mk_service owner "-" "file:tg-inbox+go_b3_spool" \
  "python3 $RD/owner_reply.py; python3 $RD/event_notify.py; cd $AG && python3 glass_runner.py; cd $AG && python3 go_b3_owner_bind.py poll"
mk_path owner "PathChanged=$RD/tg-inbox.jsonl" "PathModified=$RD/tg-inbox.jsonl"
sudo -n sed -i "/^\[Install\]/i PathChanged=/home/ari/ofn/state/owner_dialogue/go_b3_tg_spool.jsonl\nPathModified=/home/ari/ofn/state/owner_dialogue/go_b3_tg_spool.jsonl" "$S/octopus-evt-owner.path"

# 7. idle beat -> continuous discovery + review loop
mk_service idle "$EV/idle" "nats:idle" \
  "python3 $RD/discovery_runner.py; python3 $RD/revenue_drive.py"
mk_path idle "PathChanged=$EV/idle" "DirectoryNotEmpty=$EV/idle"

# 8. ziman orders/payments/stock -> state meter
mk_service orders "$EV/order_seen,$EV/payment_seen,$EV/stock_changed" "events:orders" \
  "python3 $RD/revenue_state.py"
mk_path orders "PathChanged=$EV/order_seen" "DirectoryNotEmpty=$EV/order_seen"
sudo -n sed -i "/^\[Install\]/i PathChanged=$EV/payment_seen\nPathChanged=$EV/stock_changed" "$S/octopus-evt-orders.path"

sudo -n systemctl daemon-reload
for n in mail inbound leads send cards owner idle orders; do
  sudo -n systemctl enable --now "octopus-evt-$n.path" >/dev/null 2>&1
  printf '%-8s path=%s\n' "$n" "$(systemctl is-active octopus-evt-$n.path)"
done
echo "--- units in shadow (mode.json default) ---"
cat /home/ari/ofn/state/events/mode.json
