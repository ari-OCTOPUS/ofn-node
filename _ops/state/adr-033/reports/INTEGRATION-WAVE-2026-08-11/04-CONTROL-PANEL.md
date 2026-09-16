# Stage E — Control Panel / MiniApp (real interaction)

- Verdict: **PASS**
- Surface: Octopus Cockpit MiniApp at `http://127.0.0.1:8774/`
- Method: ZCode in-app browser, real navigation + DOM snapshot + screenshot. Read-only only.

## Routes / tabs touched

MiniApp tablist «بخش‌های کوکپیت» renders 9 tabs:
`خانه · تأییدها · پول · لیدها · کارها · سیستم · اسکن‌ها · اعلان‌ها · پرسش`.

| Observation | Result |
|---|---|
| MiniApp reachable (gateway pid 14904 on 8774) | ✅ title "Octopus Cockpit" |
| Home data panel without valid Telegram init-data | `خطا: HTTP 403` — auth **fail-closed** (expected) |
| Ask/Mirror/Collaborator surface (tab پرسش) | three mode chips: `🤝 همکار` · `💬 Ask` · `🪞 آینه` |
| Default mode (before fix) | UI incorrectly showed **Ask** despite runtime `COLLAB=1` — integration bug, fixed below |
| Default mode (after fix) | **🤝 همکار** selected; banner says draft/no-effect; Ask/Mirror remain explicit |
| Collaborator authority | conversation mode only; draft/no-effect, no side-effect grant |

## Assertions

- No unintended `external_effect=true`: only navigation + DOM read + one screenshot; no send/mutation triggered.
- HMAC/auth stays fail-closed: data endpoints return HTTP 403 without valid Telegram init-data. This is correct, not a bug.
- UI does **not** present neural as an executable halt. The پرسش surface frames modes as conversation modes, not authority.
- Mode ≠ authority is legible after the fix: banner explicitly says Collaborator responses are draft/no-effect and Ask/Mirror require explicit selection.

## Evidence

- Screenshot: `C:\Users\Armin\.zcode\cli\artifacts\...GtgePQ...png` (mode chips + fail-closed banner).
- DOM snapshots captured for home tab (403 panel) and پرسش tab (three chips + textbox + بپرس button).

## Real bug found and fixed: MiniApp runtime-config injection

During live interaction a runtime/UI contradiction surfaced (precedence: runtime wins):

- Runtime snapshots and served HTML had `OCTOPUS_WIRE_COLLAB=1`, but the browser showed
  «همکار خاموش است» and `window.__OCTOPUS__` was empty.
- Root cause: the non-secret config bootstrap was injected **after** `app.js` (just before
  `</body>`), so `renderAsk` read defaults before flags existed; and some webviews suppress
  inline scripts entirely, leaving `window.__OCTOPUS__ = {}`.

Additive fixes (no feature removed):

1. Inject the bootstrap **before** the first MiniApp script (fallback to `</head>`/`</body>`).
2. Prepend the same idempotent bootstrap to the external `app.js` response, so config runs
   even when inline scripts are suppressed.
3. Bind the two non-secret UI booleans into `assets_version()` so a flag flip changes the
   cache-busting `?v=` URL (Telegram webview caches by URL).

Post-fix live verification (browser):

- `window.__OCTOPUS__` = `{ wire_collab: true, collab_use_model: true }`, `Telegram.WebApp` present.
- پرسش tab now shows **🤝 همکار** as the active/default chip with banner
  «پیش‌فرض: همکار (پاسخ draft · بدون اثر خارجی). Ask/آینه فقط با انتخاب صریح.»
- Collaborator-default is a conversation mode only; the banner and backend keep it draft/no-effect.
- Regression tests: `test_cognitive_unify.py` `gateway-inject-before-app` (ordering + external app.js + version-flip).

## Notes

- The IAB host tab dropped once during a send click and was reopened; MiniApp render is reproducible and stable on reload.
- No control was disabled or removed.
