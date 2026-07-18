---
type: prompt
status: ready
tags: [octopus, chord, doctor, prompt, phase-c]
updated: 2026-07-18
parent: "[[../CHORD — معماری فیلترِ وتر (v0)]]"
---

# پرامپتِ ایجنتِ بعدی — CHORD فاز C (اتصالِ سایه به دکتر)

> این را به هر ایجنتِ بعدی (Claude/GLM/Codex) بده. فازهای A (کشف) و B (اسکلت + ۳۰ تستِ سبز)
> در جلسهٔ 2026-07-18 تمام شد. فاز C = دکتر ارزیابیِ chord را «فقط ثبت» کند. اجرا/گیتِ زنده ممنوع.

```text
You are continuing the OCTOPUS CHORD module (F:\backup). Phases A+B are DONE:
- Code: _ops/chord/ (stdlib-only, shadow-only, 30/30 tests green: _ops/tests/test_chord.py)
- Spec: _ops/chord/README.md + "04 - Architect System/CHORD — معماری فیلترِ وتر (v0).md"
- Discovery/risks: "04 - Architect System/ANALYSES/2026-07-18_CHORD-DISCOVERY.md"

YOUR MISSION — PHASE C (shadow wiring, zero behavior change):
1. Work ONLY in an isolated git worktree from master HEAD. Never edit live-tree
   existing files from the sandbox (host-side edits truncate — see the
   vault-sandbox-quirks memory and HANDOFF). New leaf files are safe anywhere.
2. In doctor's RFC/mission cycle (_ops/doctor/doctor.py, advance_rfcs), ADD a
   flag-gated side-channel (env OCTOPUS_WIRE_CHORD_SHADOW, default OFF):
   when ON, for each RFC/mission the doctor already processes, call
     chord.adapters.doctor_adapter.shadow_assess(mission_id, observations, dim_claims, context)
   built from data the doctor ALREADY has (test results, risk class, reversibility,
   budget). Record the returned dict NEXT TO the doctor's own decision (its existing
   ledger/lessons), plus chord's own ledger. DO NOT let the verdict change any branch,
   score, or action. Flag OFF = byte-identical behavior.
3. Register the test in _ops/tests/run_all.py (one line, in the worktree) and add
   tests: shadow path ON/OFF parity (doctor decisions identical), malformed inputs,
   and no new writes outside chord-ledger when OFF.
4. Context flags you MUST pass truthfully: touches_money, touches_secrets, destructive,
   external_side_effect, touches_genome, irreversible, stop_organism.
5. LLM use: only through chord.adapters.llm_adapter (single door model_router.ask,
   task "chord.extract", local-first Qwen; Fugu optional and fail-closed). Never let
   raw LLM text bypass JSON validation. Offline = UNKNOWN, never healthy.
6. Money/LIVE/credentials/genome/schtasks = owner-only (P7). Telegram wiring of the
   🧭 card into center.py is NOT phase C — separate serial-lane mission, flag
   OCTOPUS_WIRE_CHORD, only after owner vote.
7. Deliverables: worktree branch + diff, test report (run in worktree, NOT on the
   live organism), updated "Active Context/Progress" of 03 - Projects/Chord/PROJECT.md,
   one HANDOFF bullet, and a 5-line owner report (what changed, flags, how to enable,
   how to roll back, what stays off).
STOP after that. Do not activate anything.
```

**یادآوریِ قانون‌های vault برای همان ایجنت:** commit با `git -c core.fileMode=false` و add
صریح؛ قبل از commit بلابِ stage‌شده را integrity-check کن؛ `run_all` روی ارگانیسمِ زنده هرگز؛
`_Archive`/`.agentignore` حریم؛ پایانِ جلسه HANDOFF + validatorها.

**فاز D (فقط بعد از ≥۲ هفته دادهٔ سایه + رأی مالک):** مقایسهٔ verdictهای chord با outcome
واقعی (قرمز/سبزِ تست، rollback، هزینه) → کالیبراسیونِ آستانه‌ها (uncertainty_gate) → فقط بعدش
بحثِ گیتِ زنده برای تعمیرهای کم‌ریسک.
