---
type: evidence-note
created: 2026-08-15
updated: 2026-08-15
mission: DEBT-SWEEP — MEGAPROMPT-DEBT-SWEEP-2026-08-16 v1.2
rule: هر عدد با فرمان/فایل منبع‌دار · سطح A/B/C · append-only برای بخش‌های شواهد
---

# DEBT-SWEEP 2026-08-16 — دفتر شواهد

> فایل در STEP 2 مگاپرامپت الزامی بود و تا این نشست خالی/غایب بود. نخستین بلوکِ شواهد: §R3 (C-014).

## §R3 — C-014 containment (Observatory dual-task)

### 2026-08-15 23:47:25 +10:00 — verify after old-task disable

**حکم:** C-014 **containment اثبات‌شده** (سطح A). شلیک `:36` پس از Disable نیامد.

**پیش‌فرض مالک:** تسک ویندوزی قدیمی `OCTOPUS-Observatory` امروز ~22:46 local غیرفعال شد؛ شلیک بعدی‌اش می‌بایست `23:36:27` local = `13:36:27` UTC باشد. این verify بعد از `23:41` local اجرا شد.

**۱) تسک**

```
Get-ScheduledTask -TaskName 'OCTOPUS-Observatory' | Format-List TaskName, State, TaskPath
```

نتیجه (سطح A، 2026-08-15 23:47 +10):

```
TaskName : OCTOPUS-Observatory
State    : Disabled
TaskPath : \
```

`(Get-ScheduledTask -TaskName 'OCTOPUS-Observatory').State` → `Disabled`

تسک زندهٔ باقی‌مانده (دست نخورده): `OCTOPUS Observatory Hourly` همچنان Ready/Enabled است — خاموش نشد.

**۲) evidence_chain (mode=ro)**

```
py -c "import sqlite3; con=sqlite3.connect(r'file:C:/Users/Armin/Desktop/OCTOPUS-NBB-CP-WORKING/nbb-control-plane/_ops/observatory/data/evidence.db?mode=ro', uri=True); print(con.execute('SELECT seq, occurred_at FROM evidence_chain ORDER BY seq DESC LIMIT 4').fetchall()); con.close()"
```

چهار ردیفِ آخر:

| seq | occurred_at (UTC) | local +10 | سری |
|-----|-------------------|-----------|-----|
| 15 | 2026-08-15T13:06:05+00:00 | 23:06 | Hourly `:06` |
| 14 | 2026-08-15T12:36:32+00:00 | 22:36 | قدیمی `:36` — **قبل از** Disable ~22:46 |
| 13 | 2026-08-15T12:06:04+00:00 | 22:06 | Hourly `:06` |
| 12 | 2026-08-15T11:36:31+00:00 | 21:36 | قدیمی `:36` |

جدیدترین ردیف = seq 15 = سری `:06`. هیچ ردیف `2026-08-15T13:36*` وجود ندارد.

اسکن کامل همان DB: `n=16` ردیف (seq 0..15). `HITS_13:36 = []`. آخرین `:36` همان seq 14 در 12:36:32Z است.

**۳) قضاوت**

جدیدترین ردیف‌ها پس از پنجرهٔ 23:36 فقط سری `:06` را نشان می‌دهند؛ ردیف `13:36xx` UTC غایب است ⇒ **C-014 containment اثبات‌شده**.

YAML در `01-TRUTH/CONTRADICTIONS.md` هنوز `open — owner_action` است (قاعده: فقط رأی مالک status را می‌بندد). این بلوک اثبات عملیاتی است، نه بستن دفتر.

هیچ تسکی در این verify تغییر داده نشد.
