# OWNER-RULING-PHONELIST-2026-09-18 — DIDWW deferred; phone list auto-pushed to owner Telegram

- stamp: 2026-09-18T08:30Z (18:30 AEST)
- channel: owner chat (ZCode session, lane S2-OPEN-20260918). Owner words:
  «didww فعلا تعیین هویتش مشکل داره بزارش برای هفته دیگه اتومایتک بشه الان لیست هارو
  تلگرام برام بفرست ... یکاری کن اختاپوس خودش بدونه تو تلگرام خودکار لیست بفرسته من زنگ بزنم»

## Ruling 1 — DIDWW deferred
Automated calling (DIDWW purchase, 29 phone-only leads) deferred ~1 week: retry window opens
**2026-09-25**. Purchase remains an owner-card action whenever retried (unchanged red line).

## Ruling 2 — automatic phone list to owner Telegram (EXECUTED, live)
Until the call channel is live, OCTOPUS itself pushes the callable phone-only lead list to the
owner's Telegram so the owner can call manually.

### Implementation (money-path discipline: new files only, preimage + paired test + receipt)
- script: `/home/ari/ofn/state/revenue-drive/phone_list_notify.py`
  sha256 `d219300d51594dfc…` (vault copy: PHONE-LIST-NOTIFY-20260918.py)
  — reads phone-only-queue.jsonl, formats compact Persian list, sends via the existing
  owner door `ofn.agents.owner_notify.send` (owner-facing ONLY; never touches the customer
  send path). Dedup: re-sends ONLY when the list sha changes (no daily spam).
- paired test: DRY_RUN=1 → 1 chunk, 2259 chars, format verified (PASS).
- LIVE first send 08:25:31Z: ok=true, **25 callable leads** (4 of 29 queue rows have NO phone —
  website-only: Agile Strata, Dalton Strata, StrataTeam, Metro Asset Management — need a
  contact-form path, flagged to runtime lane). List sha `271b5d899d7e70f6…`.
- automation: `octopus-phone-list-notify.timer` (every 30 min; service oneshot, User=ari)
  service sha `9a2b34079dd42cc9` · timer sha `367b1774a25444d5`
  first scheduled tick verified: exited `{"why":"unchanged"}` — dedup proven, no spam.
- rollback: `sudo systemctl disable --now octopus-phone-list-notify.timer && sudo rm
  /etc/systemd/system/octopus-phone-list-notify.{service,timer} && systemctl daemon-reload`
  + delete script + state dir. (New files only; nothing pre-existing modified.)

## Receipts
- state/revenue-drive/phone-list-notify/{state.json,log.jsonl} on 138
- journalctl -u octopus-phone-list-notify (first ticks recorded above)
