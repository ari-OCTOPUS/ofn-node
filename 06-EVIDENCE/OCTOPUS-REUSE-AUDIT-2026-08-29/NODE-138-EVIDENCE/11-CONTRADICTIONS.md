---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, node-138, contradictions]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: en
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY/contradictions.csv]]"
---

# 11 — Contradictions

```text
observed_at=2026-08-29T05:32:32Z
scope=this_host_only
```

Inherited P2 `contradictions.csv` plus this session.

| id | left | right | plane | truth_status | source |
|---|---|---|---|---|---|
| CON-SESSION-ROLE-VS-ETH0 | Cursor rule: this session is board 180 | hostname `DESKTOP-KA9RFN5` IPv4 `192.168.0.191` | identity | CONTRADICTED | local `hostname`/`ipconfig` |
| CON-P1-RUNTIME | disk HEAD `a27eb05` | PID 1351408 started 2026-08-27 | p1 | CONTRADICTED if claimed loaded; else DOCUMENTED | git + systemd |
| CON-P1-PARENT | P2 called parent UNKNOWN/HYPOTHESIS | live parent `6881337` | p1 | RESOLVED_LIVE | `git rev-parse a27eb05^` |
| CON-VAULT-HEAD | REUSE-MAP `VAULT_HEAD=c803dee` | vault now `7d65f2d` `rescue/octopus-live-tree-20260821` | lineage | STALE tip | `git rev-parse` vault |
| CON-A27-ABSENT-VAULT | P1 documented on 138 | object absent from `F:\backup` git | lineage | DOCUMENTED | `git cat-file` |
| CON-C803-ABSENT-138 | vault family `c803dee` | not an object in `/home/ari/ofn` | lineage | LIVE_VERIFIED | 138 git |
| CON-631913DE | vault `event_store`+`command_bus` | absent on 138; must not be ported | architecture | LIVE_VERIFIED | SHA search |
| CON-USER-138 | telegram template dietpi | ofn.service ari; no TG unit | 138 | RESOLVED_TO_ARI | systemd + passwd |
| CON-ROLE-SIGNED | P2 needs signed registry | only unsigned `_NODE_ROLES` + scoped A2-001 | roles | NOT_FOUND / DISPUTED | 01 |
| CON-A2-001-VS-V2 | A2: 138 origin / 180 execute | V2: 138 commander / 180 quality-only | roles | CONTRADICTED | A2-001 vs `_NODE_ROLES` |
| CON-OWNERDECISION-UNWIRED | 12-field file on disk | `owner_decide` ignores it | p2 | LIVE_VERIFIED | node.py |
| CON-SHA-FIELD-NAMES | OwnerDecision `payload_sha` | telegram contract `payload_sha256` + `policy_sha256` | p2 | CONTRADICTED | 138-TELEGRAM-CONTRACT vs owner_decision.py |
| CON-THREE-PAYLOAD-HASHES | card vs ManualPacket vs witness | not proven equal | p2 | CONTRADICTED | P2 03 |
| CON-PACKET-RAW-TARGET | card forbids raw recipient | `owner_outbox_packet` returns raw target | p2 | CONTRADICTED | vault node.py:3160 |
| CON-TWO-TRANSMIT | PATH_A canonical | PATH_B second transmit | edge6 | DOCUMENTED | P2 04/05 |
| CON-L191-THREE-LINE | MISSING-EDGES E4 “add 3 lines” | those lines are PATH_B | edge6 | STALE | MISSING-EDGES vs Phase 0 |
| CON-NTP-RTC | vault NTP.md: no RTC battery | timedatectl shows RTC time | t5 | DISPUTED | NTP.md vs timedatectl |
| CON-TIMESYNCD | unit enabled | inactive dead; NTP=no | t5 | LIVE_VERIFIED | timedatectl + systemctl |
| CON-TOKEN-COUNT | informal “three tokens” | five `OFN_BOT_TOKEN_*` names | t1 | CONTRADICTED | config.py |
| CON-QUEUE-JS | P1 adds `owner_items` | `queue.js` reads `items` only | p1 | LIVE_VERIFIED | queue.js:59 |
| CON-COCKPIT-LINES | E0 2966 | now 3058 | p1 | LIVE_VERIFIED | wc/python |
