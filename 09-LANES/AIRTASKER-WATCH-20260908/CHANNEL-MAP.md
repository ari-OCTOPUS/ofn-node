# AIRTASKER-WATCH — Channel Map (Phase 0.1)

GOV_VERSION=V8 · LADDER=L2 · lane: AIRTASKER-WATCH-20260908 · date: 2026-09-08
Evidence grade of this document: E1 (channel existence documented from official support
articles; **all latency values unverified** — no measurement has been taken yet).

## Confirmed official channels (Airtasker Support Centre, read 2026-09-08)

| # | Channel | What it is | Config path | Latency | Payload shape |
|---|---------|-----------|-------------|---------|---------------|
| 1 | **Task alerts** (saved search) | Airtasker notifies you about new tasks matching a saved alert: location + in-person/online + keywords | Web: set up task alerts (support article 360015124312) | **status: unverified** | **status: unverified** — parser built tolerant; needs 1 real sample |
| 2 | **Notification preferences** (email/push toggles incl. "Keyword task alerts") | Per-channel delivery control for the alerts above | Account settings → notification preferences (support article 201078710) | **status: unverified** | n/a (delivery control) |
| 3 | **SMS notifications** | SMS after phone-number verification | Verify phone number in web settings (support article 21380732373785) | **status: unverified** | **status: unverified** |
| 4 | App push notifications | Mobile push for new tasks/alerts | Airtasker mobile app | **status: unverified** | n/a (human channel) |

Sources (official):
- https://support.airtasker.com/hc/en-au/articles/360015124312-How-do-I-set-up-task-alerts
- https://support.airtasker.com/hc/en-au/articles/201078710-How-do-I-manage-my-notification-preferences
- https://support.airtasker.com/hc/en-au/articles/21380732373785-Can-I-get-SMS-notifications
- https://support.airtasker.com/hc/en-au/articles/4414936383769 (winning tasks: fast detailed offers win)

## Latency measurement plan (until measured: everything unverified)

1. Owner enables channel 1+2 (Painting keywords, Sydney; email on).
2. Owner forwards/saves **one real alert email** as `.eml` into this lane folder →
   parser E2 on real input; Date/Received headers give alert-side timestamp.
3. posted→seen latency = (owner opens TG card) − (task posted_at from task page,
   read manually by owner). Never inferred; n≥30 before any number is quoted
   (UNDERPOWERED rule).

## Not a channel (probed, phase 0.3)

Public search URL scraping: see PROBE-20260908.md — registry URL stale (404),
site itself answers honest probes normally (302 root). No harvesting path here;
alert channels are the sanctioned path (registry: `manual_monitor`,
"manual proposal only").
