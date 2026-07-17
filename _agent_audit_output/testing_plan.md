# نقشهٔ تست — 2026-07-16

## وضعِ موجود
- **سوئیت:** `_ops/tests/run_all.py` — ~۱۴۵ فایلِ ثبت‌شده؛ سبزِ کامل = مهرِ `CAPABILITY-OK.flag` (fingerprintِ کدِ پول)؛ هر قرمز = revoke (fail-closed).
- **ایزولاسیون:** `harness.setup()` — vaultِ موقت + env-first (OPS_DIR/GENOME_DIR/…)؛ کدِ worktree را با `REAL_VAULT=<worktree>` تست کن.
- **دو نوع اجرا:** مستقیم (اکثر) و pytest (فایل‌های fixture-دار در `PYTEST_TESTS` — اجرای مستقیمشان سبزِ دروغین می‌دهد).

## قوانینِ سخت
1. run_all را هرگز روی ارگانیسمِ در حالِ اجرا (8771 زنده) اجرا نکن — تست‌های halt/pacemaker با پروسهٔ زنده تصادم می‌کنند (سانحهٔ 07-15).
2. مهرِ capability فقط در همان درختی نوشته می‌شود که تست شده (REAL_VAULT) — اجرای worktree هرگز markerِ live را دست نمی‌زند.
3. تستِ جدید = ثبت در run_all با کامنتِ تاریخ‌دار؛ pytest-style حتماً در `PYTEST_TESTS`.
4. fixtureها واقع‌گرا (درسِ «pipeline را تست کن نه unit») — قراردادِ ورودیِ واقعی، نه شکلِ دلخواه.

## قرمزهای شناختهٔ محیطی (worktree)
`test_phase5 / test_box / test_box_wiring` — فقط به‌خاطرِ نبودِ مهرِ capability در worktree؛ روی live سبزند.

## شکاف‌های پوشش (کارِ بعدی)
| # | شکاف | تستِ لازم |
|---|---|---|
| 1 | `test_ziman_wiring` green-lie (مستقیم exit0، pytest قرمزِ biology) | انتقال به PYTEST_TESTS + فیکسِ injection یا حذفِ ادعا |
| 2 | فانتوم‌ها (drawdown/effector/mining×2) | رأی: آرشیو یا cherry-pick d0bfa7b |
| 3 | `test_durable_journal` قرمزِ واقعی (mkdir در مسیرِ صریح) | فیکسِ یک‌خطی + ثبت |
| 4 | فعال‌سازیِ فلگ‌های موج (LEAD_DISCOVERY و…) روی live | تستِ دودِ post-restart: سایدکارها تازه شوند |
| 5 | PF: پچ‌های 001-003 بعد از merge | اجرای test_truthful_cockpit روی live-PF |
| 6 | e2e سراسری: ایمیلِ fixture → لید → quote → کارت | یک تستِ زنجیرِ کاملِ چند-پرچمی |

## چرخهٔ استاندارد (هر موجِ کد)
build در worktree → تستِ واحدِ نو + همسایه‌ها → run_all کاملِ worktree → sync به live (به‌جز فایل‌های رأی-خواه) → تأییدِ نمونه روی live → commit pathspec-محدود (AV-retry) → پچ به `public/`.
