# TERRITORY-REPORT — OCTOPUS-DOCTOR

findings: **8** · classes: DEBT_HIDDEN 4 · DOC_RUNTIME_DISCREPANCY 2 · SEASON_LEFTOVER 1 · RULING_UNEXECUTED 1

## top findings (rank order)

- **[DOC-4] r7.0 SEASON_LEFTOVER** SCAN-2026-09-15: confirmed_revenue = 0 🔴 — the whole organism shows zero confirmed revenue while 03-Projects docs claim 
  - `F:/backup/OCTOPUS-DOCTOR/50-اسکن‌ها/SCAN-2026-09-15.md` · `line 24: | `confirmed_revenue` | 0 | برون‌زاد | 🔴 | ✅ |`
- **[DOC-2] r6.8 DOC_RUNTIME_DISCREPANCY** F-AUTO-BRAKE (scan 2026-09-09): heart braked again — effective_period_s=900 with brake:cardiac vs biological rhythm 42.4
  - `F:/backup/OCTOPUS-DOCTOR/60-یافته‌ها/F-AUTO-BRAKE-قلب-ترمز-خورده.md` · `line 9: `effective_period_s=900.0` با راننده `brake:cardiac` در حالی که ریتمِ زیستی `42.42640687119285``
- **[DOC-1] r5.0 DEBT_HIDDEN** F-AUTO-FROZEN-CONTROL-PLANE: octopus_state self_awareness stuck 'green' since 2026-07-18 with 0 writers/0 readers — stil
  - `F:/backup/OCTOPUS-DOCTOR/60-یافته‌ها/F-AUTO-FROZEN-CONTROL-PLANE-سبزی-که-هرگز-قرمز-نمی‌شود.md` · `line 9: مقدارِ `green` را از `2026-07-18T12:04:31+10:00` نگه داشته و **هیچ کدی** آن را نه می‌نویسد و نه می‌خوا`
- **[DOC-3] r4.8 DOC_RUNTIME_DISCREPANCY** int('متوسط') crash signature ×346: F-05 declared it fixed+closed on 2026-07-29, yet the same signature is a top 🔴 alert 
  - `F:/backup/OCTOPUS-DOCTOR/60-یافته‌ها/F-AUTO-ALERT-18-هشدارِ-تکراری-×346.md` · `line 9: ⚠️ wiring: doctor_digest_beat خطا: ValueError: invalid literal for int()… یک امضا، **346** بار`
- **[DOC-5] r4.8 DEBT_HIDDEN** F-02 self-referential reward (🔴, never revised): outcomes.jsonl 0/230 rows have an outcome field; 83 closures on only 4 
  - `F:/backup/OCTOPUS-DOCTOR/60-یافته‌ها/F-02-پاداشِ-خودارجاع.md` · `line 9: ۰ از ۲۳۰ سطر فیلدِ نتیجه دارد. ۸۳ بستار روی **۴ کلیدِ متمایز**… تنها کلیدِ متحرک `total_discoveries``
- **[DOC-6] r4.8 DEBT_HIDDEN** F-06 zero-cost structural hole (🔴 open): subscription:max forces est_worst_case()=0, so EFE's Cost term is silently drop
  - `F:/backup/OCTOPUS-DOCTOR/60-یافته‌ها/F-06-هزینهٔ-صفر.md` · `line 9: `cost_usd` در پلنِ فلت **ساختاراً صفر** است… اگر EFE را با دلار ببندی، ترمِ Cost بی‌صدا حذف می‌شود`
- **[DOC-7] r4.8 RULING_UNEXECUTED** F-08: test suite not hermetic — 56 persistently red files on a clean HEAD worktree keep the day --live gate closed; doct
  - `F:/backup/OCTOPUS-DOCTOR/60-یافته‌ها/F-08-سوئیت-غیرهرمتیک-گیتِ-زنده.md` · `line 13: **۵۶ فایل قرمز** می‌دهد… یعنی مرحلهٔ **پایه** رد می‌شود… پچِ `doctor_pulse.py` هرگز آزموده نشد — و اح`
- **[DOC-9] r4.8 DEBT_HIDDEN** Doctor findings vault ballooned to 222 files — ~200 auto-alert findings (F-AUTO-ALERT-*) with repetition counts up to ×3
  - `F:/backup/OCTOPUS-DOCTOR/60-یافته‌ها` · `dir listing: 222 files; F-AUTO-ALERT-998…×346.md … F-AUTO-ALERT-934-هشدارِ-تکراری-×85.md`

## coverage

- inventory files_total (md/json/txt ≤2MB): 360
- read: ~22/335 (≈195 F-AUTO alerts enumerated+sampled)
- method: findings + today's scan deep-read; alert pile enumerated
- excluded: per-alert bodies sampled, not individually read
