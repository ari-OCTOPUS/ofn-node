# MiniApp URL truth (reconcile)
'
f'**Stamp:** {stamp}

'
'## Truth
'
'- **Primary LIVE surface:** local miniapp_gateway process (localhost), not an invented public URL.
'
'- **State file** _ops/state/telegram/miniapp-url.json records a *named tunnel* candidate (https://app.master-painting.com) with pid/kind metadata.
'
'- **Env public URL:** unset/unknown in this shell — do not invent.
'
'- **Do not** mutate Telegram menu / BotFather URL without owner GO after live verify of tunnel.
'
'- Docs must say: localhost/process is authoritative for "is MiniApp up"; public URL is optional tunnel metadata until owner confirms.
'
