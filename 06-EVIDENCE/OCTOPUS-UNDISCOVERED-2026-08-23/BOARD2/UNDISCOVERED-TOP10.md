# BOARD2 UNDISCOVERED (marketing) — 2026-08-23
Lane: DietPi/ofn Board2 only. No live publish. Gap-close already covered G11/G13/G14/G15 (+ partial G20); holds remain G01/G02/G12.

## Top 10 still dark / unwired / doc-only
1. DARK | ofn legs :8791-8794 `/health` returns `{"error":"unknown host"}` while `/healthz` `{"ok":true}` — probe contract unclear | ssh DietPi curl 127.0.0.1:8791/health vs /healthz
2. DARK | octopus-bridge :8796 `/health` → unauthorized (needs key); `/healthz` ok name=octopus-bridge — client auth not documented for marketing lane | same curl :8796
3. UNWIRED | `octopus.command.legs` client still "later" per M4 role — no Board2 consumer wired | agent profile + /home/ari/octopus-bridge
4. HOLD/DOC | Studio = Telegram approve→publish caption-gated only; **no OF adapter**; unlock READY_FOR_ACK idle | studio skill + G12 HOLD captions 0003-0022 | F:\backup\06-EVIDENCE\OCTOPUS-GAP-CLOSE-2026-08-23\BOARD2\RESULT.json
5. HOLD | Gallery for_sale mostly photo-dark (G02); inbox/Telegram Desktop bulk still missing Mom-set | BOARD2-ZIMAN-GALLERY-PHOTOS packs + G02
6. HELD | Etsy publish path intentionally unwired | G13 + etsy-shop-verify-watch never run
7. PATH | `/home/ari/ofn/secrets.env` absent (`secrets.env=no`); shopify/ziman secrets live under `~/.local/share/ofn/secrets` + bak-shopify-* — easy to miss | DietPi ls
8. POST-GAP | Google Merchant free-listings Active but product counts were 0 pending sync — not in gap-close matrix | marketing memory 2026-08-23 Google PASS
9. DUAL | hypno-fugu-mini :8895 `/health` ok but `/healthz` not found — docs that say /healthz are stale | curl :8895
10. DOC-ONLY | Toolkit next legs (Judge.me / Telegram Ops / Canva) + standing Merchant sync watch not OFN services — marketing checklist only | VERIFIED-SUMMARY marketing toolkit

## Gap-close already covered (do not re-open as undiscovered)
G11 wire!=auto PASS; G13 dup+Etsy HELD PASS; G14 studio_wire reconcile PASS; G15 money flags PASS; G20 partial (0016); G01/G02/G12 remain owner HOLDs.
Evidence: F:\backup\06-EVIDENCE\OCTOPUS-GAP-CLOSE-2026-08-23\STATUS.json + BOARD2\RESULT.json

## Live Board2 snapshot (readonly)
- ofn.service active; ofn-heartbeat active; ofn-backup.timer ok (last run SUCCESS 03:17 AEST; inactive between)
- listen 127.0.0.1:8791-8794,8796,8895
- ziman catalog pack present ~/.local/share/ofn/ziman/
