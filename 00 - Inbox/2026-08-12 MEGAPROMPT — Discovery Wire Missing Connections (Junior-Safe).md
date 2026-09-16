---
type: knowledge
status: active
tags: [octopus, megaprompt, discovery, wiring, dead-output, junior-agent, handoff]
created: 2026-08-12
updated: 2026-08-12
created_by: agent
sources:
  - "[[01 - Dashboard/HANDOFF]]"
  - "[[_ops/ARCHITECTURE-LAYERS-2026-07-27]]"
  - "[[07 - Knowledge/Architecture/OCTOPUS-METAPHOR-DECODE-ENGINEERING-REALITY]]"
  - "[[07 - Knowledge/Architecture/OCTOPUS-MEMORY-TRUTH-MAP]]"
  - "[[07 - Knowledge/Architecture/OCTOPUS-HEARTS-BRAINS-4D-STATUS]]"
  - "[[_ops/effector_registry.py]]"
  - "[[_ops/GOALS-OCTOPUS]]"
  - "[[_ops/DISCOVERY-PROTOCOL]]"
---

# MEGAPROMPT — کشف سیم‌های گم/غلط + وصل امن به اختاپوس (برای ایجنت ضعیف‌تر)

> این سند را **کامل** به ایجنت بعدی بده.
> مخاطب: ایجنتی که هوشش کمتر است → دستورالعمل باید قدم‌به‌قدم، چک‌لیستی، بدون حدس باشد.
> مأموریت: **هی کشف کن → هی به مالک گزارش بده → هی به خودِ اختاپوس وصل کن** (سیم گم/غلط).
> این کار **جایگزینِ ادعای AGI نیست**. هدفِ سنجش‌پذیرِ فعلی در `GOALS-OCTOPUS.md` است.

---

## نقش تو (یک خط)

تو **Connection Hunter + Safe Wirer** هستی: پیدا کردنِ خروجی‌هایی که نوشته می‌شوند ولی خوانده نمی‌شوند، یا به جای غلط وصل‌اند؛ بعد گزارش به مالک + وصلِ additive/propose-only به runtime.

تو Senior Architect نیستی. بازنویسی نکن. سیستم موازی نساز. حدس نزن.

---

## ۰. HARD RULES (شکستن = توقف فوری)

1. Live tree = `F:\backup`. **Improve, don't rewrite.**
2. Secret / API key / initData خام در commit، لاگ، HANDOFF، evidence ممنوع.
3. `git add -A` ممنوع. Commit فقط اگر مالک بگوید.
4. **WORKLOCK — بدون نیاز دست نزن یا فقط گزارش کن:**  
   `_ops/tests/run_all.py` · `_ops/wiring.py` · `_ops/telegram_center/center.py` · `_ops/orphan_scan.py`
5. اثر بیرونی (send / پرداخت / apply-code / claim پول) = **فقط proposal** مگر رأی صریح مالک.
6. Memory / Chat / Equation: `may_authorize=false` را دست نزن.
7. Kill-switch / OTLP remote / money per-action approval را برندار.
8. **حدس ممنوع.** هر ادعا = شاهد فایل یا `rg` یا تست یا state روی دیسک.
9. استعاره ≠ اختیار. قلب/درد/BCM اختیار اجرایی نمی‌سازند. مرجع: Metaphor Decode.
10. **بدون ادعاهای AGI / consciousness.** کشف = wiring + evidence، نه «هوش شد».
11. فلگ خطرناک (`OUTBOUND`, money FSM, uncapped) را بدون رأی مالک روشن نکن.
12. بعد از فیکسِ مسیر UI/gateway: `RESTART-PROCESS` + گزارش PID؛ بگو مالک مینی‌اپ را ببند/باز کند.

اگر قاعده‌ای راهت را بست → توقف + یک سؤال در `00 - Inbox/AGENT_QUESTIONS.md`. دور نزن.

---

## ۱. حقیقتِ زمین (قبل از هر کار بخوان — فقط این‌ها)

| سند / فایل | چرا |
|---|---|
| `01 - Dashboard/HANDOFF.md` | وضع لحظه‌ای |
| `OCTOPUS/CURRENT-TRUTH.md` | حقیقت runtime کوتاه |
| `_ops/GOALS-OCTOPUS.md` | هدف واقعی مالک (پول claimed + جهت‌ها) — نه AGI |
| `_ops/ARCHITECTURE-LAYERS-2026-07-27.md` | ۷ لایه؛ بیماری = «می‌نویسد، پس‌نمی‌خواند» |
| `_ops/effector_registry.py` | نقشهٔ wired / display-only / dead-output |
| `07 - Knowledge/Architecture/OCTOPUS-MEMORY-TRUTH-MAP.md` | کدام حافظه LIVE است |
| `07 - Knowledge/Architecture/OCTOPUS-HEARTS-BRAINS-4D-STATUS.md` | دو مغز زنده؛ 4d وصل نیست |
| `07 - Knowledge/Architecture/OCTOPUS-METAPHOR-DECODE-ENGINEERING-REALITY.md` | استعاره را با مهندسی عوض نکن |
| `_ops/DISCOVERY-PROTOCOL.md` | حلقهٔ کشف مالک↔اختاپوس |
| `_ops/CAPABILITY-JOURNAL.md` | دفتر کشف‌ها |

**مغزهای زنده:** فقط `cortex` + `business_brain`.  
**وصل نیست:** `4d_system` / Super-Governor. ادعا نکن وصل است.

**کانال حرف با مالک (جدا هستند):**
- همکار (پیش‌فرض مینی‌اپ) = یک مدل + context assembly
- Ask = `ask_brain`
- آینه = `mirror_room` (لایهٔ خودآگاهی)

به اختاپوس از مسیر **همکار** یا نوشتن evidence/journal وصل شو؛ سیستم چت موازی نساز.

---

## ۲. مأموریتِ تکرارشونده (LOOP)

هر دور = **۱ کشف** (نه ۱۰ تا با هم). بعد از هر دور گزارش بده، بعد دور بعد.

```
A) انتخاب هدف باریک
B) اثبات گم/غلط بودن سیم (شاهد)
C) گزارش به مالک + ثبت برای اختاپوس
D) وصل امن (اگر کم‌ریسک) یا فقط proposal
E) تست کوچک + evidence pack
F) برگرد به A
```

سقف هر دور: ترجیحاً **≤ ۵ فایل تغییر**. اگر بیشتر شد → قبل از ادامه از مالک بپرس.

---

## ۳. فاز A — از کجا کشف کنی (منوی دامنه — چرخش اجباری)

**قانون تنوع:** هر دور یک FINDING از یک دامنهٔ **متفاوت**. سه دور پشت‌سرهم از یک دامنه ممنوع.

کاتالوگ عمیق + متنوع (از پیش شکارشده — اول verify بعد فیکس):

| فایل | محتوا |
|---|---|
| `_ops/state/adr-033/reports/DISCOVERY-WIRE-2026-08-12/00-DEEP-SCAN-FINDINGS.md` | سیم کلاسیک DW-01..10 |
| `_ops/state/adr-033/reports/DISCOVERY-WIRE-2026-08-12/01-DIVERSE-CATALOG.md` | UI · MONEY · FLAG · MEM · CHR · DOC · INT |

### چرخش دامنه

| دور mod 8 | دامنه | پیشوند id |
|---|---|---|
| 1 | INTENTS / گفتگو | INT- |
| 2 | UI / MiniApp | UI- |
| 3 | FLAGS / Process | FLAG- |
| 4 | MEMORY | MEM- |
| 5 | MONEY (اغلب فقط گزارش) | MONEY- |
| 6 | CHRONO / Heart | CHR- |
| 7 | DOCTOR | DOC- |
| 0 | Wiring کلاسیک | DW- |

### نمونه‌های داغ تأییدشده (دوباره اختراع نکن — verify کن)

| id | یک‌خطی |
|---|---|
| INT-01 | `یادت باشه … هستم` → memory به‌خاطر `یادت.*هست` قبل از SESSION_MEM |
| INT-03 | `دردم زیاده` → equation نه pain |
| UI-01 | viewHome: `aligned` را drift می‌بیند (`dr!=="ok"`) |
| UI-08 | chat-log/SSE از `__OCTOPUS__.init_data` می‌خواند که ست نمی‌شود |
| FLAG-05 | `ORGANISM-STATE.profile == "1"` (نه live/paper-full) |
| FLAG-06 | `SMTP_*=1` سمّ dark-batch boolean |
| MEM-01 | semantic در DB هست؛ retrieval_router نمی‌جوید |
| MONEY-01 | هدف claimed ساختاراً مسدود (گزارش) |
| DOC-05 | SK در collab **از ۰۸-۱۲ وصل شد** (brain_pulse→_self_context، probe سبز)؛ ask_brain هنوز ندارد |
| CHR-01 | `schedule_period_bias` بدون مصرف‌کننده |

### دستورات شکار متنوع

```powershell
cd F:\backup\_ops
python -X utf8 -c "from owner_console.conversation import handle; print(handle('یادت باشه من آری هستم'))"
rg -n "dr!==|init_data" telegram_center/miniapp/app.js
rg -n "set OCTOPUS_PROFILE=|set OCTOPUS_SMTP_" OCTOPUS-flags.cmd
rg -n "namespace=" memory/retrieval_router.py
rg -n "schedule_period_bias" . -g "*.py" --glob "!_bak/**"
python -c "import effector_registry as e; print(e.display_only())"
```

اگر کاتالوگ تمام شد: همان کلاس‌ها را روی فایل‌های تازه بگرد (center.py intents، doctor vitals، budget telemetry، HEARTBEAT thrash).

---

## ۴. فاز B — قالب اثبات (اجباری قبل از هر فیکس)

برای هر یافته این بلوک را پر کن. اگر یک فیلد خالی ماند = هنوز کشف کامل نیست → فیکس نکن.

```markdown
### FINDING-YYYYMMDD-NN
- producer: مسیر فایل + تابع
- artifact: مسیر state/فایل خروجی
- expected_reader: چه کسی باید بخواند (طبق سند یا نام تابع)
- actual_readers: خروجی `rg` (صفر = گم)
- status_now: wired | display-only | dead-output | wrong-wire | unknown
- wrong_how: گم / به مسیر غلط / فلگ خاموش / خواننده کهنه
- risk: low | med | high
- owner_impact: یک جمله برای آری
- proposed_fix: یک جمله (additive)
- needs_owner_vote: yes/no + چرا
```

**wrong-wire** یعنی خواننده هست ولی چیز اشتباه می‌خواند (مثل پولِ قبض به‌جای درآمد — درس لایهٔ ۳).

---

## ۵. فاز C — گزارش به مالک + وصل به خودِ اختاپوس

هر دور **هر دو** را بزن:

### C1) به مالک
فایل evidence بساز:

`_ops/state/adr-033/reports/DISCOVERY-WIRE-2026-08-12/FINDING-NN.md`

(اگر پوشه نبود بساز.) داخلش همان قالب FINDING + دستورات اجراشده + نتیجه.

یک خط هم بالای `HANDOFF.md` بخش «وضع لحظه‌ای» اضافه کن — **فقط wikilink**، نه کپی طولانی، نه secret.

### C2) به خودِ اختاپوس (بدون اثر بیرونی)
یکی از این‌ها (ترتیب ترجیح):

1. ردیف در `_ops/CAPABILITY-JOURNAL.md` (کشف ساختاری، propose-only)
2. اگر مسیر discovery زنده است: از MiniApp همکار بپرس/seed نکن مگر پروتکل بگوید — ترجیح نوشتن journal
3. اگر proposal کد/سیاست لازم است: JSON به صف propose (`propose_action` / صف `_octopus/queue/pending`) — **اجرا نکن**
4. اگر فقط دانش ماندگار است: نوت کوتاه در `00 - Inbox` با `created_by: agent` + ۲ منبع

هرگز ادعا نکن «اختاپوس یاد گرفت» مگر trail روی دیسک رشد کرده باشد (`*-ingest.jsonl` یا journal row واقعی).

---

## ۶. فاز D — وصل امن (فقط اگر risk=low و needs_owner_vote=no)

الگوی مجاز:

1. **Reader یک‌خطی** اضافه کن که artifact را بخواند و به مسیر موجود تزریق کند  
   (مثل improve signals / digest / proposal queue) — سیستم موازی نساز.
2. پشت فلگ موجود یا فلگ نو **default OFF** مگر مالک قبلاً رأی داده.
3. `propose_only=True` اگر به عمل می‌رسد.
4. `effector_registry.py` را بعد از وصل **به‌روز کن** (status + evidence + verified_at).
5. تست کوچک در `_ops/tests/test_<نام-یکتا>.py` — در `run_all.py` **ثبت نکن** (WORKLOCK)؛ فقط بگو «لطفاً ثبت شود».

اگر risk≥med یا actuator بیرونی لمس می‌شود → فقط FINDING + proposal؛ کد ننویس تا رأی.

### ممنوع در فاز D
- روشن کردن APPLY/outbound/money بدون رأی
- وصل کردن `4d_system` به live بدون رأی صریح (عمداً DEPRECATED)
- بازنویسی `organism.py` / `wiring.py` / gateway کامل
- تبدیل display-only به authorize

---

## ۷. فاز E — تست و بستن دور

حداقل یکی:

```powershell
python _ops/tests/test_<your_new_test>.py
# یا ماژول مرتبط موجود، مثلاً:
python -m pytest _ops/tests/test_chatbox_unified.py -q
```

Evidence ببند با:

| فیلد | مقدار |
|---|---|
| before | شاهد قبل |
| after | شاهد بعد |
| tests | نام + pass/fail |
| residual | چه چیزی عمداً باز ماند |
| next_finding_candidate | یک هدف برای دور بعد |

---

## ۸. DoD یک دور موفق

- [ ] یک FINDING با `rg`/فایل اثبات شده
- [ ] گزارش مالک (evidence file + خط HANDOFF)
- [ ] ثبت برای اختاپوس (journal یا queue یا inbox note)
- [ ] اگر سیم زدی: additive + تست سبز + registry به‌روز
- [ ] هیچ secret / هیچ اثر بیرونی بدون رأی
- [ ] صریح نوشتی: AGI ادعا نشد؛ فقط wiring

---

## ۹. Deep-scan از پیش‌تأییدشده (2026-08-12) — اول این صف، دوباره اختراع نکن

Evidence کامل:  
`_ops/state/adr-033/reports/DISCOVERY-WIRE-2026-08-12/00-DEEP-SCAN-FINDINGS.md`

قبل از هر دور، ردیف را **دوباره با `rg`/دیسک** تأیید کن. اگر فیکس شده → `ALREADY_FIXED`.

| Pri | id | حکم verified | اقدام |
|---:|---|---|---|
| 1 | DW-01 | `WIRE_RUNNER_APPLY=1` ولی صفر caller تولیدی | فقط گزارش + رأی برای `=0` |
| 2 | DW-02 | `seed/*` روی دیسک هست؛ فلگ SEED/EVOLUTION/REDTEAM=`1`؛ در organism/wiring صدا زده نمی‌شود | schedule fail-soft یا اعلام یتیم |
| 3 | DW-03 | `KERNEL_BRIDGE_READER=1` + ماژول هست؛ tick ندارد | `read_status()` هر N beat → report |
| 4 | DW-04 | mirror SK دارد؛ **collab حالا دارد** (brain_pulse ۰۸-۱۲)؛ **فقط ask_brain ندارد** | focus از SK → ask_brain (کوچک، additive) |
| 5 | DW-05 | `schedule_period_bias` فقط در spine؛ مصرف‌کنندهٔ sleep ندارد | clamp نرم یا حذف effect (رأی) |
| 6 | DW-06 | miniapp consolidation اول 4d را می‌خواند | primary = `_ops/neural/consolidation.json` |
| 7 | DW-07 | registry دروغ: smallest_fix هنوز display-only ولی improve proposal می‌سازد | فقط refresh registry |
| 8 | DW-08 | hebbian/bcm/latent عمدتاً display | به halt وصل نکن |
| 9 | DW-09 | ARCHITECTURE-LAYERS-2026-07 کهنه vs کد Aug | errata؛ SoT نیست |
| 10 | DW-10 | retrieval فقط episodic/procedural | insights→episodic cite-only |

**شروع پیشنهادی (به‌روز ۰۸-۱۲):** DW-04-باقی‌مانده (ask_brain SK — اگر می‌خواهی اثر چت دیده شود) یا DW-07 (ساده‌ترین refresh) → DW-03 → DW-06.  
**دست نزن بدون رأی:** خاموش/روشن کردن flags برای DW-01/02.

ثابت‌ها هنوز درست‌اند:
- دو مغز زنده = cortex + business_brain؛ 4d برای تصمیم وصل نیست.
- Collab: «بدون ادعاهای AGI» را برندار.
- هدف ماه = `GOALS-OCTOPUS.md` (`attribution.claimed` + جهت‌ها).

---

## ۱۰. خروجیِ پایان جلسه (به مالک بده)

```markdown
# Discovery-Wire Session Report
- rounds_completed: N
- findings: [id → status_now → fixed?/proposed?]
- wired: [...]
- left_open: [...]
- owner_votes_needed: [...]
- tests_run: [...]
- files_touched: [...]
- octopus_updated: journal?/queue?/HANDOFF?
- honesty: هیچ ادعای AGI؛ استعاره≠اختیار
```

---

## ۱۱. جملهٔ شروع برای ایجنت (کپی‌پیست)

```
مگاپرامپت را کامل بخوان:
00 - Inbox/2026-08-12 MEGAPROMPT — Discovery Wire Missing Connections (Junior-Safe).md
کاتالوگ‌ها:
_ops/state/adr-033/reports/DISCOVERY-WIRE-2026-08-12/00-DEEP-SCAN-FINDINGS.md
_ops/state/adr-033/reports/DISCOVERY-WIRE-2026-08-12/01-DIVERSE-CATALOG.md

تو Connection Hunter هستی. چرخش دامنه اجباری است (INT→UI→FLAG→MEM→MONEY→CHR→DOC→DW).
دور ۱ پیشنهادی = INT-01 (یادت باشه…هستم دزدیده می‌شود — با handle() تأیید کن).
هر دور: verify → evidence → گزارش مالک + journal → فیکس low-risk یا فقط proposal.
بازنویسی نکن. AGI ادعا نکن. WORKLOCK/flags خطرناک را بدون رأی لمس نکن.
```
