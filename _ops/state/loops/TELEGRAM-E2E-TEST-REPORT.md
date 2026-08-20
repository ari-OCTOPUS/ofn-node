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

## Network/cost

All new durable-loop tests used injected fake transports. External Telegram calls: 0. Paid calls: 0.
