---
type: knowledge
status: active
tags: [hypnosis]
epistemic_status: speculative
created: 2026-07-03
updated: 2026-07-03
---

# Architecture.md — همه‌یِ معماری‌هایِ فنی، یک‌جا

## SERVER_ARCHITECTURE.md (منبعِ اول‌دست، این پوشه)
Control-plane سبک رویِ یک VPS: هر پروژه در یک container؛ `stackctl` (root CLI) برایِ up/down/restart/status/logs/deploy/kill؛ Telegram control-bot (فقط chat ID مجاز) + userbot جدا (Telethon، least-privilege، هشدارِ ToS)؛ Traefik جلوی همه (TLS خودکار)؛ CI/CD گیت‌شده (test→gitleaks→build→GHCR→deploy→health-check→rollback خودکار)؛ secret via SOPS+age (نه plaintext)؛ Uptime Kuma + Dozzle برایِ observability؛ audit log و kill switch سراسری/به‌ازایِ‌پروژه. هزینه: VPS ≈AUD $35–70/ماه (جدا از بودجه‌یِ API هر پروژه؛ Brushline API ≈AUD $15–40/ماه).

## fusion-mvp (دایجست)
`run.py → Orchestrator.run(topic)`؛ جریان: researcher→analyst→guardrail→panel(۳داور)→grounding→HITL→finalize. MOCK/LIVE با env. Config: `MODEL=claude-sonnet-4-6`, `MAX_TOKENS_PER_CALL=1024`, `MAX_CALLS_PER_AGENT=3`, `GLOBAL_BUDGET_USD=0.50`. IGK: kill-switch فایلِ `logs/STOP`، audit زنجیره‌هشِ SHA-256. **LeadAgent** (جدیدترین لایه): `src/lead.py`، `USE_LEAD=True`، `MAX_LEAD_ROUNDS=3`؛ سه گیتِ غیرقابلِ‌دورزدن (بودجه، تفکیکِ producer/judge، HITL+grounding قبلِ finalize).

## Brushline / AiFarm-Lead (دایجست)
00-Orchestrator + ۶ Worker (A–F) + Constitution Gate + Approval Queue + audit هش‌زنجیره‌ای. فازِ ۰و۱ کامل؛ P3 Approval Queue ساخته شد (۴۷ چکِ سبز). شکافِ باز: semantic ACL (P2).

## infra-control (دایجست)
Docker Compose + Traefik + stackctl + CI/CD gated + Uptime Kuma/Dozzle؛ VPS: Hetzner CX22 (~€4.35–4.59/ماه). این احتمالاً پیاده‌سازیِ زنده‌یِ همان چیزی است که `SERVER_ARCHITECTURE.md` طراحی کرده — ولی جلوتر از آن کپیِ محلی.

## LANGAR (دایجست)
باتِ تلگرام رویِ Hetzner (`~/langar`)؛ `deploy.sh` + `docker-compose.unified.yml` + `.env` (BOT_TOKEN, OWNER_ID, Postgres)؛ بودجه: روزانه $۱ / ماهانه $۳۰.

## Silabi-Bot (منبعِ اول‌دست)
تک‌فایلِ پایتون (۵۴۰ خط)، بدونِ container/deploy — فقط `python silabi_bot.py` رویِ ویندوز یا Orange Pi. SQLite محلی (سه جدول: energy، ideas، food). لایه‌یِ «بازتابِ تطبیقی» (`learn_profile`) هر بار از رویِ کلِ تاریخچه بازمحاسبه می‌شود؛ چیزی رویِ دیسک ننوشته می‌شود جز خودِ دیتا — یعنی مدل هیچ‌وقت stale نمی‌ماند اما هم هیچ‌وقت خودش را روی دیسک ذخیره نمی‌کند (هزینه: هر پیام یک بازمحاسبه‌یِ کامل، که برایِ حجمِ دیتایِ شخصیِ یک‌نفره بی‌اهمیت است).

## مقایسه‌یِ معماری‌ها (روبریکِ ۱–۱۰، از پرامپتِ مادر §۷)

| معماری | Cost | Complexity | Scalability | Maintainability | Security |
|---|---|---|---|---|---|
| SERVER_ARCHITECTURE (Docker+Traefik+stackctl) | ۸ | ۶ | ۸ | ۸ | ۹ |
| fusion-mvp (multi-agent+گیت) | — | متوسط-بالا | تک‌کاربره، کافی | بالا (تست ۴۰/۴۰) | بالا (کیل‌سوییچ+audit) |
| Silabi-Bot (تک‌فایل، بدونِ container) | ۱۰ (رایگان) | ۲ | پایین (تک‌کاربره، عمداً) | ۷ | متوسط (⚠️ باگِ توکن — به `TODO.md`) |

*نمره‌هایِ ردیفِ اول مستقیماً از خودِ `SERVER_ARCHITECTURE.md` است؛ نمره‌هایِ ردیف‌هایِ دیگر برآوردِ من است چون منبع نمره نداده — صریحاً به‌عنوانِ برآورد علامت خورد، نه نقل‌قول.*
