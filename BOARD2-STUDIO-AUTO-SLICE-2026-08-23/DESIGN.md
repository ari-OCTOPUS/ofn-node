# Board2 Studio AUTO SLICE (design PASS)

## Scope NOW
- Platform: **telegram_channel** only (consent self)
- Captions: `media_items.note` non-empty only — **no invent**
- Guard: **skip re-publish** if outbox already `manual_completed` for that shot
- Flow: partner send-to-outbox → owner decide approve+confirmed_twice → publish-telegram dry_run → live

## NOT NOW
- OnlyFans / Fansly adapter live publish (blueprint only)
- Fan-out shot-0003..0022 without captions
- Flipping WIRING `studio_wire` (keep false)

## Inventory 2026-08-23
- SKIP republish: 0001, 0002
- HOLD empty caption: 0003–0022
- ELIGIBLE new enqueue: **none**

## Tool
`/home/ari/ofn/scripts/studio_auto_slice.py --inventory`
