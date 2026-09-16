#!/usr/bin/env python3
"""182 independent latch check: kill-after-send must stay 1 transmit."""
from __future__ import annotations
import json, sys, tempfile
from pathlib import Path
ORACLE = Path(__file__).resolve().parent
WT = Path(r"F:\backup\06-EVIDENCE\BOARD-180-REPLY-REPAIR-2026-08-27\pc-worker\worktree")
sys.path.insert(0, str(WT))
from durable_reply import KillAfterSend, Model, Store, Transport, Worker

def main():
    d = Path(tempfile.mkdtemp(dir=ORACLE / "tmp"))
    st = Store(d / "jobs.sqlite")
    model, tr = Model(), Transport()
    w = Worker(st, model, tr)
    tr.kill_after_send = True
    try:
        w.process("latch1", "p")
    except KillAfterSend:
        pass
    rec = st.get("latch1")
    sent1 = len(tr.sent)
    tr.kill_after_send = False
    w.retry("latch1")
    sent2 = len(tr.sent)
    rec2 = st.get("latch1")
    ok = sent1 == 1 and sent2 == 1 and len(model.calls) == 1 and rec["frozen"] == rec2["frozen"]
    out = {
        "case": "kill_after_send_one_transmit",
        "pass": ok,
        "sends": f"{sent1}->{sent2}",
        "model_calls": len(model.calls),
        "after_kill_state": rec["state"] if rec else None,
        "after_retry_state": rec2["state"] if rec2 else None,
        "handed": rec.get("handed") if rec else None,
        "patch_commit": "8fe57d68dc595c19df953d09744166ba8b15f97a",
    }
    (ORACLE / "LATCH-KAS.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
