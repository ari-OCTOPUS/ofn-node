---
type: architecture
status: draft
tags: [control-plane, governance, urcp, reconciliation, backlog, architecture]
created: 2026-07-11
updated: 2026-07-11
created_by: agent
sources:
  - "تحلیلِ بیرونیِ «Unified Runtime Control Plane برای CHRONOS-FABLE-OS» (مالک، ۲۰۲۶-۰۷-۱۱)"
  - "[[06 - Architecture Maps/MASTER-ARCHITECTURE-2026-07-09]]"
  - "[[06 - Architecture Maps/2027 Standards Base & Backlog]]"
  - "[[06 - Architecture Maps/AUDIT-MATRIX-self-improvement-2026-07-10]]"
  - "[[06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged]]"
  - "کدِ زنده: _ops/vault_updater*, _ops/cortex/auto_approve, _ops/epistemics/*, _ops/heart/replay_s, _ops/cortex/ignition_softwta"
---

# انطباقِ URCP با معماریِ فعلی — بدونِ حذف، بدونِ بازنویسی (فقط پیشنهاد)

> رأی مالک: «تحلیلِ بیرونی را چک کن، بگو با معماریِ الان چطور منطبق کنیم؛ چیزی حذف و بازنویسی نشه.»
> حکمِ کلی: **تحلیل جدی و هم‌جهت با مسیرِ فعلی است — ~۶۰٪ش را از قبل ساخته‌ایم** (با اسم‌های دیگر)، ~۲۵٪ش گپِ واقعیِ ارزشمند است (registry/manifest/conformance-score)، و ~۱۵٪ش برای سیستمِ تک-مالکِ local-first فعلاً زیادی است (NHI rotation، dual-control، NATS/Postgres). هیچ‌چیزِ آن نیازمندِ بازنویسی نیست — نگاشتِ additive کامل ممکن است.

## ۱. جدولِ انطباق — «URCP چه می‌خواهد» در برابرِ «ما چه داریم»

| مؤلفهٔ URCP | معادلِ موجود (کد/سند) | وضعیت | اقدامِ additive (بدونِ بازنویسی) |
|---|---|---|---|
| Vault Gateway (تنها مسیرِ write) | `vault_updater.py` (proposer، هرگز دیسک) + `vault_updater_gate.py` (validator ِ مستقل) + EffectorGate + LAYER_MAP (Ring×risk) | 🟢 ساخته | همین بماند؛ URCP فقط اسمِ جدیدِ همین است |
| Policy ladder (allow/restrict/require_human/shadow_only/deny) | `auto_approve.py` (خطِ قرمزِ سخت: کد/پول/spawn/secret/ژنوم/schema/human-append/kill-switch/σ/merge = همیشه مالک) + خانهٔ آره/نه + LAYER_MAP | 🟢 ساخته | نگاشت: allow≈AUTO(LOW+envelope) · restrict≈knob-bounded · require_human≈GATE · shadow_only≈فلگ‌خاموش/سایه · deny≈HOLD |
| Hard gates قبل از scoring | kill-switch، σ≤1، تِینتِ σ در control_law، سقفِ AU$30، capability-marker با fingerprint، live-gate تاریخ/فلگ، HMAC ِ human-append | 🟢 ساخته (گافِ شناختهٔ #۱: fail-open ِ بی‌سکرت — رأی مالک باز ماند) | — |
| Evidence ledger + hash chain | `epistemics/emit.py` (prev_hash+sha256)، ledger ژنوم، `code_sha256` ِ sim | 🟢 ساخته | — |
| DecisionReplay (deterministic) | **همین جلسه ساخته شد:** `heart/replay_s.py` (counterfactual + reason_codes + گزارشِ کالیبراسیون) و `cortex/ignition_softwta.shadow_compare` (winner_current vs shadow + disagreement) | 🟢 ساخته برای heart/ignition | تعمیم به دامنه‌های دیگر = فازبندیِ خودِ URCP |
| CognitionReplay (drift-grade، نه promise ِ بازتولید) | گپ | 🟡 | فقط وقتی LLM-loop ِ پولی روشن شد؛ فعلاً موضوعیت ندارد ($0-local) |
| HEART = regulator نه commander | ADR-001 coupled-not-merged + `stress.py` (ترس→مکثِ خود-تغییری = دقیقاً «stress>0.75 → restrict» ِ URCP) + innervation + heartbeat | 🟢 ساخته | HeartState envelope = یک adapter ِ read-only که سه فایلِ state موجود را جمع کند (پیشنهاد #۱۲) |
| EventEnvelope | `events.py` (schema ِ صریح: trace_id/agent_id/event_name/status/approval_state/…) | 🟢 نیمه | فیلدهای اختیاریِ schema_version/correlation_id/idempotency_key — backward-compatible (پیشنهاد #۱۱) |
| Doctor = auditor/proposer، تکاملِ governed | RFC ِ propose-only + evolution ِ paper-full (جهش sandbox→RFC→merge با مالک) + AUDIT-MATRIX | 🟢 ساخته | «AUDIT row → Detector+Policy+Test» = ایدهٔ خوب، backlog |
| Scout fleet با authority کم | `web_research.py` ($0، read-only، بیرونِ مسیرِ پول) + scout-digests ِ propose-only در Inbox | 🟢 ساخته (C0–C2) | — |
| Financial: money همیشه human-gated، dual-truth ledger | organ_gate→budget_gate (سقفِ AU$30) + attribution/reconcile (CONFIRMED فقط با actor=reconcile) + خانهٔ آره/نه | 🟢 ساخته | dual-control برای تک-مالک بی‌معناست — نگیریم |
| Registry + entity manifest + logical_id | `AGENT_REGISTRY.md`، `SYSTEM_MAP`، `Vault Cartographer` (سند/ایجنت — runtime نیست) | 🔴 **گپِ واقعیِ اصلی** | **پیشنهاد #۱۰ — Phase-0 ِ URCP: manifest ِ YAML per پروژه/ایجنت + اسکنرِ read-only + snapshot ِ registry + کارتِ داشبورد. فایلِ نو فقط، $0** |
| Capability lease (انقضادار) | فلگ‌های ACTIVATION-*.flag (حذف = لغو) — بدونِ expiry | 🟡 | فیلدِ `expires_at` روی manifest ِ #۱۰ + چکِ advisory در auto_approve (فلگ-خاموش) — نه ماشینِ lease ِ کامل |
| Conformance engine + score | `validate_frontmatter.py` + validatorها + capability gate | 🟡 | conformance_score = خروجیِ عددیِ همان validatorها روی manifestها (داخلِ #۱۰) |
| Incident entity + containment | `task.blocked` + alerts + ترسِ stress + قرنطینهٔ chrono | 🟡 | رکوردِ Incident = نوعِ رویدادِ جدید در events.py (additive) — پیشنهاد #۱۳ |
| Single-pane UI (exception-driven) | خانهٔ سادهٔ آره/نه + `8773/ops` (Now/گیرکرده/KPI) | 🟢 ساخته | کارتِ registry از #۱۰ به همان داشبورد اضافه شود |
| unknown → restrict (ASSUMPTION 5) | fail-closed ِ قلب روی ورودیِ غایب/کهنه (استراحتِ MAX) + HOLD ِ بی-provenance در vault_updater | 🟢 همین فلسفه | — |
| L0–L3 canonical (ASSUMPTION 4) | RATIFIED-TASKS | 🟢 | ARI سه‌بعدی = سه فیلدِ اختیاری روی AGENT_REGISTRY/manifest — additive |

## ۲. هم‌گرایی‌های مستقل (اعتبارِ متقاطع)

تحلیلِ بیرونی به چند چیزی رسیده که ما این هفته **مستقل و با داده** به‌شان رسیدیم — این هم‌گرایی سیگنالِ خوبی است: shadow-first قبل از live (فازِ replay ِ ما)، evidence/hash-chain (epistemics)، decision-replay ِ audit-grade (replay_s)، «توجه/استرس = تعدیلِ ریسک نه فرمانده» (ترسِ stress + boost ِ اشباع‌شوندهٔ softwta)، و مرزِ معرفتیِ «consciousness-inspired ولی governance-only» که دقیقاً خطِ قرمزِ access-only ِ ماست.

## ۳. واگرایی‌ها — کجا URCP را نگیریم یا تغییرش بدهیم

- **«control plane down → fail-closed for writes» ِ عمومی:** با فلسفهٔ مصوبِ مالک («safety-first ِ خشک نه؛ fail-closed فقط پول/خارجی») نمی‌خواند. انطباق: قاعدهٔ موجود حاکم بماند — پول/خارجی fail-closed، ارگانیسمِ داخلی fail-soft. URCP اینجا override می‌شود.
- **«همهٔ actionها فقط از gateway» به‌صورتِ یک‌جا:** اجرای کاملش = بازنویسیِ سیم‌کشیِ کلِ ارگانیسم (نقضِ صریحِ «بازنویسی نشه»). انطباق: **قانونِ gateway-first فقط برای مسیرهای نو**؛ مسیرهای موجود دست‌نخورده؛ مهاجرتِ هر مسیرِ قدیمی = رأیِ جداگانهٔ مالک.
- **ماشین‌آلاتِ enterprise (NHI rotation، dual-control، NATS/Redpanda/Postgres، exactly-once ِ توزیع‌شده):** برای تک-مالکِ local-first premature است — برچسبِ تریاژ: emerging/ops-heavy، backlog ِ دوردست، نساز.
- **نامِ CHRONOS-FABLE-OS:** به‌عنوانِ alias در [[06 - Architecture Maps/LANGAR-ALIAS-REGISTRY|LANGAR]] ثبت شود (فقط پیشنهاد)؛ تغییرِ canonical طبق خودِ URCP = require-human.
- **جدولِ ۹ فازِ مهاجرت با exit-criteria:** ساختارش خوب است ولی دروازه‌بندیِ ما از قبل سفت‌تر است (shadow→replay→رأی مالک، مثلِ S-batch). انطباق: فازهای URCP روی همان الگوی اثبات‌شدهٔ S-batch سوار شوند، نه برعکس.

## ۴. تریاژِ معرفتی خودِ تحلیل

- **FACT (بگیر):** gateway-first برای مسیرهای نو، registry/manifest، policy-trace با reason_codes، decision-replay، write-ahead ِ اجرا در gatewayهای پولی، unknown→restrict.
- **EMERGING (پشتِ فلگ/سایه):** conformance_score عددی، capability expiry، HeartState envelope رسمی، Incident entity، ARI سه‌بعدی.
- **HYPE/premature (نگیر فعلاً):** NHI/credential rotation، dual-control، صفِ پیامِ توزیع‌شده، cognition-replay ِ گسترده، UI ِ جدا (داشبوردِ موجود کافی است).

## ۵. نقشهٔ انطباقِ additive — سه قدم، همه پشتِ رأی مالک

**پیشنهاد #۱۰ — Phase-0 Registry (پیش‌نیازِ همهٔ بقیه):** `chronos.entity.yaml` برای هر پروژهٔ `03 - Projects` + `agent.manifest.yaml` برای ایجنت‌های `05 - Agents` (فیلدها: logical_id، owner، risk_tier، allowed paths، capabilities، ARI، همه با پیش‌فرضِ unknown) + اسکنرِ read-only (`_ops/registry_scan.py`) که snapshot ِ `state/registry/registry-latest.json` بسازد + کارتِ داشبورد. **فایلِ نو فقط، $0، صفر تغییرِ رفتار.** خروجی‌اش همان دیدِ «همه‌چیز از یک پنجره» است که خواسته‌ای.

**پیشنهاد #۱۱ — غنی‌سازیِ EventEnvelope:** سه فیلدِ اختیاریِ `schema_version/correlation_id/idempotency_key` در `events.emit` (backward-compatible؛ خواننده‌های فعلی نمی‌شکنند).

**پیشنهاد #۱۲ — HeartState adapter (سایه):** تابعِ read-only که stress/innervation/heart-shadow را در یک envelope جمع کند و فقط با فلگ در `state/heartstate-latest.json` بنویسد — همان «HEART از روزِ صفر telemetry بدهد» ِ تحلیل، بدونِ commander شدن.

**پیشنهاد #۱۳ — رکوردِ Incident:** نوعِ رویدادِ `incident.opened/contained` در events.py + نمایش در `8773/ops` (additive).

ترتیبِ درست همان حرفِ تحلیل است: **اول #۱۰ (دید)، بعد #۱۱–۱۳ (قراردادها)، بعد — فقط اگر خواستی — مهاجرتِ تدریجیِ مسیرهای قدیمی به gateway، هرکدام با رأیِ جدا.** هیچ‌کدام حذف/بازنویسی ندارد؛ همه فایلِ نو یا فیلدِ اختیاری‌اند.

---
*جلسهٔ ۴۸ ادامه (۲۰۲۶-۰۷-۱۱) — بررسیِ تحلیلِ بیرونیِ URCP به‌دستورِ مالک. هیچ‌کدام از پیشنهادهای #۱۰–۱۳ ساخته نشده‌اند — منتظرِ رأی.*
