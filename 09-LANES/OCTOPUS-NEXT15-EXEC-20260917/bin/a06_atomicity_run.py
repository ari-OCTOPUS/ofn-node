#!/usr/bin/env python3
"""NEXT-15 A06 — atomic reservation under concurrency + crash persistence.

Runs against the ISOLATED drill copy of the api-budget broker on 182
(/root/s2-m6-drill-20260917, ROOT repointed, fcntl lock real). Nothing live.
"""
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

DRILL = Path("/root/s2-m6-drill-20260917")


def load():
    spec = importlib.util.spec_from_file_location("abd", str(DRILL / "api_budget_drill.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["abd"] = mod
    spec.loader.exec_module(mod)
    sys.path.insert(0, str(DRILL))
    return mod


CHILD = r'''
import importlib.util, sys, os
spec = importlib.util.spec_from_file_location("abd", "%s/api_budget_drill.py")
mod = importlib.util.module_from_spec(spec); sys.modules["abd"]=mod; spec.loader.exec_module(mod)
r = mod.reserve(task_id=sys.argv[1], purpose="a06-concurrency", est_in_tok=100000,
                max_out_tok=0, route_reason="a06-test")
print(r.get("ok", r) if isinstance(r, dict) else r)
''' % str(DRILL)

CRASHER = r'''
import importlib.util, sys, os
spec = importlib.util.spec_from_file_location("abd", "%s/api_budget_drill.py")
mod = importlib.util.module_from_spec(spec); sys.modules["abd"]=mod; spec.loader.exec_module(mod)
mod.reserve(task_id="a06-crasher", purpose="a06-crash-then-die", est_in_tok=50000,
            max_out_tok=0, route_reason="a06-test")
os._exit(9)  # die WITHOUT settle — outcome unknown
''' % str(DRILL)


def main():
    ab = load()
    plan = [(100000, 50000, 19230)] * 3  # rolling pre-load = $6
    for i, (est, vis, orch) in enumerate(plan):
        r = ab.reserve(task_id="a06-prep-%d" % i, purpose="a06-prep",
                       est_in_tok=est, max_out_tok=0, route_reason="a06-test")
        ab.settle(request_id=r["request_id"], visible_tokens=vis,
                  orchestration_tokens=orch, latency_s=0.1,
                  response_sha="a06-prep-%d" % i, retained=False)
    # crasher FIRST: reserve $1 then hard-exit without settle
    pc = subprocess.run([sys.executable, "-c", CRASHER], capture_output=True, text=True)
    before = ab.month_spend(time.time())
    pa = subprocess.Popen([sys.executable, "-c", CHILD, "a06-proc-A"],
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    pb = subprocess.Popen([sys.executable, "-c", CHILD, "a06-proc-B"],
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    outs = [p.communicate()[0].strip() for p in (pa, pb)]
    accepted = sum(1 for o in outs if "True" in o)
    refused = sum(1 for o in outs if "False" in o or "CAP" in o)
    after = load()
    spent_after = after.month_spend(time.time())
    rows = after._rows()
    crasher_reserved = any(r.get("task_id") == "a06-crasher" and r.get("kind") == "reserve" for r in rows)
    crasher_settled = any(r.get("task_id") == "a06-crasher" and r.get("kind") == "settle" for r in rows)
    crasher_liability_retained = spent_after >= before  # reload still counts it
    result = {
        "concurrency": {"proc_outputs": outs, "accepted": accepted, "refused": refused,
                        "exactly_one_accepted": accepted == 1},
        "crash_persistence": {"exit_code": pc.returncode,
                              "reservation_persisted": crasher_reserved,
                              "no_settle_freed": not crasher_settled,
                              "month_before": round(before, 6),
                              "month_after": round(spent_after, 6)},
        "verdict_pass": accepted == 1 and crasher_reserved and not crasher_settled and crasher_liability_retained,
    }
    print(json.dumps(result, indent=1))
    (DRILL / "A06-CONCURRENCY-RESULT.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
