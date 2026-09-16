# G07 Dirty-tree hygiene plan (NO force push)

stamp: 2026-08-23T09:05:12+10:00
porcelain_count_now: 776

## Rules
- NO `git push --force`, NO history rewrite, NO secrets in commits
- Sparse commits only; path-filtered; human/ari merge gate
- Do not commit `.env`, locks with secrets, or unrelated Board2 binaries

## Recommended sparse commit batches (candidates only)
1. Telegram contracts + gate/attach/dual-outbox helpers + tests
2. `06-EVIDENCE/OCTOPUS-*-2026-08-23/` evidence packs from arch-loop / gap-close
3. CURRENT-TRUTH / MiniApp doc qualifies (separate review)

## Candidates list
- `06-EVIDENCE/OCTOPUS-GAP-CLOSE-2026-08-23/`
- `06-EVIDENCE/OCTOPUS-ARCH-EVOLUTION-LOOP-2026-08-23/`
- `06-EVIDENCE/OCTOPUS-TELEGRAM-WIRE-FIX-2026-08-23/`
- `06-EVIDENCE/OCTOPUS-MINIAPP-DOC-RECONCILE-2026-08-23/`
- `_ops/telegram_center/docs/`
- `_ops/telegram_center/live_telegram_gate.py`
- `_ops/telegram_center/center_sender_bridge.py`
- `_ops/telegram_center/poll_sender_bridge_attach.py`
- `_ops/telegram_center/dual_outbox_contract.py`
- `_ops/tests/test_live_telegram_wire_20260823.py`
- `_ops/tests/test_poll_sender_bridge_attach_default_off.py`
- `_ops/tests/test_dual_outbox_contract_c05.py`
- `_ops/tests/test_a18_inbound_lab_fake.py`
- `06 - Architecture Maps/TELEGRAM-DUAL-OUTBOX-CONTRACT.md`

## Not in this slice
- Auto commit/push
- Cleaning all ~773 lines in one shot
