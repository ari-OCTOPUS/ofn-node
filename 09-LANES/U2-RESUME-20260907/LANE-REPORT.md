# LANE-REPORT — U2-RESUME-20260907

ORDER=MP-OCTOPUS-V4.1 §۱۱/§۱۵ (U2) · GO=مالک 2026-09-07 («ALL») · GOV_VERSION=V8 · LADDER=L2
LANE_ID=U2-RESUME-20260907 · AUTHORITY=owner chat GO

## چه ساخته شد

پلِ «پاسخ مالک → ادامهٔ همان task» روی زیرساخت موجود، بدون bot/listener/تایمر دوم:

۱. **شِما (افزودنی، نسخه‌دار)**: `submit()` سؤال حالا `blocked_task_id` + `blocker_version` می‌گیرد؛ رکوردهای قدیمی بدون این فیلدها کاملاً بی‌اثر می‌مانند.
۲. **`take_resume()` — wake دقیقاً یک‌بار**: نخستین پاسخِ ثبت‌شدهٔ سؤالِ دارای task → payload `task_resume.v1` + رویداد پایدار `task.resume` (با `idempotency_key=resume:<qid>`، `approval_state=approved` به‌معنای «پاسخ احراز شد» نه ارتقای نردبان). ریپلای تکراری/قدیمی هرگز wake دوم نمی‌سازد.
۳. **احراز پاسخ‌دهنده (V4-A11)**: `owner_reply_ok()` — فقط chat_id مالکِ شناخته‌شده؛ قبلاً ریپلایِ هر عضو گروه به متن سؤال می‌توانست جواب پروژه را بازنویسی کند.
۴. **بیدارباش طبیعی**: همان `_drive_leg_engine()` که هر ضربان می‌چرخد، بلافاصله پس از ثبت پاسخ صدا زده می‌شود — gate recheck داخل خود موتور (HALT/بودجه/تازگی) انجام می‌شود؛ پاسخِ مالک خودش مجوز اثر نیست.
۵. ACK مالک حالا می‌گوید کارِ مربوطه «دوباره در جریان افتاد» و return دستگیرِ پیام فیلد `resumed` دارد.

## آزمون‌ها

`tests/test_u2_task_resume.py` = **5/5 سبز** (فیلدهای task + wake یک‌بار + عدم‌تکرار + سؤال عادی بی‌تغییر + fail-closed مالک) · رگرسیون: U1 ۷/۷ + `test_backup_visibility.py` سبز · AST ×3 · diff کل ‎+۶۸/−۲.

## محدودیت صادقانه

`center.py` زنده است (PID 2108) و ماژول قدیمی را در حافظه دارد — کد جدید در اولین ری‌استارت طبیعی لود می‌شود (انجام نشد؛ SERVICE-AFFECTING). تا آن لحظه، پاسخ‌ها طبق مسیر قدیمی فقط «ثبت» می‌شوند بدون resume — یعنی رفتار فعلی دست‌کم هم‌ارزش قبل است، نه کمتر.

ROLLBACK=`git checkout --` سه فایل + حذف تست · MUTATIONS=۴ ردیف U2-RECEIPT.json · COUNTERS: EXTERNAL_ACTIONS=0 · NEW_LAN_LISTENERS=0
NEXT=ری‌استارت طبیعی center (تصمیم مالک/واچ‌داگ) + نخستین سؤالِ دارای task در دنیای واقعی
