#!/usr/bin/env python3
"""NEXT-15 A11/A14 — second-host ledger self-repair run (node 160).

Real fault -> system detection -> one durable disposition -> read-back verify
-> receipt, on the ledger contract v2, executed BY the deployed code path
(EconomicLearningLedger load/recover) with zero engineer intervention inside
the episode window. Three damage families x 2 rounds + restart repetition.
Self-contained: expects ofn/learning/{receipts,ledger}.py next to this file.
"""
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "ofn"))

from ofn.learning.receipts import canonical_json, sha256_text  # noqa: E402
from ofn.learning.ledger import EconomicLearningLedger  # noqa: E402

RUN_ID = "NEXT15-A11A14-" + time.strftime("%Y%m%dT%H%M%SZ")
OUT = HERE / ("receipts-%s.jsonl" % RUN_ID)
HOST = os.uname().nodename


def emit(ev):
    row = {"run_id": RUN_ID, "host": HOST, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ"), **ev}
    with OUT.open("a") as fh:
        fh.write(json.dumps(row) + "\n")
    return row


def fresh_ledger(tag):
    d = HERE / ("case-%s" % tag)
    if d.exists():
        for f in d.iterdir():
            f.unlink()
    d.mkdir(exist_ok=True)
    return EconomicLearningLedger(d / "ledger.jsonl")


def seed(lg, n=4):
    for i in range(n):
        lg.append({"record_id": "%s-R%d" % (RUN_ID, i), "kind": "seed",
                   "outcome": "RECORDED"})


def family_orphan_restart(tag):
    lg = fresh_ledger(tag)
    seed(lg)
    p = lg.path
    row = {"record_id": "%s-ORPH" % RUN_ID, "kind": "demo", "outcome": "IN_FLIGHT"}
    row["line_sha256"] = sha256_text(canonical_json(row))
    with open(p, "a") as fh:
        fh.write(canonical_json(row) + "\n")
    dispositions = 0
    for round_i in range(3):  # three restarts
        EconomicLearningLedger(p)
        content = open(p, encoding="utf-8").read()
        dispositions = content.count("supersedes_line_sha256")
        emit({"family": "orphan_restart", "round": round_i,
              "dispositions": dispositions,
              "stable": dispositions == 1})
    v = EconomicLearningLedger(p).verify()
    return dispositions == 1 and v["valid"] and EconomicLearningLedger(p).orphans() == 0


def family_torn(tag):
    lg = fresh_ledger(tag)
    seed(lg)
    torn = '{"record_id": "T", "kind": "x", "outco'
    with open(lg.path, "a") as fh:
        fh.write(torn + "\n")
    for round_i in range(3):
        EconomicLearningLedger(lg.path)
        content = open(lg.path, encoding="utf-8").read()
        torn_disps = content.count("torn_write_disposition")
        emit({"family": "torn_write", "round": round_i,
              "dispositions": torn_disps, "bytes_preserved": torn in content,
              "stable": torn_disps == 1})
    v = EconomicLearningLedger(lg.path).verify()
    return v["status"] == "TORN_SAFE_HOLD" and torn in open(lg.path, encoding="utf-8").read()


def family_tamper(tag):
    lg = fresh_ledger(tag)
    seed(lg)
    lines = open(lg.path, encoding="utf-8").read().splitlines()
    row = json.loads(lines[1])
    row["kind"] = "hacked"
    lines[1] = json.dumps(row, sort_keys=True, separators=(",", ":"))
    open(lg.path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    v = EconomicLearningLedger(lg.path).verify()
    emit({"family": "content_tamper", "detected": not v["valid"], "status": v["status"]})
    return not v["valid"]


def main():
    emit({"event": "RUN_START", "pid": os.getpid(), "python": sys.version.split()[0]})
    results = {
        "orphan_restart_x1": family_orphan_restart("o1"),
        "torn_write_x1": family_torn("t1"),
        "content_tamper_x1": family_tamper("c1"),
        "orphan_restart_x2": family_orphan_restart("o2"),
        "torn_write_x2": family_torn("t2"),
        "content_tamper_x2": family_tamper("c2"),
    }
    verdict = {"run_id": RUN_ID, "host": HOST,
               "all_pass": all(results.values()), "families": results,
               "scope": "ledger-damage self-repair, system-executed (load/recover path), "
                        "engineer_interventions_in_window: 0",
               "a14_note": "real fleet job on node160 with durable receipt file + read-back"}
    emit({"event": "RUN_VERDICT", **verdict})
    (HERE / ("VERDICT-%s.json" % RUN_ID)).write_text(json.dumps(verdict, indent=2) + "\n")
    print(json.dumps(verdict, indent=1))


if __name__ == "__main__":
    main()
