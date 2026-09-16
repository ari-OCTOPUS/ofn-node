# Channel Map (scaffold)

> **Empty by design.** This file is populated by the **Phase 2 read-only scanner**
> (spec §13), which infers channels from file paths, wikilinks, backlinks, tags,
> frontmatter, repeated entities, and graph centrality. Until then it only documents
> the schema. The scanner never writes here directly — it emits the map as an
> `ActionProposal` through B6 for owner approval.

## Channel record schema (spec §13)

```yaml
channel_id: ch_project_people_001
type: explicit | inferred | risky | orphan | dead
from: "09 - People"
to: "03 - Projects"
evidence: [shared_person_name, backlinks, telegram_mention]
confidence: 0.72          # 0.0–1.0
risk_level: low | medium | high | critical
recommended_action: "formalize handoff channel"
```

## The eight latent channels to formalize (spec §5)

These are the human-named channels the scanner will look for first:

1. `Inbox → SuperBrain` — everything raw normalizes through B1 before Projects/Knowledge.
2. `PROJECT` hub → `PROJECT_INDEX / PROJECT_GRAPH / PROJECT_STATUS_BOARD`.
3. `Chronos → Projects` — time/energy/priority gates project work.
4. `Architect → AgentOps` — every architecture change passes through NBB (B6).
5. `Knowledge → Projects` — knowledge becomes an Evidence Packet, not an archive.
6. `People → Projects` — each person linked to project / context / last-interaction.
7. `Ops → Dashboard` — the dashboard feeds from real trace, not vibes.
8. `Memory promotion` — raw → episodic → semantic → candidate → approval → canonical.

## Discovered channels

_(none yet — Phase 2 will append here, via an approved proposal)_
