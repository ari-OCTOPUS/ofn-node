# SECURITY-QUARANTINE-ADJUDICATION (owner directive #0)

quarantine صرفاً «pre-existing red orphan» پذیرفته نیست. هر مورد root-cause و adjudicate شد.

## A. test_tg_approval_store.py → **VALID, REACHABLE, now ENABLED (14/14)**
- **phantom نیست:** ماژول `telegram_center/approval_store.py` و API (add_pending/approve/reject/
  mark_done/load_pending/sanitize) وجود دارند.
- **reachable در production:** `center.py:50` import؛ `center.py:1223-1224` روی callbackهای
  `ap:ok/ap:no` (مسیرِ approval مالک) `approval_store.approve/reject` را صدا می‌زند؛
  `owner_views.py:48` آن را «canonical mission-approval queue» می‌نامد؛ `callback_token.py:21`
  single-use atomic. → **canonical live lane، صفر orphan.**
- **root-cause شکست:** فقط `t_n_content_not_stored_in_job`، و آن هم **stale characterization**:
  whitelistِ تست `expires_epoch` را نداشت، ولی کد (approval_store.py:151، افزوده 2026-07-20 برای
  TTLِ توکنِ callback) آن را اضافه می‌کند. `expires_epoch` یک **int timestamp** است (نه محتوای کاربر).
  **invariantِ content-free دست‌نخورده** (`sensitive_content not in job` پاس می‌شود).
- **اقدام:** whitelist به contractِ فعلی migrate شد (با rationale)؛ safety assertion تضعیف نشد؛
  تست در run_all.TESTS ثبت شد (script-native). حالا **14/14**.
- **حکم:** ENABLED — نه quarantine، نه supersession.

## B. test_effector_idempotency.py → **QUARANTINED_PHANTOM تا C، سپس RESURRECT**
- phantomِ واقعی: `EffectorGate.request_idempotent` در candidate وجود ندارد (run_all:214).
- **بعد از C3 (idempotent request):** semantics آن (نه صرفاً نامِ method قدیمی) پیاده و تست احیا
  می‌شود؛ از PHANTOM خارج، در manifest ثبت، denominator افزایش. (owner directive #7)

## C. test_mining_leg.py / test_drawdown_enforcer.py → **QUARANTINED_PHANTOM (evidence)**
- API واقعاً غایب: MiningLeg/wiring.make_mining_leg؛ budget_gate.DRAWDOWN_LOG/drawdown_status.
- تا زمانی که آن lane پیاده نشده، phantom با reason می‌مانند (نه silent drop؛ در register ثبت‌اند).

## نتیجه: F-COVERAGE
tg_approval_store adjudicated و enabled → F-COVERAGE برای این مورد **PASS**. effector_idempotency
پس از C. → F-COVERAGE پس از C کامل می‌شود.
