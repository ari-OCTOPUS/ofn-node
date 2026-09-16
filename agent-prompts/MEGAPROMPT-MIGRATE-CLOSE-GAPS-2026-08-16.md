---
type: prompt
status: active
created: 2026-08-16
updated: 2026-08-16
tags: [octopus, megaprompt, migration, m0, fencing]
project: "[[04 - Architect System/architect/PROJECT]]"
---

# MEGAPROMPT — بستن جاافتادگی‌های مهاجرت + fencing (ایجنت بعد)

کپی کامل همین فایل. پیست AUTOFLOW / REST-NIGHT / SELFRUN / PERPETUAL / SEAM-LOOP / COWORK را SoT نگیر. EQUIP G8 را از نو نکن.

ورود قبل از هر کار:

```
01-TRUTH/STATE-2026-08-15-NIGHT.md §8
00 - Inbox/2026-08-16 OWNER-PENDING — All Open Items (Master Checklist).md
07 - Knowledge/شناخت-اختاپوس/61-OBSIDIAN-NIGHT-LOCK-2026-08-16.md
07 - Knowledge/شناخت-اختاپوس/57-LAPTOP-TO-ARM1-MIGRATION-2026-08-16.md
07 - Knowledge/شناخت-اختاپوس/60-THREE-BOARD-AND-FPGA-CORRECTED-2026-08-16.md
06-EVIDENCE/BEAT-OWNERSHIP-LEASE-2026-08-16.md
06-EVIDENCE/LIVE-VS-PASTE-SCAN-2026-08-16.md
01-TRUTH/CONTRADICTIONS.md   ← rg "id: C-0" قبل از هر شناسهٔ نو
```

Vault زنده = `F:\backup`. درخت در حال اجراست. آزاد بعدی هنگام نوشتن این فایل: **C-034** (C-019..C-033 مصرف). شواهد G8 ادعا کرده C-034 را گرفته ولی `CONTRADICTIONS.md` هنوز C-033 است — اول این را آشتی بده، شناسه نسوزان.

HEAD مرجع هنگام نوشتن: `d7aeabe` روی شاخه `equip/g8-containment-20260816` (G8 CONDITIONAL PASS). قبل از کار: `git status -sb` و `git log germline/master..HEAD`.

---

## تو کی هستی

ایجنت روی لپ‌تاپ ویندوز مالک (آری، سیدنی). مأموریت: **دیباگ + بازنویسی تمیز + تکمیل جاافتادگی‌های همین شب Grok**، بعد **همه‌اش را در ابسیدین قفل کن**. Cutover نکن. FPGA نخر. ارگانیسم زنده را مسلح نکن.

جملهٔ اصلی مهاجرت: **تو کد را منتقل نمی‌کنی، مالکیت حقیقت را منتقل می‌کنی.** پایان = لپ‌تاپ بسته، هیچ اتفاقی نمی‌افتد. الان هنوز آنجا نیستی.

YOU ARE HERE:

```
[x] فاز ۰ fencing lease روی دیسک، unarmed
[ ] M0 بازرسی Windows→Linux + نقشهٔ اسرار + smoke
[ ] قلاب chrono پشت فلگ خاموش
[ ] on_event روی jsonl سایه (نه لجر زنده)
[ ] M1..M6 — خارج از این نشست مگر مالک عین کلمه بگوید
```

---

## این چت چه بود (سه فرمان، یک قوس)

1. **آزادی قانونی / OCTOPUS v3.0:** شورا + AGENT-KIT روی همین ریپو. آزادی = حاکمیت (لایسنس وزن · زیرساخت · نویسندهٔ policy · داده)، نه abliteration. سخت‌افزار **Lenovo 81Y6 / ~۱۶GB / 1660 Ti** نه G700/64GB. سقف زنده **AU$2/روز / AU$30/ماه** نه ۳۰۰. MCP این ریپو دست‌نویس `"2025-06-18"` است نه sdk 2.0. P0 overlay: `_ops/octopus_v3/` · `WIRED=False` · ۱۸ تست · نوت ۵۶.
2. **مهاجرت لپ‌تاپ→Arm:** Beat Ownership Lease فاز صفر. اول پروتوتایپ HMAC (`octopus_v3/beat_lease.py`، ۱۰ تست). بعد مالک fencing آورد.
4. **سه برد + FPGA:** پاهای روشن = M4. خالی۱ = M1 شاهد. خالی۲ = M2 سپس M3. ۲× 200T = M5 ترمز. PolarFire PUF روی Artix-7 **نیست**. نوت ۶۰. rsync نکن مگر مالک IP/OS بدهد و M0 سبز باشد.

جاافتادگی‌ها عمداً ماندند تا تو ببندی — نه اینکه از نو اختراع کنی.

---

## آنچه تمام است — دوباره کاری = اتلاف

OWNER-EASE · OWNER-CLOSE · Cowork نوشته شد · EQUIP ترتیبی نوشته شد · G8 CONDITIONAL PASS (`06-EVIDENCE/EQUIP-G8-CONTAINMENT-2026-08-16.md`) · v3 P0 unarmed ۱۸/۱۸ · fencing ۱۷/۱۷ · HMAC قدیمی ۱۰/۱۰ (legacy) · FPGA نوت ۵۸. AUTOFLOW/REST-NIGHT/DEEP-SEAMS/IMPROVE-ACF/WEBPANEL/INTERVIEW.

HARDTEST VOTE 1–4 · PEP enforce · epistemics تولیدی · هویت→گیت · سیم P0 به PEP · MCP sdk 2.0 داخل `_ops` · مدل ۷بی/۲۷بی · vaara install · چرخش `.env` در ریپو · خرید FPGA · M3 cutover — **کارت بماند، اجرا نشود.**

---

## قواعد سخت

1. WORKLOCK: `_ops/tests/run_all.py` · `_ops/wiring.py` · `_ops/telegram_center/center.py` · `_ops/orphan_scan.py` — تست نو = فایل نام‌یکتا؛ **گزارش کن، ثبت نکن**.
2. `git add -A` هرگز. `_ops/state/**` زنده، `ledger.jsonl`، `nervous-system/*-data.js`، `_memory/HEARTBEAT.md` را کامیت نکن.
3. این worktree الان G8 است. فایل مهاجرت را داخل کامیت G8 نگذار. شاخهٔ پیشنهادی: `migrate/m0-close-gaps-20260816`. از مالک بپرس اگر شک داری.
4. پوش فقط با کلمهٔ تازه در **همین** پنجره (C-023).
5. TCB / `.env` / اولاما ۷بی / پروب پولی / حذف / `--amend` / STOP-ORGANISM / `BEAT-FREEZE.flag` روی درخت زنده / `OCTOPUS_BEAT_LEASE=1` روی پروسهٔ زنده — نه.
6. `*.md merge=union` — HANDOFF را چشمی چک کن.
7. PowerShell: HEREDOC بش نساز.
8. دو فریز را قاطی نکن: `_ops/budget/FREEZE.flag` ≠ `_ops/state/BEAT-FREEZE.flag`.
9. `_ops/state/migration/MIGRATION-INVENTORY.md` ممیزی MCP است نه اسکن Windows. **overwrite نکن.** گزارش M0 را جای دیگر بنویس.
10. SoT lease = `_ops/runtime/beat_lease.py`. `octopus_v3.beat_lease` fencing نیست — سیم نشود.

---

## کار ۱ — دیباگ (اجباری، قبل از کد نو)

شواهد در `06-EVIDENCE/` با عدد. حدس ننویس.

| # | شکاف | چرا خطرناک است | حکم پیشنهادی |
|---|---|---|---|
| D1 | دو ماژول lease | کسی `beat_allowed()` HMAC را به chrono وصل می‌کند؛ fencing دور می‌خورد | اگر `OCTOPUS_BEAT_LEASE=1`، مسیر HMAC باید deny یا به runtime تفویض کند. تست نام‌یکتا |
| D2 | فایل خراب ⇒ `revision=1` | همان باگ vacate؛ نویسندهٔ کهنه با token=2 می‌برد | acquire روی JSON خراب **fail-closed** مگر sidecar revision سالم باشد. تست رگرسیون |
| D3 | کامنت `_read_unlocked` دروغ می‌گوید «از صفر شروع نمی‌شود» | تست `token==1` روی corrupt با کامنت تناقض دارد | کامنت را با رفتار یکی کن |
| D4 | `FileLeaseStore.read` بدون قفل | روی دیسک محلی با replace اتمی معمولاً OK؛ روی شبکه ممنوع است (UNC از قبل RuntimeError) | اگر سوراخ دیدی ببند؛ وگرنه در شواهد بنویس «قبول‌شده برای M0/M1 محلی» |
| D5 | G8 `contradiction_claimed: C-034` بدون ردیف در CONTRADICTIONS | شناسه می‌سوزد یا دوبار مصرف می‌شود | آشتی بده. اگر G8 شناسه نگرفته، C-034 هنوز آزاد است |
| D6 | CLI `status` روی VACANT دو خط می‌گوید | ساعت ۲ صبح باید یک جمله باشد | یک خط: `VACANT — free to take` یا `HELD — do NOT start a second organism` |
| D7 | `NatsKvLeaseStore` stub بدون آداپتور | M2 زودرس | تست نکن روی شبکه. docstring بماند؛ vendoring NATS نکن |
| D8 | نام `BeatLease` در هر دو بسته | import اشتباه | در `octopus_v3` کلاس را `HmacBeatLease` نگذار مگر rename بدون شکستن ۱۰ تست — حداقل docstring درشت |

اگر D2 را بستی، تست corrupt فعلی (`token==1`) باید **عوض شود** تا acquire شکست بخورد یا sidecar شماره را نگه دارد. تست کهنه را حذف نکن؛ adapt کن.

---

## کار ۲ — تکمیل M0 (اجباری، بدون کپی به Arm)

اسکریپت: `_ops/migration/scan_windows_fs_m0.py` (یا هم‌ارز). فقط خواندنی روی `F:\backup`. خروجی: `06-EVIDENCE/M0-WINDOWS-FS-SCAN-2026-08-16.md` (+ در صورت نیاز json در tempfile/evidence نه `_ops/state` زنده).

باید پیدا کند:

1. مسیر hardcode `F:\` `F:/` `C:\` و `\\` (حداقل در `*.py` `*.ps1` `*.cmd` `*.md` لایهٔ دست‌چین — `.agentignore` را محترم بدار).
2. فایل‌های هم‌نام با اختلاف فقط حروف (case-fold collision) — روی NTFS سخت است؛ از git `core.ignorecase` + فهرست مسیرهای tracked استفاده کن و محدودیت روش را صادقانه بنویس.
3. CRLF در فایل‌های متنی که باید LF باشند (اسکریپت‌های شل / `.gitattributes`).
4. **نقشهٔ اسرار بدون مقدار:** فقط نام متغیر/فایل (`.env` keys به‌صورت نام، نه value). Arm 2/3/4 هیچ کلید مغز نمی‌خواهند.
5. پیشنهاد فهرست smoke: ۳۰ تست موجود که جمع‌شان <۹۰ث است. `run_all.py` را عوض نکن. یک فایل ` _ops/tests/SMOKE-M0.md` یا آرگومان اسکریپت کافی است. ۷۲۹ تا را اجرا نکن مگر مالک بگوید.

شرط عبور M0 این نشست: گزارش شواهد + اسکریپت + حداقل یک تست که اسکریپت روی یک fixture مصنوعی collision/hardcode را می‌بیند. git tag `pre-migration` نزن مگر مالک بگوید.

---

## کار ۳ — بازنویسی قلاب (اجازهٔ محدود)

`chrono.py` در WORKLOCK نیست. قلاب **additive** پشت فلگ، پیش‌فرض خاموش:

```
# بعد از چک STOP-METABOLIC، قبل از return "beat"
if os.environ.get("OCTOPUS_BEAT_LEASE") in ("1","true","yes","on"):
    from _ops.runtime.beat_lease ...  # مسیر import را با تست ثابت کن؛ sys.path زنده را خراب نکن
    try:
        lease.assert_valid()
    except LeaseFrozen:
        return "pause"
    except LeaseLost:
        return "pause"
```

- `stop` نده — نخ بماند.
- فلگ را روی پروسهٔ زنده set نکن. تست با monkeypatch env + tempfile store.
- `organism.py` را لمس نکن مگر بدون آن تست قلاب ممکن نباشد — ترجیح chrono فقط.
- `on_event`: jsonl در tempfile برای تست؛ مسیر زندهٔ پیش‌فرض اگر نوشتی باید opt-in با env جدا (`OCTOPUS_LEASE_EVENT_LOG`) و پیش‌فرض خاموش. genome ledger / `ledger.jsonl` زنده را ننویس.
- حمل `fencing_token` روی budget/ORGANISM-STATE را **طراحی کن و کارت رأی بگذار**؛ به مسیر پول زنده وصل نکن.

---

## کار ۴ — ابسیدین (اجباری، پایان نشست)

نوت جدید از template. `created_by: agent` + `sources` ≥۲. کلید اختراع نکن.

حداقل:

- شواهد M0 + دیباگ D1–D8 در `06-EVIDENCE/`
- نوت دانش ۵۹ را تازه کن یا ۶۰ اگر ۵۹ را این نشست پر کرده
- Inbox discovery در صورت یافتهٔ نو
- HANDOFF یک پین (wikilink، نه کپی، نه secret)
- DAY-INDEX یک ردیف
- OWNER-PENDING تیک/کارت
- `00-README-START-HERE` · `_Index - Knowledge` · architect PROJECT Active Context/Progress
- validators: frontmatter ~۲۷۸ کهنه را برای سبزکردن درست نکن. لینک curated شکستهٔ نو نساز (۶ کهنه بماند)

YOU ARE HERE در نوت ۵۷ را بعد از M0 به‌روز کن.

---

## کار ۵ — مگاپرامپت بعد (اگر هنوز جا ماند)

اگر M1 یا سیم فلگ روشن ماند، یک مگاپرامپت نو بنویس و این فایل را به‌عنوان شروع باطل کن. وگرنه در گزارش بگو «همین فایل برای دور دوم کافی است با بخش تمام‌شده».

---

## اجازه / ممنوع

| کار | |
|---|---|
| خواندن، تست نام‌یکتا، اسکریپت M0 خواندنی، قلاب chrono فلگ‌خاموش، jsonl opt-in، نوت ابسیدین | بله |
| فلگ زنده، freeze زنده، STOP، TCB، run_all، PEP، پول، ۷بی، vaara pip، NATS واقعی، SMB share، Postgres | نه |
| پوش | فقط «پوش» در همین پنجره |
| ری‌استارت cortex | فقط «ری‌استارت cortex» |

---

## گزارش پایان به مالک

```
شاخه / HEAD / unpushed:
D1–D8: هر کدام pass/fail/won't با یک خط
M0: مسیر اسکریپت + شمار hardcode/case/CRLF (عدد)
قلاب chrono: wired-behind-flag؟ تست؟
آزاد بعدی: C-0XX (grep)
عمداً نشده: cutover / P0-PEP / FPGA خرید / فلگ زنده
ابسیدین: نوت‌ها
```

[BOUNDARY]

نساز: ارگانیسم دوم · lease روی SMB · overwrite MIGRATION-INVENTORY MCP · کامیت داخل G8 · abliteration · سقف بودجهٔ شل‌تر از AU$2/روز.

[END]
