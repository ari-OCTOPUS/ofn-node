"""runtime_truth_v1 — قرارداد ماشینیِ حقیقتِ اجرایی نودها (F1، Round 19).

«قرارداد قبل از قابلیت»: این ماژول پیش از هر مولد/مصرف‌کننده‌ای فریز می‌شود
(FROZEN.lock = sha256 همین فایل؛ ویرایش بدون قفل = تست قرمز). فقط stdlib —
رفلکسِ ۱۳۸ نباید LLM/شبکه بخواهد (تست test_no_llm_import_in_reflex قفلش می‌کند).

دو محور متعامد (اصلاح دکترین ۰.۲):
  f1_status  — هستی و سیم‌کشی: LIVE | PRESENT_UNWIRED | STALE | NOT_FOUND | UNKNOWN
  gov_status — حاکمیت:        OPEN | BLOCKED | PARKED | OWNER_DECISION | BROKEN
یک چیز می‌تواند هم‌زمان PRESENT_UNWIRED و OWNER_DECISION باشد.

قواعد قفل‌شده (در خود قرارداد enforce می‌شوند، نه در حافظهٔ مصرف‌کننده):
  ۱) بدون رسید (sha/commit خالی) ⇒ f1_status=UNKNOWN — هرگز LIVE
  ۲) readers خالی ⇒ f1_status=PRESENT_UNWIRED — «بی‌خواننده» خودکشف
پنج ستون تمامیت F1: writer · readers · canonical_ref · sync_mode · conflict_winner
(ستون conflict_winner همان دیوار ضد split-brain لپ‌تاپ/برد است).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

CONTRACT_SCHEMA = "runtime_truth.v1"

F1_STATUSES: Tuple[str, ...] = (
    "LIVE", "PRESENT_UNWIRED", "STALE", "NOT_FOUND", "UNKNOWN",
)
GOV_STATUSES: Tuple[str, ...] = (
    "OPEN", "BLOCKED", "PARKED", "OWNER_DECISION", "BROKEN",
)
NODE_IDS: Tuple[str, ...] = ("138", "180", "182", "laptop")

MAX_EXCERPT = 500


class ContractViolation(ValueError):
    """نقض قرارداد = ساخته‌نشانی ردیف، نه سکوت."""


@dataclass(frozen=True)
class RuntimeTruthRow:
    id: str                       # مثل F1-138-A03
    claim: str
    node_id: str                  # 138 | 180 | 182 | laptop
    read_method: str              # فرمان دقیق اجراشده
    output_excerpt: str           # ≤500 کاراکتر
    evidence_path: str
    sha256_or_commit: str         # رسید — خالی = UNKNOWN (قاعدهٔ ۱)
    timestamp_utc: str
    f1_status: str
    gov_status: str
    writer: str                   # چه کسی می‌نویسد
    readers: Tuple[str, ...] = ()  # چه کسی می‌خواند — خالی = PRESENT_UNWIRED
    canonical_ref: str = ""       # مرجع نهایی
    sync_mode: str = ""           # چگونه همگام می‌شود
    conflict_winner: str = ""     # در تعارض چه کسی برنده است
    risk: str = ""
    next_smallest_safe_step: str = ""

    def __post_init__(self) -> None:
        if self.f1_status not in F1_STATUSES:
            raise ContractViolation(
                f"f1_status {self.f1_status!r} not in {F1_STATUSES}")
        if self.gov_status not in GOV_STATUSES:
            raise ContractViolation(
                f"gov_status {self.gov_status!r} not in {GOV_STATUSES}")
        if self.node_id not in NODE_IDS:
            raise ContractViolation(
                f"node_id {self.node_id!r} not in {NODE_IDS}")
        if len(self.output_excerpt) > MAX_EXCERPT:
            raise ContractViolation(
                f"output_excerpt {len(self.output_excerpt)} > {MAX_EXCERPT}")
        # قاعدهٔ ۱ — بدون رسید هرگز LIVE
        if not self.sha256_or_commit.strip() and self.f1_status == "LIVE":
            raise ContractViolation(
                "no receipt (sha256_or_commit empty) => f1_status must be "
                "UNKNOWN, never LIVE")
        # قاعدهٔ ۲ — بی‌خواننده هرگز LIVE
        if not self.readers and self.f1_status == "LIVE":
            raise ContractViolation(
                "empty readers => f1_status must be PRESENT_UNWIRED "
                "(or UNKNOWN/STALE), never LIVE")

    def as_dict(self) -> dict:
        d = {
            "schema": CONTRACT_SCHEMA,
            "id": self.id, "claim": self.claim, "node_id": self.node_id,
            "read_method": self.read_method,
            "output_excerpt": self.output_excerpt,
            "evidence_path": self.evidence_path,
            "sha256_or_commit": self.sha256_or_commit,
            "timestamp_utc": self.timestamp_utc,
            "f1_status": self.f1_status, "gov_status": self.gov_status,
            "writer": self.writer, "readers": list(self.readers),
            "canonical_ref": self.canonical_ref,
            "sync_mode": self.sync_mode,
            "conflict_winner": self.conflict_winner,
            "risk": self.risk,
            "next_smallest_safe_step": self.next_smallest_safe_step,
        }
        return d


def validate_rows(rows) -> None:
    """اعتبارسنجی یک مجموعه — id تکراری = نقض."""
    seen = set()
    for r in rows:
        if r.id in seen:
            raise ContractViolation(f"duplicate id {r.id!r}")
        seen.add(r.id)
