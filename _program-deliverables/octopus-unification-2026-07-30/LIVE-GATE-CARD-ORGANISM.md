# LIVE-GATE-CARD — ORGANISM · مسلح‌کردنِ پلِ اقدام

**Decision ID:** `VQ-ACTION-BRIDGE-ARM-001`
**تاریخ ساخت:** ۲۰۲۶-۰۷-۳۰ · **وضعیت:** ⏳ منتظرِ رأیِ مالک

## اثرِ دقیق

دو چیز، و فقط همین دو:

```text
۱) یک خط در F:\backup\_ops\OCTOPUS-flags.cmd:
      set OCTOPUS_WIRE_ACTION_BRIDGE=1
۲) ری‌استارتِ نرمِ organism.py (فقط PID ِ خودش؛ مسیرِ RUNBOOK)
```

## فایل‌ها/پروسه‌ها

| مورد | جزئیات |
|---|---|
| فایل | `_ops/OCTOPUS-flags.cmd` (gitignored — ردش فقط همین کارت) |
| پروسه | `python -X utf8 organism.py` — امروز PID 24760، بوتِ ۱۹:۱۸:۲۸ |
| لانچر | `RUN-ORGANISM.bat` (cmd PID 2936) — حلقهٔ خود-راه‌انداز، پس کشتنِ فرزند کافی است |
| کدِ فعال‌شده | `_ops/goal_action_bridge.py` + دو درز در `_ops/test_cycle.py` |

## چرا لازم است

زنجیرهٔ SGC-14 امروز به «متنِ روش» تمام می‌شود؛ هیچ‌کس آن را اجرا نمی‌کند و
ارزیاب درست `FAIL` می‌دهد. با این فلگ، هر چرخه یک اقدامِ **A0 (فقط مشاهده)**
از `action_bridge` می‌گیرد و رسیدِ واقعی می‌سازد — یعنی حکمِ ارزیاب برای اولین
بار روی «چیزی که واقعاً انجام شد» می‌نشیند، نه روی یک رشته.

## دامنهٔ انفجار

```text
حداکثر ۲ اقدام در روز (کادنسِ اسلاتِ SGC: OCTOPUS_TEST_CYCLE_SLOTS=2)
هر اقدام: A0 = خواندنِ یک فایلِ متریک داخلِ _ops. صفر نوشتن جز:
   · state/test_cycle/missions.jsonl        (append، یک ردیف)
   · state/test_cycle/action_receipts/*     (یک رسید)
   · state/test_cycle/action-ledger.jsonl   (append)
صفر شبکه · صفر ارسال · صفر خرج · صفر تماسِ LLM · صفر merge/deploy
A3/A4/A5 ساختاراً غیرقابلِ‌دسترس: planner اجازه نمی‌دهد و executor
   EXECUTABLE={A0,A1} دارد — اثباتِ جهشیِ M5 (executor حتی صدا زده نمی‌شود)
```

## حداکثر مدت / حجم

مدتِ پیشنهادی: **۷ روز** (تا ۲۰۲۶-۰۸-۰۶، هم‌راست با بقیهٔ پنجره‌های آزمون).
حجم: ≤۱۴ اقدام، ≤۱۴ رسید، ≤۱۴ ردیفِ mission.

## پیش‌شرط‌ها (همه امروز برقرارند)

- [x] baseline ِ پیش از تغییر ثبت شده: ۴۶۳/۴۶۳ در ۴۲ سوییت
- [x] ۱۴/۱۴ سنجهٔ پل؛ ۲۰۵/۲۰۵ رگرسیونِ سوییت‌های متأثر
- [x] ۷/۷ جهشِ اجباری قرمز (`05-MUTATION-EVIDENCE.json`)
- [x] E2E read-only با یک trace_id واحد سبز (`06-E2E-TRACE.json`)
- [x] فلگ عضوِ `PAPER_FULL_FLAGS` **نیست** ⇒ غیابش واقعاً خاموش است
- [x] هیچ تستی وضعیتِ «فلگ خاموش» را pin نکرده (چک شد)

## شاهدِ موفقیت (بعد از ری‌استارت)

```text
۱) HEARTBEAT.md خطِ بوتِ تازه با PID نو
۲) در چرخهٔ بعدی (≤۱۲ ساعت):
     state/test_cycle/missions.jsonl        یک ردیف با status=done
     state/test_cycle/action_receipts/      یک رسید با status=EXECUTED
     journal.jsonl                          outcome.action_receipt=EXECUTED
                                            + outcome.action_trace=trace:…
۳) همان trace_id در ردیفِ mission و در journal یکی باشد
```

## شاهدِ شکست

```text
· missions.jsonl خالی بماند ولی journal ردیفِ تازه داشته باشد ⇒ پل صدا نمی‌خورد
· receipt با status=FAILED ⇒ متن خطا در errors؛ چرخه باید ok=False بدهد
· ردیفی با status ِ غیرِ done/failed ⇒ گذارِ غیرقانونی (نباید ممکن باشد)
· هر فایلِ نو بیرون از state/test_cycle/ ⇒ نقضِ دامنه، فوراً rollback
```

## Rollback

```text
نرم (بدونِ ری‌استارت):  چیزی لازم نیست — پل روی خطای خودش fail-soft است
کامل:                   set OCTOPUS_WIRE_ACTION_BRIDGE=0  + ری‌استارتِ organism
آنی:                    ساختنِ فایلِ _ops/STOP-ORGANISM
برگشتِ کد:              git -C F:\backup reset --keep 8d76618
```

## شرطِ توقف (stop condition)

هر یک از این‌ها ⇒ فلگ را ۰ کن و گزارش بده:
- بیش از ۲ رسیدِ `FAILED` پیاپی
- هر رسیدی با `classification` غیر از `A0`
- هر نوشتنی بیرون از `state/test_cycle/`
- رشدِ `missions.jsonl` بیش از ۲ ردیف در روز

## رأی

```text
تأیید:  «OWNER_AUTH: ARM OCTOPUS_WIRE_ACTION_BRIDGE + ری‌استارت organism»
رد:     «نه، پل خاموش بماند»
```

رأیِ این کارت **فقط** برای این دو اثر است. ری‌استارتِ tg-center، مسلح‌کردنِ
هر فلگِ دیگر، `PATCH_CARD`، merge، push و deploy کارت‌های جدا دارند.
