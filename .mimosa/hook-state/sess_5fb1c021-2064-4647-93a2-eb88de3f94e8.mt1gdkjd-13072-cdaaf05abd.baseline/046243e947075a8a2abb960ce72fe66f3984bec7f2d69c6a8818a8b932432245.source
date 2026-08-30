#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""گرم‌کردنِ حلقهٔ recall — بدون حذف کلید/ردیف.

۱) بردارهای doctor را با encoding پایدار (بدون سیکل، بدون NaN) بازنویسی می‌کند
   روی *همان* کلیدها.
۲) cycle-keyها را از اجزای متناهی دوباره integrate می‌کند.
۳) similar_keys هر ردیف را با انتخابِ دور+نزدیک UNION می‌کند (حذف صفر).

پیش‌فرض: مسیرهای زنده. OPS_DIR برای تست ایزوله.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))
if str(_OPS / "neural") not in sys.path:
    sys.path.insert(0, str(_OPS / "neural"))


def _load_flags() -> None:
    p = _OPS / "OCTOPUS-flags.cmd"
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    for line in text.splitlines():
        s = line.strip()
        if len(s) >= 5 and s[:4].lower() == "set " and "=" in s:
            k, _, v = s[4:].partition("=")
            k, v = k.strip(), v.strip()
            if k and k not in __import__("os").environ:
                __import__("os").environ[k] = v


def measure(hist):
    from neural.consolidation import recall_reach
    m = recall_reach(hist)
    m["rows"] = len(hist)
    return m


def warm(*, persist: bool = True) -> dict:
    import numpy as np
    from neural.encoders import encode_rfc
    from neural.latent_space import SharedLatentSpace
    from neural.consolidation import (
        ConsolidationCycle, select_recall_keys, union_similar_keys, _key_cycle,
    )

    cycle = ConsolidationCycle()
    hist = cycle.history
    before = measure(hist)

    ls = SharedLatentSpace()
    dim = ls.dim
    re_doc = 0
    for key in list(ls.keys()):
        if ":doctor_archive:" not in key:
            continue
        tail = key.rsplit(":", 1)[-1]
        vec = encode_rfc("archive", f"{tail} approved", "medium", dim=dim)
        meta = ls._metadata.get(key, {})
        ls.embed(key, vec, layer=meta.get("layer") or "doctor",
                 source="recall-warm")
        re_doc += 1

    re_cyc = 0
    for key in list(ls.keys()):
        if not (key.startswith("cycle-") and ":" not in key[6:]):
            continue
        parts = [k for k in ls.keys() if k.startswith(key + ":")]
        if not parts:
            continue
        integrated = ls.integrate(parts)
        if not np.isfinite(integrated).all():
            continue
        meta = ls._metadata.get(key, {})
        ls.embed(key, integrated, layer=meta.get("layer") or "consolidation",
                 source="recall-warm")
        re_cyc += 1

    if persist:
        ls.store()

    warmed_rows = 0
    added_keys = 0
    for row in hist:
        if not isinstance(row, dict):
            continue
        own = row.get("cycle")
        if not isinstance(own, int):
            continue
        cycle_key = f"cycle-{own}"
        query = ls.get(cycle_key)
        if query is None or not np.isfinite(query).all():
            school = ls.get(f"{cycle_key}:school_awareness")
            query = school
        if query is None or not np.isfinite(query).all():
            continue
        nn = ls.similar(query, top_k=64)
        incoming = select_recall_keys(nn, cycle_key, limit=8, far_slots=8)
        if not incoming:
            continue
        prev = list(row.get("similar_keys") or [])
        merged = union_similar_keys(prev, incoming)
        if merged != prev:
            added_keys += max(0, len(merged) - len(prev))
            row["similar_keys"] = merged
            warmed_rows += 1

    if persist:
        cycle._history = hist
        cycle._save()

    after = measure(hist)
    return {
        "ok": True,
        "reembedded_doctor": re_doc,
        "reintegrated_cycles": re_cyc,
        "warmed_rows": warmed_rows,
        "added_keys": added_keys,
        "before": before,
        "after": after,
        "written": persist,
    }


if __name__ == "__main__":
    _load_flags()
    persist = "--dry" not in sys.argv
    out = warm(persist=persist)
    print(json.dumps(out, ensure_ascii=False, indent=2))
