# WLOS Deployment Guide

WLOS-Sydney-1 is a private, single-user system, so the deployment story is deliberately small: everything runs from one `docker-compose.yml` (PostgreSQL 16, Redis 7, a one-shot Prisma migrate job, the grammY bot, the BullMQ worker, the Fastify API on :8080, and a nightly backup container). The product owner's decision is to run on **local Docker now** and revisit managed hosting later using the comparison in this document. Whatever the host, two constraints are non-negotiable: data stays in the **Sydney region** when it moves to any cloud, and this remains a personal tool — not a medical service — so we optimise for low cost and low ops burden, not five-nines.

## Local development

Prerequisites:

- Node.js ≥ 20 (Node 22 recommended — it matches the `node:22-alpine` Docker image)
- Docker with Compose v2
- A Telegram bot token from @BotFather and a Sakana API key (console.sakana.ai/api-keys)

Setup:

```bash
cp .env.example .env
# Fill in at minimum:
#   TELEGRAM_BOT_TOKEN=...        # from @BotFather
#   SAKANA_API_KEY=...            # Fugu is enabled from day one (FUGU_ENABLED=true)
#   TELEGRAM_OWNER_CHAT_ID=...    # single-user mode serves only this chat

docker compose up -d postgres redis   # infra only; apps run on the host in dev
npx prisma migrate dev                # create/apply migrations (Prisma 7, engine-less + pg adapter)
npm run seed                          # exercises + baseline data (prisma/seed.ts)
```

Run the three processes in separate terminals:

```bash
npm run bot      # grammY bot, TELEGRAM_MODE=polling in dev
npm run worker   # BullMQ worker: daily planner, check-in delivery, reports
npm run api      # Fastify on http://localhost:8080 (/health, /coach/*)
```

If Fugu is unreachable or `FUGU_MONTHLY_TOKEN_BUDGET` (default 2,000,000 tokens) is exhausted, the provider chain falls back (fugu → optional OpenAI/Anthropic keys → deterministic rules). Basic coaching never depends on an LLM being up, so a missing `SAKANA_API_KEY` degrades features rather than breaking dev.

## Production: single VPS with Docker Compose

The supported production shape today is one small VPS (Sydney region) running the full compose stack:

```bash
docker compose up -d --build
```

This starts, in dependency order: `postgres` (healthchecked) → `migrate` (one-shot `prisma migrate deploy`) → `bot`, `worker`, `api` (each waits for the migrate job to complete) → `backup` (nightly pg_dump, see below). All app containers read `.env` via `env_file`; `DATABASE_URL`/`REDIS_URL` are overridden in compose to point at the internal service names.

Production hardening checklist:

- Change the default `wlos:wlos` Postgres password in both compose and `DATABASE_URL`.
- Compose publishes 5432/6379 for dev convenience — on a VPS, firewall them (or bind to 127.0.0.1) so only 80/443 are reachable.
- Switch the bot to webhook mode (below); polling is for dev.

### Telegram webhook mode

Set in `.env`:

```bash
TELEGRAM_MODE=webhook
TELEGRAM_WEBHOOK_URL=https://wlos.example.com/webhook/telegram   # must be HTTPS
TELEGRAM_WEBHOOK_SECRET=<random 32+ chars>                        # verified on every update
```

Terminate TLS with a reverse proxy in front of :8080 (the only app port compose publishes). Caddy is the least-effort option (automatic Let's Encrypt):

```caddy
wlos.example.com {
    reverse_proxy 127.0.0.1:8080
}
```

nginx equivalent:

```nginx
server {
    listen 443 ssl;
    server_name wlos.example.com;
    ssl_certificate     /etc/letsencrypt/live/wlos.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/wlos.example.com/privkey.pem;
    location / { proxy_pass http://127.0.0.1:8080; proxy_set_header X-Forwarded-For $remote_addr; }
}
```

## Managed-hosting comparison (decide later)

Ballparks are July-2026-ish for the Sydney region — **verify current pricing before deciding**. Scores are 1–10, **10 = best for this project** (so Cost 10 = cheapest, Complexity 10 = simplest).

| Option | Price ballpark | Notes |
|---|---|---|
| Local Docker (current) | ~A$0 + power | Everything colocated; backups are our own problem; no data leaves the apartment |
| AWS RDS PostgreSQL, ap-southeast-2 | t4g.micro ~US$15–30/mo | PITR built in; most reliable option; more IAM/VPC setup; low lock-in (plain Postgres, exit via pg_dump) |
| Supabase Pro | ~US$25/mo | Sydney AWS region available; easiest managed Postgres; PITR is a paid add-on; mild lock-in in auth/storage extras (unused here — we only need the database) |
| Neon | Generous free tier; pay-as-you-go above | Serverless Postgres with branching; newer vendor; **check Sydney region availability** before committing (data-residency requirement) |
| VPS for compute (Lightsail / Vultr / Fly.io, syd) | ~US$5–20/mo | Runs the compose stack as-is; pairs with any managed Postgres above |

| Option | Cost | Complexity | Scalability | Maintainability | Security | Time to implement |
|---|---|---|---|---|---|---|
| Local Docker (current) | 10 | 7 | 3 | 5 | 5 | 10 |
| AWS RDS (ap-southeast-2) | 5 | 4 | 9 | 9 | 9 | 4 |
| Supabase Pro | 6 | 8 | 7 | 8 | 8 | 8 |
| Neon | 9 | 7 | 8 | 7 | 7 | 7 |
| Sydney VPS (compute) | 8 | 6 | 5 | 6 | 6 | 8 |

**Recommendation** (medium budget, single user): keep local Docker for now. When the first cloud step happens, move compute to a Sydney VPS running this same compose file and put only Postgres on a managed service — RDS if reliability wins, Supabase if simplicity wins. Redis stays a colocated container next to the worker (it holds only queues and ephemeral state; losing it loses nothing durable). Neon is the wildcard: attractive pricing, but confirm the Sydney region first.

## Backup and restore

**Targets: RPO 24 h, RTO < 1 h.** A nightly logical dump is acceptable for a single user; losing at most one day of check-ins is annoying, not catastrophic.

- The `backup` container (postgres:16-alpine, `TZ=Australia/Sydney`) runs `pg_dump -F c` every night at **02:30 Sydney** into `./backups/wlos-YYYYMMDD.dump` and deletes dumps older than **30 days**.
- Off-site copy is a **documented manual/cron step**, not automated in compose. On the host:

```bash
# crontab: nightly at 03:30 Sydney, after the dump completes
30 3 * * * rclone copy /opt/wlos/backups remote:wlos-backups --max-age 48h
# or, keeping data in-region:
30 3 * * * aws s3 sync /opt/wlos/backups s3://wlos-backups --region ap-southeast-2
```

Restore drill — practice this into a scratch database, never straight over `wlos`:

```bash
docker compose cp ./backups/wlos-20260719.dump postgres:/tmp/restore.dump
docker compose exec postgres createdb -U wlos wlos_restore_test
docker compose exec postgres pg_restore -U wlos -d wlos_restore_test --no-owner /tmp/restore.dump
docker compose exec postgres psql -U wlos -d wlos_restore_test -c 'select count(*) from "Weight";'
docker compose exec postgres dropdb -U wlos wlos_restore_test
```

For a real restore, stop the app containers, restore into a fresh database, repoint `DATABASE_URL`, restart. **Launch acceptance item: a timed test restore must have been performed before production launch** — an unrestored backup is a hope, not a backup.

## Monitoring and ops (personal scale)

- **Logs**: all processes log pino JSON; `docker compose logs -f bot worker api` is the primary tool. Pipe through `pino-pretty` when reading by hand.
- **Health**: the API exposes `/health` on :8080. Point a free UptimeRobot monitor at it (and at the HTTPS domain in webhook mode).
- **Errors**: optional free-tier Sentry — worthwhile once webhook mode is on, since nobody is watching a terminal.
- **Disk**: watch free space; the Postgres volume, Redis AOF, and `./backups` all grow. A weekly `df -h` glance (or a cron that alerts below 20% free) is enough.
- **Cadence**: monthly, run `npm audit`, bump patch versions, and `docker compose build --pull && docker compose up -d` to pick up rebuilt base images.
- **Budget watch**: `LlmCall` rows record tokens and latency per provider; the weekly report surfaces spend against `FUGU_MONTHLY_TOKEN_BUDGET`.

## Secrets

- Secrets live only in `.env` — never in git. `.env.example` is the committed template; `TELEGRAM_BOT_TOKEN`, `SAKANA_API_KEY`, `TELEGRAM_WEBHOOK_SECRET`, and `COACH_API_KEY` are the sensitive four.
- On the server: `chmod 600 .env`, owned by the deploy user.
- Optional today: encrypt at rest with SOPS + age and decrypt on deploy.
- When moving to cloud: switch to the platform's secret manager (AWS Secrets Manager / Supabase vault) rather than copying `.env` files around; rotate the Telegram token and Sakana key at migration time.
