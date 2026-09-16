# OPS-NOTE — cloudflared / cp pull

Written: 2026-08-22T19:12:00+10:00 AEST (laptop)

- `cloudflared` process is **up** on the laptop (observed PIDs present).
- **cp pull 401** may still occur: tunnel up ≠ cp auth. Do not treat 401 as evidence that LAN:9101 bind failed or succeeded.
- LAN:9101 execute verification remains **direct LAN** to `192.168.0.182:9101` (or rollback SSH `-L 9101:127.0.0.1:9101`), not cloudflared/cp.
