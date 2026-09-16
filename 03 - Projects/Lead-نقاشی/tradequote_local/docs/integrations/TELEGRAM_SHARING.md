# Telegram sharing (D-010)

## What the app does

"SEND WITH TELEGRAM" saves the PDF to an app-private cache, then opens the
**Android system share sheet** via share_plus 13
(`SharePlus.instance.share(ShareParams(files: [XFile(pdf, mimeType:
'application/pdf')], text: message))`). The user taps Telegram in the
sheet, picks the chat, and sends. share_plus provides the content:// URI
through its own FileProvider — no storage permissions, no manifest edits.

## Why the share sheet, not a direct Telegram intent

- share_plus 13 exposes no per-package targeting; a hand-rolled
  `Intent.setPackage("org.telegram.messenger")` breaks on Telegram
  variants (Telegram X, web-based forks), needs Android 11+ package
  visibility `<queries>` entries, and its own FileProvider wiring.
- The share sheet is the standards-based path Samsung One UI optimises
  (recent-contact targets appear at the top, often making it FEWER taps).
- The button's subtitle sets expectation: "Your phone's share menu will
  open — tap Telegram."

Upgrade path (phase 2, optional): android_intent_plus with
`ACTION_SEND` + `setPackage` + `<queries>` for the two main Telegram
package ids, falling back to the sheet. Documented, not required.

## Honesty rules (invariant 6)

- Opening the sheet proves nothing about delivery. The recorded outcomes
  are: prepared → shareSheetOpened | cancelledOrUnknown | failedToOpen.
- After returning, the app asks "What happened?" — only "I sent it"
  marks the document sent (manuallyConfirmedSent + status change).
- If no app can handle the intent: plain-language error, document stays
  safe, "More sharing options" offered.

## No Telegram API

No bot, no api key, no server, no upload to any third party — the PDF
goes directly from app cache to the app the user picks.
