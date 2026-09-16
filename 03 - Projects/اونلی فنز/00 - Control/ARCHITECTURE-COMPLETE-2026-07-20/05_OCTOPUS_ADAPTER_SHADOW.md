---
type: doc
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
tags: [creator-business, architecture]
created: 2026-07-20
updated: 2026-07-20
---

# 05 · OCTOPUS ADAPTER — قرارداد SHADOW_ONLY (پیش‌فرض و تنها حالت مجاز)

> مرز قرنطینه (مگاپرامپت §۸): Project-F **هرگز** وارد MVO/revenue-organism اختاپوس نمی‌شود؛ EffectorGate پول برای PF ممنوع؛ publish از settle ارگانیسم ممنوع. E2 = تلگرام فقط به A؛ E4 = publish فقط انسان پس از GO.

## آنچه امروز واقعاً وصل است [FACT]

- `_ops/STOP-ORGANISM` / `master_halted`: هر دو بات با walk-up احترام می‌گذارند (خواندنِ فایل‌سیستمی، صفر import از `_ops`).
- `store.OctopusState`: ‏heartbeat محلی (`langar/octopus.json`) — فقط اعداد beat/pain/protective.
- `/octopus_tick`: ‏advisory محض؛ از این sprint ‏compliance-gated و ‏NEURAL_AVAILABLE-صادق.
- pf_os: **وصل نیست** (ADR: langar کانونی؛ pf_os ‏incubating).

## قراردادِ آداپتور برای آینده (design-only — قبل از هر پیاده‌سازی، رأی مالک)

| endpoint | جهت | payload | قاعده |
|---|---|---|---|
| `GET /pf/status` | اختاپوس→PF | `{beat, mode, protective, drafts_count, dm_pending, acq_ready, full_stop, karma_met}` | فقط aggregate/count؛ صفر متن hook/caption/body، صفر PII |
| `GET /pf/verdicts` | اختاپوس→PF | `{pending: [{id, kind, age_s}]}` | فقط id/نوع — متنِ تصمیم نه |
| `POST /pf/kill` | اختاپوس→PF | `{scope: cockpit\|studio\|full, reason_len}` | فقط در جهت توقف (kill مجاز، revive ممنوع از راه دور) |
| `POST /pf/route_verdict` | اختاپوس→PF | `{verdict_id, decision_ref}` | فقط ارجاع به DecisionLog id — خودِ تصمیم را حمل نمی‌کند |

قواعد سراسری: bind فقط `127.0.0.1` · rate-limit ‏(≥2s بین درخواست‌ها، الگوی rate-limiter دکتر) · بدون secret در payload/URL · لاگ append-only · فلگ `OCTOPUS_PF_ADAPTER` پیش‌فرض OFF · حالت LIVE (هر actuationی فراتر از kill) **ممنوع — در این قرارداد تعریف نشده تا قابل‌فعال‌شدن نباشد**.

## eventهای مجاز مرزی (اگر روزی pf_os commit شد — از ARCH-SCAN §4.3)

`pf.draft.created/approved` (فقط id+cert-flags) · `pf.acq.ready` (platform+tag) · `pf.dm.queued` (channel+kind) · `pf.gate.changed` · `pf.kpi.weekly` (aggregate) · `pf.kill_switch.fired` · `pf.warning.platform` · `pf.cost.threshold`.
پیش‌نیاز فنی: `events_schema` تایپ‌دار + تست boundary-egress که ردِ هر payload حاویِ blocklist/شهر/متن خام را اثبات کند (backlog #R4).
