---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, node-138, telegram, consent]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: en
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/MISSING-EDGES]]"
  - "[[03 - Projects/OFN-Board/ofn/config.py]]"
  - "[[03 - Projects/OFN-Board/ofn/adapters/consent_store.py]]"
---

# 09 — Telegram and consent

```text
observed_at=2026-08-29T05:32:32Z
method=138_source_grep_plus_unit_list_no_bot_api
scope=this_host_only
SECRETS_READ=NO
TELEGRAM_CALLS=0
```

## Existing components (reuse these)

```text
TELEGRAM_EXISTING_COMPONENTS=OFN_BOT_TOKEN_{ZIMAN,LEAD,STUDIO,STUDIO_PARTNER,OWNER}_NAMES;OFN_OWNER_USER_IDS;OFN_PARTNER_USER_IDS_*;OFN_TELEGRAM_CHANNEL_ID;OFN_ALERT_TELEGRAM;publish_to_telegram;ConsentStore;telegram_channel.py;telegram_readonly.py;alert.py;legacy_panel;POST_/api/v1/decide;Cockpit_V2_GET;MiniApp_HMAC_tests
```

Token **values** not read. Whether env is populated is **UNKNOWN**.

## Inventory

| Topic | Finding | Truth |
|---|---|---|
| bots | Five **names** in `config.py`: ZIMAN, LEAD, STUDIO, STUDIO_PARTNER, `__owner__` | `LIVE_VERIFIED` names |
| Mini App | HMAC `verify_init_data` in 138 tests; live MiniApp gateway is **191** organism | `REPO_VERIFIED` / `DOCUMENTED` |
| authentication | owner allowlist name `OFN_OWNER_USER_IDS`; partner `OFN_PARTNER_USER_IDS_*` | `LIVE_VERIFIED` names |
| HMAC | test helpers; not a live poller | `REPO_VERIFIED` |
| customer consent | `ConsentStore` + `publish_to_telegram` require release; prior studio `consent:no_release` | `REPO_VERIFIED` / `DOCUMENTED` |
| update offsets / poller | **zero** long-poll processes; no telegram-bridge fragment | `LIVE_VERIFIED` |
| tenant mapping | pack legs ziman/lead/studio + token map keys | `LIVE_VERIFIED` |
| outbox integration | publish goes through outbox / release context | `REPO_VERIFIED` |
| delivery receipts | `complete_manual` / ledger `TELEGRAM_PUBLISHED` names | `REPO_VERIFIED` |
| fallback / alert | `alert.py` Telegram only if `OFN_ALERT_TELEGRAM=1`; default off | `REPO_VERIFIED` |
| rate limits | `rate_limit.py`, `inbound_rate.py` present | `LIVE_VERIFIED` files |
| PII scrub | P1 owner_items allowlist; `flag_drift` BEARER gap is 191/`_ops` | `DOCUMENTED` |

## Answers

- **Consented reply vs draft:** outbound customer effect requires consent release + owner path. Draft/card without send is the design of `owner_decision.render_fake` (unwired). Live decide does **not** send.
- **Cold outreach block:** `consent:no_release` and kill-switch / gates (`DOCUMENTED` studio unlock + `REPO_VERIFIED` consent store).
- **Fallback message external effect?** Yes **if** `OFN_ALERT_TELEGRAM=1` and token present — crash notifier. Flag value **not read**. Treat as potential effect; default documented off.
- **Are three tokens required?** Code has **five** bot token names, not three. Audit `56e9369` / WHAT-IS-DEAD: five tokens, zero pollers.
- **Token names:** `OFN_BOT_TOKEN_ZIMAN|LEAD|STUDIO|STUDIO_PARTNER|OWNER`. Docs also mention organism `OCTOPUS_TELEGRAM_BOT_TOKEN` (191 plane) and `HFM_BOT_TOKEN` (hypno-fugu-mini) — **do not read those files**.
- **Egress exists?** Code yes (`publish_to_telegram`, alert). Live poller/bridge **no**.
- **New Poller = duplication?** **YES** — E5 / WHAT-IS-DEAD: reuse existing `__owner__` bot + one poller when env exists; do not add a sixth bot or parallel bridge.

## Contract

`/home/ari/ofn/docs/audit-138/138-TELEGRAM-CONTRACT.md` status **CONTRACT_GAP**: no production OwnerDecision Telegram card; bridge inactive; owner dialogue = legacy panel + read-only Cockpit V2. Field names include `*_sha256` and `policy_sha256` vs card `*_sha`.

```text
T1_STATUS=PARTIAL
CONTRACT=CONTRACT_GAP
POLLERS=0
BRIDGE_UNIT=ABSENT
```
