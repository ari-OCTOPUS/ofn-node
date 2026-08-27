# BUGS-P0-P4 — باگ‌ها با اولویت، علت ریشه‌ای، پچ، rollback

> Branch: `audit/zcode-20260828` · Date: 2026-08-28
> قاعده: کوچک‌ترین پچ؛ بازنویسی بزرگ فقط با duplication اثبات‌شده (فقط DUPLICATES.md langar×3).

## P0 — نقض ایمنی / افشا / اثر بیرونی بدون مجوز / خرابی لجر

### P0-1 — llama-server روی 180 به کل LAN باز است
- شاهد: `ss -lntp` ⇒ `0.0.0.0:8081 llama-server.f2 pid=170941` (2026-08-28). تنها سرویس غیر-loopback شبکهٔ اختاپوس؛ هر میزبان LAN می‌تواند مدل را فراخوانی/هزینه/پرامپت کند.
- علت ریشه‌ای: فلگ bind در سرویس octopus-llama-lab تنظیم نشده (پیش‌فرض llama.cpp = 0.0.0.0).
- کوچک‌ترین پچ: `--host 127.0.0.1` در ExecStart (یا `EnvironmentFile` مربوط) + restart سرویس.
- تست: بعد از پچ `ss -lntp | grep 8081` باید 127.0.0.1 نشان دهد؛ از میزبان دیگری curl:8081 باید fail شود.
- Rollback: حذف فلگ + restart. Commit: مخزن жив 180 (پروپوزال این‌جا؛ اعمال روی برد با هماهنگی گره).

### P0-2 — ادعای گیت بستهٔ partner_precondition نادرست است
- شاهد: `studio.yaml` گیت را declare می‌کند؛ `ofn/config.py:112 base_closed_gates=["secret_rotation","miner_isolation"]` آن را **ندارد**؛ `tests/test_shell_contract.py:278` انتظار را hardcode کرده ⇒ تست سبزِ کاذب.
- علت: گیت در سطح pack تعریف شده ولی در سطح node ثبت نشده.
- پچ: افزودن `"partner_precondition"` به base_closed_gates (یا OFN_EXTRA_CLOSED_GATES در prod) + تست منفی که غیبتش را قرمز کند.
- Rollback: حذف همان خط.
- جای commit: این مخزن (ofn-node)، PR همین audit پس از تأیید مالک.

### P0-3 — verify لجر حذفِ tip را نمی‌بیند (C-028)
- شاهد: CONTRADICTIONS.md C-028 + genome ledger 14,168 رکورد؛ VOTE 4 مالک معلق.
- پچ پیشنهادی (additive): `verify_tip()` + sidecar `.tip.json` در adapters/ledger.py + تست حذفِ آخرین رکورد ⇒ قرمز.
- Rollback: تابع جدید صفر اثر روی مسیر موجود دارد (فقط ابزار).

## P1 — قطع مسیر درآمد / شکست transport / ازدست‌رفتن کار

### P1-1 — ofn-backup.service روی 138 غیرفعال
- شاهد: systemctl 2026-08-28 («inactive (known)»). بردِ سه دیتابیس کسب‌وکار بدون بکاپ verified.
- پچ: فعال‌سازی timer + اجرای یک backup_job + ثبت receipt؛ علت غیرفعال‌بودن بررسی شود (شاید خطای قدیمی).

### P1-2 — بازتولیدپذیری: شاخهٔ rescue 302 کامیت جلوتر از master + 1149 فایل کامیت‌نشده
- شاهد: `git rev-list master...HEAD` ⇒ 302/0؛ `git status --short | wc -l` ⇒ 1149 (بیشتر state/evidence در _ops).
- اثر: SIG-IV و هر راستی‌آزمایی مستقل بلاک؛ ریسک `git clean` روی فایل‌های زنده (governor.py untracked).
- پچ: تفکیک state (gitignore/additive policy) از evidence؛ کامیت دسته‌ای برچسب‌دار؛ سپس merge rescue→master با رأی مالک.

### P1-3 — RAM لپ‌تاپ 94.5%
- شاهد: HEALTH-WATCH 2026-08-27 (firefox 965MB، Grok-Bot 659MB، Cursor 584MB، llama-server 567MB، free=900MB).
- اثر: ریسک OOM ارگانیسمِ شتاب‌دهنده. پچ عملیاتی: تخلیهٔ سشن‌های مردهٔ ایجنت‌ها؛ انتقال llama به برد.

### P1-4 — center.py تک‌فایل ~400KB (6212 خط)
- شاهد: wc + نوت 81. ریسک: هر تغییر، کل بات مالک را درگیر می‌کند (WORKLOCK). پچ: فقط پس از اثبات duplication، تجزیهٔ تدریجی interfaces/ (پیشنهاد در ROADMAP LATER).

### P1-5 — germline lag 2.46h + خطاهای push hourly
- شاهد: ORGANISM-STATE.json 2026-08-27 + hourly-push-errors.jsonl. پچ: بررسی stderr کلاس‌های خطا؛ snap-shot پوش پس از هر کار.

## P2 — فیلدهای UNKNOWN / کیفیت کارت اجرایی
- C-044 (دلیل خالی در گذار رنگ)، C-045 (ONE_TICK_TEMPORAL_SKEW)، C-042 (rounding starvation، بازتولید آفلاین)، C-043 (hard_cap rounding). پچ هر مورد کوچک و additive با تست.

## P3 — تست/کد مرده
- _verify/ کهنه؛ dead-code فهرست DEAD-CODE.md؛ 16 شکست run_all؛ شمارش تست ناسازگار؛ `.bak` ها در درخت زنده.

## P4 — زیبایی
- یکسان‌سازی میرورهای OWNER-BOARD؛ آرشیو فایل‌های صفربایتی ریشه؛ نام‌گذاری دو langar.
