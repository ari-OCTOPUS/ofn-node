---
type: architecture
status: active
tags: [overview, architecture, master-map, organism, second-brain, mermaid]
created: 2026-07-09
updated: 2026-07-16
created_by: agent
sources:
  - "[[06 - Architecture Maps/SYSTEM-OVERVIEW]]"
  - "[[06 - Architecture Maps/SYSTEM_MAP]]"
  - "[[06 - Architecture Maps/ECOSYSTEM]]"
  - "[[_ops/ORGANISM-SPEC]]"
  - "[[05 - Agents/AGENT_REGISTRY]]"
  - "[[04 - Architect System/architect/ARCHITECT_CHARTER]]"
  - "[[ROTATION_CHECKLIST]]"
  - "[[01 - Dashboard/HANDOFF]]"
companion_agents:
  - "[[05 - Agents/Vault Cartographer]]"
  - "`.claude/agents/vault-cartographer.md`"
---

# MASTER-ARCHITECTURE — نقشهٔ معماریِ کلِ vault + ارگانیسم

> نقشهٔ کانونیِ «همه‌چیز در یک نگاه». نه اسپکِ اجرا (آن‌ها در [[_ops/ORGANISM-SPEC]] و اسنادِ 04)، بلکه **نقشهٔ ذهنیِ مهندسِ معمار**: این چیست، از چه لایه‌هایی ساخته شده، ایمنی کجا قفل است، کد کجاست، ایجنت‌ها کجایند، و کجا هنوز شکاف است.
> این سند را یک ایجنتِ فقط‌خواندنی (Vault Cartographer) از روی وضعیتِ واقعیِ repo تولید و به‌روزرسانی می‌کند — نه از حافظه.

---

## ۰) یک‌خط

یک **Obsidian vault ِ agent-first** که هم‌زمان کنترل‌پلینِ چند بیزنسِ موازی است **و** میزبانِ یک **سازوارهٔ خودگاورنور** (کد پایتون در `_ops/`) — همه پشتِ گیت‌های ایمنیِ *قفل‌شده‌در‌کد*، با یک ledgerِ append-only ِ هش‌زنجیره‌ای به‌عنوانِ منبعِ حقیقت.

اصلِ حاکم: **هوشِ گران فقط در نقاطِ تصمیمِ نادر؛ ایمنی از طریقِ ساختار، نه انضباط؛ سیستم هرگز نباید بتواند معیارِ قضاوتِ خودش را دور بزند.**

---

## ۱) استکِ لایه‌ای (نمای بلند)

```mermaid
flowchart TB
    subgraph L5["👤 لایهٔ حاکمیت — انسان"]
        ARI["آری — رئیس کل واقعی (D-01)\nتنها منبعِ verdict و «پذیرش»"]
        TG["📱 Telegram Command Plane\n/status /verdict /kill /gate"]
    end
    subgraph L4["🏛 Meta-controller — architect"]
        RD["Researcher-Designer\nپیشنهاد + evidence (propose-only)"]
        CO["Chief Orchestrator\nهماهنگیِ cross-domain — بدون صدور verdict"]
    end
    subgraph L3["🧬 Organism — _ops/ (کدِ زنده)"]
        HEART["فیزیولوژی: Heart\norganism.py + live_loop"]
        META["متابولیسم: Governor\ntelemetry → organ_gate → epoch → fitness → replication"]
        NEURAL["مغز: neural / doctor / debate / afferent / legs"]
    end
    subgraph L2["🏢 Business — N tenant مستقل"]
        BIZ["Lead-نقاشی · Ziman · Mining · Crypto · Accounting · Project-F 🔒 · دانش"]
    end
    subgraph L1["📜 Substrate — دانشِ پایدار"]
        VAULT["markdown + wikilink + frontmatter (schema)\ngit + JSONL + SQLite"]
    end
    subgraph L0["⚖️ Constitution — قانونِ ماشین‌خوان"]
        LAW["CLAUDE.md + _PROJECT_INSTRUCTIONS.md\n§۰ = هرگز حذف نکن / هرگز .git را دست نزن"]
    end

    ARI <--> TG <--> CO
    RD --> CO
    CO <--> BIZ
    CO <--> HEART
    HEART <--> META <--> NEURAL
    L4 --- L3 --- L2 --- L1 --- L0
    LAW -.->|override همه‌چیز| L4
    LAW -.->|override| L3
```

| لایه | نقش | فناوری |
|---|---|---|
| **Constitution** | قانونِ اساسیِ ماشین‌خوان که حتی ایجنتِ خودمختار هم دور نمی‌زند | `CLAUDE.md` + `_PROJECT_INSTRUCTIONS.md` |
| **Substrate** | حافظهٔ پایدار/دانش، human-readable | Obsidian، markdown، git، JSONL، SQLite |
| **Business** | N بیزنسِ مستقل، هرکدام `PROJECT.md` + لاگِ تلگرام | نقاشی/گالری/ماینینگ/کریپتو/حسابداری/Project-F/دانش |
| **Meta-controller** | مغزِ خودبهبود + هماهنگ‌کننده | `04 - Architect System/architect/` |
| **Organism** | سازوارهٔ همیشه-روشنِ خودگاورنور | `_ops/` (پایتون) |
| **Governance** | انسان + گیت‌های HITL | Telegram + charter + ledger |

---

## ۲) سه مکانیزمِ ایمنیِ عرضی (روی همه‌چیز)

```mermaid
flowchart LR
    REQ["هر اکشنِ ایجنت/ارگان"] --> G{{"⛔ §Security Gate\nCRITICAL باز در ROTATION_CHECKLIST؟"}}
    G -->|باز| RO["همه read-only\n(autonomy مؤثر = صفر)"]
    G -->|بسته اکنون ✅ 2026-07-06| K{{"🔴 Kill-switch واحد (D-06)\nflag halted + فایل STOP\nfail-closed"}}
    K -->|halted| STOP["توقفِ کل"]
    K -->|روشن| H{{"🙋 HITL verdict لازم؟\nمالی / ارتباطِ بیرونی / زیرساخت / حاکمیت"}}
    H -->|بله| ARIV["منتظرِ verdictِ آری"]
    H -->|خیر، برگشت‌پذیر و درون‌پوشه| EXEC["اجرا"]
    EXEC --> LED[("📜 Anchor Ledger\nappend-only · hash-chain")]
    ARIV --> LED
```

- **§Security Gate** — تک‌منبعِ وضعیت: §۲ ARCHITECT_CHARTER. اکنون **LIFTED** (۲۰۲۶-۰۷-۰۶، verdictِ صریحِ آری؛ ۴ ردیفِ CRITICAL + Fugu = ROTATED). ۱۴ ردیفِ HIGH/MEDIUM باز = backlogِ چرخش، گیت نیستند.
- **Kill-switch (D-06)** — fail-closed؛ flag در DB + فایلِ `STOP`.
- **HITL** — نقاطِ verdictِ اجباری: هر BUY/پرداخت، هر پیام به شخصِ واقعی (Spam Act/DNCR)، هر deploy/SSH (D-20)/حذف، هر تغییرِ charter/secret.
- **live_gate_open (گیتِ دوقفله)** — هیچ مسیرِ زنده‌ای پیش از **۲۰۲۶-۰۷-۲۱** و بدونِ دو قفلِ مالک باز نمی‌شود؛ در خودِ کد چک می‌شود (`opslib.live_gate_open`)، نه فقط در سند.

---

## ۳) ارگانیسم — نگاشتِ ماژول‌های `_ops/`

سه لایه: **آناتومی** (حافظه/ledger) · **فیزیولوژی** (ضربان) · **متابولیسم** (انرژی/سهمیه) — به‌علاوهٔ مغزِ عصبی، دکتر (verifier مستقل)، مناظره، مسیرِ حسّی و پاها.

```mermaid
flowchart TB
    subgraph CORE["هستهٔ همیشه-روشن"]
        ORG["organism.py\nتیک ۵دقیقه‌ای · heartbeat · daily"]
        LL["live_loop.py"]
        BUS["unified_bus.py"]
        WIRE["wiring.py — سیم‌کشیِ کل"]
        WD["watchdog.py"]
        GERM["germline.py — ژنومِ فریز"]
        CKPT["checkpoint.py · chrono.py"]
    end
    subgraph BUD["budget/ — متابولیسم + گیت‌ها"]
        OPS["opslib.py (پلِ ledger · LockedJson · live_gate)"]
        TEL["telemetry.py (دو منبعِ حقیقت، ro)"]
        OG["organ_gate.py"]
        EP["governor_epoch.py (epoch آلوستاتیک)"]
        FIT["fitness.py (پذیرش = کلیکِ انسان)"]
        REP["replication.py (σ>1 = ALERT سرطان)"]
        MG["money_gate.py"]
        CG["capability_gate.py"]
        AC["approval_channel.py"]
        ATT["attribution.py"]
        RC["reconcile.py"]
    end
    subgraph NEU["neural/ — سیستمِ عصبی"]
        ND["neural_driver.py"]
        CONS["consolidation.py"]
        HEB["hebbian.py"]
        CIRC["circadian.py"]
        NOCI["nociceptor.py"]
        REFL["reflex.py"]
        SIG["signal_hub.py"]
        SPR["sprint.py · hooks.py"]
    end
    subgraph DOC["doctor/ — verifierِ مستقل"]
        DD["doctor.py"]
        EVO["evolution.py"]
        CAL["calibration.py"]
        CHM["chamber.py"]
        SPE["spectral.py"]
    end
    subgraph IO["حس + مناظره + پاها"]
        AFF["afferent/ (ingest_raw · sensory_bus · school_bridge)"]
        DEB["debate/ (debate_loop · client · topics)"]
        LEG["legs/ (leg · lead_leg)"]
        RHY["chrono_rhythm/rhythm.py"]
        BRN["brain/cockpit.py · panel/server.py"]
    end

    ORG --> BUS --> WIRE
    WIRE --> BUD
    WIRE --> NEU
    WIRE --> DOC
    WIRE --> IO
    TEL --> OG --> EP --> FIT --> REP
    OPS --> LED[("ledger.jsonl\nهش‌زنجیره‌ای")]
    DD -.->|ممیزیِ مستقل| BUD
    NOCI -.->|درد → protective_halt| ORG
```

نکتهٔ کلیدیِ اجرا (از HANDOFF جلسهٔ ۴۱): تصمیمِ `protective_override` اکنون **پیش از** epoch گرفته می‌شود و epoch/fitness/replication/doctor روی `not _protective_skip` گیت‌اند → protective = detect + enforce (commit `c67c591`).

---

## ۴) ناوگانِ ایجنت‌ها (planned fleet)

> **هر ردیف وارثِ §Security Gate است.** هیچ‌کدام هنوز deploy نشده (فاز ۴)؛ autonomyِ مؤثرِ همه فعلاً propose/read-only.

```mermaid
flowchart TB
    ARCHR["architect-researcher\nخودبهبودی (propose-only)"]
    ARCHO["architect-orchestrator\nجمعِ وضعیت + رابطِ تلگرام"]
    LE["learning-engine\nspine عرضی L1–L9 (L0-shadow → L3)"]
    subgraph FLEET["اسکات‌های تحقیق"]
        SCOUT["Research Scout Fleet"]
        MYC["Mycelium Scout"]
    end
    subgraph TEN["گاردهای per-tenant"]
        ACC["accounting-clerk (draft)"]
        LEADP["lead-pipeline (draft outreach)"]
        CRY["crypto-watcher (SELL/TRIM ثبت‌شده، پساگیت)"]
        MIN["mining-deathwatch (INFORM only D-10)"]
        ZIM["ziman-capacity-guard (سقف ظرفیت)"]
        PF["projectF-reporter 🔒 (بدونِ هویت/پلتفرم)"]
        KI["knowledge-indexer (read-only)"]
    end
    ARCHO --> ARCHR
    ARCHO --> FLEET
    ARCHO --> TEN
    LE -.->|contract-محور| ARCHO
```

منبعِ کانونی: [[05 - Agents/AGENT_REGISTRY]]. ماتریسِ autonomy/تشدید: [[04 - Architect System/architect/ARCHITECT_CHARTER|ARCHITECT_CHARTER]].

---

## ۵) کهکشانِ زیرسیستم‌ها (نگاشتِ پوشه → نقش)

```mermaid
mindmap
  root(("F:\\backup\nvault-organism"))
    Constitution
      CLAUDE.md
      _PROJECT_INSTRUCTIONS.md
      ROTATION_CHECKLIST
    Control-plane
      00 - Inbox (proposals · scout-digests · replication-kit)
      01 - Dashboard (HANDOFF · Home · *.html · *.base)
      06 - Architecture Maps (این نقشه)
    Business
      03 - Projects (7 tenant)
      _code (کدِ per-tenant)
      08 - Assets
      10 - Telegram processing
      09 - People
    Meta-brain
      04 - Architect System (architect · learning-engine · octopus-build-prompts · scripts)
      05 - Agents (registry · fleet)
      07 - Knowledge (genome-system · Time-Architecture · school-memory)
    Organism-code
      _ops (budget · neural · doctor · debate · afferent · legs · tests)
      _memory (حافظهٔ فشرده)
      _launchpad (second-brain-live)
    Design-synthesis
      CHRONOS-FABLE-OS (15 لایه: Executive → MachineReadable)
      survival-gateway (LiteLLM · Layer0 ضدِ lock-in)
    Negative-space
      _Duplicates (فقط مقصدِ انتقال)
      _Templates
```

- **CHRONOS-FABLE-OS** — سنتزِ طراحیِ ۱۸-فایلی؛ فلسفهٔ کانونی: «ارگانیسمِ شناختیِ فانی، paradigm-agnostic، human-anchored» برای یک اپراتورِ واقعی. هر capability با cost متر می‌شود، هر effectِ برگشت‌ناپذیر پشتِ anchorِ انسانی، هر claim با تگِ epistemic + falsifier.
- **survival-gateway** — لایهٔ ۰ ضدِ vendor-lock-in روی **LiteLLM proxy** (MIT). عمداً بیرونِ vault اجرا می‌شود؛ مدل = موتورِ تعویض‌پذیر.

---

## ۶) جریانِ داده و منبعِ حقیقت

```mermaid
flowchart LR
    SENSE["ورودی‌ها\nتلگرام · رسید · دیتای بازار · school"] --> AFF["afferent/\nsensory_bus"]
    AFF --> STATE[("_ops/state/\nstate ماشین‌خوان")]
    AFF --> LED[("ledger.jsonl\nappend-only · hash-chain\n(آناتومی/MycoLedger)")]
    STATE --> ORG["organism tick"]
    ORG --> TEL["telemetry (ro)"]
    TEL --> DEC{"تصمیم\nارزان + رویدادمحور؟"}
    DEC -->|روزمره| DET["deterministic · fail-soft · $0"]
    DEC -->|گلوگاهِ نادر| LLM["فراخوانی LLM\n(دوقفله)"]
    DET --> LED
    LLM --> LED
    LED --> DASH["01 - Dashboard\nHANDOFF · CONTROL-PANEL.html"]
    FIT["fitness.py"] -->|«پذیرش» فقط از| OUT["logs/outbox.jsonl\nstatus=sent (کلیکِ انسان)"]
```

دو منبعِ حقیقتِ تلمتری: `ledger.jsonl` (ژنوم) + `core.db/usage` (مغز، فقط‌خواندنی). واگراییِ >۲۰٪ → FREEZE + شرطِ مرگِ `STOP-METABOLIC`.

---

## ۷) وضعیتِ design ↔ reality و شکاف‌های شناخته‌شده

> **🔄 رفرشِ ۲۰۲۶-۰۷-۰۹ (اجرای META-PROMPT BaseMap v1):** جدول از repoِ واقعی (HEAD `6a12197`) reground شد. دو تغییرِ بزرگ: چند «unwired» حالا wired است، و یک **P0ِ جدیدِ integrity** کشف شد (هستهٔ بریده). جزئیات: [[04 - Architect System/octopus-build-prompts/OCTOPUS-BASE-MAP-v1]] + [[00 - Inbox/2026-07-09 PROPOSAL — core-restore runbook + E16 human-append guard wiring]].

از [[01 - Dashboard/HANDOFF]] (جلسات ۴۱–۴۲) + git log + گراندینگِ ۲۰۲۶-۰۷-۰۹:

| ناحیه | وضعیت | یادداشت (گراند‌شده) |
|---|---|---|
| 🔴 **integrity هستهٔ `_ops/`** | 🔴 **P0 جدید** | ۷ فایلِ هسته در worktree بریده؛ HEAD سالم → `git restore` |
| هستهٔ Chrono | ✅ ساخته/committed | HEAD `6a12197`، tree تمیز `[FACT]` |
| protective-halt (S-fix-3) | ✅ enforce واقعی | commit `c67c591` `[FACT]` |
| money-lock / exposure | ✅ سالم | live قفل تا 2026-07-21 `[FACT]` |
| verifier-independence (Doctor) | ✅ آسیب‌ناپذیر | + Doctor Evolution **wired** (`6a12197`,`8b6c30b`) |
| `is_human` (E16) | 🔴→🟢 رفعِ کدی | گارد ساخته/تست‌شده ۱۰/۱۰ (`human_append_guard.py`)؛ سیم‌کشی propose-only |
| `mean_awareness()` باگ | 🟡 احتمالاً fix | `test_canonical_consolidation.py` assert می‌کند؛ اجرا `[OPEN]` (هستهٔ بریده) |
| consolidation | ✅ wired behind flag | commit `c77238b` `[FACT: git log]` |
| Doctor Evolution / Box | ✅ wired | commits `6a12197` + `8b6c30b` `[FACT]` |
| پاها (legs) | ⚠️ فقط ۱ پا با حلقه | `[FACT: HANDOFF]` |
| نسخهٔ ledger | ⚠️ drift | `0.4.6` (unified_bus) ↔ `0.4.5` (test) `[FACT]` |
| تصادمِ نامِ «LANGAR» | 🔴 ≥۶ موجود | [[06 - Architecture Maps/LANGAR-ALIAS-REGISTRY]] `[OPEN]` |
| Project-F guard | ⚠️ فقط UI | enforceِ کدی پیدا نشد `[OPEN]` |
| ⏳ live-gate | ~۱۲ روز | 2026-07-21 → «Pre-Live Checklist» = P0 |
| پای 4D ‏(`4d_system`) | ✅ هم‌سطح‌سازیِ C→F ‏durable شد (۰۷-۱۶) | منبعِ حقیقت حالا `F:\backup\4d_system` (کامیت `5a69f2c`، ۱۱۱ فایل)؛ ۷ فیکسِ تولیدی سالم، ۲۷۵ تستِ هسته سبز؛ کپیِ دسکتاپ C منسوخ — جزئیات و خطِ قرمزِ B6: [[06 - Architecture Maps/TRI-PLANE RECONCILIATION - ops vs NBB-CP vs 4D-control-plane|TRI-PLANE]] §۷ `[FACT]` |

---

## ۸) نقاطِ ورودِ خواندن (برای هر مهندس/ایجنتِ تازه)

۱. [[01 - Dashboard/HANDOFF]] — آخرین وضعیت
۲. [[06 - Architecture Maps/SYSTEM-OVERVIEW]] و همین سند — چراییِ معماری
۳. [[_ops/ORGANISM-SPEC]] — اسپکِ خط‌به‌خطِ کد
۴. [[04 - Architect System/architect/ARCHITECT_CHARTER]] — قواعد/autonomy/گیت‌ها
۵. [[05 - Agents/AGENT_REGISTRY]] — ناوگان
۶. `_ops/tests/run_all.py` — قراردادِ رفتاریِ واقعیِ کد

---

## ۹) محدودهٔ منفی (این نقشه هرگز نمی‌کند)

- هیچ secret/کلید/seed را echo نمی‌کند (همه در ledger «افشاشده» فرض).
- هیچ جزئیاتِ هویت/پلتفرم/محتوای **Project-F** بیرون نمی‌دهد — فقط کدنام.
- `_Duplicates` و `_Archive` را به‌عنوانِ حقیقت نمی‌خواند (فقط مقصدِ انتقال).
- مسیرهای `.agentignore` هرگز خوانده/نوشته/echo نمی‌شوند.

> **نگهداری:** این فایل را ایجنتِ [[05 - Agents/Vault Cartographer]] (و همتای `.claude/agents/vault-cartographer.md`) از روی وضعیتِ واقعیِ repo بازتولید می‌کند — نه دستی، نه از حافظه.
