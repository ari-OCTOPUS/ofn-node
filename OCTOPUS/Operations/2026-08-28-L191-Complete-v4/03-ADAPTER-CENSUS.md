# ADAPTER CENSUS (four-pass, real run)

repo: ofn-node spine tree @68813370 · total=228 · parse_errors=['ofn.helpers.brainport']
counts: {'DEAD_CANDIDATE': 23, 'DORMANT': 110, 'LIVE_CANONICAL': 4, 'SHADOW': 90, 'UNKNOWN': 1}

## LIVE_CANONICAL (4) — entry-anchored to systemd `ofn.service → python3 -m ofn.run` (L3):
ofn.adapters, ofn.node, ofn.run, ofn.worker

## نکته‌ی صادقانه SHADOW=90
node.py/runtime آداپتورها را از طریق registry/dispatch پویا بار می‌کند؛ BFS استاتیک از ofn.run فقط ۴ ماژول را می‌رسد. طبق ADR-03، دیده‌نشدن dispatch = SHADOW (نه DEAD، نه LIVE). ارتقا به LIVE نیازمند introspection فرایند زنده (موج ۳ اختیاری).

## DEAD_CANDIDATE (23) — هرگز DEAD قطعی
ofn.adapters.alert, ofn.adapters.sysmetrics, ofn.backup_job, ofn.kernel.edge, ofn.kernel.safety, ofn.restore_job, scripts.shopify_apply_copy, tests.test_brain_probe, tests.test_cockpit_v2_frontend, tests.test_cockpit_v2_purity, tests.test_mutation_ledger_pair, tests.test_octopus_wire_drift, tests.test_rotation_reader, tests.test_runbook_coverage, tests.test_security_headers, tests.test_shell_navigation, tests.test_shell_reachability, tests.test_studio_marketing_ui, tests.test_studio_shell, tests.test_units, tests.test_ziman_shell_pieces, tools.capture_golden, tools.check_rotation

## UNKNOWN (1)
ofn.helpers.brainport — **UTF-8 BOM واقعی** در ابتدای فایل باعث parse-error ابزارهای AST می‌شود (runtime با BOM کار می‌کند) — پاک‌سازی BOM پیشنهاد doc-fix.

## ابزار
tools/adapter_census/census.py (AST بدون import هدف؛ deterministic؛ drift-guard؛ exit: 0 clean/3 parse-error)