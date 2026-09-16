# STATUS — OnlyFans live path (READ/PLAN only)

**Stamp (AEST):** 2026-08-24 ~16:05 PT  
**Host:** Board2 DietPi `ari@192.168.0.138`  
**Adapter:** `/home/ari/ofn/ofn/adapters/platforms/onlyfans.py` (mtime 2026-08-24 08:41 UTC+10 board local)  
**Constraint honored:** no `OFN_ONLYFANS_LIVE=1`, no live post, no secret values.

## Probe results (today)

| Path | Input | `ok` | `rule` |
|------|-------|------|--------|
| Dry default | `PublishRequest.dry_run=True` (default) | `true` | `adapter:dry-run` (`RULE_DRY_RUN`) |
| Live attempt gated | `dry_run=False`, `OFN_ONLYFANS_LIVE` unset | `false` | `wire:disabled` (`RULE_WIRE_CLOSED`) |
| Documented (not probed live) | `LIVE=1` + no cookie | `false` | `onlyfans:no-credentials` |
| Documented (not probed live) | `LIVE=1` + cookie present | `false` | `adapter:real-publish-not-implemented` (`RULE_NOT_IMPLEMENTED`) |

**Env presence on Board2 process (names only, no values):**

- `OFN_ONLYFANS_LIVE` — present=false
- `OFN_ONLYFANS_SESSION_COOKIE` — present=false
- `OFN_ONLYFANS_USER_AGENT` — present=false
- `OFN_ONLYFANS_ACCOUNT_ID` — present=false
- `OFN_WIRE_OUTBOUND` — present=false

**`/home/ari/.config/ofn/secrets.env` key names present:** session/bots/shopify keys only — **no** `OFN_ONLYFANS_*` keys.  
**`node.env`:** not modified; scaffold evidence says `OFN_ONLYFANS_LIVE` not in node.env.

## Base adapter rules (`ofn/adapters/platforms/base.py`)

- `RULE_DRY_RUN` = `adapter:dry-run`
- `RULE_WIRE_CLOSED` = `wire:disabled`
- `RULE_NOT_IMPLEMENTED` = `adapter:real-publish-not-implemented`
- `PublishRequest.dry_run` defaults **True**

## `platform_matrix.json` — `onlyfans`

- layer **A**, risk **RED**, `api_mode`: `api_cautious`, `adult_policy`: `platform_native_adult`
- `caption_max`: 10000, `max_posts_24h`: 24
- notes: scaffold 2026-08-24; live forbidden until second owner GO; dry_run default; `OFN_ONLYFANS_LIVE` unset
- matrix file version 0.3 / updated_at 2026-08-05 (OF entry added with scaffold)

## Tests — `tests/test_platforms_contract.py` :: `TestOnlyFansAdapter`

1. `test_dry_run_returns_ok` → ok + `RULE_DRY_RUN`
2. `test_real_publish_returns_wire_closed_not_crash` → not ok + `RULE_WIRE_CLOSED` (LIVE unset)
3. `test_platform_id_is_onlyfans`
- No test currently asserts `RULE_NOT_IMPLEMENTED` or cookie branch (would require setting LIVE in test env).

## Telegram contrast (live HTTP exists)

`telegram_channel.py`:

- Dry → `RULE_DRY_RUN`
- Live uses `urllib.request.urlopen` → `https://api.telegram.org/bot{token}/sendMessage` (form-urlencoded)
- Token passed **per call**, never stored on adapter
- **Call site** `Node.publish_to_telegram` enforces `require_release_context()` / `OwnerRelease`, consent for platform `telegram_channel`, matrix screen, outbox `approved_manual`, double confirm, etc.

OnlyFans:

- **No** `publish_to_onlyfans` (or equivalent) in `node.py`
- Adapter returns `RULE_NOT_IMPLEMENTED` even if LIVE+cookie
- Scaffold documents env keys; HTTP client **not wired**

## OwnerRelease / consent / wire_outbound

- `OwnerRelease` + `require_release_context` in `ofn/kernel/release_switch.py` — used by **telegram** publish path only today
- Consent scopes are platform-id frozensets (`parse_scope`); money-scan OFC1: recorded release scope = `telegram_channel` only → **no onlyfans-scoped consent**
- `OFN_WIRE_OUTBOUND` / `wire_outbound` default closed (`config.py`); money-scan OFC3: still closed
- `available_platforms()` includes `onlyfans` via module discovery (alongside bluesky, email_ses, shopify, telegram_channel)

## Documented OF env key **names** (values never invented/pasted)

- `OFN_ONLYFANS_LIVE`
- `OFN_ONLYFANS_SESSION_COOKIE`
- `OFN_ONLYFANS_USER_AGENT` (optional)
- `OFN_ONLYFANS_ACCOUNT_ID` (optional)

## Prior money scan skim

`F:\backup\06-EVIDENCE\BOARD2-MONEY-DEEP-SCAN-2026-08-24\`: OF consent gaps OFC1–OFC5; cash prefer CASH-1..3 Ziman images; live OF in `not_this_week_without_explicit_go`; multi-image Ziman gallery HOLD for invent; Etsy HELD.

