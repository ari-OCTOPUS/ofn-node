# Board2 Studio CONSENT RELEASE + one-item — PASS (2026-08-22)

## Discover
- Consent DB: `/home/ari/.local/share/ofn/consent.sqlite`
- Consent docs dir: `/home/ari/.local/share/ofn/consent-docs/`
- API: `ConsentStore.record_release` (schema `releases` table); owner HTTP also at `POST /api/v1/owner/consent/releases`

## Consent record (real, not bypass)
- release_id: `rel-self-tg-20260822-124450z`
- subject: `self` / tenant: `studio`
- scope: `telegram_channel`
- document_ref (board): `/home/ari/.local/share/ofn/consent-docs/owner-release-self-telegram-20260822-124450z.md`
- document_sha256: `cfa1f67d53415c8d7ca47844c9714844ab4899a31e1040305617f86c2493ebfe`
- recorded_by: `owner-ari-relay` (owner widget GO via ari)
- media_scope: existing library including shot-0001
- Consent prove: **PASS** — `may_publish` allowed for telegram_channel

## One-item enqueue (STOP)
- draft: `unlock-shot-0001`
- shot/media: `studio/shot-0001/0-1600.jpg`
- caption: existing media note `تست` (no invent)
- platform: `telegram_channel` only
- queued: **1**
- outbox_id: `studio:7b09170c06b8135d6fe79cd590b1f74f5fc68bc6bf41f2fe8ab107c97ff205e1`
- status: `pending` / kind: `studio:publish`

## Kept
- node.env bak: `/home/ari/.config/ofn/node.env.bak-studio-unlock-20260822T123514Z`
- No fan-out, no paid, no mining