# Board2 Ziman activate + Lead LIVE campaign — 2026-08-22

## Ziman — PASS
- Public catalog `activated=true` (was hardcoded `False` in `ofn/node.py::public_catalog`)
- Prove: `GET /api/v1/public/catalog` Host `ziman.master-painting.com` → 200, ok=true, count=2, activated=true, SKUs ZM-0003 / ZM-0006
- No invent products. No paid ads.
- **Rollback:** `cp /home/ari/ofn/ofn/node.py.bak-catalog-activated-20260822T125811Z /home/ari/ofn/ofn/node.py && sudo systemctl restart ofn.service`

## Lead (Master Painting / Abbas) — PASS
- Campaign `lead:campaign:b0687e052a8c3822` status=**running**
- Title: Master Painting — existing-CRM nurture (owner GO 2026-08-22)
- **Audience scope:** existing CRM leads only (new5 / contacted1 / quoted1 / review1 = 8). No stranger blast. No invent leads.
- Channels: existing 7 marketing_channels (telegram connected; others planned)
- Blast guards still closed: auto_email/auto_dm/auto_post/live_sms/live_dm
- Automation posture: manual quote/reply via outbox only — no auto-send
- healthz lead :8792 = 200
- **Rollback:** set campaign status=`paused` for `lead:campaign:b0687e052a8c3822`

## Untouched
- Mining deferred
- Studio idle beyond prior publish