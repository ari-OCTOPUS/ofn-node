# Board2 Studio APPROVE→PUBLISH drain — PASS (2026-08-22)

**One item only** — no fan-out.

## Item
- outbox_id: `studio:7b09170c06b8135d6fe79cd590b1f74f5fc68bc6bf41f2fe8ab107c97ff205e1`
- draft: `unlock-shot-0001` / media: `studio/shot-0001/0-1600.jpg`
- platform: `telegram_channel`
- caption: existing media note `تست`

## Drain
1. Owner decide approve+confirmed_twice → `approved_manual` @ 2026-08-22T12:54:56Z
2. publish-telegram dry_run → ok (`adapter:dry-run`)
3. publish-telegram live → **PASS** `adapter:ok`
4. Telegram `external_id`: **7**
5. Outbox final: `manual_completed` / completion_channel=`telegram` / completed_at=2026-08-22T12:54:58Z

## Result
**PASS**