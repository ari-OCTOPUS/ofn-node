# EFFECT-PATHS — BOARD 180

scope: this_host_only | method: read-only inspection of code + services

الگوی مرجع V2 §13:
observation → parser → typed event → evidence → hypothesis → policy/gate → proposal → approval → executor → external effect → receipt → verifier → learning

## مسیرهای اثرِ موجود روی 180
| path | producer → consumer | external effect? | gate/authority | idempotency | receipt |
|---|---|---|---|---|---|
| ICMP heartbeat | heartbeat.sh → state/health.json | none (observe) | L0 observe | n/a | health.json |
| afferent LAN watch | afferent → state/LAN-WATCH.json + LETTERS.jsonl | none (observe) | L0 observe | n/a | state files |
| organism heartbeat | app.py → organism.db (events/outbox/identity_ledger) | none (local db) | PROPOSE_ONLY | event_id | ledger rows |
| gateway L0 | uvicorn app:app → GET status/health | read-only serve | no command surface | n/a | http response |
| mesh bridge | octomesh_agent_bridge.py → SSH transmit → 138 | LAN message only | role+lease+ACK | idempotency_key | receipts/*.claim.json |
| telegram_letter | telegram_letter.py | POTENTIAL external | TELEGRAM_NOT_CONFIGURED (disabled) | n/a | LETTERS.jsonl (local) |

## P0 candidates (V2 §13)
| finding | present on 180? | verdict |
|---|---|---|
| cognition → executor direct | NO | 180 has no unrestricted executor; propose-only. SAFE |
| model output → external effect direct | NO | organism external_api=DISABLED, telegram not configured. SAFE |
| two parallel DBs for one truth | PARTIAL | organism.db (lab) vs ofn-l4 store; different domains, note only |
| business rule duplicated FE/BE | N/A on 180 | lead pipeline not on 180 (body_not_on_this_host) |
| permission broader than description | REVIEW | organism dual-binds LAN 8090; gateway 0.0.0.0:8780; two SSH servers → SECURITY-BOUNDARIES |

## نتیجه
هیچ مسیر cognition→external-effect مستقیم و بدون gate روی 180 وجود ندارد. تنها مسیر خروجیِ بالقوه (telegram) عملاً DISABLED است. مسیر mesh فقط پیام LAN با ACK/idempotency است، نه اثر مشتری.
