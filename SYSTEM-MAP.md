# SYSTEM-MAP — نقشهٔ واقعی ارگانیسم OCTOPUS

> Branch: `audit/zcode-20260828` · Author: ZCode (PC) · Date: 2026-08-28
> Sources: full read of ari322/{ofn-node, langar, Armin} @ main (2026-08-27 clones), live SSH probes of nodes 138/180/182 (2026-08-28), F:\backup live tree + vault evidence 2026-08-20..28.
> Claim labels: [FACT] = directly measured · [DERIVED] = follows from evidence · [ASSUMED] = reasonable, unverified · [UNKNOWN] = could not verify.

## 1. گره‌ها و نقش‌ها (همه در 2026-08-28 اندازه‌گیری شد)

| Node | Hostname (FACT via SSH) | Role | Key services (active) | State |
|---|---|---|---|---|
| PC (laptop) | Windows, F:\backup | شتاب‌دهنده/معماری + مغز چت + والت | organism.py:8771 (beat 52218) · cortex.py:8772 · live/server.py:8773 · telegram_center center.py · miniapp_gateway:8774 · ollama:11434 | LIVE · RAM 94.5% full ⚠ |
| 138 (DietPi) | `DietPi` 192.168.0.138 | gateway مالک + پاهای کسب‌وکار (OFN) | ofn.service · octopus-bridge · octopus-control-router · octopus-cycle-settler · octopus-router · octopus-supervisor · octopus-verify-dispatcher · ofn-heartbeat · hypno-fugu-mini:8895 | LIVE · up 10d · RAM 1.5/3.9GB · disk 20% |
| 180 | `octopus-continuity-180` | مغز شناختی/پیوستگی | octopus-gateway · octopus-organism-lab · octopus-llama-lab (llama-server :8081) · octopus-afferent-lab · octopus-soak-lab | LIVE · up 2d17h ⚠ llama binds 0.0.0.0 |
| 182 | `sensorium-opi5pro` | شاهد/سنسوریوم | nats-server (JetStream) · octopus-sensorium · fusiond S1 · metacontrol (advisory) · reflex A0 (observe) · skill-tracker · gap001-boot-probe | LIVE · up 10d12h · no LLM |
| PC_worker | (صف job لپ‌تاپ) | اجرای jobهای اسکن/تست | via _ops queues | [UNKNOWN] not directly probed this pass |

## 2. مسیر داده: مشاهده → اثر

```
Telegram (owner)
  └─ center.py (Bot-2, ~400KB) ── typed events (typed-v1 spine)
       ├─ cognition loop (memory reads ×3/cycle, readback=read_ok)
       ├─ ask_brain → cortex model_router → deepseek-v4-flash (collab) / ollama (local)
       ├─ approval bridge → Bot-1 (approval_channel, inside organism)
       └─ outbox → SenderBridge (send-locked; A18 canary only, mids 617/618)
138 (OFN node)
  ├─ partner HTTP (initData HMAC → session) → facts/ledger/outbox per tenant
  ├─ legs: ziman:8791 · painting(lead):8792 · studio:8793 · owner panel:8794
  ├─ worker → ModelRouter → RULES rung → REMOTE rung (fugu @ 8895) with scrub+quota
  └─ octopus-mesh inbox(5)/outbox(9) + bridge:8796 ↔ PC germline (E:/germline/octopus.git)
182 (sensorium)
  └─ sensors → NATS JetStream → fusiond frames → metacontrol/reflex advisory → evidence
180 (continuity)
  └─ llama-server:8081 (qwen3-0.6b local tier) + organism-lab continuity loops
Money path (the goal):
  lead/painting: quote → outbox (MANUAL send today) → job → invoice → [GAP: no E2E]
  ziman: Shopify checkout → [GAP: never smoke-tested end to end] → bank payout → CSV reconcile → CONFIRMED
  studio: TG drafts + FF/OF gated (KYC_BLOCKED) → [GAP: no live publish]
```

## 3. مغزها و مدل‌ها (LLM bind — FACT from 2026-08-27 LIVE-TRUTH + probes)

| Bind | Model | Use | Notes |
|---|---|---|---|
| 138:8895 hypno-fugu-mini | fugu (Sakana) | volume work of legs | BRAIN_PROVIDER=fugu; DeepSeek NOT proven on this port |
| 180:8081 | qwen3-0.6b-q4_0 | local tier only | ⚠ binds 0.0.0.0 (LAN-exposed) |
| PC cortex model_router | deepseek-v4-flash | collab_chat only | ACTIVATION-CORTEX-PAID.flag = OFF |
| PC :11434 | ollama | secondary local | [UNKNOWN] current models |

## 4. حافظه و ledger ها

| Store | Size | Integrity |
|---|---|---|
| genome ledger (vault `07 - Knowledge/genome-system/ledger/ledger.jsonl`) | 14,168 records, tip b8a0da75… | hash-chained; C-028: tip deletion undetected (VOTE 4 pending) |
| PC organism memory | 12,736 rows · recall_reach 91 events | read-tick/1 schema · readback ok |
| 138 sqlite ×4 (ledger/facts/outbox/products + painting/studio) | painting 176KB · products 200KB · studio 116KB | WAL + synchronous=FULL · chain verify on boot |
| langar.db (repo `langar`) | 23 tables, schema v8 | WAL · idempotent migrations |
| 4d_system memory | independent daemon | poisoning-watch green since 08-15 |

## 5. نقاط شکست (failure points)

1. **RAM لپ‌تاپ ۹۴.۵٪** — بزرگ‌ترین مصرف‌ها firefox/Grok-Bot/Cursor/llama-server. یک بار اضافه = OOM ارگانیسم. [FACT 06-EVIDENCE/OCTOPUS-HEALTH-WATCH-2026-08-27]
2. **تنها یک poller تلگرام** با lease — درست طراحی شده ولی کل کانال مالک به همین یک پروسهٔ center.py وابسته است (تک‌فایل ~400KB، WORKLOCK).
3. **germline lag 2.46h** (warn) + شاخهٔ rescue سی‌ودو کامیت جلوتر از master + ۱۱۴۹ فایل کامیت‌نشده → بحران بازتولیدپذیری: 163/163 فقط روی شاخهٔ repair قابل بازتولید بود.
4. **ofn-backup.service روی 138 غیرفعال** — بدون بکاپ تأییدشده روی برد درآمد.
5. **پیوستگی 180 فقط ۲ روز uptime** (ریبوت‌های اخیر) در برابر ۱۰ روز بقیه.

## 6. مسیرهای مرده (dead paths)

- کنترل-برین (second-brain-live) — retired 2026-07-24 (409 risk + PII quarantine) · `/brain/ask` · octopus-wire · hypno.service روی 138 (با 8895 تضاد) · پورت‌های 8791-8794 روی دسکتاپ (معلوم شد مال برد است) · task قدیمی Observatory (disabled C-014) · http.server:8765 معلق از 08-14 (kill نیاز به رأی مالک).
- در کد langar: BrainRouter، ACELoop، CoachAgent، MemorySystem.search_semantic، Contract.allows/must_ask، tracer decorator — همه کامل، هیچ‌کدام فراخوانی نمی‌شوند.
- در کد ofn: LocalBrain (rung وصل نیست)؛ outbox فرستنده ندارد (عمدی، تا سند گیت).

## 7. اجزای تکراری (خلاصه؛ جزئیات در DUPLICATES.md)

چهار router هم‌نام · researcher سه‌نسخه‌ای (langar ×2 + pro) · دو بانک سؤال · دو نرمال‌ساز رقم فارسی · دو پروژهٔ هم‌نام «langar» (گیت‌هاب HRV ≠ والت Project-F) · NBB-CP (Black Box) در برابر _ops زنده · بورد مالک با ۱۲ میرور · سه لایهٔ handoff هم‌پوشان.

## 8. نکتهٔ منبع حقیقت

GitHub = تاریخ/سجل است؛ دیسک زنده = وضعیت runtime است. الان این دو **۳ هفته تا ۲ ماه** فاصله دارند (langar@06-28، Armin@06-30، ofn-node@08-04 در برابر کار زنده تا 08-28). هر عدد این نقشه از کدام‌側 آمده، ذکر شده.
