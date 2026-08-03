# 00 — REALITY BASELINE · مأموریت یکپارچه‌سازی ۲۰۲۶-۰۷-۳۱

> ادامهٔ `octopus-unification-2026-07-30` — نه تکرارش. snapshot ِ مگاپرامپت
> (§۲) روی درخت فعلی re-probe شد؛ چند ادعای آن **کهنه** بود و این‌جا با شاهد
> تصحیح می‌شود.

## ۱. Git inventory (پیش از هر ویرایش)

```text
worktree           F:\backup\.claude\worktrees\vigilant-grothendieck-8e8250
branch             claude/octopus-code-integration-175ecb
HEAD ِ آغاز جلسه    9f14901  ==  master  (clean)
درخت زنده          F:\backup  →  branch fix/tg-p2-2026-07-30 @ ce35f61 (dirty)
نسبت               master ⊂ tg-p2  (merge-base = master tip؛ tg-p2 = +183 کامیت)
اقدام ۱            git merge --ff-only fix/tg-p2-2026-07-30  →  HEAD = ce35f61
                   (برگشت: git reset --keep 9f14901 — فقط اشاره‌گرِ شاخهٔ خودم)
اقدام ۲            کامیت‌های نجات 2ac7e9b + f2fceee (جدول §۴)
```

چرا ff: مأموریت روی «نسخهٔ واقعی» است و نسخهٔ واقعیِ در حال اجرا tg-p2 است؛
ماندن روی master یعنی ساختن duplicate از چیزهایی که آن‌جا از قبل هست
(پل اقدام `02a2af5`، مامور `0025064`، قرارداد تلگرام `54eaa09`، بازنشستگی
os_v1 `c104f61`) — دقیقاً چیزی که §۱۹ مگاپرامپت ممنوع کرده.

## ۲. تصحیح snapshot ِ مگاپرامپت (§۲.۲) — با شاهد

| ادعای snapshot | واقعیت روی درخت زنده (۲۰۲۶-۰۷-۳۱ صبح) |
|---|---|
| self-model کهنه (~۱۶۶۲ دقیقه) | **تازه است**: `state/cortex/self-model.json` سن ۵.۹ دقیقه، ۲۱۴KB |
| ORGANISM-STATE مشکوک | **تازه است**: سن ۰.۱ دقیقه — organism زنده می‌نویسد |
| Action Bridge = IMPLEMENTED_NOT_INTEGRATED | **مسلح و LOADED**: `OCTOPUS_WIRE_ACTION_BRIDGE=1` (flags.cmd:761، شاهد `13-ARMED-RUNTIME-EVIDENCE.md`)؛ صداکننده `test_cycle.py:290` |
| Unified Control = NOT_LIVE | دو importer واقعی: `goal_action_bridge.py:138` و `owner_console/status.py:14` (مسیر دوم بی‌فلگ در hot-path تلگرام) |
| Owner Console = IMPLEMENTED_NOT_WIRED | **وصل و بی‌فلگ**: `center.py:1384` و `center.py:2915` — ولی کل بسته تا امروز **بی‌گیت** بود (§۴) |
| World Discovery = IMPLEMENTED_NOT_INTEGRATED | همچنان درست: صفر importer ِ ران‌تایم؛ ۷ فایل تستش هم در `run_all.py` ثبت نیستند |
| SGC حلقهٔ ارزیابی بدون عمل | کهنه: زنجیرهٔ prereg→mission→A0→receipt→verdict→memory از `02a2af5` وصل است و دو اجرای واقعی دارد (دو ردیف `missions.jsonl`) |

## ۳. وضعیت اجزا (محورهای flag/reachability/side-effect)

| جزء | وضعیت | شاهد |
|---|---|---|
| goal_action_bridge | LOADED — دو اجرای واقعی A3→needs_approval | `state/test_cycle/missions.jsonl` ۲ ردیف؛ executor صدا نخورد (رسید=۰) |
| unified_control.snapshot (freshness) | LIVE در مسیر read-only | `snapshot.py:50-71` SLA-محور؛ `goal_action_bridge.py:65-80` fail-closed به MISSING |
| mission_contract | **CONFLICTED** | HEAD نسخهٔ v1؛ درخت زنده نسخهٔ v2 ِ **کامیت‌نشده** (tenant/project/task/scope + critical)؛ `pipeline.py:39` ِ tracked به v2 وابسته → روی checkout تمیز `TypeError` (۳ قرمز baseline) |
| owner_console | LOADED ولی تا امروز UNTRACKED | این جلسه rescue شد (§۴) |
| LockedJson (opslib:234) | مسیر نوشتن شکننده | `write()` بدون retry/رسیدِ شکست؛ WinError5 ⇒ «tmp تازه، اصلی کهنه» (اپیزود CONFLICTED ِ ۰۷-۳۰) |
| حافظه در تصمیم | تقریباً write-only | تنها read-path: `outcomes/lead_outcome_recorder.py:96-113`؛ planner ِ cortex صفر خواندن؛ `consolidate.recent_semantic` صفر صداکنندهٔ تولیدی |
| mission → کارت مالک | **قطع** | دو mission ِ needs_approval روی دیسک، صفر کارت تلگرام (VQ-MISSION-CARD-001) |
| تست‌های world_discovery | ORPHAN | ۷ فایل + `integrations/world_discovery_action/tests/test_boundary.py` — هیچ‌کدام در TESTS ِ `run_all.py` |
| درخت زنده | DIRTY در مقیاس | ~۱۲۰ فایل tracked ِ تغییرکرده در `_ops` (+۲۶٬۴۸۰ خط) کامیت‌نشده — کار جلسه‌های موازی؛ این جلسه فقط `mission_contract.py` (وابستگیِ HEAD) را می‌آورد |

## ۴. نجات کد زندهٔ بی‌گیت (کامیت‌های 2ac7e9b + f2fceee — ۶۳ فایل)

مسیر داغ ِ tracked به کدی وابسته بود که در هیچ شاخه‌ای نبود:

- `center.py:1384` → **بستهٔ owner_console** (۸ فایل + ۴ تست) — try/except آن را
  می‌بلعید؛ یک checkout تمیز = مرگ بی‌صدای مامور.
- `wiring.py:77` → `epoch_guard.py`.
- `run_all.py` ِ tracked ‏۴۳ فایل تست را نام می‌برد که فقط روی دیسک زنده بودند
  ⇒ ۴۳ قرمز ساختگی روی هر clone. همهٔ ۴۳ + بستارِ importشان
  (`context_bundle`، `control_contracts`، `epoch_guard`، `output_critic`،
  `doctor/self_accuracy`، `heart/budget_judge`، `tests/gate_report`) آورده شد.
- کپی بایت‌به‌بایت از درخت زنده؛ صفر ویرایش؛ اسکن secret پاک؛ درخت زنده
  دست‌نخورده (copy، نه move).

## ۵. قواعد ایزوله‌سازی اجرا (این جلسه)

```text
ORG_ROOT / REAL_VAULT / OCTOPUS_VAULT_ROOT  = worktree
OCTOPUS_STATE_DIR / OPS_STATE_ROOT          = worktree\_ops\state
OCTOPUS_STATE_ROOT                          = worktree\_octopus\state
GENOME_DIR                                  = worktree\07 - Knowledge\genome-system   ← opslib.py:43 به F:\backup پین است و ORG_ROOT redirectش نمی‌کند
PYTHONIOENCODING                            = utf-8
```

سنجهٔ نشت پس از هر ران: mtime ِ `F:\backup\_ops\state`، `_octopus\state`،
`genome-system\ledger` + غیاب STOP/HALT ِ تازه.
