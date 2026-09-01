# MP-07 — Keep the three lineages reconciled (partially done, C outstanding)

Read `00-ASK-PROTOCOL.md` first. Ask-first is mandatory.

## Problem

The triad is now half-reconciled. Lineage B entered `main` through an
owner-authorised squash, so `main` is canonical. Lineage C — the Obsidian vault
— has never been reconciled: it is a separate repository with zero merge-base,
and publication of its history is forbidden. Two export branches exist as the
sanctioned bridge, both sitting on the common ancestor and behind current
`main`. The risk register still describes the divergence at its old severity,
and the map itself is on an unmerged PR, so the canonical record of what is
canonical is not yet canonical.

## Forbidden

Force-push, graft, rebase of published history, squash-merge of a vault dump,
`--admin` bypass, pushing any vault HEAD, deleting a retention branch, and
deleting files during export (move to archive instead).

## Steps

1. Re-derive, live, for each lineage: HEAD, merge-base against `main`, and
   ahead/behind. Report the common ancestor explicitly. Do not reuse yesterday's
   numbers.
2. Report the exact file list the export would carry, the count, and whether any
   path touches vault-private trees or a private ops tree.
3. Report whether the board runtime is now behind `main`, and by which commits.
4. ASK Q1: refresh the export branch from post-merge `main`, or open a new dated
   export branch?
5. ASK Q2: does the export carry the full surgery file list, or a reduced set?
   If reduced, ask per-group, sequentially.
6. ASK Q3: does the board pull `main` in the next deploy window, and who runs it?
7. ASK Q4: the risk entry now sits between two states — what exact status string
   does the owner want recorded, and is it recorded before or after the vault
   export lands?
8. ASK Q5: retention branches are tagged and kept — does any branch get deleted
   now, or is deletion deferred indefinitely?
9. ASK Q6: the lineage map is on an open PR — merge it now so the canonical
   record is canonical, or hold?

## Expected output

A refreshed lineage map with live-derived numbers, plus a receipt of the six
answers. The map states one canonical lineage, one runtime record, and one
export-only lineage.

## Done when

All three lineages have a written, owner-confirmed relationship, and the map
lives on the canonical lineage.
