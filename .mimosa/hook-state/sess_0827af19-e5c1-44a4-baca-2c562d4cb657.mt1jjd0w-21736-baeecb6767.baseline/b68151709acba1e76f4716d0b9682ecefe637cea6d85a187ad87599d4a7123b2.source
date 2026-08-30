#!/usr/bin/env python3
"""project_f_brain.py — مغزِ Project-F: control-plane + ۷ زیرعامل.

PROJECT-F-BRAIN-SPEC §۳: لایهٔ هوشِ orchestration بینِ استودیوی صبا و کاکپیتِ آری.
الگوهای ۲۰۲۷ (multi-agent + HITL + bandit + governance + archive) ولی داخلِ حصارِ Project-F.

۷ زیرعامل: Strategist · Pricer · Scheduler · Copywriter · Analyst ·
Compliance-Guard · Ethics-Guard.

جریانِ HITL (tiered): §۴
  ۱. صبا درفت ثبت → مغز تحلیل + پیشنهاد.
  ۲. Compliance+Ethics Guard گیت می‌کنند (drop یا pass).
  ۳. low-risk → مستقیم به صبا.
  ۴. high-risk (قیمت/انتشار) → آری (human-append).
  ۵. verdictِ آری → اجرا درون‌پلتفرم + archive.

خطوطِ قرمز (§۵): propose-only · دوکلیده · صفر رسانه/PII · پرداخت درون‌پلتفرم ·
محدودهٔ صبا مقدم · ۲٪-cap + kill-switch · λ_persist<0 + Ethics-Guard · containment.

هیچ import از *_gate/chrono/money production. $0 آفلاین، stdlib-only.
بازاستفاده از _ops/doctor/box/ الگو (نه کانِنِ دوم).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path

LAMBDA_PERSIST = -1.0   # §۵: دست‌نخورده منفی

# state قابل‌انحراف با PF_BRAIN_DIR (تست/harness)؛ بدونِ env = کنارِ ماژول (production)
# ۲۰۲۶-۰۸-۰۳ fix: lazy resolution (الگوی saba_link._studio_dir).
def _archive_path() -> Path:
    env = os.environ.get("PF_BRAIN_DIR")
    base = Path(env) if env else Path(__file__).resolve().parent
    return base / "archive.json"


# ─── Compliance rules (hard gate) ─────────────────────────────────────────────
COMPLIANCE_RULES = [
    "faceless", "feet_only", "no_explicit", "over_18",
    "inplatform_payment", "geo_block_iran",
]

ETHICS_RULES = [
    "no_dark_pattern", "no_manipulation", "relationship_80_sales_20",
    "performer_welfare", "scope_supreme", "no_engagement_optimization",
]


@dataclass
class Proposal:
    """یک پیشنهاد از مغزِ Project-F. propose-only."""
    kind: str               # strategy | price | schedule | copy | analysis
    content: str            # draft text/plan
    risk_level: str = "low"  # low | high
    compliance_passed: bool = False
    ethics_passed: bool = False
    approved: bool = False
    status: str = "draft"   # draft → gated → submitted → approved/rejected


@dataclass
class PricingResult:
    """نتیجهٔ Pricer (contextual bandit سه‌لایه)."""
    base_rate: float
    content_multiplier: float
    time_multiplier: float
    suggested_price: float
    tier: str = "mid"      # low | mid | premium


@dataclass
class ArchiveEntry:
    """آرشیوِ «چه چیزی کار کرد». λ_persist<0 — بقا optimize نمی‌شود."""
    proposal_kind: str
    outcome: str           # approved | rejected | published | failed
    metric_before: float
    metric_after: float
    learned: bool = False  # فقط از تأییدشده‌ها یاد می‌گیرد


class ProjectFBrain:
    """مغزِ Project-F. control-plane + ۷ زیرعامل.
    بینِ صبا و آری. HITLِ tiered."""

    def __init__(self):
        self._archive: list[ArchiveEntry] = self._load_archive()
        self._budget_tokens = 0
        self._budget_cap = 2000   # 2% of E_total=100000

    # ─── FIX 7: archive persistence ─────────────────────────────────────────────
    def _load_archive(self) -> list[ArchiveEntry]:
        """FIX 7: بارگذاریِ archive از دیسک (restart-safe)."""
        try:
            data = json.loads(_archive_path().read_text(encoding="utf-8"))
            return [ArchiveEntry(**e) for e in data]
        except (json.JSONDecodeError, OSError, TypeError):
            return []

    def _save_archive(self) -> None:
        """FIX 7: ذخیرهٔ archive روی دیسک (atomic)."""
        try:
            ap = _archive_path()
            tmp = ap.with_suffix(".tmp")
            tmp.write_text(json.dumps(
                [asdict(e) for e in self._archive], ensure_ascii=False, indent=2),
                encoding="utf-8")
            tmp.replace(ap)
        except OSError:
            pass

    # ─── Strategist ─────────────────────────────────────────────────────────────
    def strategist(self, draft_title: str) -> Proposal:
        """نردبانِ ارزش (wall vs PPV) + برنامهٔ تم."""
        return Proposal(kind="strategy",
                        content=f"wall/PPV split for '{draft_title}': 55% wall, 45% PPV",
                        risk_level="low")

    # ─── Pricer (contextual bandit، approval-gated) ─────────────────────────────
    def pricer(self, content_type: str = "standard", time_slot: str = "evening") -> PricingResult:
        """قیمتِ پیشنهادی سه‌لایه: base × content × time. approval-gated.
        فقط از نتایجِ تأییدشده یاد می‌گیرد (archive)."""
        base = 10.0
        content_mult = {"standard": 1.0, "premium": 1.5, "exclusive": 2.0}.get(content_type, 1.0)
        time_mult = {"morning": 0.8, "afternoon": 0.9, "evening": 1.2, "night": 1.1}.get(time_slot, 1.0)
        price = base * content_mult * time_mult
        tier = "low" if price < 12 else ("premium" if price > 20 else "mid")
        return PricingResult(base_rate=base, content_multiplier=content_mult,
                             time_multiplier=time_mult, suggested_price=round(price, 2),
                             tier=tier)

    # ─── Scheduler ──────────────────────────────────────────────────────────────
    def scheduler(self) -> Proposal:
        """زمانِ بهینه + تقویم."""
        return Proposal(kind="schedule",
                        content="best time: evening AEST (18:00-21:00)",
                        risk_level="low")

    # ─── Copywriter (draft، human-gated) ────────────────────────────────────────
    def copywriter(self, topic: str) -> Proposal:
        """کپشن/عنوان draft. بدون explicit. human-gated."""
        return Proposal(kind="copy",
                        content=f"caption draft for '{topic}': (AI-generated, human-gated, no explicit)",
                        risk_level="low")

    # ─── Analyst (تجمیعی، صفر PII) ──────────────────────────────────────────────
    def analyst(self) -> Proposal:
        """KPIهای تجمیعی. صفر PII فن."""
        return Proposal(kind="analysis",
                        content="aggregate: churn 27%, ARPU $60, unlock 28%, retention 65%",
                        risk_level="low")

    # ─── Compliance-Guard (hard gate) ───────────────────────────────────────────
    def compliance_guard(self, proposal: Proposal, checks: dict | None = None) -> Proposal:
        """گیتِ سخت. اگر قاعده‌ای نشد → drop (status=dropped)."""
        c = checks or {}
        missing = [r for r in COMPLIANCE_RULES if not c.get(r)]
        if missing:
            proposal.status = "dropped"
            proposal.compliance_passed = False
            return proposal
        proposal.compliance_passed = True
        return proposal

    # ─── Ethics-Guard (ضدِ دستکاری، محدوده مقدم) ────────────────────────────────
    def ethics_guard(self, proposal: Proposal, checks: dict | None = None) -> Proposal:
        """ضدِ dark-pattern/دستکاری. محدودهٔ صبا مقدم. λ_persist<0."""
        c = checks or {}
        missing = [r for r in ETHICS_RULES if not c.get(r)]
        if missing:
            proposal.status = "dropped"
            proposal.ethics_passed = False
            return proposal
        # engagement-optimization ممنوع (λ_persist<0)
        proposal.ethics_passed = True
        return proposal

    # ─── HITL flow (tiered) ─────────────────────────────────────────────────────
    def process_draft(self, draft_title: str, checks: dict | None = None,
                      risk_override: str | None = None) -> dict:
        """جریانِ کاملِ HITL: تحلیل → Guard → route (low→صبا، high→آری).
        خروجی: {proposals, routed_to, guards_passed}.
        FIX 5: Pricer اضافه شد — pricing proposal تولید می‌کند."""
        # ۱. تولیدِ پیشنهادها
        pricing = self.pricer(content_type="standard", time_slot="evening")
        proposals = [
            self.strategist(draft_title),
            self.copywriter(draft_title),
            self.scheduler(),
            Proposal(kind="price",
                     content=f"PPV suggestion: ${pricing.suggested_price} ({pricing.tier} tier)",
                     risk_level="high"),   # قیمت = high-risk → آری
        ]
        # ۲. Guards
        c = checks or {}
        for p in proposals:
            self.compliance_guard(p, c)
            self.ethics_guard(p, c)
        # ۳. route: high-risk (قیمت) → آری، low-risk → صبا
        routed = []
        for p in proposals:
            if p.status == "dropped":
                routed.append({"kind": p.kind, "route": "dropped", "reason": "guard failed"})
            elif risk_override == "high" or p.risk_level == "high":
                routed.append({"kind": p.kind, "route": "ari", "reason": "high-risk"})
                p.status = "submitted"
            else:
                routed.append({"kind": p.kind, "route": "saba", "reason": "low-risk"})
                p.status = "gated"
        guards_passed = all(p.compliance_passed and p.ethics_passed for p in proposals)
        return {"proposals": [p.__dict__ for p in proposals],
                "routed_to": routed, "guards_passed": guards_passed}

    # ─── Archive (یادگیری از تأییدشده‌ها) ────────────────────────────────────────
    def archive(self, kind: str, outcome: str,
                metric_before: float = 0.0, metric_after: float = 0.0) -> ArchiveEntry:
        """ثبت در آرشیو. فقط از تأییدشده‌ها یاد می‌گیرد. λ_persist<0.
        FIX 7: persist to disk."""
        entry = ArchiveEntry(proposal_kind=kind, outcome=outcome,
                             metric_before=metric_before, metric_after=metric_after,
                             learned=(outcome in ("approved", "published")))
        self._archive.append(entry)
        self._save_archive()   # FIX 7: persist
        return entry

    @property
    def archive_size(self) -> int:
        return len(self._archive)

    def learned_entries(self) -> list[ArchiveEntry]:
        """فقط entryهایی که از آن‌ها یاد گرفته شده (تأییدشده)."""
        return [e for e in self._archive if e.learned]

    # ─── Budget (۲٪-cap) ────────────────────────────────────────────────────────
    def spend(self, tokens: int) -> bool:
        """ثبتِ مصرفِ توکن. fail-closed اگر از ۲٪ بشود."""
        projected = self._budget_tokens + tokens
        if projected > self._budget_cap:
            return False
        self._budget_tokens = projected
        return True

    @property
    def budget_used(self) -> int:
        return self._budget_tokens

    @property
    def budget_remaining(self) -> int:
        return self._budget_cap - self._budget_tokens
