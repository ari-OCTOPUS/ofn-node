#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""collab_coding + live_commands + blackbox_map — hermetic ($0)."""
import json
import os
import sys
import tempfile
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="collab-live-")
os.environ["ORG_ROOT"] = _TMP
os.environ["OPS_DIR"] = str(Path(_TMP) / "_ops")
os.environ["OCTOPUS_WIRE_COLLAB_CODING"] = "1"
os.environ["OCTOPUS_WIRE_IDENTITY_EQ"] = "1"
os.environ["OCTOPUS_WIRE_BLACKBOX_MAP"] = "1"

_OPS = Path(__file__).resolve().parent.parent
for p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "telegram_center")):
    if p not in sys.path:
        sys.path.insert(0, p)

import collab_coding as cc  # noqa: E402
import blackbox_map as bm  # noqa: E402
import live_commands as lc  # noqa: E402
import intent as im  # noqa: E402

# rebind collab queue into temp
cc.STATE = Path(_TMP) / "_ops" / "state" / "collab"
cc.QUEUE = cc.STATE / "proposals.jsonl"

fails = []


def check(cond, label):
    if not cond:
        fails.append(label)


# collab: flag on, propose, ban secrets
r = cc.propose("بهبود امتیازدهنده لید برای کار مسکونی مستقیم")
check(r.get("ok") is True, "propose ok")
check(r["proposal"]["family"] == "lead", "family lead")
check("apply" in r["proposal"] and "FORBIDDEN" in r["proposal"]["apply"], "apply forbidden")
bad = cc.propose("put OCTOPUS_CB_SECRET=abc123 into env")
check(bad.get("ok") is False and "banned" in bad.get("reason", ""), "ban secret pattern")
check("ثبت" in cc.list_card() or "cc-" in cc.list_card(), "list card")

# blackbox map
rep = bm.survey()
check(rep["n"] >= 4, "catalog size")
check(any(i["id"] == "c6_live_loop" for i in rep["items"]), "c6 in catalog")
check("جعبه" in bm.card() or "blackbox" in bm.card().lower() or "nbb" in bm.card().lower(), "card")

# live_commands router
check(lc.handles("/live"), "handles live")
check(lc.handles("/id learner"), "handles id")
check(lc.handles("/code status"), "handles code")
out = lc.dispatch("/code status")
check("propose-only" in out or "collab" in out.lower() or "کد" in out, "code status text")

# intent classification
for sample, want in (
    ("/live", "live_summary"),
    ("هویت", "identity"),
    ("/box", "blackbox"),
    ("/code propose x", "collab_code"),
):
    got = im.classify(sample)["intent"]
    check(got == want, f"intent {sample!r} → {want}, got {got}")

print("FAIL" if fails else "PASS", "— test_collab_and_live_commands")
for f in fails:
    print("  -", f)
sys.exit(1 if fails else 0)
