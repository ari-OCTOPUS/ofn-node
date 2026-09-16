# Manual acceptance checklist — Samsung Galaxy S23 FE

Use TEST data only (never real customers). Tick each line; anything that
fails goes back to the build session with a note.

## Install & setup

- [ ] 1. Install the APK (BUILD_AND_RELEASE §3) — app opens to Welcome.
- [ ] 2. Enter business details incl. a VALID ABN (use your real one) and
       GST registered ON, prices include GST. Save and start → Home.
- [ ] 3. Kill the app, reopen — details kept, Home shown (no re-onboarding).

## Quote workflow (the core promise)

- [ ] 4. NEW QUOTE → Add new customer → name only ("Test Customer") saves.
- [ ] 5. Describe: tap a quick-fill chip, add address "15 George St".
- [ ] 6. Price: one price **$1,100** → preview shows Before GST **$1,000.00**,
       GST **$100.00**, Total **$1,100.00** (the s 9-90 check).
- [ ] 7. Review shows Q-1001 (prefix per your settings) → Preview PDF:
       title QUOTE, your ABN formatted, customer, address, totals, terms,
       acceptance lines; multi-page OK with a long description.
- [ ] 8. SEND QUOTE → SEND WITH TELEGRAM → share sheet lists Telegram →
       send to your own Saved Messages → PDF arrives and opens.
- [ ] 9. Back in app: "What happened?" → I sent it → status Sent.
- [ ] 10. PREPARE IN GMAIL → compose opens with recipient (or asks for
       email), subject "Quote Q-1001 — …", body, PDF attached → back out
       → app state intact; check Gmail's own Drafts kept it.

## Draft safety

- [ ] 11. Start another quote, type a description, press phone Home, kill
       app from recents, reopen → "Continue where you left off" restores it.
- [ ] 12. Delete that draft from its menu → number gap accepted (next
       quote gets a fresh number, no crash).

## Invoice & payments

- [ ] 13. Open Q-1001 → CUSTOMER SAID YES → MAKE INVOICE → INV-1001
       created; quote still exists and links both ways.
- [ ] 14. RECORD PAYMENT $500 → Partly paid, owing $600.
- [ ] 15. Try paying $700 → blocked with the plain overpayment message.
- [ ] 16. Pay $600 → PAID in full message; Home unpaid count drops.
- [ ] 17. Remove a payment → back to Partly paid; history sensible.
- [ ] 18. Set an invoice due date in the past (new invoice, edit dates in
       flow) → shows OVERDUE on Home/To-do.

## Backup & restore

- [ ] 19. Settings → My data → BACK UP MY DATA → save via My Files.
- [ ] 20. Add one more customer (so state differs), then Restore from the
       backup file → warning shows backup date → confirm → app returns to
       the backed-up state; Q-1001/INV-1001/payments/PDFs all correct.
- [ ] 21. Try restoring a random non-backup file → clear rejection, no
       data change.

## Accessibility & polish

- [ ] 22. Phone Settings → Display → Font size max → all main screens
       usable, totals not clipped.
- [ ] 23. In-app Display → Extra large → same.
- [ ] 24. Dark theme → readable chips/buttons.
- [ ] 25. TalkBack quick pass on Home + share screen: buttons announce
       sensible labels.
- [ ] 26. Airplane mode: everything except AI + the moment of external
       sending works.

## AI (only if configured)

- [ ] 27. Settings → AI → enter endpoint/model/key → Test connection OK.
- [ ] 28. Share screen → Improve message → suggestion shown → Use this →
       text replaced; airplane mode → friendly unavailable message.
