---
type: evidence
status: active
created: 2026-08-12
updated: 2026-08-12
tags: [octopus, discovery, wiring, deep-scan]
related:
  - "[[00 - Inbox/2026-08-12 MEGAPROMPT — Discovery Wire Missing Connections (Junior-Safe)]]"
---

# Deep-Scan — سیم‌های گم/غلط (verified روی دیسک 2026-08-12)

> روش: `effector_registry` + `rg` روی `_ops` + وجود فایل روی دیسک.
> نه حدس. هر ردیف یا VERIFY شد یا STALE اعلام شد.

## Effector snapshot (اجرا شده)

```
DEAD []
DISP ['bcm.weights_bidirectional', 'hebbian.associations',
      'deep_dive.smallest_fix', 'self_model.pathology', 'latent_space.vector']
```

نکته: `smallest_fix` در registry هنوز `display-only` است ولی از ۲۰۲۶-۰۸-۰۷ در
`improve.gather_signals` → proposal propose-only خوانده می‌شود → **registry کهنه**.

---

## صف اولویت برای ایجنت بعدی (یک FINDING در هر دور)

| Pri | id | حکم | شاهد کوتاه | اقدام junior-safe |
|---:|---|---|---|---|
| 1 | DW-01 | **flag-dark / unsched** | `OCTOPUS_WIRE_RUNNER_APPLY=1` در flags؛ **صفر** caller در `.py` تولیدی | فقط گزارش + پیشنهاد `=0` تا ماژول gate پیدا/ساخته شود — فلگ را خودت خاموش نکن مگر رأی |
| 2 | DW-02 | **armed + کد هست + در tick نیست** | `_ops/seed/*` روی دیسک هست؛ فلگ‌های SEED/EVOLUTION/REDTEAM=`1`؛ import تولیدی در organism/wiring **یافت نشد** (فقط tests) | پیدا کن کجا باید schedule شود؛ یک caller fail-soft پشت فلگ موجود پیشنهاد بده — یا بگو «کد یتیم است» |
| 3 | DW-03 | **armed + unsched** | `OCTOPUS_WIRE_KERNEL_BRIDGE_READER=1` + `kernel_bridge_reader.py`؛ هیچ import در organism/wiring | هر N beat `read_status()` fail-soft → digest/report |
| 4 | DW-04 | **context gap — نیمه‌فیکس (senior verify 2026-08-12)** | mirror SK می‌خواند (`mirror_room.py:285`)؛ **collab دیگر SK دارد**: `brain_pulse.py:120-133,176-182` → `_self_context` (probe زنده: doctor.focus در context همکار ✅)؛ `smallest_fix` فعلاً خالی چون پرودوسر `deep_dive` را در SK نمی‌نویسد (همان gap در improve.py:321-330 — fail-soft)؛ **باقی‌مانده: ask_brain صفر SK** (`deep_think` هم SK ندارد) | additive کوچک: SK→ask_brain؛ و «اگر پرودوسر deep_dive نبود، صادق بگو خالی» |
| 5 | DW-05 | **dead-output field** | `math_control/spine.py` می‌نویسد `schedule_period_bias` و effect=`schedule_bias_hint`؛ **هیچ** مصرف‌کنندهٔ period/sleep | یا clamp نرم در arbiter/cardiac پشت soft-cap، یا حذف اثر از snap (با رأی) |
| 6 | DW-06 | **dual-truth UI** | `miniapp_state._brain_consolidation` اول `4d_system/outputs/self_evolved/*`؛ neural فرعی؛ `available` به موتور 4d گره خورده | primary-read `_ops/neural/consolidation.json`؛ 4d را secondary/missing صادق |
| 7 | DW-07 | **registry stale** | effector: smallest_fix=display-only ولی `improve.py:318-433` proposal می‌سازد؛ path `self_model.pathology` با فایل واقعی `state/cortex/self-model.json` جور نیست | فقط به‌روز کردن status/path/evidence در `effector_registry.py` |
| 8 | DW-08 | **display-only (عمدی/نیمه)** | hebbian/bcm weights/latent → cockpit/display؛ تصمیم از `learned_pressure`/pain می‌آید نه فایل خام | به halt وصل نکن؛ اختیاری: association top → improve ranking |
| 9 | DW-09 | **doc drift** | `ARCHITECTURE-LAYERS-2026-07-27` می‌گوید smallest_fix unread / HONEST صفرکد — کد Aug خلافش را دارد | errata کوتاه ۲۰۲۶-۰۸؛ به سند به‌عنوان SoT اعتماد نکن |
| 10 | DW-10 | **partial memory** | `retrieval_router` فقط episodic/procedural؛ insights/conclusions به تصمیم نمی‌روند | ingest insights → episodic (cite-only) مثل self_loop_ingest |

---

## VERIFY / رد ادعاهای اشتباه در اسکن اولیه

| ادعا | نتیجه |
|---|---|
| `_ops/seed/` وجود ندارد | **رد** — فایل‌ها روی دیسک هستند (۸ اوت). مشکل = unsched نه missing |
| `4d conclusions.json` غایب است | **رد کامل نیست** — `Test-Path` روی conclusions True بود؛ با این حال UI هنوز به 4d وابسته است و neural را secondary کرده |
| `smallest_fix` هنوز DEAD کامل | **رد** — propose-wired در improve؛ registry دروغ می‌گوید display-only |
| collab خودآگاهی کامل دارد | **رد** — SK در collab نیست؛ فقط mirror پر است |
| `OCTOPUS_HEBBIAN_LEDGER` unset | **رد** — در flags=`1` و wiring می‌خواندش |

---

## دستورات تأیید (کپی برای دور ۱)

```powershell
cd F:\backup\_ops
python -c "import effector_registry as e; print(e.dead_outputs()); print(e.display_only())"
rg -n "WIRE_RUNNER_APPLY" . -g "*.py" --glob "!_bak/**"
rg -n "kernel_bridge_reader" organism.py wiring.py
rg -n "seed\.(context_assembler|evolution_gate|redteam)" . -g "*.py" --glob "!tests/**" --glob "!_bak/**"
rg -n "self-knowledge-latest|smallest_fix" owner_console/collab_model_adapter.py
rg -n "schedule_period_bias" . -g "*.py" --glob "!_bak/**"
```

---

## دور پیشنهادی ۱ (کم‌ریسک‌ترین اثرِ مالک‌دیده)

**DW-04 (به‌روز):** SK در همکار از طریق `brain_pulse` وصل است (فیکسِ امروز). کارِ باقی = **ask_brain** (تزریق کوچک focus از SK) — یا برو سراغ DW-07 (ساده‌ترین: refresh خالص registry).

- فایل‌ها: `collab_model_adapter.py` (± `ask_brain.py`)
- اثر بیرونی: ۰
- تست: `test_chatbox_unified` یا تست نو یکتا
- بعد: registry کوچک برای DW-07

**دور ۲:** DW-03 kernel_bridge schedule (report-only).  
**دور ۳:** DW-06 miniapp consolidation truth.  
**قبل از دست‌زدن به flags:** DW-01/02 فقط گزارش + رأی مالک.
