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
✅ **wiring + seam** `make_cartographer_leg`/`cartographer_beat` در `wiring.py` + seamِ organism + تست ۶/۶ + ثبت در `run_all` (گام ۴؛ پشتِ `OCTOPUS_WIRE_CARTOGRAPHER`، **default-off**)
⏳ **activation (گام ۵ — فقط verdictِ مالک، کد نیست):** ست‌کردنِ `OCTOPUS_WIRE_CARTOGRAPHER=1` (یا افزودن به PAPER_FULL_FLAGS) + rotation/audit. تا آن، seam در production خاموش/None است.

## روادمپِ «آروم آروم» (هر گام گیت‌دار)
1. **Increment 1 — عضویتِ حکمرانی (این جلسه، انجام‌شده):** registry row + index + limb-contract + parent + floor/ceiling. صفر کد، صفر deploy.
2. ✅ **گام ۲ — manifest + Anchor-Ledger contract (این جلسه، انجام‌شده):** `vault-cartographer.manifest.yaml` (ماشین‌خوان، zero-PII) + بایندینگِ ledger به `_ops/events.py` (قرارداد، نه emitِ زنده). §Anchor-Ledger contract بالا.
3. ✅ **گام ۳ — code leg (این جلسه، انجام‌شده):** `_ops/legs/cartographer_leg.py` (`CartographerLeg(Leg)` — سنتینلِ کهنگیِ نقشه: `default_packet` با allowlistِ باریک + `secrets=()` + `spawn=0` + budget 0، **بدونِ send/publish/pay**، `status_snapshot`/`map_staleness_check`(pure)/`propose_refresh`(proposal+ledger)/`tick`، emitter تزریق‌پذیر) + `_ops/tests/test_cartographer_leg.py` **۱۰/۱۰ سبز**. **inert:** هیچ ارجاعی در wiring/organism ندارد → در production اجرا نمی‌شود تا گام ۴. ledgerِ واقعی دست‌نخورده (۰ ورودی).
4. ✅ **گام ۴ — wiring + seam (این جلسه، انجام‌شده):** `make_cartographer_leg()` + `cartographer_beat()` در `_ops/wiring.py` (پشتِ `OCTOPUS_WIRE_CARTOGRAPHER`، **عمداً در PAPER_FULL_FLAGS نیست → default-off**)؛ seamِ organism (init/build/beat/state-write، mirrorِ ziman، None-guarded → در production inert تا flag)؛ `_ops/tests/test_cartographer_wiring.py` **۶/۶ سبز** + ثبت در `run_all` (leg+wiring). organism/wiring هر دو parse سالم؛ ziman دست‌نخورده (فقط افزودن).
5. **گام ۵ — activation (فقط مالک، کد نیست):** `OCTOPUS_WIRE_CARTOGRAPHER=1` (یا افزودن به PAPER_FULL_FLAGS) + rotation/audit + per-domain verdict (قاعدهٔ deploy AGENT_REGISTRY §۴). اینجاست که `emit()`ِ زنده و beatِ واقعی روشن می‌شود.

## چرا «پا»یِ درست، نه بیشتر
این لیمب on-demand و read-only است؛ الزامی به تیک‌زدنِ هر beat یا organ بودجه ندارد. الگوی امن = `lead` (incubating تا organ). هرگز خودش را deploy/activate نمی‌کند — این تصمیمِ L0 است. کفِ read-only حتی با گیتِ باز حفظ می‌شود (عمدی).

## Step 5 — Activation readiness + go-live runbook (owner-gated)
> **ایجنت این را اجرا نمی‌کند.** فلیپِ فلگ = عملِ deployِ L0 (self-approval توسطِ خودِ لیمب طبقِ manifest/`AGENT_REGISTRY` ممنوع است). این بخش = بخشِ «audit»ِ قابل‌انجامِ گام ۵ + دستورِ دقیقِ فعال‌سازیِ مالک.

### Readiness audit (agent-attested, read-only)
- ✅ کد کامل (increments ۱–۴)؛ `organism.py`/`wiring.py`/`cartographer_leg.py` همه `ast.parse` سالم؛ تست‌ها سبز (leg ۱۰/۱۰، wiring ۶/۶).
- ✅ ایمنی: بدونِ send/publish/pay؛ incubating (بدونِ organ/بودجه)؛ content-free؛ read-only floor؛ STOP/HALT مقدم؛ seam با None-guard.
- ✅ inert-by-default: فلگ در PAPER_FULL_FLAGS نیست → با فلگِ خاموش، `make_cartographer_leg()=None` → beat رد. سطحِ فعالِ واقعی = فقط یک بلوکِ `cartographer` در ORGANISM-STATE؛ **beat هیچ ledger emit/mutate ندارد** (فقط `propose_refresh`ِ on-demand می‌نویسد، که حلقه صدایش نمی‌زند).
- ⏳ پیش‌شرط‌هایی که ایجنت attest نمی‌کند (مالک/ops): چرخشِ secret (ROTATION_CHECKLIST) · verdictِ per-domain.

### فعال‌سازی (مالک — یک عمل، برگشت‌پذیر)
- **گزینهٔ A (توصیه‌شده، per-run، کم‌ترین commitment):** در محیطِ launchِ organism `OCTOPUS_WIRE_CARTOGRAPHER=1` را ست کن و organism را restart کن. **rollback:** متغیر را unset + restart.
- **گزینهٔ B (پایدار، default-on هر بوت):** خطِ `"OCTOPUS_WIRE_CARTOGRAPHER",` را به `PAPER_FULL_FLAGS` در `_ops/wiring.py` اضافه کن. **rollback:** همان خط را حذف کن.

### پس از فعال‌سازی (یک هفته shadow)
1. بعد از restart: `_ops/state/ORGANISM-STATE.json` باید کلیدِ `cartographer` (status، `propose_only:true`, `read_only:true`) داشته باشد.
2. `_ops/state/events.jsonl`: نباید ورودیِ غیرمنتظره‌ای از `vault-cartographer` ببینی (beat emit نمی‌کند).
3. هر رفتارِ ناخواسته → rollback (unset/حذفِ خط) + در صورتِ لزوم `_ops/STOP-ORGANISM`.
4. تستِ رگرسیون: `python -m pytest _ops/tests/test_cartographer_wiring.py _ops/tests/test_cartographer_leg.py -q` (باید ۱۶/۱۶ بماند).
