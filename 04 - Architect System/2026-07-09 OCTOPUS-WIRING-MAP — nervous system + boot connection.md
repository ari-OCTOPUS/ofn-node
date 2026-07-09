---
type: architecture-plan
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
created_by: agent
sources:
  - "[[2026-07-09 CHRONO-GROUNDING-PLAN — design↔reality + roadmap + decision-gates]]"
  - "recon workflow wthvcewz9 + مطالعهٔ مستقیمِ organism.py/live_loop.py/wiring.py (HEAD≈605ce73)"
tags: [octopus, wiring, nervous-system, boot, coherence]
created: 2026-07-09
updated: 2026-07-09
---

# 🕸️ OCTOPUS WIRING MAP — عصب‌کشی + اتصالِ بوت

> پاسخ به نگرانیِ اصلیِ Ari: «وقتی مغزِ اصلی روشن می‌شود، تمامِ این هزار فایل باید به آن وصل باشند، وگرنه فایده‌اش چیست.» این نقشه، وضعیتِ **واقعیِ** اتصال + معماریِ **هدف** + طرحِ رساندنِ کد به آن را می‌دهد. اپیستمیک: 【E】کد · 【P】طراحی.

---

## ۰. یافتهٔ محوری — چرا الان «وصل» نیست

**دو مغزِ نامتصل:**
- `organism.py::main()` — مغزِ **در حالِ اجرا** (تنها entrypointِ واقعی). بوت: pacemaker + per-tick: neural_beat، doctor_beat، epoch، fitness، germline، heartbeat.
- `live_loop.py::LiveLoop` — ارکستراسیونِ **غنی** (bus + legs/doctor/box/rhythm/spectral/sensory/telegram publish/subscribe + Project-F + verdictِ آری). **هیچ‌چیز آن را instantiate/run نمی‌کند** → shelfware.

**سه لایهٔ نقص (به‌ترتیبِ شدت):**
1. 🔴 **`organism.py` و `LiveLoop` وصل نیستند** — مغز حلقهٔ لخت می‌زند؛ بدنِ غنی (bus/legs/handlers) بی‌کاربر.
2. 🔴 **ماژول‌های ساخته‌شده در مسیرِ زنده نیستند:** `evolution.py`، `box/`، `canonical_consolidation`، `school_bridge`، `sensory_bus` — نه در boot، نه در tick.
3. 🟠 **built-and-discarded:** `make_lead_leg()` و `make_unified_bus()` در organism صدا زده می‌شوند ولی **return دور ریخته می‌شود** → حتی با flag، در tick رانده نمی‌شوند.
4. 🟠 **همهٔ ۶ flag پیش‌فرض خاموش** (`flag()` = env=="1") → بوتِ عادی = حلقهٔ متابولیکِ لخت. حتی wiredها فایر نمی‌کنند.

جدولِ flagها (همه پیش‌فرض OFF): `OCTOPUS_WIRE_DOCTOR · _NEURAL · _UNIFIED · _LEAD · _SCHOOL · _TELEGRAM`. غایب از boot اصلاً: consolidation، evolution، box.

---

## ۱. معماریِ هدف — عصب‌کشیِ واحد (نخاع = UnifiedBus)

بوتِ مغز → **یک حلقه، یک bus، همه‌چیز وصل.** organism (زمان‌محور) نخاع (UnifiedBus) را می‌سازد و LiveLoop (رویداد‌محور) رویش سوار می‌شود؛ هر ماژول publish/subscribe می‌کند.

```
                     ❤️ chrono pacemaker (beat)  ← زمان، همه را می‌راند
                                │ beat
        ┌───────────────────────┼───────────────────────────────┐
        │            🧠 organism.main()  +  🕸️ UnifiedBus (نخاع)   │
        │  per beat:  publish(beat) → همهٔ subscriberها فایر       │
        └───────────────────────┼───────────────────────────────┘
   ┌──────────────┬─────────────┼──────────────┬─────────────────┐
   ▼ آوران        ▼ شناخت       ▼ نظارت        ▼ آوندِ اثر         ▼ ریتم
 sensory_bus    neural(۸)     doctor.run_cycle  legs (propose)   rhythm/
   → bus        + canonical_   + evolution      → proposal        spectral
   → school_     consolidation  + box(B3)        → cockpit/tel     (advisory)
   bridge(یاد)   (هر N beat)    (advisory)       → verdictِ آری
        │            │             │               → EffectorGate.settle
        └────────────┴─────────────┴───── همه advisory/propose-only ──┘
                                                   │ (money/live فقط با
                                                   ▼  capability∧approval)
                                            ❤️ genome ledger (قلب، human-append)
```

**اصولِ حاکم (تغییرنکردنی):** همه propose-only · effector فقط با human-append + capability_gate · fail-closed · additive · بدونِ ledgerِ موازی. **wiring هیچ walleی را باز نمی‌کند** — فقط ماژول‌های ساخته‌شده را به bus وصل می‌کند تا مغز از بدن استفاده کند.

---

## ۲. profileِ بوت — تصمیمِ کلیدی (طراحیِ من)

به‌جای ۶ flagِ پراکندهٔ پیش‌فرض‌خاموش، **یک سوئیچِ profile:**

| profile | چه روشن است | کاربرد |
|---|---|---|
| `bare` | فقط متابولیک (رفتارِ فعلی) | debug/emergency |
| **`paper-full`** (پیش‌فرضِ نو) | **همهٔ wiringِ امن ON**: neural + consolidation + school + sensory + doctor(+evolution+box) + unified + legs(propose-only، incubating) | **حالتِ عادی** — مغز از کلِ بدن استفاده می‌کند، $0، صفر مسیرِ پول |
| `live` | paper-full + effectorهای پول | فقط با capability∧LIVE_ENABLED∧approval + تاریخ |

`OCTOPUS_PROFILE=paper-full` پیش‌فرض شود. money/live **جدا و همچنان capability-gated** می‌ماند (profile آن را باز نمی‌کند). نتیجه: **بوتِ عادی = کلِ بدنِ امن روشن و وصل.**

---

## ۳. شکاف‌های اتصال → پرامپت‌ها (GROUP W در BUILD-PROMPTS)

| # | اتصالِ گمشده | پرامپت | وضعیت |
|---|---|---|---|
| W1 🔴 | organism ↔ LiveLoop/UnifiedBus (نخاع) — return دور ریخته را نگه‌دار، bus را بساز و per-tick publish کن | P-W1 | ready |
| W2 🔴 | sensory_bus → bus → school_bridge.learn_from در حلقهٔ زنده (آوران واقعی) | P-W2 | ready |
| W3 🔴 | profileِ بوت (`OCTOPUS_PROFILE=paper-full` پیش‌فرض؛ money جدا) | P-W3 | ready |
| W4 🔴 | **connection self-test:** بوتِ paper-full → assert هر ماژول ≥۱ بار fire کرد | P-W4 | ready (اثباتِ «همه وصل») |
| — | consolidation → tick | P-M2 | **GLM در حالِ انجام** |
| — | evolution → doctor.run_cycle | P-N1 | ready |
| — | box B3 → doctor | P-N2 | ready |
| — | legs رانده‌شده در tick (نه discard) | P-L1 | ready |

**ترتیب:** P-M2 (جاری) → **P-W1 (نخاع، مهم‌ترین)** → W2/N1/N2/L1 (ماژول‌ها روی نخاع) → W3 (profile) → **W4 (self-test = اثبات)**. بعد از W4، بوت = همه‌چیز وصل، با یک تستِ رفتاری که ثابتش می‌کند.

---

## ۴. معیارِ «تمام» (پاسخِ نهایی به «وگرنه فایده‌اش چیه»)
بوتِ `organism.py` در `paper-full` → `connection self-test` (P-W4) سبز = هر یک از این‌ها در ≥۱ beat واقعاً fire کرد: sensory→school · neural · consolidation · doctor(+evolution+box) · legs(proposal) · rhythm/spectral advisory · unified bus. تا این تست سبز نشود، «وصل» یک ادعاست نه واقعیت.

---

## ۵. اینونتوریِ کاملِ orphanها (ممیزیِ اتصال — ۷۱ ماژول → ۲۱ shelfware)

> یک ممیزیِ فقط‌خواندنیِ کلِ `_ops` هر ماژول را طبقه‌بندی کرد (wired-boot / flag-gated / support-lib / **shelfware** / alt-entrypoint / test-only). ۲۱ ماژول shelfware‌اند (ساخته+تست، بی‌مسیرِ زنده). این جدول disposition هرکدام را می‌دهد تا **هیچ‌کدام بی‌تکلیف نماند**:

| shelfware | disposition |
|---|---|
| `live_loop.py` · `brain/cockpit.py` · `unified_bus.py`* | **P-W1** (نخاع؛ *unified_bus هم flag-gated و هم return-discard است) |
| `afferent/sensory_bus.py` | **P-W2** |
| **کلِ خوشهٔ `doctor/box/` (۱۲ فایل:** box, b3_bridge, b4_fusion, falsif_harness, agent_state, dynamics, archivist, topology, warden, sensors, null_dreamer, __init__**)** | **P-N2 (گسترش‌یافته):** box.py در run_cycle instantiate + step روی trace → b3_bridge.box_to_doctor_pipeline → مسیرِ propose-onlyِ doctor؛ b4_fusion=novelty، falsif=کنترلِ دوره‌ای. بقیه support-libِ box‌اند → با wire‌شدنِ box.py خودکار reachable |
| `germline.py` (CRIT-tier alarm + retry بی‌مصرف؛ tick از `opslib.germline_lag_hours` inline استفاده می‌کند) | **P-W5 (نو)** |
| `checkpoint.py` (per-beat checkpoint/replay بی‌مصرف؛ unified_bus نسخهٔ تکراریِ خودش را دارد) | **P-W6 (نو)** |
| `doctor/spectral.py` (`spectral_mine` در run_cycle صدا زده نمی‌شود) | **P-W7 (نو)** |
| `budget/money_gate.py` | **عمداً deferred تا فاز live** (D-32؛ money قفل — از `capability_gate.require` قابلِ‌رسیدن است ولی چون spend رخ نمی‌دهد dormant است). **gap نیست.** |

**نتیجه:** پس از GROUP W (W1/W2/W3/W4) + N1/N2(گسترش)/L1 + W5/W6/W7، **هر ۲۱ shelfware یا وصل می‌شود یا عمداً deferred است** → هیچ فایلی بی‌دلیل جا نمی‌ماند. `P-W4` (connection self-test) اثباتش می‌کند.

**نوتِ خواهر:** پرامپت‌ها → [[octopus-build-prompts/CHRONO-BUILD-PROMPTS — grounded]] (GROUP W + W5/W6/W7). گراندینگ → [[2026-07-09 CHRONO-GROUNDING-PLAN — design↔reality + roadmap + decision-gates]].
