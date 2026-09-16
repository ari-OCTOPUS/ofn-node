> CANONICAL (owner forever): Master Painting→lead; Ziman/Maliheh gifts→ziman (NOT painting); Studio/OF/Saba→studio; Mining DEFERRED.
> See [[60-BOARD2-CANONICAL-BUSINESS-MAP]].
# Board2 Legs VERIFY MAP â€” 2026-08-22

Source: live DietPi `192.168.0.138` + `/home/ari/ofn/INDEX.md` + runtime `ofn.service` environ (secrets redacted).  
Rule: no guess â€” only config hosts, INDEX table, healthz, gate/flags.

## VERIFY TABLE

| Surface | Mapped business (evidence) | Live? | Stub / gap (evidence) |
|---|---|---|---|
| **lead** `:8792` `lead.master-painting.com` | **A) Master Painting lead-gen CRM** (INDEX: Â«Ù„ÛŒØ¯ Ù†Ù‚Ø§Ø´ÛŒÂ») | YES healthz 200; bot token present in runtime env; partner+owner ids present | INDEX: CRM largely built; remaining gaps documented under Â«Ù„ÛŒØ¯ Ù†Ù‚Ø§Ø´ÛŒ â€” Ú©Ø¬Ø§ ÙˆØµÙ„ Ù†ÛŒØ³ØªÂ» / HANDOFF â€” not re-invented here |
| **ziman** `:8791` `ziman.master-painting.com` | **GiftMesh Sydney brand line** on tenant `ziman` (INDEX D-25) â€” **NOT** Master Painting painting | YES healthz 200; bot token present | INDEX: GiftMesh corpus missing â†’ research pilot blocked; first real user historically on this leg |
| **studio** `:8793` `studio.master-painting.com` + `app.master-painting.com`â†’studio | **B) Studio (Saba) lane** (INDEX: Ø§Ø³ØªÙˆØ¯ÛŒÙˆ/Ø³Ø¨Ø§; `/sabaapp`) â€” OF/studio portfolio | YES healthz 200; studio+partner tokens present | INDEX: Â«Ø§Ù†ØªØ´Ø§Ø± Ù‡Ù†ÙˆØ² Ù‚ÙÙ„Â»; `OFN_WIRE_PUBLISH=1` but `wire_outbound` still in `OFN_EXTRA_CLOSED_GATES`; owner-open token `live_publish` absent from closed list but outbound still closed |
| **panel** `:8794` `panel.master-painting.com` | Owner control panel (not a customer business) | YES healthz 200; owner bot token present | Observability/ops surface |
| **ofn.service** | Node process hosting legs | active | Not a business |
| **hypno-fugu-mini** `:8895` | Adjacent miniapp (INDEX: hypno-fugu-mini; config comment points hypno mini app / Saba path split) | unit **active**; `/healthz` â†’ **404** (listen yes, that path not ok) | INDEX: `hypno` tenant exists in packs without OFN WebApp portfolio scope (D-25) |
| **ofn/wire** | Git boardâ†”Windows channel | ls-remote OK `@ ca038d42a1f2` | â€” |

### Owner-open gate tokens vs reality
Absent from closed list: `fee_payment`, `auto_payment`, `live_email_send`, `live_publish`.  
Still closed (among others): `wire_outbound`, `auto_email`, `auto_post`, `auto_dm`, `auto_scrape`, tenders/vendors/portal/terms.  
Flags: `OFN_WIRE_EMAIL=1`, `OFN_WIRE_PUBLISH=1`, `OFN_WIRE_OUTBOUND=0`, `OFN_PUBLIC_CATALOG=1`, commerce routes/webhook **off**.  
Honest read: opening those four EXTRA tokens â‰  paid rails live; commerce flags still false; outbound wire still closed.

## PARALLEL PLAN (draft only â€” NO execute until ari GO)

### Lane Painting + Lead (`lead` primary; painting CRM)
Reversible next 3 (propose only):
1. Read-only inventory of lead CRM gaps cited by INDEX/HANDOFF (endpoints + empty states) â†’ evidence note
2. Dry-run / panel observability check for lead priority + actionable outbox counts (no customer send)
3. One reversible wiring prove: catalog/public read path already flagged `OFN_PUBLIC_CATALOG=1` â€” document response shape only

### Lane Studio / OF (`studio` + hypno-fugu-mini)
Health + automation ONLY (DEFAULT):
1. Document publish lock chain: INDEX lock + `wire_outbound` closed + dry_run defaults in platforms
2. hypno-fugu-mini: confirm listen `:8895` and non-`/healthz` health path if any (no content post)
3. Automation wiring map: outbox approveâ†’publish path remains dry-run unless owner second confirm â€” no live posts / no audience msgs / no content invent

### Other
- `ziman`/GiftMesh: keep healthy; corpus gap = note only unless owner opens GiftMesh work
- `panel`/`ofn`: keep healthy

## READY_FOR_GO?

**READY_FOR_GO (narrow):** Painting+Lead reversible actions **#1â€“#3 above** may proceed when ari sends GO.  
**Studio/OF:** NOT ready for content/publish GO â€” verify/health/automation wiring only until explicit owner order.  
**Blocked for paid/live blast:** `wire_outbound` closed; commerce routes/webhook off; no invent money/OF content.

## Evidence
This folder + runtime scan `ts_utcâ‰ˆ20260822T121123Z`.