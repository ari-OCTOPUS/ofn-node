# G04 A18-LIVE-OWNER-INBOUND — verify harness (NO unlock)

stamp: 2026-08-23T09:05:12+10:00

## READY (lab)
- Lab fake PASS: `06-EVIDENCE/OCTOPUS-ARCH-EVOLUTION-LOOP-2026-08-23/A18-INBOUND-LAB-FAKE/RESULT.json`
- Path: fake inbound → local_commands → durable_loop → CONFIRMED/CLOSED (isolated SoT)
- pytest: `_ops/tests/test_a18_inbound_lab_fake.py`

## BLOCKED (LIVE Full Loop)
- Needs **real owner Telegram inbound** `/remember` + `/correct <bad-id>` in owner chat
- Must land in **durable** `_ops/state/telegram/loop/outbox` + `events` (C05 SoT) — not canary sqlite
- Writer lock must NOT grant unrestricted live sendMessage; owner messages are inbound

## Verify steps (owner/ari GO only)
1. Confirm center PID alive; attach OFF; LIVE-TELEGRAM unlock≠send
2. Owner sends one `/remember lab-live-…` and one `/correct not-a-real-id …` in owner chat only
3. Inspect newest loop/outbox CONFIRMED + events CLOSED for those updates
4. Update CURRENT-TRUTH A18 Full Loop only if step 3 PASS

## Do NOT
- Unlock live sendMessage / add send_exceptions for this prove
- Treat A18 outbound canary mids 617/618 as inbound Full Loop
