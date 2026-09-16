# Studio shot-0002 duplicate note (2026-08-23)

## Choice
**LEAVE** telegram message id=10 as known duplicate. Do **not** delete.

## Why
- ofn has `publish-telegram` only; no `deleteMessage` / unpublish path in adapters or HTTP API
- inventing a raw Bot API delete would be irreversible and outside the proven approve→publish path
- ari: prefer leave unless safe reversible delete exists

## Record
| draft | outbox | tg id | status |
|---|---|---|---|
| unlock-shot-0002 | studio:ffacc584… | **9** | canonical first PASS |
| batch-shot-0002 | studio:332925c7… | **10** | known duplicate (late executor) |

## Hard rule going forward
Before any studio publish: check outbox/media_sent/external_id for that shot; if already published, SKIP.

## Hold
shot-0003..0022 until real captions.
