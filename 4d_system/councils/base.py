"""BaseCouncil — شورای پایه با نظرهای مهرشده (سایهٔ محض).

قواعد COUNCIL-MESH: اعضا فقط زمینهٔ ناشناس می‌بینند · نظرها مهر و ناشناس
می‌مانند · شورا هیچ ابزاری اجرا نمی‌کند (صفر tool access) · خروجی =
DecisionArtifact با dissent حفظ‌شده.
"""
from __future__ import annotations

import hashlib
import secrets
from typing import Any, Callable

from councils.schemas import (DecisionArtifact, SealedOpinion, Claim,
                              now_iso, score_opinions, ARTIFACT_VERSION)

SHADOW = True   # ثابتِ ماژول — هیچ مسیر اجرایی ساخته نمی‌شود


class CouncilMember:
    """عضو = تابعِ نظر (opinion_fn) + خانوادهٔ شواهد. ابزار ندارد و ندارد."""


# ═══ STATUS: CLOSED (2026-08-19, OWNER-QUEUE-RESOLUTION Q4) ═══
# شوراها DEAD-BY-DESIGN بودند (shadow vote-seeking)؛ حکم مالک Q4: بستهٔ رسمی — نه حذف، نه فعال‌سازی؛ فعال‌سازی توجیه نشده.
# کد حذف نمی‌شود؛ صرفاً از نقشهٔ فعال خارج است (canonical: _ops/cortex/model_router.py).

    def __init__(self, name: str, family: str,
                 opinion_fn: Callable[[dict], dict]):
        self._name = name            # فقط برای ثبتِ داخلی؛ به نظر نمی‌آید
        self.family = family
        self._fn = opinion_fn

    def opine(self, anonymized_context: dict) -> dict[str, Any]:
        out = dict(self._fn(anonymized_context) or {})
        out.setdefault("opinion", "")
        out.setdefault("evidence", [])
        out.setdefault("confidence", 0.0)
        out.setdefault("dissent", None)
        out.setdefault("reproducible", False)
        out.setdefault("policy_violation", False)
        out.setdefault("falsifiable", True)
        return out


def _seal(payload: dict, family: str) -> SealedOpinion:
    blob = repr(sorted(payload.items())).encode("utf-8", "replace")
    return SealedOpinion(digest=hashlib.sha256(blob).hexdigest()[:16],
                         payload=payload, family=family)


class BaseCouncil:
    name = "base"
    zero_tool_access = True        # گارد حاکمیتی: تست این را می‌سنجد

    def __init__(self, name: str | None = None,
                 members: list[CouncilMember] | None = None):
        if name is not None:          # وگرنه attribute کلاسِ زیرشاخه می‌ماند
            self.name = name
        self.members = members or []

    # ── زمینهٔ ناشناس: هیچ نام/هویت/نظرِ عضو دیگر به عضو نمی‌رسد ─────────
    def _anonymize(self, task: dict) -> dict:
        return {"task": dict(task), "council": self.name,
                "mode": "shadow-deliberation", "peers_visible": False}

    def deliberate(self, task: dict) -> list[SealedOpinion]:
        ctx = self._anonymize(task)
        sealed = []
        for m in self.members:
            try:
                sealed.append(_seal(m.opine(ctx), m.family))
            except TimeoutError:
                # chaos: عضوِ معطل ایزوله می‌شود — شورا نمی‌میرد
                sealed.append(_seal({"opinion": "__member_timeout__",
                                     "confidence": 0.0, "evidence": [],
                                     "timeout": True}, m.family))
        return sealed

    def decide(self, task: dict) -> DecisionArtifact:
        sealed = self.deliberate(task)
        scoring = score_opinions(sealed)
        rejected = scoring["P"] != 1.0 or scoring["rogue_confidence_no_evidence"] > 0

        claims = []
        for i, s in enumerate(sealed):
            if s.payload.get("opinion") and s.payload["opinion"] != "__member_timeout__":
                claims.append(Claim(
                    claim_id=f"c{i+1}",
                    text=str(s.payload["opinion"])[:400],
                    evidence_refs=[f"e{i}-{j}" for j in
                                   range(len(s.payload.get("evidence") or []))],
                    falsification_status=(
                        "unfalsified" if s.payload.get("falsifiable")
                        else "untestable")))

        dissent = [s.payload["dissent"] for s in sealed if s.payload.get("dissent")]

        # تشخیص تناقضِ ارائه‌دهنده‌ها: نه میانگین، نه حذف — پرچم
        contradiction = len({s.payload.get("verdict")
                             for s in sealed
                             if s.payload.get("verdict")}) > 1

        return DecisionArtifact(
            schema_version=ARTIFACT_VERSION,
            artifact_id=f"da-{secrets.token_hex(6)}",
            created_at=now_iso(),
            council=self.name,
            task=dict(task),
            claims=claims,
            evidence_refs={f"e{i}-{j}": str(ev)[:120]
                           for i, s in enumerate(sealed)
                           for j, ev in enumerate(s.payload.get("evidence") or [])},
            falsification_status=("mixed" if contradiction else "unfalsified"),
            gates={"shadow_only": True, "policy_P": scoring["P"],
                   "go_no_go": "NO-GO (سایه — فعال‌سازی فقط با گیت‌های سند)"},
            capability_token=None,
            provenance={"member_count": len(self.members),
                        "families": sorted({m.family for m in self.members}),
                        "sealed_digests": [s.digest for s in sealed],
                        "contradictory_providers": contradiction},
            dissent=dissent,
            scoring=scoring,
            decision={"status": "rejected" if rejected else "proposal",
                      "reason": ("P≠1 (نقض سیاست) یا rogue-confidence بی‌شواهد"
                                 if rejected else "پیشنهادِ سایه — صلاحیت اجرا: هیچ")},
            shadow=SHADOW,
        )
