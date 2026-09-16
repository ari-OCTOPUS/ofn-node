---
type: ops-pointer
status: active
created: 2026-08-11
updated: 2026-08-11
tags: [octopus, collaborator, pointer]
---

# INTERACTION-CONTRACT — pointer

> **Canonical source of truth:**
> [[06 - Architecture Maps/OCTOPUS-COLLABORATOR-INTERACTION-CONTRACT|OCTOPUS-COLLABORATOR-INTERACTION-CONTRACT]]
>
> Related: [[_ops/DISCOVERY-PROTOCOL|DISCOVERY-PROTOCOL]] · [[_ops/CAPABILITY-JOURNAL|CAPABILITY-JOURNAL]] ·
> [[00 - Inbox/2026-08-11 SESSION — Talk Discovery ARMED|SESSION ARMED]]
>
> **Live status (2026-08-11):** Talk Discovery code is on live `_ops` and flags are **ARMED**
> (`OCTOPUS_WIRE_COLLAB=1`, `OCTOPUS_COLLAB_USE_MODEL=1`, cap=20). Collaborator is the default
> MiniApp reply path when COLLAB is on — **draft only, no external effect**.

```text
shared-collab-brain ARMED + discovery-facade + draft-only
# INTERACTION-CONTRACT — pointer

> **Canonical source of truth:**
> [`06 - Architecture Maps/OCTOPUS-COLLABORATOR-INTERACTION-CONTRACT.md`](../06%20-%20Architecture%20Maps/OCTOPUS-COLLABORATOR-INTERACTION-CONTRACT.md)
>
> Do not duplicate routing tables here. Runtime code and tests should cite the map above.
> Talk Discovery / discovery loop: see also `DISCOVERY-PROTOCOL.md` and `CAPABILITY-JOURNAL.md`.

```text
shared-collab-brain + honest-photo + discovery-journal + capped-collab-chat
!= vision != money-live != unbounded-model != auto-arm
```
