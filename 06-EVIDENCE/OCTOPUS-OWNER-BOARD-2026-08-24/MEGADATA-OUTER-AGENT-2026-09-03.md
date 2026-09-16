---
title: MEGADATA — بستهٔ کامل ایجنتِ بیرون از سیزن
created: 2026-09-03 (عصر، لپ‌تاپ)
supersedes: MEGADATA-OUTER-AGENT-2026-09-02.md (همان پوشه — کهنه؛ نخوان به‌عنوان وضعیت زنده)
author: Cursor Grok — نشست لپ‌تاپ F:\backup
purpose: یک فایل خودکفا برای ایجنت تازه‌وارد بدون حافظهٔ هیچ نشستی
vantage: laptop DESKTOP-KA9RFN5 / 192.168.0.191 — این نشست برد ۱۸۰ نیست
measured_at: 2026-09-03T16:25+10
companion_files: 00-START-HERE.md · MEMORY.md · scans/VAULT-SCAN-F-DRIVE-2026-09-02.md · megaprompts/ ×4
---

# MEGADATA — OCTOPUS برای ایجنتِ خارج از سیزن

اگر فقط یک چیز بخوانی: **این فایل را از بالا تا §۵ بخوان، بعد بر اساس مأموریتت به §۱۳ برو.** اعداد کهنهٔ پوشهٔ دسکتاپ (بستهٔ ۲ سپتامبر) را تکرار نکن.

## ۰. هویت این سند و قانون شاهد

```
node_id        = laptop-DESKTOP-KA9RFN5
asserted_ip    = 192.168.0.191
vantage        = this_host_only
scope          = laptop_workspace + public GitHub API
claim_type     = measured | citation | inference   (هر بند برچسب دارد)
NOT            = board-180  (قانون نشست «این برد ۱۸۰ است» با eth0 نقض شد — توقف نقش ۱۸۰)
```

سلسله‌مراتب حقیقت: **runtime / `gh` / فایل روی دیسک > لجر والت > CHECKPOINT تازه > یادداشت قدیم > حافظهٔ ایجنت (ممنوع به‌عنوان شاهد).** عدد بدون فرمان منبع‌دار = unverified. `mtime` ≠ شاهدِ «نشست زنده».

بستهٔ خواهر روی main مخزن: `docs/agent-context/CHIEF-ENGINEER-BRIEF-2026-09-03.md` (از #137) — برای ایجنت فقط-گیت‌هاب. این فایل والت+سیزن+لین B را هم می‌دهد.

---

## ۱. یک پاراگرافی

OCTOPUS ارگانیسم نرم‌افزاری خانگی مالک (آری / @ari322، سیدنی) است برای سه کسب‌وکار: نقاشی ساختمانی Master Painting (Abbas) · فروشگاه هدیه ziman-gift.com (Maliheh) · استودیو Nova Soles (Saba). معدن بیرون صف است. چهار میزبان دارد (لپ‌تاپ ویندوزی درایو F: + سه برد LAN). مغز نوشتاری = والت Obsidian کانونیکال `F:\backup`. مغز کدی = مخزن عمومی `github.com/ari-OCTOPUS/ofn-node`. قانون مادر: **ارگان‌ها تشخیص و پیشنهاد می‌دهند؛ پچ و ارتقا و ارسال و ادغام فقط با رأی انسان.** متریک کمپین این سیزن: یک رسید پرداخت روی `PAINT-L5-001` — تا آخرین لجر والت هنوز صفر است (سطح کسب‌وکار جدا است؛ قاطی نکن).

---

## ۲. توپولوژی ماشین‌ها (citation + measured)

| میزبان | نقش | دسترسی از این لپ‌تاپ | وضعیت آخرین کشف |
|---|---|---|---|
| لپ‌تاپ `.191` | والت کانونیکال + کلون کار + ارگانیسم والت روی 8771–8776 | محلی — همین نشست | **measured** hostname `DESKTOP-KA9RFN5`، IPv4 `192.168.0.191` |
| board138 `.138` | دروازه کسب‌وکار DietPi؛ sqlite زنده؛ `~/ofn` + `~/octopus-mesh` نسخه‌نشده | `ssh board138` / `ssh ari@192.168.0.138` — sqlite فقط `-readonly` | citation: کشف ۳برد + SEASON-LOG Round 11 |
| board180 `.180` | مغز مش `octopus-continuity-180`؛ lab روی 8090/8081/8780؛ chrony | `ssh root@192.168.0.180` (کلید لپ‌تاپ در `~/.ssh/config`) | citation: `DISCOVERY-3BOARD-20260903/nodes/board-180/NODE-IDENTITY.json` |
| board182 `.182` | شاهد `sensorium-opi5pro`؛ NATS 4222 روی LAN | `ssh root@192.168.0.182` | citation: همان رجیستر؛ WAL=WITNESS_A از اینجا خوانده شد |

دادهٔ زندهٔ 138: `~/.local/share/ofn/` و `~/ofn/ofn/agi2027_runtime/`. راز/کلید: `F:\OCTOPUS-SURVIVAL-BACKUP-2026-08-19` — فقط نقشش آزاد است؛ محتوا هرگز.

`F:\backup\mesh` یک **فایل صفر-بایتی** است. مغز مش واقعی = نودهای 180/182/138. فریب نام نخور.

---

## ۳. والت‌ها و مخازن

### والت‌ها (اسکن ۲ سپتامبر — ۱۸۹ پوشهٔ `.obsidian`)

گزارش کانونیکال: `scans/VAULT-SCAN-F-DRIVE-2026-09-02.md` همین پوشه + `F:\backup\06-EVIDENCE\OCTOPUS-OWNER-BOARD-2026-08-24\VAULT-SCAN-F-DRIVE-2026-09-02.md`. sha256 گزارش: `cb1dbb1e132e7ce0…c08ba5e`.

**واقعی مستقل (۱۱):**
1. `F:\backup` — کانونیکال (رأی مالک ۲۰۲۶-۰۸-۱۵ در `00-INDEX.md`) ~۷۲٬۵۰۰ md
2. `F:\romajan` — ۵۲ md، پژوهش تکثیر؛ round-3 کامل (نه رهاشده)
3. `F:\_______Black Box` — ۳۵ md، NBB-CP + ۱۷۱ تست
4. `F:\ofn-node` — ریشهٔ مخزن؛ `.obsidian` داخل گیت است → هر worktree کپی می‌گیرد
5–6. `F:\octopus-phase0-A-halt` / `-isolated` — دوقلوی منجمد ۲۳ ژوئیه (**قراردادهای BB-×۹ فقط اینجا زنده‌اند**)
7. `F:\backup-island` — ۶٬۰۱۴ md تا ۱۹–۲۰ اوت
8–9. `backup-SAFE-2026-07-19` / `backup-snapshot-20260723-121256`
10. `backup-deploy-lab` — اسکلت
11. `backup-Archive\مغز دوم` — ۴ md

**تو در تو داخل backup:** OFN-Board · architect · OCTOPUS-DOCTOR (دکتر والت، baseline واقعی **۱۶۸/۱۶۸** نه ۱۵۷) · `_github-export/ofn-node`.

**والت نیستند:** `F:\.obsidian` پوستهٔ خالی · `wt-*` (worktree گیت، `app.json` یکسان `4e670212…`) · campaign-tmp · `.claude\worktrees` (منبع تکرار آینه) · `OCTOPUS-SURVIVAL-BACKUP-2026-08-19` (مواد کلیدی).

### سیاست نوشتن والت

حقیقت فقط در `F:\backup\06-EVIDENCE\OCTOPUS-OWNER-BOARD-2026-08-24\` (append-only). `01-TRUTH\` = redirect. `OCTOPUS\CURRENT-TRUTH.md` خط ماشین‌نوشتهٔ `_ops` است — دست نزن. حذف ممنوع؛ فقط `99-ARCHIVE\` با پیشوند `archive_`. `git add -A` در والت **ممنوع** (کلون‌های توکار را جارو می‌کند).

### مخزن کد

- ریموت: `github.com/ari-OCTOPUS/ofn-node` — **PUBLIC** (private به‌خاطر صندلی رایگان شکست؛ sanitize روبه‌جلو).
- کلون محلی `F:\ofn-node` الان **اشغال** است: برنچ `fix/demand-harvest`، behind 2، فایل‌های untracked زیاد. **دست نزن.** الگوی امن: worktree تازه `F:\wt-<lane>`.
- `AGENTS.md` ریشه برای همه الزامی است.

---

## ۴. حاکمیت — نقض = حذف تغییرات

1. **لیست آهن (فقط مالک):** پول · رضایت/مخاطب · راز · سیاست · کشته‌کُش. restart/kill/bind پروسه ممنوع مگر رأی صریح.
2. **نام‌های مهروموم‌شده** در `ofn/kernel/events.py`: `quote_sent` / `send_authorized` بازنشدنی مگر رأی. زنجیرهٔ درآمد در `campaign_envelope_ready` تمام می‌شود.
3. **ادغام:** فقط `mergeable_state=clean` + یک رأی انسانی معتبر (`Elahe-z` یا `aram-ui` طبق GOV-V6). bot ≠ انسان. `--admin` ممنوع. self-merge ممنوع. دروازهٔ استقلال by-design قرمز می‌ماند تا انسان تأیید کند — workflow را ویرایش نکن، re-trigger نکن.
4. **حفاظت main (measured 2026-09-03 via `gh api …/branches/main/protection`):** `strict=true` · `dismiss_stale_reviews=true` · `enforce_admins=true` · `required_approving_review_count=1` · `require_code_owner_reviews=true` · چک‌های لازم: `hygiene` + `test (ubuntu-latest)` + `test (windows-latest)` + `require-independent-approval`.
5. **چک‌ها** را از `/commits/{sha}/check-runs` بخوان نه combined-status. اگر approvals هست ولی protection می‌گوید چک fail است = لنگر روی run قدیمی («چفتِ کور») — `gh run rerun --failed` نه force.
6. **لین:** یک ایجنت = یک worktree + scope در `09-LANES/`. فایل لین دیگر = توقف. حق rebase کار لین دیگر را نداری.
7. **فلگ‌های ممنوع برای روشن‌کردن بدون رأی:** `OCTOPUS_WIRE_*` · `OFN_WIRE_*` · `OBSERVATORY` · `CORTEX_HYPOTHESIS` · `auto_email` · `OFN_KEEP_GATES_OPEN` · `ofn/config.py` را برای سبز کردن تست عوض نکن.
8. **کانال ارسال — یک در، یک رأی** (OWNER-GO-LOCKS، citation): لید ایمیل آژانس‌ها ≠ DET/مشتری ≠ تلگرام مالک ≠ پل `cp.master-painting.com`. رأی یک دامنه مجوز دامنهٔ دیگر نیست.
9. **مدارک مالی** هرگز در مخزن عمومی. فقط والت + بورد 138.

---

## ۵. وضعیت اندازه‌گیری‌شدهٔ همین لحظه (لپ‌تاپ، ۲۰۲۶-۰۹-۰۳ ~۱۶:۲۵ +۱۰)

| سطح | مقدار | شاهد |
|---|---|---|
| GitHub `main` | `7af991d3c3fa3697c42f3ca6f9039410d1374bfd` | `gh api repos/ari-OCTOPUS/ofn-node/commits/main` — پیام: `feat(p1): kernel-pure architecture-contract bind + pin (#149)` · committer `2026-09-03T06:23:46Z` |
| حفاظت main | strict+dismiss+enforce_admins همه true | بند ۴ |
| PR #86 دکتر لین B | **MERGED** `2026-09-02T10:23:25Z` squash `389d39958e34568ce225d4cb45522d64921aed47` از base `94f9622` | `gh pr view 86` |
| worktree لین B | `F:\wt-self-completing-doctor` @ `44129564c46a42ba7a21d2886d2eeb6a65b4c119` برنچ `lane/self-completing-doctor` | git محلی |
| کلون `F:\ofn-node` | اشغال `fix/demand-harvest` @ `34e63a04…` dirty + behind 2 | **دست نزن** |
| والت HEAD | `d28fdf2bb7ee16722da61c8446c0ee06f21847e3` — `SNAPSHOT 2026-09-03 (~14:05 AEST)` | `git -C F:\backup` |
| ارگانیسم والت | زنده: `started=2026-09-03T09:22:06` · `beat=60431` · `frozen=false` · پای `lead-naghshi=alive` | `_ops/state/ORGANISM-STATE.json` ts `2026-09-03T16:05:11` |
| `debug-4ab476.log` ریشه | **وجود دارد** ۸۹٬۶۹۸ بایت · LastWrite `2026-09-03 09:04:27` | `Get-Item` — redirect **UNAUTHORIZED**؛ نکش، پاک نکن |
| آینهٔ LB-V1 | pointer است (نه محتوا) | `06-EVIDENCE\OCTOPUS-HANDOFF-MERGE-2026-08-22\merged\CURRENT-TRUTH.md` خط اول `# REDIRECT` |
| صف باز GitHub | غیر‌درافت: **#148** (p1 envelope/store، BLOCKED) · **#113** (110B PARKED) · **#71** (landing release/p0) + چند درافت p1 (#147…#125) | `gh pr list --state open` |

حافظهٔ نشست‌های موازی هنوز `main=60dce961` یا `825837cb` می‌گوید — **کهنه است.** main از موج خودمختاری جلوتر رفته تا #149.

بستهٔ روزانهٔ مالک `OWNER-DAILY-PACKET-2026-09-03.md` هنوز WAL=`"0"` و board=`e68aedeb` می‌نویسد — با لجر بعدی (WAL WITNESS_A + موج مرج) **تناقض سندی** دارد. قبل از عمل آن بسته را از نو اندازه بگیر.

---

## ۶. پروندهٔ لین B / دکتر خودتکمیلی — بسته

فرمان اجرایی مالک ۲ سپتامبر اجرا شد. وضعیت معتبر: **DONE + RATIFIED برای LB-V1..V4**. LB-V5 باز. debug-redirect تصویب‌نشده.

| کلید | مقدار |
|---|---|
| PR | https://github.com/ari-OCTOPUS/ofn-node/pull/86 — **ادغام‌شده** |
| بستهٔ کد | `ofn/doctor/` (پارسر miniyaml، راند فقط‌خواندنی، رسید jsonl+sha256، self-backlog ۹ فیلد، destiny چهار سرنوشت؛ PENDING بدون دلیل غیرقابل‌نمایش) |
| قرارداد | `LAB-DOCTOR-CONTRACT.yaml` → ۱۶ الزام: ۱۲ پیاده + ۲ واگذار به لین C با گارد امتناع + ۲ بک‌لاگ |
| baseline والت دکتر | **۱۶۸/۱۶۸ exit 0** (نه ۱۵۷ — عدد کهنه) |
| راند واقعی | `09-LANES/LB/runs/2026-09-02-final/` — ۲۳ یافته → پس از آرا ۱۳ همه LOW |
| کامیت والت چهار رأی | `5f38f487ad3233084db5820cf128be2a7ce4fe5a` (فقط pathهای LB-V1..V4) |
| رسید تصویب | `06-EVIDENCE\OCTOPUS-OWNER-BOARD-2026-08-24\LB-RULINGS-EXECUTED-2026-09-02.md` — نقل‌قول مالک ۲۰۲۶-۰۹-۰۲ ۱۹:۵۸:۴۷ +1000 |

رأی‌های اجراشده:
- **LB-V1** آینهٔ محتوادار → pointer؛ بایت‌به‌بایت در `99-ARCHIVE\mirror-cleanup-20260902\` (sha `7354caf8…`)
- **LB-V2** `C-NNN-*.md` → `C-0*.md` در LEDGER
- **LB-V3** خط‌زدن `verify_live_store.py` در STATE-NIGHT و TEST-COUNT
- **LB-V4** ۷ junk ریشه → `99-ARCHIVE\root-junk-20260902\`
- **LB-V5** زمان‌بندی ۲۱ اندام — **OPEN** (بعداً به لین C/D ارجاع شد؛ خودت زمان‌بندی نکن)

درس resolver: ارجاع بی‌مسیر اغلب **جابه‌جاشده** است نه مرده. نردبان ۴ پله: root-rel → src-rel → wildcard → ایندکس basename کل والت.

سه دکتر را قاطی نکن:
1. `ofn/doctor/` — اسکنر والت (لین B، #86)
2. `ofn/agents/doctor.py` — تیک سلامت بورد (موج خودمختاری #128)
3. `_ops/doctor/doctor.py` — دکتر تکاملی ۱۵۰۰خطی میراثی والت (انگل روی pacemaker؛ merge فقط human-append؛ λ_persist منفی)

---

## ۷. Wave 1 — فایل‌های مفهوم ریشه (کجا هستند، کجا نیستند)

| مفهوم | محل زنده | محل مرده/گم |
|---|---|---|
| BB-*.openapi.yaml (۹ تا، incl. Telemetry) | **فقط** دوقلوی منجمد `F:\octopus-phase0-A-halt` | ریشهٔ `F:\backup` صفر است |
| CONSTITUTIONAL-ZONES.yaml | ریشهٔ `F:\backup` (mtime ~08-19) | در مخزن ofn-node روی main غایب |
| LIFE-CURRENCY | همان ریشه + state: `_ops/state/pulse/life-currency-latest.json` | اقتصاد اندامی فاز ۲ پیاده نشده |
| LIVE-ORGANISM-MAP | ریشهٔ والت | — |
| PRE-0 / OCTOPUS-PRIME | والت + وابستگی واقعی به phase-0 | — |
| نقشهٔ اختاپوس / VERDICT_QUEUE | `06 - Architecture Maps\نقشه-اختاپوس\VERDICT_QUEUE.md` زنده (LB-V1..V5) | صف دوم داخل `4d_system` از ۲۰۲۶-۰۷-۱۱ منجمد |
| LAB-DOCTOR-CONTRACT.yaml | مخزن `ofn-node` (به فایل‌های والت وابسته است — قرارداد همگام‌سازی ندارد) | — |

چهار رأی باز CONSTITUTIONAL-ZONES از ۲۰۲۶-۰۸-۱۹: منطقهٔ MCP · schema-vs-value فلگ ACTIVATION · آیا phase-0 به B0 می‌چسبد · طبقه‌بندی `run_sandbox`.

---

## ۸. دو ارگانیسم زنده (کشف ۳ سپتامبر — قاطی نکن)

**ارگانیسم والت روی لپ‌تاپ:** پروسه‌های `F:\backup\_ops` روی پورت‌های **8771–8776**، ری‌استارت امروز ~۰۹:۱۳–۰۹:۲۲، beat شصت‌هزار+. self-model اگر «اعضای سالم» ببیند ممکن است **خودش** را دیده باشد نه بورد را.

**بدنهٔ بورد 138:** سه ریشهٔ کد — `~/ofn` (مخزن) · `~/octopus-mesh/bin` (router+settler از ۲۶ اوت، **نسخه‌نشده**) · `agi2027_runtime` داخل درخت. پورت‌های **8791–8794** = یک پروسه `python3 -m ofn.run` روی چهار سطح loopback، نه چهار سرویس. 8796 = healthz پل.

Mesh V1 ادعاشده در docs (۹ دیمون / ۷۱ تست) **فقط روی بورد** است؛ در مخزن نیست.

---

## ۹. مگاپرامپت‌ها و پارک لین‌ها

چهار فایل در `megaprompts/` همین پوشه. مالک آن‌ها را **عمداً** از `agent-prompts` به دسکتاپ برد — برنگردان.

| فایل | موضوع | اجرا |
|---|---|---|
| CONCEPT-DEBT-CENSUS-2026-09-02 | طرح‌ضد-ساخت؛ کلاس ۷گانه fail-closed | جزئی: ۱۵ کشف ۲ سپتامبر + ۱۵ کشف ۳ سپتامبر |
| PARALLEL-ORGANISM-BUILD-2026-09-02 | لین A خودآگاهی / B دکتر / C لاب 138 / D تکامل | A و B تحویل شدند (#81، #86، #90). C و D پارک |
| ATTENTION-DEBT-2026-09-02 | ۶ کورنقطه α–ζ | نوشته؛ با مورد بعدی هم‌پوشان |
| NEGLECTED-BODY-2026-09-03 | بدن مغفول (بورد/بکاپ/بهداشت/census/مش) | نوشته؛ **قبل از اجرا با ATTENTION-DEBT دداپ کن** |

فرمان سه‌لینهٔ ۳ سپتامبر (`OWNER-ORDER-THREE-LANES-2026-09-03.md`) مگاپرامپت‌های ۱۱-لینه را به **بک‌لاگ کورنقطه** تبدیل کرد. تا پرداخت کمپین = ۱ فقط سه لین فعال بودند؛ مادهٔ ۱۰ Cockpit+تلگرام را از پارک درآورد. فیلتر ایستاده: کار جدید باید `revenue_distance` یا `risk` یا `owner_attention_cost` را کم کند وگرنه BACKLOG.

لین‌های هم‌نام را قاطی نکن: «لین B» در مگاپرامپت ارگانیسم = دکتر والت؛ «لین B» در فرمان سه‌لینه = تشخیص Pulse/IMAP فقط‌خواندنی.

---

## ۱۰. دو دسته کشف مفهومی (خلاصه)

### شب ۲ سپتامبر (۱۵)
دکتر تکاملی `_ops/doctor/doctor.py` + قانون «نرخ تکامل = نرخ حضور انسان» · سنسور طیفی `spectral.py` آزمایش‌نشده · MAP-Elites / measured_lift / tournament در `evolution.py` · اتاق تخاصمی `chamber.py` · CHRONOS-FABLE-OS در `_Archive` · نظام عصبی ۱۷-استخراجگر (`nervous-system/`، والت→`graph-data.js`) · هشت‌جهان `OCTOPUS/worlds/` · نردبان A0→A6 · orphan-watchdog زنده · `restore_drill.py` در مخزن هست · سرشماری ۵۶۵تایی با بازهٔ گمشده ۳۲۸–۴۶۳ · romajan round-3 کامل.

### روز ۳ سپتامبر (۱۵) — `octopus-deep-scan-15-findings-20260903`
دو ارگانیسم (§۸) · mesh runtime نسخه‌نشده روی بورد · `economy.py`/FAKE_REWARDS روی main غایب بود (شاخهٔ #67) · لایهٔ قانون اساسی در مخزن غایب · وابستگی قراردادی دکتر به فایل والت · Governor: فایل هشدار ۵۰۴KB امروز بدون کد governor + هر دو `.flag` و `.flag.off` · لین‌های L3–L6 شبح · دو VERDICT_QUEUE · هیچ سنسور واقعی (`real_sensor:false`) · پورت 8796 فقط در docs قدیمی · `shopify_connector.py` واردکنندهٔ صفر (مسیر واقعی oauth) · بکاپ بورد = sqlite+state نه سیستم · TODO مخزن ≈۲؛ بدهی در YAML اعتراف می‌شود.

همگرایی واجب: لین دکتر جدید (`ofn/doctor/`) را با دکتر تکاملی `_ops` دوباره نساز.

---

## ۱۱. تصمیم‌های باز — فقط دست مالک

از استنباط رأی تازه از سکوت خودداری کن.

1. **LB-V5** زمان‌بندی ۲۱ اندام — OPEN
2. **redirect مسیر debug** حلقهٔ `memory_read_loop.py:tick_from_spine` — UNAUTHORIZED (فایل ریشه هنوز زنده است)
3. پاسخ DET (ارسال از mailbox مالک؛ R3) — نزدیک‌ترین گام کمپین
4. سؤال $306.90 از MP Construct — متن در OWNER-PACK-v4
5. ثبت Supplier Hub / SCM0256
6. چهار پرسش CONSTITUTIONAL-ZONES
7. URL برای harvester زیمان (#141 روی main ولی inert تا URL+دو قفل)
8. نصب Playwright روی 138 برای صادرات ۳۷ رکورد buy.nsw — یا صبر برای الهه
9. نصب تایمرهای oneshot خودمختاری روی 138 (runbook #131؛ صفر restart سرویس زنده)
10. #113 / 110B — پارک تا سازگاری D-26/D-27
11. #71 landing `release/p0` — بیرون صف main
12. #148 و درافت‌های p1 — رأی انسانی
13. صید ۳۷تایی: «بخریم یا بگیریم»

بستهٔ رأی روزانه اگر ساختی: حداکثر ۵ آیتم، تک‌خطی PowerShell بدون گیومهٔ داخلی، از لین C عبور کند.

---

## ۱۲. تله‌های فنی (هزینهٔ واقعی داده‌اند)

- محتوای بک‌اسلش/اسکیپ فقط با Write/Edit — heredoc باش NUL می‌سازد؛ بعد `ast.parse`.
- PS 5.1 گیومهٔ داخلی را می‌خورد؛ اسکریپت‌ها ASCII خالص؛ دستور مالک = یک خط.
- `pytest | tail` کد خروج را می‌بلعد → `${PIPESTATUS[0]}`.
- fetch داخل حلقه؛ بعد از هر merge دوباره `origin/main` را بگیر.
- push رد شد → fetch + بازرسی؛ `--force-with-lease` فقط بعد فهم سر ریموت.
- squash یعنی SHA برنچ ≠ SHA روی main — با شمارهٔ PR چک کن.
- `index.lock` والت: ۰ بایت + بی‌پروسه = قابل حذف؛ وگرنه نه.
- fixture باید غیاب را هم بازتاب دهد.
- GET حفاظت را PUT نکن (۴۲۲، صفر تغییر) — بدنهٔ write-schema تازه.
- زیر-endpoint protection گاهی ۴۰۴ — PUT کامل با `--input` فایل.
- `git add -A` در والت ممنوع.
- ادعای «۱۵۷/۱۵۷» و «#86 باز» و «main=60dce961» همگی در حافظهٔ ایجنت کهنه شده‌اند.

کیبورد اشتباه: متن بی‌معنی انگلیسی‌نویس اغلب فارسی است. دیکشنری وایب در حافظهٔ `octopus-vibe-coding-lexicon`.

---

## ۱۳. شروع سریع بر اساس مأموریت

**ورود عام:** `AGENTS.md` مخزن (از GitHub، نه از کلون کثیف) → این فایل §۴–§۵ → `CURRENT-TRUTH.md` بورد مالک → `OWNER-GO-LOCKS.md` (هر عدد باید `measured_at` داشته باشد؛ اگر نداشت از نو اندازه بگیر).

**درآمد/کمپین:** بورد مالک + `payment-receipts/` + پیش‌نویس DET. ارسال فقط دست مالک. کمپین `PAINT-L5-001` را با پرداخت‌های بانکی کسب‌وکار قاطی نکن.

**کد/اندام:** worktree تازه از `origin/main` (`7af991d3` را اول دوباره fetch کن) → DoD اولین کامیت → `09-LANES/<لین>/`. فایل لین A (cockpit/self-model/brain-probe) را اگر لین دیگری هست لمس نکن.

**والت/حقیقت:** فقط owner-board append-only. آینه نساز. راند دکتر = `--vault F:\backup` فقط‌خواندنی.

**بقا:** `octopus_recovery/restore_drill.py` وجود دارد؛ `POWER-CUT-TEST.md` را بخوان. بکاپ واقعی 138 = `ofn-backup.service` نه `octopus-backup` (حذف‌شده، exit-127 بود).

**مش/برد:** اول کشف `DISCOVERY-3BOARD-20260903/`. از لپ‌تاپ به 138 مستقیم سیم کد نیست — خون = GitHub + SSH ایجنت. NATS روی 182 کلاینت مخزنی ندارد.

**پژوهش:** romajan تمام تا handoff دادهٔ واقعی. NBB-CP مخزن جدا. دوقلوی phase0 = قراردادهای BB.

**ایجنت فقط-گیت‌هاب:** `docs/agent-context/CHIEF-ENGINEER-BRIEF-2026-09-03.md` روی main.

---

## ۱۴. نقشهٔ مسیرهای پرمصرف

```
C:\Users\Armin\Desktop\اختاپوس بک لپ\          ← همین بسته (ورود برای ایجنت بیرونی)
F:\backup\06-EVIDENCE\OCTOPUS-OWNER-BOARD-2026-08-24\
        CURRENT-TRUTH.md · OWNER-GO-LOCKS.md · SEASON-LOG.md · DECISIONS-LOG.md
        LB-RULINGS-EXECUTED-2026-09-02.md · FOUR-GATES-RULING-20260903.md
        DISCOVERY-3BOARD-20260903\ · ZIMAN-SEASON-2026-09-03.md
        payment-receipts\ · revenue-records\ · company-docs\
F:\backup\01-TRUTH\                            ← redirect-only
F:\backup\_ops\state\ORGANISM-STATE.json       ← ارگانیسم والت
F:\backup\_ops\doctor\                         ← دکتر تکاملی میراثی
F:\backup\OCTOPUS\worlds\                      ← هشت‌جهان
F:\wt-self-completing-doctor\                   ← لین B (پرونده بسته؛ PR ادغام شده)
F:\ofn-node\                                   ← اشغال — worktree جدا بساز
github.com/ari-OCTOPUS/ofn-node                 ← main را از ریموت بخوان
ssh board138: ~/.local/share/ofn/*.sqlite      ← دادهٔ زنده (readonly)
```

---

## ۱۵. ممنوعه‌های مطلق برای ایجنت تازه

- merge کردن PR خودت · `--admin` · force push کور
- نوشتن/درمان خودکار روی `F:\backup` خارج از owner-board
- برگرداندن مگاپرامپت‌ها به `agent-prompts`
- لمس checkout کثیف `F:\ofn-node`
- کشتن/ری‌استارت پروسه · پاک کردن `debug-4ab476.log`
- روشن کردن WAL / WIRE / KEEP_GATES
- ارسال ایمیل/تلگرام/پول · حدس ABN/بیمه/قیمت
- نوشتن `revenue` / `sent` / `booking` در لجر هویت ارگانیسم (آن‌ها فقط از لجر 138 می‌آیند)
- bind روی `0.0.0.0` از این نشست
- ساخت broker / DB / orchestrator تازه
- ادعای system_wide بدون شاهد دو `node_id`

---

## ۱۶. قالب گزارش اگر کار تحویل می‌دهی

شواهد نه ادعا. هر وضعیت: SHA + فرمان دقیق + timestamp + exit code + مسیر رسید.

وضعیت معتبر فقط: `DONE` | `BLOCKED_BY_OWNER` | `BLOCKED_BY_FILE_COLLISION` | `FAILED_WITH_EVIDENCE`.
عبارت «تقریباً تمام» ممنوع.

اگر رأی مالک لازم است حداکثر یک OWNER ITEM: یک خط PowerShell بدون گیومهٔ داخلی + یک خط VERIFY + ❌ DO NOT.

---

*اگر این فایل با runtime تناقض داشت، runtime مقدم است — تناقض را با شناسه ثبت کن، ساکت درست نکن.*
*بستهٔ ۲ سپتامبر را نگه دار به‌عنوان تاریخچه؛ برای ورود از این فایل استفاده کن.*
