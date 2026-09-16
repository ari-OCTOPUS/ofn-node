"""Reproduce budget_allows' breaker computation exactly, with diagnostics."""
import json
from pathlib import Path

S = Path("/home/ari/ofn/state/ops-agent/state")
rows = [json.loads(l) for l in open(S / "ops-receipts.jsonl") if l.strip()]
category = "B8_NON_TCB_PATCH_CANARY"

sigs = json.loads((S / "failure-signatures.json").read_text())
fixed_at = max([sg.get("fixed_at", "") for sg in sigs["signatures"]
                if sg.get("category") == category], default="")
print(f"fixed_at={fixed_at!r}  sig_categories={[s.get('category') for s in sigs['signatures']]}")

ex = [r for r in rows if r.get("kind") == "OPS_B_EXECUTED"]
fails = [r for r in ex if r.get("category") == category and r.get("verified") is False]
orej = [r for r in rows if r.get("kind") == "OPS_B_OUTCOME_REJECTED"
        and category[-2:] in str(r.get("category", ""))]

def counts(r):
    return (not fixed_at) or r.get("at", "") > fixed_at

print(f"len(ex)={len(ex)} len(fails)={len(fails)} len(orej)={len(orej)}")
for r in fails + orej:
    print("BAD?", counts(r), "|", r.get("at"), r.get("kind"), "verified=", r.get("verified"),
          "outcome=", r.get("outcome"))
unk = [r for r in ex if r.get("outcome") == "UNKNOWN_EFFECT" and counts(r)]
print("unknown_effect_counting=", len(unk))
n_bad = len([r for r in fails + orej if counts(r)])
print(f"n_bad={n_bad} -> breaker {'OPEN' if n_bad >= 2 or unk else 'CLOSED'}")
