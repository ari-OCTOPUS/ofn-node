# AI assistance ("Fugu API") — setup & data flow

The owner stated they have a real AI API (referred to as "Fugu"); its
endpoint/key were NOT embedded anywhere — they are entered at runtime.
The core app is 100% functional with AI off or unreachable (D-012).

## In-app setup (Settings → Optional online features → AI assistance)

1. Toggle **AI assistance** on.
2. **Service address** — the base URL, e.g. `https://api.fugu.example/v1`.
3. **Model name** — whatever the service expects.
4. **API key** — stored ONLY in flutter_secure_storage; never in the
   database, prefs, backups, logs or Git.
5. **Test connection** — sends a fixed two-word probe and reports
   success/failure in plain language.
6. **Disconnect AI and delete key** — immediate wipe + features off.

## Wire protocol (lib/services/ai/ai_service.dart)

The adapter speaks the OpenAI-compatible chat shape most gateways accept:

```
POST {endpoint}/chat/completions
Authorization: Bearer {key}
{"model": "...", "messages": [{"role":"system",...},{"role":"user",...}],
 "temperature": 0.4}
→ choices[0].message.content
```

`/chat/completions` is appended unless the endpoint already ends with it.
If Fugu speaks a different protocol, implement a second `AiService._chat`
variant — the rest of the app only calls `improveMessage()` /
`testConnection()`, so the swap is one file.

## Feature shipped in v0.1.0

**Improve message** on the share screen (visible only when configured):
sends the draft Telegram/Gmail message text + a fixed system instruction;
shows the suggestion beside "Use this message / Keep my message"; nothing
is applied without the user's tap. Failures (offline, bad key, timeout
20 s) show: "This feature is not available right now. You can enter the
information manually."

## Data rules (also in PRIVACY.md)

Only the message text is sent, only on tap. No customer records, ABNs,
totals-in-bulk, or database contents. No background calls. No retries
storms (single request, 20 s timeout). AI usage is not required for any
core workflow.

## Future features (design only, addendum §3)

Voice job description, price suggestion from history, smart search
(intent → LOCAL filters only), receipt OCR, photo analysis — each must
keep: off-by-default, explicit tap, review-before-save, graceful manual
fallback, and the same one-file protocol adapter.
