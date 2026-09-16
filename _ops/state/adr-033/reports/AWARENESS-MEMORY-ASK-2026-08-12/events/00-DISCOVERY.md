# 00-DISCOVERY — Cognitive Runtime v2.0 (2026-08-12)

## کشف کلیدی: event infrastructure موجود است

`_ops/evidence_plane/event_log.py` از قبل وجود دارد:
- `append_event(event_type, run_id, trace_id, checkpoint_id, ...)`
- `event_id = evt_<uuid16>`
- append-only JSONL در `state/adr-033/events/<day>.jsonl`
- redaction خودکار (text/prompt/payload/dm/content فیلتر می‌شود)
- `read_events(day, limit)` برای بازخوانی

**تصمیم:** REUSE این زیرساخت، نه بازنویسی. Cognitive layer روی آن می‌نشیند.

## call graph واقعی (file:line)

```
Chat Box (app.js renderAsk:2033)
  → POST /api/collab (miniapp_gateway.py:823)
    → collaborator.handle (collaborator.py:101)
      → conversation.handle (conversation.py:132) — 27+ regex intents
      → [COLLAB_USE_MODEL] collab_model_adapter.complete (cma.py:196)
        → _self_context (cma.py:113) → model_router.ask (mr.py:548)
          → DeepSeekClient.complete (client.py:145) → urllib POST
      → owner_recall.recall_for_owner_ask (owner_recall.py:30) → data.facts
      → equation_advice.snapshot (ea.py:150) → data.equation_advice
      → unified_context.assemble (uc.py) → data.unified_context
      → session_memory.remember (sm.py) → data.session_turn
      → collab_memory.append (cm.py:78) → content-free digest
```

## convention موجود

- UUID: `uuid4().hex[:12]` یا `[:16]` (talk_gate.py:57)
- Timestamp: `time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())` یا `opslib.now_iso()`
- Event store: JSONL در `state/adr-033/events/<day>.jsonl`
- Redaction: فیلتر `{text, prompt, payload, dm, content}` قبل از persist

## locked files (دست‌نخورده)

flags.cmd · signals-registry · capabilities-registry · run_all.py · ADR-033..037 ·
pulse_arbiter · rhythm · ledger · policy_gate · owner-verdicts

## ادعاهای baseline — همگی VERIFIED (فاز I قبلاً تأیید کرد)

A (B→H): owner_recall · data.facts · vault_empty · selfmap · _self_context — VERIFIED
B (J→N): equation_advice · shadow · limited_effect · رأی=3 — VERIFIED
C (اسناد): 00-04 + 07-11 — VERIFIED

## conflictهای زنده

C1 (TESTED/SHADOW) — حل شد (validator ok)
C2 (ADR-036) — حل شد (فایل ساخته شد)
