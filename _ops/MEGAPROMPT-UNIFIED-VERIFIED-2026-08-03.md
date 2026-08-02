---
type: megaprompt
title: OCTOPUS — UNIFIED / VERIFIED (scan → repair → sync)
status: active
audience: "Sonnet / Opus 5 — UltraThink / UltraCode"
merged_from: [DEEP-SCAN-V2, REPAIR-V2, ULTRATHINK-FULL, LEG-SYNC]
verified_against: "master 7ecb407 (worktree) + spot-checks روی درختِ زندهٔ F:/backup"
verified_at: 2026-08-03
updated: 2026-08-03
---

# مگاپرامپتِ واحدِ اختاپوس — نسخهٔ راستی‌آزمایی‌شده

سیستم LIVE است: `organism.py` (port 8771). چیزی را نشکن.
این سند چهار مگاپرامپتِ قبلی را ادغام کرده **و ادعاهایشان را با کد سنجیده**. هشت ادعای غلط
اصلاح شده — فهرستشان در §10. اول §0 را اجرا کن.

---

## §0 · نخست: راستی‌آزمایی کن، نه باور

چند سشنِ موازی روی همین ریپو کار می‌کنند و درختِ زنده صدها فایلِ کامیت‌نشده دارد.

```bash
cd F:/backup
git log --oneline -3
git status --short | wc -l           # صدها — dirty عادی است
python -X utf8 _ops/flag_drift.py
type _ops\state\fugu-quota.json      # used / consecutive_failures / STOP-FUGU؟
```

اگر چیزی با این سند نمی‌خواند → **واقعیت برنده است**، سند را گزارشِ کهنه بخوان.

> ⚠️ **تلهٔ دو-درختی (مهم‌ترین نکتهٔ این سند).** بخشی از کارِ این سیستم **untracked** است:
> در `F:/backup` هست ولی در هیچ کامیتی نیست. اگر داخلِ یک worktree کار کنی، آن فایل‌ها
> **غایب‌اند و تو به‌غلط نتیجه می‌گیری «ساخته نشده»**. تأییدشده untrackedاند (۰۸-۰۳):
> `docs/FULL-OCTOPUS-DEEP-SCAN-REPORT.md` · `docs/MEGAPROMPT-REPAIR-V2.md` · `_ops/legs/lead_card.py`
> قاعده: هر حکمِ «X وجود ندارد» را **حتماً روی `F:/backup` (نه worktree)** دوباره بسنج.

---

## §1 · قوانین آهنین (نقض = توقف)

1. هر تغییر **backward-compatible** و — هرجا ممکن است — **flag-gated**. سیستم زنده است.
2. engine دوم نساز · `_ops/octopus/` نساز · provider سوم نساز.
3. هیچ **fake green**. تستِ بدون assertionِ معنادار = بی‌ارزش.
4. **test اول، patch بعد.** هیچ blind edit — قبل از patch فایل را کامل بخوان.
5. تستِ سبز که چیزی را تست نمی‌کرد → قرمزش کن.
6. هر mutation: **idempotency key + run_id + trace_id**.
7. long-running flow: `pending/running/blocked/failed/done`.
8. معلوم نیست → `UNKNOWN` و بپرس (به `00 - Inbox/AGENT_QUESTIONS.md`).
9. **نبودِ خطا ≠ سبز.** شمارِ صریحِ pass/fail یا exit code بده.
10. «انجام‌شد» فلگ نیست، **اثر** است — با ورودیِ ساختگی یا mtime بسنج.
11. **قبل از «بساز»، «هست؟» را بپرس.** بیش از نیمِ کارِ فهرست‌شده در نسخه‌های قبلیِ این
    سند **از قبل ساخته شده بود**. اول grep، بعد کد.

### مرزهای سخت (غیرقابل مذاکره)
- **D-10:** هر buy/sell/withdraw/swap = HARD_STOP، فقط انسان.
- **D-11:** ایجنت صفر دسترسیِ کیف‌پول. فقط «تأیید ثبت شد، اجرا با خودت».
- **D-20:** ایجنت حقِ SSH به نودها ندارد. توقف از مسیرِ ثبتِ نیت.
- هیچ **send/publish/pay/delete واقعی** — transport مسلح است (`OUTBOUND=1`).
- هیچ کلید/توکن/حساب چاپ نشود. نامِ متغیر مجاز، **مقدار نه** → `[REDACTED: <type>]`.
  (این شاملِ `OCTOPUS_CB_SECRET` هم می‌شود — §5 فاز ۱.)
- **هرگز عددِ زنده جعل نکن** → «اندازه‌گیری‌نشده»، نه `۰`، نه حذفِ خط.
- **هرگز حذف نکن، فقط منتقل کن** (`_Duplicates` / `_Archive`).
- حریمِ خصوصی: `08 - Partner (PII)` · `Identity/*` · `OWNER-PROFILE*` را باز نکن.

### دروازه‌های OWNER_AUTH
- تغییر فلگ فقط با `OWNER_AUTH: ARM FLAG <name>`.
- هیچ `git add/stage/commit` بدون `OWNER_AUTH: COMMIT <paths>`. **هرگز `git add -A`.**
- هیچ ری‌استارتِ پروسه (کارِ مالک؛ ری‌استارتِ ناقص = ارگانیسمِ مرده).
- provisioningِ هر secret کارِ مالک است، نه تو.

---

## §2 · قواعدِ ماشین (آنتی‌ویروسِ لحظه‌ای فعال است)

1. هرگز `find/du/ls -R/rglob/os.walk` از ریشهٔ `F:\backup`. از `_ops/` شروع کن.
2. هرگز `.claude/` · `.git/` · `_Archive/` · `_Duplicates/` · `04 - Architect System` را نپیما.
3. **grep را همیشه به یک مسیر مقید کن** (`_ops/`, `_ops/legs/`, …). گرپِ بی‌مسیر از ریشهٔ
   vault در همین جلسه **منفیِ کاذب** داد: `OCTOPUS_WIRE_CB_TOKEN` را «فقط در ۳ فایل markdown»
   گزارش کرد، در حالی که در `callback_token.py` و `center.py` هست. سقفِ زمانی/نتیجه ساکت
   می‌خورد و شبیهِ «پیدا نشد» به نظر می‌رسد. **صفرِ بی‌مسیر را هرگز حکم نگیر.**
4. هر فرمانِ شل < ۶۰ ثانیه. حداکثر **۴ ایجنتِ همزمان**.
5. **CRLF:** `_ops/*.py` معمولاً CRLF · `.cmd` همیشه CRLF. تست: `data.count(b'\r\n')` vs
   `data.count(b'\n')`. مراقبِ `newline=''` باش.
6. **جهش‌آزماییِ اجباری:** هر سبزی که با یک جهش قرمز نشد را باور نکن. لنگرِ جهش باید
   **یکتا** باشد (`replace(...,1)` به تابعِ خواهر می‌خورد). بین جهش‌ها `__pycache__` پاک کن.
7. **هرگز `run_all.py` کامل اجرا نکن** — روی ارگانیسمِ زنده می‌نویسد. تک‌فایل اجرا کن.
8. مسیرهای فارسی: با `-X utf8` / `--encoding utf-8`.

---

## §3 · معماریِ تأییدشده (ارجاع به **نماد**، نه شماره‌خط)

```
TELEGRAM (long-poll) → tg_api → center.py :: handle_update()
  ├─ is_owner gate                          [WORKING, fail-closed]
  ├─ _handle_message (30+ commands)         [WORKING]
  ├─ _handle_callback (hm tk ap mn lg pw ms map …)
  │    └─ callback_token.py  FLAG="OCTOPUS_WIRE_CB_TOKEN"  + secret OCTOPUS_CB_SECRET
  │       center.py: import cbtok · mint per-job · کیبوردِ توکن‌دار   [BUILT, flag OFF]
  └─ bridge_to_organism                     [WORKING]

ORGANISM (organism.py, port 8771, tick 300s)  [WORKING]
  ├─ wiring.py (~245KB، 35+ flag) · هر beat در try/except · 5-level halt · _write_state atomic
  └─ business_legs_beat()  ←  _BUSINESS_LEGS_SPEC = ((name, mod_name, fn_name), …)
        قرارداد: <name>_leg.<name>_status() -> {"leg","live","signal","note"}
        اکنون ۵ پا: lead · mining · crypto · accounting · knowledge
        سایدکارِ خروجی: _ops/state/ORGANISM-STATE.business_legs
        ⚠️ این beat **فلگ ندارد** — فقط kill-switch. هر پایی که به SPEC اضافه کنی
           در تیکِ بعدی زنده است. (امن است چون status فقط‌خواندنی است — ولی بدان.)
        fail-soft: ماژول/تابعِ غایب → {"live": false, "signal": "unknown"} و beat نمی‌میرد.

LEGS: Lead/Painter [WORKING — 5-layer EffectorGate] · Ziman/Cartographer/Doctor [WORKING]
      Mining/Crypto/Accounting/Knowledge [SKELETON/STALE — G-012]
MINIAPP: telegram_center/miniapp_gateway.py (bind 127.0.0.1:8774، initData-gated، دو-لایه redact)
      → miniapp_state.py :: dispatch_api()  برای /api/{state,outbound,approvals,legs,
        value,ui-registry,current-truth,ops}                          [BUILT 2026-08-02]
MODEL PLANE: cortex/model_router.py (fail-closed) · cortex/fugu_quota.py (STOP-FUGU)
      · debate/client.py (Fugu = Sakana؛ host allowlist = api.sakana.ai؛ فقط مدلِ "fugu")
PROJECT-F: pf_os/ (compose-only by design، GATE 0 = مسدود، bridge_beat unwired — G-007)
```

---

## §4 · سه حالتِ کار — به ترتیب (قاطی نکن)

- **حالتِ A — DEEP SCAN (read-only):** فقط اگر واقعیتِ runtime نامطمئن است. هیچ patch.
- **حالتِ B — REPAIR (پیش‌فرض):** مستقیم برو §5.
- **حالتِ C — SYNC:** بعد از بستهشدنِ امنیتِ پایه.

⚠️ حالتِ A و B/C را **هم‌زمان به یک ایجنت نده** — «چیزی را عوض نکن» با «این را بساز» تناقض دارد.

---

## §5 · گرافِ کارِ واحد

> اصل: **امنیت → مشاهده‌پذیری → adapterهای امنِ read/propose → بهداشت → کارِ خطرناکِ owner-gated.**
> **پاهای skeleton:** ساختِ `status()`ِ صادق (که `signal="skeleton"` برمی‌گرداند) **مجاز** است؛
> **فعال‌سازیِ رفتارِ درآمدزا** owner-gated است (G-012). این دو یکی نیستند.

### فاز ۱ — امنیت [HIGH]

**G-001 · HMAC callback token — ⚠️ این «بساز» نیست، «بسنج و مسلح کن» است.**
از قبل موجود (تأیید ۰۸-۰۳): `_ops/telegram_center/callback_token.py` (`FLAG`, `verify`, `mint`) ·
سیم‌کشی در `center.py` (import `cbtok`، mintِ per-job، کیبوردِ توکن‌دار) ·
**تستِ قراردادِ کامل** `_ops/tests/S1-05_test_ap_binding.py` (ثبت‌شده در `run_all.py`) که
پوشش می‌دهد: flag-off = parityِ بایت‌به‌بایت · روشن + secretِ غایب = fail-closed/inert ·
bind به (jid|action|owner_id|action_hash|expires) · دستکاریِ هر جزء → reject · منقضی → reject ·
مقصدِ نامعتبر → reject · single-use/replay → reject · `callback_data ≤ 64B`.
همچنین `_ops/deploy/ACTIVATION-RUNBOOK-2026-07-21.ps1` مراحلِ مسلح‌سازی را دارد.

کارِ باقی‌مانده — فقط این چهار:
1. `S1-05_test_ap_binding.py` را **تک‌فایل** اجرا کن؛ pass/failِ صریح گزارش بده.
2. **جهش‌آزمایی:** حداقل ۳ جهشِ لنگر-یکتا در `callback_token.py` (مثلاً معکوس‌کردنِ چکِ
   `expires`) → S1-05 باید قرمز شود. اگر سبز ماند، آن مسیر **نگهبان ندارد** و باید تست بگیرد.
3. **`OCTOPUS_CB_SECRET`** پیش‌نیازِ فلگ است: `OCTOPUS_WIRE_CB_TOKEN=1` بدونِ secret =
   fail-CLOSED = **همهٔ دکمه‌ها inert**. مقدارش را نه بخوان، نه بنویس، نه چاپ کن —
   فقط گزارش بده «ست هست / ست نیست».
4. سپس **پیشنهاد** بده: `ARM FLAG OCTOPUS_WIRE_CB_TOKEN` (پس از تأییدِ حضورِ secret).
   اعمال فقط با `OWNER_AUTH`. مسیرِ tokenless را **deprecate** کن، حذف نه.

**G-002 · mutation/fault-injection framework — ✅ گپِ واقعی (در هیچ‌کدام از دو درخت نیست).**
`_ops/tests/mutation/` بساز. هر کیس باید با خراب‌کردنِ شرط واقعاً **قرمز** شود:
`missing run_id · ok:true+error · success بدون artifact · duplicate callback · replay approval ·
actor spoof · timeout · partial failure · flag-off parity · halt active · restart mid-run ·
corrupted state`. اگر کیسی SURVIVED شد، تفکیک کن: گاردِ کور، یا جهشی که به هدف نخورد.

### فاز ۲ — مشاهده‌پذیری
**G-003 · trace_id/run_id:** در `handle_update` مقدار `run_id=uuid4().hex[:12]`؛ propagate به
handlers/legs؛ در `_emit_event` به‌عنوان `trace_id`؛ در receipt `[#abc123]`.
edge: پیامِ معمولی/callback/commandِ ناشناخته/owner-denied/error-path همه trace بگیرند ·
trace در receipt و log یکی بماند · در exception حفظ شود · به secret/PII وصل نشود.

**G-006 · capability_registry:** `_ops/telegram_center/actions.py` موجود ولی مصرف‌نشده.
adapter در `_handle_callback`: اول `ACTIONS` lookup، fallback به dictِ hardcoded.
edge: actionِ جدید بدونِ تغییرِ dispatch کار کند · unknown = **fail-closed** · fallback سالم ·
**owner gate همچنان قبل از action** · قیدِ group-only/DM-only حفظ شود.

### فاز ۳ — پاها (status صادق) + adapterهای امنِ lead
پیش از هر سه: قراردادِ `_BUSINESS_LEGS_SPEC` در §3 را بخوان. الگوی مرجع: `lead_leg.lead_status()`.

**۳-الف · studio_pf** *(تأیید: در هیچ‌کدام از دو درخت نیست — گپِ واقعی)*
`03 - Projects/اونلی فنز/PROJECT.md` را بخوان → `_ops/legs/studio_pf_leg.py` با
`studio_pf_status() -> {"leg","live","signal","note"}` که **صادقانه** `live=False,
signal="skeleton"` برگرداند → به `_BUSINESS_LEGS_SPEC` اضافه کن.
اثباتِ observable: `studio_pf` در `_ops/state/ORGANISM-STATE.business_legs` ظاهر شود.

**۳-ب · cartographer** *(تأیید: `cartographer_leg.py` فقط متدِ کلاسیِ `status_snapshot()` دارد)*
تابعِ **ماژول‌سطحِ** `cartographer_status()` بساز که `status_snapshot` را wrap کند و قرارداد را
برگرداند → به SPEC اضافه کن. تست + جهش.

**۳-ج · ziman** *(همان وضعیت: `ziman_leg.py` فقط `status_snapshot()` دارد و در SPEC نیست)*
بررسی کن حذفش از SPEC عمدی بوده یا نه. اگر یکپارچه می‌شود `ziman_status()` بساز؛
اگر عمدی است **مستندش کن** و دست نزن.

**G-008 · `/lead` command:** `LeadIntakeAdapter.submit_manual(text, source) -> {ok, lead_id, status}`؛
در `_handle_message` → `/lead <text>`. همهٔ leadها از consent firewall.
edge: `/lead` بی‌متن → help · خالی/خیلی‌بلند → reject/trimِ مشخص · duplicate idempotent ·
**هیچ outbound send** · source/run_id ثبت شود.

**G-009 · first-reply owner card (read-only):** بلاکِ first-reply در `wiring.py`
(جست‌وجو: `lead-first-reply` / `LEAD_FIRST_REPLY`). adapterِ read-only، کارتِ advisory.
edge: نبودِ draft · draftِ malformed · چند draft برای یک lead · **نمایش هرگز به ارسال نرسد**.

### فاز ۴ — بهداشت
**G-005 · JSONL rotation:** `action-audit.jsonl`, `approval-log.jsonl`, `neural/effect-shadow.jsonl`.
یک `rotation.py` (آستانهٔ قابل‌تنظیم ~10MB، N backup، **archive نه delete**)، وصل به housekeeping.
edge: rotation اتمیک · خطِ نیمه‌نوشته corrupt نشود · چند writer → data loss نه · سقفِ backup تست‌شده.

**G-007 · Project-F bridge:** `03 - Projects/اونلی فنز/pf_os/bridge_beat.py` (موجود، همراهِ
`test_bridge_beat.py`). در `wiring.py` یک beat پشتِ `OCTOPUS_WIRE_SABA_BRIDGE`.
**GATE 0 را هرگز touch نکن.**
edge: flag off → صفر اثر · live mode همچنان compose-only/block · مسیرِ فارسی/فاصله‌دار درست ·
خروجی فقط status/report، نه publish/send.

### فاز ۵ — سیمِ ✅ به `authorize()` [خطرناک — OWNER_GATED]
> ⚠️ **تصحیحِ مهم:** ادعای «`authorize()` صفر صداکننده» **غلط** بود. در `lead_effect_gate.py`
> تابعِ `on_lead_verdict` مسیرِ `gate.request(...) → authorize(...)` را دارد، و
> `bridge_from_inbox` همان را برای `live_loop` wrap می‌کند. **idempotency هم از قبل هست**
> و روی **lead_id** کلید خورده (`_authorized_effect_for_lead`؛ کامنتِ F1: «یک لید فقط یک
> effectِ outbound»). پس idempotency را دوباره **نساز**.

کارِ واقعی: **آیا دکمهٔ ✅ کارتِ lead در `center.py` به `on_lead_verdict` می‌رسد؟**
۱. مسیرِ callback → verdict را دنبال کن و شکافِ دقیق را گزارش بده (نه فرض).
۲. اگر شکاف هست، وصلش کن **بدونِ** بازنویسیِ idempotencyِ موجود.
۳. همهٔ تست/patch با mock/dry-run. مسلح‌سازیِ transport = تأییدِ صریحِ owner.
۴. دکمهٔ 📤 draft در `_ops/legs/lead_card.py` **(untracked — فقط در `F:/backup`)** handler ندارد →
   handler بده یا دکمه را بردار. دکمهٔ مرده = بی‌اعتمادیِ مالک.

### فاز ۶ — صداقتِ دادهٔ MiniApp
> ⚠️ **تصحیحِ مهم:** «`/api/state` وجود ندارد، بسازش» **غلط** بود. `miniapp_gateway.py`
> هشت مسیرِ read-only را به `miniapp_state.dispatch_api()` می‌سپارد، پشتِ `validate_init_data`
> (هر شکست = **403 با بدنهٔ خالی**)، با دو لایه redact. auth و مسیر **ساخته شده‌اند.**

کارِ واقعی — فقط **صداقتِ محتوا**:
۱. `miniapp_state.dispatch_api("/api/state")` را بخوان: دادهٔ واقعی برمی‌گرداند یا placeholder؟
۲. هر عددِ نسنجیده باید **«اندازه‌گیری‌نشده»** باشد، نه `۰`، نه حذف‌شده. **هرگز عدد جعل نکن.**
۳. پوشش: همهٔ پاها (از `business_legs_beat`: live/signal/note) · mining (نودها) · lead pipeline ·
   نبض (beat/halted/protective_skip).
۴. frontend (`app.js`) واقعاً به `/api/state` وصل است؟ اعدادِ فارسی؟ آیکون از `render.py::LEG_ICONS`؟
۵. تست (الگوی `test_miniapp_gateway.py`): با initDataِ مالک داده؛ **بدونِ initData = 403**.

### فاز ۷ — یکپارچه‌سازیِ Telegram + MiniApp
- اعلانِ فوری (منشور: حداکثر ۵/روز): فقط leadِ تازه، پرداختِ گیرکرده، نودِ بی‌جواب،
  تصمیمِ منتظر، هشدارِ بحرانی. بقیه فقط در miniapp/گروه.
- `OCTOPUS_TG_MERGED_DIGEST` را بررسی کن (یک پیام به‌جای ۹).
- `guide.py`: «داشبورد در مینی‌اپ، اینجا فقط اعلان و رأی.»
- **`_ops/tg_send_log.py` (نه در `telegram_center/`) :: `record()`** — امضایش اکنون
  `chat_id/topic_id/text/stream` است و `message_id` **ندارد** (گپِ واقعی، تأییدشده).
  پارامترِ اختیاریِ backward-compatible اضافه کن؛ سپس cleanup-script برای پیام‌های +۷ روز
  (`tg_api.delete_message`).

### فقط گزارش — patch نکن (OWNER_DECISION)
**G-004** state sprawl (~۳۲۰ store) → `docs/state-inventory.md` · **G-010** watchdog split-brain ·
**G-011** money state fragmentation → inventory · **G-012** فعال‌سازیِ پاهای skeleton.
برای هرکدام فقط: inventory · report · open questions · migration/activation plan.

---

## §6 · متدِ هر patch
1. **grep بزن: از قبل هست؟** (قاعدهٔ ۱۱ · نیمِ کارِ این سند قبلاً ساخته شده بود.)
2. فایلِ هدف را کامل بخوان.
3. تستی بنویس که رفتارِ مطلوب را assert کند → اجرا: باید **FAIL**.
4. patchِ کوچکِ scoped (flag-gated هرجا ممکن است — دقت کن `business_legs_beat` فلگ ندارد).
5. تست → باید **PASS**؛ جهش‌آزمایی با لنگرِ یکتا → باید **FAIL-correct**.
6. `git status --short` (stage فقط با `OWNER_AUTH: COMMIT <paths>`).
7. گزارش: چه تغییری، کجا، چرا، rollback.

## §7 · معیارِ «تحویل‌شده» (سه شاهد)
1. اثرِ observable (`ORGANISM-STATE.business_legs` · کارتِ تلگرام · خروجیِ CLI) — نه صرفاً سبزیِ تست.
2. جهش‌آزمایی: فیکس را برگردان → تستِ مربوطه قرمز.
3. صداقت: اگر end-to-end اثبات‌نشده (مثلاً نودِ زنده لازم دارد) → **«اثبات‌نشده»** بنویس.

## §8 · معیارِ موفقیتِ جلسه
G-001 سنجیده‌شده و پیشنهادِ armش با وضعیتِ secret ثبت · G-002 کامل · هر patch تستِ سبز دارد ·
≥۳ جهشِ FAIL-correct · هیچ fake green · هیچ backward-compat نشکنده · owner decisions ثبت‌شده ·
`HANDOFF.md` (فقط wikilink، <۲۰۰ خط) و DecisionLog به‌روز.

## §9 · اسنادِ مرجع
- `F:/backup/docs/FULL-OCTOPUS-DEEP-SCAN-REPORT.md` — ⚠️ **untracked**
- `F:/backup/docs/MEGAPROMPT-REPAIR-V2.md` — ⚠️ **untracked**
- `docs/fugu_usage_policy.md` · `docs/WAVE1_VERIFIED.md` — کامیت‌شده
- `_ops/MEGAPROMPT-ULTRATHINK-FULL-2026-08-02.md` · `_ops/MEGAPROMPT-LEG-SYNC-2026-08-02.md`
- `_ops/deploy/ACTIVATION-RUNBOOK-2026-07-21.ps1` — مسلح‌سازیِ CB_TOKEN
- `_ops/implementation_reports/UI-INVENTORY-2026-08-02.md`
- `03 - Projects/Lead-نقاشی/WHY-NO-REAL-LEADS-2026-08-01.md`

---

## §10 · تصحیح‌های این نسخه (هرکدام با شاهدِ کد، ۲۰۲۶-۰۸-۰۳)

| # | ادعای نسخه‌های قبلی | واقعیت | اثر بر کار |
|---|---|---|---|
| ۱ | «برای G-001 تستِ parity و mutation بساز» | `S1-05_test_ap_binding.py` قراردادِ کامل را دارد و در `run_all.py` ثبت است | فاز ۱ از «بساز» به «بسنج + مسلح کن» تغییر کرد |
| ۲ | فلگ را روشن کن | `OCTOPUS_CB_SECRET` پیش‌نیاز است؛ بدونش fail-CLOSED = دکمه‌ها inert | پیش‌نیازِ صریح اضافه شد |
| ۳ | «`/api/state` را بساز + initData auth» | هر دو موجود؛ ۸ مسیر → `miniapp_state.dispatch_api`، 403 بدونِ initData | فاز ۶ به «صداقتِ داده» محدود شد |
| ۴ | «`authorize()` صفر صداکننده؛ idempotency اضافه کن» | `on_lead_verdict` صدایش می‌زند؛ idempotency روی `lead_id` از قبل هست | فاز ۵ به «سیمِ ✅ → verdict» محدود شد |
| ۵ | سه سندِ مرجع را بخوان | دو تای‌شان **untracked**‌اند و در worktree غایب | تلهٔ دو-درختی در §0 |
| ۶ | `lead_card.py` (بی‌مسیر) | `_ops/legs/lead_card.py`، untracked | لنگرِ درست |
| ۷ | `tg_send_log.py` ذیلِ `telegram_center` | در `_ops/` است؛ `record()` واقعاً `message_id` ندارد | مسیر اصلاح، گپ تأیید |
| ۸ | «همه چیز flag-gated» | `business_legs_beat` فلگ ندارد — kill-switch only | هشدار در §3 و §6 |

**گپ‌های تأییدشدهٔ باقی‌مانده (در هیچ‌کدام از دو درخت نیستند):** `_ops/tests/mutation/` ·
`_ops/legs/studio_pf_leg.py` · `cartographer_status()`/`ziman_status()`ِ ماژول‌سطح ·
`message_id` در `tg_send_log.record()`.

**دامنهٔ این راستی‌آزمایی:** ادعاهای «X هست» روی `master 7ecb407` سنجیده شد؛ ادعاهای
«X نیست» علاوه بر آن روی درختِ زندهٔ `F:/backup` هم دوباره سنجیده شد. درختِ زنده صدها فایلِ
کامیت‌نشده دارد — اگر چیزی نخواند، **کد برنده است**.
