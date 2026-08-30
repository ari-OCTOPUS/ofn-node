#!/usr/bin/env python3
"""test_c6_receipt_reconciliation — C6: receipt/reconciliation lane (crash windows a+b).

Proves (hermetic, fixture-only, no live DB):
  * sweep_stale_releasables: authorized-but-never-claimed intent is refused after the
    window (safe pre-claim: zero external effect); fresh rows untouched; knob=0 off;
    other statuses never touched. Existing sweep_stale_effects contract UNCHANGED.
  * sweep_stale_executions: worker lost mid-flight → RECONCILE_REQUIRED (never a fake
    refuse — the external effect may have happened); fresh EXECUTING untouched; knob=0 off.
  * reconcile_effect: human resolution of RECONCILE_REQUIRED with mandatory
    evidence+operator; settled fills receipt only if empty (never overwrites);
    failed_safe records no receipt; non-RECONCILE rows refused; halted → refused.
  * effectively-once: after reconciliation, a stale worker's complete_execution can
    never double-settle or rewrite the receipt.
  * redrive_approval (crash window a): a ledger-recorded APPROVAL whose release was
    lost to a crash is re-driven WITHOUT a new ledger append; idempotent (anti-replay);
    batch judgments are never redriven; halted → no redrive.
  * on_human_judgment routing is byte-equivalent after the C6 extraction.

Run: python -X utf8 test_c6_receipt_reconciliation.py
"""
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
import harness   # noqa: E402
ENV = harness.setup("c6-receipt-reconciliation")
import chrono    # noqa: E402
import opslib    # noqa: E402

_FAILED = 0


def check(name, cond):
    global _FAILED
    print(("PASS" if cond else "FAIL"), "-", name)
    if not cond:
        _FAILED += 1


def _db(tag):
    return chrono.ChronoDB(path=opslib.STATE_DIR / f"c6-{tag}.db")


def _appr(db, eid, aid):
    r = db.q("SELECT content_hash, action_kind, target_ref FROM gated_effect "
             "WHERE effect_id=?", (eid,))[0]
    return {"effect_id": eid, "approval_id": aid, "content_hash": r[0],
            "action_kind": r[1], "target_ref": r[2], "expires_at": None,
            "release_ref": "ref-" + str(aid)}


def _released_pay(gate, db, tag):
    e = gate.request("pay", f"order-{tag}", target_ref=f"acct-{tag}")
    assert gate.release_effect(e, _appr(db, e, f"A-{tag}")) is True
    return e


def _ms_ago(hours):
    return int((time.time() - hours * 3600) * 1000)


db = _db("lane")
gate = chrono.EffectorGate(db)

# ── 1) sweep_stale_releasables ──────────────────────────────────────────────────
e_stale = _released_pay(gate, db, "sr-old")
db.ex("UPDATE gated_effect SET approved_at=? WHERE effect_id=?", (_ms_ago(100), e_stale))
e_fresh = _released_pay(gate, db, "sr-new")
r = gate.sweep_stale_releasables(max_age_hours=72)
check("stale releasable (authorized, never claimed) → refused",
      r["refused"] == 1 and e_stale in r["ids"] and gate.status_of(e_stale) == "refused")
check("fresh releasable untouched", gate.status_of(e_fresh) == "releasable")
row = db.q("SELECT failure_reason FROM gated_effect WHERE effect_id=?", (e_stale,))[0]
check("stale releasable carries an explicit sweep reason",
      "stale releasable" in (row[0] or ""))
e_off = _released_pay(gate, db, "sr-off")
db.ex("UPDATE gated_effect SET approved_at=? WHERE effect_id=?", (_ms_ago(500), e_off))
check("knob=0 → releasable sweep off",
      gate.sweep_stale_releasables(max_age_hours=0)["refused"] == 0
      and gate.status_of(e_off) == "releasable")
e_pend = gate.request("pay", "order-sr-pend", target_ref="a")
db.ex("UPDATE gated_effect SET created_ts=? WHERE effect_id=?", (_ms_ago(500), e_pend))
gate.sweep_stale_releasables(max_age_hours=72)
check("releasable sweep never touches pending", gate.status_of(e_pend) == "pending")

# regression pin: the ORIGINAL sweep still refuses only pending, not releasable
# (fresh stale-releasable row created AFTER the last releasable sweep above)
e_pin = _released_pay(gate, db, "sr-pin")
db.ex("UPDATE gated_effect SET approved_at=? WHERE effect_id=?", (_ms_ago(500), e_pin))
r0 = gate.sweep_stale_effects(max_age_hours=72)
check("sweep_stale_effects contract unchanged (refuses stale pending only)",
      e_pin not in r0["ids"] and e_pend in r0["ids"]
      and gate.status_of(e_pin) == "releasable")

# ── 2) sweep_stale_executions ───────────────────────────────────────────────────
e_ex = _released_pay(gate, db, "sx-old")
x_ex = gate.begin_execution(e_ex, worker_ref="lost-worker")
db.ex("UPDATE gated_effect SET execution_started_at=? WHERE effect_id=?",
      (_ms_ago(10), e_ex))
e_ex2 = _released_pay(gate, db, "sx-new")
x_ex2 = gate.begin_execution(e_ex2, worker_ref="live-worker")
r = gate.sweep_stale_executions(max_exec_hours=6)
check("stale EXECUTING → RECONCILE_REQUIRED (never refused)",
      r["reconcile_required"] == 1 and e_ex in r["ids"]
      and gate.status_of(e_ex) == "RECONCILE_REQUIRED")
check("fresh EXECUTING untouched", gate.status_of(e_ex2) == "EXECUTING")
row = db.q("SELECT failure_reason, external_receipt_ref FROM gated_effect "
           "WHERE effect_id=?", (e_ex,))[0]
check("stale execution keeps honest reason, no fabricated receipt",
      "worker lost" in (row[0] or "") and (row[1] or "") == "")
check("knob=0 → execution sweep off",
      gate.sweep_stale_executions(max_exec_hours=0)["reconcile_required"] == 0)
gate.complete_execution(e_ex2, x_ex2, "RCPT-live")   # پاک‌سازی: مسیرِ سالم settle

# ── 3) reconcile_effect — human resolution ──────────────────────────────────────
check("reconcile settled with evidence → settled + receipt filled",
      gate.reconcile_effect(e_ex, "settled", "BANK-STMT-77", "owner") is True
      and gate.status_of(e_ex) == "settled")
row = db.q("SELECT external_receipt_ref, failure_reason FROM gated_effect "
           "WHERE effect_id=?", (e_ex,))[0]
check("reconciled row records evidence as receipt + audit trail",
      row[0] == "BANK-STMT-77" and "reconciled(settled) by owner" in (row[1] or ""))
check("stale worker cannot double-settle a reconciled row (effectively-once)",
      gate.complete_execution(e_ex, x_ex, "RCPT-late") is False
      and db.q("SELECT external_receipt_ref FROM gated_effect WHERE effect_id=?",
               (e_ex,))[0][0] == "BANK-STMT-77")

# halt-during path: receipt recorded at halt time must NOT be overwritten by reconcile
e_hd = _released_pay(gate, db, "hd")
x_hd = gate.begin_execution(e_hd, worker_ref="W")
opslib.STOP_ORGANISM.write_text("test", "utf-8")
try:
    gate.complete_execution(e_hd, x_hd, "RCPT-HALT")     # → RECONCILE_REQUIRED + receipt
finally:
    opslib.STOP_ORGANISM.unlink(missing_ok=True)
check("precondition: halt-during left RECONCILE_REQUIRED with receipt",
      gate.status_of(e_hd) == "RECONCILE_REQUIRED")
gate.reconcile_effect(e_hd, "settled", "EVIDENCE-NEW", "owner")
check("reconcile never overwrites an existing receipt",
      db.q("SELECT external_receipt_ref FROM gated_effect WHERE effect_id=?",
           (e_hd,))[0][0] == "RCPT-HALT" and gate.status_of(e_hd) == "settled")

# failed_safe path — no receipt fabricated
e_fs = _released_pay(gate, db, "fs")
x_fs = gate.begin_execution(e_fs, worker_ref="W")
db.ex("UPDATE gated_effect SET execution_started_at=? WHERE effect_id=?", (_ms_ago(10), e_fs))
gate.sweep_stale_executions(max_exec_hours=6)
check("reconcile failed_safe → FAILED_SAFE, zero receipt",
      gate.reconcile_effect(e_fs, "failed_safe", "PROVIDER-LOG-0-CHARGES", "owner") is True
      and gate.status_of(e_fs) == "FAILED_SAFE"
      and (db.q("SELECT external_receipt_ref FROM gated_effect WHERE effect_id=?",
                (e_fs,))[0][0] or "") == "")

# guards
e_g = _released_pay(gate, db, "guard")
check("reconcile on non-RECONCILE row → False",
      gate.reconcile_effect(e_g, "settled", "EV", "owner") is False
      and gate.status_of(e_g) == "releasable")
e_g2 = _released_pay(gate, db, "guard2")
x_g2 = gate.begin_execution(e_g2, worker_ref="W")
db.ex("UPDATE gated_effect SET execution_started_at=? WHERE effect_id=?", (_ms_ago(10), e_g2))
gate.sweep_stale_executions(max_exec_hours=6)
check("reconcile without evidence → False",
      gate.reconcile_effect(e_g2, "settled", "", "owner") is False)
check("reconcile without operator → False",
      gate.reconcile_effect(e_g2, "settled", "EV", "") is False)
check("reconcile with bogus resolution → False",
      gate.reconcile_effect(e_g2, "maybe", "EV", "owner") is False)
opslib.STOP_ORGANISM.write_text("test", "utf-8")
try:
    check("no reconciliation under halt (D-block)",
          gate.reconcile_effect(e_g2, "settled", "EV", "owner") is False
          and gate.status_of(e_g2) == "RECONCILE_REQUIRED")
finally:
    opslib.STOP_ORGANISM.unlink(missing_ok=True)

# ── 4) reconciliation_report (read-only) ────────────────────────────────────────
rep = gate.reconciliation_report(max_exec_hours=6, max_age_hours=72)
check("report lists the unresolved RECONCILE_REQUIRED row",
      e_g2 in rep["reconcile_required"] and rep["attention_total"] >= 1)
st_before = gate.status_of(e_g2)
gate.reconciliation_report()
check("report has zero side effects", gate.status_of(e_g2) == st_before)

# ── 5) redrive_approval — crash window (a) ──────────────────────────────────────
# crash sim: قضاوتِ پول با binding در ledger ثبت شد ولی release هرگز اجرا نشد.
e_rd = gate.request("pay", "order-rd", target_ref="acct-rd")
j_rd = _appr(db, e_rd, "A-RD")          # همان محتوایی که on_human_judgment می‌ساخت
check("redrive: pending money judgment → releasable (no new ledger append)",
      chrono.redrive_approval(j_rd, "LEDGER-H1", gate) is True
      and gate.status_of(e_rd) == "releasable")
check("redrive is idempotent (second run: no state change, no double release)",
      chrono.redrive_approval(j_rd, "LEDGER-H1", gate) is False
      and gate.status_of(e_rd) == "releasable")
x_rd = gate.begin_execution(e_rd, worker_ref="W")
gate.complete_execution(e_rd, x_rd, "RCPT-RD")
check("redrive after settle → no-op",
      chrono.redrive_approval(j_rd, "LEDGER-H1", gate) is False
      and gate.status_of(e_rd) == "settled")

# batch judgments are NEVER redriven
e_batch = gate.request("send", "internal-rd", target_ref="chan")
check("generic (no effect_id) judgment is never redriven — fail-closed",
      chrono.redrive_approval({"note": "generic"}, "LEDGER-H2", gate) is False
      and gate.status_of(e_batch) == "pending")

# non-money id-only redrive goes through release_one (customer path)
e_one = gate.request("lead_outbound", "customer-rd", target_ref="cust")
check("id-only non-money redrive → release_one path → releasable",
      chrono.redrive_approval({"effect_id": e_one}, "LEDGER-H3", gate) is True
      and gate.status_of(e_one) == "releasable")

# halted → no redrive
e_rd2 = gate.request("pay", "order-rd2", target_ref="acct-rd2")
j_rd2 = _appr(db, e_rd2, "A-RD2")
opslib.STOP_ORGANISM.write_text("test", "utf-8")
try:
    check("no redrive under halt",
          chrono.redrive_approval(j_rd2, "LEDGER-H4", gate) is False
          and gate.status_of(e_rd2) == "pending")
finally:
    opslib.STOP_ORGANISM.unlink(missing_ok=True)
check("empty entry_ref → no redrive",
      chrono.redrive_approval(j_rd2, "", gate) is False
      and gate.status_of(e_rd2) == "pending")

# ── 6) on_human_judgment routing equivalence after extraction ───────────────────
import os
os.environ["OCTOPUS_WIRE_HUMAN_APPEND_GUARD"] = "0"


class _FakeLedger:
    def append(self, event_type, judgment, actor, is_human):
        return {"actor": actor, "is_human": is_human, "hash": "H-EQ"}

    def last_age_tick(self):
        return 0


class _FakeGate:
    def __init__(self):
        self.calls = []

    def release_effect(self, effect_id, approval):
        self.calls.append(("exact", effect_id, approval.get("release_ref")))
        return True

    def release_one(self, effect_id, entry):
        self.calls.append(("one", effect_id, entry.get("hash")))
        return True

    def release_gated_effects(self, entry):
        self.calls.append(("batch", None, entry.get("hash")))
        return 0


g1 = _FakeGate()
chrono.on_human_judgment(
    {"effect_id": "E-m", "content_hash": "ch", "action_kind": "pay",
     "target_ref": "t", "approval_id": "AP"}, gate=g1, ledger=_FakeLedger())
g2 = _FakeGate()
chrono.on_human_judgment({"effect_id": "E-p"}, gate=g2, ledger=_FakeLedger())
g3 = _FakeGate()
chrono.on_human_judgment({"note": "generic"}, gate=g3, ledger=_FakeLedger())
check("post-refactor routing identical (exact / one / batch, ledger hash as ref)",
      g1.calls == [("exact", "E-m", "H-EQ")]
      and g2.calls == [("one", "E-p", "H-EQ")]
      and g3.calls == [("batch", None, "H-EQ")])


if __name__ == "__main__":
    print(f"\n== {_FAILED} failure(s) ==")
    print("OK test_c6_receipt_reconciliation" if _FAILED == 0
          else "FAIL test_c6_receipt_reconciliation")
    sys.exit(1 if _FAILED else 0)
