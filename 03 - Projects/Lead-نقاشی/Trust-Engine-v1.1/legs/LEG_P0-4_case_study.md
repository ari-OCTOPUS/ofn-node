# LEG — `case_study`
**Version:** 1.1 · **Priority:** **P1** (re-sliced 2026-07-21: P0 is funnel-only; activate after real jobs flow through the new funnel)
**Pattern source:** Upscale (suburb-named case studies), Brushworks (before/after + ROI story), Higgins (named B2B case studies)
**Type:** propose-only Leg

## Mission
Convert every completed job into reusable proof assets: a suburb-named case study, a before/after pair with a problem→solution caption, and (for pre-sale jobs) a numeric ROI story. These are the raw material of the whole Trust Factory — suburb pages, GBP posts, quote appendices, and the future PM/strata capability pack all draw from this library.

## Integration contract *(verify against repo)*
- Trigger: `job.completed` **and** (`review.received` with rating ≥ 4 **or** Owner command `/casestudy <job_id>`). Waiting for the review first means every case study can quote it.
- Emits `LegProposal(kind="case_study")` → approval card → on Approve: writes to the content
  library (`content/case_studies/`), and optionally proposes a GBP post + suburb-page block.
- Publishing anywhere public is a **separate** proposal (one asset, each placement gated).

## Input
```json
{
  "job_id": "uuid", "suburb": "", "service": "", "niche_tags": ["pre_sale","gyprock","mould"],
  "value_band": "under_2k|2k_5k|5k_10k|10k_plus",
  "photos": {"before": ["path"], "after": ["path"]},
  "owner_notes": "free text — what was the problem, what did we do, anything unusual",
  "review_quote": "string|null", "review_rating": 5,
  "presale_context": {"listed_price": null, "sold_price": null, "days_on_market": null}
}
```

## Processing steps
1. **Consent gate (hard rule):** card asks/confirms client permission status for photos.
   `photo_consent ∈ {granted_written, granted_verbal, not_asked}` — `not_asked` blocks
   publication (library-only, watermarked INTERNAL). Address is NEVER published — suburb only.
   Faces, house numbers, vehicles, distinctive identifiable features → flagged for blur.
2. **LLM composition** (prompt below) → case study markdown + captions + GBP post variant.
3. **ROI story branch:** only if `presale_context` numbers are Owner-supplied and the client
   consented to the story being told. No invented uplift figures — ever.
4. Card with full preview → Approve → asset saved with `asset_id`, tagged by suburb/niche.

## LLM prompt template (system)
```
You write proof assets for {{BUSINESS_NAME}}, a Sydney painting & maintenance business.
From the job data, produce THREE outputs:

1. case_study_md (150–250 words):
   Title: "{{Service}} in {{Suburb}} — {{outcome phrase}}"
   Structure: The problem (2-3 sentences, concrete: what the client faced, why it mattered —
   bond at risk, open home in 9 days, mould coming back every winter) → What we did (specific
   prep/system/products, days on site) → The result (finish, deadline met, review quote if
   provided). Australian English, first person plural, zero superlatives-without-evidence.
2. before_after_caption (≤ 200 chars): problem → solution, suburb named.
   Pattern: "Water-stained ceiling in {{Suburb}} — stain-blocked, re-set and repainted in a day."
3. gbp_post (≤ 1200 chars): case study compressed for a Google Business Profile post,
   ending with one CTA line ("Free fixed quotes in {{Suburb}} — {{PHONE}}").

Rules: never state the street/address; never invent numbers; if presale_context has real
figures AND consent, you may add ONE ROI sentence ("painted for ${{cost}}, sold ${{delta}}
above the agent's pre-paint appraisal") — otherwise omit entirely; quote the review verbatim
if provided, attributed as "{{first name}}, {{suburb}}".
Output JSON: {"case_study_md": str, "before_after_caption": str, "gbp_post": str,
"suggested_tags": [str]}
```

## Telegram approval card
```
📸 CASE STUDY — {{suburb}} · {{service}} · {{value_band}}
Photo consent: {{photo_consent}} {{"⚠️ publication blocked" if not_asked}}
── Preview ──
{{case_study_md | truncate 400}}
Caption: {{before_after_caption}}
[✅ Save to library] [✅+📍 Save + propose GBP post] [✏️ Edit] [🗑 Skip]
```

## Asset library contract
```
content/case_studies/{{asset_id}}.md     (front-matter: suburb, niche_tags, value_band,
                                          consent, created_at, source_job_id)
content/photos/{{asset_id}}/before|after (blur-checked)
```
Consumers (later legs read, never regenerate): Suburb-Page Factory (P1), GBP-Post agent (P1),
Quote-Draft appendix ("recent work near you" — top 2 same-suburb assets), PM/strata capability
pack (P1 B2B), website gallery.

## Outcome recording
`record_proposal_outcome(proposal_id, outcome ∈ {saved, saved_and_gbp_proposed, skipped}, meta:{asset_id, suburb, niche_tags})`
Long-loop learning: when a future lead mentions seeing the work ("saw your Mosman job"),
Owner tags `/lead ... source=case_study` — closes the proof→lead attribution loop.

## KPIs
- assets/month vs jobs/month (target: ≥ 60% of jobs yield an asset)
- suburb coverage: # target suburbs with ≥ 2 assets (feeds suburb-page readiness)
- attributed leads mentioning proof assets

## Failure modes & guards
- No usable photos → text-only case study allowed, flagged `no_visual` (lower priority for
  publication; card suggests photo protocol reminder for next job).
- Duplicate asset for job_id → idempotent, version bump.
- Consent uncertain → default INTERNAL. The library must never be the thing that burns a client
  relationship.

## Compliance notes
- Privacy: publish suburb-level only; no addresses, no identifiable interiors without consent,
  metadata (EXIF GPS) stripped by the photo effector before save.
- ACL: ROI claims only with real, client-consented figures; review quotes verbatim, never
  edited for favourability.
