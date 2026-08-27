# THREE PARALLEL LANES — real inventory @ 2026-08-27T03:00:17+00:00Z (source: 138 sqlite read-only)
| Lane | Business | Real inventory | Cycle-1 task (180) | Stage | Verified cash |
|---|---|---|---|---|---|
| A | Painting | 8 leads / 44 sources / 7 channels / 1 campaign | 6b5a0753 triage+quote-skeleton | new→qualified | AUD 0 |
| B | Ziman | 40 products / 15 listing events | c2361fcc margin-rank+listing-draft | in_progress→ready | AUD 0 |
| C | Studio | 24 drafts / 22 media / 3 collections | 23281cb3 offer-package | opportunity→brief | AUD 0 |
Anti-starvation: ≥1 cycle/lane/window; ≤60% single-lane cap; P0 may pause all.
Pipelines (canonical): painting new→qualified→quote_draft→approved→contacted→won/lost→paid · ziman in_progress→…→sold→paid · studio opportunity→…→invoiced→paid
