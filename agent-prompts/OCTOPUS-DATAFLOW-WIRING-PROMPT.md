---
type: build-prompt
project: "پازل هشت‌پا / OCTOPUS visualization"
goal: connect the world-network on ONE data backbone; make dataflow input→output correct & healthy
author: grounded hand-off (session 2026-07-12)
status: ready-to-run
---

# 🐙 OCTOPUS — پرامپتِ سیم‌کشیِ جریانِ داده (Dataflow Wiring)

> **به ایجنت:** این یک منشورِ کاملِ خودبسنده است. کلِ شناختِ لازم از پروژه داخلش هست؛
> از حافظه چیزی فرض نکن، از همین سند + خواندنِ فایل‌ها کار کن.
> **قاعدهٔ کانونی:** IMPROVE, DON'T REWRITE — افزایشی کار کن، رابط/رندرِ موجود را نشکن،
> هر تغییرِ >۳۰٪ را اول بپرس. هر عدد یا برچسبِ epistemic (`[FACT]`/`[EST]`) باید منبع داشته باشد؛
> عددِ جعلی ممنوع.

---

## ۰. نقش و قواعدِ قفل‌شده (Hard Rules)
- تو یک **System Architect + Frontend Data-Engineer** هستی. خروجی: کدِ کارآمدِ production، نه توضیح.
- **read-only مطلق روی `F:\backup`** — هرگز چیزی در F: ننویس. فقط اکسترکتورهای موجود آن را می‌خوانند.
- **privacy:** پروژهٔ «اونلی فنز / Project-F» فقط به‌صورتِ status انتزاعی (🟢 money-locked + مهلت) مجاز است؛
  هیچ هویت/محتوا هرگز. پوشهٔ «اونلی فنز» و «۰۹ - People» از گراف prune می‌مانند.
- **صداقت:** اگر داده‌ای واقعی نیست، «نمادین/نیازمندِ منبع» علامت بزن؛ عدد نساز.
- **ADHD-aware UX:** هر دنیا به «یک کارِ روشنِ بعدی» می‌رسد؛ بصری برای حرکت است نه خیره‌شدن.

---

## ۱. نقشهٔ فعلیِ سیستم (Ground Truth — همین الان درست است)

**دو درخت:**
- **ورودی (منبعِ حقیقت، read-only):** `F:\backup` — دو زیرسیستم:
  - `F:\backup\4d_system\outputs\` → ارگانیسمِ SOG/Brain (events SQLite، sog math، strategy، frontier، budget، decision_packets، daemon).
  - `F:\backup\_ops\state\` → ارگانیسمِ حاکم (business-brain، fitness، cardiac-budget، ORGANISM-STATE با chrono، wiring).
- **خروجی (ورک‌اسپیسِ ویژوال، editable):** `C:\Users\Armin\Desktop\پازل هشت پا\OCTOPUS\worlds\` — هابِ `index.html` + ۱۰ دنیا.

**سه اکسترکتورِ read-only (Input → JS globals) — ساخته و زمان‌بندی‌شده‌اند:**
| اسکریپت | می‌خواند | می‌نویسد | Global |
|---|---|---|---|
| `extract_live_data.py` | `4d_system/outputs` | `nervous-system/live-data.js` | `window.LIVE_DATA` |
| `extract_ops_data.py` | `_ops/state` | `nervous-system/ops-data.js` | `window.OPS_DATA` |
| `extract_graph.py` | کلِ vault (md + wikilinks) | `OCTOPUS/worlds/graph-data.js` | `window.OCTOPUS_GRAPH` |

> هر سه در `refresh-live-data.bat` زنجیر شده‌اند و با Windows Scheduled Task
> `OctopusLiveDataRefresh` هر ۳۰ دقیقه اجرا می‌شوند (با `PYTHONUTF8=1`). این «لایهٔ ورودی» است — دست‌نخورده نگهش دار، فقط مصرفش را تمیز کن.

**شکلِ واقعیِ داده (schema — تأییدشده):**
- `LIVE_DATA`: `sog{identity_now, drift_now, healthy, default{Eshadow,Dself,identity}, surface[21×21]}` ·
  `events{total_rows, recent[≤400], by_name, by_status, by_agent}` · `frontier{total_cells, families, generation, cells[{family,rho,kurt,mi,count}]}` ·
  `budget{cap, cloud_calls, remaining, by_provider{fugu,glm,ollama}}` · `packets[{timestamp,alert_type,context,why_now,recommendation,consequence}]` ·
  `daemon{total_ticks, stopped_at, generation}` · `cycle[9 phases]` · `tcb[]` · `portrait{word_count,preview}`.
- `OPS_DATA`: `money{month{usd,aud}, today, confirmed, claimed, weights{value,urgency,efficiency,human,waste}, spend, projects[{id,name,status,detail,content_free}], proposals[{part,title,action}]}` ·
  `time{chrono_beat, metabolic_age, age_tick, deadlines[{label,date,days_left}], wires_on, wires_total, epoch_mode}`.
- `OCTOPUS_GRAPH`: `{nodes[{l,g,d,c}], edges[[a,b]], groups[{name,color,n}], total_files, total_links, shown_nodes}`.

**وضعیتِ فعلیِ دنیاها (که باید بهترش کنی):**
- هاب `worlds/index.html`: `graph-data.js` + `live-data.js` را لود می‌کند و `window.OCTO_CORE={graph,live}` می‌سازد + نوارِ vitals دارد. **این تنها «هستهٔ مشترک» است و فقط در صفحهٔ هاب زندگی می‌کند.**
- هر ۱۰ دنیا الان **جداگانه** `live-data.js` (و ۳/۶ هم `ops-data.js`) را لود و **مستقل پارس** می‌کنند — کدِ نگاشت در هر فایل تکرار شده.
- دنیاهای ۲/۵ گرافِ زنده دارند (`octo-core.js`)؛ بقیه canvas/Three.js مستقل‌اند.
- **گلوگاه:** هر صفحه HTMLِ جداست؛ globalها بینِ صفحات رد نمی‌شوند؛ هیچ ماژولِ دادهٔ واحدی وجود ندارد؛ ناوبریِ بینِ دنیاها فقط «‹ خانه» است؛ نمایِ «جریانِ داده از ورودی تا خروجی» هیچ‌جا دیده نمی‌شود.

---

## ۲. هدف (چه چیزی را وصل کنیم)
یک **ستون‌فقراتِ دادهٔ واحد** بساز که هر سه منبع را نرمال‌سازی و یکجا سرو کند؛ همهٔ دنیاها از همان بخورند؛
شبکهٔ دنیاها با ناوبری/سیگنالِ مشترک به‌هم وصل شود؛ و **کلِ مسیرِ ورودی→خروجی** (منبع → اکسترکتور → global → core → دنیا → کارِ بعدیِ کاربر) شفاف، معتبر و «سالم/کهنه» قابل‌تشخیص شود.

---

## ۳. معماریِ هدف (بساز این را)

### الف) `octo-data.js` — هستهٔ دادهٔ مشترک (تنها منبعِ نگاشت)
یک فایلِ جدید در `OCTOPUS/worlds/octo-data.js` که **همهٔ صفحات لودش می‌کنند**. باید:
1. سه global را بخواند (`LIVE_DATA`, `OPS_DATA`, `OCTOPUS_GRAPH`) با fallbackِ graceful (اگر نبود → `null`، نه crash).
2. یک API تایپ‌دار و مستند بدهد، مثل:
   `OCTO.sog()` · `OCTO.events()` · `OCTO.frontier()` · `OCTO.budget()` · `OCTO.packets()` · `OCTO.daemon()` ·
   `OCTO.money()` · `OCTO.time()` · `OCTO.graph()` · `OCTO.risks()` (نگاشتِ drift/budget/daemon/gate) ·
   `OCTO.vitals()` (رشتهٔ علائمِ حیاتی) · `OCTO.nextAction()` (مهم‌ترین کارِ الان از packets/daemon/proposals) ·
   `OCTO.freshness()` (سنِ هر منبع از فیلدِ `generated`).
3. helperهای مشترک: پالت (`cyan #22d3ee, pink #f472b6, gold #fcd34d, purple #a855f7, green #34d399, red #ef4444`)،
   فرمتِ عددِ فارسی، و «حالتِ نمادین» وقتی منبع خالی است.
4. صفرِ side-effect؛ فقط خواندن؛ idempotent.
سپس **هر ۱۰ دنیا + هاب را refactor کن** تا به‌جای پارسِ مستقیمِ globalها، از `octo-data.js` بخوانند
(کدِ تکراری حذف شود). هابِ `OCTO_CORE` را هم روی همین API سوار کن.

### ب) شبکهٔ دنیاها را وصل کن (Connected world-network)
- یک **هدرِ vitals مشترک** (identity ✓/drift · events · budget · gen · daemon) در **همهٔ** دنیاها از `OCTO.vitals()`.
- **ناوبریِ عرضی:** از هر دنیا به دنیاهای مرتبط لینک بده (نه فقط «خانه»). مثال‌ها:
  ریسک(۸)→تصمیم(۷) وقتی packet منتظر است؛ کاکپیت(۱)→هر دنیا که «کارِ بعدی» به آن اشاره دارد؛
  کهکشان(۵) کلیک روی نودِ Knowledge/Architect → هستی‌شناسی(۲).
- یک **بَجِ سراسری** برای «صفِ owner-gate (N)» که اگر packet منتظر باشد در همهٔ دنیاها دیده شود (مرزِ انسانی).

### ج) نمای «جریانِ داده» (Input→Output visibility)
هاب را با یک نوارِ **DATAFLOW** گسترش بده (یا یک دنیای ۱۱ کوچک): زنجیرهٔ
`منابعِ F: → ۳ اکسترکتور → ۳ global → octo-data → ۱۰ دنیا` را نشان بده،
با **freshness** هر مرحله (از `generated`) و پرچمِ 🟢تازه / 🟡کهنه(>۴۵ دقیقه) / 🔴غایب.
این همان «دیدنِ درست‌پیش‌رفتنِ جریان» است — اگر یک اکسترکتور نخورده باشد، اینجا قرمز می‌شود.

### د) استحکامِ لایهٔ ورودی
اکسترکتورها را دست‌کاریِ منطقی نکن (read-only و درست‌اند)، ولی:
- در `octo-data.js` سنِ داده را از `generated` بخوان و «کهنه» را به کاربر بگو (نه سکوت).
- اگر یک global غایب بود، همان دنیا graceful به «نمادین» برگردد و **دلیل** («extract_*.py را اجرا کن») نشان دهد.

---

## ۴. کارها به‌ترتیب (Ordered tasks)
1. `octo-data.js` را بساز و تست کن (روی داده‌های واقعی + حالتِ غایب).
2. هاب را رویش سوار کن؛ مطمئن شو نوارِ vitals و OCTO_CORE از API می‌آیند.
3. دنیا‌به‌دنیا (۱ تا ۱۰) به `octo-data.js` مهاجرت بده؛ کدِ پارسِ تکراری را حذف کن؛ رفتارِ بصری حفظ شود.
4. هدرِ vitals + ناوبریِ عرضی + بَجِ owner-gate را اضافه کن.
5. نوارِ DATAFLOW با freshness را بساز.
6. اورلیِ «◆ ریاضی ۳بعدی» (`octo-info.js` / `MATHVIZ.gap`) هر دنیا را با واقعیتِ فعلی هم‌راستا کن (برچسب‌های gapِ کهنه را پاک کن).
7. راستی‌آزمایی (بخش ۶).

---

## ۵. قواعدِ حاکمیت و صداقت (تخطی‌ناپذیر)
- read-only روی F:؛ فقط اکسترکتورها آن را می‌خوانند؛ ویژوال هرگز مستقیم به F: وصل نمی‌شود.
- Project-F فقط status؛ صفر echo هویت/محتوا؛ prune پابرجا.
- هر مقدارِ نمایشی یا `[FACT]` (از فایل خوانده شد) است یا `[EST]` (استنتاج) — علامت‌دار؛ عددِ ساختگی ممنوع.
- افزایشی: هیچ دنیایی نباید بشکند؛ هر تغییرِ بزرگ اول proposal.

---

## ۶. معیارهای پذیرش (Verification — همه باید سبز شوند)
- [ ] هر ۱۰ دنیا + هاب فقط از `octo-data.js` داده می‌خوانند (صفر پارسِ تکراریِ global).
- [ ] با حذف/کهنه‌کردنِ یک منبع، دنیای مربوط graceful «نمادین + دلیل» نشان می‌دهد (crash نه).
- [ ] هدرِ vitals و بَجِ owner-gate در همهٔ دنیاها دیده می‌شود و با داده‌ی واقعی می‌خواند.
- [ ] ناوبریِ عرضیِ حداقل ۳ مسیر (۸→۷، ۱→هدف، ۵→۲) کار می‌کند.
- [ ] نوارِ DATAFLOW سنِ هر ۳ منبع را نشان می‌دهد و کهنه/غایب را قرمز می‌کند.
- [ ] هیچ نوشتنی روی F: رخ نداده؛ privacy حفظ شده؛ اعداد با داده‌ی واقعیِ اکسترکتور مطابق‌اند
      (`identity 0.135073`, `events 5044`, `budget 998/1000`, `frontier gen 9`, `rev 0`, `chrono beat`, `wires 22/30`).
- [ ] `refresh-live-data.bat` هنوز exit 0 می‌دهد و هر سه فایل تازه می‌شوند.

---

## ۷. سبک و محدودیت‌ها
- RTL فارسی + اصطلاحاتِ فنیِ انگلیسی؛ پالتِ بالا؛ زیبایی‌شناسیِ dark holographic (scanline/glow) حفظ شود.
- ترجیحاً افزودنِ تک‌فایل (`octo-data.js`) + edit‌های کوچکِ surgical؛ WORLDS/CSSِ موجود را بی‌دلیل بازننویس.
- عملکرد موبایل: سبک بمان؛ Three.js فقط جایی که هست؛ کلِ core بدونِ dependency.
- در پایان: یک گزارشِ کوتاه بده — چه وصل شد، کدام مسیرِ ورودی→خروجی حالا سالم است، چه چیزی هنوز `[EST]`/نمادین مانده.
