# CHRONO-MIGRATION-ROLLBACK (C)

## اصل
migration فقط روی fixture/copy اجرا می‌شود؛ chrono.db زنده هرگز. پس rollback = دور انداختنِ fixture.

## اثباتِ rollback روی copy (fixture-proven)
prototype یک copy از DBِ pre-migration نگه می‌دارد و تأیید می‌کند:
- copy شکلِ v1 را حفظ می‌کند (بدونِ ستون‌های v2، `user_version=0`).
- یعنی نقطهٔ بازگشتِ byte-identical پیش از هر migration موجود است.

## رویهٔ rollback (وقتی به candidate پورت شد، هنوز روی fixture)
1. پیش از migration: `shutil.copy2(chrono.db, chrono.db.pre-v2.bak)` (فقط fixture).
2. اگر migration/تست شکست خورد: فایلِ migrate‌شده را دور بینداز، `.pre-v2.bak` را بازگردان.
3. چون table-recreate اتمیک زیرِ یک transaction/executescript است، شکستِ نیمه‌کاره
   به حالتِ before برمی‌گردد (خودِ SQLite rollback می‌کند).
4. هیچ‌گاه روی chrono.db زنده — پس rollbackِ live لازم نیست (owner boundary).

## گیت
migration فقط پس از owner-approval و فقط با یک نقطهٔ backupِ اثبات‌شده به live نزدیک می‌شود
(خارج از scopeِ فاز صفر؛ activation ممنوع).
