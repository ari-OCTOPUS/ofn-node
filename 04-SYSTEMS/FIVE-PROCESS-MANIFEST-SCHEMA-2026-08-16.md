---
type: system-spec
id: FIVE-PROCESS-MANIFEST-SCHEMA
created: 2026-08-16 ~06:3x (مأموریت Manifest & TCB Sequence — پس از فکت‌چک)
mode: PROPOSE-ONLY — بدون enforce، بدون تغییر manifest امضاشده
scan_basis_note: "پایهٔ اسکنِ مأموریت (e5faff4/beat37123) کهنه بود؛ این سند با HEAD=39b756c [A] نوشته شد"
---

# اسکیمای شناسنامهٔ پنج‌پروسه‌ای زنده (T1)

## وضعیت پیاده‌سازی [A]

پروبِ فقط-خواندن **از قبل موجود و فعال** است: `_ops/audit/organism_manifest.py`
(کامیت b9a9a53، PHASE02 آن را به AEB وصل کرد). آخرین اجرا [A]:

| role | pid | ports | entry-sha256 (12) |
|---|---|---|---|
| organism | 25912 | 8771,8777 | 515e4dc65bfb |
| cortex | 22796 | 8772 | ef1471feef3e |
| live | 9836 | 8773 | 90ecc453da24 |
| gateway | 20572 | 8774 | 0392d2bd2fad |
| center | 11500 | 8776 | d67422f1d32d |
| (aux) unknown | 5780 | 8765 | http.server لوکال [A] |
| (aux) unknown | 12276 | — | دیمون 4d (بدون .py در cmdline) [A] |

## اسکیما (octopus-organism-manifest، نسخهٔ صفر — پیاده‌شده)

```yaml
schema: octopus-organism-manifest/0
observed_at: <iso-utc>                     # TTL volatile 24h
declared_members: [organism, center, gateway, live, cortex]
members_observed:
  - role: <str>                            # نقش از basename ورودی؛ ناشناخته='unknown'
    pid: <int>                             # از Win32_Process [A]
    started: <datetime>                    # CreationDate
    ports_listening: [<int>]               # netstat -ano [A]
    entry_file: <path|null>                # نخستین .py از cmdline (مطلق/نسبی حل‌شده)
    entry_sha256: <hex|null>               # هش فایل ورودیِ در حال اجرا
    effect_paths: [<str>]                  # کلاس اثر (read-only/write-memory/send-telegram/spend)
    cmdline: <str-300>
flags_effective_last_wins: {<FLAG>: <val>} # بازپارس flags.cmd با «آخرین تعریف برنده» (موتور flag_drift) [A]
scheduled_tasks: [<name=state>]            # Get-ScheduledTask *Observator*/*OCTOPUS*
drift:                                     # ادعا در برابر مشاهده
  declared_not_observed: [<role>]
  observed_not_declared: [<role>]
  unknown_cmdline_members: <int>
```

**CLAIMED vs LIVE و سنجش دلتا:** فیلد `drift` همین تمایز است —
`declared_members` (ادعا، از STATE) منهای `members_observed` (مشاهدهٔ پروس)؛
هر مقدار unknown/غایب = شکاف شناسنامه. دلتای هش (entry_sha در برابر
امضای مالک) = قدمِ رأی‌دار بعدی (نسخهٔ ۱: امضای همین manifest).

**کلاس‌های اثر per-limb [B از نقشهٔ کد + A از پروب]:** organism=write-state/send-via-center ·
center=send-telegram(write tg-state) · gateway=local-http/read · live=local-http/read ·
cortex=write-outputs/llm-budget-capped · (دقت: spend-fugu منتفی — فوگو بازنشسته [A: _TIER_ROLE]).

## پروب [A]
`py _ops/audit/organism_manifest.py` — فقط-خواندن (CIM/netstat/parse)؛
هیچ پروسه/فلگ/فایلی را تغییر نمی‌دهد (بازبینی کد + اجرای بی‌اثر многокاره).
