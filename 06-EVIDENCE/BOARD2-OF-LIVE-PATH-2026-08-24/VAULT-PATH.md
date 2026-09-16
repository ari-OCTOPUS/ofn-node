# VAULT-PATH — OnlyFans session cookie (laptop vault-only)

**Rule:** never paste cookie/token **values** in chat, evidence, git, or `node.env`. Field **names** and **paths** only.

## Recommended concrete path (matches existing laptop secrets layout)

Prior patterns on this machine:

| Path | Role |
|------|------|
| `F:\backup\_ops\secrets\google-ga4\` | OAuth client + token JSON + `HOWTO-FILL.md` / `README.md` |
| `F:\backup\_ops\secrets\ziman-maliheh\` | Shopify recovery / bank / TFN JSON (vault-only) |
| `F:\backup\.env` | Canonical organism vault (Telegram etc.) — MUST_STAY_ON_LAPTOP |
| Board2 runtime | `/home/ari/.config/ofn/secrets.env` — key names only when owner injects |

### Recommendation for OnlyFans

```
F:\backup\_ops\secrets\onlyfans\
  README.md              # names + fill instructions; NO values
  HOWTO-FILL.md          # how owner pastes cookie locally
  session-cookie.env     # OPTIONAL local file; gitignored; KEY=value locally
  .gitignore             # ignore *.env cookie files if folder ever tracked
```

**Canonical file for the cookie material (when owner fills):**  
`F:\backup\_ops\secrets\onlyfans\session-cookie.env`

Suggested **key names** inside that file (values owner-only):

- `OFN_ONLYFANS_SESSION_COOKIE=`
- `OFN_ONLYFANS_USER_AGENT=` (optional)
- `OFN_ONLYFANS_ACCOUNT_ID=` (optional)

Do **not** put these in:

- Chat / evidence packs
- `F:\backup\_ops\OCTOPUS.env` / flags
- Board2 `/home/ari/.config/ofn/node.env`

**Board2 runtime (only after second GO):** owner may copy **key names** into `/home/ari/.config/ofn/secrets.env` via secure channel they control — agents must not invent or echo values. Today that file has Shopify/bot keys only; **no** `OFN_ONLYFANS_*` keys present.

## Env key names (document everywhere; values nowhere)

| Key | Required for live attempt | Notes |
|-----|---------------------------|-------|
| `OFN_ONLYFANS_SESSION_COOKIE` | yes | vault-only |
| `OFN_ONLYFANS_LIVE` | yes for live | must stay unset until second GO |
| `OFN_ONLYFANS_USER_AGENT` | no | optional |
| `OFN_ONLYFANS_ACCOUNT_ID` | no | optional selector |

## Contrast Shopify (Board2 secrets.env key names only)

Present on Board2 `secrets.env`: `OFN_SHOPIFY_CLIENT_ID`, `OFN_SHOPIFY_CLIENT_SECRET`, `OFN_SHOPIFY_ADMIN_TOKEN` (+ wire flag `OFN_SHOPIFY_WIRE` documented in adapter). OF should follow the same **secrets.env / vault** split, not chat.

