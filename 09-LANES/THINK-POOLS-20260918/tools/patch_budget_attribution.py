#!/usr/bin/env python3
"""RUN-TO-COMPLETION item 3 — api_budget.py provider attribution + per-provider cap.

Run ON BOARD 138:  python3 patch_budget_attribution.py

What it does (5 exact, uniqueness-checked replacements):
  R1  reserve() signature: drop the silent provider="sakana-fugu" default;
      refuse to record without a real provider name (PROVIDER_ATTRIBUTION_REQUIRED).
  R2  reserve() charge path: rolling per-provider cap (contract key
      per_provider_cap_usd_24h, default 0.25) -> PROVIDER_CAP_REACHED.
  R3  new helper _provider_spend_24h() — settles in last 24h + open reserves,
      attributed via reserve rows so historical unattributed settles still count.
  R4  settle rows now carry the reserve's provider (kills the 49.4%-unnamed
      source; historical rows are never rewritten — the ledger is hash-chained).
  R5  broker VERSION bump for provenance.

Aborts without touching the file if the preimage sha or any anchor mismatch.
Historical `unknown`/unnamed rows stay untouched by design.
"""
import hashlib
import sys
from pathlib import Path

TARGET = Path("/home/ari/ofn/state/api-budget/api_budget.py")
EXPECTED_PRE = "ff78fee904325e51db492859323a6e302c94527526d569d51467be39d1ec2bbe"

R1_OLD = '''def reserve(task_id: str, purpose: str, est_in_tok: int, max_out_tok: int,
            route_reason: str, ctx_hash: str = "", provider: str = "sakana-fugu",
            model: str | None = None, now: float | None = None) -> dict:
    if any(type(v) is not int or v < 0 for v in (est_in_tok, max_out_tok)):'''
R1_NEW = '''def reserve(task_id: str, purpose: str, est_in_tok: int, max_out_tok: int,
            route_reason: str, ctx_hash: str = "", provider: str | None = None,
            model: str | None = None, now: float | None = None) -> dict:
    provider = (provider or "").strip()
    if provider.lower() in ("", "unknown", "none", "null"):
        return {"ok": False, "error": "PROVIDER_ATTRIBUTION_REQUIRED"}
    if any(type(v) is not int or v < 0 for v in (est_in_tok, max_out_tok)):'''

R2_OLD = '''        ok, why = check_budget(task_id, est_max, now)
        if not ok:
            return {"ok": False, "error": why}
'''
R2_NEW = '''        ok, why = check_budget(task_id, est_max, now)
        if not ok:
            return {"ok": False, "error": why}
        pp_cap = float((contract() or {}).get("per_provider_cap_usd_24h", 0.25))
        pp_spent = _provider_spend_24h(provider, now)
        if pp_spent + est_max > pp_cap:
            return {"ok": False, "error": "PROVIDER_CAP_REACHED", "provider": provider,
                    "provider_spent_usd": round(pp_spent, 6),
                    "provider_cap_usd": pp_cap}
'''

R3_OLD = '''    if month_spend(now) + est_max_usd > float(c.get("max_usd_monthly", 100.0)):
        return False, "MONTHLY_CAP"
    return True, "OK"
'''
R3_NEW = '''    if month_spend(now) + est_max_usd > float(c.get("max_usd_monthly", 100.0)):
        return False, "MONTHLY_CAP"
    return True, "OK"


def _provider_spend_24h(provider: str, now: float) -> float:
    """Per-provider rolling spend: settles in the last 24h plus every open
    reservation of this provider (fail-closed liability), attributed via the
    reserve rows so historical unattributed settles still count."""
    rows = _rows()
    settles = {r.get("request_id"): r for r in rows if r.get("kind") == "settle"}
    cutoff = datetime.fromtimestamp(now - 86400, timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S+00:00")
    total = 0.0
    for r in rows:
        if r.get("kind") != "reserve" or r.get("provider") != provider:
            continue
        s = settles.get(r.get("request_id"))
        if s is not None:
            if str(s.get("at", "")) > cutoff:
                total += float(s.get("cost_usd", 0.0) or 0.0)
        else:
            total += float(r.get("est_max_usd", 0.0) or 0.0)
    return total
'''

R4_OLD = '''    _append({"schema": "octopus.api-budget.v1", "kind": "settle",
             "request_id": request_id, "task_id": res["task_id"], "at": now_iso(),'''
R4_NEW = '''    _append({"schema": "octopus.api-budget.v1", "kind": "settle",
             "provider": res.get("provider", ""),
             "request_id": request_id, "task_id": res["task_id"], "at": now_iso(),'''

R5_OLD = 'VERSION = "octopus-api-budget-broker/1.1.0-multiprovider"'
R5_NEW = 'VERSION = "octopus-api-budget-broker/1.2.0-provider-attribution"'

REPLACEMENTS = [("R1 signature+guard", R1_OLD, R1_NEW),
                ("R2 per-provider cap", R2_OLD, R2_NEW),
                ("R3 helper", R3_OLD, R3_NEW),
                ("R4 settle attribution", R4_OLD, R4_NEW),
                ("R5 version", R5_OLD, R5_NEW)]


def main() -> int:
    pre = hashlib.sha256(TARGET.read_bytes()).hexdigest()
    if pre != EXPECTED_PRE:
        print("PREIMAGE_MISMATCH", pre)
        return 2
    src = TARGET.read_text(encoding="utf-8")
    for name, old, new in REPLACEMENTS:
        n = src.count(old)
        if n != 1:
            print(f"ABORT anchor {name} count={n}")
            return 3
        src = src.replace(old, new)
    with TARGET.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(src)
    post = hashlib.sha256(TARGET.read_bytes()).hexdigest()
    print("PREIMAGE ", pre)
    print("POSTIMAGE", post)
    print("PATCHED", len(REPLACEMENTS), "replacements")
    return 0


if __name__ == "__main__":
    sys.exit(main())
