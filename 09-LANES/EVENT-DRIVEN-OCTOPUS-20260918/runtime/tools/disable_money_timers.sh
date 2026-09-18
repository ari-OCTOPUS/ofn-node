#!/bin/bash
# disable_money_timers.sh — Phase 5 timer sunset (EVENT-DRIVEN-OCTOPUS 2026-09-18).
# For every money-path timer whose cycle is now event-driven: preimage (unit text) +
# disable --now + receipt row. Non-money timers (pulse, watchdogs, doctor, soak, ...)
# are NOT touched. Rollback: re-enable from the preimages.
set -u
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
EV=/home/ari/ofn/state/events
PRE=$EV/timer-preimages-$STAMP
RCPT=$EV/timer-sunset.jsonl
mkdir -p "$PRE"

# unit -> replacement (evidence comment)
TIMERS="
octopus-revenue-drive.timer  evt-idle+evt-send+evt-leads (funnel chain on domain events + idle)
octopus-shopify-watch.timer  octopus-ziman-watch.service (beat-driven sensor, 60s orders / 300s stock)
octopus-owner-reply.timer    evt-owner.path (PathChanged tg-inbox.jsonl)
octopus-reply-alert.timer    evt-mail.path (IMAP IDLE -> mail_seen)
octopus-imap.timer           octopus-imap-idle.service (IMAP IDLE push)
octopus-glass.timer          evt-owner.path (PathChanged tg-inbox + go_b3 spool)
octopus-quote.timer          evt-inbound.path (quote_requested event)
octopus-go-b3-bind.timer     evt-owner.path (PathChanged go_b3_tg_spool.jsonl)
octopus-discovery.timer      evt-idle.path (beat-idle -> discovery_runner, 4h budget guard)
octopus-phone-list-notify.timer evt-leads.path (lead_found)
octopus-scheduler.timer      evt-mesh.path (PathChanged octopus-mesh/state/events)
"

echo "$TIMERS" | while read -r unit why; do
  [ -z "$unit" ] && continue
  if ! systemctl list-unit-files "$unit" >/dev/null 2>&1 || ! systemctl cat "$unit" >/dev/null 2>&1; then
    printf '{"at":"%s","kind":"TIMER_NOT_FOUND","unit":"%s"}\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$unit" >> "$RCPT"
    echo "SKIP (not found): $unit"
    continue
  fi
  systemctl cat "$unit" > "$PRE/$unit.txt" 2>/dev/null
  systemctl list-timers --all --no-pager "$unit" 2>/dev/null | tail -n +2 | head -1 > "$PRE/$unit.last-tick.txt"
  was=$(systemctl is-enabled "$unit" 2>/dev/null || echo unknown)
  active=$(systemctl is-active "$unit" 2>/dev/null || echo unknown)
  sudo -n systemctl disable --now "$unit" >/dev/null 2>&1
  now=$(systemctl is-enabled "$unit" 2>/dev/null || echo unknown)
  printf '{"at":"%s","kind":"MONEY_TIMER_DISABLED","unit":"%s","was_enabled":"%s","is_enabled":"%s","was_active":"%s","replacement":"%s","preimage":"%s"}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$unit" "$was" "$now" "$active" "$why" "$PRE/$unit.txt" >> "$RCPT"
  echo "disabled: $unit (was=$was active=$active -> $now)"
done

echo
echo "=== remaining active timers (money path must be empty) ==="
systemctl list-timers --all --no-pager 2>/dev/null | grep -E 'octopus|ofn' | grep -vE 'pulse|watchdog|soak|doctor|witness|absence|selfmodel|brainwake|experience|coding-worker|provider-probe|budget-monitor|eti-telemetry|ops-agent|autonomy-supervisor|compute|shadow-verify|feedback-loop|learningfeeder|cognition|durability|mesh|fleet-scheduler|fake-hwclock' || true
echo
echo "preimages: $PRE"
echo "receipts:  $RCPT"
