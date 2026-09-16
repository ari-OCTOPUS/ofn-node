---
type: report
schema: octopus-heart-g4-report/1
gate: G4 — authority removal only
status: PROMOTED_LIVE
created: 2026-08-25
promoted: 2026-08-25 (runtime witness: beats 49093/49095)
owner_directive: Heart v2 gate plan (approved 2026-08-24) — Gate 0 + G4 only
---

# G4 — سلب اختیار رأی shadow از نبض زنده

## چه شد

شکاف زندهٔ اختیار بسته شد **فقط با سلب اختیار** — هیچ قابلیت، فلگ یا فعال‌سازی تازه‌ای اضافه نشد.

قبل: `_control_vote` رکورد `heart-shadow-latest.json` را می‌خواند (`mode=shadow`، `production_wire.open=false`) و period آن (۲۴۴s) به‌عنوان رأی کامل وارد اجماع زندهٔ arbiter می‌شد که نبض ~96s ارگانیسم را می‌راند — با اینکه تولیدکنندهٔ خودش آن رکورد را غیرمعتبر اعلام کرده بود.

بعد: رأی control_law همچنان **مشاهده** می‌شود (period و telemetry و دلایل حفظ می‌شوند) اما `present=false`، `eligible_for_live=false`، `authority=SHADOW_ONLY` است و از اجماع/ترمز/رنگ حذف می‌شود.

## تغییرات (۵ فایل، همه در worktree ایزوله)

1. `_ops/heart/pulse_arbiter.py` — هستهٔ G4:
   - `_control_authority()`: در این گیت **هرگز** authority نمی‌دهد (حتی اگر رکورد shadow خودش `production_wire.open=true` ادعا کند — آن فایل مالک production wire نیست).
   - `_authority_vote()`: مشاهده بدون اختیار؛ `observed_period_s` حفظ می‌شود.
   - `arbitrate()`: defense-in-depth — رأی بدون `eligible_for_live=True` هرگز وارد محاسبه نمی‌شود (fail-closed، نه fail-open).
   - **Anchor ثابت non-acceleration**: اولین beat پس از G4 مقدار live فعلی (مثلاً 96.32s) را به `authority_floor_s` مهاجرت می‌دهد؛ beatهای بعدی همان anchor را بازاستفاده می‌کنند — کندی موقت anchor را بالا نمی‌برد (ضد-ratchet) و حذف رأی shadow هرگز تسریع نمی‌آورد. جابه‌جایی anchor فقط در Gate 1 (HeartStore).
   - نبود baseline معتبر → wire بسته (`NO_VALID_BASELINE`)؛ تسریع ممکن نیست.
   - commit اتمیک: read→apply→write زیر یک `LockedJson`، با recheck کامل گیت‌های مالک و STOP/HALT داخل قفل (بستن TOCTOU).
   - شکست نوشتن primary → `written=false`, `wire_open=false`, رکورد قبلی سالم می‌ماند. شکست sink ثانویه → LATEST commit باقی می‌ماند (`sink_written=false` فقط گزارش).
   - `effective_period_if_open()` هم HALT را رعایت می‌کند (بستن bypass دوم).
2. `_ops/tests/test_pulse_arbiter_authority.py` (جدید) — ۲۷ تست: مشاهده‌پذیری بدون اختیار، self-declared wire، malformed/NaN/stale، ترمز shadow بی‌اثر، ترمز معتبر برنده، defense-in-depth، anchor ثابت، ضد-ratchet، بسته‌موقتِ wire، شکست primary/secondary، STOP/HALT، recheck گیت در commit، precision fail-closed.
3. `_ops/tests/test_pulse_arbiter_wire_readiness.py` — قرارداد (ج) از «سه رأی live» به قرارداد درست «دو رأی معتبر + anchor ثابت» اصلاح شد.
4. `_ops/tests/test_bounded_read.py` — رفع fixture که write خودش را هم stall می‌کرد (root cause کامل: `BOUNDED-READ-ROOT-CAUSE.md`). production دست‌نخورده.
5. `_ops/tests/run_all.py` — ثبت `test_pulse_arbiter_authority.py` (فقط ثبت؛ قواعد ضعیف نشدند).

## اعتبارسنجی

| مورد | نتیجه |
|---|---|
| compile همهٔ فایل‌های تغییرکرده | PASS |
| ۲۷+۲۳+۵+۱۰+۱۹+۱۵+۱۴+۱۷+۱۲ تست مرتبط | همه سبز |
| `run_all.py --only` (همهٔ سوییت‌های تغییرکرده) | exit 0 |
| runner کامل | سوییت‌های G4 همه سبز؛ ~۶۶ شکست نامرتبط (هیچ‌کدام به فایل‌های تغییرکرده ارجاع ندارند؛ سازگار با baseline شناخته‌شدهٔ checkout تازه) |
| phantom_guards | ۷/۹ با patch، ۷/۹ روی HEAD پاک — یکسان |
| replay آفلاین روی baseline واقعی زنده | PASS: رأی ۲۴۴.4s دیده‌شده/غیراهل؛ candidate 55.17s؛ applied 96.32s = anchor؛ بدون تسریع |
| بازبینی مستقل | بدون blocker؛ ۴ مورد کم‌خطر که ۲ موردش همان‌جا harden شد |
| Stop Gate فایل‌سیستم | PASS (NTFS محلی، بدون sync agent) |
| hash هدف زنده | دو بار تأیید: مطابق manifest |

## وضعیت promotion: متوقف

طبق طرح مصوب، preflight سلامت ledger لازم است. نتیجه:

```text
verify()      = PASS (زنجیره سالم، 14656 رکورد، صفر خراب)
verify_tip()  = FAIL (file=14656 tip=14294؛ اما tip_hash == hash رکورد آخر)
```

تفسیر اولیه: شمارندهٔ sidecar غیرقابل‌اعتماد، نه truncation. forensic بعدی ریشه را قطعی کرد:

**ریشهٔ forensic (تأیید دو مسیر مستقل):** ۳۶۲ شکست خاموشِ نوشتن sidecar در پنجرهٔ 2026-08-16..20 — `os.replace` زیر قفل فایل ویندوز (AV/indexer)، بلعیده با `except Exception: pass` — که از آن پس با منطق `prev_n+1` برای همیشه حفظ شد. زنجیره و hash همیشه سالم بودند؛ صفر truncation. همان بازبینی یک باگ دوم هم یافت: `seal_tip` به‌دلیل همان `prev_n+1` عملاً قادر به ترمیم count نبود (تست بازتولیدکننده اضافه شد).

رفع: `seal_tip` اصلاح شد (شمارش صریح واقعی؛ رفتار append بایت‌به‌بایت دست‌نخورده)، روی کپی temp از دادهٔ زنده تمرین شد (mismatch→ok، بعد از append هم ok)، سپس **یک بار روی زنده** با رسید کامل اجرا شد: `GENOME-TIP-RESEAL-RECEIPT.json` (14299→14661، همان head hash، بدون لمس تاریخ).

## Promotion (اجرا شد)

پس از سبزشدن گیت ledger: پچ ۷-فایلی روی درخت زنده اعمال، compile و سوییت‌های کلیدی روی درخت زنده سبز، ری‌استارت کنترل‌شده (marker `RESTART-REQUESTED` → خروج تمیز `exited=RESTART` در beat 49089 → relaunch؛ STOP مالک هرگز لمس نشد)، و مشاهدهٔ دو beat:

| beat | n_present | driver | candidate | effective | floor_source | control vote |
|---|---|---|---|---|---|---|
| 49093 | ۲ | authority-hold | 55.03s | **96.44s** | LEGACY_LIVE_BASELINE (مهاجرت anchor) | SHADOW_ONLY، observed=253.51s |
| 49095 | ۲ | authority-hold | 55.01s | **96.44s** | G4_FIXED_ANCHOR (ضد-ratchet) | — |

ناوردی‌های زنده: رأی shadow قابل‌مشاهده/غیرمجاز؛ حذف رأی کندِ shadow هیچ تسریعی نیاورد؛ anchor بین beat ثابت ماند؛ beat جلو رفت؛ بدون halt؛ ژنوم پس از ۵ append همچنان `verify∧verify_tip` سبز (14666=14666).

## بازگشت (rollback)

`git checkout --` همان ۷ فایل + حذف `test_pulse_arbiter_authority.py` + ری‌استارت با marker. (sidecar نیاز به بازگشت ندارد — شمارش واقعی را حمل می‌کند.)
