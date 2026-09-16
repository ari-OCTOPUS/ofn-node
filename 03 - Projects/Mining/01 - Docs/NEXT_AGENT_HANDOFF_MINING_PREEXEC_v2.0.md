---
type: agent_handoff
version: "2.0"
project: Mining
status: active
mining_leg: active
created: 2026-07-12
updated: 2026-07-12
tags: [mining, handoff, agent, execution, roadmap]
---

# NEXT AGENT HANDOFF — Mining v2.0

> **ایجنت بعدی: اول این فایل را بخوان.**
> تاریخ تهیه: 2026-07-12
> وضعیت: **Mining Leg فعال در اختاپوس — VERDICT_QUEUE باز — آماده فاز اجرایی**

---

## 0. خلاصه وضعیت

```yaml
mining_leg:
  status: ACTIVE
  flag: OCTOPUS_WIRE_MINING=1
  organism_pid: 21556
  started: 2026-07-12T13:14:11
  leg_id: mining-fleet
  autonomy: read-only + propose-only
  money_link: incubating (budget=0)
  secrets: () — D-11
  telegram_digest: active (⛏ topic)

verdict_queue:
  MIN-V1: open  (کدام ریگ‌ها سالم‌اند؟)
  MIN-V2: open  (برق <$0.05/kWh؟)
  MIN-V3: open  (هیچ mining فعلی؟ — می‌تونی ببندی)
  MIN-V4: open  (Hardware Registry پر؟)
  MIN-V5: open  (wallet access صفر؟ — می‌تونی ببندی)
  MIN-V6: open  (coin scouting فقط report؟ — می‌تونی ببندی)

organism_state:
  electricity_mood: "🟡" (fail-closed — ریگ‌ها ناشناخته)
  nodes_total: 0
  nodes_running: 0
  hashrate_measured: false
  wire_mining: true

next_immediate_action:
  "01 - Docs/10-Step Roadmap — Competitive Intel & Execution.md → مرحله ۱"
```

---

## 1. فایل‌های خواندنی (ترتیب مهم)

```yaml
truth_anchor_priority:
  1: "01 - Docs/10-Step Roadmap — Competitive Intel & Execution.md"
     reason: "۱۰ مرحله بعدی + تحلیل ۱۲ رقیب بازار"
  2: "01 - Docs/Phase Status - Execution Plan & Prompt v2.0.md"
     reason: "truth anchor — فاز فعلی + ۳ لایه فعال‌سازی"
  3: "MANIFEST.yaml"
     reason: "spec کامل پروژه + hard rules + blackbox_potential"
  4: "PROJECT.md"
     reason: "شناسنامه + Active Context + KPIها"
  5: "VERDICT_QUEUE.md"
     reason: "۶ تصمیم باز — مرحله ۱ دستورالعمل بستن ۳ تا"
  6: "REGISTRY.md"
     reason: "رجیستری tenant + hard-gated actions"
  7: "RUNBOOK.md"
     reason: "مجاز/ممنوع + hardware registry minimum"
  8: "DecisionLog.md"
     reason: "تاریخچه تصمیمات + فعال‌سازی leg"
  9: "Coin Scouting Framework.md"
     reason: "چارچوب انتخاب کوین + قالب death-watch"
  10: "Hardware Registry & Runbook.md"
      reason: "رجیستری ناوگان — همه [To measure]"
  11: "contracts/adapter.yaml"
      reason: "رابط Mining ↔ اختاپوس"
  12: "README.md"
      reason: "نقشه ایجنت سریع"

reference_only:
  - "01 - Docs/TENTACLE-ALPHA-MINING_Hybrid_MegaPrompt_v3.0.md"
  - "02 - Code/mining_preexec_mvp/docs/ARCHITECTURE.md"
  - "02 - Code/mining_preexec_mvp/docs/OCTOPUS_LEG_DESIGN.md"
  - "02 - Code/mining_preexec_mvp/plans/MASTER_PLAN.md"
```

---

## 2. قوانین غیرقابل عبور

```yaml
hard_rules:
  D-10: "هر buy/sell/withdraw = HARD_STOP و فقط انسان"
  D-11: "ایجنت هیچ‌وقت wallet/seed/private key نمی‌بیند"
  D-20: "SSH مستقیم ممنوع — deploy فقط از مسیر repo+deploy gate با verdict"
  D-2:  "معیار abandon فقط death-watch: dev dead 8w، chain stalled، community dead"
  electricity: "<$0.05/kWh یا solar — بالاتر = mining HALT"
  coin_selection: "فقط از طریق Coin Scouting Framework"
```

### ممنوع مطلق

```yaml
forbidden:
  - read_wallet_seed
  - read_private_key
  - create_or_modify_wallet
  - buy / sell / withdraw
  - ssh_to_node (مستقیم)
  - deploy_to_node (بدون verdict)
  - start_miner / stop_miner (بدون verdict)
  - connect_to_pool (بدون verdict)
  - expose_or_store_secret
  - deactivate OCTOPUS_WIRE_MINING (بدون verdict مالک)
```

### مجاز

```yaml
allowed:
  - read_all_project_files
  - close_VERDICT_V3_V5_V6 (safety-only — zero physical access needed)
  - create_or_edit_docs
  - generate_markdown_reports
  - update_INDEX_DecisionLog_PhaseStatus
  - read_ORGANISM_STATE_json
  - propose_physical_rig_checks (draft only)
  - update_OpenQuestions
```

---

## 3. ۱۰ مرحله بعدی (از نقشه راه)

ایجنت بعدی باید از **مرحله ۱** شروع کند و بدون پرش بره جلو:

| مرحله | توضیح | مدت | وابستگی |
|---|---|---|---|
| **۱** | بستن MIN-V3, V5, V6 (تایید safety state از ORGANISM-STATE) | ۱۵ min | هیچ |
| **۲** | تحقیق رقبا ✅ انجام شد — فقط مرور کن | ۵ min | هیچ |
| **۳** | بررسی فیزیکی ریگ‌ها — MIN-V1 | ۱-۲ ساعت | نیاز به دسترسی فیزیکی |
| **۴** | بررسی هزینه برق — MIN-V2 | ۳۰ min | نیاز به اطلاعات مالک |
| **۵** | انتخاب ماینر (XMRig ARMv8) | ۳۰ min | مرحله ۳ |
| **۶** | انتخاب کوین #۱ (Monero) | ۳۰ min | مرحله ۵ |
| **۷** | وصل ریگ اول (deploy gate) | ۱-۲ ساعت | مرحله ۳-۶ + verdict مالک |
| **۸** | بررسی Fleet Manager vs Mining Leg | ۳۰ min | مرحله ۷ |
| **۹** | تأیید Telegram digest | ۱۵ min | مرحله ۷ |
| **۱۰** | اولین گزارش هفتگی + بستن V4 | ۳۰ min | مرحله ۷ |

---

## 4. تحلیل رقبا (مرحله ۲ — خلاصه)

### رقبای Tier-1 (پلتفرم‌های مدیریت)

| رقیب | قیمت | CPU | ARM | نقاط ضعف |
|---|---|---|---|---|
| **Hive OS** | $0.50/mo/rig | ✅ | ❌ x86 only | malware target، بدون ARM |
| **Awesome Miner** | Free→paid | ✅ | ❌ x86 only | Windows-only |
| **MinerStat** | ~$2/rig/mo | ✅ | ⚠️ Linux ممکن | جامعه کوچک |

### رقبای Tier-2 (ماینرها)

| رقیب | ARM | توصیه |
|---|---|---|
| **XMRig** | ✅ ARMv8 | ✅ انتخاب اول |
| **XMRigCC** | ✅ ARMv8 | ✅ اگر dashboard خواستی |
| **Rigel** | ❌ NVIDIA only | ❌ |

### رقبای Tier-3 (تهدیدات)

| تهدید | شدت |
|---|---|
| **Antminer X5/X9 (RandomX ASIC)** | 🔴 بالا — D2 پوشش می‌دهد |
| **NiceHash حذف CPU algorithms** | 🟡 متوسط — ما مستقیم pool |
| **پایین بودن profitability** | 🟡 متوسط — D2 = survival |

### شکاف بازار (فرصت ما)

| شکاف | وضعیت |
|---|---|
| OSINT/Security برای mining | هیچ‌کس انجام نداده |
| AI CPU optimization | هیچ‌کس |
| ARM-native management | هیچ‌کس |
| Unified CPU + monitor + security | هیچ‌کس |

---

## 5. فایل‌های عملیاتی اختاپوس

```yaml
ops_files:
  env: "F:/backup/.env"
    contains: "OCTOPUS_WIRE_MINING=1"
  flags: "F:/backup/_ops/OCTOPUS-flags.cmd"
    contains: "OCTOPUS_WIRE_MINING=1"
  state: "F:/backup/_ops/state/ORGANISM-STATE.json"
    contains: "mining key + wire_mining: true"
  leg: "F:/backup/_ops/legs/mining_leg.py"
    size: "21 KB, 389 lines, 2 brains"
  organism: "F:/backup/_ops/organism.py"
    pid: 21556
  restart_method: |
    create STOP-ORGANISM + RESTART-REQUESTED in F:/backup/_ops/
    organism picks up, clears files, restarts with new env
  rollback: |
    delete OCTOPUS_WIRE_MINING=1 from .env and OCTOPUS-flags.cmd
    restart organism
```

---

## 6. ساختار پروژه Mining

```text
Mining/
├── README.md                          ← نقشه ایجنت سریع
├── INDEX.md                           ← فهرست کامل (۱۶ بخش)
├── PROJECT.md                         ← شناسنامه پروژه
├── MANIFEST.yaml                      ← spec + hard rules + blackbox
├── REGISTRY.md                        ← رجیستری tenant
├── RUNBOOK.md                         ← مجاز/ممنوع
├── VERDICT_QUEUE.md                   ← ۶ تصمیم باز
├── DecisionLog.md                     ← تاریخچه تصمیمات
├── OpenQuestions.md                   ← مجهول‌ها
├── Coin Scouting Framework.md         ← چارچوب + death-watch
├── Hardware Registry & Runbook.md      ← رجیستری ناوگان
├── contracts/adapter.yaml             ← رابط اختاپوس
│
├── 01 - Docs/
│   ├── Phase Status - Execution Plan & Prompt v2.0.md  ← TRUTH ANCHOR
│   ├── 10-Step Roadmap — Competitive Intel & Execution.md  ← ۱۰ مرحله
│   ├── NEXT_AGENT_HANDOFF_MINING_PREEXEC_v2.0.md  ← ← این فایل
│   ├── TENTACLE-ALPHA-MINING_Hybrid_MegaPrompt_v3.0.md  ← spec v3.0
│   ├── NEXT_AGENT_HANDOFF_MINING_PREEXEC_v1.0.md  ← نسخه قدیمی (ref only)
│   ├── Strategy & Roadmap/ (۷ PDF)
│   ├── Bot System/ (۳ PDF)
│   └── Orange Pi Automation System/ (۲ MD)
│
├── 02 - Code/
│   ├── Ai bots/ (sentinel, coordinator, fleet, deploy)
│   ├── Robo-data/ (نسل قبلی)
│   └── mining_preexec_mvp/ (۱۰ module, schemas, tests, plans)
│
├── 03 - Rigs/
│   ├── Mining-1/Hcash/ (deploy scripts)
│   ├── Mining-1/Mining E/ (screenshots)
│   ├── Mining-1/Mining Q/ (screenshots)
│   └── Mining-10- pro-plus/Verus coin/
│
├── 04 - Research/
│   ├── Quantum Physics Dataset/ (۷ PDF)
│   └── SCOUT-B.md (Track B)
│
├── 05 - Media/
│   ├── TENTACLE-ALPHA_Architecture_Diagram.png
│   ├── TENTACLE-ALPHA_Competitor_Matrix_2027.png
│   ├── Pics/ (۵۸ عکس)
│   └── photos/ (۵ عکس)
│
├── data/photos/ (۵ عکس)
├── contracts/ (adapter.yaml)
└── _archive/ (shortcuts, caches)
```

---

## 7. source-of-truth hierarchy

```yaml
priority:
  1: "01 - Docs/10-Step Roadmap — Competitive Intel & Execution.md"
  2: "01 - Docs/Phase Status - Execution Plan & Prompt v2.0.md"
  3: "MANIFEST.yaml"
  4: "PROJECT.md"
  5: "VERDICT_QUEUE.md"
  6: "DecisionLog.md"
  7: "REGISTRY.md"
  8: "RUNBOOK.md"
  9: "Coin Scouting Framework.md"
  10: "contracts/adapter.yaml"
  context_only:
    - "Mining.md (لاگ تلگرام)"
    - "01 - Docs/TENTACLE-ALPHA-MINING_Hybrid_MegaPrompt_v3.0.md"
    - "01 - Docs/NEXT_AGENT_HANDOFF_MINING_PREEXEC_v1.0.md"
```

---

## 8. مسائل باز

```yaml
open_blockers:
  - hardware_inventory_unverified (MIN-V1 — مرحله ۳)
  - electricity_unknown (MIN-V2 — مرحله ۴)
  - wallet_seed_rotation_unresolved (Security Gate — بلندمدت)
  - hashrate_unmeasured (وابسته به ریگ فعال)
  - verdict_queue_3_remaining (V1, V2, V4 — بعد از مراحل ۳-۴)

safe_to_close_now:
  - MIN-V3: ORGANISM-STATE → nodes=0, hashrate=0 → ZERO mining active ✅
  - MIN-V5: REGISTRY → wallet_policy: zero agent access ✅
  - MIN-V6: RUNBOOK + adapter → autonomous_allowed: [] ✅
```

---

## 9. خروجی مدیریتی مورد انتظار

در پایان هر جلسه، ایجنت باید بدهد:

```yaml
project: Mining
mode: execution-phase-1 (leg active, verdicts closing)
execution_performed: false (read-only + proposals only)
files_created: []
files_updated: []
verdicts_closed: []
verdicts_remaining: []
mining_leg_status: read_from_ORGANISM_STATE
next_steps: []
security_confirmation: "no secrets, no SSH, no deploy, no execution"
```

---

## 10. یادآوری نهایی

> **الگوی اصلی = اختاپوس.** Mining Leg زیرمجموعه MYCELIAL organism است.
> همه قواعد MYCELIAL اعمال می‌شود.
> مراحل را بدون پرش طی کن.
> هر چیزی بدون evidence انسانی `unknown` بگذار.
> اگر شک داشتی، fail-closed کن و verdict request بده.
