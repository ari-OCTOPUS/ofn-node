---
type: log
status: active
created: 2026-08-11
updated: 2026-08-11
tags: [octopus, cognitive-unify, talk-discovery, shadow]
aliases: [Cognitive Unify]
---

# SESSION — Cognitive Unify (UI + Discovery + Policy)

## Done (owner order)

1. **Default UI** — وقتی `OCTOPUS_WIRE_COLLAB=1`، chip پیش‌فرض 🤝 همکار؛ Ask و آینه فقط صریح.
2. **Discovery facade** — `discovery_facade.discover_reply_text()` با provenance (catalog / dark+journal / World Discovery).
3. **Truth sync** — ADR-023 → Live ARMED؛ pointer به‌روز؛ `SPEC_NOT_BUILT` برای vision/send/OTLP-live/C_t-gating.
4. **CriticalityV2** — SHADOW-only؛ `spectral_heuristic` صریح؛ بدون gate به قلب/router.
5. **Pulse shadow compare** — divergence JSONL پشت `OCTOPUS_WIRE_PULSE_ARBITER_SHADOW` (پیش‌فرض OFF).
6. **TalkDiscoveryPolicy** — draft مجاز؛ EXTERNAL_SEND حتی با approval ممنوع.
7. **Approval SM** — fail-closed؛ hash verify قبل از EXECUTING؛ بدون Redis.

## Invariant

Collaborator = پیش‌فرض **پاسخ draft** · نه مسیر اثر خارجی.

## Tests

`test_cognitive_unify.py` 9/9 · `test_talk_discovery.py` سبز.

## Docs

[[03 - Projects/research-spec-compiler/adr/ADR-023-octopus-collaborator|ADR-023]] ·
[[06 - Architecture Maps/OCTOPUS-COLLABORATOR-INTERACTION-CONTRACT]] ·
[[_ops/DISCOVERY-PROTOCOL]]
