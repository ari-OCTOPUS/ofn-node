# AUTH-THREAT-MODEL (M0)
- single factor: Telegram-bound session + localhost/tunnel reachability
- V2 risks: tunnel breadth; CSRF on POSTs (verify SameSite); approvals lack API-level payload-hash/expiry binding (verify M1); secrets.env adjacency — web path must never read it
- V2 must add: idempotency, expiry, payload-hash binding, first-valid-wins, receipts (per handbook)
