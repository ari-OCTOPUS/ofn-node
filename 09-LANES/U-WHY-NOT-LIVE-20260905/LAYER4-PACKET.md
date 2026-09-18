---
type: note
status: channel_selected
live_effect: closed
telegram_gate: recorded_no_send
requires: owner_only_if_outbound_send
may_authorize: false
tags: [octopus, layer-4, channel-selection, this-host-only]
created: 2026-09-05
updated: 2026-09-05
lane: U-WHY-NOT-LIVE-20260905
live_organism_claim: false
---

# Layer 4 packet — mesh channels selected; live-effect still closed

`status: channel_selected` · `live_effect: closed` · `may_authorize: false`

Machine receipt: `LAYER4-CHANNEL-SELECTION.json`  
Handoff: [[07-HANDOFF/U-LAYER4-CHANNEL-SELECTION-2026-09-05]]  
Prior one-gate packet (outbound still closed): [[07-HANDOFF/U-LAYER4-ONE-GATE-2026-09-05]]

This packet does **not** open a gate. No send. No env wire exported to `1`. Quality brain, `PROPOSE_ONLY`.

```yaml
arbiter:
  node_id: laptop-vault / DESKTOP-KA9RFN5
  asserted_ip: 192.168.0.191
  vantage: ssh_local_forward_from_laptop_191
  scope: this_host_only plus node138 via tunnel
  claim_type: observation
  not_node180: true
  evidence:
    - 09-LANES/U-WHY-NOT-LIVE-20260905/LAYER4-CHANNEL-SELECTION.json
    - 09-LANES/U-WHY-NOT-LIVE-20260905/LAYER3-RECEIPT.json
    - 09-LANES/U-WHY-NOT-LIVE-20260905/LAYER2-COMPLETE.json
    - F:/ofn-node/ofn/config.py:294
```

## Owner delegated the pick (2026-09-05)

Owner: «همه چیو از قبل داخل برد 138 ساختم خودت کانالاشو انتخاب کن».

That sentence **delegates channel naming** among things already built on board 138. It is **not** a GO to send, lift `HOLD_EXTERNAL`, or pick Telegram vs live OF vs paid ads.

This lane named the already-proven 138 loopback legs. It did **not** invent a broker, MiniApp, or outbound product.

## What was selected (operational mesh)

All five 138 loopback services that Layer 2/3 already proved healthy. Source: `F:/ofn-node/ofn/config.py:294` (`ports={"ziman": 8791, "lead": 8792, "studio": 8793, "owner": 8794}`) plus `LAYER2-COMPLETE.json` (`8796` = `octopus_bridge.run`, not `ofn.run`).

| selected | remote (138 loopback) | family | day-to-day |
|---|---|---|---|
| ziman | `127.0.0.1:8791` | `ofn.run` | **primary** |
| lead | `127.0.0.1:8792` | `ofn.run` | mesh |
| studio | `127.0.0.1:8793` | `ofn.run` | mesh |
| owner | `127.0.0.1:8794` | `ofn.run` | mesh |
| octopus_bridge | `127.0.0.1:8796` | `octopus_bridge.run` (not ofn) | **primary** |

**Primary pair:** ziman (`8791`) + octopus_bridge (`8796`). Default rule unless ofn config or L2/L3 receipts showed another intended primary. No contradiction found (`resolution: null`, no open port-map fight).

Laptop `127.0.0.1:8791` is harvest ingest PID `2324` (`LAYER3-RECEIPT.json` + listen table this session). That is **not** the selected ziman channel. Selected ziman is **138** `8791`, reached here as `127.0.0.1:18791`.

## Tunnel health this hour (GET only)

Existing Layer 3 tunnel reused. ssh PID `26364` still listening on `127.0.0.1:18791-18794,18796` (Get-Process / Get-NetTCPConnection `2026-09-05T16:08:19+10:00`). No new SSH. No `0.0.0.0`.

`GET /healthz` `2026-09-05T16:08:32+10:00` (`LAYER4-CHANNEL-SELECTION.json`):

| remote | local forward | http | ok | n (body length) |
|---|---|---|---|---|
| 8791 ziman | 18791 | 200 | true | 12 |
| 8792 lead | 18792 | 200 | true | 12 |
| 8793 studio | 18793 | 200 | true | 12 |
| 8794 owner | 18794 | 200 | true | 12 |
| 8796 bridge | 18796 | 200 | true | 38 (`name=octopus-bridge`) |

No POST. No send.

Grade: **E3** for five-port tunnel `/healthz` this hour. **E0** for live-organism / outbound effect.

## What was not selected (external-effect class)

Telegram, live OF, and paid ads were **not** selected as the Layer-4 live-send channel. They are a different class.

One-by-one Q1 (`2026-09-05T16:16:37+10:00`): owner chose `open_record` for **Telegram cards only**. Receipt: `Q1-TELEGRAM-GO.json` · [[07-HANDOFF/U-LAYER4-TELEGRAM-GATE-2026-09-05]]. **Send still false.** Wires unchanged.

`01-TRUTH/SEASON-5-2026-09-04.md` still says `HOLD_EXTERNAL` is true for Telegram / live OF / paid ads. That disagreement is `status: open`, `resolution: null` — Season 5 was not rewritten.

This turn does **not** ask the owner to pick among those three. Mesh pick is done. Outbound remains HOLD until a **later** named GO (below). That later sentence is **not** this turn.

Painting-draft winner: **not declared**. No 138 ledger evidence for revenue / sent / booking. This packet writes none of those tokens.

## Still closed

- `HOLD_EXTERNAL`
- `auto_email`
- every `OCTOPUS_WIRE_*` / `OFN_WIRE_*` / `OBSERVATORY` / `CORTEX_HYPOTHESIS`
- D1, D7, `OWNER_KEY`
- wholesale `_ops/OCTOPUS-flags.cmd` and `RUN-ORGANISM.bat`
- first external-effect row on the 138 ledger (not written here)

`AGENTS.md` §4: blocked is a decision. «همرو باز کن» remains too broad for outbound. This delegation only named mesh legs.

## One-line GO needed later — if the owner wants real outbound

Do **not** treat this turn as that GO.

```
OWNER DECISION — LAYER4 2026-09-05: I lift HOLD_EXTERNAL for exactly one outbound channel: <Telegram | live OF | paid ads>. I open only that named gate. OCTOPUS-flags.cmd stays closed. auto_email and OCTOPUS_WIRE_LEAD_OUTBOUND stay 0. First effect records only on the 138 ledger.
```

Until that sentence exists with one outbound channel named, live-effect stays closed. Mesh selection does not substitute for it.

## Capability blockers (unchanged)

| id | state | source |
|---|---|---|
| SIG-IV | `PENDING` | `09-LANES/N3V2-MATH-20260905T031103Z/LANE-REPORT.md`; `CLOSEOUT-RECEIPT.json` |
| Memory Gate B | `CLOSED` (`H1_STRONG_FAIL`) | `CLOSEOUT-RECEIPT.json` `memory_gate_b: CLOSED` |

These are not opened by channel naming. Live-organism claim remains **E0**.

## Not executed

Flags, send, bind `0.0.0.0`, harvest kill, `ofn.service` restart, new 138→180 tunnel, 180 password guesses, commit/push, N3V2 math mutate.
