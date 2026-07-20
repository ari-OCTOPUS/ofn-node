# Gmail — Level 1 compose (implemented) & Level 2 drafts (researched only)

## Level 1 — "Prepare in Gmail" (SHIPPED, D-011)

flutter_email_sender fires an email intent with recipients, subject, body
and the PDF attached; on the S23 FE the default mail app (Gmail) opens its
compose screen fully filled. The user presses Send — or backs out, in
which case **Gmail itself** may keep its own draft.

- Missing customer email → bottom sheet asks for it, optional
  "Remember it for this customer" writes it back to the record.
- Any intent failure → automatic fallback to the system share sheet.
- Truthful wording everywhere: the button is **"Prepare in Gmail"**, never
  "Saved to Gmail Drafts"; outcome recorded is `prepared`, and only the
  user's "I sent it" marks the document sent. The app cannot verify
  sending, delivery, or Gmail's draft behaviour — and never claims to.
- Works offline up to the compose screen; sending is Gmail's business.

## Level 2 — true Gmail API drafts (NOT implemented; research summary)

Creating a real Draft in the user's Gmail account requires: internet at
creation time, a Google Cloud project with the Gmail API enabled, an OAuth
consent screen, an Android OAuth client bound to the app's SHA-1 +
package id, the `gmail.compose` scope, secure token storage + refresh/
revocation handling, and an RFC 2822/MIME message with the PDF as a
base64 part. For a personal install the consent screen can stay in
testing mode with the owner as a test user; wider distribution triggers
Google verification.

Decision: out of MVP. It adds a Google dependency, online-only behaviour
and OAuth maintenance for marginal benefit over Level 1 (Gmail already
keeps its own drafts on back-out). If wanted later: keep it strictly
behind an off-by-default "Optional online features" toggle with a plain
explanation, official OAuth only (no password entry), narrowest scope,
`Disconnect Gmail` wiping tokens from secure storage, and zero impact on
offline operation. No fake `.eml` shortcut will be labelled as a Gmail
draft.

## Setup the OWNER must do for Level 2 (if ever requested)

1. Google Cloud project → enable Gmail API. 2. OAuth consent screen
(testing) + owner as test user. 3. Android OAuth client id with app
SHA-1 + package id. 4. Rebuild with the integration enabled. These steps
cannot be done by the app itself and are why Level 2 is a deliberate,
separate project.
