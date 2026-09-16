# طرحِ نهاییِ یکپارچه‌سازیِ OCTOPUS — «یک حلقهٔ تصمیم، با تمبرِ اصالت»

**نسخه:** 2026-08-03 · **پایه:** برندهٔ داوری = Design 2 (ONE DECISION LOOP)، به‌علاوهٔ پیوندهای اجباری از Design 3 و Design 1 · **شاخه:** master (درختِ زنده، dirty)

> قاعدهٔ استنادِ این سند: هر جا ممکن بوده با **نامِ نماد** لنگر انداخته‌ام نه شمارهٔ خط (درسِ ثبت‌شدهٔ این vault: درختِ زنده وسطِ جلسه شاخه عوض می‌کند و شماره‌خط می‌پوسد). شماره‌خط‌ها، هرجا آمده‌اند، «در لحظهٔ ممیزیِ ۰۸-۰۳» معتبرند و باید پیش از ویرایش دوباره resolve شوند.

---

## ۰. تشخیص، در یک بند

ارگانیسم مشکلِ **سیم‌کشی** ندارد؛ دو چیزِ دیگر ندارد: **اثرِ پایانی** و **نوع**. سنجیده‌شده: ۴۰ کارت پیشنهاد شد، هر ۴۰ تحویل شد (`delivery=SENT` برای همه)، ۲۱ تا تصمیم گرفته شد، و **صفر تا هرگز اثر نکرد** — هر ۲۱ ردیف در `_ops/state/doctor/rfc-verdicts.db::rfc_decision` در وضعیتِ `RECONCILE_REQUIRED` با `receipt_id=''` و `operation_key=NULL` نشسته‌اند، روی ۲۰ زمان‌مُهرِ متمایز از `2026-07-26T07:08:13` تا `2026-07-31T09:48:33` — یعنی تصمیم‌های واقعیِ مالک از مسیرِ قدیمیِ `mark_rfc_consumed`، نه یک دستهٔ مهاجرت. هم‌زمان ۱۹ کارتِ تحویل‌شده هرگز تصمیم نگرفتند (قدیمی‌ترین ۸ روزه، `2026-07-26`؛ در فاصلهٔ همین ممیزی از ۱۸ به ۱۹ رسید)، و تنها پروبی که برای دیدنِ همین ساخته شده بود — `_ops/c6_probes.py::_probe_tg_stale_delivery` — روی فیلدِ `delivery` فیلتر می‌کند در حالی که صف در فیلدِ `decision` است، پس **ساختاراً** یک صفرِ تمیز برمی‌گرداند. و روی همهٔ این‌ها یک لایهٔ سوم نشسته: هر عددی که منتشر می‌شود یک اسکالرِ برهنه است، پس یک ثابتِ منجمد (`_octopus/state/octopus_state.json::self_awareness = "green"`، ۱۶ روز بی‌تغییر، صفر نویسنده، صفر خواننده)، یک اسنپ‌شاتِ نگه‌داشته‌شده (`control_law` = 60.0 که هر ۵ بیت یک‌بار **نوشته** و هر تیک **خوانده** می‌شود)، یک mtime که آرتیفکتِ merge است (۶ فایل از ۲۰ فایلِ `_ops/state/pulse/`، تا ۶.۶ ساعت جلوتر از `ts` درونی‌شان)، یک اسکنِ بریده‌شده (`scan_metadata(max_files=50_000)` که دقیقاً ۵۰٬۰۰۰ برمی‌گرداند) و یک اندازه‌گیریِ واقعی، **همه یک‌شکل رندر می‌شوند**. پس مسئلهٔ مالک «۱۹ کارتِ بی‌تصمیم» نیست؛ مسئله این است که **۲۱ تصمیمی که قبلاً گرفته، صفر اثر تولید کرده و هیچ سطحی به او نگفته**.

---

## ۱. اصلِ سازمان‌دهنده

> **هیچ‌چیز «wired» شمرده نمی‌شود مگر بتواند کارتی را نام ببرد که به `APPLIED` با `receipt_id` ناتهی رسیده باشد — روی ذخیرهٔ زنده، نه فیکسچر.**

از این یک جمله سه قاعده بیرون می‌آید و کلِ طرح روی همین سه‌تا می‌ایستد:

1. **یک چرخهٔ عمرِ کارت، و فقط یکی.** هر زیرسیستمی که اثری می‌خواهد — قلب، sync، 4D، نقشه، مسلح‌کردنِ فلگ — از `_ops/outcomes/pending_card_recovery.py::prepare_rfc_card` عبور می‌کند و در همان پاکتِ rfc می‌نشیند. راهِ دومی برای درخواستِ اثر وجود ندارد. این تنها چیزی است که **تعدادِ سطح‌هایی که مالک باید تماشا کند را کم می‌کند**، نه اینکه هر سطح را جداگانه صادق‌تر کند.
2. **هر عددِ منتشرشده یک نوع دارد، نه یک مقدار.** `(value, source, observed_ts, cadence_s, last_change_ts, dof, mode)` با `mode ∈ LIVE|HELD|CONSTANT|UNKNOWN` که از دادهٔ داخلِ خودِ ظرفِ canonical **استنتاج** می‌شود، نه ادعا. غیابِ ورودی ⇒ `UNKNOWN`، هرگز `0` و هرگز سبز.
3. **قاعده را ببند، نه نمونه را.** به‌جای «این فایلِ مرده را وصل کن»: «هیچ ظرفی حق ندارد بدونِ خوانندهٔ محتوایی وجود داشته باشد». به‌جای «این پروب را درست کن»: «هر فیلتری که روی یک ذخیرهٔ ناتهی صفر رکورد می‌گیرد، `UNKNOWN` برمی‌گرداند نه `0`».

**آنچه این اصل صریحاً ممنوع می‌کند:**

- **نویسندهٔ دوم روی یک فایلِ حالت.** گران‌ترین باگِ تکرارشوندهٔ این ارگانیسم (چهار حادثه در چهار روز). با یک گاردِ AST بسته می‌شود، نه با انضباط.
- **صفحهٔ فرمانِ دوم.** مینی‌اپ فقط **می‌خواند** و **پرتاب می‌کند**. هیچ verb ی نمی‌گیرد. دیوارِ 405 و allowlistِ `miniapp_gateway.py` بایت‌به‌بایت دست‌نخورده می‌ماند و یک تست همین را assert می‌کند.
- **حذف.** هیچ‌چیز delete نمی‌شود. بازنشستگی = **انتقال به `_Archive` + سنگ‌قبر** که به یک card id ارجاع می‌دهد.
- **سبزِ خودساخته.** خودِ census/registry هرگز به‌عنوان «خواننده» شمرده نمی‌شود؛ خواننده باید **محتوا مصرف کند**. وگرنه همهٔ نامه‌دان‌های مرده روزِ استقرارِ قرارداد خودشان را سبز می‌کنند.
- **مسلح‌کردن به‌دستِ ایجنت.** هر فلگ، هر فایلِ `ACTIVATION-*`، هر مسیرِ پول، هر outbound = **رأی مالک**. اعلامِ فلگ با مقدار `=0` مسلح‌کردن نیست و کارِ ایجنت است؛ `=1` رأی است.

---

## ۲. نقشهٔ یکپارچه

```
PRODUCERS (unchanged)                CANONICAL VESSELS (single writer each)
─────────────────────────────        ────────────────────────────────────────
heart/producers.compute_all()  ───>  _ops/state/pulse/heart-signals-latest.json
heart/shadow.py                ───>  _ops/state/pulse/heart-shadow-latest.json   [vital, sla 3600]
heart/setpoint                 ───>  _ops/state/pulse/heart-setpoint-latest.json [daily]
heartstate.persist()           ───>  _ops/state/pulse/heartstate-latest.json     [armed by FILE]
organism.py::_write_state      ───>  _ops/state/ORGANISM-STATE.json              [SOLE WRITER]
                                       └─ key "arbiter"  <- pulse_arbiter.arbiter_snapshot()  (ungated)
                                       └─ key "proposal_metrics" <- brain_worker  (C7 repairs source)
pending_card_recovery.py       ───>  _ops/state/pulse/pending-cards.json         [card SoT]
   _mutate_store()                     (single mutation path)
pending_card_recovery.py       ───>  _ops/state/doctor/rfc-verdicts.db::rfc_decision [verdict SoT]

                                     ↓  READ-ONLY
                     C1 lifecycle_fold  +  C10 provenance.stamp()
                     (pure; zero writes; every figure typed)
                                     ↓
SURFACES
─────────────────────────────────────────────────────────────────────────────
[PRIMARY / COMMAND]  telegram_center/center.py  +  budget/approval_channel.py
                     ── the ONLY writer of decision SUBMITTED->DECIDED
                        (persist_rfc_verdict, reached only from the TG callback)
[READ]               OCTOPUS-DOCTOR/doctor/scanner.py::scan()   (PROV + _m + stamps)
[READ]               _ops/dashboard/server.py , _ops/live/server.py
[READ]               _ops/c6_probes.py::PROBES
[READ]               telegram_center/miniapp_gateway.py  127.0.0.1:8774
                     ── GET only, initData HMAC, allowlist; 405 wall INVARIANT
                     ── the ONLY target of the cloudflared tunnel
                     ── launcher = deep-link back INTO Telegram. no verb.
[READ / PUSH]        brief.morning_text  ── owner-debt line (aging pressure)

4D  ─────────────────────────────────────────────────────────────────────────
4d_system/                    -> _Archive/Projects/2026 - 4d_system/  [OWNER_VOTE, MOVE]
4d_system/brain/telegram_bot.py  -> fail-closed guard + single-poller probe (BEFORE the move)
4d_system/.env                -> UNKNOWN contents; .agentignore matches *.env; never read
THE ONE LIVE LINK:
  heart/sog_math.py::SOURCE_4PY  -> C:\Users\Armin\Desktop\4D\4.py   [ABSENT, parent absent]
  heart/shadow.py , heart/control_law.py  -> read_lock() only, never run_lock()
  _ops/state/sim/PULSE-EQUATIONS-LOCKED.json  (2026-07-10T20:09:22)  -> stays the record
  verdict: provenance UNVERIFIABLE. gates unchanged. run_lock() fails closed.

DEAD LETTERBOXES  (each gets exactly one of two exits, never a third)
─────────────────────────────────────────────────────────────────────────────
_ops/state/pulse/heart-params-shadow.jsonl   (372KB, ~4.75min, 0 readers)
_ops/state/pulse/heart-setpoint-audit.jsonl  (7d cold; owner is TOLD it exists)
_ops/state/heart-wires-latest.json           (flag=1, mtime fresh -> most deceptive)
_ops/state/pulse/work-health.json            (readers exist, gated off)
   EXIT A: a named CONTENT reader, declared in C3
   EXIT B: _Archive + tombstone naming a card id that resolves in pending-cards.json
   (there is no EXIT C. "keep as is" is not available; it is what produced this list.)
```

**راهنمای نقشه:** فلش‌های سمتِ چپ = نویسنده‌ها (بدونِ تغییر). ستونِ وسط = ظرف‌های canonical، هرکدام دقیقاً یک نویسنده. `C1` و `C10` هیچ چیزی نمی‌نویسند؛ یک تاشدگیِ خالص‌اند. همهٔ سطح‌ها از همان تاشدگی می‌خوانند، پس **نمی‌توانند دربارهٔ یک عدد اختلاف داشته باشند**. تلگرام تنها جایی است که تصمیم نوشته می‌شود.

---

## ۳. اجزا

### C10 — `_ops/provenance.py` :: `Stamp` / `stamp()` / `Mode` (جدید، خالص) — پیوند از Design 3

- **هدف:** تنها تعریفِ «عددِ تمبرخورده» و تنها جایی که قواعدِ `LIVE|HELD|CONSTANT|UNKNOWN` وجود دارند. `stamp(value, source, observed_ts, cadence_s, history=None, writer="")` ⇒ dict با کلیدهای `value/source/observed_ts/age_s/cadence_s/last_change_ts/dof/mode/writer`. قواعد: منبع غایب یا `observed_ts` غایب ⇒ `UNKNOWN`؛ `age_s > 2×cadence_s` ⇒ `HELD`؛ `dof==1` روی پنجره‌ای که ≥۳× cadenceِ **اعلام‌شدهٔ همان ظرف** را پوشش می‌دهد ⇒ `CONSTANT`؛ وگرنه `LIVE`.
- **می‌خواند:** هیچ مسیری. تابعِ خالص روی مقادیری که caller قبلاً بارگذاری کرده.
- **می‌نویسد:** **هیچ.**
- **چرا منبعِ حقیقتِ دوم نیست:** نه ثابتِ مسیر دارد نه persistence. نمی‌تواند با هیچ ظرفی مخالفت کند؛ فقط می‌تواند یکی را توصیف کند.
- **سنجهٔ پذیرش (باتری جهش روی فیکسچرِ ایزوله):** (الف) `ts` یک heart-shadowِ فیکسچری را ۱۰ دقیقه عقب ببر ⇒ کارت `HELD` رندر کند نه عدد؛ (ب) ۲۸۸ نمونهٔ یکسانِ `period_s` بده ⇒ `dof=1`, `mode=CONSTANT`؛ (ج) به مسیرِ ناموجود اشاره کن ⇒ `mode=UNKNOWN` و نتیجه **کلیدِ عددیِ `value` نداشته باشد**، پس `float(stamp)` خطا بدهد نه صفر. هر جهش باید دقیقاً یک assert را بشکند؛ SURVIVED یعنی گارد کور است.
- **دو ردِ ساختاری (اجباری):**
  1. **`stamp()` یک mtime را به‌عنوان `observed_ts` نمی‌پذیرد** — `mode=UNKNOWN, reason='mtime-only'`. دلیل سنجیده‌شده: ۱۴ از ۲۰ فایلِ `_ops/state/pulse/` git-tracked اند و ۶ تا mtimeِ آرتیفکتِ merge دارند، تا ۶.۶ ساعت جلوتر از `ts` درونی‌شان.
  2. **`ts` سطحِ بالای `ORGANISM-STATE.json` تازگیِ یک کلید را اثبات نمی‌کند.** مسیرِ `merge_prev` در `_ops/organism.py::_write_state` (بلوکِ back-fill، ~205-218 در لحظهٔ ممیزی) در مسیرِ خطا/STOP هر کلیدِ غایب را از حالتِ قبلی پر می‌کند و هم‌زمان `ts` سطحِ بالا را جلو می‌برد. پس `observed_ts` **باید داخلِ خودِ مقدار** باشد.

### C1 — `lifecycle_fold` (جدید، فقط خواندنی) — ستون فقرات

- **هدف:** یک تاشدگیِ خالص که برای هر کارت جواب می‌دهد «این تصمیم کجاست»، در پنج مرحله: `PROPOSED → DELIVERED → DECIDED → EFFECTED → MEASURED`، به‌علاوهٔ `STALLED` و `UNKNOWN`. مدلِ خواندنِ واحد برای C2، C4، C6، C7، C15.
- **می‌خواند:** `_ops/state/pulse/pending-cards.json` (از طریقِ `_ops/outcomes/pending_card_recovery.py::_load_store`) و `_ops/state/doctor/rfc-verdicts.db::rfc_decision` (از طریقِ `pending_card_recovery.py::load_rfc_verdicts` — تابعی که docstringِ خودش می‌گوید «projection … for recovery/UI» و امروز **صفر صداکنندهٔ تولیدی** دارد).
- **می‌نویسد:** **هیچ.**
- **چرا منبعِ حقیقتِ دوم نیست:** تاشدگیِ خالص با صفر نوشتن نمی‌تواند از منابعش واگرا شود؛ نه رونوشت نگه می‌دارد نه persistence. هر مرحله‌ای که منبعش غایب یا ناخوانا باشد `UNKNOWN` می‌شود، نه `0` و نه سبز. **هر عددی که برمی‌گرداند از C10 عبور می‌کند** (تمبرخورده).
- **سنجهٔ پذیرش:** روی درختِ امروز: `proposed=40, delivered=40, decided=21, effected=0, stalled=19, reconcile_required=21, oldest_stalled=2026-07-26`. تحلیلِ **AST** (نه grep — grep کامنت را می‌شمارد و `from pkg import mod` را از دست می‌دهد) نشان دهد شمارِ صداکنندهٔ تولیدیِ `load_rfc_verdicts` از ۰ به ۱ رفت. جهشِ دوجهته در `STATE_DIR` ایزوله: یک رکورد را `SUBMITTED→DECIDED` کن ⇒ `stalled=18`؛ برگردان ⇒ `19`. تاشدگی‌ای که در هر دو جهت حرکت نکند هنوز کور است.
- **نکتهٔ ایزوله (درسِ ثبت‌شده):** pipeline وقتی بی‌آرگومان ساخته شود `DEFAULT_STORE`ِ **زنده** را می‌سازد. harness باید **اول** وارد شود؛ سنجهٔ ایزوله = صفر بایتِ تغییر در کلِ `_ops/state/` حینِ اجرا.

### C2 — بازنشانهٔ پروبِ کارتِ راکد + قاعدهٔ `predicate_never_matches` — پیوند از Design 3

- **هدف:** دو چیز، به همین ترتیب. **اول قاعده:** به هر ردیفِ `PROBES` یک اعلانِ `reads: (path, field, expected_values)` اضافه شود و یک پروبِ خودسنجِ `predicate_never_matches` که می‌گوید: **هر فیلتری که روی یک ذخیرهٔ ناتهی صفر رکورد بگیرد، `UNKNOWN` (-1) برمی‌گرداند، نه `0`**. **بعد نمونه:** `_probe_tg_stale_delivery` را از `delivery` به `stalled` ِ C1 ببر و رشته‌های `subject`/`hypothesis` خودش را هم اصلاح کن (وگرنه پروبی مستند می‌شود که دیگر کارِ نوشته‌شده‌اش را نمی‌کند).
- **می‌خواند:** `_ops/state/pulse/pending-cards.json` (همان SoT که `pending_card_recovery.py` پیش از هر ارسال می‌نویسد)، از مسیرِ C1.
- **می‌نویسد:** فقط همان رکوردِ پروبِ c6 که امروز هم می‌نویسد. هیچ ذخیرهٔ موازی‌ای persist نمی‌شود.
- **چرا منبعِ حقیقتِ دوم نیست:** پروب یک مشاهده ثبت می‌کند نه حالت؛ خروجی‌اش از قبل یک دفترِ مشتق است.
- **سنجهٔ پذیرش:** `predicate_never_matches` باید **پیش از** رفعِ نمونه، روی همان predicateِ خرابِ `delivery` شلیک کند — این اثبات می‌کند قاعده نمونه را بدونِ اینکه به او گفته باشند می‌گیرد. سپس شمارشِ پروب از `0` به `19` می‌رود با ذکرِ قدیمی‌ترین `2026-07-26` (۸ روز). جهشِ دوجهته: فیکسچری که همهٔ `decision`ها `DECIDED` است ⇒ `0`؛ همان با یک `SUBMITTED` ⇒ `1`؛ فیکسچری که کلیدِ `decision` در آن تغییرِ نام داده ⇒ `UNKNOWN/-1`، نه `0`.

### C11 — `_ops/heart/pulse_arbiter.py` :: ممنوعیتِ «consensus» — پیوند از Design 3

- **هدف:** آربیتر بلندترین دروغِ باربر است: با یک متحرک و دو ثابت، `driver="consensus"`, `n_present=3`, `color=GREEN` منتشر می‌کند. `_vote()` فیلدهای `mode/dof/last_change_ts` می‌گیرد؛ `arbitrate()` فیلدهای `n_moving/n_held/n_constant` و **یک قاعدهٔ سخت: وقتی `n_moving <= 1` مقدارِ `driver` حق ندارد `consensus` باشد — می‌شود `solo:<name>`.** `_cardiac_vote` ساختاراً `CONSTANT` تمبر می‌خورد (`bio_rhythm.period_s` تابعِ قطعیِ mass است و mass فقط از organهای بودجه و `fitness attribution.confirmed` رشد می‌کند که `0` است ⇒ `dof=1` بدونِ نیاز به تاریخچه). `_control_vote` با مقایسهٔ `ts` خودِ `heart-shadow-latest.json` با ساعتِ تیک، `HELD` تمبر می‌خورد (نوشته هر ~۲۲۰s، خوانده هر ~۵۷s). `_rhythm_vote` تنها `LIVE` است.
- **می‌خواند:** دقیقاً همان سه اسنپ‌شاتی که امروز می‌خواند — `cardiac.status_snapshot()`، `heart/shadow.read_shadow_latest()`، dictِ ریتم که `organism.py` پاس می‌دهد — به‌علاوهٔ دنبالهٔ کرانه‌دارِ `heart-params-shadow.jsonl` برای `dof`.
- **می‌نویسد:** هیچ‌چیزِ جدید. `persist()` **دقیقاً همان‌طور gated می‌ماند** (`OCTOPUS_WIRE_PULSE_ARBITER` + `_ops/ACTIVATION-PULSE-ARBITER.flag`)، پس `arbiter-latest.json` و `arbiter-shadow.jsonl` هم‌چنان ساخته نمی‌شوند. فیلدهای جدید سوارِ مسیرِ **از قبل بی‌قیدِ** `arbiter_snapshot()` می‌شوند که به کلیدِ `arbiter` در `ORGANISM-STATE.json` می‌رسد، نوشته‌شده توسطِ تنها نویسندهٔ موجود.
- **چرا منبعِ حقیقتِ دوم نیست:** `ORGANISM-STATE.json` از قبل ظرفِ اثبات‌شده است (خوانده‌شده توسطِ `OCTOPUS-DOCTOR/doctor/scanner.py` و `_ops/dashboard/server.py`) و دقیقاً یک نویسنده دارد. مقصدِ flag-gated بسته می‌ماند، پس جای دومی برای ظاهرشدنِ خوانشِ آربیتر وجود ندارد.
- **سنجهٔ پذیرش:** ظرفِ یک بیت پس از ری‌استارت، `ORGANISM-STATE.json → arbiter.driver` بخواند `solo:rhythm` با `n_present=3, n_moving=1`، و `scanner.scan()` آن را در رسیدِ `period_s` سطح بدهد **بدونِ هیچ تغییری در doctor فراتر از ردیفِ PROV** — یعنی اثر روی سطحی دیده شود که هیچ‌کدام از دو ماژول مالکش نیستند. جهش: `_rhythm_vote` را ثابت کن ⇒ `n_moving=0` و driver **نباید** `consensus` رندر کند.
- **هشدارِ قراردادِ رشته:** `driver` یک قراردادِ رشته‌ای است. `scanner.py` فقط `.startswith('brake')` را تست می‌کند (امن)، ولی هر مصرف‌کننده‌ای که `== 'consensus'` مقایسه کند بی‌صدا رفتار عوض می‌کند. خواننده‌ها را **پیش از** فرود با AST بشمار، نه بعدش.
- **فراموشیِ ری‌استارت:** «آخرین ts دیده‌شدهٔ shadow» در حافظهٔ پروسه است (مثلِ `_period_hist` که هرگز persist نمی‌شود). پس از ری‌استارت باید یک چرخه `UNKNOWN` گزارش شود، نه `LIVE` — و تستِ پذیرش باید **همان تیکِ پس‌ازری‌استارت** را assert کند.

### C12 — گاردِ انحصارِ نوشتنِ `ORGANISM-STATE.json` (تستِ AST) — پیوند از Design 1

- **هدف:** بستنِ **کلاسِ** «دو نویسنده روی یک فایلِ حالت» (چهار حادثه در چهار روز)، به‌جای انضباط. دقیقاً یک ماژول حق دارد این فایل را برای نوشتن باز کند: allowlistِ تک‌ورودی `_ops/organism.py::_write_state`.
- **می‌خواند:** سورسِ مخزن از راهِ AST.
- **می‌نویسد:** **هیچ.**
- **چرا منبعِ حقیقتِ دوم نیست:** گاردی است که وجودِ حقیقتِ دوم را **قابلِ کشفِ ساختاری** می‌کند، به‌جای کشف در تولید.
- **سنجهٔ پذیرش:** جهش: در رونوشتِ موقتِ درخت یک `LockedJson(STATE_FILE).write(...)` دوم بگذار ⇒ تست قرمز و پیامِ خطا `file:symbol` را نام ببرد؛ برگردان ⇒ سبز. گارد باید برای **نوشتنِ غیرمستقیم** هم قرمز شود (helperی که `STATE_FILE` را به‌عنوان آرگومان می‌گیرد) — این حالت جداگانه جهش‌آزموده شود.

### C3 — `wiring_contract` (قاعده، نه نمونه) + دو پیوندِ اجباری از Design 1

- **هدف:** ناممکن‌کردنِ کلِ کلاسِ «ادعای wired بودن که هیچ اثری اثباتش نمی‌کند». یک تستِ رجیستری‌محور با دو جهت: (الف) هر ظرفِ اعلام‌شده حداقل یک **خوانندهٔ تولیدی** داشته باشد؛ (ب) هر قابلیتِ اعلام‌شده یک نمادِ **اثرِ پایانی** نام ببرد و حداقل یک رکورد از آن اثر نشان دهد، وگرنه `UNKNOWN` — هرگز سبز.
- **می‌خواند:** ASTِ درختِ سورس، `_ops/OCTOPUS-COMPONENT-REGISTRY.md`، و `_ops/state/flags-loaded-live.json` (برای تشخیصِ خوانندهٔ gated-off).
- **می‌نویسد:** **هیچ** (فقط تست).
- **چرا منبعِ حقیقتِ دوم نیست:** هیچ حالتِ اجرایی ذخیره نمی‌کند و همه‌چیز را از کد مشتق می‌کند، پس کد authoritative می‌ماند. رجیستری از قبل مستنداتِ tracked است؛ این تست آن را **ابطال‌پذیر** می‌کند نه به ذخیرهٔ حالتِ دوم تبدیل.
- **سه قاعدهٔ باربر (بدونِ این‌ها C3 پوچ است):**
  1. **خواننده باید محتوا مصرف کند.** `import` خواندن نیست. C3 در شکلِ ساده‌اش با «یک ماژول import شود و هرگز صدا زده نشود» ارضا می‌شود؛ آن‌وقت هر نامه‌دانِ مرده روزِ فرودِ قرارداد خودش را سبز می‌کند. تحلیل باید فراخوانی/دسترسیِ صفت را ببیند، و **خودِ رجیستری/census هرگز خواننده شمرده نمی‌شود.**
  2. **گاردِ حضورِ فایلِ `ACTIVATION-*` (تست، نه یادداشت).** هر فایلِ `ACTIVATION-*` که در رجیستری نام برده شده باید روی دیسک موجود باشد، وگرنه تست قرمز. دلیل: `heartstate-latest.json` هر ~۵۷ ثانیه می‌نویسد و armش **فایلِ** `_ops/ACTIVATION-HEARTSTATE.flag` است (از `2026-07-23` دست‌نخورده)، نه فلگِ envی که اعلام می‌کند. یک ممیزیِ فلگ آن را «خاموش» گزارش می‌کند در حالی که می‌نویسد. یک سنگ‌قبرِ نثری جلوی ایجنتِ پاکسازی را نمی‌گیرد؛ تست می‌گیرد.
  3. **سیاستِ stream و سقفِ اندازه.** ظرف‌های `kind=stream` هرگز مقدارشان روی هیچ سطحی نمی‌رود؛ فقط چکیده (`last_ts`, `n_lines`, `bytes`) با سقفِ ~۵۱۲ بایت. و streamی که تنها خوانندهٔ اعلام‌شده‌اش خودِ رجیستری باشد ⇒ قرمز. زیرِ این قاعده `heart-params-shadow.jsonl` یا خوانندهٔ محتوایی می‌گیرد یا سنگ‌قبر — «همین‌طور بماند» گزینه نیست.
- **سنجهٔ پذیرش:** روی درختِ امروز باید بدونِ راهنمایی دقیقاً این مجموعه را نام ببرد: `heart-params-shadow.jsonl`، `heart-setpoint-audit.jsonl`، `_ops/state/heart-wires-latest.json` (فریبنده‌ترین: فلگش قطعاً `1` و mtimeاش تازه است، پس هر چکِ liveness پاس می‌شود)، `_ops/state/pulse/work-health.json` با علتِ صریح `reader-gated-off: OCTOPUS_WIRE_DEADWRITE_CARDS absent from flags-loaded-live.json`، `load_rfc_verdicts`، `_ops/legs/sync_health.py`، و `_octopus/state/octopus_state.json`. **اگر صفر مشکل گزارش کند، خودش خراب است.** سبز فقط وقتی ممکن است که هر مورد یا خواننده داشته باشد یا سنگ‌قبری که **یک card id را نام ببرد که در `pending-cards.json` resolve شود** — و ورودیِ معافی که idاش resolve نشود، خودش قرمز است.

### C5 — `CardSpec`: یک پاکت، رسیدِ اجباری

- **هدف:** تغییرِ setpointِ قلب، آرشیوِ 4D و مسلح‌کردنِ یک فلگ را **کارتِ هم‌شکل** کند. پاکتِ موجودِ rfc عیناً بازاستفاده می‌شود (`kind / rfc_id / summary / owner / nonce / expires_at / token_sha256 / delivery / decision / created_ts / updated_ts`) و همان `_key(kind, cid)`. فقط effector فرق می‌کند، و **هر effector موظف است پیش از `begin_rfc_apply` یک `operation_key` بدهد و در `ack_rfc_verdict` یک `receipt_id` ناتهی**. نبودِ رسید ⇒ کدِ موجود خودش ردیف را در `RECONCILE_REQUIRED` می‌گذارد — که حالا C4 آن را به کارت برمی‌گرداند. مسیرِ قدیمیِ `mark_rfc_consumed` بازنشسته می‌شود؛ هر ۲۱ پایانهٔ بی‌رسید از همان مسیر آمده‌اند.
- **می‌خواند:** `_ops/state/doctor/rfcs.json` — همان منبعِ پیشنهادی که `_ops/organism.py` از راهِ `rebuild_rfc_cards` می‌خواند.
- **می‌نویسد:** هیچ‌چیزِ جدید — یک تستِ قرارداد به‌علاوهٔ یک بخشِ مشخصات.
- **چرا منبعِ حقیقتِ دوم نیست:** هیچ ظرفی اضافه نمی‌کند؛ فقط محدود می‌کند چه چیزی وارد ظرفِ موجود شود، و مسیری را که ۲۱ پایانهٔ بی‌رسید تولید کرده حذف می‌کند.
- **سنجهٔ پذیرش:** سه کارتِ فیکسچری (تغییرِ setpoint، آرشیوِ دایرکتوری، مسلح‌کردنِ فلگ) کلِ چرخه را در `STATE_DIR`ِ ایزوله طی کنند و هر سه با رسیدهای **متمایز و ناتهی** به `APPLIED` برسند. فیکسچرِ چهارم که `operation_key` ندارد باید به `RECONCILE_REQUIRED` برسد، نه `APPLIED`. ایزوله با «صفر بایتِ تغییر در `_ops/state/`» اثبات شود.

### C4 — «راکد‌ماندن، خودش یک کارت می‌شود» — **مشروط**

- **هدف:** توقفِ خودِ حلقه دوباره وارد حلقه شود. هر ردیفِ `rfc_decision` در `RECONCILE_REQUIRED` با `receipt_id` تهی و قدیمی‌تر از آستانه، به یک پیشنهاد تبدیل شود. امروز ۲۱ ردیف — وضعیتی که اسمش لفظاً «یک انسان باید reconcile کند» است و هشت روز به هیچ انسانی نگفته.
- **می‌خواند:** `rfc_decision` از راهِ C1.
- **می‌نویسد:** یک کارت، **منحصراً** از راهِ `pending_card_recovery.py::prepare_rfc_card`، داخلِ `pending-cards.json`، فقط از مسیرِ `_mutate_store`. یک ردیف اضافه می‌کند، نه یک فایل؛ فلگِ جدید نمی‌خواهد و سوارِ `OCTOPUS_WIRE_PROPOSAL_BUTTONS`ِ از قبل اعلام‌شده می‌شود.
- **چرا منبعِ حقیقتِ دوم نیست:** فقط از راهِ نویسندهٔ canonical داخلِ ظرفِ canonical می‌نویسد و تنها مسیرِ جهشِ موجود را استفاده می‌کند.
- **شرطِ فعال‌سازی (اصلاحِ اجباریِ داور، غیرقابلِ چشم‌پوشی):** C4 حق ندارد شلیک کند تا زمانی که **دستِ‌کم یک کارت روی ذخیرهٔ زنده به `APPLIED` با `receipt_id` ناتهی رسیده باشد** — نه در فیکسچرِ ایزولهٔ C5. اولین کارتِ تجمیعی **با دست** ساخته و ارسال می‌شود. زیرسیستمی که مسیرِ اثرِ زنده‌اش ۰ از ۲۱ است، حق ندارد با نوشتنِ کارتی دربارهٔ شکستِ خودش، خودش را bootstrap کند.
- **سنجهٔ پذیرش:** دقیقاً **یک** کارتِ تجمیعی که ۲۱ ردیف را خلاصه می‌کند (نه ۲۱ کارت)، با قدیمی‌ترین `2026-07-26`، سوار بر دایجستِ روزانهٔ موجود — بدونِ کانالِ outboundِ جدید. پس از تصمیمِ مالک، `rfc_decision` ردیفی با `state=APPLIED` و `receipt_id` ناتهی نشان دهد: **اولین `APPLIED` در کلِ تاریخِ آن جدول.** با `updated_ts` درونی سنجیده شود، هرگز با mtime.

### C6 — نمای خواندنیِ چرخهٔ عمر در مینی‌اپ + پرتاب‌کننده (بدونِ verb)

- **هدف:** مینی‌اپ نمای **خواندنیِ** C1 می‌شود و هیچ چیزِ دیگر: فهرستِ هر کارت با مرحله و سن، و در هر ردیف یک پرتاب‌کننده که کاربر را به همان کارتِ تلگرامی می‌برد که تصمیم واقعاً آنجا گرفته می‌شود.
- **می‌خواند:** تاشدگیِ C1، از راهِ `_ops/telegram_center/miniapp_gateway.py` موجود — فقط `GET`، اعتبارسنجیِ HMACِ `initData` پیش از یک بایت داده، پروکسی از 8773، bind روی `127.0.0.1:8774`. هم‌زمان `_ops/telegram_center/miniapp_state.py::get_approvals_state` از `_ops/state/outcomes/outcomes.db` جدا می‌شود: کوئریِ `SELECT ... FROM deliveries WHERE resolved=0` روی پایگاهی اجرا می‌شود که تنها جدولش `outcomes` است، پس throw می‌کند و به UI `{'status':'unknown_schema','pending':[]}` می‌دهد در حالی که ۱۹ کارت منتظرند. این خوانشِ حقیقتِ دوم **حذف** می‌شود؛ یعنی تعداد ذخیره‌های مشورت‌شده کم می‌شود نه زیاد.
- **می‌نویسد:** **هیچ.**
- **چرا منبعِ حقیقتِ دوم نیست:** gateway هیچ مسیرِ جهش‌دهندهٔ تصمیم نمی‌گیرد. `persist_rfc_verdict` تنها نویسندهٔ گذارِ تصمیم می‌ماند و فقط از callbackِ تلگرام (پس از `verify_rfc_callback`) قابلِ رسیدن است.
- **سه گاردِ اجباری:**
  1. **projectionِ سخت‌گیر:** فقط `{rfc_id, summary, created_ts, decision, age}`. فیلدهای `token_sha256`, `nonce`, `owner` هرگز project نمی‌شوند. `pending-cards.json` این‌ها را دارد و تنها هدفِ تونلِ cloudflared همین gateway است — یک باگِ projection این تونل را به سطحِ اعتبارنامه تبدیل می‌کند.
  2. **سنجهٔ پذیرش باید بدنهٔ پاسخِ HTTP را بایت‌گرپ کند**، نه کدِ projection را بازرسی. `GET /api/approvals` با initDataِ معتبر باید `count==19` بدهد، دقیقاً برابرِ پروبِ C2، و byte-grepِ بدنه هیچ رخدادی از هیچ مقدارِ `token_sha256`/`nonce`ِ موجود در ذخیره پیدا نکند.
  3. **ناوردایِ دیوارِ 405:** یک تست assert کند که allowlistِ تک‌ورودی و پاسخ‌های 405 روی هر متدِ غیرِ GET در `miniapp_gateway.py` بایت‌به‌بایت تغییر نکرده‌اند. امروز هیچ verdict، هیچ ارسال و هیچ جهشِ حالتی از تونلِ عمومی قابلِ رسیدن نیست چون **دیوارِ متد ناممکنش می‌کند**، نه چون کسی بازبینی کرده. آن دیوار سیاست نمی‌شود.
- **یک UNKNOWNِ صریح:** آیا `pending-cards.json` مرجعی به پیامِ تلگرامیِ اصلی نگه می‌دارد (`chat_id`/`message_id`)؟ **نامعلوم** — در شواهدِ سنجیده‌شده چنین فیلدی فهرست نشده. اگر نباشد، پرتاب‌کننده **حق ندارد لینکی حدس بزند**: ردیف `UNKNOWN` رندر می‌کند و `mark_delivery` (همان نویسندهٔ تک‌گانهٔ موجود) از این پس در لحظهٔ ارسال یک `tg_message_ref` ثبت می‌کند — رو به جلو. کارت‌های قدیمی برای همیشه `UNKNOWN` می‌مانند، نه لینکِ ساختگی.
- **سنجهٔ پذیرش (کلی):** نما ۱۹ کارتِ راکد با سن، و ۲۱ ردیفِ reconcile را فهرست کند. `POST` یک verdict به 8774 ⇒ `405`، و `pending-cards.json` قبل و بعد **بایت‌یکسان**. تصمیمی که از مینی‌اپ پرتاب شد، در ذخیره‌ای ظاهر شود که مسیرِ callbackِ تلگرام نوشته — همان نویسنده، همان دودمانِ `updated_ts` — که ثابت می‌کند پرتاب‌کننده مسیریابی کرد، عمل نکرد.

### C7 — تعمیرِ صداقتِ `proposal_metrics`

- **هدف:** `ORGANISM-STATE.json` امروز `proposal_metrics {proposals_delivered: 0, proposal_outcomes: 0, proposals_sent: 0, proposal_accept_rate: 0.0}` و `proposal_router {seen_total: 0}` گزارش می‌کند در برابرِ ۴۰ کارتِ SENT و ۲۱ تصمیم. همان شکستِ «منبعِ اشتباه» است، یک لایه بالاتر — و `_ops/cortex/goal_directed.py` آن را به‌عنوانِ خطِ پایهٔ هدف مصرف می‌کند.
- **می‌خواند:** C1.
- **می‌نویسد:** همان کلیدِ `proposal_metrics` در `_ops/state/ORGANISM-STATE.json`، از راهِ همان نویسندهٔ واحدِ موجود (`_ops/brain_worker.py`، تغذیه‌شده از `ctx.wired.live_loop.proposal_metrics()`).
- **چرا منبعِ حقیقتِ دوم نیست:** همان کلید، همان فایل، همان نویسندهٔ واحد — فقط منبعِ عدد عوض می‌شود. افزودنِ نویسندهٔ دوم اینجا دقیقاً همان باگی است که این طرح نباید تکرارش کند (و C12 اجازه‌اش را نمی‌دهد).
- **سنجهٔ پذیرش:** `proposals_delivered` از `0` به `40`، `proposal_outcomes` از `0` به `21`، و یک `proposals_effected` تازه‌سطح‌شده که `0` می‌خواند — **صادقانه، نه پنهان**. پیش از جایگزینیِ کلید، یک چرخهٔ کامل در سایه اجرا شود و قدیم/جدید کنارِ هم لاگ شوند، چون `goal_directed.py` هفته‌هاست در برابرِ صفر تفاضل می‌گیرد و پرشِ `0→40` می‌تواند انتخابِ هدف را مختل کند.

### C8 — صداقتِ اصالتِ sog (نسخهٔ درست، با ردِ رشتهٔ `"unavailable"`) — پیوند از Design 3

- **هدف:** سه گیتِ زندهٔ قلب (`delta_self`, `e_shadow`, `i_pred`) همه `locked` اند در برابرِ `_ops/state/sim/PULSE-EQUATIONS-LOCKED.json` (ts `2026-07-10T20:09:22`, `provenance.source_4py_sha256 = f856b1be…`). `SOURCE_4PY` در `_ops/heart/sog_math.py` از `SOG_4PY_PATH` با پیش‌فرضِ `C:\Users\Armin\Desktop\4D\4.py` می‌آید؛ آن فایل و پوشهٔ والدش **موجود نیستند**، `SOG_4PY_PATH` هیچ‌جا ست نشده، و هیچ نسخه‌ای از `4.py` در کلِ vault نیست. امروز چیزی نمی‌شکند چون مصرف‌کننده‌های زنده (`_ops/heart/shadow.py`، `_ops/heart/control_law.py`) فقط `read_lock()` را صدا می‌زنند و هرگز `run_lock()` را.
- **مکانیزمِ درست (این نکته دو طرحِ دیگر را رد کرد):** `sog_math._sha256_file()` روی `OSError` **رشتهٔ لفظیِ `"unavailable"`** برمی‌گرداند و همان به‌عنوانِ `source_4py_sha256` نوشته می‌شود. آن مقدار truthy و غیرِ null است، پس گاردی که «null» را تست کند و گاردی که «حضور/تطابقِ هش» را تست کند، **هر دو از کنارش رد می‌شوند** و قفلی نوشته می‌شود که هنوز سه گیت را `locked` نشان می‌دهد. گارد باید روی **قابلِ‌راستی‌آزمایی‌بودن** کلید بخورد و رشتهٔ `"unavailable"` را صریحاً رد کند.
- **می‌خواند:** `_ops/state/sim/PULSE-EQUATIONS-LOCKED.json` و وجود/هشِ `SOURCE_4PY`.
- **می‌نویسد:** یک فیلدِ افزوده روی `_ops/state/pulse/heart-shadow-latest.json` (علامتِ حیاتیِ اعلام‌شدهٔ لایه، ~۱۵ خواننده، `sla_s 3600`)، از راهِ نویسندهٔ واحدِ موجودِ همان ظرف. و در مسیرِ عادی **کمتر** می‌نویسد: `run_lock()` دیگر نمی‌تواند قفل را با اصالتِ غیرقابلِ‌راستی‌آزمایی بازنویسی کند.
- **چرا منبعِ حقیقتِ دوم نیست:** نه فایلِ جدید نه نویسندهٔ جدید؛ یک فیلد روی ظرفی که از قبل نویسنده‌اش را دارد. اعداد تغییر نمی‌کنند، فقط برچسبشان.
- **سنجهٔ پذیرش:** `heart-shadow-latest.json` مقدارِ `sog_provenance = "UNVERIFIABLE"` حمل کند تا وقتی `SOG_4PY_PATH` ست نشده و `4.py` غایب است؛ `"VERIFIED"` فقط اگر مسیرِ داده‌شده به `f856b1be…` هش شود؛ `"MISMATCH"` در غیرِ این‌صورت — پس یک `4.py`ِ بازیابی‌شده از نسخه‌ای ناشناخته نمی‌تواند سبزِ کاذب بسازد. `read_lock()` به‌جای `{}` روی غیاب، نشانگرِ صریحِ `UNKNOWN` برگرداند (fail-softِ فعلی یک ورودیِ غایب را به ورودیِ تهی تبدیل می‌کند). اجرای `run_lock()` با `SOURCE_4PY` غایب باید **non-zero exit** کند و `PULSE-EQUATIONS-LOCKED.json` را **بایت‌یکسان** بگذارد — با sha256ِ قبل و بعد تأیید شود. خروجی‌های عددیِ `e_shadow/delta_self/i_pred` قبل و بعد بایت‌یکسان بمانند.

### C9 — صداقتِ نقشه (`metadata_scan`)

- **هدف:** سه دروغ اینجا به هم می‌رسند. `_ops/telegram_center/metadata_scan.py` هرگز vault را اسکن نکرده؛ سقفِ `50_000` در **محلِ فراخوانی** (`_ops/telegram_center/center.py::_handle_map_callback` ⇒ `scan_metadata(max_files=50_000, max_seconds=60)`) hardcode است، در حالی که `DEFAULT_MAX_FILES` خودِ ماژول `200_000` است؛ و `EXCLUDE_DIRS` شاملِ `.git` هست ولی `.claude` نیست، پس ۴۹٬۹۳۹ از ۵۰٬۰۰۰ رکورد، نُه رونوشتِ کهنهٔ vault زیرِ `.claude/worktrees/` اند. کارتِ گزارش ۱۶٬۱۶۲ می‌گوید؛ markdownِ trackedِ واقعی ۲٬۱۲۷ است.
- **قاعده، نه نمونه:** `.claude` به `EXCLUDE_DIRS` اضافه شود؛ `truncated = files_seen >= max_files` یک فیلدِ درجه‌یک شود؛ شکستِ per-top-level-directory اضافه شود؛ و سقف از محلِ فراخوانی به **یک ثابتِ نام‌دار داخلِ خودِ scanner** منتقل شود تا هیچ call siteی نتواند دوباره بی‌صدا شکلِ نقشه را بازتعریف کند. هر call siteِ دومی که `max_files` خودش را پاس بدهد باید قراردادِ C3 را بشکند.
- **می‌خواند:** درختِ vault، با فیلترِ خودِ `metadata_scan`.
- **می‌نویسد:** همان مسیرهای امروزی (`_octopus/state/metadata_scan.json` و manifestِ متناظر)، همان نویسندهٔ واحد؛ یک کلیدِ جدید (`truncated`) و یک بلوکِ شکست.
- **چرا منبعِ حقیقتِ دوم نیست:** یک فیلترِ اسکن است و حالتی نگه نمی‌دارد؛ آنچه یک گزارشِ موجود می‌شمارد را تصحیح می‌کند، نه اینکه فهرستِ دومی بسازد. `metadata_scan` از قبل `excluded_dirs` را منتشر می‌کند، پس تغییرِ `EXCLUDE_DIRS` مقایسهٔ تاریخی را **آشکارا** می‌شکند نه بی‌صدا.
- **سنجهٔ پذیرش:** اسکنِ با استثنای `.claude` عددی به‌مراتب زیرِ ۵۰٬۰۰۰ با `truncated=false` بدهد و برشِ markdownاش در تلورانسِ اعلام‌شده‌ای از `git ls-files '*.md'` = ۲٬۱۲۷ بنشیند؛ کارت هر دو عدد را کنارِ هم نشان دهد. اسکنی که به سقف بخورد باید `UNKNOWN` رندر کند **حتی اگر عدد تولید کرده باشد**. سقفِ `max_seconds=60` می‌ماند — اسکنِ بازگشتی روی این ماشین پاتولوژیک است (دو آنتی‌ویروسِ لحظه‌ای).

### C13 — گاردِ tracked-بودن و محلِ اعلامِ فلگ — پیوند از Design 3

- **هدف:** دو دروغ‌گویِ ساختاری، یک قاعده. (الف) ماژولی که در رجیستریِ `_ops/tests/run_all.py` نام برده شده باید در `git ls-files` دیده شود — امروز `test_sync_agent.py` کامیت شده در حالی که **پنج فایلِ پیاده‌سازیِ `_ops/sync_agent.py` untracked اند**، پس یک clone تازه یک تستِ phantom می‌گیرد. (ب) هر رشتهٔ فلگی که در کدِ `_ops/` ارجاع می‌شود باید محلِ اعلام در `_ops/OCTOPUS-flags.cmd` داشته باشد، حتی با مقدارِ `0` — امروز `OCTOPUS_WIRE_PULSE_ARBITER`، `OCTOPUS_PF_MINIAPP` و `OCTOPUS_WIRE_DEADWRITE_CARDS` صفر بار در آن فایل ظاهر می‌شوند، پس هیچ تصمیمِ مالکی دربارهٔ آن‌ها خانهٔ بادوامی ندارد.
- **می‌خواند:** خروجیِ `git ls-files`، `_ops/tests/run_all.py`، `_ops/OCTOPUS-flags.cmd` (فقط نامِ محلِ اعلام)، `_ops/state/flags-loaded-{organism,center,cortex,live}.json`.
- **می‌نویسد:** **هیچ.**
- **چرا منبعِ حقیقتِ دوم نیست:** سازگاریِ آرتیفکت‌هایی را که از قبل وجود دارند assert می‌کند؛ حالتی از خودش ندارد و چیزی تعمیر نمی‌کند.
- **سنجهٔ پذیرش:** امروز باید دقیقاً گزارش کند: ۵ فایلِ پیاده‌سازیِ untracked پشتِ یک ورودیِ تستِ کامیت‌شده؛ ۳ فلگِ ارجاع‌شده در کد بدونِ محلِ اعلام؛ و `OCTOPUS_WIRE_SYNC_AGENT` حاضر در مجموعه‌های organism/center/cortex (۱۵۱) و غایب از پروسهٔ زنده (۱۴۸، ۱۶ ساعت عمر). اگر تمیز گزارش کند، git را نمی‌خواند.

### C14 — پروبِ تک‌پولرِ 409 (نهفته)

- **هدف:** `4d_system/brain/telegram_bot.py` روی `getUpdates` long-poll می‌کند و **همان نامِ envِ توکنِ مرکزِ زنده** را ارجاع می‌دهد. امروز نه پروسه‌ای هست نه scheduled task (شش تسکِ موجود: `OCTOPUS-Cortex-Watchdog`, `OCTOPUS-doctor-day`, `OCTOPUS-Live-Watchdog`, `OCTOPUS-MiniApp-Watchdog`, `OCTOPUS-TG-Center-Watchdog`, `OctopusLiveDataRefresh` — هیچ‌کدام برای 4D). پس خطر **نهفته** است نه فعال. قاعده: حداکثر یک نقطهٔ ورودیِ long-pollِ `getUpdates` از یک entrypointِ زنده یا تسکِ ثبت‌شده قابلِ رسیدن باشد.
- **می‌خواند:** درختِ سورس برای نقاطِ `getUpdates`؛ `Get-ScheduledTask` از مسیرِ PowerShellِ موجود (نه Bash — Bash اینجا بی‌صدا خالی برمی‌گرداند)؛ `_ops/state/pulse/telegram-poll.json` و `tg-center.json` برای هویتِ پولرِ زنده.
- **می‌نویسد:** **هیچ.**
- **چرا منبعِ حقیقتِ دوم نیست:** فهرستِ پروسه و تسک را مشاهده می‌کند؛ هویتِ هیچ پولری را جایی ثبت نمی‌کند.
- **سنجهٔ پذیرش:** امروز باید «۲ کاندید، ۱ قابلِ‌رسیدن» برگرداند و کارت بگوید «نهفته، نه فعال». پس از آرشیوِ 4D باید «۱ و ۱» بدهد. اگر هر وقت «۲ قابلِ‌رسیدن» برگرداند، مرکز در آستانهٔ ازدست‌دادنِ updateهایش است. به‌علاوه یک گاردِ fail-closed در خودِ `telegram_bot.py`: تا وقتی یک متغیرِ envِ صریحاً **متمایز** ست نشده، refuse به poll — سنجه: اجرا در سندباکس ⇒ خروجِ non-zero با صفر فراخوانیِ `getUpdates`، و شمارندهٔ 409ِ مرکزِ زنده روی صفر بماند.

### C16 — `sync_health` صادقانه UNKNOWN می‌شود

- **هدف:** بینِ لایهٔ قلب، 4D و ارگانیسم **هیچ مکانیزمِ syncی وجود ندارد؛ هرگز ساخته نشد**. ماژولی که دقیقاً برای پاسخ به «آیا در sync است» ساخته شد — `_ops/legs/sync_health.py` با `record_success/record_failure/divergence_check/snapshot` — هرگز چیزی ثبت نکرده و مسیرهایش روی دیسک وجود ندارند. `_ops/sync_agent.py` سه هدف دارد (`studio_pf`, `cartographer`, `lead`) و هرگز اجرا نشده؛ دفترش `_ops/state/sync-agent/` وجود ندارد.
- **می‌خواند:** `sync_health.snapshot()` و وجودِ `SYNC_DIR`/`HEALTH_PATH` و `_ops/state/sync-agent/`.
- **می‌نویسد:** **هیچ.** و صریحاً دفتر را **نمی‌سازد** — ساختنِ دایرکتوری یک اجرا را جعل می‌کند.
- **چرا منبعِ حقیقتِ دوم نیست:** `sync_health.py` تنها نویسندهٔ رکوردهای sync می‌ماند، اگر و وقتی که اجرا شود؛ این جزء فقط غیاب را گزارش می‌کند.
- **سنجهٔ پذیرش:** هر سه هدف `{status:'UNKNOWN', reason:'ledger absent — never executed', last_run_ts:null}` بخوانند. فیکسچری که **یک** رکوردِ مصنوعی می‌کارد باید دقیقاً همان هدف را سبز کند و دو تای دیگر `UNKNOWN` بمانند — این اثبات می‌کند غیاب به یک حکمِ سراسری تبدیل نمی‌شود. رابطهٔ heart↔4D↔organism به‌عنوانِ **غیابِ اعلام‌شده** رندر شود (`NO MECHANISM, never built`)، نه شکست.

### C15 — خطِ بدهیِ مالک در بریفِ صبح (فشارِ سن‌گرفتن) — پیوند از Design 3

- **هدف:** تنها مکانیزمِ **تشدید** در کلِ طرح: تصمیمی که نمی‌آید باید **بلندتر** شود، نه اینکه محو شود. یک جملهٔ خالص: «۱۹ کارت منتظر، قدیمی‌ترین ۸ روز؛ ۲۱ تصمیم بی‌اثر، قدیمی‌ترین ۸ روز».
- **می‌خواند:** C1.
- **می‌نویسد:** **هیچ** در گامِ مهندسی — یک تابعِ خالص با تستِ واحد، **بی‌سیم**. (نامِ نماد: `morning_text` در ماژولِ `brief`؛ مسیرِ دقیقِ فایل در لحظهٔ پیاده‌سازی resolve شود — در شواهد فقط با نامِ نماد ثبت شده.)
- **چرا منبعِ حقیقتِ دوم نیست:** یک تابعِ رندر روی تاشدگیِ C1؛ بینِ فراخوانی‌ها هیچ مقداری نگه نمی‌دارد.
- **سنجهٔ پذیرش:** تستِ واحد روی فیکسچر؛ سنِ صفر ⇒ جمله تولید نشود؛ ذخیرهٔ ناخوانا ⇒ `UNKNOWN`، هرگز «۰ کارت منتظر». **نوشتنِ جمله مهندسی است؛ فرستادنش رأی مالک است** (بندِ ۷).

---

## ۴. حلقهٔ تعامل

### چرخهٔ عمرِ واحد

```
(1) PROPOSED   prepare_rfc_card()          -> pending-cards.json          [تنها راهِ درخواستِ اثر]
(2) DELIVERED  mark_delivery()             PENDING -> LEASED -> SENT      [+ tg_message_ref، رو به جلو]
(3) DECIDED    persist_rfc_verdict()       SUBMITTED -> DECIDED           [فقط از callbackِ تلگرام]
                 ↳ verify_rfc_callback() اول؛ نوشتنِ بادوام پیش از ACK
(4) EFFECTED   claim_rfc_verdicts() -> begin_rfc_apply(operation_key)
                 -> ack_rfc_verdict(receipt_id)  -> APPLIED
                 ↳ بدونِ operation_key/receipt: RECONCILE_REQUIRED  (صادقانه، نه سبز)
(5) MEASURED   C1 fold -> C2 probe · C7 proposal_metrics · C6 mini-app · C15 morning brief
                 ↳ RECONCILE_REQUIRED کهنه  ⇒  C4  ⇒  دوباره مرحلهٔ (1)
```

### الف) ۱۹ کارتِ بی‌تصمیم: سطح‌آوردن و بستن

امروز: ۴۰ کارت `delivery=SENT`، ۱۹ تا `decision=SUBMITTED`، قدیمی‌ترین `2026-07-26` (در فاصلهٔ همین ممیزی ۱۸→۱۹؛ خودِ این رشد باید در سنجه دیده شود). هیچ سطحی عدد نمی‌گوید: پروب صفرِ تمیز می‌دهد، مینی‌اپ لیستِ خالی می‌دهد چون جدولِ `deliveries` اصلاً وجود ندارد، و `proposal_metrics` صفر است.

بستن، بدونِ هیچ صفحهٔ فرمانِ جدید و بدونِ هیچ نویسندهٔ جدید:

1. **سطح (خواندن):** یک تغییرِ predicate باعث می‌شود بدهی شمردنی شود، و بعد **سه سطح از یک فیلدِ یک فایل** می‌خوانند: پروبِ c6 عددِ ۱۹ می‌دهد، `get_approvals_state` همان ۱۹ را از پشتِ HMACِ همان gatewayِ `127.0.0.1:8774` می‌دهد، و بریفِ صبح در همان DMی که مالک از قبل می‌گیرد می‌گوید «۱۹ منتظر، قدیمی‌ترین ۸ روز». سه خواننده، یک ظرف، یک عدد؛ و اگر ذخیره ناخوانا باشد هر سه `UNKNOWN` می‌گویند و **هیچ‌کدام صفر نمی‌گوید**.
2. **تصمیم (مسیرِ بی‌تغییر):** زدنِ کارت در مینی‌اپ **هیچ تصمیمی نمی‌گیرد**. دکمه‌اش deep-link به همان پیامِ تلگرامی است، پس رأی هنوز روی کیبوردِ approval زده می‌شود که bindingِ توکن، `approval_id`ِ یک‌بارمصرف و cross-checkِ Chrono در `_ops/budget/approval_channel.py` و `_ops/outcomes/pending_card_recovery.py` نگه‌بانش‌اند.
3. **اثر:** فشارِ کلید ⇒ `persist_rfc_verdict` ⇒ `SUBMITTED→DECIDED` روی همان نویسندهٔ واحد ⇒ سپس `claim → begin_rfc_apply → ack_rfc_verdict` تا `APPLIED` با رسید.
4. **بازگشت:** در خوانشِ بعدی، عدد روی **هر سه سطح هم‌زمان** یک واحد می‌افتد. سنجهٔ پذیرشِ حلقه دقیقاً همین است — **به‌علاوهٔ شرطِ دومی که دو طرحِ دیگر نداشتند:** افتِ ۱۹→۱۸ به‌تنهایی قبول نیست، چون افتِ شمارنده را هم تصمیمی که اثر کرد تولید می‌کند و هم تصمیمی که در `RECONCILE_REQUIRED` با رسیدِ تهی افتاد (کاری که هر ۲۱ تصمیمِ قبلی کردند). **پذیرش = افتِ شمارنده + یک ردیفِ `APPLIED` با `receipt_id` ناتهی در `rfc_decision`.**
5. **تشدید:** بریف سنِ قدیمی‌ترین کارت را گزارش می‌کند، پس تصمیمی که نمی‌آید هر روز بلندتر می‌شود.

همین رفتار شاملِ ۶ کارتِ mission در `_ops/state/test_cycle/owner_cards/` با `verdict: ""` هم می‌شود: به‌عنوان بدهی شمرده می‌شوند و تهی‌بودنشان `UNDECIDED` رندر می‌کند، **هرگز «تأییدشده با سکوت»**.

### ب) سه مثالِ کاری با **یک شکلِ کارت**

پاکت یکی است (`kind/rfc_id/summary/owner/nonce/expires_at/token_sha256/delivery/decision/created_ts/updated_ts`)، کیبورد یکی، ماشینِ حالت یکی، leaseِ exactly-once یکی. تنها چیزی که فرق می‌کند **اثری است که وقوعش را اثبات می‌کند**:

| کارت | effector | `operation_key` | `receipt_id` (رسید) |
|---|---|---|---|
| تغییرِ setpointِ قلب | نویسندهٔ موجودِ setpoint | شناسهٔ نوشتِ setpoint | نوشتِ انجام‌شده روی `_ops/state/pulse/heart-setpoint-latest.json` با `ts` درونیِ جدید |
| آرشیوِ 4D | جابه‌جاییِ `4d_system/` | شناسهٔ عملیاتِ انتقال | مسیرِ سنگ‌قبر: `_Archive/Projects/2026 - 4d_system/` |
| مسلح‌کردنِ یک فلگ | افزودنِ اعلان به `_ops/OCTOPUS-flags.cmd` | شناسهٔ ویرایش | شمارِ فلگِ زنده پس از ری‌استارت (مثلاً `148 → 151`) |

نتیجهٔ عملی برای مالک: **قلب، sync، 4D و نقشه یکپارچه‌سازیِ اختصاصی نمی‌گیرند — هرکدام یک کارت می‌گیرند.** تعدادِ سطح‌هایی که باید تماشا شود کم می‌شود، نه اینکه هر سطح جداگانه صادق‌تر شود.

> نکتهٔ CRLF (درسِ ثبت‌شده): `_ops/OCTOPUS-flags.cmd` پایان‌خطِ CRLF دارد و باربر است. ویرایش با ابزارِ متنیِ ساده آن را می‌کشد و `cmd.exe` یک‌درمیان می‌خواند (سابقه: مرکز با ۵۹ از ۱۵۶ فلگ بالا آمد). effectorِ کارتِ فلگ باید CRLF را حفظ کند و **با اثر** سنجیده شود، نه با «انجام شد».

---

## ۵. ترتیبِ اجرا، از کوچک‌ترین

| # | گام | نوع | چه چیزی را باز می‌کند | سنجهٔ پذیرش | شعاعِ انفجار |
|---|---|---|---|---|---|
| 1 | `_ops/provenance.py` (C10): `Stamp/stamp()/Mode`، خالص، صفر I/O، **صفر importer در روزِ اول** | SAFE | هر عددِ صادقی که بعداً منتشر می‌شود؛ بدونِ آن C1 اسکالرِ برهنه می‌دهد و تلهٔ `control_law` تکرار می‌شود | باتریِ سه‌جهشه: `HELD` روی ts عقب‌رفته، `CONSTANT/dof=1` روی ۲۸۸ نمونهٔ یکسان، `UNKNOWN` بدونِ کلیدِ `value` (⇒ `float()` خطا) | **هیچ.** هیچ ماژولی هنوز importش نمی‌کند |
| 2 | `lifecycle_fold` (C1)، فقط خواندنی، خروجی تمبرخورده | SAFE | مدلِ خواندنِ C2/C4/C6/C7/C15؛ و **کشفِ `effected=0`** روی سطحی که کسی نمی‌بیند | `40/40/21/0/19/21`, `oldest=2026-07-26`؛ AST: صداکنندهٔ تولیدیِ `load_rfc_verdicts` از ۰ به ۱؛ جهشِ دوجهته `19↔18` | **هیچ نوشتنی.** صفر بایتِ تغییر در `_ops/state/` (harness اول وارد شود) |
| 3 | `predicate_never_matches` **اول**، بعد بازنشانهٔ `_probe_tg_stale_delivery` (C2) | SAFE | صفِ نامرئی را روی سطحی که doctor از قبل منتشر می‌کند، دیدنی می‌کند — و ثابت می‌کند قاعده نمونه را بی‌راهنمایی می‌گیرد | قاعده **پیش از** رفع روی predicateِ خرابِ `delivery` شلیک کند؛ سپس پروب `0→19`؛ فیکسچرِ بی‌`decision` ⇒ `UNKNOWN/-1` نه `0` | خروجیِ یک پروب |
| 4 | `metadata_scan` (C9): `.claude` به `EXCLUDE_DIRS`، `truncated`، انتقالِ سقف به ثابتِ ماژول | SAFE | حذفِ ۴۹٬۹۳۹ فایلِ phantom از تصویرِ ارگانیسم از خودش | مجموع زیرِ ۵٬۰۰۰ با `truncated=false`؛ برشِ markdown در تلورانسِ `git ls-files '*.md'`=۲٬۱۲۷؛ اسکنِ به‌سقف‌خورده ⇒ `UNKNOWN` | اعدادِ کارتِ نقشه در اسکنِ بعدی عوض می‌شوند؛ هیچ فلگ/پروسه‌ای |
| 5 | `sog_math` (C8): `run_lock()` fail-closed با ردِ صریحِ رشتهٔ `"unavailable"`؛ `read_lock()` به‌جای `{}` مقدارِ `UNKNOWN`؛ `sog_provenance` روی `heart-shadow-latest.json` | SAFE | حذفِ یک سبزِ کاذبِ ایستاده روی سه گیتِ زندهٔ قلب | `sog_provenance="UNVERIFIABLE"`؛ `run_lock()` ⇒ non-zero و sha256ِ فایلِ قفل قبل/بعد یکسان؛ خروجی‌های عددی بایت‌یکسان | یک فیلد روی ظرفی با ~۱۵ خواننده؛ صفر تغییرِ عددی |
| 6 | گاردِ fail-closedِ `4d_system/brain/telegram_bot.py` + پروبِ تک‌پولر (C14) | SAFE | خنثی‌کردنِ 409ِ نهفته **پیش از** هر دست‌زدنی به دایرکتوریِ 4D | سندباکس: خروجِ non-zero با صفر `getUpdates`؛ پروب: «۲ کاندید / ۱ قابلِ‌رسیدن، نهفته نه فعال» | یک ماژولِ بازنشسته و غیرِ در حالِ اجرا |
| 7 | گاردِ حضورِ `ACTIVATION-*` + ثبتِ `_ops/ACTIVATION-HEARTSTATE.flag` به‌عنوانِ **باربر علی‌رغمِ ظاهر** | SAFE | جلوگیری از قتلِ بی‌صدای نویسنده‌ای که هر ~۵۷ ثانیه می‌نویسد | حذفِ فایل در درختِ موقت ⇒ تست قرمز با نامِ فایل | تست + مستندات |
| 8 | گاردِ tracked-بودن + محلِ اعلامِ فلگ (C13) | SAFE | بستنِ دو کلاسِ phantom | گزارشِ دقیقِ: ۵ فایلِ untracked، ۳ فلگِ بی‌اعلان، `151 vs 148` | فقط چک؛ روزِ اول بلند است — همین هدف است |
| 9 | `sync_health.snapshot()` ⇒ `UNKNOWN` روی غیابِ مسیرها (C16) | SAFE | غیاب دیگر به سبز/صفر لاندری نمی‌شود | سه هدف `UNKNOWN`؛ فیکسچرِ تک‌رکوردی فقط همان یکی را سبز کند | یک وضعیتِ مشتق از سبزِ ضمنی به `UNKNOWN`ِ صریح |
| 10 | `pulse_arbiter` (C11): تمبرِ سه رأی، `n_moving/n_held/n_constant`، **ممنوعیتِ `consensus` وقتی `n_moving<=1`** | SAFE | بلندترین دروغِ قابلِ‌دیدنِ ارگانیسم، بدونِ هیچ فلگی (`arbiter_snapshot()` از قبل بی‌قید است) | یک بیت پس از ری‌استارت: `driver='solo:rhythm'`, `n_present=3`, `n_moving=1`، دیده‌شده از `scanner.scan()`؛ جهش: ریتم را ثابت کن ⇒ `n_moving=0` و **هرگز** `consensus`؛ تیکِ پس‌ازری‌استارت `UNKNOWN` نه `LIVE` | رشتهٔ `driver` در `ORGANISM-STATE.json['arbiter']`؛ خواننده‌ها **پیش از** فرود با AST شمرده شوند |
| 11 | گاردِ انحصارِ نوشتن روی `ORGANISM-STATE.json` (C12) | SAFE | بستنِ ساختاریِ کلاسِ «دو نویسنده»، پیش از اینکه C7 در همان فایل بنویسد | جهش: نویسندهٔ دوم در درختِ موقت ⇒ قرمز با `file:symbol`؛ حالتِ **غیرمستقیم** جداگانه جهش‌آزموده | فقط تست |
| 12 | `scanner.py`: `_m()` تمبرها را در `PROV` ادغام کند؛ `UNKNOWN` رنگِ سوم؛ تغییرِ نامِ `self_awareness_pct` → `docstring_coverage_pct` | SAFE | حذفِ نظرِ دومِ موجود (doctor از مقادیر، dashboard از mtime) و رفعِ تصادمِ دو کمیتِ هم‌نام | `_octopus/state/octopus_state.json` به‌جای سبز، `CONSTANT since 2026-07-18T12:04:31, 0 writers, 0 readers` رندر شود؛ هر ردیفِ سبزِ `self_awareness` پس از این = رگرسیون | شکلِ خروجیِ اسکنِ doctor؛ `ingest.ingest_scan()` **در همان تغییر** بررسی شود (نویسنده و خواننده با هم) |
| 13 | رندرِ کارت‌های قلب/نقشه/sync از روی تمبرها در `dashboard/server.py` و `live/server.py`؛ ردیفِ `work-health.json` بماند با برچسبِ `reader-gated-off` | SAFE | اولین نقطه‌ای که مالک تفاوت را می‌بیند | کارتِ قلب سرواژه‌اش از `consensus` به `solo:rhythm` عوض شود و دو ردیفِ `dof=1` بگیرد؛ کارتِ نقشه ۱۶٬۱۶۲ را نگوید؛ کارتِ sync چهار ردیفِ `UNKNOWN`. **هیچ کارتی حق ندارد عددی رندر کند که تمبرش `UNKNOWN` است** | دو سطحِ HTTPِ محلی، فقط‌خواندنی |
| 14 | `CardSpec` (C5): تستِ قرارداد؛ بازنشستگیِ `mark_rfc_consumed` | SAFE | «کارتِ هم‌شکل» را از آرزو به قاعده تبدیل می‌کند و مسیری را که ۲۱ پایانهٔ بی‌رسید ساخت می‌بندد | سه فیکسچر ⇒ `APPLIED` با رسیدهای متمایز؛ فیکسچرِ بی‌`operation_key` ⇒ `RECONCILE_REQUIRED`؛ صفر بایتِ تغییر در `_ops/state/` | تست + یک بازنشستگی |
| 15 | **اولین کارتِ تجمیعیِ ۲۱ ردیف با دست ساخته و ارسال شود** (C4 هنوز خاموش) | SAFE (ساخت) → OWNER_VOTE (تصمیمش) | اثباتِ زندهٔ مسیرِ رسید — پیش‌شرطِ بی‌قیدوشرطِ C4 | یک ردیف در `rfc_decision` به `state=APPLIED` با `receipt_id` ناتهی برسد: **اولین `APPLIED` در کلِ تاریخِ آن جدول**؛ با `updated_ts` درونی سنجیده شود، نه mtime | یک کارتِ اضافه در دایجستِ موجود |
| 16 | فعال‌کردنِ C4 (تجمیعِ خودکار، سقفِ یک کارت در هر دایجست) | SAFE، **مشروط به گامِ ۱۵** | توقفِ حلقه دوباره وارد حلقه می‌شود | همان سنجهٔ C4؛ و اگر ۱۵ پاس نشده باشد، C4 روشن نمی‌شود | یک ردیف در ظرفِ کارت‌ها، فقط از راهِ `_mutate_store` |
| 17 | `proposal_metrics` (C7): یک چرخهٔ کامل در سایه، لاگِ قدیم/جدید، سپس جایگزینیِ کلید | SAFE | حذفِ صفرهایی که `goal_directed.py` هفته‌هاست در برابرشان تفاضل می‌گیرد | `proposals_delivered 0→40`، `proposal_outcomes 0→21`، `proposals_effected = 0` (صریح، نه پنهان) | یک کلید در `ORGANISM-STATE.json` و یک مصرف‌کننده؛ برگشت‌پذیر |
| 18 | `wiring_contract` (C3) با هر سه قاعدهٔ باربر | SAFE | بستنِ کلاسِ نامه‌دانِ مرده — **عمداً بعد از C4/C5** تا قرمز جایی برای رفتن داشته باشد (یک کارتِ هم‌شکل) | دقیقاً همان هفت موردِ شناخته‌شده را بی‌راهنمایی نام ببرد؛ ورودیِ معافی که card idاش resolve نشود، خودش قرمز | سوییت قرمز می‌ماند تا تعیین‌تکلیف. **باید صریحاً «عمدی» اعلام شود** وگرنه ایجنتِ بعدی با گشادکردنِ معافیت «درستش می‌کند» |
| 19 | نمای خواندنیِ مینی‌اپ (C6) زیرِ `/api/miniapp`ِ موجود، با whitelistِ سخت و تستِ byte-grep و تستِ ناوردایِ دیوارِ 405 | SAFE | حذفِ خوانشِ `outcomes.db::deliveries` (یک حقیقتِ دومِ در حالِ شکل‌گیری) و بستنِ نیمهٔ خواندنیِ حلقه | `count==19` برابرِ پروب؛ `POST` ⇒ `405` و فایل بایت‌یکسان؛ byte-grepِ بدنه صفر رخدادِ `token_sha256`/`nonce`؛ فایلِ gateway بایت‌یکسان | **هیچ تا زمانِ مسلح‌شدن** — مسیرها بدونِ اعلامِ فلگ 404 می‌مانند |
| 20 | خطِ بدهیِ مالک برای بریف (C15) به‌صورتِ تابعِ خالص، **بی‌سیم**، با تستِ واحد | SAFE | جداکردنِ «نوشتنِ جمله» از «فرستادنِ جمله» | تستِ واحد؛ ذخیرهٔ ناخوانا ⇒ `UNKNOWN` نه «۰ منتظر» | هیچ، تا گامِ بعد |
| 21 | اعلامِ سه فلگِ بی‌محلِ اعلان در `_ops/OCTOPUS-flags.cmd` **با مقدارِ `=0`** | OWNER_VOTE (سبک) | به رأی‌های آینده خانهٔ بادوام می‌دهد. **اعلام با `=0` مسلح‌کردن نیست** | هر سه نام در فایل حاضر؛ CRLF حفظ شده (با اثر پس از ری‌استارت سنجیده شود، نه با ظاهر) | فقط فایلِ فلگ؛ تا ری‌استارت هیچ رفتاری عوض نمی‌شود |
| 22 | ری‌استارتِ پروسه‌های زنده برای رفعِ رانشِ ۳ فلگی | OWNER_VOTE | `OCTOPUS_WIRE_SYNC_AGENT` و هر اعلانِ تازه وارد پروسهٔ زنده شود | شمارِ فلگِ زنده `148 → 151`؛ **همان کد، خروجیِ متفاوت، صفر تغییرِ کد** | تپش و مسیرِ پول برای پنجرهٔ ری‌استارت قطع می‌شود |
| 23 | مسلح‌کردنِ `OCTOPUS_WIRE_DEADWRITE_CARDS` (`=1`) + ری‌استارت | OWNER_VOTE | کارتِ dead-write رندر می‌شود | `work-health.json` از `DEAD_LETTERBOX` به سبز؛ کارت `ts` **درونی** را نشان دهد نه mtime؛ صفر تغییرِ کد بینِ دو مشاهده | دو کارتِ فقط‌خواندنی |
| 24 | مسلح‌کردنِ `OCTOPUS_PF_MINIAPP` (`=1`) | OWNER_VOTE | نمای خواندنیِ چرخهٔ عمر روی تونل زنده می‌شود | نما ۱۹ کارتِ راکد را رندر کند **و** `POST` به 8774 ⇒ `405` با فایلِ بایت‌یکسان؛ بدونِ HMACِ معتبر ⇒ 403 | سطحِ خواندنی از راهِ تونلِ cloudflared — دلیلِ اینکه رأی است نه کار |

---

## ۶. تعیین‌تکلیفِ 4D

سه چیزِ **جدا** نامِ 4D را حمل می‌کنند. عمداً با هم حل نمی‌شوند.

### ۶.۱ دایرکتوری — انتقال، نه حذف

`4d_system/` از `2026-07-18` بازنشسته است و سنگ‌قبرِ خودش را دارد: `4d_system/DEPRECATED.md`. دیمنش در کلِ عمرش **۳ تیک** اجرا کرده و «احیای» `2026-08-02` یک اسموک‌تستِ یک‌ثانیه‌ای بود (`resumed 23:10:12`, `stopped 23:10:13`) که pidِ ثبت‌شده‌اش مرده است.

- **حکم:** انتقال به `_Archive/Projects/2026 - 4d_system/` + یادداشتِ سنگ‌قبر که محتوای `DEPRECATED.md` را با خود جلو می‌برد. **هرگز `rm`.**
- **نوع:** OWNER_VOTE، به شکلِ کارتِ استاندارد. `receipt_id` = مسیرِ سنگ‌قبر.
- **پیش‌شرط:** گامِ ۶ جدولِ بالا (گاردِ fail-closed + پروبِ تک‌پولر) **باید قبلاً فرود آمده باشد** — دقیقاً چون «انتقالِ آرشیو» همان عملیاتی است که وسوسه می‌کند کسی «یک‌بار چک کند هنوز اجرا می‌شود».
- **پس از انتقال:** پروبِ تک‌پولر باید «۱ و ۱» بدهد و هیچ مسیری زیرِ `4d_system/` نباید در هیچ ورودیِ رجیستری با وضعیتِ LIVE بماند.

### ۶.۲ تصمیمِ `SOURCE_4PY` — تنها پیوندِ زنده

`_ops/heart/sog_math.py::SOURCE_4PY = os.environ.get("SOG_4PY_PATH", r"C:\Users\Armin\Desktop\4D\4.py")`. آن فایل و پوشهٔ والدش موجود نیستند، `SOG_4PY_PATH` هیچ‌جا ست نشده، و جست‌وجوی سراسری هیچ نسخه‌ای از `4.py` در vault پیدا نمی‌کند. امروز چیزی نمی‌شکند چون `_ops/heart/shadow.py` و `_ops/heart/control_law.py` فقط `read_lock()` را صدا می‌زنند.

- **آنچه ایجنت انجام می‌دهد (SAFE، گامِ ۵):** صداقت، نه بازسازی. `run_lock()` fail-closed می‌شود و **رشتهٔ لفظیِ `"unavailable"`ِ خروجیِ `_sha256_file()` را صریحاً رد می‌کند** — گاردی که فقط `null` را تست کند از کنارِ آن رد می‌شود و قفلی می‌نویسد که هنوز سه گیت را `locked` نشان می‌دهد. `read_lock()` به‌جای `{}` مقدارِ `UNKNOWN` برمی‌گرداند. سه گیت به‌جای `locked` خام، `locked (اصالت از 2026-07-10 غیرقابلِ راستی‌آزمایی)` رندر می‌کنند. **هیچ مقدارِ گیتی دست نمی‌خورد. قفل دوباره اجرا نمی‌شود. جایگزینِ ساختگیِ `4.py` ساخته نمی‌شود.**
- **آنچه مالک تصمیم می‌گیرد (OWNER_VOTE):** یکی از سه: (الف) `4.py` را از بکاپ/ماشینِ دیگر بازگردان؛ (ب) `SOG_4PY_PATH` را به نسخهٔ بازمانده اشاره بده؛ (ج) آرتیفکتِ `2026-07-10` را برای همیشه منجمد بپذیر با سنگ‌قبر.
- **سنجهٔ پذیرشِ گزینه‌های (الف)/(ب):** هشِ بازمحاسبه‌شده **دقیقاً برابرِ `f856b1be…`ِ ثبت‌شده در همان فایلِ قفل** باشد ⇒ `VERIFIED` و آرتیفکتِ ۰۷-۱۰ عطف‌به‌ماسبق اعتبار می‌گیرد. نابرابر ⇒ `MISMATCH`، نه سبز. صرفِ **حضورِ** یک فایل هرگز کافی نیست.

### ۶.۳ رباتِ 409ِ نهفته

`4d_system/brain/telegram_bot.py` روی `getUpdates` long-poll می‌کند و همان **نامِ envِ توکن** مرکزِ زنده را ارجاع می‌دهد. امروز نه پروسه‌ای هست نه scheduled taskی (شش تسکِ موجود هیچ‌کدام 4D نیستند)، پس خطر **نهفته** است. آنچه امن نگهش می‌دارد **گارد است، نه نبودِ پروسه** — افزودنِ یک تسک در آینده دوباره مسلحش می‌کند.

- گاردِ fail-closed در خودِ ماژول + پروبِ ناوردایِ تک‌پولر (C14). قرمزبودنِ پروب در اولین اجرا با نام‌بردنِ همین ماژول، **خروجیِ درستِ اول** است.
- `4d_system/.env` در `2026-08-02 23:09` لمس شده، یک دقیقه پیش از اسموک‌تست. **اینکه توکنی دارد یا نه نامعلوم است و باید نامعلوم بماند** — `.agentignore` الگویِ `*.env` را می‌گیرد و منشور خواندن/echo کردنش را ممنوع می‌کند. گارد خواندنش را **غیرلازم** می‌کند. اگر مالک نتواند وجودِ توکنِ زنده را رد کند، شاخهٔ امن چرخشِ secret طبقِ `04 - Architect System/architect/01-Project/SECRETS-ROTATION-CHECKLIST.md` است — و چرخش یک رأی است. اگر انتقالِ آرشیو این فایل را جابه‌جا کند، سنگ‌قبر فقط **مسیر** را ثبت می‌کند، هرگز محتوا را.

### ۶.۴ خارج از دامنهٔ 4D، ولی نزدیکش

`_ops/budget/approval_channel_merge.py::UnifiedApprovalChannel` خودش را «ORPHAN 2026-07-16 → REVIVED 2026-08-02 … Zero live callers remains» اعلام می‌کند: یک پلِ کارکننده که سوییتِ تست مرده طبقه‌بندی‌اش می‌کند. این یک **اختلافِ طبقه‌بندی** است نه سؤالِ 4D. یک ردیف در رجیستریِ C3 با خواننده‌های اعلام‌شده می‌گیرد و قاعده تکلیفش را روشن می‌کند: یا صداکنندهٔ واقعی، یا سنگ‌قبر با card id. **یک پلِ کارکننده به‌حرفِ یک سوییت کنارِ یک دایرکتوریِ مرده آرشیو نمی‌شود** — این دقیقاً همان درهم‌ریختنی است که بندِ ۵ ممنوع می‌کند.

---

## ۷. تصمیم‌های مالک

فقط این‌ها رأی‌اند. باقیِ سند کارِ مهندسیِ امن است.

1. **مسلح‌کردنِ سه فلگِ بی‌اعلان — به دو مرحله.** اعلام با `=0` (کارِ ایجنت، گامِ ۲۱) در برابرِ `=1` (رأی). سه نام: `OCTOPUS_WIRE_PULSE_ARBITER`، `OCTOPUS_PF_MINIAPP`، `OCTOPUS_WIRE_DEADWRITE_CARDS`.
   **هزینهٔ تصمیم‌نگرفتن:** مسیرهای مینی‌اپ 404 می‌مانند و نمای صفِ تصمیم هرگز به دستِ شما نمی‌رسد؛ کارتِ dead-write رندر نمی‌شود و مخزن هم‌چنان شبیهِ «شکاف بسته شد» به‌نظر می‌رسد.
2. **ری‌استارتِ پروسه‌های زنده.** پروسهٔ زنده ۱۶ ساعت است روی ۱۴۸ فلگ می‌دود در حالی که organism/center/cortex هرکدام ۱۵۱ دارند.
   **هزینهٔ تصمیم‌نگرفتن:** رانشِ فلگ باقی می‌ماند؛ هر رأیِ فلگی که بدهید تا ری‌استارتِ بعدی بی‌اثر است — و C11/C13 تا آن لحظه نمی‌توانند «همان کد، خروجیِ متفاوت» را اثبات کنند.
3. **اولین کارتِ تجمیعیِ ۲۱ ردیفِ `RECONCILE_REQUIRED`** (دستی ساخته می‌شود، سوارِ دایجستِ روزانهٔ موجود؛ کانالِ outboundِ جدید نیست).
   **هزینهٔ تصمیم‌نگرفتن:** مسیرِ اثر هرگز روی ذخیرهٔ زنده اثبات نمی‌شود، پس C4 هرگز روشن نمی‌شود و هر تصمیمِ آیندهٔ شما به همان چاهِ ۰-از-۲۱ می‌ریزد.
4. **۱۹ کارتِ منتظر (قدیمی‌ترین `2026-07-26`) + ۶ کارتِ missionِ با `verdict: ""`.**
   **هزینهٔ تصمیم‌نگرفتن:** صف رشد می‌کند (در فاصلهٔ همین ممیزی ۱۸→۱۹) و بریفِ صبح هر روز بلندتر می‌شود. هیچ ایجنتی حق تصمیم ندارد.
5. **تعیین‌تکلیفِ سه نامه‌دانِ قلب** — `heart-params-shadow.jsonl`، `heart-setpoint-audit.jsonl`، `_ops/state/heart-wires-latest.json`. برای هرکدام: خوانندهٔ محتوایی، یا `_Archive` + سنگ‌قبر. «همین‌طور بماند» گزینه نیست.
   **هزینهٔ تصمیم‌نگرفتن:** C3 قرمز می‌ماند و ایجنتِ بعدی وسوسه می‌شود با گشادکردنِ معافیت سبزش کند. توجه: دربارهٔ `heart-setpoint-audit.jsonl` **در تلگرام به شما گفته شده که این ممیزی وجود دارد** و ۷ روز است هیچ‌کس نمی‌خواندش؛ و `heart-wires-latest.json` فریبنده‌ترین است چون فلگش `1` و mtimeاش تازه است.
6. **آشتیِ armِ `heartstate`** — از fallbackِ فایلِ `_ops/ACTIVATION-HEARTSTATE.flag` به فلگِ envی که خودش اعلام می‌کند.
   **هزینهٔ تصمیم‌نگرفتن:** یک نویسندهٔ هر-۵۷-ثانیه‌ای روی فایلی می‌ایستد که از `2026-07-23` دست‌نخورده و هر ممیزیِ فلگ آن را «خاموش» می‌خواند. گاردِ گامِ ۷ تله را می‌گیرد، ولی حذفش نمی‌کند. **سنجهٔ پذیرش: تداومِ نوشتن با cadenceِ ~۵۷ ثانیه در طولِ تغییر، سنجیده با `ts` درونی.**
7. **آرشیوِ `4d_system/` به `_Archive/Projects/2026 - 4d_system/` + سنگ‌قبر.**
   **هزینهٔ تصمیم‌نگرفتن:** 409ِ نهفته یک scheduled task با مرکزِ زنده فاصله دارد. (گارد آن را مهار می‌کند؛ انتقال حذفش می‌کند.)
8. **تعیین‌تکلیفِ `SOG_4PY_PATH`** — بازیابی، اشاره به نسخهٔ بازمانده، یا پذیرشِ انجمادِ دائم با سنگ‌قبر. **و** اینکه آیا `4d_system/.env` باید فرضِ حاملِ توکن گرفته شود و چرخش انجام شود.
   **هزینهٔ تصمیم‌نگرفتن:** سه گیتِ زندهٔ قلب برای همیشه روی آرتیفکتی می‌ایستند که اصالتش قابلِ بازراستی‌آزمایی نیست. (چیزی نمی‌شکند؛ فقط برچسبْ `UNVERIFIABLE` می‌ماند.)
9. **تعیین‌تکلیفِ پنج فایلِ untrackedِ `_ops/sync_agent.py`** — کامیت، یا انتقال به `_Archive` با سنگ‌قبر.
   **هزینهٔ تصمیم‌نگرفتن:** cloneِ تازه یک تستِ phantom می‌گیرد و مخزن دربارهٔ خودش دروغ می‌گوید. (توجه: هیچ‌کدام از دو گزینه ادعا نمی‌کند sync کار می‌کند — `_ops/state/sync-agent/` هنوز وجود ندارد و مکانیزمِ heart↔4D↔organism **هرگز ساخته نشده**.)
10. **خطِ بدهیِ مالک در بریفِ صبحی که واقعاً فرستاده می‌شود.**
    **هزینهٔ تصمیم‌نگرفتن:** تنها مکانیزمِ تشدیدِ طرح خاموش می‌ماند و صف دوباره در سکوت رشد می‌کند. (افزودنِ محتوا به یک DMِ زمان‌بندی‌شده هنوز outbound است.)
11. **tracked-کردنِ `_ops/OCTOPUS-flags.cmd` (امروز gitignored).** **مشروط:** فقط پس از تأییدِ اینکه هیچ مقدارِ secretی داخلش نیست. هدرِ خودِ فایل ادعا می‌کند non-secret است و نامِ secretها جداگانه در snapshotهای `flags-loaded-*` نگه‌داری می‌شوند — ولی این ادعا **در همین ممیزی مستقلاً راستی‌آزمایی نشده و تا آن لحظه UNKNOWN است**.
    **هزینهٔ تصمیم‌نگرفتن:** هر رأیِ مسلح‌کردن در این سند بی‌تاریخچه و بازتولیدناپذیر می‌ماند — همان شکستی که در درس‌های همین vault ثبت شده.
12. **(اختیاری، ارزان)** اعلامِ `OCTOPUS_WIRE_PULSE_ARBITER=1` + ساختِ `_ops/ACTIVATION-PULSE-ARBITER.flag` **فقط برای سریِ زمانیِ روی دیسک**. خوانشِ آربیتر از قبل در `ORGANISM-STATE.json` زنده است و doctor و داشبورد می‌خوانندش، پس هیچ‌چیز به این وابسته نیست. **`wire_open` باز نمی‌شود** — آن تغییرِ رفتار است نه رصدپذیری.
    **هزینهٔ تصمیم‌نگرفتن:** هیچ. فقط `arbiter-latest.json` / `arbiter-shadow.jsonl` هرگز ساخته نمی‌شوند و تاریخچه‌ای برای تحلیلِ بعدی نمی‌ماند. **شرط:** پیش از اولین نوشتن باید زیرِ C3 با خوانندهٔ نام‌دار ثبت شوند، وگرنه نامه‌دانِ مردهٔ بعدی‌اند.

---

## ۸. غیرهدف‌های عمدی

1. **صفحهٔ فرمانِ دوم ساخته نمی‌شود.** مینی‌اپ هیچ verbی نمی‌گیرد. دیوارِ 405 و allowlistِ gateway بایت‌به‌بایت ناوردا می‌مانند و یک تست همین را assert می‌کند. `persist_rfc_verdict` فقط از callbackِ تلگرام قابلِ رسیدن است و **این reachability تست می‌شود، نه کامنت**.
2. **پرتاب‌کنندهٔ «resurface» ساخته نمی‌شود.** هر ۴۰ کارت `delivery=SENT` اند؛ هیچ‌چیز در تحویل گم نشده. بازتحویل مشکلی را حل می‌کند که رخ نداده و یک رأیِ outbound را خرجِ اسپم می‌کند.
3. **«باس»/فضای‌نامِ جدید روی `ORGANISM-STATE.json` ساخته نمی‌شود.** فقط کلیدِ **موجودِ** `proposal_metrics` منبعش تصحیح می‌شود و کلیدِ **موجودِ** `arbiter` فیلد می‌گیرد. شش فضای‌نامِ مشتق روی داغ‌ترین فایلِ مسیرِ تیک نمی‌رود؛ projection زیرِ یک نویسنده هم بالاخره یک کش است.
4. **`wire_open` باز نمی‌شود.** آربیتر همچنان مشورتی است؛ رانندهٔ تپش هم‌چنان `cardiac.effective_period(...)` در `_ops/organism.py` است. تصحیحِ برچسبِ `consensus → solo:rhythm` رصدپذیری است، نه تغییرِ رفتار.
5. **قفلِ معادلات دوباره اجرا نمی‌شود و هیچ مقدارِ گیتی تغییر نمی‌کند.** `4.py`ِ ساختگی تولید نمی‌شود. `PULSE-EQUATIONS-LOCKED.json` رکورد می‌ماند.
6. **هیچ‌چیز حذف نمی‌شود.** نه `4d_system/`، نه نامه‌دان‌ها، نه `octopus_core/`، نه `_ops/ACTIVATION-HEARTSTATE.flag`. انتقال + سنگ‌قبر، همیشه.
7. **کانالِ outboundِ جدید ساخته نمی‌شود.** کارتِ تجمیعی سوارِ دایجستِ روزانهٔ موجود می‌شود و خطِ بدهی سوارِ DMِ موجود.
8. **این طرح sync را نمی‌سازد.** بینِ قلب، 4D و ارگانیسم مکانیزمی وجود ندارد و اینجا هم ساخته نمی‌شود؛ فقط به‌عنوانِ **غیابِ اعلام‌شده** منتشر می‌شود. `_ops/state/sync-agent/` عمداً ساخته نمی‌شود — ساختنِ دایرکتوری یک اجرا را جعل می‌کند.
9. **این طرح ۱۹ کارت را تصمیم نمی‌گیرد و `delta_self` را مثبت نمی‌کند.** ابزارِ صادق را با پیشرفت اشتباه نگیرید — این حالتِ شکستِ خودِ این لایه است.
10. **گاردی برای سبزشدن بازنویسی نمی‌شود.** C3، C13 و fail-closeِ `sog_math` روزِ اول بلند و قرمزند؛ همین هدف است. تناقض به مالک می‌رود، نه به آستانه. معافیت باید یک card id را نام ببرد که resolve شود.
11. **۲۱ ردیفِ `RECONCILE_REQUIRED` نویزِ مهاجرت نیستند** و به‌صورتِ دسته‌ای پاک نمی‌شوند: ۲۰ زمان‌مُهرِ متمایز از ۰۷-۲۶ تا ۰۷-۳۱ یعنی این‌ها تأییدهای واقعیِ مالک‌اند که هرگز اعمال نشدند.
12. **هیچ فایلِ `.env` خوانده، echo یا کپی نمی‌شود** و هیچ secretی در کد، نوت، کارت، لاگ یا HANDOFF نوشته نمی‌شود — شاملِ محتوای احتمالیِ `4d_system/.env` که وضعیتش **UNKNOWN** است و UNKNOWN می‌ماند.