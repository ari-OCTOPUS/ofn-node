---
type: architecture-note
lane: D-S0-HUNT
measured_at: 2026-09-03T20:34:54+10:00
vantage: this_host_only
host: DESKTOP-KA9RFN5
asserted_ip: 192.168.0.191
ip_source: Get-NetIPAddress Wi-Fi
scope: this_host_only
claim_type: observation
owner_pick: "آشپزخانهٔ خاموش — harvest جدا از ofn.run"
accounting: not_done
started: none
---

# Harvest vs `ofn.run` — kitchens stay off the dining room

Lane: **D-S0-HUNT**. This laptop (`DESKTOP-KA9RFN5` / Wi-Fi `192.168.0.191`). Not board 180. No fetch, no start, no flag, no accounting.

Probe receipt: `09-LANES/D-S0-HUNT/receipts/harvest-boundary-20260903T1033Z.json` (`measured_at_utc` `2026-09-03T10:34:54Z`).

```yaml
arbiter:
  node_id: laptop-vault / DESKTOP-KA9RFN5
  asserted_ip: 192.168.0.191
  vantage: this_host_only
  scope: this_host_only
  claim_type: observation
```

## 1. Are kitchens wired into `ofn.run`?

**No.** `F:\ofn-node\ofn\run.py` does not import harvest / imap / buynsw.

| claim | value | source |
|---|---|---|
| AST imports in `run.py` | **55** | probe `run_py.import_count` |
| hits matching `harvest` / `imap` / `buynsw` / `ofn.agents` | **[]** · `wired_into_run=false` | same receipt |
| `run.py` bytes | **28701** | `Get-Item` this session + probe |
| `marketing_run.py` | imports `build_node` from `.run` only — no harvest | `F:\ofn-node\ofn\marketing_run.py` lines 31–32 |
| docs vs code | `OFN-LOCAL-ARCHITECTURE.md` §1.1 / §3 also said not imported | **agree** |

Callers that *do* import harvest modules (not `ofn.run`): `tests/test_demand_harvest.py`, `tests/test_h1_harvest.py`, `tests/test_h1_buysw.py`, `tests/test_nsw_ocp_harvest.py`, `tests/test_seek_harvest.py`, `tests/test_h1_buysw_dom.py`, `tools/ingest_buynsw_batch.py` → `h1_buysw_dom`, `ofn/agents/rate_card_builder.py` → `nsw_ocp_harvest.is_painting_award`. Source: grep `from ofn.agents` this session.

`02-AGENT-CONTRACTS.yaml` lists harvest files as A2_research **modules**. That is a contract map, not an import edge into `ofn.run`. Not treated as a wiring claim.

## 2. DEAD SOURCE labels (real code)

Exact docstring label **DEAD SOURCE** on four agent files. Other hits are vocabulary / receipts. Full line list: probe `dead_source_hits` (**14** hits / **9** files).

| path | one line |
|---|---|
| `F:\ofn-node\ofn\agents\demand_harvest.py` | `DEAD SOURCE — labeled 2026-09-02 (D-31 step 1).` |
| `F:\ofn-node\ofn\agents\h1_harvest.py` | `DEAD SOURCE — labeled 2026-09-02 (D-31 step 1).` |
| `F:\ofn-node\ofn\agents\h1_buysw.py` | `DEAD SOURCE — labeled 2026-09-02 (D-31 step 1; 4th candidate, D-34 §B-4).` |
| `F:\ofn-node\ofn\agents\nsw_ocp_harvest.py` | `DEAD SOURCE (as a lead module — the upstream itself is alive; see below)` |
| `F:\ofn-node\docs\octopus-os\02-AGENT-CONTRACTS.yaml` | `dead_source_labels: … h1_buysw/h1_harvest/demand_harvest + nsw_ocp parked` |
| `F:\ofn-node\docs\octopus-surgery\governance\2026-09-02\receipts\DEAD-SOURCE-LABELS-20260902.json` | D-31 step 1 receipt of those four labels |
| `F:\ofn-node\ofn\kernel\source_health.py` | kernel vocab: dead source → `UNKNOWN` (not the D-31 label) |
| `F:\ofn-node\tests\test_chaos_owner_absent.py` | `test_dead_source_classifies_unknown` |
| `F:\ofn-node\docs\octopus-surgery\architecture\2026-09-02\receipts\HALT-CHAOS-20260902.json` | cites `source_health` vocab |

`seek_harvest.py` and `h1_buysw_dom.py`: **no** DEAD SOURCE label (probe). Receipt JSON says seek was left unlabeled on purpose.

## 3. What `demand_harvest` *would* do (code only — not run)

`ofn/agents/demand_harvest.py` **13259** B (`Get-Item` this session). No `if __name__ == "__main__"` (probe `has_dunder_main=false`). Importing the file defines functions; it does not start a loop.

If a caller invoked `cycle()` with the default `fetch`:

| field | value | source |
|---|---|---|
| local bind / listen | **none** | probe `bind_or_listen_lines=[]` `port_literals=[]` |
| wire / harvest flags in this file | **none** | probe `flag_names=[]`; `OCTOPUS_WIRE_HARVEST` has **zero** `.py` hits under `F:\ofn-node` (grep this session) |
| default GET | `https://tenders.nsw.gov.au/?event=public.api.tender.search` | `cycle()` default `url=` line 260 |
| timeout / retries | `TIMEOUT_S=20` · `MAX_RETRIES=3` | lines 45–46 |
| 403 | `HarvestError` → cycle returns `PARKED` | `fetch_json` / `cycle` |
| USER_AGENT | `octopus-demand-harvester/1.0 …` | line 44 |
| needs from caller | `fetch`, `existing_ids`, `create_lead`, optional `notify` | `cycle()` signature |

`buynsw-harvester/` is a Chrome MV3 folder (**8** files, probe). Default `autoPost` off (`tools/buynsw-harvester/README.md`). File ingest = `tools/ingest_buynsw_batch.py` → `h1_buysw_dom.ingest_batch`. **Not** `ofn.run`.

## 4. 8791 — three tenants, `resolution: null`

Do not collapse.

| tenant | body | source | status |
|---|---|---|---|
| this-host live `.191` | `tools/buynsw-harvester/ingest_server.py --port 8791 --allow-no-auth` | `09-LANES/B-PULSE-IMAP/FOUR-SHELLS-MAP.md` §2–3 (listen `2026-09-03T10:22:37Z`) | FILE_VERIFIED prior B; **not re-listened** this session |
| code-intended ziman | `ofn.run` `ports["ziman"]=8791` | `F:\ofn-node\ofn\config.py` line 283 | FILE_VERIFIED this session |
| 138 | `python3 -m ofn.run` on `127.0.0.1:8791` | B `SSH-RO-RECEIPT.md` / listen-138 `2026-09-03T09:32:05Z` | FILE_VERIFIED prior B; **no SSH** this session |
| this `F:\ofn-node` tree | `ingest_server.py` **absent** (3 candidate paths) | probe `ingest_server_in_tree=false` | verified |

Same port number, three stories. `status: open`.

## 5. Not done

No `ofn.run`, no `demand_harvest`, no ingest_server, no extension start, no fetch, no flag, no bind, no commit, no accounting.
