# Integration Inventory

| Integration | Current status | Safe mode | Notes |
|---|---:|---|---|
| Telegram Owner Bot | Configured by env name | approval/read | values redacted; owner allowlist present |
| Telegram Lead Bot | Token configured, allowlist empty | locked | set `OFN_PARTNER_USER_IDS_LEAD` before partner use |
| Instagram | Existing business asset per owner statement | read-only first | no OAuth/publish adapter enabled here |
| Google Business Profile | Existing asset per owner statement | read-only first | no scraping; official API only |
| Cloudflared tunnel | configured | routes only | host inventory captured |
| Email | env flag exists, outbound off | planned | mailbox ingest before send |
| Publish | env flag exists, off | blocked | OwnerRelease required later |
| B2B directories | planned registry | research only | contact != consent |
| Tender portals | planned registry | alert/mailbox ingest | no submit automation |
