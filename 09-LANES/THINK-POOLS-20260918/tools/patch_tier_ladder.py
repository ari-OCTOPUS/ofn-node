#!/usr/bin/env python3
"""Owner-approved fix (RUN-TO-COMPLETION item 4 follow-up): provider tier ladder.

Measured defects (2026-09-18):
  gemini   frontier -> gemini-3.8-flash  (falls back to standard; its own
           strong is gemini-3.1-pro-preview -> frontier was WEAKER than strong)
  deepseek strong/frontier -> deepseek-flash (no ladder at all), even though
           the discovery record proves deepseek-v4-pro is on offer.

Root cause (both): providers.model() only CONSIDERS a tier when the tier's env
var is set — and deepseek had no strong/frontier keys in model_vars at all.
The discovered tiers record (authoritative "ids actually offered") was never
consulted for those tiers.

Fix:
  R1  model(): discovery tiers first, env vars as fallback (not as gate).
      Also documents the regeneration rules if discovered-models.json is
      ever rebuilt (no in-tree generator exists today).
  R2  deepseek model_vars: add strong/frontier env names.
  R3  discovered-models.json: gemini.frontier=gemini-3.1-pro-preview (best pro
      on offer = same grade as strong, honest), deepseek.strong/frontier=
      deepseek-v4-pro (best id on offer), with tier_changes entries recorded
      in the file's own schema.

Run ON 138. Aborts without writing on any preimage/anchor mismatch.
"""
import hashlib
import json
import sys
from pathlib import Path

PROVIDERS = Path("/home/ari/ofn/state/api-budget/providers.py")
DISCOVERY = Path("/home/ari/ofn/state/api-budget/config/discovered-models.json")
PRE_PROVIDERS = "c4e3380b170bb6a41ebde23d7322e08ae8e684fef390846ab77882fc4e8b1748"
PRE_DISCOVERY = "cfb938950dbd7d1ddbf84a003de4bf1c12562a0db8bc73ef2549185a3fff2f61"

R1_OLD = '''    for t in (tier, "standard", "strong", "economy", "frontier", "local"):
        env_name = env().get(mv.get(t, ""), "") if mv.get(t) else ""
        if not env_name:
            continue
        if tiers.get(t):
            return tiers[t]
        return env_name
    return ""
'''
R1_NEW = '''    # Discovery record is authoritative: a tier entry means the provider
    # really offers that model. Env vars are the fallback, not the gate —
    # gating on env presence is what let tier=frontier silently fall back to
    # standard for gemini and both strong/frontier fall back for deepseek
    # (measured 2026-09-18, owner-approved tier-ladder fix).
    # If discovered-models.json is ever regenerated, keep these rules:
    #   gemini.frontier   = gemini-3.1-pro-preview (best pro on offer)
    #   deepseek.strong   = deepseek-v4-pro       (best id on offer)
    #   deepseek.frontier = deepseek-v4-pro
    for t in (tier, "standard", "strong", "economy", "frontier", "local"):
        if tiers.get(t):
            return tiers[t]
        env_name = env().get(mv.get(t, ""), "") if mv.get(t) else ""
        if env_name:
            return env_name
    return ""
'''

R2_OLD = '''        model_vars={"standard": "DEEPSEEK_MODEL_STANDARD",
                    "reasoning": "DEEPSEEK_MODEL_REASONING"},'''
R2_NEW = '''        model_vars={"standard": "DEEPSEEK_MODEL_STANDARD",
                    "strong": "DEEPSEEK_MODEL_STRONG",
                    "frontier": "DEEPSEEK_MODEL_FRONTIER",
                    "reasoning": "DEEPSEEK_MODEL_REASONING"},'''


def main() -> int:
    pre = hashlib.sha256(PROVIDERS.read_bytes()).hexdigest()
    pre2 = hashlib.sha256(DISCOVERY.read_bytes()).hexdigest()
    if pre != PRE_PROVIDERS:
        print("PREIMAGE_MISMATCH providers.py", pre)
        return 2
    if pre2 != PRE_DISCOVERY:
        print("PREIMAGE_MISMATCH discovered-models.json", pre2)
        return 2

    src = PROVIDERS.read_text(encoding="utf-8")
    for name, old, new in (("R1 model()", R1_OLD, R1_NEW), ("R2 deepseek vars", R2_OLD, R2_NEW)):
        n = src.count(old)
        if n != 1:
            print(f"ABORT anchor {name} count={n}")
            return 3
        src = src.replace(old, new)
    with PROVIDERS.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(src)

    data = json.loads(DISCOVERY.read_text(encoding="utf-8"))
    g = data["gemini"]
    g.setdefault("tiers", {})["frontier"] = "gemini-3.1-pro-preview"
    g.setdefault("tier_changes", {})["frontier"] = {
        "configured": None, "resolved": "gemini-3.1-pro-preview",
        "why": "owner-approved 2026-09-18: frontier must not be weaker than strong"}
    ds = data["deepseek"]
    ds.setdefault("tiers", {})["strong"] = "deepseek-v4-pro"
    ds.setdefault("tiers", {})["frontier"] = "deepseek-v4-pro"
    ds.setdefault("tier_changes", {})["strong"] = {
        "configured": None, "resolved": "deepseek-v4-pro",
        "why": "owner-approved 2026-09-18: ladder above standard existed but was unmapped"}
    ds.setdefault("tier_changes", {})["frontier"] = {
        "configured": None, "resolved": "deepseek-v4-pro",
        "why": "owner-approved 2026-09-18: best id on offer for the strongest tier"}
    DISCOVERY.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n",
                         encoding="utf-8", newline="\n")

    print("PREIMAGE providers", pre)
    print("POSTIMAGE providers", hashlib.sha256(PROVIDERS.read_bytes()).hexdigest())
    print("PREIMAGE discovery", pre2)
    print("POSTIMAGE discovery", hashlib.sha256(DISCOVERY.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
