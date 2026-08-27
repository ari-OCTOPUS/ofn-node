# TEST-GAPS

scan: 2026-08-27T23:03Z · numbers from commands this session unless noted

## Ran this session (real output)

```
python3 /root/octopus-mesh/tests/test_business_cycle.py -q
Ran 15 tests in 0.128s  OK

python3 /root/octopus-mesh/tests/test_reply_retry.py -q
Ran 27 tests in 0.249s  OK

python3 /root/octopus-mesh/tests/test_cognitive_worker.py -q
Ran 6 tests in 0.049s  OK

PYTHONPATH=/opt/octopus/lab python3 -m unittest ofn.organism.tests.test_life ofn.organism.tests.test_learn -q
Ran 14 tests in 0.106s  OK
```

Total this session on 180: **62 passed, 0 failed, 0 skipped** (these four commands only).

## Not run this session

- 138 `/home/ari/ofn/tests` — **113 files** on disk, `ofn_test_run_this_session=NOT_RUN` (do not claim green).
- 180 remaining organism tests (19 files under ofn/organism/tests; only two modules run).
- ofn-l4 `tests/test_shadow.py` — NOT_RUN.
- Mesh TTL tests: historically T21/T23 fail vs backup because live policy includes cognitive_wake.v1 — **do not “fix” by editing signed policy.json**.
- No end-to-end test: 180 artifact → 138 mint witness → 182 verdict → Telegram → APPROVE → executor → 138 ledger receipt.
- No test that Armin repo produces a lead (repo has no pipeline).
- No test that hypno-fugu and OFN owner-dialogue do not share tokens (security gap).
- No idempotency test for 138 executor against bizop exact_payload.
- No recovery test for 180 disk 90%.
- No contract test that 182 policy.json must match 180/138.

## Gaps that block money claims

1. Negative test: “Telegram inactive ⇒ no customer send” — not automated.
2. Witness packet mint from 138 — no harness on 180 (correct; 180 must not send).
3. Forbidden keys revenue/SENT/booking — covered in test_business_cycle; **not** covered for 138 ofn packs this session.
4. PC_worker jobs — no tests because body not observed.

## Rule

Do not say “all green”. Say the command and the count.
