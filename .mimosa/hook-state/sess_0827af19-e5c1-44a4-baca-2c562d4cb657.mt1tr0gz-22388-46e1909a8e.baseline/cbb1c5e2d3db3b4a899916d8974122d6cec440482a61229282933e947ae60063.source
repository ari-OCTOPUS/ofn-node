"""
ace.py — حلقه‌ی ACE (Agentic Context Engineering) به‌صورتِ «خودپیشنهاددهنده».

طبقِ چشم‌اندازِ Unified Agent Prompt (بخش ۶) و گاردریلِ no-self-edit:
عامل system instructions/قاعده‌ی خودش را **هرگز** خودکار بازنویسی نمی‌کند؛ فقط
درس را به‌شکلِ یک proposal تولید می‌کند و انسان تأیید می‌کند (HITL).

سه نقش:
  • Generator → مسیر/پاسخ تولید شد (ورودیِ این ماژول؛ trace + outcome).
  • Reflector → خطا/کمبود را تشخیص می‌دهد، کانِ شکستِ گم‌شده را پیدا می‌کند.
  • Curator  → درس را به‌صورتِ یک diffِ procedural (playbook) پیشنهاد می‌دهد —
               نه اعمالِ خودکار. به‌صورتِ status="pending" در db ذخیره می‌شود.

خالص و قاعده‌محور (بدونِ LLM)؛ db تزریق‌پذیر است تا تست‌پذیر بماند.
هیچ side-effectِ مخرب ندارد: فقط نوشتنِ proposalِ pending که انسان approve/reject می‌کند.
"""

from __future__ import annotations

from dataclasses import dataclass, field

MIN_SAMPLES = 5          # گیتِ کلی: کمتر از این کل، اصلاً reflect نکن (همسو با SelfImprover)
MIN_LABEL_SAMPLES = 3    # گیتِ هر دسته: کمتر از این در یک label، برایش پیشنهاد نده
FAILURE_RATE_GATE = 0.3  # اگر نرخِ شکستِ یک الگو از این بیشتر بود → پیشنهادِ playbook


@dataclass
class Outcome:
    """نتیجه‌ی یک اجرا (Generator)."""
    task: str
    ok: bool
    label: str = "general"     # دسته‌ی کار (مثلِ research/coach/health)
    error: str = ""            # پیامِ خطا در صورتِ شکست
    note: str = ""


@dataclass
class Proposal:
    """خروجیِ Curator — یک تغییرِ procedural پیشنهادی (نه اعمال‌شده)."""
    label: str
    title: str
    playbook: str              # متنِ قاعده‌ی پیشنهادی (افزودنی، نه بازنویسی)
    evidence: dict = field(default_factory=dict)
    status: str = "pending"


class ACEReflector:
    """خطاها/کمبودها را روی مجموعه‌ای از Outcomeها جمع‌بندی می‌کند."""

    @staticmethod
    def reflect(outcomes: list[Outcome]) -> dict:
        n = len(outcomes)
        if n < MIN_SAMPLES:
            return {"ok": False, "reason": f"نمونه کم است ({n}<{MIN_SAMPLES})", "by_label": {}}

        by_label: dict[str, dict] = {}
        for o in outcomes:
            d = by_label.setdefault(o.label, {"total": 0, "fail": 0, "errors": {}})
            d["total"] += 1
            if not o.ok:
                d["fail"] += 1
                key = (o.error or "unknown").strip()[:80]
                d["errors"][key] = d["errors"].get(key, 0) + 1
        for d in by_label.values():
            d["fail_rate"] = d["fail"] / d["total"] if d["total"] else 0.0
        return {"ok": True, "reason": None, "by_label": by_label}


class ACECurator:
    """از reflection، proposalهای procedural می‌سازد و به‌صورتِ pending ذخیره می‌کند."""

    def __init__(self, db=None):
        self.db = db

    def curate(self, reflection: dict) -> list[Proposal]:
        if not reflection.get("ok"):
            return []
        proposals: list[Proposal] = []
        for label, d in reflection["by_label"].items():
            if d["total"] < MIN_LABEL_SAMPLES:
                continue
            if d["fail_rate"] >= FAILURE_RATE_GATE and d["errors"]:
                top_err = max(d["errors"].items(), key=lambda kv: kv[1])[0]
                proposals.append(Proposal(
                    label=label,
                    title=f"کاهشِ شکستِ «{label}» (نرخِ شکست {d['fail_rate']:.0%})",
                    playbook=(
                        f"در کارهای دسته‌ی «{label}»، قبل از پاسخ این بررسی اضافه شود: "
                        f"خطای پرتکرار «{top_err}» را پیش‌گیری کن "
                        f"(مثلاً اعتبارسنجیِ ورودی/منبع پیش از اقدام)."
                    ),
                    evidence={"total": d["total"], "fail": d["fail"],
                              "fail_rate": round(d["fail_rate"], 3), "top_error": top_err},
                ))
        return proposals

    def persist(self, proposals: list[Proposal]) -> int:
        """proposalها را به‌صورتِ pending در db ذخیره می‌کند (HITL). تعدادِ ذخیره‌شده را برمی‌گرداند."""
        if not self.db or not proposals:
            return 0
        saved = 0
        for p in proposals:
            try:
                self.db.save_improvement_report(
                    {"label": p.label, "kind": "ace_procedural", **p.evidence},
                    [p.title, p.playbook],
                    "pending",
                )
                saved += 1
            except Exception:
                pass
        return saved


class ACELoop:
    """هماهنگ‌کننده‌ی Reflector→Curator. اجرا فقط proposalِ pending تولید می‌کند."""

    def __init__(self, db=None):
        self.db = db
        self.reflector = ACEReflector()
        self.curator = ACECurator(db)

    def run(self, outcomes: list[Outcome], persist: bool = True) -> dict:
        reflection = self.reflector.reflect(outcomes)
        proposals = self.curator.curate(reflection)
        saved = self.curator.persist(proposals) if persist else 0
        return {
            "reflection": reflection,
            "proposals": proposals,
            "saved": saved,
            "applied_automatically": False,  # گاردریل: هرگز خودکار اعمال نمی‌شود
        }
