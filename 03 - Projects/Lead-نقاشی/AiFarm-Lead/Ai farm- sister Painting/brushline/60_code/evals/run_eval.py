#!/usr/bin/env python3
"""
P6 -- Gate/content evaluation harness (KB-08). OFFLINE, CI-runnable.

Runs a golden set of drafts through the Constitution Gate and reports:
  - per-dimension precision / recall (consent, ABN, opt-out, ACL, PII)
  - overall gate status accuracy
  - false HARD_BLOCK count (blocking something that should PASS/SOFT_FLAG)
  - eval LLM spend (0 for the deterministic set; small for semantic-ACL cases,
    which use a FAKE Sonnet client -- no network)

Exit 0 = every golden case matches expectation; exit 1 = a gate regression.
CI runs this (`make eval`) so a compliance regression fails the build.
Run locally: python3 evals/run_eval.py
"""
import json
import os
import sys
import tempfile

# Offline env BEFORE importing config (singleton reads env at import).
_TMP = tempfile.mkstemp(suffix="_brushline_eval.db")[1]
os.environ.setdefault("BRUSHLINE_DB_PATH", _TMP)
os.environ.setdefault("KILL_SWITCH_FILE", _TMP + ".KILL")
os.environ.setdefault("ANTHROPIC_API_KEY", "")
os.environ.setdefault("SERPER_API_KEY", "")
os.environ.setdefault("ALLOWED_OPERATOR_CHAT_IDS", "")
os.environ.setdefault("BUSINESS_NAME", "Sister Painting")
os.environ.setdefault("BUSINESS_ABN", "11222333444")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import init_db, get_connection
from src.gate import ConstitutionGate
from src.models import Draft, DraftType
from src.governance import get_daily_spend_aud

ABN = "11222333444"
DIMS = ["consent", "abn", "optout", "acl", "pii"]


def _dim_of(flag: str):
    if flag.startswith("SPAM_NO_CONSENT"):        return "consent"
    if flag.startswith("SENDER_ID_MISSING_ABN"):  return "abn"
    if flag.startswith("NO_OPT_OUT"):             return "optout"
    if flag.startswith("ACL_"):                   return "acl"
    if flag.startswith("PII_"):                   return "pii"
    return None


class _FakeLLM:
    """Deterministic stand-in for Sonnet in semantic-ACL golden cases."""
    def __init__(self, claims):
        self._claims = claims
        self.messages = self

    def create(self, **kw):
        text = json.dumps({"claims": self._claims})
        return type("M", (), {
            "content": [type("C", (), {"text": text})()],
            "usage": type("U", (), {"input_tokens": 120, "output_tokens": 20})(),
        })()


# (label, draft_type, content, consent, expect_status, expect_dims, fake_claims)
GOLDEN = [
    ("lead_pass",        "speed_to_lead",  "Hi, thanks for your enquiry. ABN " + ABN + ". Reply STOP to opt out.", True,  "pass",       set(),        None),
    ("lead_no_consent",  "speed_to_lead",  "Hi there. ABN " + ABN + ". Reply STOP to opt out.",                    False, "hard_block", {"consent"},  None),
    ("lead_no_abn",      "speed_to_lead",  "Hi there. Reply STOP to opt out.",                                     True,  "hard_block", {"abn"},      None),
    ("lead_no_optout",   "speed_to_lead",  "Hi there. ABN " + ABN + ".",                                           True,  "hard_block", {"optout"},   None),
    ("lead_superlative", "speed_to_lead",  "We are the best painters. ABN " + ABN + ". Reply STOP to opt out.",    True,  "soft_flag",  {"acl"},      None),
    ("lead_pii",         "speed_to_lead",  "Email jordan@example.com. ABN " + ABN + ". Reply STOP to opt out.",    True,  "soft_flag",  {"pii"},      None),
    ("review_pass",      "review_response","Thanks so much for the review. -- Sister Painting ABN " + ABN,         False, "pass",       set(),        None),
    ("review_no_abn",    "review_response","Thanks so much for the review, we appreciate it.",                     False, "hard_block", {"abn"},      None),
    ("review_superlat",  "review_response","We are the cheapest in town. -- Sister Painting ABN " + ABN,           False, "soft_flag",  {"acl"},      None),
    ("followup_pass",    "followup",       "Just checking in on your quote. ABN " + ABN + ". Reply STOP to opt out.", True, "pass",      set(),        None),
    ("suburb_clean",     "suburb_page",    "House painting in Glebe. Free no-obligation quote available.",         False, "pass",       set(),        None),
    ("suburb_superlat",  "suburb_page",    "The best painters in Glebe, Sydney.",                                  False, "soft_flag",  {"acl"},      None),
    ("suburb_pii",       "suburb_page",    "Call 0400111222 for a painting quote in Glebe.",                       False, "soft_flag",  {"pii"},      None),
    ("suburb_semantic",  "suburb_page",    "Trusted by thousands of Glebe homeowners for house painting.",         False, "soft_flag",  {"acl"},      ["trusted by thousands"]),
    ("suburb_sem_clean", "suburb_page",    "Interior and exterior house painting in Glebe. Free quote.",           False, "pass",       set(),        []),
]


def _save_draft(d: Draft) -> None:
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO drafts (id, lead_id, draft_type, content, agent_id,
               model_used, tokens_in, tokens_out, cost_usd, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (d.id, None, d.draft_type.value, d.content, d.agent_id,
             d.model_used, 0, 0, 0.0, d.created_at.isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def evaluate(cases):
    """Return (report_dict, passed_bool). passed == no golden mismatch."""
    init_db()
    stats = {d: {"tp": 0, "fp": 0, "fn": 0} for d in DIMS}
    status_ok = 0
    false_hard = 0
    mismatches = []

    for (label, dt, content, consent, exp_status, exp_dims, fake_claims) in cases:
        g = ConstitutionGate()
        if fake_claims is not None:
            g._llm = _FakeLLM(fake_claims)
        d = Draft(draft_type=DraftType(dt), content=content,
                  agent_id="eval", model_used="x")
        _save_draft(d)
        res = g.check(d, consent_verified=consent)
        pred_status = res.status.value
        pred_dims = set(x for x in (_dim_of(f) for f in res.flags) if x)

        for dim in DIMS:
            in_exp, in_pred = dim in exp_dims, dim in pred_dims
            if in_exp and in_pred:
                stats[dim]["tp"] += 1
            elif in_pred and not in_exp:
                stats[dim]["fp"] += 1
            elif in_exp and not in_pred:
                stats[dim]["fn"] += 1

        if pred_status == exp_status:
            status_ok += 1
        else:
            mismatches.append((label, "status", exp_status, pred_status))
        if pred_dims != exp_dims:
            mismatches.append((label, "dims", sorted(exp_dims), sorted(pred_dims)))
        if pred_status == "hard_block" and exp_status != "hard_block":
            false_hard += 1

    total = len(cases)
    report = {
        "total": total,
        "status_accuracy": status_ok / total if total else 1.0,
        "false_hard_block": false_hard,
        "eval_spend_aud": round(get_daily_spend_aud(), 6),
        "dims": {},
        "mismatches": mismatches,
    }
    for dim in DIMS:
        tp, fp, fn = stats[dim]["tp"], stats[dim]["fp"], stats[dim]["fn"]
        report["dims"][dim] = {
            "tp": tp, "fp": fp, "fn": fn,
            "precision": round(tp / (tp + fp), 3) if (tp + fp) else 1.0,
            "recall": round(tp / (tp + fn), 3) if (tp + fn) else 1.0,
        }
    return report, (len(mismatches) == 0)


def format_report(r) -> str:
    out = ["=== Brushline Gate Eval (P6, KB-08) ==="]
    out.append(f"cases: {r['total']}   status accuracy: {r['status_accuracy']*100:.1f}%"
               f"   false HARD_BLOCK: {r['false_hard_block']}")
    out.append(f"eval LLM spend (fake semantic): AUD {r['eval_spend_aud']}")
    out.append("dimension   precision  recall   (tp/fp/fn)")
    for dim, m in r["dims"].items():
        out.append(f"  {dim:<9} {m['precision']:>7.3f}  {m['recall']:>6.3f}   "
                   f"({m['tp']}/{m['fp']}/{m['fn']})")
    if r["mismatches"]:
        out.append("REGRESSIONS:")
        for mm in r["mismatches"]:
            out.append("  " + str(mm))
    return "\n".join(out)


def main():
    report, passed = evaluate(GOLDEN)
    print(format_report(report))
    print("\nRESULT:", "PASS" if passed else "FAIL (gate regression -- see above)")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
