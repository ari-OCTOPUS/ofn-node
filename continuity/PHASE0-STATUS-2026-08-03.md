# OCTOPUS Continuity — Phase 0 Status — 2026-08-03

## اصل مرجع
مرجع این کار همان تصمیم قبلی است: **هضم به‌جای merge**، بدون حذف برگشت‌ناپذیر، بدون merge کور، و با اولویت کنترل مالک، برگشت‌پذیری، حفظ معنا، و یکپارچگی state/ledger.

## انجام‌شده در این نشست

### 1) حفاظت از commitهای رهاشده
- `git config gc.pruneExpire never` فعال شد.
- هدف: جلوگیری از prune خودکار dangling/unreachable commitها تا وقتی تصمیم archive/bundle گرفته شود.
- نکته: شمارش اولیه قبل از فعال‌سازی، 168 unreachable commit نشان داد. شمارش‌های بعدی روی repo سنگین کند/ناپایدار بودند، پس فعلاً اصل ایمنی فعال است و برای شمارش دقیق باید job جدا اجرا شود.

### 2) kill seam فعال شد
فایل تغییرکرده:
- `_ops/agi2027_runtime/managed_flags.json`

فلگ اضافه‌شده:
```json
"OCTOPUS_WIRE_KILL_SEAM": "1"
```

اثر مورد انتظار:
- `/stop` فقط افکتورها را نبندد؛ مسیر پول/organ_gate را هم fail-closed کند.

تست‌های پاس‌شده:
- `_ops/tests/test_kill_seam_wire.py` → 8/8
- `_ops/tests/test_kill_seam_closer.py` → 5/5

### 3) درز privacy در `langar_bridge` سخت‌تر بسته شد
فایل‌های تغییرکرده:
- `_ops/legs/langar_bridge.py`
- `_ops/tests/test_langar_bridge_scrub.py`

یافته:
- bridge قبلاً خروجی `LangarBot.handle()` را می‌گرفت و سپس ممکن بود `guard.clean()` را معتبر بداند.
- `clean()` فقط متن را sanitize می‌کند، ولی سیاست deny-by-default (`policy_ok`, blocklist/config صریح) را enforce نمی‌کند.
- مسیر صحیح باید فقط `OpsecGuard.scrub()` را بپذیرد، چون `scrub()` خروجی `(allowed, safe_text)` دارد.

اصلاح:
- `_scrub_via_langar` دیگر `clean()` را fallback معتبر نمی‌داند.
- اگر `scrub()` موجود نباشد، خطا بدهد، خروجی نامعتبر بدهد، یا `allowed=False` بدهد، متن خام بیرون نمی‌رود و پیام کوتاه fail-closed برمی‌گردد.

تست‌های پاس‌شده:
- `_ops/tests/test_langar_bridge_scrub.py` → 8/8
- `_ops/tests/test_langar_route_parity.py` با UTF-8 → 17/17
- `_ops/agi2027_control/run_tests.py` → 25/25

### 4) وضعیت langar
- `03 - Projects/اونلی فنز/langar/langar_config.json` وجود ندارد.
- بنابراین fail-closed بودن خروجی‌های Project-F رفتار درست است تا policy صریح ساخته شود.
- `KILL` داخل langar وجود ندارد.

## واقعیت فعلی که کشف شد

### Git / branches / worktrees
- branchهای محلی در آخرین شمارش سریع: 38
- worktree ثبت‌شده در git: 2
- دایرکتوری زیر `.claude/worktrees`: 2
- worktreeهای 4تایی قبلی که در گزارش قبلی دیده شده بودند، الان به‌صورت دایرکتوری worktree فعال دیده نشدند؛ اما branchهایشان هنوز وجود دارند یا قبلاً merge شده‌اند.

### Branchهای ahead از master که کارت Integration می‌خواهند
آخرین شمارش موفق:

1. `claude/telegram-governance-integration-832984` — ahead=12
   - موضوع: governance تلگرام، درِ ورودی واحد، UI دکمه‌ای، Painting OS، quote/invoice/email.
   - پیشنهاد: **اولویت بالا برای digest/port-by-intent**، نه merge کور.

2. `phase-d` — ahead=8
   - موضوع: lead verdict button, consent_store, funnel metrics, speed-to-lead, release/send separation, notification transport.
   - پیشنهاد: **اولویت بالا/متوسط** چون به lead/outbound/value نزدیک است؛ ولی همه پشت flag و owner gate بررسی شود.

3. `claude/project-f-agent-build-aa512f` — ahead=5
   - موضوع: Project-F build package، KPI/RAG/production، reconcile، pf_know.
   - پیشنهاد: **port idea not code** تا تضاد با langar/privacy/state بررسی شود.

4. `claude/c6-self-improvement-ignition-c73186` — ahead=3
   - موضوع: C6 self-improvement indexes/prediction preregistration.
   - پیشنهاد: **sandbox/research**؛ به TCB نزدیک است، D6 sensitivity.

5. `backup/pre-deploy-2026-07-21` — ahead=2
   - موضوع: backup snapshot و state churn.
   - پیشنهاد: **archive/reference only**.

6. `fix/tg-p1-2026-07-30` — ahead=2
   - موضوع: keyboard scrub و callback_data سقف 64B.
   - پیشنهاد: **اولویت بالا برای بررسی targeted** چون امنیت/تلگرام است.

7. `claude/vigilant-grothendieck-8e8250` — ahead=1
   - موضوع: hermetic کردن `test_master_halt`.
   - پیشنهاد: **احتمالاً cherry-pick/test کوچک** بعد از کارت.

8. `fix/neural-loop-close-310-214` — ahead=1
   - موضوع: neural→decision shadow-first + self-wipe guard.
   - پیشنهاد: **research/sandbox** تا استقلال تصمیم کنترل شود.

### Approvals
- pending: 105
- expired: 103
- live/non-expired: 2
- high_live: 0
- 70 مورد expired با عنوان تکراری: «یه لطفی بکن و وضعیتو یه نگاه بنداز ببین چیزی هست»

دو approval زنده:
1. `sgc-mission-mis-1c23c01e91e00a8f30e9`
   - medium / sgc_action
   - title: بررسی لیدهای باز و آماده claim از مسیر proposal router...

2. `sgc-mission-mis-c1a32c8b4dee05705752`
   - medium / sgc_action
   - title: پیشنهاد صریح به مالک برای ثبت attribution.claim روی یک لید مشخص تأییدشده...

پیشنهاد:
- 103 expired را با backup قبل/بعد به وضعیت expired/rejected منتقل کنیم، **بدون اجرای هیچ mission**.
- دو مورد زنده را مالک باید approve/reject/hold کند.

### Working tree / state
شمارش robust با `git status -uall`:
- total status lines: 3932
- modified/index-ish: 2631
- untracked: 1301

ریشه‌های سنگین:
- modified: عمدتاً `Obsidian Vault` و `_ops/state`.
- untracked: عمدتاً `_archive-binaries` و چند مورد `_ops`.

تصمیم:
- هیچ commit کور از state/log/runtime انجام نشود.
- state زنده، archive binaries، docs PMO، و کد باید جدا کارت‌بندی شوند.

## فایل‌های این فاز
- `continuity/PHASE0-STATUS-2026-08-03.md`
- `continuity/ARTIFACT-MANIFEST.jsonl` — summary manifest سبک.

## قدم بعدی پیشنهادی
1. گرفتن اجازه مالک برای پاکسازی منطقی approvalهای expired.
2. ساخت Integration Card برای 8 branch ahead.
3. شروع از دو branch تلگرامی/امنیتی:
   - `fix/tg-p1-2026-07-30`
   - `claude/telegram-governance-integration-832984`
4. بعد `phase-d` برای lead/outbound safety.

## قواعد ادامه
- merge مستقیم ممنوع.
- حذف خام ممنوع.
- هر تغییر live با test و rollback.
- raw/state/log بدون طبقه‌بندی commit نشود.
