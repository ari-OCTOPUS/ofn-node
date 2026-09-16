# LIVE-TRUTH — 2026-08-27 morning (Board2 runtime, not 2026-08-24 CURRENT-TRUTH)

**Supersedes:** `F:\backup\06-EVIDENCE\OCTOPUS-OWNER-BOARD-2026-08-24\CURRENT-TRUTH.md` is NOT live SoT.
**Legs SoT:** ofn `ofn/cockpit-v2-20260827` @ `cc7a65b` (M0 read-only inventory; panel untouched). No git upstream on this branch.
**Measured:** 2026-08-27 ~10:54 AEST via ssh ari@192.168.0.138 (DietPi aarch64).

## Board2 hardware / wire
- Host: DietPi 192.168.0.138 user ari (M4 Legs Runner)
- ofn.service: active | octopus-bridge.service: active | ofn-heartbeat.service: active
- ofn-backup.service: inactive (known, not this yellow)
- Ports loopback: :8791-8794 (legs) :8796 (bridge) :8895 (hypno)
- Bridge: `e21f20d` octopus-bridge main (local dirty `connector.py`; no origin tracking)
- ofn working tree dirty: cockpit-v2 docs + `http_api.py` + `run.py` + untracked `web/cockpit-v2/`

## Open yellow (CLOSED 2026-08-27 ~10:58 AEST)
- ABD applied: `/etc/systemd/system/octopus-heartbeat.service.d/start-limit.conf` → `StartLimitIntervalSec=0`.
- Script unchanged. 3x start Result=success / ExecMainStatus=0. Timer still active (last 10:58, next 10:59 AEST).
- ofn-heartbeat left active.
- Rollback: `F:\backup\06-EVIDENCE\OCTOPUS-OWNER-BOARD-2026-08-27\ROLLBACK-octopus-heartbeat.md` (rm drop-in + daemon-reload).
- Evidence: `HEARTBEAT-ABD-2026-08-27.md` same folder.
## Lanes (Board2 only)
- Ziman: first-paid 0007 watch WAITING_EXPIRED end of 2026-08-25; do not recreate unless owner GO. 0014 stays draft.
- Studio / Nova Soles: EXPORT-WATERMARKED 9/9 SoT; FF upload gated (last KYC_BLOCKED). **No OF live from this board.**
- Painting: not in this check.
- cockpit-v2: follow this branch as legs SoT; no panel mutate from marketing.

## Failed units (out of legs path)
- ofn-assistant-update.service failed (RAG refresh)
- smartmontools.service failed (unrelated)

Status: **YELLOW** — wire+legs+bridge up; Phase-3 no upstream; octopus-heartbeat start-limit open. No secrets.

## Cycle-7 internalized runbook (2026-08-27 ~13:55 AEST)
Source: Cycle-6 INTERNAL_RUNBOOK (do not rebuild C6). Teacher copy into this existing LIVE-TRUTH. No new tree. HOLD_EXTERNAL. No send/publish. No systemctl start/enable. No BRAIN_PROVIDER flip. No secrets.

### Memory inputs
- C6: settle-138/cycle-6/ 00=59b9f5c6 01=b0343083 02=fecd6ddb 03=b3b00a87 04=c373d5a8
- C1-C5 receipts as memory. C4 Stay HOLD (Snapp contact / gallery COGS / NS-FF-08 price).

### Three lane pointers (live ofn, not a fifth store)
- Painting: ofn.service :8792 / lead.master-painting.com + /home/ari/.local/share/ofn/painting.sqlite. Quote = send_lead_quote to outbox (manual). Fugu DAY1 inbox is empty/not running. 8 sqlite rows are pilots. Vault PDFs 0100-A/0101-B unsigned. Do not contact Snapp.
- Ziman: ofn.service :8791 + /home/ari/.local/share/ofn/products.sqlite. COPY-DRAFTS 11 already APPLIED 2026-08-24 (titles/SEO). Do not regen Fugu. Do not recreate ZM-0003. Gallery cogs=0 stays UNKNOWN.
- Studio: ofn.service :8793 + /home/ari/.local/share/ofn/studio.sqlite. TG 0004-0022 skip_republish. NS-FF-01..09 wm = vault only, not on 138. KYC_BLOCKED 0/9. Do not upload. Do not bind NS-FF-08 price.

### LLM bind (three LIVE only)
- 138 127.0.0.1:8895 hypno-fugu-mini (probe 200). BRAIN_PROVIDER=fugu. DeepSeek NOT proven on this port. Leave it.
- 180 127.0.0.1:8081 octopus-llama-lab qwen3-0.6b-q4_0. Local tier only. No second llama. No ollama :11434.
- Laptop Center: _ops/cortex/model_router.py collab_chat=deepseek-v4-flash. ACTIVATION-CORTEX-PAID.flag is OFF. Do not flip BRAIN_PROVIDER.
- DEAD: hypno.service (do not start; fights :8895), /brain/ask, octopus-wire, ofn-backup, 182 no LLM.
- Code: Board2 /home/ari/ofn/ofn/helpers/brainport.py ALLOW painting|ziman|studio. Live OFN caller is RemoteBrain→fugu. Do not mint a fifth path.

OCTOPUS executes. External agents teacher only. VERIFIED_CASH is the goal.
