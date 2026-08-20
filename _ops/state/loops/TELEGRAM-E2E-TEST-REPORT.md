# Telegram E2E Test Report

Generated: 2026-08-20

## Targeted execution

- `test_telegram_durable_loop.py`: 14/14 PASS.
- `test_tg_api.py`: 34/34 PASS.
- `test_tg_center.py`: 43/43 PASS.
- `test_tg_send_receipts.py`: 11/11 PASS.
- `test_telegram_truthful_receipts.py`: 7/7 PASS.
- `test_telegram_closed_loop_20260820.py`: 15/15 PASS.
- `test_no_silent_message_drop.py`: 8/8 PASS.
- `test_tg_poll_health.py`: 9/9 PASS.
- `test_tg_409_rival_poller.py`: 4/4 PASS.
- `test_restart_center_wiring.py`: 10/10 PASS.
- `test_inbound_log_and_hang_detection.py`: 9/9 PASS.
- `test_tg_probe_invalid_spam.py`: 11/11 PASS.
- `test_phase0_receipt_rig.py`: 15/17 FAIL, reproduced unchanged on baseline HEAD before this patch.

Targeted total: 175 passed, 2 pre-existing failed.

## Full registry run

`_ops/tests/run_all.py` was executed. It did not complete: multiple pre-existing non-Telegram suites failed, then `test_capability_registry.py` exceeded the runner's 300-second per-file timeout. Therefore full execution coverage is incomplete and is not reported as PASS.

## Owner-mandated verification run (2026-08-21)

- `test_tg_instant_and_sendlog.py`: 15/15 PASS — output `verification-2026-08-21/instant-suite.txt` sha256 `e091682d9877eee8f7b48c7538a9dba58338226452eab147ea05d92a410667e6`.
- `test_telegram_shadow_roundtrip.py`: 10/10 PASS — output `verification-2026-08-21/shadow-roundtrip.txt` sha256 `f2f1d51bd2dc502feff225ca8d42c972af7a4d0bba45577860289dc5376f725b`.
- direct_sends: 0 (both suites assert 0).
- direct-send text lines in outputs: 0.
- Telegram HTTP calls referenced in outputs: 0 (fake transports only).
- paid_calls / memory_mutations referenced in outputs: 0 / 0.
- `_sig_fear` containment accepted as `CONTAINED_VERIFIED` (not CLOSED; task_id=None terminal=BLOCKED).

## Network/cost

All new durable-loop tests used injected fake transports. External Telegram calls: 0. Paid calls: 0.
