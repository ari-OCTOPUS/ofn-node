---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, prompt, cockpit, dashboard, claude-design]
created: 2026-07-10
updated: 2026-07-10
created_by: agent
---

# 🐙 پرامپت Claude Design — کابین بازرسی کامل اکتاپوس (System-Check Cockpit)

## طرز استفاده (۳ قدم)

1. **بستهٔ وضعیت را تازه کن:** `python -X utf8 F:\backup\_ops\export_status.py` → خروجی: `F:\backup\_ops\state\export\octopus-status-bundle.json` (بدون secret؛ پروفایل خصوصی عمداً غایب).
2. در **Claude Design**: قالب **Prototype**، مدل Opus 4.8، بعد کل بلوک پرامپت پایین را در جعبهٔ «Describe an app idea» بچسبان.
3. با دکمهٔ **+** فایل `octopus-status-bundle.json` را ضمیمه کن (یا بعد از ساخت، در خود اپ paste کن). هر بار خواستی چک کنی: قدم ۱ را تکرار کن و فایل تازه را در اپ بارگذاری کن.

> نکته: اپ کاملاً آفلاین/فقط‌خواندنی است — هیچ کنترلی روی ارگانیسم ندارد و نباید داشته باشد (kill-switch فقط فایل محلی `_ops/STOP-ORGANISM` است، نه هیچ UI بیرونی).

---

## پرامپت (از اینجا تا انتهای فایل را کپی کن)

```
Build "Octopus Mission Control" — a single-file, fully self-contained, READ-ONLY health-inspection cockpit web app for a live autonomous system called Octopus. No backend, no external CDNs/fonts/network calls. All CSS/JS inline. It must render perfectly offline.

# WHAT OCTOPUS IS (context for good copywriting inside the app)
Octopus is a 24/7 "digital organism" running on the owner's Windows machine: a metabolism (budget governor, all $0 shadow until a live-gate opens on 2026-07-21), a heart (pacemaker/beats), a doctor (self-improvement RFCs that ALWAYS need a human tap to merge), neural memory (consolidation + BCM forgetting + sparse input filter + shared latent space), a school (awareness per cell), legs (propose-only workers), and a Telegram human-approval channel. Everything dangerous is behind human gates. This app's ONLY job: take a status-bundle JSON and show the owner, at a glance, whether the whole system is healthy — and exactly what needs attention.

# INPUT
The app accepts a JSON "status bundle" three ways:
1. File upload (drag & drop + file picker),
2. Paste into a textarea,
3. A "بارگذاری نمونه" (Load Sample) button with the embedded sample below.
Parse defensively: EVERY top-level key may be null or missing (e.g. modules not yet activated) — render a neutral "هنوز داده ندارد" chip instead of crashing. Never mutate the data.

# BUNDLE SCHEMA (top-level keys)
- _meta: {generator, bundle_version, note, generated_at}
- organism_state: {ts, started, epoch_mode, halted (null=ok, string=reason), frozen (bool), stop_organism (bool), month{key, musd, usd, aud}, today{musd, usd}, suspect_zero_total (int), conflicts (array — MUST be empty), germline_lag_h (float, hours since last off-box backup), germline_alert, optionally: wiring{wire_*: bool, profile, doctor_every_n, consolidation_every_n}, leg{leg_id, hlc, money_link, proposals_emitted}, cardiac{...}, protective_skip (bool), fitness_authoritative, sigma, sigma_zone}
- fitness: {ts, authoritative (bool — stays false until 28 days of experience data), experience_span_days, authoritative_note, acceptance_source, integrity_alerts (array), attribution{revenue_by_cell, coverage, claimed, confirmed}, cells{<biz>: {sent, rejected, failed, acceptance_rate, judged, tokens, efficiency, waste, fitness} or {excluded: true, reason}}, weights{value, urgency, efficiency, human, waste}}
- replication: {sigma{sigma_effective (must be ≤ 1.0), zone, spawn_proposed, spawn_approved, parents, alerts}, ...}
- telemetry: per-organ spend snapshot (micro-USD) — all zeros in shadow mode
- school_awareness: {awareness{C01..C03, E01..E03: 0..1}, mean}
- channel_status: Telegram channel state or null (null = token not configured yet)
- fisher: null OR {ts, cells_used, fisher_condition_number (finite or null), current_weights, advisory_weights, natural_step, eta, eps, advisory_only: true, authoritative: false, numpy_used, note}
- chamber_temperature: null OR {ts, T, explore, merge_rate, stagnation}  // T must be within [0.2, 1.5]
- bcm_weights_summary: null OR {step, beta, count, saturation_of_512 (must be ≤ 1.0), strongest_10: array of [key, w] pairs, weakest_10: same}
- latent_summary: null OR {total, by_layer{layer: count}}
- sparse_summary: null OR {tracked_keys}
- phase_metrics: array of pre-registered metric records {phase, ts, registered_before_implementation (bool), metrics{...}, rollback, gate} — phases blueprint-phase-3-bcm/4-sparse/5-chamber-temperature/6-fisher + one honest retroactive record for phases 0-2
- phase_reviews: array of {phase_id: "phase-0".."phase-6", review_type: PHASE_RESULT|AUDIT_REPORT|ROADMAP, ts, payload{summary, tests, ...}, verdict: "approved"|"rejected"|"needs-revision"|null, verdict_ts, verdict_note, _file}
- consolidation_summary: {cycles (int), last{cycle, insights[], verified_sources[], discarded_sources[], timestamp, latent_vector?, bcm_*?, sparse_*?}}
- governor_alerts_tail: last ~30 raw lines of the ops alert log (markdown-ish: "## <iso-ts> (metabolism)" headers + "- message" lines)
- chrono: {exists (bool — chrono.db present), heartbeats, gated_effects, duration_markers, effects_by_status{status: count}, rfc_verdicts_total, rfc_verdicts_tail[{rfc_id, verdict, bottleneck_key, ts}]}
- genome_ledger: {exists, records (int), verify_scars (string like "OK: ok-with-scars: 1 torn-but-anchored record(s) at line(s) [40]"), verify_scars_ok (bool)}
- organ_table: {ORGAN_NAME: budget-info} — organ registry from budgets.yaml
- epochs: {count, latest{...}}

# LAYOUT — 8 tabs (RTL, Persian labels, English technical terms kept as-is)
Header (always visible): big status pill — 🟢 زنده / 🟡 کهنه (stale) / 🔴 متوقف — computed from rules R1-R4 below; organism uptime (now − started); "تازگی داده: X دقیقه پیش" from organism_state.ts; overall health score (0-100, from the rules engine) as a ring gauge; bundle generated_at.

Tab 1 «نمای کلی» (Overview): traffic-light cards for the vital signs — halted/frozen/stop, month & today spend in AUD with a "قفل زنده تا 2026-07-21" countdown, suspect_zero, conflicts, germline lag (thresholds below), σ_effective gauge vs the hard 1.0 line, school mean-awareness, protective_skip. Below: the full health-check table (all rules, each row: name / status ✅⚠️⛔ / evidence value / hint in Persian).

Tab 2 «بلوپرینت» (Blueprint P0-P6): a 7-column phase board built from phase_reviews. Per phase: PHASE_RESULT summary, verdict badge (approved=green, null=amber "منتظر رأی مالک", rejected=red), verdict_note tooltip, AUDIT/ROADMAP presence dots. Under it, phase_metrics cards: pre-registered badge (registered_before_implementation ? "پیش‌ثبت ✅" : "retroactive — صادقانه"), each metric's definition + accept criteria.

Tab 3 «حافظه و مغز» (Memory/Neural): consolidation cycles count + last insights list (Persian strings) + verified vs discarded sources; BCM card (β, step, count, saturation bar of 512 with ≤1.0 marker, strongest/weakest 10 keys as two small tables) or "BCM هنوز اجرا نشده — منتظر restart"; sparse card (tracked_keys) or inactive chip; latent space counts by layer as a small bar chart.

Tab 4 «دکتر و تکامل» (Doctor/Evolution): chamber_temperature card (T dial bounded [0.2,1.5], explore/merge_rate/stagnation) or "🔴 chamber-T خاموش — طبق طراحی (فقط رأی صریح)"; RFC verdict history from chrono.rfc_verdicts_tail (table: rfc_id, verdict merged/rejected, ts) + rfc_verdicts_total; a static reminder card: "merge هرگز خودکار نیست — فقط tap انسانی در تلگرام".

Tab 5 «پول و متابولیسم» (Money): telemetry per-organ table (all zeros expected — that's HEALTHY pre-live-gate, show it positively); organ_table registry (flag: if "PAINTING" missing → amber note "ارگان PAINTING منتظر verdict — پای Lead-نقاشی incubating"); fitness weights donut + cells table (or "cells خالی — هنوز دادهٔ outbox نیست"); attribution claimed/confirmed; fisher advisory card (condition number, current vs advisory weights side-by-side bars, big "ADVISORY-ONLY" watermark) or inactive chip; epochs count + latest epoch mode.

Tab 6 «مدرسه» (School): six gauge bars C01,C02,C03,E01,E02,E03 (0..1) + mean; note which cells are dormant (<0.1).

Tab 7 «ایمنی» (Safety): read-only invariant checklist rendered from static text (I1 append-only … I10 anti-injection — write one Persian line each); kill-switch explainer ("فایل _ops/STOP-ORGANISM — خارج از این اپ"); genome ledger card: records count + verify_scars string — treat "ok-with-scars: 1 … line(s) [40]" as GREEN with a small 🩹 badge and tooltip "زخمِ لنگرشدهٔ شناخته‌شده — تاریخ بازنویسی نشده"; chrono card: exists/heartbeats/effects_by_status (pending>0 → amber); channel_status (null → "توکن تلگرام هنوز ست نشده").

Tab 8 «هشدارها و خام» (Alerts/Raw): parse governor_alerts_tail into grouped entries (timestamp header + items), newest first, colored by ⚠️ presence; a collapsible pretty-printed JSON tree of the whole bundle with search.

# HEALTH-CHECK RULES ENGINE (compute on every load; each rule: id, Persian name, status pass|warn|fail|info, evidence, hint)
R1 freshness: minutes since organism_state.ts — <15 pass, <60 warn («داده کهنه»), else fail («ارگانیسم احتمالاً خاموش — RUN-ORGANISM.bat»). If the bundle itself is old, say so (use _meta.generated_at).
R2 halted === null else FAIL (show reason).
R3 frozen === false else FAIL («I3 FREEZE — تطبیق تلمتری/حسابداری را ببین»).
R4 stop_organism === false else FAIL («STOP-ORGANISM فعال»).
R5 month.usd === 0 AND today.usd === 0 → pass («سایهٔ $0 سالم»); anything nonzero before 2026-07-21 → FAIL CRITICAL («خرج پیش از گیت زنده!»).
R6 suspect_zero_total === 0 else warn.
R7 conflicts.length === 0 else FAIL («CONFLICT در صف انسانی»).
R8 germline_lag_h: <2 pass, <26 warn, else fail («بک‌اپ off-box عقب است»).
R9 replication.sigma.sigma_effective ≤ 1.0 else FAIL CRITICAL («I8 ضدسرطان») ; also show zone.
R10 fitness.authoritative must be false while experience_span_days < 28 — if true early → FAIL («fitness زودتر از موعد authoritative شده؟»).
R11 fitness.integrity_alerts empty else FAIL («عدم تطبیق outbox/db»).
R12 phases: for phase-0..6, PHASE_RESULT exists AND verdict === "approved" → pass; verdict null → warn («منتظر رأی»); rejected → fail; missing → warn.
R13 phase_metrics contains records for blueprint-phase-3..6 with registered_before_implementation === true → pass else warn.
R14 genome_ledger.verify_scars_ok === true → pass (scar count from the string shown as 🩹 badge); false → FAIL («زنجیرهٔ ژنوم شکسته»).
R15 chrono.exists && heartbeats > 0 → pass; else warn («pacemaker چیزی persist نکرده — بعد از restart دوباره چک کن»).
R16 chrono.effects_by_status: pending === 0 (or absent) → pass; pending > 0 → info with count («sweep ظرف ۷۲h رد می‌کند»).
R17 school mean > 0 → pass; all cells < 0.1 → warn («مدرسه خاموش؟»).
R18 consolidation_summary.cycles > 0 and last.timestamp within 48h → pass else warn.
R19 bcm_weights_summary: absent → info («BCM هنوز نچرخیده»); present → saturation_of_512 ≤ 1.0 else FAIL.
R20 chamber_temperature: absent → pass with info («RED خاموش — درست»); present → 0.2 ≤ T ≤ 1.5 else FAIL.
R21 fisher: absent → info; present → advisory_only === true AND (condition_number finite or null-with-note) else FAIL.
R22 organ_table contains "PAINTING" → pass; missing → warn («§۵ diff بودجه منتظر verdict»).
R23 governor_alerts_tail: entries with ⚠️ in the last 24h → list them as warn (count), none → pass.
R24 wiring (if organism_state.wiring present): wire_chamber_t must be false/absent → else FAIL CRITICAL («گیت قرمز بدون رأی صریح باز شده!»); no key containing "live"/"money" may be true.
Overall score: pass=1, warn=0.5, fail=0, info excluded; weight R5, R9, R24 ×3, R2-R4, R7, R14 ×2. Show as percent + letter (A+/A/B/C/D).

# DESIGN
Dark deep-sea theme (near-black blue background, bioluminescent accent colors: teal/cyan for pass, amber for warn, coral-red for fail), subtle octopus/tentacle motif in the header (pure CSS/SVG, no images), rounded cards, RTL layout with dir="rtl", system Persian-friendly font stack (Vazirmatn if locally available, then Segoe UI, Tahoma fallback — NO webfont downloads). Fully responsive down to 380px. A "خلاصهٔ چاپی" button that opens a print-friendly one-page summary (header + rules table). Persian digits acceptable but keep numeric precision. Smooth but minimal animations. Every card has a small "?" tooltip explaining what the metric means in one Persian sentence.

# OPTIONAL LIVE MODE
A settings drawer with an off-by-default "حالت زنده" toggle + URL field (default http://127.0.0.1:8771/api/organism). When enabled, poll every 60s and merge into organism_state only. On any fetch/CORS error show a friendly note: «مرورگر اجازهٔ localhost نداد — از فایل bundle استفاده کن» and auto-disable. Never send anything anywhere; GET only.

# HARD CONSTRAINTS
- READ-ONLY: no buttons that claim to stop/start/approve anything. Include a permanent footer banner: «این کابین فقط‌خواندنی است — کنترل فقط از مسیرهای human-gated خود سیستم».
- Handle absent/null modules gracefully everywhere.
- All thresholds live in one CONFIG object at the top of the script so they're easy to edit.
- No external requests except the optional live-mode localhost GET.

# EMBEDDED SAMPLE (wire to the «بارگذاری نمونه» button; real shadow-mode data, no secrets)
{"_meta":{"generator":"export_status.py v1 (read-only)","bundle_version":1,"generated_at":"2026-07-10T11:30:00"},
"organism_state":{"ts":"2026-07-10T11:28:46","started":"2026-07-08T15:07:05","epoch_mode":"allostatic — تابع فشار (نه clock)","halted":null,"frozen":false,"stop_organism":false,"month":{"key":"2026-07","musd":0,"usd":0.0,"aud":0.0},"today":{"musd":0,"usd":0.0},"suspect_zero_total":0,"conflicts":[],"germline_lag_h":0.64},
"fitness":{"ts":"2026-07-10T00:03:38","authoritative":false,"experience_span_days":0,"integrity_alerts":[],"attribution":{"claimed":0,"confirmed":0},"cells":{},"weights":{"value":0.30,"urgency":0.25,"efficiency":0.20,"human":0.20,"waste":0.05}},
"replication":{"sigma":{"sigma_effective":0.0,"zone":"pre-replication","spawn_proposed":0,"spawn_approved":0,"parents":1,"alerts":[]}},
"telemetry":{"per_organ_musd":{"PROJECT_F":0,"ARCHITECT_SYS":0,"GENOME_SYS":0,"ZIMAN":0,"DEBATE_LOOP":0}},
"school_awareness":{"awareness":{"C01":0.06,"C02":0.88,"C03":0.06,"E01":0.06,"E02":0.88,"E03":0.06},"mean":0.0417},
"channel_status":null,"fisher":null,"chamber_temperature":null,"bcm_weights_summary":null,
"latent_summary":{"total":42,"by_layer":{"acquisition":14,"doctor":13,"school":8,"consolidation":7}},
"phase_metrics":[{"phase":"blueprint-phase-3-bcm","registered_before_implementation":true,"metrics":{"memory_decay_rate":{"accept":"0 < β <= 0.1"},"memory_saturation":{"accept":"<= 1.0"}}},{"phase":"blueprint-phase-5-chamber-temperature","registered_before_implementation":true,"risk_label":"RED"},{"phase":"retro-registration-phases-0-1-2","registered_before_implementation":false,"retroactive":true}],
"phase_reviews":[{"phase_id":"phase-0","review_type":"PHASE_RESULT","verdict":"approved","payload":{"summary":"Stabilization + safety hardening"}},{"phase_id":"phase-3","review_type":"PHASE_RESULT","verdict":"approved","payload":{"summary":"BCM forgetting — فقط ایندکس retrieval"}},{"phase_id":"phase-6","review_type":"PHASE_RESULT","verdict":"approved","payload":{"summary":"Fisher advisory"}}],
"consolidation_summary":{"cycles":552,"last":{"cycle":552,"insights":["آگاهیِ میانگین: 0.02"],"verified_sources":["school_awareness"],"discarded_sources":[],"timestamp":1783994000}},
"governor_alerts_tail":["## 2026-07-10T09:45:03 (metabolism)","- ⚠️ consolidation bcm خطا: RuntimeError: boom",""],
"chrono":{"exists":false},
"genome_ledger":{"exists":true,"records":96,"verify_scars":"OK: ok-with-scars: 1 torn-but-anchored record(s) at line(s) [40]","verify_scars_ok":true},
"organ_table":{"PROJECT_F":{"floor":3},"ARCHITECT_SYS":{"floor":2},"GENOME_SYS":{"floor":2},"ZIMAN":{"floor":1},"DEBATE_LOOP":{"floor":0.5}},
"epochs":{"count":57,"latest":{"mode":"allostatic"}}}
```
