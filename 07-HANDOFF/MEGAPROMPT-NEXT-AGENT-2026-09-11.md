# MEGAPROMPT — NEXT-AGENT · ۱۱ سپتامبر ۲۰۲۶ صبح
## MISSION-ID: OCTOPUS-NEXT-20260911 · gov: V8 / L2 · mode: EXECUTE · production_authorized=false مگر جایی که رأیِ ثبت‌شدهٔ مالک صریح باشد

این سند را ایجنتِ بعدی پس از دریافتِ مستقیم از مالک اجرا می‌کند. تهیهٔ سند = اجرا نیست، مجوزِ اثرِ خارجی نیست.
نویسنده: لِین `CORTEX-CONNECT-ALL-20260910` (ZCode) در پایانِ نشستِ ۱۰→۱۱ سپتامبر. همهٔ ادعاهای این سند رسیددارند؛ هر چه رسید ندارد صریحاً UNKNOWN نوشته شده.

---

## OP-0 — ورود (۱۵ دقیقه، بدونِ استثنا)

1. بخوان: `AGENTS.md` · `07-HANDOFF/ENGINEERING-ENTRYPOINT-2026-09-04.md` · `01 - Dashboard/OCTOPUS-VITAL-DATA-2026-09-08.md` **§ وضعیت سیزن ۱۱ سپتامبر** (بلوکِ بالای فایل) · `F:/wt-cortex-connect-all-20260910/09-LANES/CORTEX-CONNECT-ALL-20260910/{LANE-REPORT.md, CLICK-TRACE.json}` (بخشِ ۶ و بلوکِ `review_20260911`) · `01 - Dashboard/OCTOPUS-OWNER-BOARD/…/OWNER-APPROVALS*` (رأی‌های ثبت‌شده) · `git log --oneline -15` در `F:/backup`.
2. **قانونِ اسکنِ غیبتِ سه‌سطحی** را اجرا کن (VITAL-DATA § حکمِ داوری ۰۹-۰۹): `git ls-files -z` در برابرِ دیسک · `git ls-tree -r -d --name-only` در برابرِ دیسک · مسیرهای مصرفیِ کدِ زندهٔ `_ops`. نتیجه را با شمار بنویس، حتی اگر صفر.
3. یک لِین اعلام کن و **worktree مستقل** بساز (الگو: `git worktree add --no-checkout -b codex/<lane> F:/wt-<lane> HEAD` → `git reset -q` → `git checkout HEAD -- _ops AGENTS.md`؛ هرگز `git add -A`؛ commit فقط با مسیرِ صریح). `F:/backup` = درختِ زنده؛ روی آن فقط با رأی/دستورِ مالک بنویس (ابسیدین با دستورِ مالک استثناست).
4. قبل از هر پرسش از مالک: OWNER-APPROVALS و git log را بخوان — رأیِ ثبت‌شده را دوباره نپرس. ایجنت‌های موازی فعال‌اند؛ `index.lock` دیگران را حذف نکن.
5. GOV_VERSION=V8 و LADDER=L2 را اولِ LANE-REPORT بنویس. راز/توکن/`.env`/`secrets.env`/`*.key` را نخوان و چاپ نکن. هیچ فلگِ `OCTOPUS_WIRE_*`/`OFN_WIRE_*` را لمس نکن.

---

## OP-1 — زنده‌کردنِ وصلهٔ «🪞 آینه» (بالاترین ارزش برای مالک؛ **گیت‌دار**)

**وضعیتِ ورودی (رسیددار):** کلیک‌های مالک 732409705/706/707/**709 (امروز 07:19:57)** روی `mr:know` همه بی‌اثر؛ روترِ باتِ درونی scheme `mr` نداشت؛ وصله + تست ۸/۸ در `F:/wt-cortex-connect-all-20260910` (کامیت 5685b89؛ کلِ شاخه a7aed79). درختِ زنده هنوز `approval_channel.py` = `4b77da6402816ef6…`؛ نسخهٔ وصله‌شده `399651420bdd2c75…`. **ری‌استارت به‌تنهایی فعالش نمی‌کند.**

**اگر رأیِ مالک (انتقال + ری‌استارت) ثبت شده:**
1. pre-image: sha256 ِ `F:/backup/_ops/budget/approval_channel.py` + `_ops/tests/test_tg_callback_emitter_parity.py` را در لِین ثبت کن.
2. انتقال: در `F:/backup`، `git cherry-pick 5685b89` (فقط وصلهٔ آینه) — یا با رأیِ گسترده‌تر، `git merge --no-ff codex/cortex-connect-all-20260910`. اگر conflict: توقف، گزارش، بدونِ حلِ دستیِ فایلِ زنده.
3. post-image: sha256 باید `399651420bdd2c75…` باشد (فقط برای cherry-pick تکی؛ برای merge کامل هش را تازه محاسبه و ثبت کن). تست‌ها را **در F:/backup** اجرا کن: `test_inner_mirror_callback` ۸/۸ · `test_tg_callback_emitter_parity` ۹/۹ · `test_telegram_poll_e2e` ۷/۷.
4. ری‌استارت با ابزارِ مصوب (`_ops/RESTART-ORGANISM.bat`، detached؛ `.bat` کنسول را نگه می‌دارد). رسیدِ بارگذاری: هشِ ماژولِ بارشده در process-identity/startup record == post-image؛ PID تازه؛ نبضِ `pulse/telegram-poll.json` تازه.
5. اثباتِ زنده = **یک کلیکِ تازهٔ مالک** روی کارتِ initiative (کارت را خودت جعل نکن): باید در `tg-send-log.jsonl` ردیفِ `bot_role=inner` با `update_id` بیاید (اگر `OCTOPUS_TG_MIRROR=1`) یا toastِ توضیح‌دار (فلگ خاموش). `CLICK-TRACE-2.json` با وضعیت‌های مستقل بنویس؛ INFERRED را PASS ننویس.

**اگر رأی نیست:** فقط بندهای ۱ و ۳ (تست در worktree) را انجام بده و دستورهای دقیقِ ۲/۴ را آماده در LANE-REPORT بگذار. کارتِ یک‌تصمیمیِ مالک: «انتقال + ری‌استارت — بله / نه / فقط انتقال».

---

## OP-2 — رسیدِ disposition برای poller ِ باتِ درونی (بدونِ گیت؛ کدِ لِین)

**چرا:** مرکز `_log_disposition` دارد (همان `inbound-log.jsonl`، `kind=disposition`, `update_id`, `outcome`, `reason`)؛ باتِ درونی ندارد ⇒ هیچ ردیابیِ کلیکِ inner از INFERRED بالاتر نمی‌رود و مسیرِ موفقِ ACK کور است.
**چه:** در `approval_channel.poll_once` پس از dispatch/ACK/send، یک ردیف با همان قرارداد بنویس: `{"ts","bot":"inner","update_id","kind":"disposition","outcome": "answered|sent|error|dropped-allowlist","reason": "<scheme:verb>","ack_ok": bool,"send_ok": bool|null}` — بدونِ متن (§۱۰). `tg_receipts.collect()` را طوری گسترش بده که ردیف‌های inner را هم join کند.
**تست (transport جعلی، هم‌الگوی `tests/test_inner_mirror_callback.py`):** callback معتبر ⇒ answered/ack_ok · dict ⇒ sent · خطای handler ⇒ error + هشدار · غیرمالک ⇒ dropped · ردیفِ ورود و disposition با یک `update_id` join می‌شوند · هیچ متنی ذخیره نمی‌شود · `test_both_bots_log_inbound` و `test_phase0_receipt_rig` سبز می‌مانند (۱۵/۱۷ baseline آن دومی، دو FAIL قدیمیِ مرکز).

---

## OP-3 — ریشهٔ سوختِ مغزِ پولی با دادهٔ اندازه‌گیری‌شده (بدونِ تماسِ پولیِ تازه)

**داده (خوانشِ 07:36 محلی از `_ops/state/paid-calls.jsonl`):** اولین `burned_without_output=true` ۱۰-۰۹ 16:53:36؛ تا امروز ۹۰ سوخته = $0.058؛ **امروز ۶۷ سوخته / ۳۸ موفق (۶۴٪)**؛ همه `deepseek-v4-flash`؛ secondary ۵۷ / primary ۳۳.
**کار:**
1. تحلیلِ فقط‌خواندنی: سوخته‌ها بر حسبِ `task`, `max_tokens`, `tokens_out`, `finish_reason`, `retry_of`؛ آیا retry با بودجهٔ صریح هم می‌سوزد؟ (نرخِ سوختِ ردیف‌های `retry_of≠null`). نمودار/جدولِ ساده در لِین.
2. کدِ مسیر: `cortex/model_router._ask_paid` + client — کجا `finish_reason=length` می‌شود با `chars_out=0`؟ آیا مدل در حالتِ «thinking» است و خروجیِ مرئی جدا شمرده می‌شود؟ فرضیه را با **ردیف‌های واقعی** بسنج، نه با تماسِ تازه.
3. پیشنهادِ وصله (کد در لِین + تستِ قرمز از ردیف‌های واقعیِ لجر، بدونِ دادهٔ ساختگی): گزینه‌ها = خاموش‌کردنِ reasoning برای taskهای کوتاه · بودجهٔ صریحِ thinking · مسیرِ مدلِ غیراستدلالی برای `summarize/triage/customer_reply`. هر گزینه با اثرِ دلاریِ تخمینی از همین لجر.
4. کارتِ مالک (یک تصمیم، ≤۳ گزینه): تعویض/تنظیمِ مدلِ پولی = تصمیمِ مالک. تا رأی، هیچ تغییری در `TASK_TIERS`/`budgets.yaml`.

---

## OP-4 — آماده‌سازیِ روشن‌کردنِ اتصال‌های مغز (هر فلگ یک رأی)

فلگ‌ها (پیش‌فرض خاموش؛ کد و تست در شاخهٔ لِین): `OCTOPUS_CONNECT_STORE_REPLY` · `OCTOPUS_CONNECT_LEAD_TRIAGE` · `OCTOPUS_CONNECT_OWNER_DIGEST`.
برای هر فلگ یک کارتِ یک‌تصمیمی بساز: اثرِ دقیق (کدام caller، کدام کارت به مالک، کدام لجر)، هزینهٔ روزانهٔ سقف‌دار (`brain_link.daily_cap`)، rollback (فلگ خاموش + ری‌استارت)، و این‌که **هیچ‌کدام به مشتری چیزی نمی‌فرستد**. وقتی رأیی رسید: فلگ در پیکربندیِ envِ ارگانیسم (همان الگوی `OCTOPUS-flags.cmd` با pre/post sha)، ری‌استارت (کلاس Z)، و اولین ردیفِ واقعی در `paid-calls.jsonl` با `task ∈ {customer_reply, lead_triage, owner_digest}` = رسیدِ فعال‌سازی. اولین ارسالِ واقعی به مشتری = کارتِ جداگانه، هرگز خودکار. `content_draft` caller ِ خودکار ندارد؛ فقط با brief ِ مالک.

---

## OP-5 — وابستگی‌های زندهٔ خارج از git (سطحِ ۳ قانونِ غیبت)

`_ops/legs/mail_credentials.py` روی دیسک هست، `.gitignore:278` ⇒ در هیچ worktree ای نیست؛ `test_lead_pipeline` در هر worktree تازه می‌شکند. **فایل را کپی نکن.**
1. سرشماری: هر مسیرِ `.gitignore` که کدِ `_ops` آن را import/open می‌کند (تقاطعِ الگوهای gitignore با literalهای مصرفی) — فهرست با شمار.
2. برای هر مورد: یا importِ fail-soft در مصرف‌کننده (مثلِ `lead_outbound_transport` → حالتِ «بدونِ credential»)، یا stub ِ track‌شدهٔ بی‌راز با نامِ متفاوت + انتخابِ runtime. هیچ رازی وارد git نشود. تست در worktree تازه.

---

## OP-6 — پورتِ C1–C5 گپ‌ها (کارِ فنیِ باقی‌ماندهٔ AUDIT10H)

منبعِ مشخصات: `F:/wt-audit10h-aie-closure-20260909/09-LANES/*/LANE-REPORT.md` (tip ad53eea) بخشِ C-axis. **اگر مشخصات آن‌جا نبود، نساز؛ UNKNOWN بنویس و توقف کن.** اگر بود: هر C یک تستِ قرمز→سبز، صفر mutation روی نود/۱۳۸، رسیدِ sha.

---

## OP-7 — دیده‌بانیِ مسیرِ پول (فقط‌خواندنی مگر رویداد)

`_ops/state/store-watch.json` (صفر سفارش در 21:00Z) · `drive/store-sync.jsonl` · مارکرِ اولین سفارش · لاگِ ساعتیِ Airtasker (automation-4a540be1، `hourly-check.log`). اگر اولین سفارش آمد: قفلِ CASH، `receipts/FIRST-ORDER-RECEIPT.json`، و (اگر فلگ روشن) پیش‌نویسِ `store_reply` → کارتِ مالک. ادعای «سفارش» فقط با `order_id` واقعی.

---

## OP-8 — H9 (فقط‌خواندنی)

رأی ۲۰۲۶-۰۹-۲۲؛ `three_role.py` و حافظه را لمس نکن. گزارش: T/R شمارِ فعلی از رسیدهای اجرا؛ محلِ تستِ طلایی (در `_ops/tests` با نامِ H9 پیدا نشد — احتمالاً ofn-node/لِین AGGRESSIVE-CLOSURE؛ پیدا کن و اجرا کن، عدد بده).

---

## OP-9 — ابسیدین و بهداشتِ گزارش (پایانِ نشست، الزامی)

سه سطح طبقِ قرارداد: VITAL-DATA (بلوکِ تازه بالا، عنوانِ قبلی «قبلی —» شود) · `OCTOPUS/CURRENT-TRUTH.md` (بلوکِ افزودنی بعد از `OCTOPUS-AUTO-END`، BOM حفظ) · `ACTIVE-SEASON-…md` (بلوکِ روز در انتها). سپس هر دو اعتبارسنج با شمارِ صریح: baseline امروز = فرانت‌متر منشور ۰/میراث ۴۸۳ · لینک دست‌چین ۱۷ + عملیاتی ۱۲۴. جاروی CJK/U+FFFD/backspace روی هر فایلِ فارسی. مسیرهای ویندوزی در heredoc پایتون با forward slash (`\\b` → backspace می‌شود).

---

## تحویل

`09-LANES/<LANE>/LANE-REPORT.md` (چه شد / چه ماند / چه شکست / شواهد / rollback) + رسیدها + از دیسک بازخوانی. گزارشِ فارسی: اولِ همه وضعیتِ OP-1 (آینه زنده شد یا نه، با رسید)، بعد OP-3 با عدد، بعد بقیه. UNKNOWN/NOT_RUN/LOCAL_TESTED را PASS/LIVE ننویس. کارت‌های مالک: هر کدام یک تصمیم، ≤۳ گزینه، ۳۰ ثانیه، با پیامد و rollback؛ «اگر خسته‌ای فقط #۱».

---

## پرامپتِ مالک برای ایجنتِ بعدی (کپی کن و بفرست — همان‌طور که این نشست شروع شد)

```
پرامپت زیر را از دیسک کامل بخوان و اجرا کن:
F:\backup\07-HANDOFF\MEGAPROMPT-NEXT-AGENT-2026-09-11.md

اولویت اول: دکمهٔ «🪞 آینه» من چهار بار مرده (آخرین بار امروز 07:19:57،
update_id=732409709). وصله در worktree هست ولی زنده نیست. رأی من:
[ انتقال + ری‌استارت: بله / نه / فقط انتقال ]  ← یکی را بنویس

بعد از آن، ترتیب OP-2 تا OP-9 را همان‌طور که در فایل است اجرا کن. برای
هر فلگ CONNECT جدا از من بپرس؛ چیزی به مشتری نفرست. سوختِ مغز پولی را با
عدد از لجر واقعی گزارش کن، تماس پولی تازه برای شاهد نساز.

worktree مستقل بساز، F:\backup را فقط با رأی من یا برای ابسیدین دست بزن.
راز نخوان. فلگ wire را لمس نکن. کلیک را دوباره اجرا نکن.

در پایان: اول بگو آینه زنده شد یا نه (با رسید)، بعد عددهای سوخت، بعد
تغییرات و تست‌ها، بعد کارت‌های تصمیم من — هر کدام یک تصمیم، حداکثر سه گزینه.
گزارش را از دیسک بازخوانی کن و بعد تحویل بده.
```
