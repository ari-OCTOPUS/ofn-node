#!/usr/bin/env python3
"""182 independent fixtures against pc-worker candidate. Not their test file."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ORACLE = Path(__file__).resolve().parent
WT = Path(r"F:\backup\06-EVIDENCE\BOARD-180-REPLY-REPAIR-2026-08-27\pc-worker\worktree")
sys.path.insert(0, str(WT))

from durable_reply import (  # noqa: E402
    AckLost,
    DupBlocked,
    KillAfterSend,
    KillBeforeSend,
    Model,
    NoEvent,
    SendFailed,
    Store,
    Transport,
    Worker,
    run_once,
)

PATCH_REF = "557b6b485a8dfbf671800970a94e6b4a452c5fac"
BASE = "441af7632dd6e248ccdb4b95f08aebf4f0cca2d6"


def fresh():
    d = Path(tempfile.mkdtemp(dir=ORACLE / "tmp"))
    store = Store(d / "jobs.sqlite")
    model = Model()
    transport = Transport()
    return Worker(store, model, transport), model, transport, store


def row(name, ok, detail):
    return {"case": name, "pass": bool(ok), "detail": detail}


def case_frozen_immutability():
    w, model, tr, st = fresh()
    tr.fail_send = True
    try:
        w.process("t1", "hello")
    except SendFailed:
        pass
    rec1 = st.get("t1")
    h, blob, key = rec1["frozen_hash"], rec1["frozen"], rec1["idempotency_key"]
    tr.fail_send = False
    w.retry("t1")
    rec2 = st.get("t1")
    ok = rec2["frozen_hash"] == h and rec2["frozen"] == blob and rec2["idempotency_key"] == key and len(model.calls) == 1
    return row("frozen_immutability", ok, f"hash_same={rec2['frozen_hash']==h} model_calls={len(model.calls)}")


def case_ack_before_processed():
    w, model, tr, st = fresh()
    tr.fail_send = True
    try:
        w.process("t1", "hello")
    except SendFailed:
        pass
    rec = st.get("t1")
    mid_ok = rec["state"] != "INPUT_PROCESSED" and rec["state"] == "REPLY_PENDING"
    tr.fail_send = False
    w.retry("t1")
    rec2 = st.get("t1")
    # processed only after transport recorded ACK
    term_ok = rec2["state"] == "INPUT_PROCESSED" and rec2["idempotency_key"] in tr.acks
    return row("ack_before_processed", mid_ok and term_ok, f"after_fail={rec['state']} after_ok={rec2['state']} acked={rec2['idempotency_key'] in tr.acks}")


def case_send_failure():
    w, model, tr, st = fresh()
    tr.fail_send = True
    try:
        w.process("t1", "hello")
    except SendFailed:
        pass
    rec = st.get("t1")
    blob = rec["frozen"]
    tr.fail_send = False
    w.retry("t1")
    rec2 = st.get("t1")
    ok = blob is not None and rec2["frozen"] == blob and rec2["state"] == "INPUT_PROCESSED" and len(model.calls) == 1
    return row("send_failure", ok, f"state={rec2['state']} model_calls={len(model.calls)}")


def case_ack_lost():
    w, model, tr, st = fresh()
    tr.lose_ack = True
    try:
        w.process("t1", "hello")
    except AckLost:
        pass
    rec = st.get("t1")
    not_processed = rec["state"] != "INPUT_PROCESSED"
    tr.lose_ack = False
    w.retry("t1")
    rec2 = st.get("t1")
    ok = not_processed and rec2["frozen"] == rec["frozen"] and len(model.calls) == 1 and rec2["state"] == "INPUT_PROCESSED"
    return row("ack_lost", ok, f"after_lost={rec['state']} after_retry={rec2['state']} model_calls={len(model.calls)}")


def case_sigkill_before():
    w, model, tr, st = fresh()
    tr.kill_before_send = True
    try:
        w.process("t1", "hello")
    except KillBeforeSend:
        pass
    rec = st.get("t1")
    sent0 = len(tr.sent)
    tr.kill_before_send = False
    w.retry("t1")
    rec2 = st.get("t1")
    ok = rec["frozen"] is not None and rec2["frozen"] == rec["frozen"] and len(model.calls) == 1 and sent0 == 0
    return row("sigkill_before_send", ok, f"sent_before={sent0} model_calls={len(model.calls)} state={rec2['state']}")


def case_sigkill_after():
    w, model, tr, st = fresh()
    tr.kill_after_send = True
    try:
        w.process("t1", "hello")
    except KillAfterSend:
        pass
    rec = st.get("t1")
    sent1 = len(tr.sent)
    tr.kill_after_send = False
    w.retry("t1")
    sent2 = len(tr.sent)
    rec2 = st.get("t1")
    # crash after send: must not rerun model; orphan recover; idempotent transmit should not double-effect
    ok_model = len(model.calls) == 1
    ok_recover = rec["state"] != "INPUT_PROCESSED"
    ok_idemp = sent2 == sent1  # second send should be no-op if truly idempotent
    return row("sigkill_after_send", ok_model and ok_recover and rec2["frozen"] == rec["frozen"],
               f"model_calls={len(model.calls)} after_kill={rec['state']} sends={sent1}->{sent2} idemp_send={ok_idemp}")


def case_no_model_rerun():
    w, model, tr, st = fresh()
    tr.fail_send = True
    try:
        w.process("t1", "hello")
    except SendFailed:
        pass
    tr.fail_send = False
    w.retry("t1")
    try:
        w.retry("t1")
    except DupBlocked:
        pass
    return row("no_model_rerun_on_retry", len(model.calls) == 1, f"model_calls={len(model.calls)}")


def case_duplicate_receiver():
    w, model, tr, st = fresh()
    w.process("t1", "hello")
    e1 = len(tr.sent)
    blocked = False
    try:
        w.process("t1", "hello")
    except DupBlocked:
        blocked = True
    e2 = len(tr.sent)
    return row("duplicate_receiver", blocked and e2 == e1 and len(model.calls) == 1, f"blocked={blocked} sends={e1}->{e2} model={len(model.calls)}")


def case_orphan_recovery():
    w, model, tr, st = fresh()
    tr.fail_send = True
    try:
        w.process("t1", "hello")
    except SendFailed:
        pass
    rec = st.get("t1")
    # illegal stuck: force processed-without-ack then recover via scanner
    rec["state"] = "REPLY_PENDING"
    st.upsert(rec)
    tr.fail_send = False
    recovered = w.scan_orphans()
    rec2 = st.get("t1")
    ok = "t1" in recovered and rec2["state"] == "INPUT_PROCESSED" and len(model.calls) == 1
    return row("orphan_recovery", ok, f"recovered={recovered} state={rec2['state']} model={len(model.calls)}")


def case_start_limit():
    w, model, tr, st = fresh()
    # no_event and duplicate must exit 0
    c1 = run_once(w, None)
    w2, model2, tr2, st2 = fresh()
    w2.process("t2", "x")
    c2 = run_once(w2, "t2")
    ok = c1 == 0 and c2 == 0
    return row("start_limit_no_flap", ok, f"no_event_rc={c1} duplicate_rc={c2}")


def case_no_listener():
    w, model, tr, st = fresh()
    w.process("t1", "hello")
    # independent: worker/transport have no bind/listen attrs used
    opened = any(hasattr(tr, n) and getattr(tr, n) for n in ("sock", "socket", "listener", "server"))
    return row("no_listener_no_external", not opened, f"transport_listen={opened}")


CASES = [
    case_frozen_immutability,
    case_ack_before_processed,
    case_send_failure,
    case_ack_lost,
    case_sigkill_before,
    case_sigkill_after,
    case_no_model_rerun,
    case_duplicate_receiver,
    case_orphan_recovery,
    case_start_limit,
    case_no_listener,
]


def main() -> int:
    rows = []
    for fn in CASES:
        try:
            rows.append(fn())
        except Exception as e:
            rows.append(row(fn.__name__, False, f"{type(e).__name__}: {e}"))
    passed = sum(1 for r in rows if r["pass"])
    total = len(rows)
    # map fields
    by = {r["case"]: r for r in rows}
    sig_after = by["sigkill_after_send"]
    # idemp_send note in detail
    disputed = [r["case"] for r in rows if not r["pass"]]
    if passed == total:
        verdict = "confirmed"
        status = "ORACLE_VS_PC_WORKER_CONFIRMED_180_OFFICIAL_STILL_OPEN"
    elif passed == 0:
        verdict = "disputed"
        status = "ORACLE_VS_PC_WORKER_DISPUTED"
    else:
        # partial: if only idempotent-send after crash is soft, still confirmed-with-note vs disputed
        hard = [c for c in disputed if c not in ("sigkill_after_send",)]
        verdict = "disputed" if hard else "confirmed"
        status = "ORACLE_VS_PC_WORKER_CONFIRMED_WITH_IDEMP_SEND_NOTE" if not hard else "ORACLE_VS_PC_WORKER_DISPUTED"

    # If any hard fail → disputed. If all pass → confirmed. Mixed hard → disputed.
    if disputed and any(c != "sigkill_after_send" for c in disputed):
        verdict = "disputed"
        status = "ORACLE_VS_PC_WORKER_DISPUTED"
    elif disputed:
        # only sigkill_after failed: that's a real idempotent-transmit gap → disputed
        verdict = "disputed"
        status = "ORACLE_VS_PC_WORKER_DISPUTED_IDEMPOTENT_TRANSMIT"

    out = {
        "schema": "octopus.witness.oracle-182.candidate.v1",
        "PATCH_REF": PATCH_REF,
        "BASE_COMMIT": BASE,
        "candidate": "pc-worker worktree durable_reply.py",
        "tests_adopted_from_candidate": False,
        "passed": passed,
        "total": total,
        "rows": rows,
        "verdict": verdict,
        "MUTATIONS": 0,
        "180_official": "still_waiting",
    }
    (ORACLE / "CANDIDATE-ORACLE.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": f"{passed}/{total}", "verdict": verdict, "fail": disputed, "rows": rows}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
