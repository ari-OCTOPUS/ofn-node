---
tags: [obsidian, vault, index, agent-context]
aliases: [ولت-ایندکس, Vault Index]
updated: 2026-09-03
---

# Obsidian Vault Index — نقشه کامل یادداشت‌ها

> این فایل برای Obsidian graph ساخته شده.
> هر node در graph باید به اینجا لینک داشته باشد یا از اینجا لینک بگیرد.

## هسته‌های اصلی

- [[CLAUDE]] — قانون اساسی · اول هر session
- [[MEGA-DATA]] — نقشه کامل سیستم
- [[HANDOFF]] — وضعیت زنده session
- [[INDEX]] — ورودی اصلی vault
- [[PORTFOLIO-TENANT-MAP]] — چهار tenant
- [[DECISIONS]] — تصمیمات ثبت‌شده

## پرتفوی

- [[ziman]] — GiftMesh Sydney · ملیحه
- [[lead]] — Master Painting · عباس  
- [[studio]] — تولید محتوا · سبا
- [[hypno]] — tenant چهارم · بدون charter

## معماری

- [[docs/architecture/ZIMAN-BROWSER-HARVESTER]] — PR#141
- [[ofn/agents/source_registry]] — PR#142 · ۱۷ منبع
- [[ofn/agents/seek_harvest]] — ✅ LIVE
- [[ofn/agents/h1_harvest]] — ⚰️ DEAD
- [[ofn/agents/nsw_ocp_harvest]] — ⚠️ PARKED

## امنیت و رضایت

- [[docs/consent/]] — سیاست رضایت
- [[docs/security/]] — سیاست امنیتی
- [[CLAUDE#گیت‌های بسته]] — secret_rotation · partner_precondition

## وضعیت منابع

| منبع | وضعیت | فایل |
|---|---|---|
| Seek painter jobs | ✅ LIVE | seek_harvest.py |
| tenders.nsw.gov.au | ⏳ PR#141 | ziman_tender_harvest.py |
| NSW OCP bulk | ⚠️ PARKED | nsw_ocp_harvest.py |
| h1 feed (NSW eTendering) | ⚰️ DEAD | h1_harvest.py |
| Indeed painter jobs | 🔵 stub | — |
| Airtasker painting | 🔵 stub | — |
| HiPages quotes | 🔵 stub | — |

## گراف وابستگی agents

```
source_registry
    ├── seek_harvest          ✅
    ├── ziman_tender_harvest  ⏳ PR#141
    ├── nsw_ocp_harvest       ⚠️
    └── [stub‌ها...]          🔵

outbound_worker
    ├── lead_email_writer
    ├── owner_notify
    └── imap_listener

quote_pipeline
    ├── quote_engine
    └── quote_fingerprint
```

---
*update: 2026-09-03 · board138*
