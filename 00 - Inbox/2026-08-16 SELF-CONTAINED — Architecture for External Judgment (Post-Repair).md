---
type: knowledge
kind: architecture-state-for-external-judgment
status: active
created: 2026-08-16 (~14:0x)
updated: 2026-08-16
created_by: agent (GLM, closing session of the repair night)
audience: external-judging-agents / councils
supersedes: "[[2026-08-15 SELF-CONTAINED — Architecture Deep-Scan for External Agents]]" (pre-repair snapshot)
sources:
  - "[[../06-EVIDENCE/DEEP-TEST-1H-2026-08-16]]"
  - "[[../06-EVIDENCE/PHASE02-2026-08-16]]"
  - "[[../00 - Inbox/2026-08-15↯16 NIGHT — MASTER SUMMARY|MASTER SUMMARY]]"
tags: [octopus, architecture, self-contained, judgment, post-repair, no-go]
---

# سند خودکش — وضعیت معماری برای قضاوت خارجی (پس از شب ترمیم 15↯16 اوت)

> **این سند خودکش است.** به vault نیاز نداری؛ هر ادعا با فرمان قابل‌رویت زیر خودش آمده. قبلی‌اش (2026-08-15) قضاوت شد؛ این جانشین پس از ~۷۰ کامیت ترمیم است. **قانون بزرگ شب: پیش از هر قضاوت، پیش‌فرضت را با درخت زنده بسنج (کلاس خطای C-015/C-018 سه بار امتحان شد).**

## ۱. توپولوژی زنده [A]

پنج عضو `_ops` (درخت F:\backup) + دیمون مغز `4d_system` + سه تسک زمان‌بند:

| عضو | نقش | مرز |
|---|---|---|
| organism (8771) | حلقهٔ اصلی، wiring ۴۰+ | write-state, send-via-center |
| center (8776) | بات تلگرام مرزی + relay دکتر | send-telegram |
| gateway (8774) | HTTP لوکال مینی‌اپ | local-http |
| live (8773) | سرویس زنده | local-http |
| cortex (8772) | لایهٔ شناختی | write-outputs, llm-budget-capped |
| daemon 4d | مغز: چرخه‌های propose-only (explore/introspect/create) | write-4d-outputs |
| تسک‌ها | Hourly (رصدخانه، ساعتی) · Poisoning Watch (۶ساعته) · Consolidation Tick (۶ساعته) — هر سه با python.exe مطلق | — |

## ۲. آنچه این شب ساخته/تغییر کرد (همه با کامیت)

| تغییر | ماهیت | شاهد زنده |
|---|---|---|
| **مرز اعتماد امضاشده + enforce** | manifest با SHA256 چهارده فایل TCB مغز + امضای Ed25519 مالک + `OCTOPUS_TCB_MANIFEST_ENFORCE=1` در همهٔ اعضا و دیمون — ویرایش TCB ⇒ mismatch ⇒ مسیر halt | `openssl pkeyutl -verify …` ×۲ Verified |
| **PEP سایه روی مرز ارسال تلگرام** | lease تک‌مصرف متصل به hash(action,params) + ناظر fail-soft در دو گلوگاه زنده — **ترافیک واقعی دیده و قضاوت شده** | `_ops/state/telegram-pep-shadow.jsonl` |
| **هولداوت پنهان L1** | ۶۰ آیتم frozen از بک‌تست، طلای هش‌شده، API فقط-بری‌ری، ACL مالک | **یافته: gaming (base-rate) مدل را شکست (0.0829<0.0978)** |
| **R16 صف فرضیه** | ۱۰۶۳→۳۹۷ فعال/۷۵۵ dedup، سقف اتمی ۱۰/روز (BEGIN IMMEDIATE، تست ۱۵-رشته) | `sqlite3 … hypotheses GROUP BY status` |
| **R18 دلتا-نه-سطح** | watermark منبع در consolidation 4d + گیت gist سمنتیک — تکرار سطح دیگر ثبت نمی‌شود | تیک ۶ساعته: cycle 5, sk=['cycle-1'] |
| **فیکس recall (C-021)** | ریشه: hash-as-float32 ⇒ NaN ⇒ similar() تهی — **M3: 9.28%→14.4%, median 2→21** | `recall_reach()` = 90/984/21.0 |
| **شوراها (سایه)** | کرنل ۱۹گام + عضو اولامای واقعی + گیت عدم‌اختیار ۵/۵ — **اجماع ≠ اجرا** | تست‌ها ۲۹ سبز |
| **کرنل بین شرایط دیمون** | دیمون نسل ۳ با enforce؛ self_code=False (بنر) — ولی C-024: env از .env:32 | daemon_state.json |

## ۳. کارنامهٔ صادقانهٔ قابلیت‌ها (سخت‌آزمایش ۶گانه)

**S5 خودترمیمی: REAL** · S1 مقاومت مسمومیت: PARTIAL (یک ردیف مسموم ایده‌های نو را سرکوب کرد) · S2 حاکمیت: PARTIAL (۹/۱۰ حمله رد؛ شکاف‌ها مستند) · S3 شورا: PARTIAL · S4 شواهد: PARTIAL (تکرار زیر دو شناسه قطعیت را دوبرابر کرد؛ حذف آخرین ردیف بی‌ردپاست) · **S6 پیش‌بینی: METAPHOR** (لبه‌ای بر نرخ پایه نیست؛ مسیر بهبود واقعی پیدا شد: persistence 0.0472<0.0617).

## ۴. وضعیت حکم

**NO-GO برای خودمختاری پیامددار قائم است** — دقیق‌تر از شب قبل: مسیرهای عملکردی سبز و تثبیت‌شده؛ کنترل‌های ساختاری (PEP فعال، ارزیاب مستقل L2/L3، جداسازی per-leg، lease در مسیر واقعی) هنوز سایه/طرح‌اند. **فرمول رسمی:** «حلقهٔ مشاهده و پیشنهاددهی با dedup و watermark فعال است؛ یادگیری خودکار، تثبیت جهش، ارسال/پرداخت خودکار و اجرای پیامددار همچنان NO-GO.»

## ۵. آنچه از قاضی می‌خواهیم (سؤالات §)

۱. **شکل:** آیا توپولوژی پنج‌عضو+دیمون+سه‌زمان‌بند، با دو منبع پیکربندی واگرا (flags.cmd/.env)، قابل‌دفاع است یا باید یک منبع واحد شود؟
۲. **اختیار:** آیا «manifest امضاشده + PEP سایه + هولداوت L1» مسیر درستی به سوی ارزیاب مستقل است؟
۳. **یادگیری:** M3 از ۹ به ۱۴٪ رسید؛ آیا هدف «M3=1.0ِ M1» اصلاً درست است یا واحدش فرق دارد؟
۴. **آمادگی:** کدام از کارت‌های بازِ رأی مالک را گلوگاه GO می‌دانید؟
۵. **مقایسه:** با چارچوب‌های ۲۰۲۶ (CSA/OWASP/MCPS) این معماری کجاست؟
۶. **Dissent:** کجا قضاوتتان نامطمئن است؟

**قالب خروجی:** ابتدا جعبهٔ ۸خطی verdict؛ سپس پاسخ به ۶ سؤال؛ هر ادعا به شمارهٔ § همین سند ارجاع بدهید.

## ۶. فرمان‌های راستی‌آزمایی (قاضی خودش اجرا کند)

```bash
cd F:\backup
openssl pkeyutl -verify -pubin -inkey _ops/owner-signing/octopus-owner-ed25519-public.pem -rawin -in 4d_system/config/trust-boundary.json -sigfile 4d_system/config/trust-boundary.json.sig
py -X utf8 _ops/tests/test_no_go_envelope.py
py -X utf8 -c "import json,sys; sys.path.insert(0,r'F:/backup/_ops/neural'); from consolidation import recall_reach; h=json.loads(open(r'F:/backup/_ops/neural/consolidation.json',encoding='utf-8').read()); print(recall_reach(h))"
cat _ops/state/telegram-pep-shadow.jsonl
powershell -NoProfile -Command "Get-ScheduledTask -TaskName '*Observator*','*Poisoning*','*Consolidation*' | ForEach-Object { \$_.TaskName + '=' + \$_.State }"
```

## ۷. مرز

این سند SoT اجرایی نیست؛ منبع نهایی: درخت زنده + STATE + CONTRADICTIONS (C-001..C-026، آزاد C-027). پروتکل پوش (C-023): کامیت آزاد، پوش فقط با کلمهٔ مالک.
