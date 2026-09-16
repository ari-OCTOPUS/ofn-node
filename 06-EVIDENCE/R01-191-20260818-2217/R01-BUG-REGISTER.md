# R01-BUG-REGISTER — شدت · بازتولید · شاهد · حداقل فیکس امن · rollback · تست

run: R01-191-20260818-2217 · همهٔ فیکس‌ها «پیشنهادی» هستند — هیچ تغییری اعمال نشد (R01_FORBIDDEN).

## B1 — HIGH · فایل credential در git tracked
- شاهد: `git ls-files _ops/legs/mail_credentials.py` → برگرداند (۹,۲۷۹B)؛ remote germline (E:) هم دارد. محتوا باز نشد.
- بازتولید: `git ls-files _ops/legs/mail_credentials.py`
- حداقل فیکس امن: `git rm --cached` (فقط index) + افزودن به .gitignore — **با مجوز صریح مالک**؛ چرخش واقعی credential: اجرای انسانی (طبق D3).
- Rollback: `git restore --staged`؛ هیچ history-rewrite لازم نیست (repo محلی + آینهٔ E:).
- تست: `git check-ignore _ops/legs/mail_credentials.py` → exit 0.

## B2 — MED · /sh مسلح، ناسازگار با D2
- شاهد: `_ops/ACTIVATION-RAW-SHELL.flag` PRESENT؛ `STOP-RAW-SHELL` ABSENT؛ handler در پروسهٔ زنده.
- بازتولید: `ls _ops/ACTIVATION-RAW-SHELL.flag`
- فیکس: حذف پرچم توسط مالک (یک فایل؛ rearm با بازساخت پرچم). **اقدام مالک، نه ایجنت.**
- Rollback: `touch _ops/ACTIVATION-RAW-SHELL.flag`
- تست: ارسال `/sh` بدون آرگومان → باید «🔴 ACTIVATION وجود ندارد» بدهد (fail-closed).

## B3 — MED · شکاف کشف تست (الگوی t_*)
- شاهد: pytest روی test_classifier.py و test_evidence_envelope_handshake.py → exit=5 «no tests ran» با وجود ۳۰ تابع واقعی (۲۴+۶).
- بازتولید: `python -X utf8 -m pytest -q _ops/action_bridge/tests/test_classifier.py; echo $?`
- فیکس پیشنهادی (کاندیدای عالی CARD-001 به‌جای memory.db — طبق D4): conftest.py کوچک برای collect توابع `t_*` یا rename — **فقط در worktree قرنطینه با مراسم F5.**
- Rollback: حذف conftest.
- تست: pytest همان فایل → تعداد collect > 0 و exit=0.

## B4 — MED · فایل‌های یتیم/آثار redirect اشتباه
- شاهد: `_ops/state/memory.db` (صفر بایت، Aug 7) · `_ops/all` · `_ops/confirm` · `_ops/graded` · `_ops/propose` · `_ops/state$db` · `_ops/tests/nul`.
- بازتولید: `ls -la` هرکدام.
- فیکس: پس از طبقه‌بندی F2 → فقط `mv` به _Archive/_Duplicates (قانون §۰.۱ — حذف هرگز).
- Rollback: mv برگشت.
- تست: `test -f` مسیر مقصد.

## B5 — LOW · دایرکتوری worktree ثبت‌نشده
- شاهد: `.claude/worktrees/telegram-operational-control-de7666/` بدون `.git`؛ در `git worktree list` نیست؛ حاوی کپی کامل + باندل یکسان.
- فیکس: F2 → ORPHAN/ARCHIVE.

## B6 — LOW · دو stub-git ناتمام
- شاهد: AI-sume/.git و genome-system/.git با `config.lock` رهاشده، HEAD→master، بی-commit؛ git دستورات روی آن‌ها به repo والد resolve می‌شود (رفتار گیج‌کننده).
- فیکس: F2 → طبقه‌بندی (ARCHIVE یا تکمیل init با تصمیم مالک).

## B7 — LOW · ۱۳۴ فایل صفربایتی
- شاهد: 03b؛ شامل WALهای صفر (طبیعی)، لاگ crash صفر (`telegram/center-crash.log`)، `_unwired_*`.
- فیکس: پایش؛ لاگ‌های صفرِ دیرینه → F2.

## B8 — MED · board_cp روی 0.0.0.0:8801
- شاهد: F1 §1 (پروسهٔ زنده). فعلاً بدون LAN؛ با بازگشت LAN = سرویس TLS در معرض کل شبکهٔ محلی.
- فیکس پیشنهادی: bind به 127.0.0.1 + دسترسی از طریق tunnel — **کارت کد، پس از F4 با مراسم.**

## B9 — INFO · شمارش خطوط events.jsonl
- ۴٬۶۳۱ newline در برابر ۴٬۶۷۵ خط parse موفق (احتمالاً CRLF/خط آخر بدون newline). بدون اثر شناسه‌ها (۰ تکرار).

## B10 — INFO · envelope sidecar متوقف از 02:45
- emit_cycle.py/envelope.py امروز ویرایش شده‌اند ولی چرخهٔ جدید منتشر نشده؛ `handshake_sidecar_running=false`. با D5/D6 سازگار (بدون scheduler) — فقط ثبت.

## داوری D4 مالک (CARD-001)
فرض memory.db (HYPOTHESIS_WEAKENED در F1) → پیشنهاد نهایی: **B3 جانشین شود** — کاملاً قابل بازتولید، کوچک، تست‌پذیر، برگشت‌پذیر، و ارزش حاکمیتی مستقیم (درستیِ ادعای «تست سبز» را برای همهٔ repo برمی‌گرداند).
