#!/usr/bin/env python3
from __future__ import annotations
import json

RULES = {
    "R-ACD-01": lambda c: not (c.get("point") is not None and c.get("ci") is None),
    "R-ACD-02": lambda c: c.get("label") != "UNDERPOWERED",
    "R-ACD-03": lambda c: c.get("judge_independent", False),
    "R-EFF-01": lambda c: c.get("owner_vote", False) or c.get("effect_class") == "read_only",
    "R-EFF-02": lambda c: not c.get("may_authorize", False),
    "R-INV-01": lambda c: c.get("tool_validated", True),
    "R-GEN-01": lambda c: c.get("counter_external_actions", 0) == 0,
}

def decide(subject, context):
    for rid, check in RULES.items():
        if not check(context):
            action = "halt" if rid == "R-INV-01" else "deny"
            return action, rid, f"{subject} failed {rid}"
    return "allow", "R-ALL-PASS", f"{subject} passed all rules"

def selftest():
    fx = [
        ("valid", {"point":0.5,"ci":[.3,.7],"label":"PASS","judge_independent":True,"effect_class":"read_only","tool_validated":True,"counter_external_actions":0}, "allow"),
        ("no_ci", {"point":0.5,"ci":None,"label":"PASS","judge_independent":True,"effect_class":"read_only","tool_validated":True,"counter_external_actions":0}, "deny"),
        ("underpowered", {"point":0.3,"ci":[.1,.5],"label":"UNDERPOWERED","judge_independent":True,"effect_class":"read_only","tool_validated":True,"counter_external_actions":0}, "deny"),
        ("ext_no_vote", {"point":0.5,"ci":[.3,.7],"label":"PASS","judge_independent":True,"effect_class":"reversible","owner_vote":False,"tool_validated":True,"counter_external_actions":0}, "deny"),
        ("inv", {"point":0.5,"ci":[.3,.7],"label":"PASS","judge_independent":True,"effect_class":"read_only","tool_validated":False,"counter_external_actions":0}, "halt"),
    ]
    results = [{"name":n,"expected":e,"got":decide(n,c)[0],"pass":decide(n,c)[0]==e} for n,c,e in fx]
    return {"total":len(fx),"passed":sum(1 for r in results if r["pass"]),"results":results}

if __name__ == "__main__":
    print(json.dumps(selftest(), ensure_ascii=False, indent=1))
