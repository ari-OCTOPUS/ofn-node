# Systemd Timers — board138 Deploy Guide

## What these do

| Timer | Time | Purpose |
|---|---|---|
| `ofn-sync` | 06:50 | `git pull` + `ingest_manual_leads.py` — keeps DB fresh |
| `ofn-digest` | 07:00 | Generates daily callable list in `digests/YYYY-MM-DD.md` |

Sync runs 10 minutes before digest so the DB has the latest leads.

## ASSUMPTIONS — verify before deploy

- **Repo path:** `/home/dietpi/ofn` — OWNER INPUT REQUIRED (Ari: what's the actual path?)
- **User:** `dietpi` — check with `whoami` on board138
- **Timezone:** `Australia/Sydney` — check with `timedatectl`
- **Git auth:** HTTPS token or SSH key cached — check with `cd ~/ofn && git pull origin main`
- **Python:** `/usr/bin/python3` — check with `which python3`

## Deploy steps (on board138)

```bash
# 1. Copy files
sudo cp deploy/systemd/ofn-*.service /etc/systemd/system/
sudo cp deploy/systemd/ofn-*.timer /etc/systemd/system/

# 2. Reload systemd
sudo systemctl daemon-reload

# 3. Enable and start timers
sudo systemctl enable --now ofn-sync.timer
sudo systemctl enable --now ofn-digest.timer

# 4. Verify
systemctl list-timers | grep ofn
```

## Manual test

```bash
# Test sync
sudo systemctl start ofn-sync.service
journalctl -u ofn-sync.service --no-pager -n 20

# Test digest
sudo systemctl start ofn-digest.service
cat ~/ofn/digests/$(date +%Y-%m-%d).md
```

## Future: Telegram notification

After digest runs, send the output to Ari via Telegram bot.
Needs: bot token + chat ID — OWNER INPUT REQUIRED.
