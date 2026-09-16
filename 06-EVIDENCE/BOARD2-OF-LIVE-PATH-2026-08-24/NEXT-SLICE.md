# NEXT-SLICE — Safe HTTP client (dry default; no live until second owner GO)

## Goal

Implement an OnlyFans **HTTP client scaffold** inside `/home/ari/ofn/ofn/adapters/platforms/onlyfans.py` (or a tiny helper module under `adapters/platforms/`) such that:

1. `dry_run=True` still returns `adapter:dry-run` / ok (unchanged).
2. `dry_run=False` + `OFN_ONLYFANS_LIVE` unset still returns `wire:disabled` (unchanged).
3. `dry_run=False` + `LIVE=1` + no cookie still returns `onlyfans:no-credentials`.
4. `dry_run=False` + `LIVE=1` + cookie present: may **attempt** structured HTTP **only if** a second, explicit owner GO later arms live; **until that GO**, keep returning a **non-sending** rule (prefer keep `adapter:real-publish-not-implemented` **or** introduce `onlyfans:http-scaffold-dry-hold` that never opens a socket unless a second flag is approved).

**This slice default recommendation:** build the client function(s) and unit-test them with mocked `urlopen`, but **do not call the network** from `publish()` until second owner GO. Replace `RULE_NOT_IMPLEMENTED` with a thin `_post_create(...)` that is unreachable without GO.

## Mirror telegram pattern

From `telegram_channel.py` / `publish_to_telegram`:

- Secrets at **call time** from env (`OFN_ONLYFANS_SESSION_COOKIE`), never stored on the class, never logged.
- Prefer stdlib `urllib.request` (already used for Telegram/Shopify style) unless owner chooses otherwise.
- Timeouts short (e.g. 15s).
- Map HTTP failures to `rule=` strings; never raise out of `publish()`.

## Out of scope for this slice

- Setting `OFN_ONLYFANS_LIVE=1`
- Writing cookie values into `secrets.env` / chat
- Node `publish_to_onlyfans` / OwnerRelease wiring (G5 — later slice)
- Inventing captions/prices
- Shopify multi-image Ziman gallery upload (HOLD)
- Etsy

## Acceptance (still dry)

- Existing `TestOnlyFansAdapter` 3 tests still pass.
- New tests: mock HTTP; assert **no** network when dry_run or LIVE unset.
- `available_platforms()` still lists `onlyfans`.
- Evidence note updated; bak under `/home/ari/.local/share/ofn/bak-...`

## Second slice (after owner review of this pack)

Consent scope `onlyfans` + vault cookie file + OwnerRelease call-site — still no LIVE until **SECOND-GO-CHECKLIST** complete.

