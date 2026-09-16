# Shadow Reader Contract — `_ops/kernel_bridge_reader.py` (WP-D)

> **وضعیت:** implemented / shadow-ready. Default OFF.
> **Flag:** `OCTOPUS_WIRE_KERNEL_BRIDGE_READER` (default `0`).

## What this is

A read-only shadow reader inside `_ops` that reads `body_bridge/output/*.json`
artifacts and produces a structured freshness/integrity report. It is the
_first_ live `_ops` consumer of body_bridge outputs — addressing the audit
finding that body_bridge had no live `_ops` consumer.

## Contract boundary

| Rule | Detail |
|------|--------|
| Reads from | `body_bridge/output/*.json` and `*.jsonl` only |
| Writes to | `_ops/state/kernel-bridge-reader-report.json` (observability only) |
| Imports from `4d_system` | **NEVER** (AST-verified in tests) |
| Imports `kernel_consumer` | **NEVER** |
| Production decision change | **NONE** |
| Default state | OFF |
| Activation | Owner verdict only (`OCTOPUS_WIRE_KERNEL_BRIDGE_READER=1`) |

## Freshness taxonomy

| Status | Meaning |
|--------|---------|
| `fresh` | Artifact modified within `max_age_h` (default 48h) |
| `stale` | Artifact older than `max_age_h` |
| `missing` | Artifact does not exist |
| `corrupt` | Artifact exists but is unparseable |
| `incompatible` | Artifact parses but schema doesn't match expected keys |

**No status is ever converted to `healthy/empty`** — each is recorded honestly.

## Evidence ladder position

```
implemented   ✅
configured    ✅ (flag documented)
armed         — (default OFF, not armed in any current runtime)
executed      — (not executed until owner arms it)
consumed      — (report exists but no downstream decision consumer yet)
```

This is deliberately at `implemented/shadow-ready`. The activation ladder is:

```
implemented -> shadow consumed -> advisory -> decision input
```

Each step requires a separate owner verdict. This mission only delivers
`implemented/shadow-ready`.

## Wiring note

If the owner later decides to arm this reader, the wiring would go in
`_ops/wiring.py` (a reserved file — do not touch without owner verdict). The
reader is designed so it can be called from any heartbeat/tick without
modification: `kernel_bridge_reader.persist_report()`.
