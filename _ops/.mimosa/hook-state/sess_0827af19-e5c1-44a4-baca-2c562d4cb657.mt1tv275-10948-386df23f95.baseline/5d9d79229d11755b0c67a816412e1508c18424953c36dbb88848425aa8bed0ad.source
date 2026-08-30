# -*- coding: utf-8 -*-
"""پلِ دکترِ تکاملی/اجزای خودترمیم → chord. **بدونِ import از doctor** (بدونِ چرخه).

قراردادِ فراخوانی (وقتی مالک وایرینگ را رأی داد، از سمتِ doctor صدا زده می‌شود):
    from chord.adapters.doctor_adapter import shadow_assess
    a = shadow_assess(mission_id, observations, dim_claims, context)
    # a["verdict"] فقط «نظرِ مشورتی» است؛ doctor تصمیمِ خودش را طبقِ گیت‌های
    # موجود (approval/allowlist/worktree) می‌گیرد. chord چیزی اجرا نمی‌کند.
"""
from __future__ import annotations

from ..ledger import append
from ..observation import count_contradictions
from ..repair_policy import assess
from ..state_vector import build_state_vector


def shadow_assess(mission_id: str, observations: list,
                  dim_claims: list | None = None,
                  context: dict | None = None,
                  weights: dict | None = None,
                  targets: dict | None = None,
                  log: bool = True) -> dict:
    """ارزیابیِ سایه: محاسبه + ثبت در ledgerِ خودِ chord. هیچ side-effect دیگری ندارد."""
    vec = build_state_vector(observations or [], dim_claims or [],
                             weights=weights, targets=targets)
    a = assess(mission_id, vec, context=context,
               contradiction_count=count_contradictions(observations or []))
    rec = a.to_dict()
    if log:
        try:
            append(rec, dedup_key=f"{a.mission_id}:{a.verdict}:{a.weighted_distance}")
        except Exception:  # noqa: BLE001 — ثبتِ سایه هرگز مسیرِ اصلی را نکشد
            rec["ledger_error"] = True
    return rec
