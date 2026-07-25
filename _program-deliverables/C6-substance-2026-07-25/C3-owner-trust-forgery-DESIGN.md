# C3 — the research loop forges owner trust (learning_gate / gate / research_loop)
# VERDICT: real-bug
# FILES: ['F:\\backup\\_ops\\outcomes\\learning_gate.py', 'F:\\backup\\_ops\\memory\\gate.py', 'F:\\backup\\_ops\\outcomes\\research_loop.py', 'F:\\backup\\_ops\\tests\\test_learning_loop.py', 'F:\\backup\\_ops\\tests\\test_c3_owner_trust_forgery.py (new)', 'F:\\backup\\_ops\\tests\\run_all.py']
# FLAG: none — deliberately unflagged. This only TIGHTENS what a caller may declare inside the already-gated OCTOPUS_WIRE_MEMORY_GATE surface; a flag would leave the forgery open by default, which is the opposite of the repo's fail-closed idiom. C6 stays dark behind its own two gates.

## SUMMARY
Make trust EARNED FROM EVIDENCE instead of DECLARED BY THE CALLER. (1) learning_gate._verify_outcome now also reads `verdict` + `payload_json` and returns an `owner_attested` bit that is true only for a row carrying the single-writer owner attestation (`verdict='measurement'` + `payload.owner_verdict_raw`, written only by verdict_recorder.record_owner_verdict). Without it, a declared OWNER_CONFIRMED is capped to GRADED and the privileged literal source='owner' is replaced by 'unattested_owner_claim' — so no future namespace can be tricked. (2) The decision receipt now records the trust the GATE granted plus the claim that was made (CLAIMED_*/OWNER_CLAIM_UNATTESTED), so over-claims become durably auditable instead of silent. (3) gate.py adds a producer-consistency guard: the privileged literal 'owner' only commits from owner-surface producers; a self-declaring automated producer gets `propose`, never `commit`. (4) research_loop declares the honest grade (GRADED, source='research_loop') and stamps its outcome row `payload.self_run=True`. (5) The C3 test fixture is made faithful by routing through record_owner_verdict. Net effect on the two legitimate call sites: byte-equivalent stored trust (owner tap still OWNER_CONFIRMED, lead still GRADED-in-semantic); only receipt reason_codes and the research memory's provenance.source change.

## TESTS
NEW HERMETIC TEST — F:\backup\_ops\tests\test_c3_owner_trust_forgery.py ($0, offline, stubbed evaluator so no subprocess, per-test sqlite under the harness state dir).

FAILS TODAY: test #1 proves a non-owner caller currently mints an OWNER_CONFIRMED memory in an owner-only namespace (`store.get("owner_fact","self-serving")` returns trust=OWNER_CONFIRMED). Test #2 proves the source label is forged today (`provenance_json.source == "owner"`). PASSES AFTER the patch. Test #3 (owner tap) and #4 (single-writer) are the regression fences.

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_c3_owner_trust_forgery.py — C3: «مالک تأیید کرد» فقط با گواهیِ مالک.

قبل از پچ (قرمز): یک callerِ غیرمالک (research_loop) با نوشتنِ ردیفِ outcomeِ خودش
میلی‌ثانیه قبل + رشتهٔ source="owner" خاطرهٔ OWNER_CONFIRMED در namespaceِ owner_only
می‌سازد — بدونِ هیچ مالکی در حلقه.
بعد از پچ (سبز): trust از **شواهد** مشتق می‌شود نه از ادعا؛ مسیرِ واقعیِ رأی دست‌نخورده.
$0 آفلاین؛ صفر شبکه/پول/effect؛ ادعای مکانیزمی (شمارشِ نویسنده) نه wall-clock.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("c3-owner-trust")
_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "memory"), str(_OPS / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib                  # noqa: E402
import memory_store as ms      # noqa: E402
import gate as gate_mod        # noqa: E402
import decision_receipt as dr  # noqa: E402
import outcome_store as osx    # noqa: E402
import learning_gate as lg     # noqa: E402
import verdict_recorder as vr  # noqa: E402

_STATE = Path(str(opslib.STATE_DIR))
_OREF_SELF = "research|rc_x|accepted-measurement"


def _eval_pass(*, internal_metric_pass=True, **kw):
    return {"overall_verdict": "pass", "anti_hacking_flag": False}


def _stores(tag):
    md = _STATE / "memory" / f"m-{tag}.db"
    rp = _STATE / "receipts" / f"r-{tag}.db"
    od = _STATE / "outcomes" / f"o-{tag}.db"
    for p in (md, rp, od):
        p.parent.mkdir(parents=True, exist_ok=True)
    store = ms.MemoryStore(path=md)
    return store, gate_mod.MemoryGate(store), dr.DecisionReceiptStore(rp), osx.OutcomeStore(path=od)


def _close(*objs):
    for o in objs:
        try:
            o.close()
        except Exception:  # noqa: BLE001
            pass


def _self_written_row(oc):
    """دقیقاً همان ردیفی که research_loop.py:363 می‌نویسد — بدونِ هیچ گواهیِ مالک."""
    oc.record({"correlation_id": "rc_x", "proposal_id": "rc_x", "leg_id": "research",
               "event_type": "accepted-measurement", "value_aud_claimed": 0.0,
               "idempotency_key": _OREF_SELF})


# ── ۱: callerِ غیرمالک نمی‌تواند OWNER_CONFIRMED بسازد (قرمزِ امروز) ──────────────
def t_nonowner_cannot_mint_owner_confirmed():
    os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "1"
    store, g, rc, oc = _stores("forge")
    try:
        _self_written_row(oc)
        r = lg.learn_from_outcome(
            memory_gate=g, receipt_store=rc, outcome_store=oc, evaluator=_eval_pass,
            signal={"content": "my own change is good", "mkey": "self-serving",
                    "namespace": "owner_fact", "correlation_id": "rc_x",
                    "outcome_ref": _OREF_SELF, "trust": "OWNER_CONFIRMED",
                    "salience": 0.9, "source": "owner", "producer": "research_loop"})
        got = store.get("owner_fact", "self-serving")
        assert got is None, (
            "جعلِ اعتماد: callerِ غیرمالک خاطرهٔ owner_fact ساخت "
            f"(trust={got.get('trust')}) — {r}")
        assert not r.get("learned"), f"ادعای owner بدونِ گواهی نباید commit شود: {r}"
        assert r.get("owner_claim_unattested") is True, f"ادعای جعلی باید در telemetry بیاید: {r}"
    finally:
        _close(store, rc, oc)


# ── ۲: ادعای بی‌گواهی سقف می‌خورد، ولی یادگیری نمی‌میرد ─────────────────────────
def t_unattested_claim_is_capped_not_silent():
    os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "1"
    store, g, rc, oc = _stores("cap")
    try:
        _self_written_row(oc)
        r = lg.learn_from_outcome(
            memory_gate=g, receipt_store=rc, outcome_store=oc, evaluator=_eval_pass,
            signal={"content": "research finding: batched IN() beats N+1", "mkey": "capped",
                    "namespace": "semantic", "correlation_id": "rc_x",
                    "outcome_ref": _OREF_SELF, "trust": "OWNER_CONFIRMED",
                    "salience": 0.6, "source": "owner", "producer": "research_loop"})
        assert r.get("learned"), f"حلقه باید یاد بگیرد (فقط با گریدِ صادق): {r}"
        assert r.get("trust") == "GRADED" and r.get("trust_declared") == "OWNER_CONFIRMED", r
        got = store.get("semantic", "capped")
        assert got and got["trust"] == "GRADED", got
        prov = json.loads(got.get("provenance_json") or "{}")
        assert prov.get("source") != "owner", f"برچسبِ ممتازِ owner نباید جعل شود: {prov}"
        # ادعای جعلی باید در رسیدِ durable قابلِ ممیزی باشد
        rec = rc.resolve(r["receipt_id"]) or {}
        assert "OWNER_CLAIM_UNATTESTED" in (rec.get("reason_codes") or []), rec
    finally:
        _close(store, rc, oc)


# ── ۳: مسیرِ واقعیِ رأیِ مالک دست‌نخورده OWNER_CONFIRMED می‌گیرد ────────────────
def t_owner_verdict_path_still_mints_owner_confirmed():
    os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "1"
    store, g, rc, oc = _stores("owner")
    try:
        out = vr.record_owner_verdict(oc, proposal_id="P9", verdict="approved",
                                      correlation_id="corr-O9", leg_id="lead")
        assert out["recorded"] and out["event_type"] == "accepted-measurement", out
        r = lg.learn_from_outcome(
            memory_gate=g, receipt_store=rc, outcome_store=oc, evaluator=_eval_pass,
            signal={"content": "owner accepted proposal (leg=lead)", "mkey": "owner-rule",
                    "namespace": "owner_fact", "correlation_id": "corr-O9",
                    "outcome_ref": out["idempotency_key"], "trust": "OWNER_CONFIRMED",
                    "salience": 0.6, "source": "owner", "producer": "owner_verdict"})
        assert r.get("learned") and r.get("trust") == "OWNER_CONFIRMED", r
        assert not r.get("owner_claim_unattested"), r
        got = store.get("owner_fact", "owner-rule")
        assert got and got["trust"] == "OWNER_CONFIRMED", got
    finally:
        _close(store, rc, oc)


# ── ۴: گواهیِ مالک **تک-نویسنده** است (ادعای مکانیزمی، نه ساعتِ دیواری) ─────────
def t_owner_attestation_has_exactly_one_writer():
    key = lg._OWNER_ATTEST_KEY
    allow = {"verdict_recorder.py",                  # تنها نویسنده (رونوشتِ تپِ واقعی)
             "learning_gate.py",                     # فقط خواننده (verify)
             "test_c3_owner_trust_forgery.py"}       # همین تست
    hits = []
    for p in _OPS.rglob("*.py"):
        if any(part in ("state", "_Archive", "__pycache__", "_legacy") for part in p.parts):
            continue
        try:
            if key in p.read_text("utf-8", errors="ignore"):
                hits.append(p.name)
        except OSError:
            continue
    extra = sorted(set(hits) - allow)
    assert not extra, f"گواهیِ مالک نویسندهٔ نو گرفت (single-writer شکست): {extra}"
    assert "verdict_recorder.py" in hits, "نویسندهٔ canonicalِ گواهی گم شد"


if __name__ == "__main__":
    failed = harness.run([
        ("[۱] callerِ غیرمالک نمی‌تواند OWNER_CONFIRMED بسازد", t_nonowner_cannot_mint_owner_confirmed),
        ("[۲] ادعای بی‌گواهی capped + قابلِ ممیزی", t_unattested_claim_is_capped_not_silent),
        ("[۳] مسیرِ رأیِ مالک دست‌نخورده", t_owner_verdict_path_still_mints_owner_confirmed),
        ("[۴] گواهیِ مالک تک-نویسنده", t_owner_attestation_has_exactly_one_writer),
    ])
    sys.exit(1 if failed else 0)
```

REGRESSION SET TO RUN (one process per file, per repo idiom): test_c3_owner_trust_forgery.py, test_learning_loop.py (10 cases), test_research_loop.py (10 cases), test_memory_gate.py, test_lead_learning_wire.py, test_verdict_outcome.py, test_paper_lead_mvo_e2e.py. I did NOT execute them (read-only mandate: run_all writes live state). Predicted results, with the reasoning: test_memory_gate.py:97-99 submits owner_fact/source=owner with NO producer → `_owner_source_ok` returns True → still OWNER_CONFIRMED (green). test_research_loop.py's six `store.get("semantic", f"research-...")` assertions (:113,:131,:173,:285,:303,:321) are untouched because the namespace stays semantic and the stored trust was already GRADED. test_lead_learning_wire.py asserts counts and namespace only, and the lead path declares DETERMINISTIC/source='deterministic', which the cap never touches.

## RISKS
- (a) THE ANSWER — what trust a self-run sandbox experiment should carry: **GRADED is the ceiling, and never OWNER_CONFIRMED.** taxonomy.py:12-14 orders the grades strongest→weakest and taxonomy.py:74-75 states the rule is «چه کسی مجاز است این namespace را commit کند» — نه خودِ مدل. OWNER_CONFIRMED is defined operationally at gate.py:167-168 as `source == 'owner'` under the `owner_only`/`owner_or_deterministic` committers — i.e. a human confirmation; C6's driver is a daily beat (c6_trigger.c6_research_beat) with no human in it, so this grade is simply unavailable. DETERMINISTIC is defined at gate.py:170-171 as `source == 'deterministic'` under `owner_or_deterministic` — a reproducible non-model procedure; a benchmark measurement over a model-authored hypothesis is not that. GRADED is defined by gate.py:66-88 `_verify_external_grade` — 'True only for an INDEPENDENT, self-consistent grade receipt — never for a claimant-controlled flag', with the explicit independence rule at gate.py:79 `if not grader or grader == claimant: return False`. A sandbox experiment that passes an injected verifier_fn, a held-out gate, and governance.utility with hard constraints is exactly a graded self-claim → **GRADED**.
- (a-caveat, stated honestly) Today C6 does NOT actually earn GRADED: c6_trigger._derive_fns (c6_trigger.py:197-222) builds experiment_fn and verifier_fn as two closures over the same hypothesis, and the verifier merely re-reads the `benchmark_gain_ms` the experiment itself reported — grader == claimant, which gate.py:79 rejects. The taxonomically strict home for such a claim is `namespace='self_claim'` (taxonomy.py:79, committer `external_grade`, default_trust ADVISORY), where the gate stores ADVISORY until an independent grade receipt validates and then upgrades to GRADED by itself. I did NOT ship that: it would (i) move C6 memories out of `semantic`, the only namespace any live reader searches (lead_outcome_recorder.py:66), (ii) require editing six assertions in test_research_loop.py, and (iii) collide with `_LEARNABLE_TRUST` (learning_gate.py:41), which excludes ADVISORY — so C6 would learn nothing at all until an independent grader exists. That is the owner's call, not mine.
- (b) THE ANSWER — should `source='owner'` be allowed from a non-owner caller: **No, and today nothing prevents it.** The gate has no way to know the caller is not the owner: `source` is a plain string on the candidate dict, there is no session, actor, or capability object anywhere on the path, and gate.py:168 grants OWNER_CONFIRMED on the string alone. Since the gate cannot authenticate the caller, the fix is to stop asking the caller: the privileged grade is derived from a durable artifact the caller does not author in a privileged way — the outcome row's owner attestation (`verdict='measurement'` + `payload.owner_verdict_raw`, verdict_recorder.py:77-80), whose repo-wide writer count is exactly one. Forging OWNER_CONFIRMED now requires writing a row that impersonates an owner tap, which requires editing verdict_recorder.py or adding a new writer — a **code change**, which the self-improvement loop is structurally forbidden from applying (propose_only_apply_guard, research_loop.py:471-473, plus governance.self_improvement_permits fail-closed at :43-47) — and which the new single-writer test fails on. That is as close to 'impossible' as a single-process, no-auth repo can honestly get; I am not claiming cryptographic unforgeability. Layer 2 (gate.py producer allowlist) is explicitly labelled as drift-catching, not authentication.
- (c) THE ANSWER — does `_verify_outcome`'s contract need strengthening, and what distinguishes a legitimate self-written outcome from forgery: **Yes — existence is necessary but not sufficient — but the discriminator is NOT self-authorship or elapsed time.** All three legitimate callers write their own row moments before verifying it (verdict_recorder.py:142→:165, lead_outcome_recorder.py:91→wiring.py:1908, research_loop.py:363→:367); a rule banning self-written rows would break the entire learning arc, and a wall-clock 'gap' rule would be exactly the kind of timing-based claim this vault already paid for (warm-cache/GC/ordering artifacts) — hardware-dependent and gameable by inserting a sleep. The honest discriminator is the **attestation class** of the row, a counted mechanism-level property: verdict_recorder's row is a transcription of an act that originated OUTSIDE the process (an owner tap arriving over Telegram) and carries the single-writer marker; the lead row is a deterministic computation over an external lead and claims only a mechanism grade; research_loop's row records nothing external at all — it is the loop asserting its own success, which supports GRADED and nothing above it. Hence the strengthened contract: `(ok, owner_attested, why)`, with `owner_attested` gating the OWNER grade, plus the receipt recording the trust the GATE granted rather than the trust the caller claimed.
- Behaviour deltas on the two legitimate call sites (both intentional, both small): the owner-tap path (verdict_recorder.py:165) is unchanged in stored trust/namespace/memory_id but its receipt reason_codes now read TRUST_GRADED (what the semantic committer actually granted) plus CLAIMED_OWNER_CONFIRMED, instead of the previous TRUST_OWNER_CONFIRMED — i.e. the receipt stops repeating a claim the gate never honoured. The lead path (wiring.py:1908) likewise records TRUST_GRADED + CLAIMED_DETERMINISTIC. Receipts are inert by design (decision_receipt.py:7 — no policy or runner changes behaviour based on a receipt), and no test asserts a reason code, so blast radius is telemetry only. Caps checked: reason_code ≤48 chars, ≤30 items (decision_receipt.py:61-63) — longest new code is CLAIMED_OWNER_CONFIRMED (23).
- The research memory's stored trust does not change (it was already GRADED via the semantic accident, gate.py:181-189); what changes is that the declaration finally matches it and `provenance.source` stops saying 'owner'. Anyone auditing existing rows in the live memory.db will still find research memories whose provenance says source='owner' — pre-existing rows are NOT rewritten (vault law: never delete/mutate, append only). A follow-up owner-gated pass could append retractions for them; I did not touch live state.
- The `_verify_outcome` signature changes from a 2-tuple to a 3-tuple. It is module-private with exactly one caller (learning_gate.py:139) and no external importer (grep across _ops: only learning_gate.py:98,139 and a stale entry in state/cortex/self-model.json:3852, which is a generated self-model artifact, not code). No fake/stub OutcomeStore exists in the suite that would break on the widened SELECT — test_research_loop.py's `_RaisingOutcomes` raises on `record` before any verify happens.
- The gate.py producer allowlist is a string check and I am not pretending otherwise: a caller that lies about BOTH `source` and `producer` still passes that layer. It is only reachable, however, for owner-only namespaces, and the learning_gate evidence layer stands in front of it for every automated learner. A stronger version (an injected `owner_attestation_validator`, mirroring the existing `grade_receipt_validator` idiom at gate.py:58-64,86-88) would be default-open until wired and would break test_memory_gate.py:97-99, so I left it out and named the residual gap instead of hiding it.
- Deliberately NOT flag-gated. Every other addition in this repo is flag-off by default, but this one removes a capability (the ability to declare owner trust) rather than adding behaviour; putting it behind a flag would leave the forgery reachable by default, and the flag itself would become the thing an unattested caller could turn off. It only tightens code already living behind OCTOPUS_WIRE_MEMORY_GATE.
- Not verified by execution: I did not run the suite (read-only mandate — run_all.py writes live state). Every prediction above is from source reading; the owner or the next agent should run the regression set listed in `tests` before merging.

## CODE
=== PATCH 1/6 — F:\backup\_ops\outcomes\learning_gate.py ===

-- 1a. ANCHOR (lines 39-41), APPEND AFTER IT --
OLD:
FLAG = "OCTOPUS_WIRE_MEMORY_GATE"        # یادگیری پشتِ همان فلگِ Memory Gate (نویسندهٔ خاطره)
# فقط این trustها «outcomeِ واقعی»اند؛ بقیه preference/ادعا → یاد گرفته نمی‌شوند.
_LEARNABLE_TRUST = ("OWNER_CONFIRMED", "DETERMINISTIC", "GRADED")

NEW:
FLAG = "OCTOPUS_WIRE_MEMORY_GATE"        # یادگیری پشتِ همان فلگِ Memory Gate (نویسندهٔ خاطره)
# فقط این trustها «outcomeِ واقعی»اند؛ بقیه preference/ادعا → یاد گرفته نمی‌شوند.
_LEARNABLE_TRUST = ("OWNER_CONFIRMED", "DETERMINISTIC", "GRADED")

# ── C3-fix (owner-trust forgery) ─────────────────────────────────────────────
# «مالک تأیید کرد» فقط با گواهیِ **ساختاری** روی خودِ ردیفِ outcome معتبر است، نه با
# رشته‌ای که caller در dict گذاشته. این کلید در کلِ درخت **یک نویسنده** دارد:
# verdict_recorder.record_owner_verdict (verdict_recorder.py:78) — همان تابعی که تپِ
# واقعیِ دکمهٔ تلگرام را رونویسی می‌کند. تستِ single-writer این ناوردی را قفل نگه می‌دارد؛
# شکستنش نیازمندِ **ویرایشِ کد** است، و حلقهٔ خودبهبودی ساختاراً اجازهٔ apply/merge ندارد
# (research_loop.propose_only_apply_guard + governance.self_improvement_permits).
_OWNER_ATTEST_KEY = "owner_verdict_raw"
_OWNER_ATTEST_VERDICT = "measurement"
# جایگزینِ source="owner"ِ بی‌گواهی — عمداً هرگز برابرِ هیچ منبعِ ممتازی نیست.
_UNATTESTED_SOURCE = "unattested_owner_claim"


-- 1b. ANCHOR: REPLACE THE WHOLE FUNCTION `_verify_outcome` (lines 98-117) --
OLD (exact, 20 lines starting `def _verify_outcome(outcome_store, outcome_ref: str, trust: str) -> "tuple[bool, str]":` and ending `    return (ok, f"outcome event_type={et}")`)

NEW:
def _owner_attested(row) -> bool:
    """آیا این ردیفِ outcome واقعاً **تپِ مالک** را رونویسی کرده؟ row=(event_type, verdict, payload_json).

    خودنویسی جرم نیست — هر سه callerِ مشروع ردیفِ خودشان را می‌نویسند (verdict_recorder.py:142،
    lead_outcome_recorder.py:91، research_loop.py:363). چیزی که فرق می‌کند **کلاسِ گواهی** است:
    ردیفِ رأی، رونوشتِ یک کنشِ بیرونی (تپِ مالک) است؛ ردیفِ پژوهش، ادعای حلقه دربارهٔ خودش.
    fail-closed."""
    try:
        et, verdict_col, payload_json = str(row[0] or ""), str(row[1] or ""), row[2]
        if et != "accepted-measurement" or verdict_col != _OWNER_ATTEST_VERDICT:
            return False
        pl = json.loads(payload_json or "{}")
        return isinstance(pl, dict) and bool(str(pl.get(_OWNER_ATTEST_KEY) or "").strip())
    except Exception:  # noqa: BLE001
        return False


def _verify_outcome(outcome_store, outcome_ref: str, trust: str) -> "tuple[bool, bool, str]":
    """گاردِ محتوایی (red-team P1 fix) + **سقفِ trust از روی شواهد** (C3-fix).

    outcome_refِ ادعایی باید یک ردیفِ **واقعیِ** outcomes.db باشد و event_typeاش با trust
    سازگار (OWNER_CONFIRMED → فقط accepted-measurement). ولی وجودِ ردیف **کافی نیست**:
    caller می‌تواند میلی‌ثانیه قبل ردیفِ خودش را بنویسد. پس گواهیِ مالک هم برگردانده می‌شود
    تا سقفِ trust از شواهد بیاید نه از ادعا. خروجی: (ok, owner_attested, why). fail-closed."""
    if outcome_store is None:
        return (False, False, "no-outcome-store")   # نمی‌توان verify کرد → یاد نگیر (fail-closed)
    ref = str(outcome_ref or "").strip()
    if not ref:
        return (False, False, "no-outcome-ref")
    try:
        row = outcome_store._conn.execute(   # noqa: SLF001 — read-only verify
            "SELECT event_type, verdict, payload_json FROM outcomes "
            "WHERE idempotency_key=?", (ref,)).fetchone()
    except Exception:  # noqa: BLE001
        return (False, False, "outcome-query-error")
    if not row:
        return (False, False, "outcome-ref not found (forged trust)")
    et = str(row[0] or "")
    attested = _owner_attested(row)
    ok = (et == "accepted-measurement") if trust == "OWNER_CONFIRMED" else (et in (
        "accepted-measurement", "delivered", "outcome-recorded", "decided"))
    return (ok, attested, f"outcome event_type={et} owner_attested={attested}")


-- 1c. ANCHOR (lines 138-141) --
OLD:
        # ── گاردِ ۱: outcome-binding (trust باید با یک outcomeِ واقعی پشتیبانی شود) ──
        ok, why = _verify_outcome(outcome_store, signal.get("outcome_ref"), trust)
        if not ok:
            return {"learned": False, "reason": f"unverified outcome — {why} (trust not bound to reality)"}

NEW:
        # ── گاردِ ۱: outcome-binding (trust باید با یک outcomeِ واقعی پشتیبانی شود) ──
        ok, owner_attested, why = _verify_outcome(outcome_store, signal.get("outcome_ref"), trust)
        if not ok:
            return {"learned": False, "reason": f"unverified outcome — {why} (trust not bound to reality)"}
        # ── گاردِ ۱ب (C3-fix): trust و برچسبِ ممتاز از **شواهد** مشتق می‌شوند، نه از ادعا ──
        # gate.py:168 به هر کسی که رشتهٔ source=="owner" بیاورد مستقیم OWNER_CONFIRMED می‌دهد و
        # هیچ راهی ندارد بفهمد caller مالک نیست. پس این‌جا، بدونِ گواهیِ مالک روی خودِ outcome:
        #   (۱) ادعای OWNER_CONFIRMED به سقفِ صادقش (GRADED) می‌خورد،
        #   (۲) برچسبِ ممتازِ source="owner" برداشته می‌شود تا هیچ namespaceِ owner-onlyِ آینده
        #       (procedural/owner_fact) با تغییرِ یک رشته جعل نشود.
        declared_trust = trust
        source = str(signal.get("source") or "learning_gate")
        owner_claim_unattested = False
        if not owner_attested:
            if trust == "OWNER_CONFIRMED":
                trust, owner_claim_unattested = "GRADED", True
            if source == "owner":
                source, owner_claim_unattested = _UNATTESTED_SOURCE, True


-- 1d. ANCHOR (line 168, inside `candidate`) --
OLD:
                     "source": signal.get("source", "learning_gate"),
NEW:
                     "source": source,


-- 1e. ANCHOR (lines 174-183) --
OLD:
        res = memory_gate.submit(candidate)
        if res.get("verb") == "commit":
            mid = res.get("memory_id")
        elif res.get("verb") == "skip":
            # dedup: همان درس قبلاً یاد گرفته شده → یادگیریِ تکراری صفر (نه artifactِ نو)
            return {"learned": False, "reason": "duplicate learning (already learned)",
                    "eval_verdict": ev["verdict"], "memory_id": None, "dedup": True}
        else:
            return {"learned": False, "reason": f"gate {res.get('verb')}: {res.get('reason')}",
                    "eval_verdict": ev["verdict"]}

NEW:
        res = memory_gate.submit(candidate)
        if res.get("verb") == "commit":
            mid = res.get("memory_id")
            # رسید باید trustی را ثبت کند که **گیت داد**، نه آن‌چه caller خواست.
            granted_trust = str(res.get("trust") or trust)
        elif res.get("verb") == "skip":
            # dedup: همان درس قبلاً یاد گرفته شده → یادگیریِ تکراری صفر (نه artifactِ نو)
            return {"learned": False, "reason": "duplicate learning (already learned)",
                    "eval_verdict": ev["verdict"], "memory_id": None, "dedup": True}
        else:
            return {"learned": False, "reason": f"gate {res.get('verb')}: {res.get('reason')}",
                    "eval_verdict": ev["verdict"], "trust_declared": declared_trust,
                    "owner_claim_unattested": owner_claim_unattested}


-- 1f. ANCHOR (line 196) --
OLD:
                "reason_codes": [f"TRUST_{trust}", f"EVAL_{ev['verdict'].upper()}"],
NEW:
                # صداقتِ رسید: trustِ **اعطاشده** + ادعای متفاوتِ caller (اگر بود) — قابلِ ممیزی
                "reason_codes": ([f"TRUST_{granted_trust}", f"EVAL_{ev['verdict'].upper()}"]
                                 + ([f"CLAIMED_{declared_trust}"]
                                    if granted_trust != declared_trust else [])
                                 + (["OWNER_CLAIM_UNATTESTED"] if owner_claim_unattested else [])),


-- 1g. ANCHOR (lines 216-218) --
OLD:
        return {"learned": not pending_admission, "staged": bool(pending_admission),
                "memory_id": mid, "receipt_id": rid,
                "eval_verdict": ev["verdict"], "anti_hacking_flag": False,
NEW:
        return {"learned": not pending_admission, "staged": bool(pending_admission),
                "memory_id": mid, "receipt_id": rid,
                "trust": granted_trust, "trust_declared": declared_trust,
                "owner_claim_unattested": owner_claim_unattested,
                "eval_verdict": ev["verdict"], "anti_hacking_flag": False,


=== PATCH 2/6 — F:\backup\_ops\memory\gate.py (defense in depth) ===

-- 2a. ANCHOR (line 37, end of the _SECRET_RX block), APPEND AFTER IT --
OLD:
    r"\bpassword\b\s*[:=]|\bseed\b\s*[:=]|\bapi[_-]?key\b\s*[:=]|0x[a-fA-F0-9]{40})", re.I)
NEW:
    r"\bpassword\b\s*[:=]|\bseed\b\s*[:=]|\bapi[_-]?key\b\s*[:=]|0x[a-fA-F0-9]{40})", re.I)

# C3-fix: «owner» یک برچسبِ **ممتاز** است، نه رشتهٔ آزاد. گیت نمی‌تواند caller را احراز هویت کند؛
# این لایه فقط driftِ آینده را می‌گیرد (producerِ خودکاری که خودش را owner اعلام کند → propose،
# هرگز commit). گاردِ اصلی در learning_gate است: گواهیِ مالک روی خودِ ردیفِ outcome.
_OWNER_PRODUCERS = ("owner", "owner_verdict", "owner_tap", "human", "tg-proposal-button")


-- 2b. ANCHOR (lines 164-169, head of `_grade`) --
OLD:
    def _grade(self, ns, rule, source, candidate):
        """(trust, verb). verb ∈ commit|propose|reject. trust در reject حاملِ دلیل است."""
        committer = rule.get("committer")
        if committer in ("owner_only", "owner_or_deterministic"):
            if source == "owner":
                return "OWNER_CONFIRMED", "commit"

NEW:
    def _owner_source_ok(self, candidate) -> bool:
        """source=="owner" فقط از producerهای سطحِ مالک (یا بدونِ producer = مسیرهای قدیمی).
        producerِ خودکارِ خوداعلام‌کننده (research_loop و امثالش) → False → propose نه commit."""
        prod = str(candidate.get("producer") or "").strip()
        return (not prod) or prod in _OWNER_PRODUCERS

    def _grade(self, ns, rule, source, candidate):
        """(trust, verb). verb ∈ commit|propose|reject. trust در reject حاملِ دلیل است."""
        committer = rule.get("committer")
        if committer in ("owner_only", "owner_or_deterministic"):
            if source == "owner" and self._owner_source_ok(candidate):
                return "OWNER_CONFIRMED", "commit"


=== PATCH 3/6 — F:\backup\_ops\outcomes\research_loop.py ===

-- ANCHOR (lines 362-373) --
OLD:
                oref = f"research|{contract.get('contract_id')}|accepted-measurement"
                outcome_store.record({"correlation_id": str(contract.get("contract_id")),
                                      "proposal_id": str(contract.get("contract_id")), "leg_id": "research",
                                      "event_type": "accepted-measurement", "value_aud_claimed": 0.0,
                                      "idempotency_key": oref})
                lr = _lg.learn_from_outcome(
                    memory_gate=memory_gate, receipt_store=receipt_store, outcome_store=outcome_store,
                    signal={"content": f"research finding: {contract.get('hypothesis')}"[:200],
                            "mkey": f"research-{contract.get('contract_id')}", "namespace": "semantic",
                            "correlation_id": str(contract.get("contract_id")), "outcome_ref": oref,
                            "trust": "OWNER_CONFIRMED", "salience": 0.6,
                            "source": "owner", "producer": "research_loop"},

NEW:
                oref = f"research|{contract.get('contract_id')}|accepted-measurement"
                # ردیفِ outcomeِ **خودنوشته** — صریحاً برچسب‌دار: این رونوشتِ هیچ کنشِ بیرونی
                # نیست، اندازه‌گیریِ حلقه از خودش است. هیچ گواهیِ مالکی ندارد (و نباید داشته باشد).
                outcome_store.record({"correlation_id": str(contract.get("contract_id")),
                                      "proposal_id": str(contract.get("contract_id")), "leg_id": "research",
                                      "event_type": "accepted-measurement", "value_aud_claimed": 0.0,
                                      "idempotency_key": oref,
                                      "payload": {"self_run": True, "measurement_only": True,
                                                  "verifier": str(contract.get("verifier"))[:64],
                                                  "held_out": str(ho.get("overall_verdict"))[:16]}})
                # C3-fix (تراز با taxonomy): آزمایشِ sandboxِ خوداجرا **هرگز** OWNER_CONFIRMED نیست —
                # هیچ مالکی در این مسیر نیست (درایور: c6_trigger.c6_research_beat، یک beatِ روزانه).
                # DETERMINISTIC هم نیست: ورودیِ فرضیه مدل‌زاد است و خروجی یک اندازه‌گیری، نه یک
                # رویهٔ قطعیِ بازتولیدپذیر. سقفِ صادق = GRADED (verifier + held-out + U>0)، و
                # trustِ نهایی را **گیت** می‌دهد نه این‌جا. source هم دیگر برچسبِ ممتازِ owner
                # را حمل نمی‌کند. (namespace عمداً semantic می‌ماند — تنها namespaceی که در
                # درختِ زنده خوانده می‌شود؛ حرکت به self_claim = رأیِ مالک، بخشِ risks.)
                lr = _lg.learn_from_outcome(
                    memory_gate=memory_gate, receipt_store=receipt_store, outcome_store=outcome_store,
                    signal={"content": f"research finding: {contract.get('hypothesis')}"[:200],
                            "mkey": f"research-{contract.get('contract_id')}", "namespace": "semantic",
                            "correlation_id": str(contract.get("contract_id")), "outcome_ref": oref,
                            "trust": "GRADED", "salience": 0.6,
                            "source": "research_loop", "producer": "research_loop"},


=== PATCH 4/6 — F:\backup\_ops\tests\test_learning_loop.py (fixture faithfulness) ===

-- ANCHOR (lines 90-94, inside `_learn`) --
OLD:
    # outcome-binding: یک outcomeِ واقعی ثبت کن تا trust به آن bind شود (red-team P1)
    if record_outcome:
        oc.record({"correlation_id": "corr-L1", "proposal_id": "P1", "leg_id": "lead",
                   "event_type": "accepted-measurement", "value_aud_claimed": 0.0,
                   "idempotency_key": _OREF})

NEW:
    # outcome-binding: یک outcomeِ واقعی ثبت کن تا trust به آن bind شود (red-team P1).
    # C3-fix: ردیف باید از **تنها نویسندهٔ گواهیِ مالک** بیاید، وگرنه خودِ فیکسچر یک جعلِ
    # OWNER_CONFIRMED است. idem همان "corr-L1|P1|accepted-measurement" = _OREF (تغییری در
    # کلید/dedup/مقدار نمی‌دهد؛ فقط payload.owner_verdict_raw + verdict='measurement' اضافه می‌شود).
    if record_outcome:
        import verdict_recorder as _vr  # noqa: WPS433
        _vr.record_owner_verdict(oc, proposal_id="P1", verdict="approved",
                                 correlation_id="corr-L1", leg_id="lead")


=== PATCH 5/6 — NEW FILE F:\backup\_ops\tests\test_c3_owner_trust_forgery.py ===
(full content in the `tests` field)

=== PATCH 6/6 — F:\backup\_ops\tests\run_all.py ===

-- ANCHOR (line 124) --
OLD:
         "test_learning_loop.py",
NEW:
         "test_learning_loop.py",
         # 2026-07-25 C3-fix (owner-trust forgery): «مالک تأیید کرد» فقط با گواهیِ ساختاری روی
         # خودِ ردیفِ outcome — نه با رشتهٔ source="owner". callerِ غیرمالک دیگر نمی‌تواند
         # OWNER_CONFIRMED بسازد؛ مسیرِ واقعیِ رأی دست‌نخورده؛ گواهی تک-نویسنده (تستِ ساختاری).
         "test_c3_owner_trust_forgery.py",
