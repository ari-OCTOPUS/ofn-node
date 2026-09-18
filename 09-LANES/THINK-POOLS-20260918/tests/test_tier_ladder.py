#!/usr/bin/env python3
"""Paired test — provider tier ladder (owner-approved RUN-TO-COMPLETION follow-up).

RED before patch_tier_ladder.py (gemini frontier==flash, deepseek strong==flash),
GREEN after. Reads only model NAMES — never a credential. Follows the
test_provider_failover.py standalone convention.
"""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "providers.py"
spec = importlib.util.spec_from_file_location("prov", SRC)
prov = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prov)

PASS, FAIL = [], []


def check(name, ok, detail=""):
    print(("PASS" if ok else "FAIL"), name, detail if not ok else "")
    (PASS if ok else FAIL).append(name)


# T1 — gemini: frontier must not be weaker than strong
g_std = prov.model("gemini", "standard")
g_str = prov.model("gemini", "strong")
g_fro = prov.model("gemini", "frontier")
check("T1 gemini frontier == strong grade (pro)",
      g_fro == g_str and "pro" in g_fro, f"frontier={g_fro!r} strong={g_str!r}")
check("T1b gemini frontier != standard's flash",
      g_fro != g_std and "flash" not in g_fro, f"frontier={g_fro!r} standard={g_std!r}")

# T2 — deepseek: a real ladder above standard
d_std = prov.model("deepseek", "standard")
d_str = prov.model("deepseek", "strong")
d_fro = prov.model("deepseek", "frontier")
check("T2 deepseek strong above standard",
      d_str != d_std and d_str == "deepseek-v4-pro", f"strong={d_str!r} standard={d_std!r}")
check("T2b deepseek frontier above standard",
      d_fro != d_std and d_fro == "deepseek-v4-pro", f"frontier={d_fro!r}")
check("T2c deepseek reasoning unchanged (v4-pro)",
      prov.model("deepseek", "reasoning") == "deepseek-v4-pro", "")

# T3 — sanity: openai frontier untouched
check("T3 openai frontier still gpt-6-astra",
      prov.model("openai", "frontier") == "gpt-6-astra", "")

# T4 — every resolved tier for gemini/deepseek is an id the provider offers
disc = {}
try:
    import json
    disc = json.loads((HERE.parent / "config" / "discovered-models.json").read_text(encoding="utf-8"))
except (OSError, ValueError):
    pass
if disc:
    ok_ids = True
    detail = ""
    for pid in ("gemini", "deepseek"):
        ids = set(disc.get(pid, {}).get("ids") or [])
        for t in ("standard", "strong", "frontier"):
            m = prov.model(pid, t)
            if ids and m and m not in ids:
                ok_ids = False
                detail += f"{pid}.{t}={m} not in ids; "
    check("T4 resolved tiers are offered ids", ok_ids, detail)
else:
    check("T4 resolved tiers are offered ids", True, "discovery record unreadable - skipped")

print(f"-- {len(PASS)} checks, {len(FAIL)} failed")
sys.exit(1 if FAIL else 0)
