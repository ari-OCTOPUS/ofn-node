# NEXT AGENT PROMPT — Project-F Obsidian Structure v1

Workspace:

```text
C:\Users\Armin\Desktop\پازل هشت پا
```

Target:

```text
03 - Projects\اونلی فنز
```

## Mission

Continue Project-F Obsidian structuring safely. The previous agent created a numbered Obsidian folder skeleton and index files, but did **not** move existing files.

## Read first

```text
_memory/protocols/GRAPH-SEARCH-PROTOCOL.md
_memory/graph/SCHEMA.md
_memory/agents/privacy-steward.md
03 - Projects/اونلی فنز/HOME.md
03 - Projects/اونلی فنز/INDEX.md
03 - Projects/اونلی فنز/RUNBOOK.md
03 - Projects/اونلی فنز/REGISTRY.md
03 - Projects/اونلی فنز/VERDICT_QUEUE.md
03 - Projects/اونلی فنز/00 - Control/OBSIDIAN-STRUCTURE-v1.md
```

## Hard containment

- Outside Project-F folder use only alias `Project-F`.
- Do not echo identity/platform/media/private content.
- Do not read/summarize PII unless strictly needed and local-only.
- No outward action: no publish/send/spend/account/deploy/run.

## Current created folders

```text
00 - Control
01 - Strategy
02 - Research
03 - Experiments
04 - Content Studio
05 - Acquisition
06 - Ops & Runtime
07 - Compliance & Privacy
08 - Partner (PII)
09 - Archive
```

Each has `_INDEX.md`.

## Next safe tasks

1. Validate all new wikilinks from `HOME.md` and `INDEX.md` resolve.
2. Update `VERDICT_QUEUE.md` with `PF-STRUCT-V1` if not present.
3. Create `03 - Experiments/EXPERIMENT-REGISTER.md` using content-free schema.
4. Create `07 - Compliance & Privacy/BOUNDARIES.md` as a hard-rules summary.
5. Do not move files until owner verdict.

## Owner verdict needed

Ask:

```text
PF-STRUCT-V1: انتقال واقعی فایل‌ها طبق OBSIDIAN-STRUCTURE-v1؟
گزینه‌ها:
A) yes-all
B) yes-docs-only-not-code
C) no-keep-flat
D) later
```

Recommended default: `B`.

## End of run

Append memory event to `_memory/execution/runs.jsonl`, then write next prompt if continuing.
