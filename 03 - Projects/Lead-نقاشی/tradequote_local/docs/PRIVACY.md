# Privacy

## Where data lives

All business data — customers, quotes, invoices, payments, settings,
audit history — is stored **only on the phone**, in the app's private
storage. There is no account, no server, no analytics, and the app never
transmits data on its own.

## What ever leaves the phone, and when

| Action | What leaves | Where it goes |
|---|---|---|
| Send with Telegram / More options | The PDF + your message | The app YOU pick in Android's share menu |
| Prepare in Gmail | Recipient, subject, body, PDF | Your mail app's compose screen (sending is your tap) |
| Save PDF / Save backup | The file | The location YOU pick (phone, SD, or Drive if you choose it — Drive uses internet at that moment) |
| AI "Improve message" (OFF by default) | Only the message text, only when you tap the AI button | The AI service YOU configured in Settings |

Nothing else. No background sync, ever.

## AI assistance specifics (D-012)

- Disabled by default; enabling requires the owner to enter their own
  service address, model and key in Settings.
- Sent per tap: the draft message text plus a fixed instruction. Customer
  records, invoices, ABNs and financials are **not** sent.
- Responses are suggestions shown for review; nothing is saved without an
  explicit "Use this message".
- "Disconnect AI and delete key" wipes the stored key immediately.
- Whether the AI provider retains inputs is governed by THAT provider's
  policy — the owner should check it; the app cannot control it.

## APP (Australian Privacy Principles) context

A sole-trader/small Pty Ltd holding its own customer contact details
locally is handling ordinary business records. This app helps by: not
duplicating data to third parties, keeping records accurate and
retrievable (backups), and never selling or sharing data. If the business
grows into APP-covered territory, professional privacy advice applies —
this document is not legal advice.

## Data deletion

Deleting the app deletes the local data (Android removes app-private
storage). Backup files the owner exported remain wherever they were saved
and should be deleted separately if required.
