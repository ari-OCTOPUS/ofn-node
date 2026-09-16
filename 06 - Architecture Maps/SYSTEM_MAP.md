---
type: moc
status: active
tags: [architecture, map, governance]
created: 2026-07-03
updated: 2026-07-03
---

# SYSTEM_MAP — نقشه کل سیستم

> حلقه: architect ↔ دامنه‌ها ↔ تلگرام ↔ verdict انسانی. سه مکانیزم ایمنی روی همه‌چیز: **HITL**، **Kill-switch**، **§Security Gate**. منبع قواعد: [[04 - Architect System/architect/ARCHITECT_CHARTER|ARCHITECT_CHARTER]].

```mermaid
flowchart TB
    ARI["👤 آری — رئیس کل واقعی (D-01)\nهمه verdictها"]
    TG["📱 Telegram Command Plane\n/status /verdict /kill /gate"]
    GATE{{"⛔ §Security Gate\nCRITICAL باز در ROTATION_CHECKLIST؟\n→ همه read-only\nوضعیت فعلی: بسته"}}
    KS(["🔴 Kill-switch واحد (D-06)\nflag halted در DB + فایل STOP\nfail-closed"])
    LEDGER[("📜 Anchor Ledger\nappend-only · hash-chain\nهمه verdictها و اجراها")]

    subgraph ARCH["🏛 architect (fusion-mvp runtime)"]
        RD["Researcher-Designer\nفقط پیشنهاد"]
        CO["Chief Orchestrator\nعملیات cross-domain — بدون verdict"]
    end

    subgraph DOMAINS["دامنه‌ها (manifest = قرارداد)"]
        ACC["Accounting\ntenant #1 · draft-only"]
        LEAD["Lead-نقاشی\ntenant #2 · draft outreach"]
        MIN["Mining\ntenant #3 · INFORM only (D-10)"]
        CRY["Crypto-etoro\nBUY=انسان · SELL=exit_rules (D1)"]
        ZIM["Ziman\nسقف ظرفیت (D4)"]
        PF["Project-F 🔒\nفقط کد — بدون جزئیات"]
        HYP["هیپنوتیزم 📚\nfiction-canon ≠ evidence"]
    end

    ARI <-->|verdict / دستور| TG
    TG <--> CO
    RD -->|پیشنهاد + evidence| CO
    CO -->|پیشنهاد با ID| TG
    CO <-->|خواندن manifest / نوشتن draft| DOMAINS
    GATE -.->|override همه مجوزها| ARCH
    GATE -.->|override| DOMAINS
    KS -.->|halt همه| ARCH
    KS -.->|halt| DOMAINS
    CO -->|هر رویداد| LEDGER
    TG -->|هر verdict| LEDGER
```

## گیت‌های HITL (نقاط verdict اجباری)

| نقطه | چه چیزی بدون انسان رد نمی‌شود |
|---|---|
| مالی | هر BUY · SELL اختیاری · هر پرداخت/خرج (charter §۳، §۷) |
| ارتباط بیرونی | هر پیام به مشتری/شخص واقعی (Spam Act / DNCR در Lead) |
| زیرساخت | deploy، تغییر کد، SSH (D-20)، حذف |
| حاکمیت | تغییر charter/قواعد/مجوزها — فقط انسان، هرگز ایجنت |
| گیت امنیتی | باز/بسته کردن §Security Gate — فقط verdict ثبت‌شده |

## وضعیت لایه‌ها (2026-07-03)

کاغذ (فاز ۱–۳): ✅ کامل · runtime (فاز ۴): ⏳ منتظر rotation + TOP-5 آدیت — [[00 - Inbox/Prompt - Phase 4 Real Integration|پرامپت Phase 4]]
