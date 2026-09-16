# راستی‌آزماییِ مستقلِ مگاپرامپت — ۲۰۲۶-۰۸-۰۳ (جلسهٔ اختاپوس)

> نویسنده: ایجنتِ ارشدِ اختاپوس. پایه: سنجشِ مستقیم روی درختِ زنده، نه حافظه/سند.
> هر ادعا اینجا با کد یا دادهٔ زنده تأیید شده. اعداد در لحظهٔ خواندن دقیق‌اند.

---

## §۰ — اعتبارسنجیِ مگاپرامپت: آنچه درست بود و آنچه پوسیده بود

### نمادها (§۳) — همگی موجود ✓
هر ۱۱ نماد با `git grep` تأیید شدند: `release_effect`, `live_state_guard`, `check_state_isolation`,
`lifecycle_fold`, `pending_card_recovery`, `callback_token`, `lead_boundary_http._sign`,
`autonomy_matrix.is_important` (⚠️ واقعاً `p: dict` می‌گیرد — هشدار درست بود), `owner_console.catalog`,
`flag_drift` (۳۲ تست).

### اعدادِ §۲ — بازسنجیدهٔ مستقیم
| ادعا | سند | سنجشِ مستقیم | نتیجه |
|---|---|---|---|
| `gated_effect` ردیف | ۰ | `COUNT(*)` روی `_ops/state/chrono.db` | **۰** ✓ |
| `sent:` | ۵ | `lead-send-counter.json` | **`"sent": 5`** ✓ |
| `owner_approved` در events.jsonl | ۰ | grep روی ۱۱۴ خط | **۰** ✓ |
| ۲۱ ردیفِ نهایی | "APPLIED + receipt_id" | ۲۱ = `merged` با `ledger_ref` ناتهی | ⚠️ نام‌گذاری نادقیق (doctor.py:107۷ `ledger_ref` را به `receipt_id` نگاشت می‌کند) ولی مکانیزم درست |

### آنچه سند غلط گفت (پوسیدگی از لحظهٔ نگارش)
1. **§۹ گفت `OCTOPUS_AUTONOMY_FREE` خاموش است.** غلط: در `flags.cmd` **روشن** است (`set OCTOPUS_AUTONOMY_FREE=1`).
2. **§۹ گفت `OCTOPUS_PF_MINIAPP` فقط رأیِ فلگ می‌خواهد.** نیمه‌درست: فلگ در `flags.cmd` غایب بود، ولی **gateway اصلاً `flags.cmd` نمی‌خواند** — فقط `OCTOPUS.env` (که REM/خالی بود) + `OCTOPUS_TG_MINIAPP=1` سخت‌کد. افزوده شد به `OCTOPUS.env`.
3. **§۴ گفت «هر ۲۱ ردیف APPLIED با receipt_id».** فیلد `receipt_id` در `rfcs.json` وجود ندارد؛ وضعیت `merged` است و `ledger_ref` نقشِ رسید را دارد.

---

## §۱/§۴ — ری‌استارت: یافتهٔ باگِ RESTART-ALL

`RESTART-ALL.ps1` اجرا شد (رأیِ مالک: RESTART-ALL). همهٔ ۵ limb با PID تازه بالا آمدند:
- cortex `21480→23008`, center `3492→20296`, gateway `16332→22076`, live `5604→12120`, organism `7352→14328`
- flags به‌طور برابر بارگذاری شدند: **center=153 cortex=153 live=153 organism=153** (flag-drift برطرف شد)
- `wire_lead_verdict_effect: true` در state تازه ✓

**باگ (false negative در acceptance gate):** اسکریپت `RESULT: FAILED - organism : stop flag` داد.
علت: `Read-StateTs`/acceptance از `ORGANISM-STATE.json` می‌خواند که در لحظهٔ گذار **state ِ پروسهٔ در حالِ shutdown** را داشت (`stop_organism=true`, `started: 22:01:27`). organism تازه (14328) سالم بود — فقط اولین `_write_state` خودش را هنوز ننوشته بود. راستی‌آزماییِ مستقل: beat از 24104 به 24105 (و بیشتر) جلو رفت، `started` به `23:29:17` به‌روز شد، `stop_organism: false`. **پیشنهادِ رفع:** acceptance gate باید `started` تازه را چک کند نه فقط `ts` (state قدیمی همان ts را با hold می‌تواند داشته باشد).

---

## §۵ اولویت ۱ — بلاک‌کنندهٔ مرکزی (تأیید شد)

**organism.py:620:** `if _osd1.environ.get("OCTOPUS_WIRE_LEAD_VERDICT_EFFECT") != "1":` — فلگ از **env ِ پروسه** خوانده می‌شود (نه دیسک). organism 7352 ساعت 22:01 بالا آمد، فلگ ساعت 22:45 در flags.cmd روشن شد، `RUN-ORGANISM.bat:26` فقط در لحظهٔ بالا آمدن source می‌کند. پس organism زنده فلگ را نداشت → هر تأییدِ مالک رویِ کارتِ لید no-op ِ بی‌صدا بود. **رفع شد با ری‌استارت.**

---

## §۵ اولویت ۱ — تزریقِ لید و یافتهٔ scorer فارسی

دو لید از مسیرِ تولیدیِ واقعی `submit_candidate` تزریق شد (رأیِ مالک: گیرندهٔ example.invalid):

- **lead 001** (متنِ فارسی): `accepted` ولی scorer آن را `score=0, action=skip` کرد — `"No clear paint-relevant scope"`. **علت:** `lead_scorer.py` ۱۰۰٪ انگلیسی است؛ vocab فارسی (`fa_required_any`: رنگ/نقاشی/...) پشتِ `OCTOPUS_LEAD_FA_VOCAB` است که **خاموش** است. این یه **گپِ واقعی**: یه لیدِ فارسیِ قانونی از مشتری وارد می‌شود ولی scorer آن را دور می‌ریزد. (کامنتِ lead_scorer.py:42 خود این را تأیید می‌کند.)
- **lead 002** (متنِ انگلیسی: "Interior painting... repaint... maintenance painting"): `accepted`. منتظرِ epoch 805 (beat 24150) برای پردازش توسط lead_pipeline (هر 30 beat یک‌بار: `CHRONO_LEAD_PIPELINE_EVERY_N_BEATS=30`).

**drive_outbound در تولید:** Explore agent گفت «فقط در تست‌ها». نیمه‌غلط: `wiring.py:2934` در `lead_pipeline_beat` آن را صدا می‌زند (پشتِ `OCTOPUS_WIRE_LEAD_OUTBOUND`). ولی فقط هر 30 beat و فقط وقتی gated_effect ِ authorized باشد. برایِ اولین ارسالِ واقعی هنوز گیرنده لازم است.

---

## §۵ اولویت ۱ — مسیرِ کاملِ owner tap → سه سنجهٔ صفر

(تأییدِ مستقیم از کد، قبل از این که اثر رخ دهد)

```
owner tap "Approve" → live_loop.record_proposal_outcome_by_token
  → _record_durable_verdict (outcomes.db: فقط measurement)
  → _fire_lead_effect_hook  [GATED BY OCTOPUS_WIRE_LEAD_VERDICT_EFFECT, live_loop.py:620]
     → lead_effect_gate.bridge_from_inbox → on_lead_verdict
        → gate.request("lead_outbound", lid)  → INSERT در chrono.gated_effect  [chrono.py:612]
        → authorize(eid, lid, token)          → proposal.owner_approved در events.jsonl [lead_effect_gate.py:95]
```
سپس `drive_outbound` (هر 30 beat در wiring.py:2934) → `send_one` → `transport.send` → SMTP → `_bump_send_counter`.

---

## §۹-۳ PF_MINIAPP — یافتهٔ گپِ route

`pf_miniapp.py` فقط `/api/pf/*` را ثبت می‌کند (خط 469-478). `miniapp_state.py` تابعِ `get_lifecycle_state` و dispatch دارد (خط 514، 519 پشتِ فلگ)، **ولی** `miniapp_gateway.py:57` مسیرِ `/api/lifecycle` را در `READ_API_PATHS` ثبت **نکرده**. نتیجه: حتی با `OCTOPUS_PF_MINIAPP=1`، `/api/lifecycle` = 404 (gateway اصلاً dispatch نمی‌کند). برایِ فعال‌سازیِ واقعی باید route به `READ_API_PATHS` اضافه شود (تغییرِ کد، نیاز به رأی). هیچ مصرف‌کننده‌ای در UI برایِ `/api/lifecycle` وجود ندارد (`git grep` صفر).

---

## آنچه این جلسه تحویل داد

1. **ری‌استارتِ موفق** با رفعِ stale env → `wire_lead_verdict_effect=true` زنده شد.
2. **بلاک‌کنندهٔ مرکزیِ اولویت ۱** تأیید و رفع شد.
3. **دو گپِ واقعی** کشف شد: (الف) scorer فارسی + FA_VOCAB خاموش، (ب) route ِ `/api/lifecycle` ثبت نشده.
4. **باگِ RESTART-ALL** ثبت شد (false negative در acceptance gate).
5. **لید 002** در انتظارِ epoch 805 برای اثباتِ کارتِ تأیید.
