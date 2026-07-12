---
type: reference
status: active
owner: آری
risk_level: low
autonomy_level: read-only
created: 2026-07-12
updated: 2026-07-12
created_by: agent
tags: [agents, registry, architecture, octopus, limb, olp-1, read-only]
sources:
  - "[[05 - Agents/Vault Cartographer]]"
  - "[[05 - Agents/AGENT_REGISTRY]]"
  - "[[04 - Architect System/architect/ARCHITECT_CHARTER]]"
aliases: ["Cartographer Limb", "Vault Cartographer OLP-1", "پای نقشه‌بردار"]
---

# Vault Cartographer — انطباقِ لیمب (OLP-1)

> «آروم آروم خودتو منطبقِ اختاپوس کن به‌عنوان یک پا.» این سند، ایجنتِ موجودِ [[05 - Agents/Vault Cartographer|Vault Cartographer]] را به قراردادِ لیمبِ OLP-1 نگاشت می‌کند. **Increment 1 = عضویتِ حکمرانی (documentation).** هیچ کد سیم‌کشی/deploy/تیک نمی‌شود — آن‌ها گام‌های بعدیِ گیت‌دارند (§روادمپ).

## یک‌خط
پای **فقط‌خواندنیِ نقشه‌برداری/ممیزیِ معماری** اختاپوس: از repoِ واقعی نقشهٔ لایه‌ای + شکاف‌های design↔reality را با citation تولید می‌کند و **فقط پیشنهاد** می‌دهد. کم‌ریسک‌ترین لیمبِ ممکن — صفر جهش، صفر اکشنِ بیرونی، صفر spend.

## قراردادِ لیمب (limb contract — OLP-1)
```yaml
limb_id: vault-cartographer
organ: CARTOGRAPHER            # فاقدِ organ در budgets.yaml (no-spend → incubating، مثل الگوی lead)
kind: read-model / audit-limb  # تیک‌نمی‌زند؛ on-demand است (برخلافِ ziman/lead که هر beat تیک می‌زنند)
parent_authority: "Architect/_ops"
owner: "آری"
risk_tier: R1 (low, contained)
autonomy_floor: read-only      # کفِ سخت — حتی وقتی گیت باز است عمداً همین می‌ماند
autonomy_ceiling: propose-only # سقف — فقط پیشنهادِ متنی برای ثبتِ انسان/مادر
execution_state: "ZERO mutation, ZERO outward — فقط map/report/propose"
control_surface:
  reads: "کل vault منهای .agentignore / _Duplicates / _Archive / secrets / هویتِ Project-F"
  emits:
    - "06 - Architecture Maps/MASTER-ARCHITECTURE-*.md (پیشنهادی)"
    - "پیشنهاد/گزارش در 00 - Inbox (propose-only)"
    - "memory candidate (provisional؛ canonical فقط با curator+مالک)"
  tools: [Read, Grep, Glob, Bash(بی‌ضرر)]   # بدونِ Write/commit/move/delete در حالتِ لیمب
hard_gated / forbidden:
  - "تغییرِ کد / charter / genome / policy / permissions"
  - "صدورِ verdict"
  - "هر اکشنِ خارجی (publish/send/spend/deploy/login)"
  - "echo از secret/کلید/seed یا هویت/پلتفرم/محتوای Project-F 🔒"
kill_switch: "§Security Gate (ROTATION_CHECKLIST) → autonomyِ مؤثر=read-only؛ + STOP-ORGANISM سراسری"
```

## عضویت در اختاپوس (وضعیتِ این Increment)
- ✅ ثبت در [[05 - Agents/AGENT_REGISTRY|AGENT_REGISTRY]] (ردیفِ `vault-cartographer` افزوده شد — مثلِ بقیه: phase-4، not-deployed).
- ✅ فهرست در [[05 - Agents/_Index - Agents|_Index - Agents]] (لیستِ فعال).
- ✅ واژگانِ limb/OLP-1 + `parent: Architect/_ops` صریح (همین سند).
- ✅ رفعِ ناسازگاریِ autonomy: floor=read-only / ceiling=propose-only (بدنهٔ شناسنامه).

## Anchor-Ledger contract (Increment 2 — تعریف‌شده، هنوز سیم‌نشده)
هر اجرای نقشه‌برداری باید یک ردِ ساختاریافته در Anchor Ledger بگذارد (قاعدهٔ سراسریِ AGENT_REGISTRY §۲: «هر اکشن = ورودیِ ledger»). قرارداد:
- **module/sink:** `_ops/events.py` → `state/events.jsonl` (append-only، content-free، scrubِ `_BANNED_ECHO`).
- **`agent_id`:** `vault-cartographer` · **event_names:** `task.started/completed/failed/blocked` + `approval.required`.
- **`enrich=true`:** زمینهٔ control-plane (owner/risk_tier) از `state/registry/registry-latest.json` می‌چسبد.
- **approval policy:** هر پیشنهادی که موضوعِ گیت‌دار را لمس کند → `approval_state=required` (هرگز auto).
- **content rule:** فقط عبارتِ عمومی + citation (file:line)؛ هرگز secret/هویت/محتوا.
- **binding status:** فقط **قرارداد** است؛ تماسِ واقعیِ `emit()` با code leg (گام ۳) می‌آید.
- قراردادِ ماشین‌خوانِ کامل: `05 - Agents/vault-cartographer.manifest.yaml` (فایلِ YAML — لینکِ ویکی نیست).

## چک‌لیستِ کاملِ‌بودنِ لیمب (OLP-1 §۱۱)
✅ Owner/Authority روشن · ✅ Source-of-truth (repoِ واقعی) · ✅ Risk tier (R1) · ✅ Hard gates · ✅ Autonomy floor/ceiling · ✅ Obsidian map (خروجیِ کانونی) · ✅ اتصالِ sanitised (propose-only، صفر echo)
✅ **Manifest ماشین‌خوان** (`vault-cartographer.manifest.yaml` — Increment 2) · ✅ **Anchor-Ledger contract** (binding تعریف‌شده — Increment 2)
✅ **code leg** `_ops/legs/cartographer_leg.py` + تست ۱۰/۱۰ (گام ۳؛ inert تا wiring)
⏳ wiring + tick در `_ops/wiring.py`+`organism.py` پشتِ `OCTOPUS_WIRE_CARTOGRAPHER` (گام ۴؛ emitِ زنده اینجا فعال می‌شود) · ⏳ ثبتِ verdictِ مالک برای «live» (گام ۵)

## روادمپِ «آروم آروم» (هر گام گیت‌دار)
1. **Increment 1 — عضویتِ حکمرانی (این جلسه، انجام‌شده):** registry row + index + limb-contract + parent + floor/ceiling. صفر کد، صفر deploy.
2. ✅ **گام ۲ — manifest + Anchor-Ledger contract (این جلسه، انجام‌شده):** `vault-cartographer.manifest.yaml` (ماشین‌خوان، zero-PII) + بایندینگِ ledger به `_ops/events.py` (قرارداد، نه emitِ زنده). §Anchor-Ledger contract بالا.
3. ✅ **گام ۳ — code leg (این جلسه، انجام‌شده):** `_ops/legs/cartographer_leg.py` (`CartographerLeg(Leg)` — سنتینلِ کهنگیِ نقشه: `default_packet` با allowlistِ باریک + `secrets=()` + `spawn=0` + budget 0، **بدونِ send/publish/pay**، `status_snapshot`/`map_staleness_check`(pure)/`propose_refresh`(proposal+ledger)/`tick`، emitter تزریق‌پذیر) + `_ops/tests/test_cartographer_leg.py` **۱۰/۱۰ سبز**. **inert:** هیچ ارجاعی در wiring/organism ندارد → در production اجرا نمی‌شود تا گام ۴. ledgerِ واقعی دست‌نخورده (۰ ورودی).
4. **گام ۴ — wiring + tick (گیت‌دار):** `make_cartographer_leg()` در `wiring.py` + (اختیاری) beatِ کم‌فرکانس برای «architecture-drift pulse». پشتِ flag، paper-first، یک هفته shadow.
5. **گام ۵ — activation:** فقط verdictِ صریحِ مالک + عبور از rotation/audit (قاعدهٔ deploy AGENT_REGISTRY §۴).

## چرا «پا»یِ درست، نه بیشتر
این لیمب on-demand و read-only است؛ الزامی به تیک‌زدنِ هر beat یا organ بودجه ندارد. الگوی امن = `lead` (incubating تا organ). هرگز خودش را deploy/activate نمی‌کند — این تصمیمِ L0 است. کفِ read-only حتی با گیتِ باز حفظ می‌شود (عمدی).
